import {useEffect, useRef, useState} from 'react';
import * as L from './vendor/leaflet/leaflet.js';
import './vendor/leaflet/leaflet.css';
import {mapGeometry} from './mapGeometry.js';

export default function StreetMap({current,selected,onSelect,latitude=4.6537,longitude=-74.0645,confirmed=false}) {
  const container=useRef(null), instance=useRef(null);
  const [status,setStatus]=useState('loading');
  const [retry,setRetry]=useState(0);
  const [places,setPlaces]=useState([]),[chosen,setChosen]=useState(null),[externalRoute,setExternalRoute]=useState(null);
  const [searching,setSearching]=useState(false),[routing,setRouting]=useState(false),[searchDone,setSearchDone]=useState(false),[apiError,setApiError]=useState('');
  const pending=useRef(null);
  const api=import.meta.env.VITE_API_BASE_URL || '';
  async function callApi(path,options,signal){
    const response=await fetch(api+path,{...options,signal:AbortSignal.any([signal,AbortSignal.timeout(45000)])});
    const data=await response.json().catch(()=>({}));
    if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'No se pudo completar la consulta del mapa.');
    return data;
  }
  async function searchPlaces(){
    pending.current?.abort();const controller=new AbortController();pending.current=controller;
    setSearching(true);setRouting(false);setApiError('');setPlaces([]);setChosen(null);setExternalRoute(null);setSearchDone(false);
    try{const data=await callApi('/api/mapa/talleres?'+new URLSearchParams({lat,lon}),{},controller.signal);setPlaces(data.lugares);setSearchDone(true);}
    catch(error){if(error.name!=='AbortError')setApiError(error.message||'No pudimos conectar con la búsqueda de talleres.');}
    finally{if(!controller.signal.aborted)setSearching(false);}
  }
  async function requestRoute(place){
    pending.current?.abort();const controller=new AbortController();pending.current=controller;
    setChosen(place);setExternalRoute(null);setRouting(true);setApiError('');
    try{const data=await callApi('/api/mapa/ruta',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lat,lon,destino_lat:place.lat,destino_lon:place.lon})},controller.signal);setExternalRoute(data);}
    catch(error){if(error.name!=='AbortError')setApiError(error.message||'No pudimos conectar con el servicio de rutas.');}
    finally{if(!controller.signal.aborted)setRouting(false);}
  }
  const rawLat=current?.lat ?? latitude, rawLon=current?.lon ?? longitude;
  const valid=String(rawLat).trim()!=='' && String(rawLon).trim()!=='' && Number.isFinite(Number(rawLat)) && Number.isFinite(Number(rawLon)) && Number(rawLat)>=4.4 && Number(rawLat)<=4.9 && Number(rawLon)>=-74.3 && Number(rawLon)<=-73.9;
  const lat=valid?Number(rawLat):4.6537,lon=valid?Number(rawLon):-74.0645;
  useEffect(()=>{
    pending.current?.abort();setPlaces([]);setChosen(null);setExternalRoute(null);setSearchDone(false);setApiError('');setSearching(false);setRouting(false);
    return ()=>pending.current?.abort();
  },[lat,lon,current?.id,confirmed]);
  useEffect(()=>{
    setStatus('loading');
    const map=L.map(container.current,{scrollWheelZoom:false}).setView([lat,lon],14);
    instance.current=map;
    const tiles=L.tileLayer(import.meta.env.VITE_MAP_TILE_URL || 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',{
      maxZoom:19, attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);
    let failed=false;
    tiles.on('tileerror',()=>{failed=true;setStatus('error');});
    tiles.on('load',()=>{if(!failed)setStatus('ready');});
    const timeout=setTimeout(()=>setStatus(s=>s==='loading'?'error':s),12000);
    const resize=new ResizeObserver(()=>map.invalidateSize({pan:false}));resize.observe(container.current);
    return ()=>{clearTimeout(timeout);resize.disconnect();map.remove();instance.current=null;};
  },[retry]);
  useEffect(()=>{
    const map=instance.current;if(!map)return;
    const layer=L.layerGroup().addTo(map),bounds=[[lat,lon]];
    const origin=L.circleMarker([lat,lon],{radius:9,color:'#fff',weight:3,fillColor:'#183d35',fillOpacity:1}).addTo(layer);
    origin.bindTooltip(current?'Origen del caso':valid?'Origen del formulario':'Centro de Bogotá');
    for(const [i,item] of (current?.alternativas || []).entries()){
      if(!Number.isFinite(item.lat)||!Number.isFinite(item.lon))continue;
      const active=selected===item.id, position=[item.lat,item.lon];bounds.push(position);
      const marker=L.circleMarker(position,{radius:active?13:10,color:active?'#183d35':'#486d53',weight:3,fillColor:active?'#d2e59a':'#fff',fillOpacity:1}).addTo(layer);
      const label=document.createElement('span');label.textContent=`${String.fromCharCode(65+i)} · ${item.nombre}${item.es_demo?' (ejemplo ficticio)':''}`;
      marker.bindTooltip(label);marker.on('click',()=>onSelect?.(item.id));
      const line=mapGeometry(item.ruta);
      if(line.length){L.polyline(line,{color:active?'#183d35':'#718c6a',weight:active?5:3,opacity:active?1:.5}).addTo(layer);bounds.push(...line);}
    }
    if(bounds.length>1)map.fitBounds(bounds,{padding:[35,35],maxZoom:16});else map.setView([lat,lon],14);
    return ()=>layer.remove();
  },[current,selected,onSelect,lat,lon,valid,retry]);
  useEffect(()=>{
    const map=instance.current;if(!map)return;
    const layer=L.layerGroup().addTo(map),bounds=[[lat,lon]];
    for(const place of places){
      bounds.push([place.lat,place.lon]);
      const marker=L.circleMarker([place.lat,place.lon],{radius:chosen?.id===place.id?13:10,color:'#0c6480',weight:3,fillColor:'#8fd4e3',fillOpacity:1}).addTo(layer);
      const label=document.createElement('span');label.textContent=place.nombre;
      marker.bindTooltip(label);marker.on('click',()=>{pending.current?.abort();setRouting(false);setChosen(place);setExternalRoute(null);setApiError('');});
    }
    const line=mapGeometry(externalRoute);
    if(line.length){L.polyline(line,{color:'#007d9c',weight:5}).addTo(layer);bounds.push(...line);}
    if(bounds.length>1)map.fitBounds(bounds,{padding:[35,35],maxZoom:16});
    return ()=>layer.remove();
  },[places,chosen,externalRoute,lat,lon,retry]);
  return <section className="geographic-card street-map-card" aria-label="Mapa interactivo del caso">
    <div className="map-top"><strong>Mapa de Bogotá · calles y ubicación</strong><span className="map-pill">Leaflet + OpenStreetMap</span></div>
    <div className="map-search-actions"><button type="button" className="primary" disabled={!valid||(!current&&!confirmed)||searching||routing} onClick={searchPlaces}>{searching?'Buscando negocios…':'Buscar talleres reales cerca de mí'}</button><small>Busca hasta 8 negocios en un radio de 5 km. La búsqueda consulta OpenStreetMap y las rutas usan tu clave de ORS, también si el caso está en modo demo.</small>{!current&&!confirmed&&<small>Confirma el origen del formulario para buscar.</small>}</div>
    <div ref={container} className="street-map" aria-label="Mapa con origen, talleres y rutas disponibles"/>
    {status==='loading'&&<p className="map-disclaimer" role="status">Cargando calles…</p>}
    {status==='error'&&<div className="map-disclaimer" role="alert">No se pudieron cargar todas las calles. Revisa la conexión a internet. <button type="button" className="text-button" onClick={()=>setRetry(x=>x+1)}>Reintentar mapa</button></div>}
    {apiError&&<p className="map-search-error" role="alert">{apiError}</p>}
    {routing&&<p className="map-disclaimer" role="status">Calculando recorrido a pie con OpenRouteService…</p>}
    {externalRoute&&chosen&&<div className="map-route-summary" role="status"><strong>Ruta a {chosen.nombre}</strong><p>{(externalRoute.distancia_m/1000).toFixed(2)} km · {Math.ceil(externalRoute.duracion_s/60)} min a pie, estimados.</p><small>{externalRoute.advertencia}</small></div>}
    {searchDone&&!places.length&&<p className="map-disclaimer">No se encontraron negocios registrados en OpenStreetMap a menos de 5 km. Esto no confirma que no existan talleres en la zona.</p>}
    {!!places.length&&<div className="map-place-list"><h3>Negocios encontrados en OpenStreetMap</h3><p>Azul: resultados externos. Verde: catálogo del caso. Confirma reparación, horarios y disponibilidad con el negocio.</p>{places.map(place=><article key={place.id} className={chosen?.id===place.id?'map-place active':'map-place'}><strong>{place.nombre}</strong><p>{place.direccion}</p><small>{(place.distancia_recta_m/1000).toFixed(2)} km en línea recta · {place.reparacion_registrada?'Reparación registrada en OSM; confirma disponibilidad.':'Tienda de bicicletas; reparación sin confirmar.'}</small><div><button type="button" className="secondary" disabled={routing||searching} onClick={()=>requestRoute(place)}>Trazar ruta a pie</button><a href={place.fuente} target="_blank" rel="noreferrer">Ver ficha OSM ↗</a></div></article>)}</div>}
    <p className="map-disclaimer">{current?.demo?'Los talleres verdes del caso son ejemplos ficticios, sin rutas reales. La búsqueda azul consulta negocios externos reales.':'Los recorridos disponibles los calcula OpenRouteService. Sin datos de ruta no se dibuja un recorrido.'}</p>
    {current && !current.alternativas?.length && <p className="map-disclaimer">Se muestra tu origen. Los talleres aparecerán cuando el análisis produzca alternativas.</p>}
    {!valid&&<p className="map-disclaimer">Ingresa una ubicación válida para mostrar tu origen; por ahora se muestra el centro de Bogotá.</p>}
    <p className="map-disclaimer">La búsqueda externa funciona por separado del análisis: sus negocios no se guardan en el caso ni se incorporan al chat. OpenStreetMap recibe el área consultada; OpenRouteService recibe el origen y destino al solicitar una ruta.</p>
    <div className="street-map-links"><a href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`talleres de bicicletas cerca de ${lat},${lon}, Bogotá, Colombia`)}`} target="_blank" rel="noreferrer">Buscar otros talleres en Google Maps ↗</a><a href="https://www.openstreetmap.org/fixthemap" target="_blank" rel="noreferrer">Reportar un error del mapa</a></div>
  </section>;
}
