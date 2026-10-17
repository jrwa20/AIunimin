import json
import math
import os
import httpx
from database import connect

def distance(a, b):
    lat1, lat2 = math.radians(a[0]), math.radians(b[0])
    dlat, dlon = lat2-lat1, math.radians(b[1]-a[1])
    term = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371000 * 2 * math.asin(min(1, math.sqrt(term)))

def buscar_servicios_propios(category, origin, demo):
    with connect() as db:
        rows = db.execute('SELECT * FROM servicios WHERE es_demo=?', (int(demo),)).fetchall()
    results = []
    for row in rows:
        item = dict(row)
        item['categorias'] = json.loads(item['categorias'])
        if category not in item['categorias']:
            continue
        if not demo and (not item['verificado_en'] or not item['fuente']):
            continue
        item['distancia_recta_m'] = round(distance(origin, (item['lat'], item['lon'])))
        if item['distancia_recta_m'] <= 20000:
            results.append(item)
    return sorted(results, key=lambda x: (x['distancia_recta_m'], x['id']))[:3]

def calcular_ruta(origin, destination, demo):
    if demo:
        return {'proveedor': 'Demostración: sin consulta externa', 'tipo': 'linea_recta',
                'distancia_m': None, 'duracion_s': None,
                'geometria': [[origin[1], origin[0]], [destination[1], destination[0]]],
                'advertencia': 'Línea recta ilustrativa; no es una ruta transitable ni un tiempo de viaje.'}
    key = os.getenv('ORS_API_KEY')
    if not key:
        raise RuntimeError('Falta configurar ORS_API_KEY en el backend.')
    with httpx.Client(timeout=25) as client:
        response = client.post('https://api.openrouteservice.org/v2/directions/foot-walking/geojson',
                               headers={'Authorization': key},
                               json={'coordinates': [[origin[1], origin[0]], [destination[1], destination[0]]]})
        response.raise_for_status()
        feature = response.json()['features'][0]
        summary = feature['properties']['summary']
        return {'proveedor': 'OpenRouteService', 'tipo': 'ruta',
                'distancia_m': summary['distance'], 'duracion_s': summary['duration'],
                'geometria': feature['geometry']['coordinates'],
                'advertencia': 'Estimación peatonal. No confirma condiciones actuales ni acceso con bicicleta.'}
