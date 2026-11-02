"""Las pantallas del juego (estilo aventura: islas, mar, madera y pergamino)."""

import math
import random

import pygame

from . import gato as modulo_gato
from . import paisaje, pincel, ropa, ui
from . import lienzo as dibujo
from .lienzo import Lienzo
from .fx import Efectos, Fueguito, rebote, suave
from .gato import Gato
from .mate import (C, ERRORES, ErrorEntrada, casi_igual, diagnosticar, diagnosticar_primitiva, equivalentes,
                   es_primitiva, parsear, tex)
from .mate import x as VAR_X
from .mate import y as VAR_Y
from .mate import z as VAR_Z
from .mundos import MUNDOS, generar, generar_nivel, mundo_por_id
from .sonido import sonidos
from .ui import (ALTO, ANCHO, ARENA, ARENA_OSC, BORDE, CORAL, DURAZNO, GRIS, LAVANDA, LAVANDA_OSC,
                 MADERA, MADERA_OSC, MENTA_OSC, ROSA_OSC, SOL, SOL_OSC, SUAVE, TARJETA, TINTA, Boton, CampoTexto)

CREMA = (255, 248, 230)
FRASES_BIEN = ["¡Bien!", "¡Excelente!", "¡Eso!", "¡Perfecto!", "¡Muy bien!", "¡Genial!", "¡Impecable!", "¡Miau, sí!"]
FRASES_MAL = ["Uy...", "Casi...", "Mmm, no.", "¡Ups!"]
FRASES_INICIO = ["¡Vamos! Yo te acompaño.", "¡A practicar!", "¡Miau! ¿Arrancamos?", "Tranqui, de a un paso."]


def centrar(sup, s, y, x=None):
    r = s.get_rect(midtop=(x if x is not None else ANCHO // 2, y))
    sup.blit(s, r)
    return r


def letrero(sup, rect, texto_s, tam=26):
    """Cartel de madera con un título."""
    rect = pygame.Rect(rect)
    ui.tabla_madera(sup, rect)
    t = ui.texto_borde(texto_s, tam, CREMA, MADERA_OSC, 2)
    sup.blit(t, t.get_rect(center=rect.center))


def dibujar_monedero(sup, monedas, arriba_derecha):
    """Cartelito de madera con las monedas que tenés."""
    t = ui.texto_borde(str(monedas), 24, CREMA, MADERA_OSC, 2)
    r = pygame.Rect(0, 0, t.get_width() + 70, 50)
    r.topright = arriba_derecha
    ui.tabla_madera(sup, r, radio=14)
    ui.moneda(sup, (r.left + 28, r.centery), 15)
    sup.blit(t, t.get_rect(midleft=(r.left + 50, r.centery)))
    return r


_VELO = {}


def _velo_logica():
    """Un tinte lila suave para las preguntas de pensar (así se distinguen de las de calcular)."""
    if "v" not in _VELO:
        v = Lienzo(*((ANCHO, ALTO)))
        v.fill((186, 150, 236, 34))
        _VELO["v"] = v
    return _VELO["v"]


def cartelito_consigna(logica):
    """PENSÁ (lamparita) o CALCULÁ (lápiz), para que se note qué tipo de consigna es."""
    clave = ("cartel", logica)
    if clave in _VELO:
        return _VELO[clave]
    texto = "PENSÁ" if logica else "CALCULÁ"
    color = (150, 110, 220) if logica else ui.CORAL
    t = ui.texto(texto, 15, CREMA, negrita=True)
    s = Lienzo(t.get_width() + 44, 30)
    dibujo.rect(s, BORDE, s.get_rect(), border_radius=15)
    dibujo.rect(s, color, s.get_rect().inflate(-4, -4), border_radius=13)
    if logica:   # lamparita
        dibujo.circle(s, (255, 236, 140), (17, 13), 7)
        dibujo.rect(s, (230, 230, 230), (14, 19, 7, 5), border_radius=2)
    else:        # lápiz
        dibujo.line(s, (255, 214, 102), (10, 22), (22, 9), 5)
        dibujo.polygon(s, (255, 236, 200), [(8, 25), (10, 19), (14, 23)])
    s.blit(t, (32, 15 - t.get_height() // 2))
    _VELO[clave] = s
    return s


def flecha_reiniciar(sup, centro, tam, color):
    cx, cy = centro
    r = pygame.Rect(0, 0, tam, tam)
    r.center = centro
    dibujo.arc(sup, color, r, 0.6, math.tau - 0.2, 4)
    dibujo.polygon(sup, color, [(cx + tam * 0.5, cy - tam * 0.42), (cx + tam * 0.52, cy), (cx + tam * 0.12, cy - tam * 0.14)])


def nombre_corto(m):
    return m.nombre.replace("Mundo ", "")


class Escena:
    permite_m = True
    musica = "isla"

    def __init__(self, app):
        self.app = app
        self.botones = []

    def evento(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.atras()
            return True
        for b in list(self.botones):
            if b.evento(e):
                return True
        return False

    def atras(self):
        pass

    def actualizar(self, dt):
        pass

    def dibujar(self, sup):
        pass

    def dibujar_botones(self, sup):
        for b in self.botones:
            b.dibujar(sup)

    def boton_opciones(self, rect):
        icono = Lienzo(*((40, 40)))
        ui.engranaje(icono, (20, 20), 32, BORDE)
        return Boton(rect, icono, self.abrir_opciones, ARENA, relieve=4)

    def abrir_opciones(self):
        self.app.cambiar(Opciones(self.app, self), None)

    def armar(self):
        pass


# =============================================================== MENÚ

class Menu(Escena):
    def __init__(self, app):
        super().__init__(app)
        self.cielo = paisaje.Cielo(semilla=2)
        self.mar = paisaje.Mar(470)
        self.gato = Gato(170)
        self.gato.reaccionar("feliz", 1.2)
        self.t = 0.0
        self.armar()

    def armar(self):
        app = self.app
        n = len(app.progreso.cuaderno)
        x, y = 690, 236
        self.botones = [
            Boton((x, y, 400, 74), "¡Jugar!", self.jugar, CORAL, CREMA, tam=34, tecla=[pygame.K_RETURN, pygame.K_KP_ENTER]),
            Boton((x, y + 92, 400, 56), f"Tienda de {app.progreso.nombre_gato}" if app.progreso.nombre_gato
                  else "Tienda del michi", lambda: app.cambiar(Tienda(app), "ola"), (255, 170, 200), tam=24),
            Boton((x, y + 162, 400, 56), f"Cuaderno de errores ({n})", lambda: app.cambiar(Cuaderno(app)), SOL, tam=23),
            Boton((x, y + 232, 400, 56), "Cómo escribir fórmulas", lambda: app.cambiar(Ayuda(app)), LAVANDA, tam=23),
            Boton((x, y + 302, 193, 56), "Opciones", self.abrir_opciones, ARENA, tam=22),
            Boton((x + 207, y + 302, 193, 56), "Salir", app.salir, ARENA, tam=22),
        ]

    def jugar(self):
        self.app.cambiar(Mapa(self.app), "ola")

    def atras(self):
        self.app.salir()

    def evento(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.rect_nombre.collidepoint(e.pos):
            sonidos.tocar("click")
            self.app.cambiar(NombreGato(self.app), "fundido")
            return True
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.rect_gato.collidepoint(e.pos):
            sonidos.tocar("miau")
            self.gato.reaccionar(random.choice(["feliz", "sorpresa", "festejo"]), 1.2)
            return True
        return super().evento(e)

    rect_gato = pygame.Rect(150, 420, 220, 240)
    rect_nombre = pygame.Rect(0, 0, 0, 0)

    def actualizar(self, dt):
        self.t += dt
        self.cielo.actualizar(dt)
        self.mar.actualizar(dt)
        self.gato.actualizar(dt)
        if self.botones[0].rect.collidepoint(dibujo.raton()) and self.gato.animo == "normal":
            self.gato.reaccionar("feliz", 0.8, saltar=False)

    def dibujar(self, sup):
        self.cielo.dibujar(sup)
        self.mar.dibujar(sup)
        paisaje.dibujar_isla(sup, (math.sin(self.t * 0.8) * 2, 470), 520, 230, ui.PASTO, semilla=5, palmeras=2)
        paisaje.dibujar_isla(sup, (1040, 610), 220, 110, ui.PASTO, semilla=9, palmeras=1)
        self.gato.dibujar(sup, (260, 640))
        nombre = self.app.progreso.nombre_gato or "¿Nombre?"
        t = ui.texto_borde(nombre, 22, CREMA, MADERA_OSC, 2)
        self.rect_nombre = pygame.Rect(0, 0, t.get_width() + 40, 42)
        self.rect_nombre.midtop = (260, 666)
        encima = self.rect_nombre.collidepoint(dibujo.raton())
        ui.tabla_madera(sup, self.rect_nombre.move(0, -2 if encima else 0), radio=12)
        sup.blit(t, t.get_rect(center=self.rect_nombre.move(0, -2 if encima else 0).center))
        # título
        titulo = ui.texto_borde("Derivia", 128, SOL, BORDE, 6)
        y = 40 + math.sin(self.t * 1.6) * 6
        sup.blit(titulo, titulo.get_rect(midtop=(430, y)))
        sub = ui.texto_borde("Derivadas e integrales, isla por isla", 26, CREMA, BORDE, 3)
        sup.blit(sub, sub.get_rect(midtop=(430, y + 168)))
        dibujar_monedero(sup, self.app.progreso.monedas, (ANCHO - 24, 24))
        self.dibujar_botones(sup)


# =============================================================== MAPA (camino)

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
        self.app.cambiar(Menu(self.app), "fundido")

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
        self.botones.append(Boton((20, 660, 220, 46), "Repasar este mundo", self.repasar_mundo, (186, 150, 236),
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
        claves = []
        for k in range(6):
            i = abiertos[k % len(abiertos)] if k < len(abiertos) else random.choice(abiertos)
            gen = random.choice(m.niveles[i].generadores).__name__
            claves.append({"mundo": m.id, "nivel": i, "gen": gen, "semilla": random.randrange(10**9)})
        errores = [c["clave"] for c in p.cuaderno if c["clave"]["mundo"] == m.id]
        if errores:
            claves[random.randrange(len(claves))] = random.choice(errores)
        random.shuffle(claves)
        self.app.cambiar(Juego(self.app, m.id, None, practica=claves, titulo_practica=f"Repaso · {m.tema}"), "ola")

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
                self.app.cambiar(Juego(self.app, self.mundo.id, a["i"]), "ola")
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


# =============================================================== JUEGO

# (etiqueta en LaTeX, lo que se inserta, cuántos lugares vuelve el cursor) — como en la calculadora
TECLADO = [("x^{2}", "^2", 0), ("x^{n}", "^()", 1), (r"\sqrt{x}", "raiz()", 1), (r"\sqrt[n]{x}", "raiz3()", 1),
           (r"(\;\;)", "()", 1), ("+", "+", 0), ("-", "-", 0), (r"\cdot", "*", 0), ("/", "/", 0),
           (r"\mathrm{sen}", "sen()", 1), (r"\cos", "cos()", 1), ("e^{x}", "e^()", 1), (r"\ln", "ln()", 1)]
FUNCIONES_TECLADO = (r"\mathrm{sen}", r"\cos", "e^{x}", r"\ln")
NUMEROS = ["7", "8", "9", "4", "5", "6", "1", "2", "3", "0", ","]

PIE_GATO = (96, ALTO - 8)
BOCA_GATO = (150, ALTO - 120)
X_GLOBO = 196


class Juego(Escena):
    musica = "estudio"

    def __init__(self, app, mundo_id, nivel_idx, practica=None, titulo_practica=None):
        super().__init__(app)
        self.practica = practica is not None
        self.practica_claves = practica
        self.repasos = set()
        self.errores_log = []
        if self.practica:
            # repaso del cuaderno (mundo_id None) o repaso de un mundo entero
            self.mundo = mundo_por_id(mundo_id) if mundo_id else None
            self.nivel = None
            self.ejercicios = [generar(c["mundo"], c["nivel"], c["gen"], c["semilla"]) for c in practica]
            for k, ej in enumerate(self.ejercicios):
                if k:   # en los repasos tampoco se repiten las preguntas de andamiaje
                    ej.pasos = [p for p in ej.pasos if not p.repetitivo] or ej.pasos
            self.vidas_max = 5
            self.titulo = titulo_practica or "Repaso del cuaderno"
            self.color = self.mundo.color if self.mundo else ui.ROSA
        else:
            self.mundo = mundo_por_id(mundo_id)
            self.nivel = self.mundo.niveles[nivel_idx]
            self.nivel_idx = nivel_idx
            self.ejercicios = generar_nivel(mundo_id, nivel_idx)
            self._meter_repaso()
            self.vidas_max = self.nivel.vidas
            self.titulo = f"{self.mundo.nombre} · {self.nivel.nombre}"
            self.color = self.mundo.color
        self.vidas = self.vidas_max
        self.i = 0
        self.puntos = 0
        self.puntos_vistos = 0.0
        self.racha = 0
        self.errores = 0
        self.pistas_usadas = 0
        self.resultados = []
        self.al_cuaderno = 0
        self.sacados = 0
        self.fx = Efectos()
        self.fuego = Fueguito()
        self.gato = Gato(128)
        self.gato.reaccionar("feliz", 1.0)
        self.charla = ("¡Es un jefe! Acá no hay pistas, pero vos podés." if self.jefe
                       else random.choice(FRASES_INICIO))
        self.t_charla = 3.5
        self.sacudir = 0
        self.t = 0.0
        self.t_entrada = 0.0
        self.t_moneda = 1.0
        self.t_corazon = 10.0
        self.ultimo_tic = None
        self.monedas_vistas = float(app.progreso.monedas)
        self.salteo_usado = False
        self.campo = CampoTexto((0, 0, 560, 58), al_enter=self.comprobar, al_cambiar=self._previsualizar)
        pygame.key.start_text_input()
        self.empezar_ejercicio()

    @property
    def permite_m(self):
        return not (self.estado == "pregunta" and self.paso.tipo == "expresion")

    # ---------------------------------------------- armado
    def _meter_repaso(self):
        """Mete un ejercicio del cuaderno de errores entre los del nivel."""
        prog = self.app.progreso
        if self.mundo.id in prog.repaso_mundos:
            return      # un solo repaso por mundo (para practicar más está el cuaderno)
        candidatos = [c for c in prog.cuaderno if c["clave"]["mundo"] == self.mundo.id]
        if candidatos:
            c = random.choice(candidatos)["clave"]
            prog.repaso_mundos.append(self.mundo.id)
            prog.guardar()
            try:
                ej = generar(c["mundo"], c["nivel"], c["gen"], c["semilla"])
            except Exception:
                return
            pos = random.randint(1, len(self.ejercicios))
            self.ejercicios.insert(pos, ej)
            self.repasos.add(pos)

    @property
    def jefe(self):
        return bool(self.nivel and self.nivel.jefe)

    @property
    def tiempo(self):
        return self.nivel.tiempo if self.nivel else None

    def empezar_ejercicio(self):
        self.ej = self.ejercicios[self.i]
        self.paso_i = 0
        self.fallo_ej = False
        self.pasos_revelados = set()
        self.t_entrada = 0.0
        self.empezar_paso()

    def empezar_paso(self):
        self.paso = self.ej.pasos[self.paso_i]
        self.intentos = 0
        self.pistas_vistas = 0
        self.feedback = None
        self.estado = "pregunta"     # pregunta | bien | revelado | sin_vidas
        self.marcadas = {}
        self.t_marcas = {}
        self.t_paso = 0
        self.auto_t = None
        self.preview = None
        self.ultimo_tic = None
        self.campo.poner("")
        self.es_logica = self.paso.tipo == "opcion" and self.paso.esperado is None
        self.musica = "pensar" if self.es_logica else "estudio"
        sonidos.musica(self.musica)
        self.armar()

    def _respuesta_tex(self):
        p = self.paso
        if p.esperado is not None:
            return f"${p.prefijo} {p.mostrar or tex(p.esperado)}$"
        for o in p.opciones:
            if o.correcta:
                return f"${o.tex}$" if o.tex else f"**{o.texto}**"
        return ""

    def _teclado(self):
        teclas = list(TECLADO)
        extra = []
        if VAR_Y in self.paso.variables:
            extra.append(("y", "y", 0))
        if VAR_Z in self.paso.variables:
            extra.append(("z", "z", 0))
        if self.paso.chequeo == "primitiva":
            extra.append((r"+\,C", "+C", 0))
        if self.paso.chequeo == "numero":
            extra = [(r"\pi", "pi", 0), ("e", "e", 0)]
            teclas = [t for t in teclas if t[0] not in FUNCIONES_TECLADO]
        return teclas + extra

    def alternar_numeros(self):
        self.app.progreso.teclado_numerico = not self.app.progreso.teclado_numerico
        self.app.progreso.guardar()
        self.armar()

    def reiniciar(self):
        """Empezar el nivel de nuevo (por ejemplo, para hacerlo perfecto)."""
        if self.practica:
            nuevo = Juego(self.app, self.mundo.id if self.mundo else None, None, practica=self.practica_claves,
                          titulo_practica=self.titulo)
        else:
            nuevo = Juego(self.app, self.mundo.id, self.nivel_idx)
        self.app.cambiar(nuevo, "fundido")

    COSTO_SALTEAR = 30

    def _boton_saltear(self, rect):
        """Saltear el ejercicio: una vez por nivel, cuesta monedas (en los jefes no se puede)."""
        if self.jefe:
            txt, ok = "Saltear: no (jefe)", False
        elif self.salteo_usado:
            txt, ok = "Ya salteaste uno", False
        else:
            txt = f"Saltear (−{self.COSTO_SALTEAR})"
            ok = self.app.progreso.monedas >= self.COSTO_SALTEAR
        return Boton(rect, txt, self.saltear, (186, 150, 236), TINTA, tam=17, habilitado=ok, sonido="salto")

    def saltear(self):
        if self.salteo_usado or self.jefe or self.estado != "pregunta":
            return
        prog = self.app.progreso
        if prog.monedas < self.COSTO_SALTEAR:
            return
        prog.monedas -= self.COSTO_SALTEAR
        self.salteo_usado = True
        self.fx.texto(self.pos_monedas[0] + 30, self.pos_monedas[1] + 30, f"−{self.COSTO_SALTEAR}", ui.CORAL, 24,
                      sube=-20, dur=1.0)
        prog.anotar_error(self.ej.clave, self.ej.formula)     # para repasarlo después
        self.al_cuaderno += 1
        self.resultados.append("salteado")
        self.racha = 0
        self.gato.reaccionar("sorpresa", 1.0, saltar=False)
        self.i += 1
        if self.i >= len(self.ejercicios):
            self.terminar_nivel()
        else:
            self.empezar_ejercicio()

    def _boton_pista(self, rect):
        """El botón de pista siempre está, así se entiende cuándo se puede usar."""
        n, vistas = len(self.paso.pistas), self.pistas_vistas
        if self.jefe:
            txt, ok = "Sin pistas (jefe)", False
        elif not n:
            txt, ok = "Sin pistas acá", False
        elif vistas >= n:
            txt, ok = "No hay más pistas", False
        else:
            txt, ok = ("Pista (−5 monedas)" if n == 1 else f"Pista {vistas + 1}/{n} (−5 monedas)"), True
        return Boton(rect, txt, self.pista, SOL, TINTA, tam=19, habilitado=ok, sonido="pista")

    def armar(self):
        """Calcula la ubicación de todo según el estado actual."""
        icono = Lienzo(*((36, 36)))
        flecha_reiniciar(icono, (18, 18), 26, BORDE)
        self.botones = [Boton((14, 10, 108, 44), "Salir", self.atras, DURAZNO, tam=19, relieve=4),
                        self.boton_opciones((130, 10, 48, 44)),
                        Boton((186, 10, 48, 44), icono, self.reiniciar, ARENA, relieve=4)]
        self.capas = []
        if self.ej.grafico:
            self.cx, self.ancho = 480, 860
            g = ui.grafico(self.ej.grafico)
            self.capas.append((g, g.get_rect(topright=(ANCHO - 24, 108))))
        else:
            self.cx, self.ancho = ANCHO // 2, 1100
        cx, ancho = self.cx, self.ancho
        y = 108
        consigna = self.ej.consigna
        if self.i in self.repasos or self.practica:
            consigna = "**Repaso del cuaderno** · " + consigna
        s = ui.rico(consigna, 20, SUAVE, ancho=ancho, color_negrita=ui.CORAL_OSC)
        self.capas.append((s, s.get_rect(midtop=(cx, y))))
        y += s.get_height() + 4
        f = ui.formula(self.ej.formula, 46)
        s = ui.escalar_a(f.sup, ancho)
        self.capas.append((s, s.get_rect(midtop=(cx, y))))
        y += s.get_height() + 14
        for k in range(self.paso_i):
            p = self.ej.pasos[k]
            mal = k in self.pasos_revelados
            s = ui.escalar_a(ui.rico(p.resumen, 20, ROSA_OSC if mal else MENTA_OSC, ancho=ancho - 100), ancho - 60)
            r = s.get_rect(midtop=(cx + 16, y))
            self.capas.append((s, r))
            self.capas.append(("cruz" if mal else "tilde", (r.left - 20, r.centery)))
            y += s.get_height() + 6
        if self.paso_i:
            y += 6
        n_pasos = len(self.ej.pasos)
        pregunta = self.paso.pregunta
        if n_pasos > 1:
            pregunta = f"**Paso {self.paso_i + 1} de {n_pasos}.** " + pregunta
        s = ui.rico(pregunta, 24, TINTA, ancho=ancho - 150, color_negrita=LAVANDA_OSC)
        insignia = cartelito_consigna(self.es_logica)
        total = insignia.get_width() + 12 + s.get_width()
        x_ins = cx - total // 2
        self.capas.append((insignia, insignia.get_rect(topleft=(x_ins, y + 1))))
        self.capas.append((s, s.get_rect(topleft=(x_ins + insignia.get_width() + 12, y))))
        y += max(s.get_height(), insignia.get_height()) + 16

        respondiendo = self.estado == "pregunta"
        if self.paso.tipo == "expresion":
            pre = ui.escalar_a(ui.formula(ui.fracciones_grandes(self.paso.prefijo), 30).sup, 380) \
                if self.paso.prefijo else None
            ancho_campo = min(560, ancho - 40 - (pre.get_width() + 14 if pre else 0))
            pw = pre.get_width() + 14 if pre else 0
            x0 = cx - (pw + ancho_campo) // 2
            alto_campo = max(58, pre.get_height() + 6) if pre else 58
            if pre:
                self.capas.append((pre, pre.get_rect(midleft=(x0, y + alto_campo // 2))))
            self.campo.rect = pygame.Rect(x0 + pw, y + (alto_campo - 58) // 2, ancho_campo, 58)
            self.campo.habilitado = respondiendo
            y += alto_campo + 8
            self.y_preview = y
            y += 44
            if respondiendo:
                teclas = self._teclado()
                etiquetas = [ui.formula(et, 22).sup for et, _, _ in teclas]
                anchos = [max(46, e.get_width() + 22) for e in etiquetas]
                total = sum(anchos) + 6 * len(anchos) + 56 + 64
                x = cx - total // 2
                for (et, ins, ret), w, sup_et in zip(teclas, anchos, etiquetas):
                    self.botones.append(Boton((x, y, w, 40), sup_et, (lambda a=ins, b=ret: self.campo.insertar(a, b)),
                                              ARENA, radio=10, relieve=4, sonido="tecla"))
                    x += w + 6
                self.botones.append(Boton((x, y, 56, 40), "AC", lambda: self.campo.poner(""), ui.ROSA, tam=17,
                                          radio=10, relieve=4, sonido="tecla"))
                abierto = self.app.progreso.teclado_numerico
                self.botones.append(Boton((x + 62, y, 58, 40), "123", self.alternar_numeros,
                                          SOL if abierto else DURAZNO, tam=17, radio=10, relieve=4, sonido="tecla"))
                y += 50
                if abierto:
                    numeros = NUMEROS + [str(v) for v in self.paso.variables] + ["←", "→", "⌫"]
                    total = len(numeros) * 52 - 6
                    x = cx - total // 2
                    for n in numeros:
                        accion = {"←": self.campo.izquierda, "→": self.campo.derecha, "⌫": self.campo.borrar_atras}.get(
                            n, (lambda n=n: self.campo.insertar(n)))
                        self.botones.append(Boton((x, y, 46, 40), n, accion, TARJETA, tam=19, radio=10, relieve=4,
                                                  sonido="tecla"))
                        x += 52
                    y += 50
                y += 6
                x = cx - (290 + 14 + 190 + 14 + 230) // 2
                self.botones.append(self._boton_pista((x, y, 290, 52)))
                self.botones.append(self._boton_saltear((x + 304, y, 190, 52)))
                self.botones.append(Boton((x + 508, y, 230, 52), "Comprobar  ↵", self.comprobar, CORAL, CREMA,
                                          tam=21, sonido=None))
                y += 64
        else:
            ops = self.paso.opciones
            con_texto = any(o.texto for o in ops)
            alto = 62 if con_texto else 84
            w = min(540, (ancho - 18) // 2)
            x0 = cx - (2 * w + 18) // 2
            self.rect_opciones = {}
            for k, o in enumerate(ops):
                fila, col = divmod(k, 2)
                rect = pygame.Rect(x0 + col * (w + 18), y + fila * (alto + 16), w, alto)
                contenido = o.texto if o.texto else ui.formula(ui.fracciones_grandes(o.tex), 28).sup
                b = Boton(rect, contenido, (lambda k=k: self.elegir(k)), TARJETA, tam=21,
                          tecla=[pygame.K_1 + k, pygame.K_KP1 + k], habilitado=respondiendo and k not in self.marcadas,
                          etiqueta_tecla=str(k + 1), sonido=None, relieve=6)
                b.marcado = self.marcadas.get(k)
                b.t_marcado = self.t_marcas.get(k, 0) if hasattr(self, "t_marcas") else 0
                self.rect_opciones[k] = rect
                self.botones.append(b)
            y += ((len(ops) + 1) // 2) * (alto + 16)
            if respondiendo:
                self.botones.append(self._boton_pista((cx - 247, y, 290, 46)))
                self.botones.append(self._boton_saltear((cx + 57, y, 190, 46)))
                y += 58
        # globito del gato: feedback, pista o charla
        self.panel = None
        y += 6
        if self.feedback:
            self.panel = self._panel_feedback(y)
        elif self.pistas_vistas:
            cuerpo = "\n".join(self.paso.pistas[:self.pistas_vistas])
            self.panel = self._panel(y, "Pista", cuerpo, (255, 246, 214), SOL_OSC)
        elif self.charla and self.t_charla > 0:
            self.panel = self._panel(max(y, ALTO - 130), self.charla, "", TARJETA, ui.CORAL_OSC)

    def _panel(self, y, titulo, cuerpo, color, color_titulo, con_boton=False):
        ancho = ANCHO - X_GLOBO - 24
        ancho_txt = ancho - 50 - (210 if con_boton else 0)
        t = ui.texto(titulo, 23, color_titulo, negrita=True)
        c = ui.rico(cuerpo, 19, TINTA, ancho=ancho_txt, color_negrita=color_titulo) if cuerpo else None
        alto = 22 + t.get_height() + (c.get_height() + 8 if c else 0) + 14
        alto = max(alto, 86 if con_boton else 0)
        # el globito va abajo, al lado del gato (pero sin tapar el ejercicio)
        rect = pygame.Rect(X_GLOBO, max(y, ALTO - 16 - alto), ancho, alto)
        if rect.bottom > ALTO - 12:
            rect.bottom = ALTO - 12
        if con_boton:
            b = Boton((rect.right - 206, rect.centery - 28, 184, 54), "Continuar  ↵", self.continuar, LAVANDA,
                      tam=20, tecla=[pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE], sonido="paso")
            self.botones.append(b)
        return dict(rect=rect, color=color, titulo=t, cuerpo=c, borde=color_titulo)

    def _panel_feedback(self, y):
        fb = self.feedback
        if fb["tipo"] == "bien":
            return self._panel(y, fb["titulo"], fb["cuerpo"], (232, 248, 222), MENTA_OSC, con_boton=self.auto_t is None)
        if fb["tipo"] == "info":
            return self._panel(y, fb["titulo"], fb["cuerpo"], TARJETA, SUAVE)
        return self._panel(y, fb["titulo"], fb["cuerpo"], (255, 234, 226), ROSA_OSC,
                           con_boton=self.estado in ("revelado", "sin_vidas"))

    # ---------------------------------------------- acciones
    def atras(self):
        if self.practica and not self.mundo:
            self.app.cambiar(Cuaderno(self.app))
        else:
            self.app.cambiar(Mapa(self.app, self.mundo.id), "ola")

    def _previsualizar(self, texto):
        if not texto.strip():
            self.preview = None
            return
        try:
            self.preview = ("ok", tex(self._parsear(texto, tal_cual=True), tal_cual=True))
        except ErrorEntrada as ex:
            self.preview = ("err", str(ex))
        except Exception:
            self.preview = ("err", "No entiendo la fórmula.")
        if self.feedback and self.feedback["tipo"] == "info":
            self.feedback = None
            self.armar()

    def pista(self):
        if self.pistas_vistas < len(self.paso.pistas):
            self.pistas_vistas += 1
            self.pistas_usadas += 1
            self.puntos = max(0, self.puntos - 5)
            self.app.progreso.monedas = max(0, self.app.progreso.monedas - 5)
            self.fx.texto(self.pos_monedas[0] + 30, self.pos_monedas[1] + 30, "−5", ui.CORAL, 24, sube=-20, dur=1.0)
            self.gato.reaccionar("pensando", 2.5, saltar=False)
            if self.feedback and self.feedback["tipo"] != "bien":
                self.feedback = None
            self.armar()

    def _parsear(self, texto, tal_cual=False):
        return parsear(texto, self.paso.variables, permitir_c=self.paso.chequeo == "primitiva", tal_cual=tal_cual)

    def comprobar(self):
        if self.estado != "pregunta" or self.paso.tipo != "expresion":
            return
        try:
            r = self._parsear(self.campo.texto)
        except ErrorEntrada as ex:
            self.feedback = dict(tipo="info", titulo="Mmm, no entiendo lo que escribiste",
                                 cuerpo=f"{ex} (Esto no te saca vidas. En el menú está la ayuda para escribir fórmulas.)")
            self.gato.reaccionar("sorpresa", 1.2, saltar=False)
            sonidos.tocar("tic")
            self.armar()
            return
        p = self.paso
        if p.chequeo == "primitiva":
            if es_primitiva(r, p.integrando, p.var or p.variables[0]):
                nota = ""
                if not r.has(C) and p.prefijo.startswith("\\int"):
                    nota = "Ojo: en el parcial no te olvides del $+\\,C$."
                self.acierto(nota)
            else:
                _, titulo, cuerpo = diagnosticar_primitiva(r, p.integrando, p.var or p.variables[0], p.errores)
                self.fallo(titulo, cuerpo, tuya=self._tuya())
            return
        if equivalentes(r, p.esperado):
            self.acierto()
        elif p.chequeo == "numero" and casi_igual(r, p.esperado):
            self.acierto(f"Está bien, pero en el parcial dejalo exacto: ${tex(p.esperado)}$.")
        else:
            _, titulo, cuerpo = diagnosticar(r, p.esperado, p.errores, p.original)
            self.fallo(titulo, cuerpo, tuya=self._tuya())

    def _tuya(self):
        try:
            return f"${self.paso.prefijo} {tex(self._parsear(self.campo.texto, tal_cual=True), tal_cual=True)}$"
        except Exception:
            return self.campo.texto

    def elegir(self, k):
        if self.estado != "pregunta":
            return
        o = self.paso.opciones[k]
        self.t_marcas = getattr(self, "t_marcas", {})
        self.t_marcas[k] = pygame.time.get_ticks() / 1000
        if o.correcta:
            self.marcadas[k] = "bien"
            self.acierto(origen=self.rect_opciones[k].center)
        else:
            self.marcadas[k] = "mal"
            titulo, cuerpo = ERRORES.get(o.error, ("Todavía no", "Esa no es."))
            self.fallo(titulo, cuerpo, tuya=f"${o.tex}$" if o.tex else o.texto)

    def _origen(self):
        if self.paso.tipo == "expresion":
            return self.campo.rect.center
        return (self.cx, 400)

    def acierto(self, nota="", origen=None):
        self.racha += 1
        pts = 10 + 2 * min(self.racha - 1, 5)
        if self.tiempo:
            pts += max(0, int(self.tiempo - self.t_paso))
        self.puntos += pts
        self.app.progreso.monedas += pts
        self.estado = "bien"
        self.charla = None
        cuerpo = self.paso.explicacion
        if self.paso.tipo == "expresion" and self.paso.mostrar:
            cuerpo = f"${self.paso.prefijo} {self.paso.mostrar}$\n{cuerpo}"
        if nota:
            cuerpo = f"**{nota}**\n{cuerpo}" if cuerpo else f"**{nota}**"
        self.feedback = dict(tipo="bien", titulo=f"{random.choice(FRASES_BIEN)}   +{pts}", cuerpo=cuerpo)
        if (not self.paso.explicacion and not nota) or self.tiempo:
            self.auto_t = 0.9 if not self.tiempo else 1.6
        self.t_marcas = getattr(self, "t_marcas", {})
        for k, o in enumerate(self.paso.opciones):
            if o.correcta:
                self.marcadas[k] = "bien"
                self.t_marcas.setdefault(k, pygame.time.get_ticks() / 1000)
        # festejo
        ox, oy = origen or self._origen()
        self.fx.confeti(ox, oy, 12 + min(self.racha, 6) * 2, 0.55)
        self.fx.texto(ox, oy - 34, f"+{pts}", ui.SOL, 30, sube=45, dur=1.4)
        for k in range(min(3, 1 + pts // 12)):
            self.fx.volar((ox, oy), self.pos_monedas, self._llego_moneda, dur=0.95, demora=0.25 + k * 0.15)
        if self.racha >= 3:
            sonidos.tocar("bien_racha", 0.75)
        else:
            sonidos.tocar("bien", 0.75)
        if self.racha in (3, 5, 8, 12, 20):
            self.fx.texto(ANCHO // 2, 300, f"¡Racha ×{self.racha}!", ui.CORAL, 44, sube=50, dur=1.8)
            sonidos.tocar("fuego")
            self.gato.reaccionar("festejo", 1.4)
        else:
            self.gato.reaccionar("feliz", 1.2)
        self.armar()

    def _llego_moneda(self):
        self.t_moneda = 0.0
        sonidos.tocar("moneda", 0.5, variar=True)

    def fallo(self, titulo, cuerpo, sin_reintento=False, tuya=""):
        self.errores_log.append(dict(formula=self.ej.formula, consigna=self.ej.consigna, pregunta=self.paso.pregunta,
                                     tuya=tuya, correcta=self._respuesta_tex(), titulo=titulo, cuerpo=cuerpo,
                                     explicacion=self.paso.explicacion))
        self.vidas -= 1
        self.t_corazon = 0.0
        self.racha = 0
        self.errores += 1
        self.intentos += 1
        self.fallo_ej = True
        self.sacudir = 0.4
        self.charla = None
        self.app.sacudir(7)
        sonidos.tocar("mal")
        self.gato.reaccionar("triste", 1.8)
        titulo = f"{random.choice(FRASES_MAL)} {titulo}"
        if self.vidas <= 0 or sin_reintento or self.intentos >= self.paso.max_intentos:
            self.estado = "sin_vidas" if self.vidas <= 0 else "revelado"
            self.pasos_revelados.add(self.paso_i)
            self.t_marcas = getattr(self, "t_marcas", {})
            for k, o in enumerate(self.paso.opciones):
                if o.correcta:
                    self.marcadas[k] = "bien"
            extra = f"La respuesta era:  {self._respuesta_tex()}"
            if self.paso.explicacion:
                extra += "\n" + self.paso.explicacion
            self.feedback = dict(tipo="mal", titulo=titulo, cuerpo="\n".join(t for t in (cuerpo, extra) if t))
        else:
            self.feedback = dict(tipo="mal", titulo=titulo, cuerpo=cuerpo + "  **¡Probá de nuevo!**")
        self.armar()

    def continuar(self):
        if self.estado == "sin_vidas":
            if self.fallo_ej:
                self.app.progreso.anotar_error(self.ej.clave, self.ej.formula)
                self.al_cuaderno += 1
            self.app.cambiar(FinNivel(self.app, self, gano=False))
            return
        if self.estado not in ("bien", "revelado"):
            return
        self.paso_i += 1
        if self.paso_i < len(self.ej.pasos):
            self.empezar_paso()
        else:
            self.terminar_ejercicio()

    def terminar_ejercicio(self):
        prog = self.app.progreso
        if self.fallo_ej:
            prog.anotar_error(self.ej.clave, self.ej.formula)
            self.al_cuaderno += 1
            self.resultados.append("mal")
        else:
            if prog.en_cuaderno(self.ej.clave) and prog.anotar_acierto(self.ej.clave):
                self.sacados += 1
            self.resultados.append("bien")
        self.i += 1
        if self.i >= len(self.ejercicios):
            self.terminar_nivel()
        else:
            self.empezar_ejercicio()

    def terminar_nivel(self):
        faltas = self.errores + self.pistas_usadas + (1 if self.salteo_usado else 0)
        estrellas = 3 if faltas == 0 else (2 if faltas <= 2 else 1)
        nuevo_mundo = None
        if not self.practica:
            prog = self.app.progreso
            orden = [m.id for m in MUNDOS]
            pos = orden.index(self.mundo.id)
            era_ultimo = self.nivel_idx == len(self.mundo.niveles) - 1
            ya = prog.aprobado(self.mundo.id, self.nivel_idx)
            prog.registrar(self.mundo.id, self.nivel_idx, estrellas, self.puntos)
            if era_ultimo and not ya and pos + 1 < len(MUNDOS):
                nuevo_mundo = MUNDOS[pos + 1]
        self.app.cambiar(FinNivel(self.app, self, gano=True, estrellas=estrellas, nuevo_mundo=nuevo_mundo))

    # ---------------------------------------------- loop
    @property
    def pos_monedas(self):
        return (ANCHO - 230, 32)

    def evento(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.atras()
            return True
        if self.estado == "pregunta" and self.paso.tipo == "expresion":
            if e.type == pygame.MOUSEBUTTONDOWN and not self.campo.rect.collidepoint(e.pos):
                pass
            elif self.campo.evento(e):
                return True
        if self.estado == "bien" and self.auto_t is not None and e.type == pygame.KEYDOWN and \
                e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            self.continuar()
            return True
        for b in list(self.botones):
            if b.evento(e):
                return True
        return False

    def actualizar(self, dt):
        self.t += dt
        self.t_entrada += dt
        self.t_moneda += dt
        self.t_corazon += dt
        self.campo.actualizar(dt)
        self.sacudir = max(0, self.sacudir - dt)
        self.fx.actualizar(dt)
        self.fuego.actualizar(dt, min(1.0, self.racha / 8))
        self.gato.actualizar(dt)
        self.puntos_vistos += (self.puntos - self.puntos_vistos) * min(1, dt * 6)
        self.monedas_vistas += (self.app.progreso.monedas - self.monedas_vistas) * min(1, dt * 5)
        if self.t_charla > 0:
            self.t_charla -= dt
            if self.t_charla <= 0 and not self.feedback:
                self.charla = None
                self.armar()
        if self.estado == "pregunta" and self.tiempo:
            self.t_paso += dt
            quedan = int(self.tiempo - self.t_paso)
            if quedan < 3 and quedan != self.ultimo_tic:
                self.ultimo_tic = quedan
                sonidos.tocar("tic")
            if self.t_paso >= self.tiempo:
                self.fallo("¡Se acabó el tiempo!", "", sin_reintento=True, tuya="(se acabó el tiempo)")
        if self.auto_t is not None and self.estado == "bien":
            self.auto_t -= dt
            if self.auto_t <= 0:
                self.auto_t = None
                self.continuar()

    def _dibujar_encabezado(self, sup):
        r = pygame.Rect(-10, -10, ANCHO + 20, 74)
        ui.tabla_madera(sup, r, radio=0)
        t = ui.texto_borde(self.titulo, 24, CREMA, MADERA_OSC, 2)
        sup.blit(t, (248, 32 - t.get_height() // 2))
        x = 248 + t.get_width() + 12
        if self.jefe:
            et = ui.texto_borde("JEFE", 16, CREMA, ui.CORAL_OSC, 2)
            rr = pygame.Rect(x, 18, et.get_width() + 18, 28)
            dibujo.rect(sup, CORAL, rr, border_radius=14)
            dibujo.rect(sup, BORDE, rr, 2, border_radius=14)
            sup.blit(et, et.get_rect(center=rr.center))
        # vidas
        x = ANCHO - 34
        for k in range(self.vidas_max - 1, -1, -1):
            if k < self.vidas:
                ui.corazon(sup, (x, 30), 28, CORAL)
            else:
                ui.corazon(sup, (x, 30), 28, GRIS, brillo=False)
                if k == self.vidas and self.t_corazon < 0.6:
                    kk = self.t_corazon / 0.6
                    tam = 28 * (1 + kk * 1.2)
                    cap = Lienzo(*((80, 80)))
                    ui.corazon(cap, (40, 40), tam, CORAL)
                    cap.set_alpha(int(255 * (1 - kk)))
                    sup.blit(cap, (x - 40, 30 - 40 - kk * 20))
            x -= 38
        # monedas
        mx, my = self.pos_monedas
        bump = 1 + 0.35 * max(0.0, 1 - self.t_moneda / 0.25)
        ui.moneda(sup, (mx, my), 14 * bump)
        pts = ui.texto_borde(str(int(round(self.monedas_vistas))), 24, CREMA, MADERA_OSC, 2)
        sup.blit(pts, pts.get_rect(midleft=(mx + 22, my - 4)))
        nivel_txt = ui.texto(f"+{self.puntos} en este nivel", 12, (255, 236, 190), negrita=True)
        sup.blit(nivel_txt, nivel_txt.get_rect(midleft=(mx - 8, my + 21)))
        # racha con fuego
        if self.racha >= 2:
            fx = mx - 70
            escala = 0.8 + min(self.racha, 10) * 0.08
            self.fuego.dibujar(sup, (fx, 44), escala)
            rt = ui.texto_borde(f"×{self.racha}", 20, SOL, MADERA_OSC, 2)
            sup.blit(rt, rt.get_rect(midleft=(fx + 14, 34)))
        # soga con el progreso
        n = len(self.ejercicios)
        sep = min(30, 600 // max(1, n))
        x0 = ANCHO // 2 - (n - 1) * sep // 2
        dibujo.line(sup, MADERA, (x0 - 14, 86), (x0 + (n - 1) * sep + 14, 86), 3)
        for k in range(n):
            c = (x0 + k * sep, 86)
            if k < len(self.resultados):
                color = {"bien": ui.PASTO, "salteado": (186, 150, 236)}.get(self.resultados[k], CORAL)
                dibujo.circle(sup, BORDE, c, 10)
                dibujo.circle(sup, color, c, 8)
            elif k == self.i:
                rr = 10 + 2 * math.sin(self.t * 5)
                dibujo.circle(sup, BORDE, c, rr + 2)
                dibujo.circle(sup, SOL, c, rr)
            else:
                dibujo.circle(sup, ARENA_OSC, c, 7)
                dibujo.circle(sup, ARENA, c, 5)
        if self.tiempo:
            restante = max(0.0, 1 - min(self.t_paso, self.tiempo) / self.tiempo)
            rr = pygame.Rect(ANCHO // 2 - 220, 100, 440, 10)
            dibujo.rect(sup, BORDE, rr.inflate(4, 4), border_radius=6)
            dibujo.rect(sup, (240, 228, 204), rr, border_radius=5)
            col = ui.PASTO if restante > 0.5 else (SOL if restante > 0.25 else CORAL)
            dibujo.rect(sup, col, (rr.left, rr.top, int(rr.width * restante), rr.height), border_radius=5)

    def dibujar(self, sup):
        sup.blit(paisaje.pergamino(), (0, 0))
        if self.es_logica:
            sup.blit(_velo_logica(), (0, 0))
        k = suave(self.t_entrada / 0.35)
        dx = int((1 - k) * 90)
        for s, r in self.capas:
            if s == "tilde":
                ui.tilde(sup, (r[0] + dx, r[1]), 18, MENTA_OSC, 3)
            elif s == "cruz":
                ui.cruz(sup, (r[0] + dx, r[1]), 18, ROSA_OSC, 3)
            else:
                if k < 1:
                    s = s.copy()
                    s.set_alpha(int(255 * k))
                sup.blit(s, r.move(dx, 0))
        if self.paso.tipo == "expresion":
            temblor = int(math.sin(self.sacudir * 50) * 9 * (self.sacudir / 0.4)) if self.sacudir else 0
            orig = self.campo.rect
            self.campo.rect = orig.move(temblor + dx, 0)
            self.campo.dibujar(sup)
            self.campo.rect = orig
            if self.preview and self.estado == "pregunta":
                if self.preview[0] == "ok":
                    et = ui.texto("Leo:", 18, SUAVE, negrita=True)
                    fm = ui.escalar_a(ui.formula(self.preview[1], 26, LAVANDA_OSC).sup, 900)
                    w = et.get_width() + 12 + fm.get_width()
                    x = self.cx - w // 2
                    cy = self.y_preview + 18
                    sup.blit(et, (x, cy - et.get_height() // 2))
                    sup.blit(fm, (x + et.get_width() + 12, cy - fm.get_height() // 2))
                else:
                    centrar(sup, ui.texto(self.preview[1], 18, SUAVE), self.y_preview + 6, self.cx)
        for b in self.botones:
            b.dibujar(sup, dx if b.rect.top > 90 else 0)
        # el gato y su globito
        self.gato.dibujar(sup, PIE_GATO)
        if self.panel:
            p = self.panel
            ui.globo(sup, p["rect"], BOCA_GATO, p["color"], p["borde"], 3)
            if self.app.progreso.nombre_gato:
                et = ui.texto_borde(self.app.progreso.nombre_gato, 16, CREMA, MADERA_OSC, 2)
                r = pygame.Rect(0, 0, et.get_width() + 22, 26)
                r.bottomleft = (p["rect"].left + 18, p["rect"].top + 6)
                dibujo.rect(sup, MADERA, r, border_radius=13)
                dibujo.rect(sup, MADERA_OSC, r, 2, border_radius=13)
                sup.blit(et, et.get_rect(center=r.center))
            sup.blit(p["titulo"], (p["rect"].left + 22, p["rect"].top + 14))
            if p["cuerpo"]:
                sup.blit(p["cuerpo"], (p["rect"].left + 22, p["rect"].top + 22 + p["titulo"].get_height()))
            for b in self.botones:
                if b.rect.colliderect(p["rect"]) and b.rect.top > p["rect"].top:
                    b.dibujar(sup)
        self._dibujar_encabezado(sup)
        for b in self.botones[:3]:
            b.dibujar(sup)
        self.fx.dibujar(sup)


# =============================================================== FIN DE NIVEL

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
        revisar = ("Revisar errores", lambda: app.cambiar(RevisarErrores(app, juego, self), "fundido"), SOL, TINTA)
        b = [revisar]
        if juego.practica:
            if juego.mundo:
                b.append(("Volver al mapa", lambda: app.cambiar(Mapa(app, juego.mundo.id), "ola"), CORAL, CREMA))
            else:
                b.append(("Volver al cuaderno", lambda: app.cambiar(Cuaderno(app)), CORAL, CREMA))
        else:
            m, i = juego.mundo, juego.nivel_idx
            principal = None
            if not gano:
                principal = ("Reintentar", lambda: app.cambiar(Juego(app, m.id, i), "ola"), CORAL, CREMA)
            elif i + 1 < len(m.niveles):
                principal = ("Siguiente nivel", lambda: app.cambiar(Juego(app, m.id, i + 1), "ola"), CORAL, CREMA)
            elif nuevo_mundo:
                principal = ("¡A la isla nueva!", lambda: app.cambiar(Mapa(app, nuevo_mundo.id), "ola"), CORAL, CREMA)
            b.append(("Mapa", lambda: app.cambiar(Mapa(app, m.id), "ola"), ARENA if principal else CORAL,
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
            self.app.cambiar(Cuaderno(self.app))
        else:
            self.app.cambiar(Mapa(self.app, self.j.mundo.id), "ola")

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


# =============================================================== CUADERNO

class Cuaderno(Escena):
    MAX = 8

    def __init__(self, app):
        super().__init__(app)
        self.items = list(app.progreso.cuaderno)
        self.gato = Gato(120)
        self.gato.animo_base = "normal" if self.items else "dormido"
        self.gato.animo = self.gato.animo_base
        self.botones = [Boton((24, 22, 128, 50), "Menú", self.atras, DURAZNO, tam=22)]
        if self.items:
            self.botones.append(Boton((ANCHO - 330, 640, 300, 60), f"Practicar ({min(len(self.items), self.MAX)})",
                                      self.practicar, CORAL, CREMA, tam=24, tecla=[pygame.K_RETURN, pygame.K_KP_ENTER]))

    def atras(self):
        self.app.cambiar(Menu(self.app))

    def practicar(self):
        claves = [c["clave"] for c in self.items[:self.MAX]]
        random.shuffle(claves)
        self.app.cambiar(Juego(self.app, None, None, practica=claves), "ola")

    def actualizar(self, dt):
        self.gato.actualizar(dt)

    def dibujar(self, sup):
        sup.blit(paisaje.pergamino(), (0, 0))
        letrero(sup, (ANCHO // 2 - 230, 16, 460, 62), "Cuaderno de errores", 30)
        sup.blit(ui.rico("Los ejercicios en los que te equivocaste. Cada uno sale cuando lo resolvés **2 veces sin errores** "
                         "(acá o cuando te aparece de repaso en un nivel).", 18, SUAVE, ancho=1180, color_negrita=ui.CORAL_OSC),
                 (40, 90))
        if not self.items:
            s = ui.rico("¡Está vacío! Cuando te equivoques en un ejercicio, va a aparecer acá para que lo repases.",
                        24, SUAVE, ancho=700, centrado=True)
            centrar(sup, s, 260)
            self.gato.dibujar(sup, (ANCHO // 2, 520))
        y = 140
        for item in self.items[:self.MAX]:
            r = pygame.Rect(40, y, ANCHO - 80, 50)
            ui.tarjeta(sup, r, TARJETA, 14, ui.ARENA_OSC, 4)
            c = item["clave"]
            try:
                m = mundo_por_id(c["mundo"])
                lugar = f"{m.nombre} · {m.niveles[c['nivel']].nombre}"
            except (KeyError, IndexError):
                lugar = ""
            sup.blit(ui.texto(lugar, 16, SUAVE, negrita=True), (r.left + 18, r.centery - 10))
            f = ui.escalar_a(ui.formula(item["formula"], 24).sup, 620)
            sup.blit(f, f.get_rect(midleft=(r.left + 380, r.centery)))
            for k in range(2):
                ui.estrella(sup, (r.right - 60 + k * 28, r.centery), 11,
                            SOL if k < item["repasos"] else (232, 222, 200), BORDE, brillo=False)
            y += 60
        if len(self.items) > self.MAX:
            sup.blit(ui.texto(f"…y {len(self.items) - self.MAX} más", 18, SUAVE, negrita=True), (40, 660))
        if self.items:
            self.gato.dibujar(sup, (ANCHO - 420, ALTO - 6), 100)
        self.dibujar_botones(sup)


# =============================================================== AYUDA

class Ayuda(Escena):
    FILAS = [
        ("Potencia", "x^3", ["x^3"]),
        ("Multiplicar", "3x   o   3*x", ["3x"]),
        ("Seno y coseno", "sen(x)   cos(x)", ["sen(x)", "cos(x)"]),
        ("Tangente", "tg(x)", ["tg(x)"]),
        ("e a la algo", "e^(2x)", ["e^(2x)"]),
        ("Logaritmo natural", "ln(x)", ["ln(x)"]),
        ("Raíz cuadrada", "raiz(x)", ["raiz(x)"]),
        ("Raíz cúbica (o la que sea)", "raiz3(x)", ["raiz3(x)"]),
        ("Fracción", "(x+1)/(x^2+1)", ["(x+1)/(x^2+1)"]),
        ("Seno al cuadrado", "sen(x)^2", ["sen(x)^2"]),
        ("Decimales", "0,5x", ["0,5x"]),
        ("Otras variables", "3x^2y + z", ["3x^2y+z"]),
        ("Constante de integración", "x^3/3 + C", ["x^3/3+C"]),
        ("Pi", "8pi/3", ["8pi/3"]),
    ]

    def __init__(self, app):
        super().__init__(app)
        self.botones = [Boton((24, 22, 128, 50), "Menú", self.atras, DURAZNO, tam=22)]
        self.filas = [(nombre, ejemplo, r"\quad ".join(tex(parsear(m, (VAR_X, VAR_Y, VAR_Z), True)) for m in muestras))
                      for nombre, ejemplo, muestras in self.FILAS]
        self.gato = Gato(120)
        self.gato.animo_base = "normal"

    def atras(self):
        self.app.cambiar(Menu(self.app))

    def actualizar(self, dt):
        self.gato.actualizar(dt)

    def dibujar(self, sup):
        sup.blit(paisaje.pergamino(), (0, 0))
        letrero(sup, (ANCHO // 2 - 250, 16, 500, 62), "Cómo escribir fórmulas", 30)
        x1, x2, x3 = 60, 290, 560
        y = 96
        for et, x in [("Para escribir…", x1), ("tipeás", x2), ("y se ve así", x3)]:
            sup.blit(ui.texto(et, 18, SUAVE, negrita=True), (x, y))
        y += 30
        for nombre, ejemplo, vista in self.filas:
            r = pygame.Rect(40, y, 760, 36)
            dibujo.rect(sup, TARJETA, r, border_radius=12)
            dibujo.rect(sup, ui.ARENA_OSC, r, 2, border_radius=12)
            sup.blit(ui.texto(nombre, 18, TINTA), (x1, y + 8))
            sup.blit(ui.texto(ejemplo, 18, LAVANDA_OSC, mono=True, negrita=True), (x2, y + 8))
            if vista:
                f = ui.escalar_a(ui.formula(vista, 22).sup, 230)
                sup.blit(f, f.get_rect(midleft=(x3, y + 18)))
            y += 40
        consejos = ("**Consejos del gato**\n"
                    "• Usá paréntesis: **e^2x** se lee como $e^2\\cdot x$. Para $e^{2x}$ escribí **e^(2x)**.\n"
                    "• Debajo del cuadro vas a ver «Leo: …» con cómo entendí lo que escribiste.\n"
                    "• No hace falta simplificar: si es la misma función escrita distinto, está bien.\n"
                    "• Si tu teclado escribe â cuando apretás ^, no pasa nada: lo entiendo igual.\n"
                    "• En las integrales podés poner **+ C** o no.\n"
                    "• Equivocarte al tipear **no** te saca vidas.\n"
                    "• Con la tecla **M** prendés o apagás el sonido.")
        cuerpo = ui.rico(consejos, 17, TINTA, ancho=370, color_negrita=ui.CORAL_OSC)
        caja = pygame.Rect(828, 0, 420, cuerpo.get_height() + 36)
        caja.bottom = 560
        ui.globo(sup, caja, (1110, 590), TARJETA)
        sup.blit(cuerpo, (caja.left + 22, caja.top + 18))
        self.gato.dibujar(sup, (1110, ALTO - 12))
        self.dibujar_botones(sup)


# =============================================================== OPCIONES

class Opciones(Escena):
    """Se abre encima de la pantalla en la que estabas (la deja en pausa)."""

    def __init__(self, app, previa):
        super().__init__(app)
        self.previa = previa
        self.musica = getattr(previa, "musica", "isla")
        self.foto = app.lienzo.copy()
        velo = Lienzo(*(self.foto.get_size()))
        velo.fill((40, 30, 40, 140))
        self.foto.blit(velo, (0, 0))
        self.t = 0.0
        p = app.progreso
        self.panel = pygame.Rect(ANCHO // 2 - 300, 96, 600, 540)
        x, y = self.panel.left + 50, self.panel.top + 110
        self.controles = [
            ui.Interruptor((x + 380, y, 110, 40), p.musica, self.poner_musica),
            ui.Deslizador((x + 20, y + 66, 470, 14), p.vol_musica, self.vol_musica),
            ui.Interruptor((x + 380, y + 120, 110, 40), p.sonido, self.poner_efectos),
            ui.Deslizador((x + 20, y + 186, 470, 14), p.vol_efectos, self.vol_efectos),
            ui.Interruptor((x + 380, y + 240, 110, 40), p.pantalla_completa, self.poner_pantalla),
        ]
        self.botones = [Boton((self.panel.centerx - 110, self.panel.bottom - 86, 220, 58), "Listo", self.atras,
                              CORAL, CREMA, tam=24, tecla=[pygame.K_RETURN, pygame.K_KP_ENTER])]
        self._habilitar()

    def _habilitar(self):
        self.controles[1].habilitado = self.app.progreso.musica
        self.controles[3].habilitado = self.app.progreso.sonido

    def poner_musica(self, v):
        self.app.progreso.musica = v
        sonidos.poner_musica(v)
        self.app.progreso.guardar()
        self._habilitar()

    def poner_efectos(self, v):
        self.app.progreso.sonido = v
        sonidos.poner_efectos(v)
        self.app.progreso.guardar()
        self._habilitar()

    def vol_musica(self, v):
        self.app.progreso.vol_musica = v
        sonidos.poner_volumenes(musica=v)
        self.app.progreso.guardar()

    def vol_efectos(self, v):
        self.app.progreso.vol_efectos = v
        sonidos.poner_volumenes(efectos=v)
        self.app.progreso.guardar()

    def poner_pantalla(self, v):
        self.app.poner_pantalla_completa(v)

    def atras(self):
        self.app.cambiar(self.previa, None)

    def evento(self, e):
        for c in self.controles:
            if c.evento(e):
                return True
        return super().evento(e)

    def actualizar(self, dt):
        self.t += dt

    def dibujar(self, sup):
        sup.blit(self.foto, (0, 0))
        k = rebote(min(1.0, self.t / 0.3))
        panel = self.panel.move(0, int((1 - k) * 60))
        ui.tarjeta(sup, panel, ui.PERGAMINO, 26, ui.ARENA_OSC, 8)
        letrero(sup, (panel.centerx - 160, panel.top - 26, 320, 64), "Opciones", 30)
        x, y = panel.left + 50, panel.top + 110
        filas = [("Música", y), ("Efectos de sonido", y + 120), ("Pantalla completa  (F11)", y + 240)]
        for txt, yy in filas:
            sup.blit(ui.texto(txt, 26, TINTA, negrita=True), (x, yy + 4))
        icono_m = pygame.Rect(x + 300, y + 2, 36, 36)
        ui.parlante(sup, (icono_m.centerx, icono_m.centery), 30, SUAVE, self.app.progreso.musica)
        sup.blit(ui.texto("La tecla M silencia todo de una.", 17, SUAVE), (x, y + 300))
        dy = int((1 - k) * 60)
        for c in self.controles:
            c.rect.move_ip(0, dy)
            c.dibujar(sup)
            c.rect.move_ip(0, -dy)
        self.dibujar_botones(sup)


# =============================================================== TIENDA DEL MICHI

class Tienda(Escena):
    COLS, FILAS = 5, 4

    def __init__(self, app):
        super().__init__(app)
        self.cielo = paisaje.Cielo(semilla=8, nubes=4)
        self.mar = paisaje.Mar(400)
        self.gato = Gato(250)
        self.gato.reaccionar("feliz", 1.2)
        self.fx = Efectos()
        self.lugar = "conjuntos"
        self.sel = None              # id de prenda o de conjunto que se está probando
        self.t = 0.0
        self.mensaje = "¡Elegí algo para probarle!"
        self.armar()

    @property
    def prog(self):
        return self.app.progreso

    def atras(self):
        self.app.cambiar(Menu(self.app), "ola")

    def _sincronizar(self):
        modulo_gato.ROPA = tuple(self.prog.ropa_puesta.values())

    # ---- conjuntos y prendas con la misma interfaz
    def _piezas(self, item_id):
        c = ropa.CONJUNTO_POR_ID.get(item_id)
        return c.piezas if c else (item_id,)

    def _precio(self, item_id):
        c = ropa.CONJUNTO_POR_ID.get(item_id)
        return c.precio if c else ropa.POR_ID[item_id].precio

    def _nombre(self, item_id):
        c = ropa.CONJUNTO_POR_ID.get(item_id)
        return c.nombre if c else ropa.POR_ID[item_id].nombre

    def _tiene(self, item_id):
        return all(p in self.prog.ropa_comprada for p in self._piezas(item_id))

    def _puesto(self, item_id):
        return all(self.prog.ropa_puesta.get(ropa.POR_ID[p].lugar) == p for p in self._piezas(item_id))

    def _probando(self):
        puesta = dict(self.prog.ropa_puesta)
        if self.sel:
            for p in self._piezas(self.sel):
                puesta[ropa.POR_ID[p].lugar] = p
        return tuple(puesta.values())

    def _items(self):
        if self.lugar == "conjuntos":
            return [c.id for c in ropa.CONJUNTOS]
        return [p.id for p in ropa.CATALOGO if p.lugar == self.lugar]

    def _tarjeta(self, item_id, w, h):
        s = Lienzo(*((w, h)))
        img = modulo_gato.superficie(66, "normal", ropa=self._piezas(item_id))
        s.blit(img, img.get_rect(midtop=(w // 2, -10)))
        nombre = ui.escalar_a(ui.texto(self._nombre(item_id), 13, TINTA, negrita=True), w - 6)
        s.blit(nombre, nombre.get_rect(midtop=(w // 2, h - 38)))
        if self._puesto(item_id):
            et = ui.texto("¡Puesto!", 14, MENTA_OSC, negrita=True)
            s.blit(et, et.get_rect(midtop=(w // 2, h - 20)))
        elif self._tiene(item_id):
            et = ui.texto("Es tuyo", 14, ui.LAVANDA_OSC, negrita=True)
            s.blit(et, et.get_rect(midtop=(w // 2, h - 20)))
        else:
            precio = self._precio(item_id)
            et = ui.texto(str(precio), 15, ui.SOL_OSC if self.prog.monedas >= precio else SUAVE, negrita=True)
            ancho = et.get_width() + 20
            x = w // 2 - ancho // 2
            ui.moneda(s, (x + 7, h - 11), 8)
            s.blit(et, (x + 18, h - 20))
        return s

    def armar(self):
        self.botones = [Boton((24, 22, 128, 50), "Menú", self.atras, DURAZNO, tam=22),
                        self.boton_opciones((ANCHO - 76, 22, 56, 50))]
        pestañas = [("conjuntos", "Conjuntos")] + ropa.LUGARES
        x0, ancho_p = 566, 82
        for k, (clave, nombre) in enumerate(pestañas):
            self.botones.append(Boton((x0 + k * (ancho_p + 4), 110, ancho_p, 42), nombre,
                                      (lambda c=clave: self.elegir_lugar(c)),
                                      SOL if clave == self.lugar else ARENA, tam=13, relieve=4, sonido="tecla", radio=12))
        w, h = 128, 116
        for k, item in enumerate(self._items()[:self.COLS * self.FILAS]):
            fila, col = divmod(k, self.COLS)
            rect = (x0 + col * (w + 8), 166 + fila * (h + 10), w, h)
            color = (226, 246, 210) if self._puesto(item) else ((255, 236, 196) if item == self.sel else TARJETA)
            self.botones.append(Boton(rect, self._tarjeta(item, w - 10, h - 8), (lambda i=item: self.tocar(i)), color,
                                      radio=14, relieve=4, sonido="tecla"))
        if self.sel and not self._tiene(self.sel):
            alcanza = self.prog.monedas >= self._precio(self.sel)
            self.botones.append(Boton((90, 602, 380, 64), f"Comprar · {self._precio(self.sel)}", self.comprar, CORAL,
                                      CREMA, tam=26, habilitado=alcanza, sonido=None))
        if self.prog.ropa_puesta:
            self.botones.append(Boton((180, 676, 200, 38), "Sacarle todo", self.sacar_todo, ARENA, tam=16, relieve=4))

    def elegir_lugar(self, clave):
        self.lugar = clave
        self.armar()

    def tocar(self, item_id):
        nombre = self._nombre(item_id)
        if self._tiene(item_id):
            if self._puesto(item_id):
                for p in self._piezas(item_id):
                    self.prog.poner(ropa.POR_ID[p].lugar, None)
                self.mensaje = f"Le sacaste: {nombre}"
                self.gato.reaccionar("sorpresa", 0.8, saltar=False)
            else:
                for p in self._piezas(item_id):
                    self.prog.poner(ropa.POR_ID[p].lugar, p)
                self.mensaje = f"¡Le pusiste: {nombre}!"
                self.gato.reaccionar("feliz", 1.0)
                sonidos.tocar("estrella", 0.6)
            self.sel = None
            self._sincronizar()
        else:
            self.sel = item_id
            faltan = self._precio(item_id) - self.prog.monedas
            self.mensaje = (f"Probándose: {nombre}" if faltan <= 0 else f"Te faltan {faltan} monedas para: {nombre}")
            self.gato.reaccionar("sorpresa" if faltan > 0 else "feliz", 0.9, saltar=faltan <= 0)
        self.armar()

    def comprar(self):
        item = self.sel
        ok = self.prog.comprar_conjunto(self._piezas(item), self._precio(item))
        if ok:
            for p in self._piezas(item):
                self.prog.poner(ropa.POR_ID[p].lugar, p)
            self._sincronizar()
            sonidos.tocar("desbloqueo")
            sonidos.tocar("miau")
            sonidos.agachar(1.2)
            self.fx.confeti(270, 420, 60, 1.0)
            self.fx.chispas(270, 460, 24, ui.SOL, 300)
            self.fx.texto(270, 330, f"−{self._precio(item)}", ui.SOL, 40, sube=30, dur=1.5)
            self.gato.reaccionar("festejo", 2.0)
            self.mensaje = f"¡Compraste: {self._nombre(item)}!"
            self.sel = None
        else:
            sonidos.tocar("mal")
        self.armar()

    def sacar_todo(self):
        for lugar in list(self.prog.ropa_puesta):
            self.prog.poner(lugar, None)
        self.sel = None
        self._sincronizar()
        self.mensaje = "¡Al natural!"
        self.armar()

    def actualizar(self, dt):
        self.t += dt
        self.cielo.actualizar(dt)
        self.mar.actualizar(dt)
        self.gato.actualizar(dt)
        self.fx.actualizar(dt)
        self.gato.ropa = self._probando() if self.sel else None

    def dibujar(self, sup):
        self.cielo.dibujar(sup, sol=False)
        self.mar.dibujar(sup)
        pts = [(0, ALTO)] + [(x, 520 + 10 * math.sin(x / 70 + 1)) for x in range(0, 561, 20)] + [(560, ALTO)]
        dibujo.polygon(sup, ui.ARENA, pts)
        dibujo.lines(sup, ui.ESPUMA, False, pts[1:-1], 5)
        pieza, m = pincel.pedestal(300, 84, CORAL) if pincel.HAY_SKIA else (None, 0)
        if pieza is not None:
            sup.blit(pieza, (120 - m, 528 - m))
        else:
            dibujo.ellipse(sup, BORDE, (120, 528, 300, 70))
            dibujo.ellipse(sup, CORAL, (124, 528, 292, 62))
            dibujo.ellipse(sup, (255, 170, 150), (150, 538, 240, 42), 4)
        self.gato.dibujar(sup, (270, 566))
        nombre = self.app.progreso.nombre_gato
        letrero(sup, (ANCHO // 2 - 250, 16, 500, 64), f"Tienda de {nombre}" if nombre else "Tienda del michi", 30)
        dibujar_monedero(sup, self.prog.monedas, (ANCHO - 92, 22))
        msg = ui.rico(self.mensaje, 20, TINTA, ancho=380, centrado=True)
        caja = pygame.Rect(0, 0, 420, msg.get_height() + 28)
        caja.midtop = (270, 100)
        ui.globo(sup, caja, (330, 200), TARJETA)
        sup.blit(msg, msg.get_rect(center=caja.center))
        panel = pygame.Rect(552, 96, 708, 610)
        ui.tarjeta(sup, panel, ui.PERGAMINO, 24, ui.ARENA_OSC, 6)
        if self.lugar == "conjuntos":
            nota = ui.texto("Los conjuntos traen varias prendas juntas, más baratas que por separado.", 14, SUAVE)
            sup.blit(nota, (566, 684))
        self.dibujar_botones(sup)
        self.fx.dibujar(sup)


# =============================================================== NOMBRE DEL GATO

class NombreGato(Escena):
    permite_m = False
    SUGERENCIA = "Derivia"

    def __init__(self, app, primera_vez=False):
        super().__init__(app)
        self.primera_vez = primera_vez
        self.cielo = paisaje.Cielo(semilla=11)
        self.mar = paisaje.Mar(470)
        self.gato = Gato(220)
        self.gato.reaccionar("sorpresa" if primera_vez else "feliz", 1.5)
        self.fx = Efectos()
        self.t = 0.0
        self.saliendo = None
        self.campo = CampoTexto((560, 300, 520, 62), al_enter=self.listo, al_cambiar=self._cambio,
                                placeholder="Nombre del michi", largo_max=14)
        self.campo.fredoka = True
        self.campo.poner(app.progreso.nombre_gato or "")
        pygame.key.start_text_input()
        self.armar()

    def armar(self):
        self.botones = []
        if not self.primera_vez:
            self.botones.append(Boton((24, 22, 128, 50), "Volver", self.atras, DURAZNO, tam=22))
        x0 = 560
        self.botones.append(Boton((x0 + 176, 410, 164, 50), self.SUGERENCIA,
                                  (lambda: self.campo.poner(self.SUGERENCIA)), ARENA, tam=20, relieve=4, sonido="tecla"))
        self.boton_listo = Boton((x0 + 90, 548, 340, 66), "¡Listo!", self.listo, CORAL, CREMA, tam=28,
                                 habilitado=bool(self.campo.texto.strip()))
        self.botones.append(self.boton_listo)

    def _cambio(self, texto):
        if hasattr(self, "boton_listo"):
            self.boton_listo.habilitado = bool(texto.strip())
        if texto and self.gato.animo == "normal":
            self.gato.reaccionar("feliz", 0.6, saltar=False)

    def atras(self):
        if not self.primera_vez:
            self.app.cambiar(Menu(self.app), "fundido")

    def listo(self):
        nombre = " ".join(self.campo.texto.split())[:14]
        if not nombre or self.saliendo is not None:
            return
        self.app.progreso.nombre_gato = nombre
        self.app.progreso.guardar()
        sonidos.tocar("miau")
        sonidos.tocar("estrella", 0.6)
        self.gato.reaccionar("festejo", 2)
        self.fx.confeti(300, 420, 60, 1.0)
        self.fx.texto(300, 230, f"¡Hola, {nombre}!", ui.SOL, 40, sube=30, dur=1.6)
        self.saliendo = 1.4

    def evento(self, e):
        if self.saliendo is None and self.campo.evento(e):
            return True
        return super().evento(e)

    def actualizar(self, dt):
        self.t += dt
        self.cielo.actualizar(dt)
        self.mar.actualizar(dt)
        self.gato.actualizar(dt)
        self.fx.actualizar(dt)
        self.campo.actualizar(dt)
        if self.saliendo is not None:
            self.saliendo -= dt
            if self.saliendo <= 0:
                self.saliendo = None
                self.app.cambiar(Menu(self.app), "ola")

    def dibujar(self, sup):
        self.cielo.dibujar(sup)
        self.mar.dibujar(sup)
        paisaje.dibujar_isla(sup, (40, 500), 520, 210, ui.PASTO, semilla=5, palmeras=2)
        self.gato.dibujar(sup, (300, 640))
        titulo = "¡Hola! ¿Cómo se llama tu michi?" if self.primera_vez else "¿Cómo se llama tu michi?"
        t = ui.texto_borde(titulo, 40, SOL, BORDE, 4)
        sup.blit(t, t.get_rect(midtop=(820, 120 + math.sin(self.t * 1.6) * 4)))
        sub = ui.texto_borde("Te va a acompañar en todas las islas.", 22, CREMA, BORDE, 2)
        sup.blit(sub, sub.get_rect(midtop=(820, 186)))
        rect = pygame.Rect(530, 270, 580, 370)
        ui.tarjeta(sup, rect, ui.PERGAMINO, 24, ui.ARENA_OSC, 6)
        self.campo.dibujar(sup)
        sup.blit(ui.texto("Sugerencia:", 18, SUAVE, negrita=True), (560, 422))
        self.dibujar_botones(sup)
        self.fx.dibujar(sup)


# =============================================================== REVISAR ERRORES

class RevisarErrores(Escena):
    """Los errores del nivel que terminaste: qué pusiste, qué era y por qué."""

    def __init__(self, app, juego, volver):
        super().__init__(app)
        self.j = juego
        self.volver = volver
        self.scroll = 0.0
        self.objetivo = 0.0
        self.gato = Gato(110)
        self.gato.animo_base = "pensando"
        self.gato.animo = "pensando"
        self.tarjetas = [self._tarjeta(e) for e in juego.errores_log]
        self.alto_total = sum(t.get_height() + 16 for t in self.tarjetas)
        self.botones = [Boton((24, 22, 140, 50), "Volver", self.atras, DURAZNO, tam=22)]

    def _tarjeta(self, e):
        w = 980
        partes = [ui.rico(e["consigna"], 16, SUAVE, ancho=w - 40),
                  ui.escalar_a(ui.formula(e["formula"], 30).sup, w - 40),
                  ui.rico(f"**{e['titulo']}**", 20, ui.CORAL_OSC, ancho=w - 40, color_negrita=ui.CORAL_OSC)]
        if e["tuya"]:
            partes.append(ui.rico(f"Pusiste:  {e['tuya']}", 18, TINTA, ancho=w - 40))
        partes.append(ui.rico(f"Era:  {e['correcta']}", 18, MENTA_OSC, ancho=w - 40))
        explicacion = "\n".join(t for t in (e["cuerpo"], e["explicacion"]) if t)
        if explicacion:
            partes.append(ui.rico(explicacion, 16, SUAVE, ancho=w - 40))
        alto = sum(p.get_height() + 6 for p in partes) + 24
        s = Lienzo(*((w, alto)))
        dibujo.rect(s, (226, 210, 180), s.get_rect().move(0, 4), border_radius=16)
        dibujo.rect(s, TARJETA, s.get_rect().inflate(0, -4).move(0, -2), border_radius=16)
        dibujo.rect(s, ui.ARENA_OSC, s.get_rect().inflate(0, -4).move(0, -2), 2, border_radius=16)
        y = 12
        for p in partes:
            s.blit(p, (20, y))
            y += p.get_height() + 6
        return s

    def atras(self):
        self.app.cambiar(self.volver, "fundido")

    def evento(self, e):
        if e.type == pygame.MOUSEWHEEL:
            self.objetivo = max(0, min(max(0, self.alto_total - 520), self.objetivo - e.y * 60))
            return True
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_DOWN, pygame.K_UP):
            self.objetivo = max(0, min(max(0, self.alto_total - 520), self.objetivo + (60 if e.key == pygame.K_DOWN else -60)))
            return True
        return super().evento(e)

    def actualizar(self, dt):
        self.scroll += (self.objetivo - self.scroll) * min(1, dt * 10)
        self.gato.actualizar(dt)

    def dibujar(self, sup):
        sup.blit(paisaje.pergamino(), (0, 0))
        letrero(sup, (ANCHO // 2 - 230, 16, 460, 62), "Revisar errores", 30)
        clip = sup.get_clip()
        sup.set_clip(pygame.Rect(0, 96, ANCHO, ALTO - 96))
        y = 110 - self.scroll
        for t in self.tarjetas:
            sup.blit(t, (ANCHO // 2 - t.get_width() // 2 + 60, y))
            y += t.get_height() + 16
        sup.set_clip(clip)
        if self.alto_total > 560:
            sup.blit(ui.texto("Usá la ruedita del mouse (o las flechas) para ver más", 15, SUAVE, negrita=True),
                     (ANCHO - 450, 66))
        self.gato.dibujar(sup, (90, ALTO - 10))
        self.dibujar_botones(sup)
