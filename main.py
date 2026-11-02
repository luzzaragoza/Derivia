"""Derivia: un juego para aprender a derivar e integrar.

Para jugar:  python main.py"""

import os
import sys


def _icono():
    import pygame
    s = pygame.Surface((64, 64), pygame.SRCALPHA)
    try:
        from juego import gato
        cara = gato.superficie(70, "feliz")
        s.blit(cara, cara.get_rect(midtop=(32, 0)))
    except Exception:
        pygame.draw.circle(s, (247, 152, 60), (32, 32), 30)
    return s


def main():
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame

    pygame.mixer.pre_init(22050, -16, 1, 512)
    pygame.init()
    pygame.display.set_caption("Derivia")
    pantalla = pygame.display.set_mode((1280, 720), pygame.SCALED | pygame.RESIZABLE)

    # pantalla de carga mientras se importan SymPy y matplotlib (tardan unos segundos)
    for y in range(720):
        k = y / 719
        pygame.draw.line(pantalla, (int(120 + 86 * k), int(200 + 38 * k), int(234 + 8 * k)), (0, y), (1280, y))
    f = pygame.font.Font(None, 64)
    t = f.render("Cargando Derivia...", True, (64, 46, 40))
    pantalla.blit(t, t.get_rect(center=(640, 360)))
    pygame.display.flip()
    pygame.event.pump()

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from juego.app import App
    pygame.display.set_icon(_icono())

    App(pantalla).correr()
    pygame.quit()


if __name__ == "__main__":
    main()
