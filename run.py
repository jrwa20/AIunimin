"""Start the built app: python run.py (after installing backend dependencies)."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
python = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
if python.exists() and Path(sys.prefix).resolve() != (ROOT / '.venv').resolve():
    os.execv(str(python), [str(python), str(Path(__file__).resolve()), *sys.argv[1:]])
sys.path.insert(0, str(ROOT / 'backend'))
if not (ROOT / 'frontend/dist/index.html').exists():
    raise SystemExit('Primero compila la interfaz: cd frontend y ejecuta npm install y npm run build.')
try:
    import uvicorn
except ImportError:
    raise SystemExit('Instala las dependencias: python -m pip install -r backend/requirements.txt')
if __name__ == '__main__':
    if '--open' in sys.argv:
        import threading
        import time
        import urllib.request
        import webbrowser

        def open_when_ready():
            for _ in range(60):
                try:
                    with urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=1) as response:
                        if response.status == 200:
                            webbrowser.open('http://127.0.0.1:8000')
                            return
                except OSError:
                    time.sleep(.5)
        threading.Thread(target=open_when_ready, daemon=True).start()
    uvicorn.run('main:app', host='127.0.0.1', port=8000)
