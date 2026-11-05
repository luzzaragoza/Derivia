"""La pantalla de resultados al terminar un nivel."""

import math
import random

import pygame

from .. import escenas, paisaje, ui
from .. import lienzo as dibujo
from ..fx import Efectos, rebote
from ..gato import Gato
from ..lienzo import Lienzo
from ..mundos import MUNDOS
from ..sonido import sonidos
from ..ui import (
    ALTO,
    ANCHO,
    ARENA,
    BORDE,
    CORAL,
    MADERA,
    SOL,
    SUAVE,
    TINTA,
    Boton,
)
from .base import CREMA, Escena, centrar


class FinNivel(Escena):
    def __init__(self, app, juego, gano, estrellas=0, nuevo_mundo=None):
        super().__init__(app)
        self.j = juego
        self.gano = gano
        self.estrellas = estrellas
        self.nuevo_mundo = nuevo_mundo
        self.t = 0.0
        self.es_jefe = gano and not juego.practica and juego.jefe
        self.tema = paisaje.tema(juego.mundo.id) if juego.mundo else paisaje.tema("1")
        self.cielo = paisaje.Cielo(semilla=6, tema=self.tema)
        self.mar = paisaje.Mar(520, self.tema["mar"])
        self.fx = Efectos()
        self.gato = Gato(170)
        self.t_fuegos = 0.9
        if self.es_jefe:
            puesta = dict(app.progreso.ropa_puesta)
            puesta["cabeza"] = "corona"      # ¡corona de campeona para la foto!
            self.gato.ropa = tuple(puesta.values())
        self.estrellas_hechas = 0
        self.puntos_vistos = 0
        self.ultimo_tic = 0
        app.progreso.guardar()      # las monedas ya se fueron sumando durante el nivel
        sonidos.agachar(2.5)
        if gano:
            self.gato.reaccionar("festejo", 99)
            self.gato.animo_base = "feliz"
            self.fx.lluvia_confeti(ANCHO, 200 if self.es_jefe else 140)
            sonidos.tocar("jefe" if self.es_jefe else "nivel")
            if self.es_jefe:
                sonidos.agachar(3.5)
        else:
            self.gato.reaccionar("triste", 99)
            self.gato.animo_base = "triste"
            self.fx.lluvia(ANCHO, 90)
            sonidos.tocar("perder")
        cx, y = ANCHO // 2 + 120, 594
        # de izquierda a derecha: revisar errores, mapa y, abajo a la derecha, lo que sigue
        revisar = ("Revisar errores", lambda: app.cambiar(escenas.RevisarErrores(app, juego, self), "fundido"), SOL, TINTA)
        b = [revisar]
        if juego.practica:
            if juego.mundo:
                b.append(("Volver al mapa", lambda: app.cambiar(escenas.Mapa(app, juego.mundo.id), "ola"), CORAL, CREMA))
            else:
                b.append(("Volver al cuaderno", lambda: app.cambiar(escenas.Cuaderno(app)), CORAL, CREMA))
        else:
            m, i = juego.mundo, juego.nivel_idx
            principal = None
            if not gano:
                principal = ("Reintentar", lambda: app.cambiar(escenas.Juego(app, m.id, i, desafio=juego.desafio), "ola"),
                             CORAL, CREMA)
            elif i + 1 < len(m.niveles):
                principal = ("Siguiente nivel", lambda: app.cambiar(escenas.Juego(app, m.id, i + 1), "ola"), CORAL, CREMA)
            elif nuevo_mundo:
                principal = ("¡A la isla nueva!", lambda: app.cambiar(escenas.Mapa(app, nuevo_mundo.id), "ola"), CORAL, CREMA)
            b.append(("Mapa", lambda: app.cambiar(escenas.Mapa(app, m.id), "ola"), ARENA if principal else CORAL,
                      TINTA if principal else CREMA))
            if principal:
                b.append(principal)
        total = len(b) * 230 + (len(b) - 1) * 18
        x = cx - total // 2
        for k, (txt, acc, col, ct) in enumerate(b):
            ultimo = k == len(b) - 1
            boton = Boton((x, y, 230, 62), txt, acc, col, ct, tam=21,
                          tecla=[pygame.K_RETURN, pygame.K_KP_ENTER] if ultimo else None,
                          habilitado=bool(juego.errores_log) if k == 0 else True)
            self.botones.append(boton)
            x += 248

    def atras(self):
        if self.j.practica and not self.j.mundo:
            self.app.cambiar(escenas.Cuaderno(self.app))
        else:
            self.app.cambiar(escenas.Mapa(self.app, self.j.mundo.id), "ola")

    def _pos_estrella(self, k):
        if self.es_jefe:
            return (ANCHO // 2 + 120 + (k - 1) * 96, 228 - (10 if k == 1 else 0))
        return (ANCHO // 2 + 120 + (k - 1) * 110, 200 - (16 if k == 1 else 0))

    def actualizar(self, dt):
        self.t += dt
        self.cielo.actualizar(dt)
        self.mar.actualizar(dt)
        self.fx.actualizar(dt)
        self.gato.actualizar(dt)
        if self.es_jefe:
            self.t_fuegos -= dt
            if self.t_fuegos <= 0:
                x, y = random.uniform(80, ANCHO - 80), random.uniform(50, 300)
                color = random.choice([ui.SOL, CORAL, (140, 220, 255), (190, 150, 240), (150, 230, 140)])
                self.fx.chispas(x, y, 30, color, 380)
                self.fx.chispas(x, y, 10, (255, 255, 255), 160)
                sonidos.tocar("fuegos", 0.35, variar=True)
                self.t_fuegos = random.uniform(0.4, 0.9) if self.t < 7 else random.uniform(1.5, 3)
        if self.gano and not self.j.practica:
            while self.estrellas_hechas < self.estrellas and self.t > 0.6 + self.estrellas_hechas * 0.45:
                x, y = self._pos_estrella(self.estrellas_hechas)
                self.fx.chispas(x, y, 22, ui.SOL, 300)
                self.fx.confeti(x, y, 25, 0.8)
                sonidos.tocar("estrella")
                self.estrellas_hechas += 1
            if self.nuevo_mundo and self.t > 2.2 and not getattr(self, "_desbloqueo_sonado", False):
                self._desbloqueo_sonado = True
                sonidos.tocar("desbloqueo")
        meta = self.j.puntos
        if self.t > 0.4 and self.puntos_vistos < meta:
            self.puntos_vistos = min(meta, self.puntos_vistos + max(1, meta * dt / 1.2))
            if int(self.puntos_vistos) // 15 != self.ultimo_tic:
                self.ultimo_tic = int(self.puntos_vistos) // 15
                sonidos.tocar("tic", 0.4)

    def dibujar(self, sup):
        self.cielo.dibujar(sup)
        if not self.gano:
            gris = Lienzo(*((ANCHO, ALTO)))
            gris.fill((60, 70, 90, 70))
            sup.blit(gris, (0, 0))
        self.mar.dibujar(sup)
        paisaje.isla_tema(sup, (-20, 545), 400, 190, self.tema, semilla=12, palmeras=1)
        self.gato.dibujar(sup, (170, 680))
        # pergamino central
        j = self.j
        card = pygame.Rect(ANCHO // 2 - 240, 40, 720, 530)
        if self.es_jefe:
            self._dibujar_jefe(sup, card)
            return
        ui.tarjeta(sup, card, ui.PERGAMINO, 26, ui.ARENA_OSC, 8)
        if self.gano:
            titulo = "¡Repaso terminado!" if j.practica else "¡Nivel superado!"
            t = ui.texto_borde(titulo, 50, SOL, BORDE, 4)
        else:
            t = ui.texto_borde("Te quedaste sin vidas", 44, CORAL, BORDE, 4)
        esc = rebote(min(1, self.t / 0.5))
        t2 = dibujo.escalar(t, (max(1, int(t.get_width() * esc)), max(1, int(t.get_height() * esc))))
        sup.blit(t2, t2.get_rect(center=(card.centerx, card.top + 64)))
        y = card.top + 110
        if self.gano and not j.practica:
            for k in range(3):
                c = self._pos_estrella(k)
                ui.estrella(sup, c, 44, (236, 226, 204), (200, 184, 160), brillo=False)
                if k < self.estrellas_hechas:
                    edad = self.t - (0.6 + k * 0.45)
                    r = 44 * rebote(min(1, edad / 0.35))
                    ui.estrella(sup, c, r, SOL, BORDE)
            y += 140
            frase = {3: "¡Perfecto! Ni un error ni una pista.", 2: "¡Muy bien! Casi perfecto.",
                     1: "Aprobado. Repetilo para sacar las 3 estrellas."}[self.estrellas]
            centrar(sup, ui.texto(frase, 22, SUAVE, negrita=True), y, card.centerx)
            y += 44
        elif not self.gano:
            centrar(sup, ui.rico("No pasa nada: **así se aprende**. Mirá bien la explicación del error y volvé a intentarlo.",
                                 21, SUAVE, ancho=600, centrado=True, color_negrita=ui.CORAL_OSC), y + 10, card.centerx)
            y += 100
        bien = sum(1 for r in j.resultados if r == "bien")
        datos = [("Monedas", str(int(self.puntos_vistos))), ("Sin errores", f"{bien} de {len(j.ejercicios)}"),
                 ("Errores", str(j.errores)), ("Pistas", str(j.pistas_usadas))]
        for k, (a, b) in enumerate(datos):
            col, fila = k % 2, k // 2
            x = card.centerx - 260 + col * 290
            caja = pygame.Rect(x, y + fila * 70, 250, 60)
            dibujo.rect(sup, (250, 236, 206), caja, border_radius=14)
            dibujo.rect(sup, ui.ARENA_OSC, caja, 2, border_radius=14)
            sup.blit(ui.texto(a, 16, SUAVE, negrita=True), (caja.left + 14, caja.top + 6))
            sup.blit(ui.texto(b, 24, TINTA, negrita=True), (caja.left + 14, caja.top + 26))
            if a == "Monedas":
                ui.moneda(sup, (caja.right - 26, caja.centery), 14)
        y += 150
        mensajes = []
        if j.bonus_desafio:
            mensajes.append(f"¡Te salteaste el **{j.mundo.nombre}**! Todos sus niveles quedan con 3 estrellas "
                            f"y te llevás **+{j.bonus_desafio} monedas** de regalo.")
        if j.puntos:
            mensajes.append(f"Ahora tenés **{self.app.progreso.monedas} monedas** para gastar en la tienda del michi.")
        if self.nuevo_mundo:
            mensajes.append(f"¡Desbloqueaste el **{self.nuevo_mundo.nombre}: {self.nuevo_mundo.tema}**!")
        if j.al_cuaderno:
            mensajes.append(f"{j.al_cuaderno} ejercicio(s) fueron al **cuaderno de errores** para repasar.")
        if j.sacados:
            mensajes.append(f"Sacaste {j.sacados} ejercicio(s) del cuaderno. ¡Ya te salen!")
        for m in mensajes[:2]:
            s = ui.rico(m, 18, TINTA, ancho=660, centrado=True, color_negrita=ui.CORAL_OSC)
            centrar(sup, s, y, card.centerx)
            y += s.get_height() + 2
        self.fx.dibujar(sup)
        self.dibujar_botones(sup)


    def _dibujar_jefe(self, sup, card):
        """Pantalla especial: rayos dorados, trofeo, fuegos artificiales y la isla nueva."""
        j = self.j
        centro = (card.centerx, card.top + 150)
        rayos = Lienzo(*((ANCHO, ALTO)))
        for k in range(16):
            a = self.t * 0.25 + k * math.tau / 16
            p1 = (centro[0] + math.cos(a - 0.09) * 900, centro[1] + math.sin(a - 0.09) * 900)
            p2 = (centro[0] + math.cos(a + 0.09) * 900, centro[1] + math.sin(a + 0.09) * 900)
            dibujo.polygon(rayos, (255, 226, 120, 70), [centro, p1, p2])
        sup.blit(rayos, (0, 0))
        ui.tarjeta(sup, card, (255, 244, 214), 26, ui.SOL_OSC, 8)
        dibujo.rect(sup, ui.SOL, card.inflate(-16, -16), 3, border_radius=20)
        trofeo(sup, (card.centerx, card.top + 10), 92 * rebote(min(1, self.t / 0.6)))
        t = ui.texto_borde("¡Jefe derrotado!", 54, SOL, BORDE, 5)
        esc = rebote(min(1, max(0.01, (self.t - 0.15) / 0.5)))
        t2 = dibujo.escalar(t, (max(1, int(t.get_width() * esc)), max(1, int(t.get_height() * esc))))
        sup.blit(t2, t2.get_rect(center=(card.centerx, card.top + 92)))
        for k in range(3):
            c = self._pos_estrella(k)
            ui.estrella(sup, c, 30, (236, 222, 190), (200, 180, 140), brillo=False)
            if k < self.estrellas_hechas:
                edad = self.t - (0.6 + k * 0.45)
                ui.estrella(sup, c, 30 * rebote(min(1, edad / 0.35)), SOL, BORDE)
        caja = pygame.Rect(card.left + 40, card.top + 228, card.width - 80, 166)
        if self.nuevo_mundo:
            nuevo = paisaje.tema(self.nuevo_mundo.id)
            mini = paisaje.gradiente(caja.width, caja.height, *nuevo["cielo"])
            dibujo.rect(mini, nuevo["mar"][1], (0, caja.height * 0.58, caja.width, caja.height))
            paisaje.isla_tema(mini, (caja.width // 2 - 170, 52), 340, 150, nuevo, semilla=3, palmeras=2)
            sup.blit(mini, caja)
            dibujo.rect(sup, BORDE, caja, 4, border_radius=6)
            et = ui.texto_borde(f"¡Nueva isla: {nuevo['nombre']}!", 28, CREMA, BORDE, 3)
            sup.blit(et, et.get_rect(midtop=(caja.centerx, caja.top + 8)))
            sub = ui.texto_borde(f"{self.nuevo_mundo.nombre}: {self.nuevo_mundo.tema}", 18, SOL, BORDE, 2)
            sup.blit(sub, sub.get_rect(midbottom=(caja.centerx, caja.bottom - 8)))
        else:
            txt = "¡Terminaste Derivia! Ya dominás el cálculo." if j.mundo.id == MUNDOS[-1].id else \
                "¡Isla completada! Repetí el jefe cuando quieras para mejorar tus estrellas."
            s = ui.rico(f"**{txt}**", 26, TINTA, ancho=caja.width - 40, centrado=True, color_negrita=ui.CORAL_OSC)
            sup.blit(s, s.get_rect(center=caja.center))
        datos = [("Monedas", str(int(self.puntos_vistos))), ("Errores", str(j.errores)),
                 ("Sin errores", f"{sum(1 for r in j.resultados if r == 'bien')}/{len(j.ejercicios)}")]
        for k, (a, b_) in enumerate(datos):
            r = pygame.Rect(card.left + 60 + k * 205, card.top + 410, 190, 56)
            dibujo.rect(sup, (250, 232, 190), r, border_radius=14)
            dibujo.rect(sup, ui.SOL_OSC, r, 2, border_radius=14)
            sup.blit(ui.texto(a, 15, SUAVE, negrita=True), (r.left + 12, r.top + 5))
            sup.blit(ui.texto(b_, 22, TINTA, negrita=True), (r.left + 12, r.top + 24))
            if a == "Monedas":
                ui.moneda(sup, (r.right - 24, r.centery), 12)
        msg = ui.rico(f"Ahora tenés **{self.app.progreso.monedas} monedas** para la tienda.", 18, TINTA, ancho=640,
                      centrado=True, color_negrita=ui.CORAL_OSC)
        centrar(sup, msg, card.top + 482, card.centerx)
        self.fx.dibujar(sup)
        self.dibujar_botones(sup)


def trofeo(sup, centro, tam):
    """Copa dorada."""
    if tam < 4:
        return
    cx, cy = centro
    k = tam / 90
    for lado in (-1, 1):
        asa = pygame.Rect(0, 0, 34 * k, 40 * k)
        asa.center = (cx + lado * 38 * k, cy + 4 * k)
        dibujo.ellipse(sup, BORDE, asa.inflate(8, 8), max(3, int(10 * k)))
        dibujo.ellipse(sup, SOL, asa, max(2, int(6 * k)))
    copa = [(cx - 40 * k, cy - 30 * k), (cx + 40 * k, cy - 30 * k), (cx + 30 * k, cy + 18 * k),
            (cx + 10 * k, cy + 30 * k), (cx - 10 * k, cy + 30 * k), (cx - 30 * k, cy + 18 * k)]
    dibujo.polygon(sup, BORDE, copa, max(3, int(8 * k)))
    dibujo.polygon(sup, SOL, copa)
    dibujo.rect(sup, BORDE, (cx - 8 * k - 3, cy + 28 * k, 16 * k + 6, 18 * k))
    dibujo.rect(sup, ui.SOL_OSC, (cx - 8 * k, cy + 28 * k, 16 * k, 16 * k))
    base = pygame.Rect(0, 0, 60 * k, 16 * k)
    base.midtop = (cx, cy + 44 * k)
    dibujo.rect(sup, BORDE, base.inflate(6, 6), border_radius=5)
    dibujo.rect(sup, MADERA, base, border_radius=4)
    ui.estrella(sup, (cx, cy - 4 * k), 15 * k, (255, 248, 220), BORDE, brillo=False)
    dibujo.line(sup, (255, 240, 180), (cx - 28 * k, cy - 22 * k), (cx - 20 * k, cy + 10 * k), max(2, int(4 * k)))
