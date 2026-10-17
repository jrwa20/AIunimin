import io
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
import database
import agents
import tools
from main import app

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', tmp_path / 'test.db')
    monkeypatch.setattr(config, 'UPLOAD_DIR', tmp_path / 'uploads')
    monkeypatch.setattr(config, 'DEMO', True)
    with TestClient(app) as client:
        yield client

def image():
    output = io.BytesIO()
    Image.new('RGB', (16, 16), '#d2e59a').save(output, format='PNG')
    return output.getvalue()

def create(client, description='La llanta de mi bicicleta pierde aire', **changes):
    data = {'descripcion': description, 'lat': '4.6537', 'lon': '-74.0645', 'puede_caminar': 'true'}
    data.update(changes)
    return client.post('/api/casos', data=data, files={'imagen': ('../foto.png', image(), 'image/png')})

def test_full_demo_flow_persists_analysis_action_chat_and_traces(client):
    response = create(client)
    assert response.status_code == 201
    case = response.json()
    assert case['estado'] == 'completado' and case['demo']
    assert case['analisis']['categoria_servicio'] == 'pinchazo'
    assert len(case['alternativas']) == 3
    assert all(a['ruta']['distancia_m'] is None and a['ruta']['tipo'] == 'linea_recta' for a in case['alternativas'])
    assert 'imagen' not in case
    cid = case['id']
    payload = {'servicio_id': case['alternativas'][0]['id'], 'revision': 1, 'clave_idempotencia': 'prueba-operacion-1'}
    first = client.post(f'/api/casos/{cid}/solicitudes', json=payload)
    assert first.status_code == 201
    assert client.post(f'/api/casos/{cid}/solicitudes', json=payload).json()['id'] == first.json()['id']
    assert client.post(f'/api/casos/{cid}/mensajes', json={'contenido':'¿Cuánto cuesta la reparación?'}).status_code == 200
    restored = client.get(f'/api/casos/{cid}').json()
    assert len(restored['solicitudes']) == 1 and len(restored['mensajes']) == 2
    assert 'no está verificado' in restored['mensajes'][-1]['contenido']
    actors = {e['actor'] for e in client.get(f'/api/casos/{cid}/trazas').json()}
    assert {'agente_analisis', 'agente_servicios_movilidad', 'buscar_servicios_propios', 'calcular_ruta', 'guardar_solicitud'} <= actors
    assert client.get(f'/api/casos/{cid}/evidencia').content == image()
    assert len(client.get('/api/casos').json()) == 1
    # Reopen SQLite through a fresh app lifecycle, preserving the same path.
    with TestClient(app) as restarted:
        assert restarted.get(f'/api/casos/{cid}').json()['analisis'] == restored['analisis']
        assert restarted.get(f'/api/casos/{cid}').json()['solicitudes'] == restored['solicitudes']

def test_missing_information_stops_mobility_then_clarifies(client):
    case = create(client, 'Necesito ayuda con algo que no entiendo').json()
    assert case['estado'] == 'requiere_aclaracion'
    assert not case['alternativas']
    traces = client.get(f"/api/casos/{case['id']}/trazas").json()
    assert 'agente_servicios_movilidad' not in {e['actor'] for e in traces}
    response = client.post(f"/api/casos/{case['id']}/aclaraciones", json={'respuesta':'La cadena de la bicicleta se sale', 'revision':1})
    assert response.json()['estado'] == 'completado' and response.json()['revision'] == 2
    assert response.json()['analisis']['categoria_servicio'] == 'transmision'
    assert len(client.get(f"/api/casos/{case['id']}/revisiones").json()) == 2
    assert client.post(f"/api/casos/{case['id']}/aclaraciones", json={'respuesta':'Otro detalle', 'revision':1}).status_code == 409

@pytest.mark.parametrize('description,status', [('Mi computador no funciona correctamente','fuera_de_alcance'), ('La bicicleta no frena y frena perfectamente','contradictorio')])
def test_invalid_analysis_branches(client, description, status):
    case = create(client, description).json()
    assert case['estado'] == status and not case['alternativas']

@pytest.mark.parametrize('changes', [{'lat':'5.1'}, {'lon':'0'}, {'puede_caminar':'false'}, {'descripcion':'        '}])
def test_invalid_form(client, changes):
    assert create(client, **changes).status_code == 422
    assert client.get('/api/casos').json() == []

def test_rejects_fake_and_oversized_images(client):
    data = {'descripcion':'Necesito reparar una llanta', 'lat':4.65,'lon':-74.06,'puede_caminar':'true'}
    assert client.post('/api/casos',data=data,files={'imagen':('x.png',b'not an image','image/png')}).status_code == 422
    assert client.post('/api/casos',data=data,files={'imagen':('x.png',b'x'*(5*1024*1024+1),'image/png')}).status_code == 413

def test_request_must_belong_to_current_case_revision(client):
    case = create(client).json(); cid = case['id']
    path = f'/api/casos/{cid}/solicitudes'
    assert client.post(path,json={'servicio_id':'inventado','revision':1,'clave_idempotencia':'operacion-falsa'}).status_code == 422
    assert client.post(path,json={'servicio_id':'demo-01','revision':2,'clave_idempotencia':'operacion-vieja'}).status_code == 409
    assert client.post(path,json={'servicio_id':case['alternativas'][0]['id'],'revision':1,'clave_idempotencia':'operacion-buena'}).status_code == 201
    assert client.post(path,json={'servicio_id':case['alternativas'][1]['id'],'revision':1,'clave_idempotencia':'otra-operacion'}).status_code == 409

def test_model_failure_is_persisted_without_secret(client,monkeypatch):
    monkeypatch.setattr(config,'DEMO',False)
    def fail(): raise RuntimeError('SECRET-TEST-DO-NOT-LEAK')
    monkeypatch.setattr(agents,'gemini_client',fail)
    case = create(client).json()
    assert case['estado'] == 'error'
    assert 'SECRET-TEST' not in json.dumps(case)
    assert 'SECRET-TEST' not in client.get(f"/api/casos/{case['id']}/trazas").text

class FakeGemini:
    """Provider contract test only; does not claim live model behavior."""
    def __init__(self): self.models = self
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def generate_content(self,**kwargs):
        self.kwargs = kwargs
        analysis = agents.demo_analysis({'descripcion':'La llanta pierde aire','aclaraciones':[]})
        return type('Response',(),{'text': json.dumps(analysis)})()

def test_live_catalog_empty_excludes_demo_records(client,monkeypatch):
    monkeypatch.setattr(config,'DEMO',False)
    with database.connect() as db:
        db.execute('DELETE FROM servicios WHERE es_demo=0')
    provider = FakeGemini(); monkeypatch.setattr(agents,'gemini_client',lambda:provider)
    case = create(client).json()
    assert case['estado'] == 'sin_alternativas' and not case['demo']
    assert provider.kwargs['contents'][0].inline_data.mime_type == 'image/png'
    assert provider.kwargs['config'].response_schema is agents.Analisis

def test_real_maintenance_catalog_has_provenance_and_excludes_demo(client):
    candidates = tools.buscar_servicios_propios('mantenimiento',(4.6537,-74.0645),False)
    assert len(candidates) == 2
    assert all(not item['es_demo'] and item['fuente'].startswith('https://www.specialized.com/') and item['verificado_en'] for item in candidates)
    assert not tools.buscar_servicios_propios('pinchazo',(4.6537,-74.0645),False)

def test_route_failure_produces_partial_result(client,monkeypatch):
    monkeypatch.setattr(config,'DEMO',False)
    monkeypatch.setattr(agents,'gemini_client',FakeGemini)
    with database.connect() as db:
        db.execute('INSERT INTO servicios VALUES(?,?,?,?,?,?,?,?,?)',('real-test','Servicio prueba contrato','["pinchazo"]',4.654,-74.065,'Dirección de prueba','https://example.com','2026-10-16',0))
    def fail(*args): raise RuntimeError('provider secret')
    monkeypatch.setattr(agents,'calcular_ruta',fail)
    case = create(client).json()
    assert case['estado'] == 'parcial'
    assert case['alternativas'][0]['ruta'] is None
    assert 'provider secret' not in json.dumps(case)

def test_ors_request_coordinate_order_and_response(monkeypatch):
    calls = {}
    def handler(req):
        calls['payload'] = json.loads(req.content)
        calls['path'] = req.url.path
        return __import__('httpx').Response(200,json={'features':[{'properties':{'summary':{'distance':1250,'duration':900}},'geometry':{'coordinates':[[-74.06,4.65],[-74.07,4.66]]}}]})
    import httpx
    original = httpx.Client
    monkeypatch.setenv('ORS_API_KEY','dummy-contract-test')
    monkeypatch.setattr(tools.httpx,'Client',lambda **kwargs:original(transport=httpx.MockTransport(handler)))
    route = tools.calcular_ruta((4.65,-74.06),(4.66,-74.07),False)
    assert calls['payload']['coordinates'] == [[-74.06,4.65],[-74.07,4.66]]
    assert 'foot-walking' in calls['path']
    assert route['distancia_m'] == 1250 and route['duracion_s'] == 900

def test_missing_case_and_empty_chat(client):
    assert client.get('/api/casos/no-existe').status_code == 404
    case = create(client).json()
    assert client.post(f"/api/casos/{case['id']}/mensajes",json={'contenido':'   '}).status_code == 422

def test_interrupted_case_is_recoverable_after_restart(client):
    case = create(client).json()
    with database.connect() as db:
        db.execute("UPDATE casos SET estado='procesando' WHERE id=?", (case['id'],))
    with TestClient(app) as restarted:
        restored = restarted.get(f"/api/casos/{case['id']}").json()
        assert restored['estado'] == 'error'
        assert 'interrumpió' in restored['error']
        assert any(x['actor'] == 'recuperacion_inicio' for x in restarted.get(f"/api/casos/{case['id']}/trazas").json())
