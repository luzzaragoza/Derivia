"""Genera el ícono de Derivia (la cara del gato) en juego/assets/.

    python herramientas/hacer_icono.py

Deja:
  juego/assets/icono.png   el de la ventana del juego
  juego/assets/derivia.ico el del .exe y el instalador (16 a 256 px)
  tienda/imagenes/*.png    los logos del paquete de la Microsoft Store

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
    # logos del paquete de la Microsoft Store (tamaños que pide el manifiesto)
    tienda = os.path.join(RAIZ, "tienda", "imagenes")
    os.makedirs(tienda, exist_ok=True)
    gato_png = Image.open(png)
    for nombre, (w, h), relleno in (("StoreLogo", (50, 50), 1.0), ("Square44x44Logo", (44, 44), 1.0),
                                    ("Square150x150Logo", (150, 150), 0.8), ("Wide310x150Logo", (310, 150), 0.8)):
        lado = round(min(w, h) * relleno)
        lienzo = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        chico = gato_png.resize((lado, lado), Image.LANCZOS)
        lienzo.paste(chico, ((w - lado) // 2, (h - lado) // 2), chico)
        lienzo.save(os.path.join(tienda, nombre + ".png"))
    print("Listo:", png, ", derivia.ico y los logos de la tienda")


if __name__ == "__main__":
    main()
