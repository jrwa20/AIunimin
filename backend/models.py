from typing import Literal
from pydantic import BaseModel, Field

Categoria = Literal['pinchazo', 'frenos', 'transmision', 'mantenimiento']

class Analisis(BaseModel):
    estado: Literal['valido', 'requiere_aclaracion', 'contradictorio', 'fuera_de_alcance']
    necesidad: str
    categoria_servicio: Categoria | None
    observaciones_imagen: list[str]
    hechos_reportados: list[str]
    hipotesis: list[str]
    contradicciones: list[str]
    informacion_faltante: list[str]
    preguntas_aclaracion: list[str]
    advertencias: list[str]

class Aclaracion(BaseModel):
    respuesta: str = Field(min_length=3, max_length=4000)
    revision: int = Field(ge=1)

class Mensaje(BaseModel):
    contenido: str = Field(min_length=1, max_length=2000)

class Solicitud(BaseModel):
    servicio_id: str
    revision: int = Field(ge=1)
    clave_idempotencia: str = Field(min_length=8, max_length=100)
