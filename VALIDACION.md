# Validación de la primera versión

Fecha: 16 de octubre de 2026.

## Comprobaciones realizadas

- Backend: **17 pruebas aprobadas**, última ejecución 3,12 segundos.
- Frontend: compilación de producción correcta mediante Vite.
- Navegador: formulario con ejemplo, confirmación del origen, ejecución de agentes en demo, tres alternativas, solicitud guardada, respuesta sobre precio desconocido y vista de trazas.
- Recuperación real en navegador después de reiniciar el servidor: se conservaron análisis, alternativas, solicitud y conversación.
- Revisión de escritorio a 1440 px y móvil a 390 px. Historial y resultados sin desbordamiento horizontal tras corregir la cuadrícula del historial.

## Cobertura automatizada

1. Caso de demostración completo con análisis, rutas ilustrativas, acción, chat y trazas.
2. Información insuficiente: no se ejecuta movilidad; una aclaración crea otra revisión.
3. Entrada ajena al dominio.
4. Descripción contradictoria.
5–8. Latitud, longitud, desplazamiento no confirmado y descripción vacía.
9. Imagen falsa o mayor de 5 MB.
10. Solicitud ajena a las alternativas, revisión antigua y duplicados.
11. Fallo de IA conservado sin filtrar detalles de credenciales.
12. Catálogo conectado vacío: exclusión de registros ficticios y contrato de envío de imagen al SDK.
13. Catálogo real de mantenimiento con procedencia.
14. Fallo geográfico: resultado parcial sin ruta inventada.
15. Contrato ORS: orden de coordenadas, perfil peatonal y lectura de distancia/duración.
16. Caso inexistente y pregunta vacía.
17. Recuperación de un caso interrumpido al arrancar de nuevo.

## Límites de lo verificado

Las llamadas a Gemini y OpenRouteService se simularon en las pruebas de contratos. La demostración del navegador usó reglas y servicios ficticios, identificados expresamente. No se ejecutaron llamadas externas con credenciales del grupo.

Para acreditar las siete fases en la sustentación: configurar claves propias en `backend/.env`, seleccionar `DEMO_MODE=false`, comprobar el modelo disponible, realizar consultas reales y registrar latencia, cuotas y costo aplicables. El catálogo real inicial solo acredita mantenimiento general; ampliar categorías si se demuestra otra necesidad. El grupo debe confirmar vigencia y acceso al establecimiento antes de usarlo como recomendación práctica.

El paquete no contiene claves, base de datos de la sesión, evidencias subidas, entornos virtuales ni dependencias instaladas. Incluye el código y la interfaz compilada. El repositorio GitHub todavía debe crearse y publicarse con la cuenta del grupo.
