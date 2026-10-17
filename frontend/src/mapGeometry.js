// ORS entrega [longitud, latitud]; Leaflet espera [latitud, longitud].
export function mapGeometry(route) {
  if(route?.tipo!=='ruta' || !Array.isArray(route.geometria))return [];
  const points=route.geometria;
  if(points.length<2 || !points.every(p=>Array.isArray(p)&&p.length>=2&&Number.isFinite(p[0])&&Number.isFinite(p[1])&&Math.abs(p[0])<=180&&Math.abs(p[1])<=90))return [];
  return points.map(([lon,lat])=>[lat,lon]);
}
