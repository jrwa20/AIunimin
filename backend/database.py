import json
import csv
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, timezone
from config import DB_PATH

CATEGORIAS = [
    {'id': 'pinchazo', 'nombre': 'Llantas y pinchazos'},
    {'id': 'frenos', 'nombre': 'Revisión de frenos'},
    {'id': 'transmision', 'nombre': 'Cadena y transmisión'},
    {'id': 'mantenimiento', 'nombre': 'Mantenimiento general'},
]

def now():
    return datetime.now(timezone.utc).isoformat()

@contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=20)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS servicios (
          id TEXT PRIMARY KEY, nombre TEXT NOT NULL, categorias TEXT NOT NULL,
          lat REAL NOT NULL, lon REAL NOT NULL, direccion TEXT NOT NULL,
          fuente TEXT NOT NULL, verificado_en TEXT, es_demo INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS casos (
          id TEXT PRIMARY KEY, descripcion TEXT NOT NULL, lat REAL NOT NULL,
          lon REAL NOT NULL, modo TEXT NOT NULL, estado TEXT NOT NULL,
          revision INTEGER NOT NULL, demo INTEGER NOT NULL, imagen TEXT NOT NULL,
          mime TEXT NOT NULL, hash_imagen TEXT NOT NULL, creado_en TEXT NOT NULL,
          actualizado_en TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS revisiones (
          caso_id TEXT NOT NULL REFERENCES casos(id), revision INTEGER NOT NULL,
          aclaraciones TEXT NOT NULL, analisis TEXT, alternativas TEXT NOT NULL DEFAULT '[]',
          error TEXT, PRIMARY KEY(caso_id, revision));
        CREATE TABLE IF NOT EXISTS solicitudes (
          id TEXT PRIMARY KEY, caso_id TEXT NOT NULL REFERENCES casos(id),
          revision INTEGER NOT NULL, servicio_id TEXT NOT NULL REFERENCES servicios(id),
          estado TEXT NOT NULL, creado_en TEXT NOT NULL, clave TEXT UNIQUE NOT NULL,
          UNIQUE(caso_id, revision));
        CREATE TABLE IF NOT EXISTS mensajes (
          id INTEGER PRIMARY KEY, caso_id TEXT NOT NULL REFERENCES casos(id),
          revision INTEGER NOT NULL, rol TEXT NOT NULL, contenido TEXT NOT NULL,
          creado_en TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS eventos (
          id INTEGER PRIMARY KEY, caso_id TEXT NOT NULL REFERENCES casos(id),
          revision INTEGER NOT NULL, actor TEXT NOT NULL, estado TEXT NOT NULL,
          resumen TEXT NOT NULL, creado_en TEXT NOT NULL);
        ''')
        examples = [
            ('demo-01', 'Taller Pedal Norte · ejemplo', ['pinchazo', 'frenos', 'mantenimiento'], 4.6652, -74.0622, 'Punto ficticio · Chapinero'),
            ('demo-02', 'Biciestación Parkway · ejemplo', ['pinchazo', 'transmision', 'mantenimiento'], 4.6418, -74.0730, 'Punto ficticio · Teusaquillo'),
            ('demo-03', 'Ciclo Taller Central · ejemplo', ['pinchazo', 'frenos', 'transmision', 'mantenimiento'], 4.6531, -74.0804, 'Punto ficticio · Galerías'),
        ]
        for sid, name, categories, lat, lon, address in examples:
            db.execute('INSERT OR IGNORE INTO servicios VALUES(?,?,?,?,?,?,?,?,?)',
                       (sid, name, json.dumps(categories), lat, lon, address, 'Datos ficticios para demostración académica', None, 1))
        with (Path(__file__).parent / 'catalogo.inicial.csv').open(encoding='utf-8', newline='') as source:
            for row in csv.DictReader(source):
                db.execute('INSERT OR IGNORE INTO servicios VALUES(?,?,?,?,?,?,?,?,?)',
                    (row['id'], row['nombre'], json.dumps(row['categorias'].split('|')), float(row['lat']), float(row['lon']),
                     row['direccion'], row['fuente'], row['verificado_en'], 0))

def event(cid, revision, actor, status, summary):
    with connect() as db:
        db.execute('INSERT INTO eventos(caso_id,revision,actor,estado,resumen,creado_en) VALUES(?,?,?,?,?,?)',
                   (cid, revision, actor, status, summary, now()))

def get_case(cid):
    with connect() as db:
        row = db.execute('SELECT * FROM casos WHERE id=?', (cid,)).fetchone()
        if not row:
            return None
        case = dict(row)
        revision = dict(db.execute('SELECT * FROM revisiones WHERE caso_id=? AND revision=?', (cid, case['revision'])).fetchone())
        case['analisis'] = json.loads(revision['analisis']) if revision['analisis'] else None
        case['alternativas'] = json.loads(revision['alternativas'])
        case['aclaraciones'] = json.loads(revision['aclaraciones'])
        case['error'] = revision['error']
        case['solicitudes'] = [dict(x) for x in db.execute('SELECT * FROM solicitudes WHERE caso_id=? ORDER BY creado_en', (cid,))]
        case['mensajes'] = [dict(x) for x in db.execute('SELECT * FROM mensajes WHERE caso_id=? AND revision=? ORDER BY id', (cid, case['revision']))]
        case['demo'] = bool(case['demo'])
        return case

def public_case(case):
    return {k: v for k, v in case.items() if k not in {'imagen', 'mime', 'hash_imagen'}}
