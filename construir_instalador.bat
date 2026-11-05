@echo off
REM Arma el instalador de Derivia: salida\Derivia-Setup-<version>.exe
REM Necesita Python y Inno Setup 6 (https://jrsoftware.org/isdl.php).
REM Lo mas facil es no correr esto y bajar el instalador que arma GitHub (ver LEEME.md).
cd /d "%~dp0"
if not exist .venv (
  echo Creando el entorno de Python...
  py -m venv .venv || python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requisitos-armado.txt
pyinstaller --noconfirm --clean derivia.spec || goto error
pip-licenses --from=mixed --with-license-file --no-license-path --format=plain-vertical --output-file=dist\Derivia\LICENCIAS.txt
copy /y juego\assets\fuentes\OFL.txt dist\Derivia\LICENCIA-Fredoka.txt >nul

set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist %ISCC% (
  echo.
  echo No encontre Inno Setup 6. Instalalo de https://jrsoftware.org/isdl.php y volve a correr esto.
  echo Igual el juego ya quedo armado en dist\Derivia\Derivia.exe
  pause
  exit /b 1
)
%ISCC% /DVersion=dev instalador.iss || goto error
echo.
echo ==========================================================
echo  Listo! El instalador esta en la carpeta  salida
echo ==========================================================
pause
exit /b 0

:error
echo.
echo Algo fallo: mira los mensajes de arriba.
pause
exit /b 1
