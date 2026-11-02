@echo off
REM Arma Derivia.exe dentro de la carpeta dist
cd /d "%~dp0"
if not exist .venv (
  echo Creando el entorno de Python...
  py -m venv .venv || python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt pyinstaller
REM Skia: el motor de graficos que dibuja botones, islas y paneles con calidad alta.
REM Si no se pudiera instalar, el juego igual funciona con dibujos mas simples.
pip install skia-python || echo (No se pudo instalar Skia: el juego va a usar los graficos simples)
pyinstaller --noconfirm --clean derivia.spec
echo.
echo ==========================================================
echo  Listo! El juego esta en:  dist\Derivia.exe
echo  Podes copiarlo a donde quieras (por ejemplo al Escritorio).
echo ==========================================================
pause
