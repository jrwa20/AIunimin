"""One-command local launcher for the downloadable project."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description='Iniciar BiciAyuda localmente.')
    parser.add_argument('--check', action='store_true', help='Comprobar la instalación sin abrir la aplicación.')
    args = parser.parse_args()
    if sys.version_info < (3, 11):
        raise SystemExit('Necesitas Python 3.11 o superior. Instálalo desde https://www.python.org/downloads/')
    python = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not (ROOT / 'frontend/dist/index.html').exists():
        raise SystemExit('Falta la interfaz compilada. Extrae el ZIP completo, conservando todas las carpetas.')
    if not python.exists():
        if args.check:
            raise SystemExit('Falta crear el entorno local. Ejecuta iniciar.py sin --check.')
        print('Preparando el entorno local de BiciAyuda…', flush=True)
        subprocess.run([sys.executable, '-m', 'venv', str(ROOT / '.venv')], check=True)
    check = subprocess.run([str(python), '-c', 'import fastapi, uvicorn, multipart, dotenv, google.genai, langgraph, pydantic, httpx, PIL'],
                           capture_output=True, text=True)
    if check.returncode:
        if args.check:
            raise SystemExit('Faltan dependencias. Ejecuta iniciar.py sin --check para instalarlas.')
        print('Instalando dependencias. La primera ejecución necesita conexión a Internet…', flush=True)
        subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(ROOT / 'backend/requirements.lock.txt')], check=True)
    if args.check:
        print('Instalación lista. Ejecuta iniciar.py para abrir BiciAyuda.')
        return
    print('\nBiciAyuda: http://127.0.0.1:8000\nMantén esta ventana abierta mientras uses la aplicación.\n', flush=True)
    subprocess.run([str(python), str(ROOT / 'run.py'), '--open'], cwd=ROOT, check=True)

if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as error:
        raise SystemExit(f'No se pudo completar el inicio (código {error.returncode}). Revisa el mensaje anterior.')
    except KeyboardInterrupt:
        print('\nBiciAyuda detenida.')
