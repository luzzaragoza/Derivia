"""Las pantallas del juego (estilo aventura: islas, mar, madera y pergamino).

Cada pantalla vive en su propio módulo y se carga recién cuando se la usa: así el menú aparece
sin esperar a SymPy (que solo hace falta en los niveles). Se usan como siempre:

    from juego import escenas
    escenas.Mapa(app)
"""

import importlib

_MODULO = {
    "Escena": "base",
    "Menu": "menu",
    "Mapa": "mapa",
    "Juego": "nivel",
    "FinNivel": "fin_nivel",
    "Cuaderno": "cuaderno",
    "Ayuda": "ayuda",
    "Opciones": "opciones",
    "DesafioIntro": "desafio",
    "Tienda": "tienda",
    "NombreGato": "nombre_gato",
    "RevisarErrores": "revisar_errores",
}

__all__ = list(_MODULO)


def __getattr__(nombre):
    if nombre not in _MODULO:
        raise AttributeError(f"module {__name__!r} has no attribute {nombre!r}")
    clase = getattr(importlib.import_module(f".{_MODULO[nombre]}", __name__), nombre)
    globals()[nombre] = clase          # la próxima vez ya está a mano
    return clase


def __dir__():
    return sorted(set(globals()) | set(__all__))
