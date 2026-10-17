"""Import verified, user-curated services: python import_catalog.py catalogo.csv."""
import csv
import json
import sys
from datetime import datetime
from urllib.parse import urlparse
from database import CATEGORIAS, connect, init_db

def import_catalog(path):
    with open(path, encoding='utf-8-sig', newline='') as source:
        rows = list(csv.DictReader(source))
    allowed = {x['id'] for x in CATEGORIAS}
    validated = []
    for row in rows:
        categories = [x.strip() for x in row['categorias'].split('|')]
        lat, lon = float(row['lat']), float(row['lon'])
        if not row['id'].strip() or row['id'].startswith('demo-') or not row['nombre'].strip():
            raise ValueError('Identificador o nombre inválido.')
        if not set(categories) <= allowed or not categories or '' in categories:
            raise ValueError('Categorías inválidas.')
        if not (4.4 <= lat <= 4.9 and -74.3 <= lon <= -73.9):
            raise ValueError('Coordenadas fuera del área inicial de Bogotá.')
        if urlparse(row['fuente']).scheme not in {'https', 'http'} or not urlparse(row['fuente']).netloc:
            raise ValueError('Indica una URL de procedencia verificable.')
        datetime.fromisoformat(row['verificado_en'])
        if not row['direccion'].strip():
            raise ValueError('Indica la dirección verificada.')
        validated.append((row['id'], row['nombre'], json.dumps(categories), lat, lon, row['direccion'], row['fuente'], row['verificado_en'], 0))
    init_db()
    with connect() as db:
        for values in validated:
            db.execute('''INSERT INTO servicios VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
                nombre=excluded.nombre,categorias=excluded.categorias,lat=excluded.lat,lon=excluded.lon,
                direccion=excluded.direccion,fuente=excluded.fuente,verificado_en=excluded.verificado_en,es_demo=0''', values)
    return len(validated)

if __name__ == '__main__':
    print(f'{import_catalog(sys.argv[1])} servicios importados.')
