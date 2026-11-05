"""Dónde guarda el juego sus cosas (progreso y memorias de matplotlib)."""

import os
from pathlib import Path


def carpeta_datos():
    """%APPDATA%\\Derivia en Windows; ~/.local/share/Derivia en Linux. La crea si no existe."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    carpeta = base / "Derivia"
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta
