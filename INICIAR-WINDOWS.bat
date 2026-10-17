@echo off
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 iniciar.py
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo Necesitas instalar Python 3.11 o superior desde https://www.python.org/downloads/
        echo Durante la instalacion, activa la opcion Add Python to PATH.
    ) else (
        python iniciar.py
    )
)
pause
