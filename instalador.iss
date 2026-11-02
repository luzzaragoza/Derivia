; Instalador de Derivia (Inno Setup 6: https://jrsoftware.org/isinfo.php)
;
; Antes hay que armar dist\Derivia con PyInstaller (construir_instalador.bat lo hace todo).
; A mano:   iscc /DVersion=1.0.0 instalador.iss
; Deja:     salida\Derivia-Setup-<versión>.exe

#ifndef Version
  #define Version "0.0.0-dev"
#endif

[Setup]
; AppId identifica al juego en Windows: NO cambiarlo, o las actualizaciones se instalan aparte
AppId={{3C533C80-51A2-44CF-BA30-5B8FD02CD63B}
AppName=Derivia
AppVersion={#Version}
AppVerName=Derivia {#Version}
AppPublisher=Luz Zaragoza
AppPublisherURL=https://github.com/luzzaragoza/Derivia
DefaultDirName={autopf}\Derivia
DefaultGroupName=Derivia
DisableProgramGroupPage=yes
; no pide permisos de administrador: se instala para el usuario (o para todos, si lo elige)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=salida
OutputBaseFilename=Derivia-Setup-{#Version}
SetupIconFile=juego\assets\derivia.ico
UninstallDisplayIcon={app}\Derivia.exe
UninstallDisplayName=Derivia
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; si el juego está abierto, ofrece cerrarlo antes de actualizar
CloseApplications=yes

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "escritorio"; Description: "Crear un acceso directo en el Escritorio"; GroupDescription: "Accesos directos:"

[Files]
; al actualizar se borra la versión vieja entera para que no queden archivos sueltos
Source: "dist\Derivia\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
Type: filesandordirs; Name: "{app}\_internal"

[Icons]
Name: "{autoprograms}\Derivia"; Filename: "{app}\Derivia.exe"
Name: "{autodesktop}\Derivia"; Filename: "{app}\Derivia.exe"; Tasks: escritorio

[Run]
Filename: "{app}\Derivia.exe"; Description: "Jugar a Derivia ahora"; Flags: nowait postinstall skipifsilent

; El progreso (%APPDATA%\Derivia\progreso.json) no se toca ni al actualizar ni al desinstalar.
