@echo off
REM Arma el juego en la carpeta dist\Derivia (sin instalador; para el instalador: construir_instalador.bat)
cd /d "%~dp0"
if not exist .venv (
  echo Creando el entorno de Python...
  py -m venv .venv || python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requisitos-armado.txt
pyinstaller --noconfirm --clean derivia.spec
echo.
echo ==========================================================
echo  Listo! El juego esta en la carpeta  dist\Derivia
echo  Se abre con Derivia.exe. Si lo moves, move la carpeta entera.
echo ==========================================================
pause
