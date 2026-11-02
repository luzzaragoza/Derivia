"""Genera el ícono de Derivia (la cara del gato) en juego/assets/.

    python herramientas/hacer_icono.py

Deja dos archivos:
  juego/assets/icono.png   el de la ventana del juego
  juego/assets/derivia.ico el del .exe y el instalador (16 a 256 px)

Necesita pygame-ce y Pillow (pip install pillow). Con skia-python el gato sale más prolijo."""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pygame  # noqa: E402
from PIL import Image  # noqa: E402

LADO = 256


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    from juego import gato
    from juego.lienzo import poner_escala

    poner_escala(4)                              # se dibuja grande para que quede nítido
    cara = gato.superficie(70, "feliz", ropa=()).sup
    # recortar lo transparente y centrarlo en un cuadrado
    caja = cara.get_bounding_rect(min_alpha=1)
    cara = cara.subsurface(caja).copy()
    k = LADO * 0.96 / max(caja.w, caja.h)
    cara = pygame.transform.smoothscale(cara, (round(caja.w * k), round(caja.h * k)))
    icono = pygame.Surface((LADO, LADO), pygame.SRCALPHA)
    icono.blit(cara, cara.get_rect(center=(LADO // 2, LADO // 2)))

    carpeta = os.path.join(RAIZ, "juego", "assets")
    png = os.path.join(carpeta, "icono.png")
    pygame.image.save(icono, png)
    Image.open(png).save(os.path.join(carpeta, "derivia.ico"),
                         sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("Listo:", png, "y derivia.ico")


if __name__ == "__main__":
    main()
