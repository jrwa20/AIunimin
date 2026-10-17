# Procedencia del catálogo inicial

Consulta documental: 16 de octubre de 2026. Dos establecimientos reales con servicio técnico anunciado en su directorio oficial. No se verificó atención presencial, disponibilidad de cupos ni servicios específicos como reparación de pinchazos.

| Registro | Dirección publicada | Coordenadas del enlace oficial Obtener indicaciones | Fuente |
|---|---|---|---|
| Specialized Zona G - Bogotá | Calle 70A 4-80 | 4.6520588, -74.0540596 | [Directorio oficial](https://www.specialized.com/co/es/store-finder/specialized-zona-g-bogot%C3%A1/6411187) |
| Specialized Bogotá 122 | Calle 122 17A-56 | 4.701551874058105, -74.04665039176432 | [Directorio oficial](https://www.specialized.com/co/es/store-finder/specialized-bogota-122/7018607) |

Se clasificaron únicamente como mantenimiento general por su oferta publicada de servicio técnico. No se asumió cobertura específica de las demás categorías. Los datos se incluyen en `catalogo.inicial.csv` y se cargan al iniciar si el identificador aún no existe. El modo conectado solo utiliza los registros reales; el modo demostración solo utiliza los ficticios.

Las coordenadas provienen del parámetro `destination` de los enlaces publicados por cada establecimiento en su directorio, sin reutilizar claves de mapas. Son ubicaciones documentales, no un levantamiento de campo; se recomienda confirmar el acceso antes de desplazarse. No se incluyeron horarios, precios ni teléfonos para evitar afirmar disponibilidad no consultada en tiempo real.

El directorio se puede ampliar mediante `import_catalog.py` después de verificar nombre, categorías, dirección y posición. Una URL válida y una fecha no bastan para certificar un lugar: la revisión del dato es responsabilidad de quien lo incorpora.
