"""Efectos visuales: confeti, chispas, textos que flotan, monedas que vuelan y fueguito."""

import math
import random

import pygame

from . import ui

COLORES_CONFETI = [(250, 124, 104), (255, 204, 77), (64, 182, 196), (122, 196, 106), (247, 152, 60),
                   (186, 150, 236), (255, 255, 255)]


def suave(t):
    """Curva de 0 a 1 que arranca y termina despacio."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def rebote(t):
    """0 → 1 pasándose un poquito y volviendo (para cosas que 'aparecen')."""
    t = max(0.0, min(1.0, t))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


class Confeti:
    def __init__(self, x, y, fuerza=1.0, lluvia=False):
        self.x, self.y = x, y
        if lluvia:
            self.vx, self.vy = random.uniform(-40, 40), random.uniform(60, 200)
        else:
            a = random.uniform(-math.pi * 0.95, -math.pi * 0.05)
            v = random.uniform(180, 460) * fuerza
            self.vx, self.vy = math.cos(a) * v, math.sin(a) * v
        self.ang = random.uniform(0, 360)
        self.vang = random.uniform(-500, 500)
        self.color = random.choice(COLORES_CONFETI)
        self.w, self.h = random.randint(6, 11), random.randint(3, 6)
        self.vida = random.uniform(1.6, 2.6) if not lluvia else random.uniform(3, 5)
        self.fase = random.uniform(0, 6.28)

    def actualizar(self, dt):
        self.vida -= dt
        self.vy += 520 * dt
        self.vx *= 0.985
        self.vy = min(self.vy, 260)
        self.x += (self.vx + 40 * math.sin(self.fase + self.vida * 4)) * dt
        self.y += self.vy * dt
        self.ang += self.vang * dt

    def dibujar(self, sup):
        if self.vida <= 0:
            return
        ancho = abs(math.cos(math.radians(self.ang))) * self.w + 1
        r = pygame.Rect(0, 0, ancho, self.h)
        r.center = (self.x, self.y)
        pygame.draw.rect(sup, self.color, r, border_radius=2)


class Chispa:
    def __init__(self, x, y, color=(255, 230, 120), vel=220):
        a = random.uniform(0, math.tau)
        v = random.uniform(vel * 0.4, vel)
        self.x, self.y = x, y
        self.vx, self.vy = math.cos(a) * v, math.sin(a) * v
        self.vida = self.vida0 = random.uniform(0.35, 0.7)
        self.color = color
        self.r = random.uniform(3, 6)

    def actualizar(self, dt):
        self.vida -= dt
        self.vx *= 0.9
        self.vy *= 0.9
        self.x += self.vx * dt
        self.y += self.vy * dt

    def dibujar(self, sup):
        if self.vida <= 0:
            return
        k = self.vida / self.vida0
        r = self.r * (0.4 + 0.6 * k)
        ui.destello(sup, (self.x, self.y), r * 2.2, self.color)


class TextoFlotante:
    def __init__(self, x, y, txt, color, tam=30, sube=60, dur=1.0):
        self.x, self.y0 = x, y
        self.sup = ui.texto_borde(txt, tam, color, (60, 40, 30), 3)
        self.t, self.dur, self.sube = 0.0, dur, sube
        self.vida = dur

    def actualizar(self, dt):
        self.t += dt
        self.vida = self.dur - self.t

    def dibujar(self, sup):
        if self.vida <= 0:
            return
        k = self.t / self.dur
        esc = 0.7 + 0.3 * suave(self.t / 0.35)
        s = self.sup
        if esc != 1:
            s = pygame.transform.smoothscale(s, (max(1, int(s.get_width() * esc)), max(1, int(s.get_height() * esc))))
        s = s.copy()
        s.set_alpha(int(255 * (1 - suave((k - 0.6) / 0.4))))
        sup.blit(s, s.get_rect(center=(self.x, self.y0 - self.sube * suave(k))))


class Volador:
    """Una moneda o estrella que vuela en curva hasta un destino y avisa al llegar."""

    def __init__(self, desde, hasta, al_llegar=None, dur=0.7, demora=0.0, tipo="moneda"):
        self.p0, self.p2 = pygame.Vector2(desde), pygame.Vector2(hasta)
        medio = (self.p0 + self.p2) / 2
        self.p1 = medio + pygame.Vector2(random.uniform(-120, 120), -random.uniform(120, 220))
        self.t = -demora
        self.dur = dur
        self.al_llegar = al_llegar
        self.tipo = tipo
        self.vida = 1

    def actualizar(self, dt):
        self.t += dt
        if self.t >= self.dur and self.vida > 0:
            self.vida = 0
            if self.al_llegar:
                self.al_llegar()

    def dibujar(self, sup):
        if self.vida <= 0 or self.t < 0:
            return
        k = suave(self.t / self.dur)
        p = (1 - k) ** 2 * self.p0 + 2 * (1 - k) * k * self.p1 + k ** 2 * self.p2
        if self.tipo == "moneda":
            ui.moneda(sup, p, 13, giro=self.t * 10)
        else:
            ui.estrella(sup, p, 16, ui.SOL, ui.SOL_OSC)


class Gota:
    def __init__(self, ancho):
        self.x = random.uniform(0, ancho)
        self.y = random.uniform(-200, 0)
        self.v = random.uniform(380, 560)
        self.vida = 4

    def actualizar(self, dt):
        self.y += self.v * dt
        self.vida -= dt

    def dibujar(self, sup):
        pygame.draw.line(sup, (140, 190, 220), (self.x, self.y), (self.x - 3, self.y + 12), 2)


class Efectos:
    def __init__(self):
        self.lista = []

    def confeti(self, x, y, n=40, fuerza=1.0):
        self.lista += [Confeti(x + random.uniform(-30, 30), y, fuerza) for _ in range(n)]

    def lluvia_confeti(self, ancho, n=120):
        for _ in range(n):
            c = Confeti(random.uniform(0, ancho), random.uniform(-400, -10), lluvia=True)
            self.lista.append(c)

    def chispas(self, x, y, n=14, color=(255, 230, 120), vel=220):
        self.lista += [Chispa(x, y, color, vel) for _ in range(n)]

    def texto(self, x, y, txt, color=(255, 220, 90), tam=32, **kw):
        self.lista.append(TextoFlotante(x, y, txt, color, tam, **kw))

    def volar(self, desde, hasta, al_llegar=None, **kw):
        self.lista.append(Volador(desde, hasta, al_llegar, **kw))

    def lluvia(self, ancho, n=70):
        self.lista += [Gota(ancho) for _ in range(n)]

    def actualizar(self, dt):
        for p in self.lista:
            p.actualizar(dt)
        self.lista = [p for p in self.lista if p.vida > 0 and getattr(p, "y", 0) < 900]

    def dibujar(self, sup):
        for p in self.lista:
            p.dibujar(sup)


class Fueguito:
    """Llamita animada para la racha. tam crece con la racha."""

    def __init__(self):
        self.particulas = []
        self.acum = 0.0

    def actualizar(self, dt, intensidad):
        self.acum += dt * (10 + 14 * intensidad)
        while self.acum > 1:
            self.acum -= 1
            self.particulas.append([random.uniform(-5, 5) * (0.6 + intensidad), 0.0,
                                    random.uniform(30, 60) * (0.8 + intensidad * 0.6), 0.0,
                                    random.uniform(0.35, 0.6)])
        for p in self.particulas:
            p[3] += dt
            p[1] -= p[2] * dt
            p[0] *= 0.96
        self.particulas = [p for p in self.particulas if p[3] < p[4]]

    def dibujar(self, sup, base, escala=1.0):
        bx, by = base
        self.t = getattr(self, "t", 0.0) + 1 / 60
        e = escala
        tt = self.t
        # chispitas que suben
        for x, y, _, t, vida in self.particulas:
            k = t / vida
            r = (4 * (1 - k) + 1) * e
            color = (255, 236, 140) if k < 0.4 else ((255, 170, 60) if k < 0.7 else (236, 90, 50))
            pygame.draw.circle(sup, color, (bx + x * e, by - 26 * e + y * e * 0.6), r)
        # la llama (forma de gota que titila)

        def llama(ancho, alto, dy=0):
            punta = (bx + math.sin(tt * 9) * 3 * e, by - alto * e + math.sin(tt * 13) * 2 * e)
            return [(bx - ancho * e, by - 4 * e + dy), (bx - ancho * 1.15 * e, by - alto * 0.45 * e + dy),
                    (bx - ancho * 0.5 * e, by - alto * 0.75 * e + dy), punta,
                    (bx + ancho * 0.55 * e, by - alto * 0.72 * e + dy), (bx + ancho * 1.15 * e, by - alto * 0.42 * e + dy),
                    (bx + ancho * e, by - 4 * e + dy), (bx, by + 3 * e + dy)]
        pygame.draw.polygon(sup, (92, 50, 30), llama(13.5, 34))
        pygame.draw.polygon(sup, (240, 96, 50), llama(11, 30))
        pygame.draw.polygon(sup, (255, 170, 60), llama(7.5, 22))
        pygame.draw.polygon(sup, (255, 236, 140), llama(4, 13))
