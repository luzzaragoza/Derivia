"""Autoprueba del juego armado:  Derivia.exe --autoprueba [archivo.txt]

Abre el juego como siempre pero sin tocar tu progreso (usa una carpeta temporal), recorre el menú,
el mapa, la tienda y los 49 niveles (con fórmulas, el teclado y los gráficos de regiones),
dibuja unos cuadros de cada uno y se cierra. Sale con código 0 si todo anduvo y 1 si algo falló
(el detalle queda en el archivo, si se pasó uno). La usa GitHub para probar el .exe antes de publicarlo."""

import os
import sys
import tempfile
import time
import traceback


def correr(archivo_log=None):
    os.environ["APPDATA"] = os.environ["XDG_DATA_HOME"] = tempfile.mkdtemp(prefix="derivia_autoprueba_")
    renglones = []
    inicio = time.perf_counter()
    try:
        import pygame

        from . import escenas, ui
        from .app import App, tamaño_inicial
        from .mundos import MUNDOS

        pygame.init()
        app = App(pygame.display.set_mode(tamaño_inicial(), pygame.RESIZABLE))

        def mostrar(escena, cuadros=5):
            app.escena = escena
            for _ in range(cuadros):
                escena.actualizar(1 / 60)
                escena.dibujar(app.lienzo)
                app._componer(1 / 60)
                pygame.display.flip()
                pygame.event.pump()

        mostrar(app.escena)
        for pantalla in (escenas.Menu(app), escenas.Mapa(app), escenas.Tienda(app), escenas.Ayuda(app)):
            mostrar(pantalla)
            renglones.append(f"ok  {type(pantalla).__name__}")
        ui.formula(r"\int_0^1 x^2\,dx = \frac{1}{3}", 40)
        for m in MUNDOS:
            for i, nivel in enumerate(m.niveles):
                t = time.perf_counter()
                mostrar(escenas.Juego(app, m.id, i))
                renglones.append(f"ok  {m.nombre} · {nivel.nombre} ({time.perf_counter() - t:.2f} s)")
        codigo = 0
    except Exception:
        renglones.append(traceback.format_exc())
        codigo = 1
    renglones.append(f"{'TODO OK' if codigo == 0 else 'FALLÓ'} en {time.perf_counter() - inicio:.1f} s")
    texto = "\n".join(renglones)
    if archivo_log:
        with open(archivo_log, "w", encoding="utf-8") as f:
            f.write(texto + "\n")
    elif sys.stdout:
        print(texto)
    return codigo
