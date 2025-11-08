@echo off
echo 🚀 Iniciando Kairos API...

REM Activar entorno virtual
call venv\Scripts\activate

REM Iniciar API
python backend/api/app.py

pause