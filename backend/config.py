import os
from pathlib import Path
from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / '.env')

def local_path(name, default):
    path = Path(os.getenv(name, default))
    return path if path.is_absolute() else BASE / path

DEMO = os.getenv('DEMO_MODE', 'true').lower() == 'true'
DB_PATH = local_path('DATABASE_PATH', 'data/biciayuda.db')
UPLOAD_DIR = local_path('UPLOAD_DIR', 'data/uploads')
MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
