@echo off
REM Arma Calculandia.exe dentro de la carpeta dist
cd /d "%~dp0"
if not exist .venv (
  echo Creando el entorno de Python...
  py -m venv .venv || python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean calculandia.spec
echo.
echo ==========================================================
echo  Listo! El juego esta en:  dist\Calculandia.exe
echo  Podes copiarlo a donde quieras (por ejemplo al Escritorio).
echo ==========================================================
pause
