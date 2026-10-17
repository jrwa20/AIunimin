"""Exploración externa del mapa, independiente del análisis y del catálogo del caso."""
import math
import os
import time
from threading import Lock
import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from tools import calcular_ruta, distance

router = APIRouter(prefix='/api/mapa')
_cache = {}
_lock = Lock()

class RouteRequest(BaseModel):
    lat: float = Field(ge=4.4, le=4.9)
    lon: float = Field(ge=-74.3, le=-73.9)
    destino_lat: float = Field(ge=4.4, le=4.9)
    destino_lon: float = Field(ge=-74.3, le=-73.9)

def parse_places(elements, origin):
    found = []
    for element in elements:
        tags = element.get('tags', {})
        if tags.get('service:bicycle:repair') == 'no':
            continue
        if tags.get('shop') != 'bicycle' and tags.get('service:bicycle:repair') != 'yes':
            continue
        point = element.get('center') or element
        lat, lon = point.get('lat'), point.get('lon')
        if not isinstance(lat, (int,float)) or not isinstance(lon, (int,float)):
            continue
        if not math.isfinite(lat) or not math.isfinite(lon) or not (4.4<=lat<=4.9 and -74.3<=lon<=-73.9):
            continue
        if element.get('type') not in ('node','way','relation') or not isinstance(element.get('id'),int):
            continue
        meters = round(distance(origin, (lat,lon)))
        if meters > 5000:
            continue
        address = ' '.join(filter(None,[tags.get('addr:street'),tags.get('addr:housenumber')]))
        found.append(dict(id=f"osm-{element['type']}-{element['id']}",
            nombre=tags.get('name') or 'Negocio de bicicletas sin nombre registrado',lat=lat,lon=lon,
            direccion=address or 'Dirección no registrada; consulta el punto del mapa.',
            distancia_recta_m=meters,reparacion_registrada=tags.get('service:bicycle:repair')=='yes',
            fuente=f"https://www.openstreetmap.org/{element['type']}/{element['id']}"))
    return sorted(found,key=lambda x:(x['distancia_recta_m'],x['id']))[:8]

@router.get('/talleres')
def search(lat: float=Query(ge=4.4,le=4.9),lon: float=Query(ge=-74.3,le=-73.9)):
    key=(round(lat,5),round(lon,5)); stamp=time.monotonic()
    with _lock:
        cached=_cache.get(key)
        if cached and stamp-cached[0]<300:return cached[1]
    query=f'''[out:json][timeout:10];(nwr(around:5000,{lat},{lon})["shop"="bicycle"];nwr(around:5000,{lat},{lon})["service:bicycle:repair"="yes"];);out center tags;'''
    try:
        endpoints = ['https://overpass.private.coffee/api/interpreter', 'https://overpass-api.de/api/interpreter']
        with httpx.Client(timeout=httpx.Timeout(15,connect=5),headers={'User-Agent':'BiciAyudaBogota/1.1 academic map search'}) as client:
            for index,endpoint in enumerate(endpoints):
                try:
                    response=client.get(endpoint,params={'data':query})
                    response.raise_for_status(); data=response.json()
                    if data.get('remark') and index==0:continue
                    break
                except (httpx.HTTPError,ValueError):
                    if index==len(endpoints)-1:raise
        if data.get('remark'):
            raise HTTPException(503,'La búsqueda externa no pudo completarse. Intenta más tarde.')
        places=parse_places(data.get('elements',[]),(lat,lon))
    except HTTPException:raise
    except httpx.HTTPStatusError as error:
        raise HTTPException(503,'OpenStreetMap/Overpass está ocupado. Intenta más tarde.' if error.response.status_code in (429,504) else 'El servicio externo rechazó la búsqueda. Intenta más tarde.') from None
    except (httpx.HTTPError,ValueError,KeyError,TypeError):
        raise HTTPException(503,'No se pudo consultar OpenStreetMap/Overpass. Revisa la conexión e intenta más tarde.') from None
    result={'lugares':places,'proveedor':'OpenStreetMap / Overpass','radio_m':5000,
            'advertencia':'Datos comunitarios: confirma reparación, horarios y disponibilidad directamente con el negocio.'}
    with _lock:
        if len(_cache)>=32:_cache.clear()
        _cache[key]=(stamp,result)
    return result

@router.post('/ruta')
def route(payload: RouteRequest):
    if not os.getenv('ORS_API_KEY','').strip():
        raise HTTPException(503,'Falta ORS_API_KEY en backend/.env. Configura la clave y reinicia el servidor.')
    try:
        return calcular_ruta((payload.lat,payload.lon),(payload.destino_lat,payload.destino_lon),False)
    except httpx.HTTPStatusError as error:
        code=error.response.status_code
        message={401:'OpenRouteService no acepta la clave. Revisa ORS_API_KEY y reinicia.',403:'OpenRouteService rechazó el acceso. Revisa la clave y los permisos.',429:'Se agotó la cuota de OpenRouteService. Espera o revisa tu cuenta.',404:'OpenRouteService no encontró un recorrido para esos puntos.'}.get(code,f'OpenRouteService no pudo calcular la ruta (HTTP {code}). Prueba otro taller.')
        raise HTTPException(503,message) from None
    except (httpx.HTTPError,ValueError,KeyError,IndexError,TypeError,RuntimeError):
        raise HTTPException(503,'No se pudo obtener una ruta a pie. Revisa la conexión o prueba otro taller.') from None
