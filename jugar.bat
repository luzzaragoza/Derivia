@echo off
REM Juega directamente con Python (sin armar el .exe)
cd /d "%~dp0"
if not exist .venv (
  echo Preparando todo por primera vez, puede tardar un par de minutos...
  py -m venv .venv || python -m venv .venv
  call .venv\Scripts\activate.bat
  python -m pip install --upgrade pip
  pip install -r requirements.txt
) else (
  call .venv\Scripts\activate.bat
)
REM Skia (graficos en alta calidad). Si falta, se instala una sola vez.
python -c "import skia" 2>nul || pip install skia-python
start "" pythonw main.py
