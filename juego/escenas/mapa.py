"""El mapa de islas: cada mundo es una isla con un camino de niveles."""

import math
import random

import pygame

from .. import escenas, paisaje, pincel, ui
from .. import lienzo as dibujo
from ..fx import Efectos, suave
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
    DURAZNO,
    GRIS,
    LAVANDA,
    MADERA_OSC,
    SOL,
    SUAVE,
    TARJETA,
    TINTA,
    Boton,
)
from .base import CREMA, Escena


def nombre_corto(m):
    return m.nombre.replace("Mundo ", "")


def _catmull(pts, pasos=24):
    if len(pts) < 2:
        return pts
    p = [pts[0]] + pts + [pts[-1]]
    salida = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = (pygame.Vector2(q) for q in p[i - 1:i + 3])
        for k in range(pasos):
            t = k / pasos
            salida.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                 + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    salida.append(pygame.Vector2(pts[-1]))
    return salida


class Mapa(Escena):
    def __init__(self, app, mundo_id=None):
        super().__init__(app)
        prog = app.progreso
        if mundo_id is None:
            abiertos = [m.id for m in MUNDOS if prog.mundo_desbloqueado(m.id)]
            mundo_id = abiertos[-1] if abiertos else MUNDOS[0].id
        self.sel = [m.id for m in MUNDOS].index(mundo_id)
        self.fondos = {}
        self.humo, self.gotas, self.luciernagas = [], [], []
        self.t_rayo, self.rayo = 4.0, None
        self.gato = Gato(92)
        self.t = 0.0
        self.desliz = None
        self.hover = None
        self.capas = {}
        self.fx = Efectos()
        self.arranque = None
        self.armar()

    @property
    def mundo(self):
        return MUNDOS[self.sel]

    def atras(self):
        self.app.cambiar(escenas.Menu(self.app), "fundido")

    def _nodos(self, m):
        n = len(m.niveles)
        pts = []
        for i in range(n):
            x = 300 + (680 * i / max(1, n - 1))
            y = 470 + 78 * math.sin(i * 1.35 + 0.4)
            pts.append((x, y))
        return pts

    def _actual(self, m):
        """El primer nivel desbloqueado sin aprobar (ahí se sienta el gato)."""
        p = self.app.progreso
        abiertos = [i for i in range(len(m.niveles)) if p.desbloqueado(m.id, i)]
        for i in abiertos:
            if not p.aprobado(m.id, i):
                return i
        return abiertos[-1] if abiertos else None

    def _capa(self, idx):
        """Isla + camino + nodos (lo que no se mueve), cacheado por mundo."""
        if idx in self.capas:
            return self.capas[idx]
        with pincel.siempre():
            self.capas[idx] = self._armar_capa(idx)
        return self.capas[idx]

    def _armar_capa(self, idx):
        m = MUNDOS[idx]
        p = self.app.progreso
        s = Lienzo(*((ANCHO, ALTO)))
        paisaje.isla_tema(s, (100, 205), 1080, 500, paisaje.tema(m.id), semilla=idx * 7 + 1, palmeras=4,
                          palmeras_borde=True)
        nodos = self._nodos(m)
        curva = _catmull(nodos)
        # camino
        por_tramo = (len(curva) - 1) / max(1, len(nodos) - 1)
        for k in range(0, len(curva) - 1, 3):
            tramo = int(k / por_tramo)
            hecho = p.aprobado(m.id, tramo) and tramo + 1 < len(nodos) and p.desbloqueado(m.id, tramo + 1)
            if hecho:
                dibujo.line(s, BORDE, curva[k], curva[min(k + 3, len(curva) - 1)], 14)
            dibujo.circle(s, ui.oscurecer(m.color, 0.6) if hecho else (196, 160, 110), curva[k], 7 if hecho else 5)
        for k in range(0, len(curva) - 1, 3):
            tramo = int(k / por_tramo)
            hecho = p.aprobado(m.id, tramo) and tramo + 1 < len(nodos) and p.desbloqueado(m.id, tramo + 1)
            if hecho:
                dibujo.line(s, ui.aclarar(m.color, 0.1), curva[k], curva[min(k + 3, len(curva) - 1)], 8)
        # nodos
        for i, (nx, ny) in enumerate(nodos):
            nivel = m.niveles[i]
            abierto = p.desbloqueado(m.id, i)
            r = 38 if nivel.jefe else 30
            if nivel.jefe:
                dibujo.line(s, BORDE, (nx + 10, ny - r - 34), (nx + 10, ny - r + 6), 4)
                dibujo.polygon(s, BORDE, [(nx + 12, ny - r - 36), (nx + 46, ny - r - 24), (nx + 12, ny - r - 10)])
                dibujo.polygon(s, CORAL if abierto else GRIS,
                                    [(nx + 13, ny - r - 32), (nx + 40, ny - r - 24), (nx + 13, ny - r - 15)])
            color = (m.color if p.aprobado(m.id, i) else SOL) if abierto else (200, 192, 178)
            bola, mb = pincel.esfera(r, color, BORDE) if pincel.HAY_SKIA else (None, 0)
            if bola is not None:
                s.blit(bola, (nx - r - 2 - mb, ny - r - 2 - mb))
            else:
                dibujo.circle(s, BORDE, (nx, ny + 6), r + 3)
                dibujo.circle(s, BORDE, (nx, ny), r + 3)
                dibujo.circle(s, ui.oscurecer(color, 0.8), (nx, ny + 5), r)
                dibujo.circle(s, color, (nx, ny), r)
                if abierto:
                    dibujo.circle(s, ui.aclarar(color, 0.5), (nx - r * 0.3, ny - r * 0.35), r * 0.22)
            if abierto:
                num = "J" if nivel.jefe else str(i + 1)
                t = ui.texto_borde(num, 30 if nivel.jefe else 26, CREMA, BORDE, 3, sombra=False)
                s.blit(t, t.get_rect(center=(nx, ny + 1)))
                est = p.estrellas(m.id, i)
                for k in range(3):
                    ex = nx + (k - 1) * 24
                    ey = ny + r + 16 - (4 if k == 1 else 0)
                    ui.estrella(s, (ex, ey), 11, SOL if k < est else (238, 228, 210), BORDE, brillo=False)
            else:
                ui.candado(s, (nx, ny), int(r * 0.8), (150, 140, 126))
        return s

    def armar(self):
        p = self.app.progreso
        m = self.mundo
        self.botones = [Boton((20, 18, 128, 50), "Menú", self.atras, DURAZNO, tam=22),
                        self.boton_opciones((ANCHO - 76, 18, 56, 50))]
        txt = "Volver a bloquear" if p.todo_desbloqueado else "Desbloquear todo"
        self.botones.append(Boton((ANCHO - 290, 18, 200, 50), txt, self.alternar_todo, ARENA, tam=17))
        abierto = any(p.desbloqueado(m.id, i) for i in range(len(m.niveles)))
        self.botones.append(Boton((20, 660, 220, 46), "Repasar este mundo", self.repasar_mundo, (186, 150, 236),
                                  tam=17, relieve=4, habilitado=abierto))
        if p.desbloqueado(m.id, 0) and not p.aprobado(m.id, len(m.niveles) - 1):
            self.botones.append(Boton((20, 604, 220, 46), "Desafío del jefe", self.desafio, CORAL, CREMA,
                                      tam=17, relieve=4))
        for d, x in ((-1, ANCHO // 2 - 360), (1, ANCHO // 2 + 310)):
            destino = self.sel + d
            ok = 0 <= destino < len(MUNDOS) and p.mundo_desbloqueado(MUNDOS[destino].id)
            icono = Lienzo(*((30, 30)))
            ui.triangulo(icono, (15, 15), 22, CREMA if ok else (230, 222, 210), d)
            self.botones.append(Boton((x, 100, 50, 50), icono, (lambda d=d: self.mover(d)), LAVANDA,
                                      habilitado=ok, tecla=pygame.K_LEFT if d < 0 else pygame.K_RIGHT,
                                      relieve=5, sonido="salto"))
        # fichas de islas abajo
        n = len(MUNDOS)
        x0 = ANCHO // 2 - (n - 1) * 32
        for k, mm in enumerate(MUNDOS):
            abierto = p.mundo_desbloqueado(mm.id)
            icono = ui.texto(nombre_corto(mm), 17, BORDE if abierto else (170, 160, 150), negrita=True)
            b = Boton((x0 + k * 64 - 26, 666, 52, 40), icono, (lambda k=k: self.ir(k)),
                      mm.color if abierto else (220, 214, 204), habilitado=abierto, radio=14, relieve=4,
                      sonido="salto")
            b.ficha = k
            self.botones.append(b)
        self.nodos = self._nodos(m)
        self.gato_nodo = self._actual(m)

    def repasar_mundo(self):
        """Mezcla de ejercicios de los niveles abiertos de este mundo (sin estrellas, con monedas)."""
        p = self.app.progreso
        m = self.mundo
        abiertos = [i for i in range(len(m.niveles)) if p.desbloqueado(m.id, i)]
        if not abiertos:      # mundo todavía cerrado: no hay nada para repasar
            return
        claves = []
        for k in range(6):
            i = abiertos[k % len(abiertos)] if k < len(abiertos) else random.choice(abiertos)
            gen = random.choice(m.niveles[i].generadores)
            claves.append({"mundo": m.id, "nivel": i, "gen": gen, "semilla": random.randrange(10**9)})
        errores = [c["clave"] for c in p.cuaderno if c["clave"]["mundo"] == m.id]
        if errores:
            claves[random.randrange(len(claves))] = random.choice(errores)
        random.shuffle(claves)
        self.app.cambiar(escenas.Juego(self.app, m.id, None, practica=claves, titulo_practica=f"Repaso · {m.tema}"), "ola")

    def desafio(self):
        self.app.cambiar(escenas.DesafioIntro(self.app, self, self.mundo), None)

    def alternar_todo(self):
        p = self.app.progreso
        p.todo_desbloqueado = not p.todo_desbloqueado
        p.guardar()
        self.capas = {}
        self.armar()

    def mover(self, d):
        self.ir(self.sel + d)

    def ir(self, destino):
        if destino == self.sel or not (0 <= destino < len(MUNDOS)):
            return
        if not self.app.progreso.mundo_desbloqueado(MUNDOS[destino].id):
            return
        direccion = 1 if destino > self.sel else -1
        self.desliz = [0.0, direccion, self.sel]
        self.sel = destino
        self.humo, self.gotas, self.luciernagas, self.rayo = [], [], [], None
        self.hover = None
        self.armar()
        self.gato.reaccionar("feliz", 0.8)

    def _nodo_en(self, pos):
        for i, (nx, ny) in enumerate(self.nodos):
            r = 40 if self.mundo.niveles[i].jefe else 32
            if (pos[0] - nx) ** 2 + (pos[1] - ny) ** 2 <= r * r:
                return i
        return None

    def evento(self, e):
        if self.arranque:
            return False
        if super().evento(e):
            return True
        if self.desliz:
            return False
        if e.type == pygame.MOUSEMOTION:
            nuevo = self._nodo_en(e.pos)
            if nuevo is not None and nuevo != self.hover:
                sonidos.tocar("hover")
            self.hover = nuevo
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            i = self._nodo_en(e.pos)
            if i is not None:
                if self.app.progreso.desbloqueado(self.mundo.id, i):
                    self.arrancar(i)
                else:
                    sonidos.tocar("mal", 0.5)
                    self.gato.reaccionar("triste", 0.8)
                return True
        return False

    def arrancar(self, i):
        """El gato salta al nivel, gira y suena la fanfarria; después arranca."""
        nx, ny = self.nodos[i]
        if self.gato_nodo is not None:
            gx, gy = self.nodos[self.gato_nodo]
            desde = (gx - 58, gy + 30)
        else:
            desde = (nx - 58, ny + 30)
        self.arranque = dict(t=0.0, i=i, desde=desde, hasta=(nx, ny - 22), festejo=False, listo=False)
        self.hover = None
        sonidos.tocar("salto")
        sonidos.tocar("inicio")
        sonidos.agachar(1.8)
        self.gato.reaccionar("feliz", 3, saltar=False)

    def actualizar(self, dt):
        self.t += dt
        for cielo, mar in self.fondos.values():
            cielo.actualizar(dt)
            mar.actualizar(dt)
        self._efectos_tema(dt)
        self.gato.actualizar(dt)
        self.fx.actualizar(dt)
        a = self.arranque
        if a:
            a["t"] += dt
            if a["t"] >= 0.42 and not a["festejo"]:
                a["festejo"] = True
                nx, ny = self.nodos[a["i"]]
                self.fx.confeti(nx, ny - 30, 50, 1.1)
                self.fx.chispas(nx, ny, 20, ui.SOL, 320)
                nivel = self.mundo.niveles[a["i"]]
                rotulo = "¡Jefe!" if nivel.jefe else f"¡Nivel {a['i'] + 1}!"
                self.fx.texto(nx, ny - 150, rotulo, SOL, 46, sube=30, dur=1.1)
                self.gato.reaccionar("festejo", 3)
            if a["t"] >= 1.3 and not a["listo"]:
                a["listo"] = True
                self.app.cambiar(escenas.Juego(self.app, self.mundo.id, a["i"]), "ola")
        if self.desliz:
            self.desliz[0] += dt / 0.5
            if self.desliz[0] >= 1:
                self.desliz = None

    def _tooltip(self, sup, i):
        m = self.mundo
        nivel = m.niveles[i]
        nx, ny = self.nodos[i]
        abierto = self.app.progreso.desbloqueado(m.id, i)
        w = 330
        titulo = ui.texto(nivel.nombre, 22, TINTA, negrita=True)
        desc = ui.rico(nivel.descripcion, 16, SUAVE, ancho=w - 30)
        etiquetas = ["Opciones" if nivel.modo == "opciones" else "Tipeo"]
        if nivel.tiempo:
            etiquetas.append(f"{int(nivel.tiempo)} s")
        if nivel.jefe:
            etiquetas.append("JEFE")
        pie = "¡Clic para jugar!" if abierto else "Pasá el nivel anterior para abrirlo"
        h = 26 + titulo.get_height() + desc.get_height() + 60
        rect = pygame.Rect(0, 0, w, h)
        rect.midbottom = (nx, ny - 54)
        if rect.top < 160:
            rect.midtop = (nx, ny + 66)
        rect.clamp_ip(pygame.Rect(10, 10, ANCHO - 20, ALTO - 20))
        ui.globo(sup, rect, (nx, ny - 34 if rect.bottom < ny else ny + 40), TARJETA)
        y = rect.top + 12
        sup.blit(titulo, (rect.left + 16, y))
        y += titulo.get_height() + 4
        sup.blit(desc, (rect.left + 16, y))
        y += desc.get_height() + 8
        x = rect.left + 16
        for et in etiquetas:
            t = ui.texto(et, 14, TINTA if et != "JEFE" else CREMA, negrita=True)
            r = pygame.Rect(x, y, t.get_width() + 16, 22)
            dibujo.rect(sup, CORAL if et == "JEFE" else ARENA, r, border_radius=11)
            sup.blit(t, t.get_rect(center=r.center))
            x += r.width + 6
        pie_s = ui.texto(pie, 15, ui.CORAL_OSC if abierto else SUAVE, negrita=True)
        sup.blit(pie_s, (rect.left + 16, y + 28))

    # ------------------------------------------------ fondo de cada isla
    def _fondo(self, idx):
        if idx not in self.fondos:
            t = paisaje.tema(MUNDOS[idx].id)
            self.fondos[idx] = (paisaje.Cielo(semilla=4, nubes=5, tema=t),
                                paisaje.Mar(215, [ui.aclarar(t["mar"][0], 0.1)] + t["mar"]))
        return self.fondos[idx]

    def _dibujar_fondo(self, sup, idx):
        cielo, mar = self._fondo(idx)
        cielo.dibujar(sup)
        mar.dibujar(sup)

    def _efectos_tema(self, dt):
        deco = paisaje.tema(self.mundo.id)["deco"]
        if deco == "volcan":
            if random.random() < dt * 5:
                cx, cy = paisaje.volcan_cima((100, 205), 1080, 500)
                self.humo.append([cx + random.uniform(-8, 8), cy, random.uniform(10, 16), 0.0])
            for h in self.humo:
                h[1] -= 26 * dt
                h[0] += 10 * dt
                h[2] += 9 * dt
                h[3] += dt
            self.humo = [h for h in self.humo if h[3] < 3.5]
        elif deco == "tormenta":
            self.t_rayo -= dt
            if self.t_rayo <= 0:
                x = random.uniform(200, ANCHO - 200)
                puntos = [(x, 0)]
                for k in range(1, 7):
                    puntos.append((puntos[-1][0] + random.uniform(-40, 40), k * 34))
                self.rayo = [puntos, 0.35]
                self.t_rayo = random.uniform(4, 8)
                sonidos.tocar("trueno", 0.5)
            if self.rayo:
                self.rayo[1] -= dt
                if self.rayo[1] <= 0:
                    self.rayo = None
            for _ in range(int(dt * 220) + 1):
                self.gotas.append([random.uniform(0, ANCHO + 100), random.uniform(-30, 0)])
            for g in self.gotas:
                g[0] -= 140 * dt
                g[1] += 620 * dt
            self.gotas = [g for g in self.gotas if g[1] < ALTO]
        elif deco == "calavera":
            if not self.luciernagas:
                self.luciernagas = [[random.uniform(150, 1130), random.uniform(300, 640), random.uniform(0, 6.28)]
                                    for _ in range(16)]
            for f in self.luciernagas:
                f[2] += dt

    def _dibujar_efectos_tema(self, sup):
        deco = paisaje.tema(self.mundo.id)["deco"]
        if deco == "volcan":
            for x, y, r, edad in self.humo:
                capa = Lienzo(int(r * 2) + 2, int(r * 2) + 2)
                dibujo.circle(capa, (120, 110, 120, int(150 * (1 - edad / 3.5))), (r + 1, r + 1), r)
                sup.blit(capa, (x - r, y - r))
        elif deco == "tormenta":
            for x, y in self.gotas:
                dibujo.line(sup, (170, 190, 220), (x, y), (x - 4, y + 12), 1)
            if self.rayo:
                puntos, vida = self.rayo
                flash = Lienzo(*((ANCHO, ALTO)))
                flash.fill((255, 255, 255, int(110 * vida / 0.35)))
                sup.blit(flash, (0, 0))
                dibujo.lines(sup, (255, 250, 200), False, puntos, 5)
                dibujo.lines(sup, (255, 255, 255), False, puntos, 2)
        elif deco == "calavera":
            for x, y, fase in self.luciernagas:
                px = x + math.sin(fase * 0.7) * 30
                py = y + math.cos(fase * 0.9) * 18
                brillo = 0.5 + 0.5 * math.sin(fase * 3)
                halo = Lienzo(*((24, 24)))
                dibujo.circle(halo, (200, 255, 140, int(90 * brillo)), (12, 12), 11)
                sup.blit(halo, (px - 12, py - 12))
                dibujo.circle(sup, (230, 255, 170), (px, py), 2.5)
            niebla = paisaje.niebla()
            desplaza = (self.t * 18) % ANCHO
            sup.blit(niebla, (desplaza - ANCHO, 560))
            sup.blit(niebla, (desplaza, 560))

    def dibujar(self, sup):
        if self.desliz:
            self._dibujar_fondo(sup, self.desliz[2])
            nuevo = Lienzo(ANCHO, ALTO, alfa=False)
            self._dibujar_fondo(nuevo, self.sel)
            nuevo.set_alpha(int(255 * suave(self.desliz[0])))
            sup.blit(nuevo, (0, 0))
        else:
            self._dibujar_fondo(sup, self.sel)
        if self.desliz:
            k = suave(self.desliz[0])
            d = self.desliz[1]
            sup.blit(self._capa(self.desliz[2]), (-d * ANCHO * k, 0))
            sup.blit(self._capa(self.sel), (d * ANCHO * (1 - k), 0))
        else:
            sup.blit(self._capa(self.sel), (0, 0))
            m = self.mundo
            a = self.arranque
            if a:
                nx, ny = self.nodos[a["i"]]
                r = 44 + 10 * abs(math.sin(a["t"] * 9))
                dibujo.circle(sup, SOL, (nx, ny), r, 6)
                k = suave(min(1.0, a["t"] / 0.42))
                x = a["desde"][0] + (a["hasta"][0] - a["desde"][0]) * k
                y = a["desde"][1] + (a["hasta"][1] - a["desde"][1]) * k - math.sin(k * math.pi) * 120
                giro = 360 * suave((a["t"] - 0.5) / 0.45) if a["t"] > 0.5 else 0
                self.gato.dibujar(sup, (x, y), angulo=-giro)
            elif self.gato_nodo is not None:
                # anillo que late en el nivel actual
                nx, ny = self.nodos[self.gato_nodo]
                r = (40 if m.niveles[self.gato_nodo].jefe else 32) + 6 + 4 * math.sin(self.t * 4)
                dibujo.circle(sup, CREMA, (nx, ny), r, 4)
                self.gato.dibujar(sup, (nx - 58, ny + 30))
            self._dibujar_efectos_tema(sup)
            if self.hover is not None:
                nx, ny = self.nodos[self.hover]
                dibujo.circle(sup, (255, 255, 255), (nx, ny), 44, 3)
        # cartel del mundo
        m = self.mundo
        tengo, total = self.app.progreso.estrellas_mundo(m.id)
        rect = pygame.Rect(ANCHO // 2 - 290, 86, 580, 80)
        ui.tabla_madera(sup, rect)
        t1 = ui.texto_borde(f"{m.nombre.upper()} · {paisaje.tema(m.id)['nombre'].upper()}", 17, SOL, MADERA_OSC, 2)
        t2 = ui.texto_borde(m.tema, 30, CREMA, MADERA_OSC, 3)
        sup.blit(t1, t1.get_rect(midtop=(rect.centerx, rect.top + 8)))
        sup.blit(t2, t2.get_rect(midtop=(rect.centerx, rect.top + 28)))
        ui.estrella(sup, (rect.right - 70, rect.centery), 13, SOL, BORDE)
        st = ui.texto_borde(f"{tengo}/{total}", 17, CREMA, MADERA_OSC, 2)
        sup.blit(st, st.get_rect(midleft=(rect.right - 52, rect.centery)))
        self.dibujar_botones(sup)
        for b in self.botones:
            if getattr(b, "ficha", None) == self.sel:
                dibujo.rect(sup, CREMA, b.rect.inflate(10, 12).move(0, 2), 3, border_radius=16)
        if self.hover is not None and not self.desliz and not self.arranque:
            self._tooltip(sup, self.hover)
        self.fx.dibujar(sup)
