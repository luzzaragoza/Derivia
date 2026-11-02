"""Derivia: un juego para aprender a derivar e integrar.

Para jugar:  python main.py"""

import os
import sys


def _icono():
    import pygame
    s = pygame.Surface((64, 64), pygame.SRCALPHA)
    pygame.draw.rect(s, (200, 186, 240), (0, 0, 64, 64), border_radius=16)
    f = pygame.font.Font(None, 72)
    t = f.render("f'", True, (112, 88, 196))
    s.blit(t, t.get_rect(center=(32, 34)))
    return s


def main():
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame

    pygame.init()
    pygame.display.set_caption("Derivia")
    pygame.display.set_icon(_icono())
    pantalla = pygame.display.set_mode((1280, 720), pygame.SCALED | pygame.RESIZABLE)

    # pantalla de carga mientras se importan SymPy y matplotlib (tardan unos segundos)
    pantalla.fill((250, 246, 240))
    f = pygame.font.Font(None, 56)
    t = f.render("Cargando Derivia...", True, (112, 88, 196))
    pantalla.blit(t, t.get_rect(center=(640, 360)))
    pygame.display.flip()
    pygame.event.pump()

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from juego.app import App

    App(pantalla).correr()
    pygame.quit()


if __name__ == "__main__":
    main()
