"""Las pantallas del juego."""

import math
import random

import pygame

from . import ui
from .mundos import MUNDOS, generar, generar_nivel, mundo_por_id
from .mate import (C, ERRORES, ErrorEntrada, casi_igual, diagnosticar, diagnosticar_primitiva, equivalentes,
                   es_primitiva, parsear, tex)
from .mate import x as VAR_X
from .mate import y as VAR_Y
from .mate import z as VAR_Z
from .ui import (ALTO, AMARILLO, AMARILLO_OSC, ANCHO, CELESTE, DURAZNO, DURAZNO_OSC, FONDO, FONDO_2, GRIS,
                 LAVANDA, LAVANDA_OSC, MENTA, MENTA_OSC, ROSA, ROSA_OSC, SUAVE, TARJETA, TINTA, Boton,
                 CampoTexto)

FRASES_BIEN = ["¡Bien!", "¡Excelente!", "¡Eso!", "¡Perfecto!", "¡Muy bien!", "¡Genial!", "¡Impecable!"]

_FONDO_CACHE = None


def fondo(sup):
    """Fondo crema con renglones de cuaderno."""
    global _FONDO_CACHE
    if _FONDO_CACHE is None:
        f = pygame.Surface((ANCHO, ALTO))
        f.fill(FONDO)
        for y in range(40, ALTO, 34):
            pygame.draw.line(f, (238, 231, 222), (0, y), (ANCHO, y), 1)
        _FONDO_CACHE = f
    sup.blit(_FONDO_CACHE, (0, 0))


def centrar(sup, s, y, x=None):
    r = s.get_rect(midtop=(x if x is not None else ANCHO // 2, y))
    sup.blit(s, r)
    return r


class Escena:
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


# =============================================================== MENÚ

class Menu(Escena):
    SIMBOLOS = ["∫", "∂", "π", "Σ", "√", "∞", "f′", "dx", "∬", "∭", "Δ", "dy", "x²", "lim"]

    def __init__(self, app):
        super().__init__(app)
        rng = random.Random()
        colores = [LAVANDA, MENTA, ROSA, CELESTE, DURAZNO]
        self.flotantes = [dict(s=rng.choice(self.SIMBOLOS), x=rng.uniform(0, ANCHO), y=rng.uniform(0, ALTO),
                               v=rng.uniform(8, 22), tam=rng.randint(30, 70), color=rng.choice(colores),
                               fase=rng.uniform(0, 6.28))
                          for _ in range(26)]
        n = len(app.progreso.cuaderno)
        cx, y = ANCHO // 2, 318
        self.botones = [
            Boton((cx - 190, y, 380, 64), "Jugar", lambda: app.cambiar(Mapa(app)), LAVANDA,
                  tam=26, tecla=[pygame.K_RETURN, pygame.K_KP_ENTER]),
            Boton((cx - 190, y + 82, 380, 64), f"Cuaderno de errores ({n})",
                  lambda: app.cambiar(Cuaderno(app)), ROSA, tam=24),
            Boton((cx - 190, y + 164, 380, 64), "Cómo escribir fórmulas",
                  lambda: app.cambiar(Ayuda(app)), MENTA, tam=24),
            Boton((cx - 190, y + 246, 380, 64), "Salir", app.salir, DURAZNO, tam=24),
        ]
        self.t = 0

    def atras(self):
        self.app.salir()

    def actualizar(self, dt):
        self.t += dt
        for f in self.flotantes:
            f["y"] -= f["v"] * dt
            if f["y"] < -80:
                f["y"] = ALTO + 40
                f["x"] = random.uniform(0, ANCHO)

    def dibujar(self, sup):
        fondo(sup)
        for f in self.flotantes:
            s = ui.texto(f["s"], f["tam"], f["color"], negrita=True)
            sup.blit(s, (f["x"] + 12 * math.sin(self.t * 0.7 + f["fase"]), f["y"]))
        titulo = ui.texto("Calculandia", 92, LAVANDA_OSC, negrita=True)
        sombra = ui.texto("Calculandia", 92, LAVANDA, negrita=True)
        centrar(sup, sombra, 108 + 5, ANCHO // 2 + 4)
        centrar(sup, titulo, 108)
        centrar(sup, ui.texto("Derivadas e integrales, nivel por nivel", 24, SUAVE), 228)
        self.dibujar_botones(sup)


# =============================================================== MAPA

class Mapa(Escena):
    def __init__(self, app, mundo_id=None):
        super().__init__(app)
        prog = app.progreso
        if mundo_id is None:
            abiertos = [m.id for m in MUNDOS if prog.mundo_desbloqueado(m.id)]
            mundo_id = abiertos[-1] if abiertos else MUNDOS[0].id
        self.sel = mundo_id
        self.armar()

    def atras(self):
        self.app.cambiar(Menu(self.app))

    def elegir_mundo(self, mid):
        self.sel = mid
        self.armar()

    def jugar(self, mid, idx):
        self.app.cambiar(Juego(self.app, mid, idx))

    def alternar_todo(self):
        p = self.app.progreso
        p.todo_desbloqueado = not p.todo_desbloqueado
        p.guardar()
        self.armar()

    def _tarjeta_mundo(self, m, w, h, abierto):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.blit(ui.texto(m.nombre, 13, SUAVE if abierto else GRIS, negrita=True), (2, 1))
        s.blit(ui.texto(m.tema, 18, TINTA if abierto else SUAVE, negrita=True), (2, 17))
        tengo, total = self.app.progreso.estrellas_mundo(m.id)
        if abierto:
            t = ui.texto(f"{tengo}/{total}", 15, SUAVE, negrita=True)
            s.blit(t, t.get_rect(midright=(w - 2, h // 2)))
            ui.estrella(s, (w - t.get_width() - 16, h // 2), 9, AMARILLO if tengo else GRIS,
                        AMARILLO_OSC if tengo else None)
        else:
            ui.candado(s, (w - 14, h // 2), 18)
        return s

    def _fila_nivel(self, m, i, nivel, w, h, abierto):
        p = self.app.progreso
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        color_num = ui.oscurecer(m.color, 0.75) if abierto else GRIS
        pygame.draw.circle(s, color_num, (28, h // 2), 24)
        num = "J" if nivel.jefe else str(i + 1)
        n = ui.texto(num, 22, TARJETA, negrita=True)
        s.blit(n, n.get_rect(center=(28, h // 2)))
        s.blit(ui.texto(nivel.nombre, 22, TINTA if abierto else SUAVE, negrita=True), (68, 8))
        desc = ui.escalar_a(ui.rico(nivel.descripcion, 17, SUAVE, ancho=w - 300), w - 300)
        s.blit(desc, (68, 40))
        etiquetas = [("Opciones" if nivel.modo == "opciones" else "Tipeo", (255, 255, 255))]
        if nivel.tiempo:
            etiquetas.append((f"{int(nivel.tiempo)} s", (255, 255, 255)))
        if nivel.jefe:
            etiquetas.append(("JEFE", ROSA))
        x = w - 220
        for txt, col in etiquetas:
            t = ui.texto(txt, 14, TINTA, negrita=True)
            r = pygame.Rect(x, 8, t.get_width() + 16, 24)
            pygame.draw.rect(s, col, r, border_radius=12)
            s.blit(t, t.get_rect(center=r.center))
            x += r.width + 6
        if abierto:
            est = p.estrellas(m.id, i)
            for k in range(3):
                ui.estrella(s, (w - 88 + k * 32, h // 2 + 10), 13, AMARILLO if k < est else (238, 234, 240),
                            AMARILLO_OSC if k < est else GRIS)
        else:
            ui.candado(s, (w - 56, h // 2 + 6), 24)
        return s

    def armar(self):
        p = self.app.progreso
        self.botones = []
        for k, m in enumerate(MUNDOS):
            abierto = p.mundo_desbloqueado(m.id)
            rect = pygame.Rect(30, 84 + k * 58, 340, 52)
            b = Boton(rect, self._tarjeta_mundo(m, rect.width - 28, rect.height - 6, abierto),
                      (lambda mid=m.id: self.elegir_mundo(mid)), m.color if abierto else (236, 232, 238),
                      habilitado=abierto, radio=14)
            b.mundo = m.id
            self.botones.append(b)
        m = mundo_por_id(self.sel)
        for i, nivel in enumerate(m.niveles):
            abierto = p.desbloqueado(m.id, i)
            rect = pygame.Rect(400, 84 + i * 96, 850, 88)
            b = Boton(rect, self._fila_nivel(m, i, nivel, rect.width - 24, rect.height - 6, abierto),
                      (lambda i=i: self.jugar(m.id, i)), TARJETA, habilitado=abierto)
            self.botones.append(b)
        self.botones.append(Boton((ANCHO - 384, 18, 130, 44), "← Menú", self.atras, FONDO_2, tam=18))
        txt = "Volver a bloquear" if p.todo_desbloqueado else "Desbloquear todo"
        self.botones.append(Boton((ANCHO - 240, 18, 210, 44), txt, self.alternar_todo, FONDO_2, tam=16))

    def dibujar(self, sup):
        fondo(sup)
        sup.blit(ui.texto("Elegí un nivel", 30, TINTA, negrita=True), (30, 22))
        m = mundo_por_id(self.sel)
        sup.blit(ui.texto(f"{m.nombre}: {m.tema}", 21, SUAVE), (402, 34))
        for b in self.botones:
            if getattr(b, "mundo", None) == self.sel:
                pygame.draw.rect(sup, ui.oscurecer(m.color, 0.6), b.rect.inflate(8, 8), 3, border_radius=18)
        self.dibujar_botones(sup)


# =============================================================== JUEGO

TECLADO = [("x²", "^2", 0), ("^", "^", 0), ("()", "()", 1), ("sen", "sen()", 1), ("cos", "cos()", 1),
           ("e^", "e^()", 1), ("ln", "ln()", 1), ("√", "raiz()", 1), ("/", "/", 0), ("·", "*", 0)]


class Particula:
    def __init__(self, x, y):
        a = random.uniform(0, math.tau)
        v = random.uniform(120, 360)
        self.x, self.y = x, y
        self.vx, self.vy = math.cos(a) * v, math.sin(a) * v - 160
        self.vida = random.uniform(0.6, 1.1)
        self.color = random.choice([LAVANDA_OSC, MENTA_OSC, ROSA_OSC, AMARILLO_OSC, DURAZNO_OSC])
        self.tam = random.randint(4, 8)

    def actualizar(self, dt):
        self.vida -= dt
        self.vy += 600 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    def dibujar(self, sup):
        if self.vida > 0:
            pygame.draw.rect(sup, self.color, (self.x, self.y, self.tam, self.tam), border_radius=2)


class Juego(Escena):
    def __init__(self, app, mundo_id, nivel_idx, practica=None):
        super().__init__(app)
        self.practica = practica is not None
        self.repasos = set()
        if self.practica:
            self.mundo = None
            self.nivel = None
            self.ejercicios = [generar(c["mundo"], c["nivel"], c["gen"], c["semilla"]) for c in practica]
            self.vidas_max = 5
            self.titulo = "Repaso del cuaderno de errores"
            self.color = ROSA
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
        self.racha = 0
        self.errores = 0
        self.pistas_usadas = 0
        self.resultados = []
        self.al_cuaderno = 0
        self.sacados = 0
        self.particulas = []
        self.sacudir = 0
        self.campo = CampoTexto((0, 0, 560, 58), al_enter=self.comprobar, al_cambiar=self._previsualizar)
        pygame.key.start_text_input()
        self.empezar_ejercicio()

    # ---------------------------------------------- armado
    def _meter_repaso(self):
        """Mete un ejercicio del cuaderno de errores entre los del nivel."""
        cuaderno = self.app.progreso.cuaderno
        orden = [m.id for m in MUNDOS]
        hasta = orden.index(self.mundo.id)
        candidatos = [c for c in cuaderno if c["clave"]["mundo"] in orden and orden.index(c["clave"]["mundo"]) <= hasta]
        if candidatos and random.random() < 0.7:
            c = random.choice(candidatos)["clave"]
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
        self.empezar_paso()

    def empezar_paso(self):
        self.paso = self.ej.pasos[self.paso_i]
        self.intentos = 0
        self.pistas_vistas = 0
        self.feedback = None
        self.estado = "pregunta"     # pregunta | bien | revelado | sin_vidas
        self.marcadas = {}
        self.t_paso = 0
        self.auto_t = None
        self.preview = None
        self.campo.poner("")
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
            extra.append(("+C", "+C", 0))
        if self.paso.chequeo == "numero":
            extra = [("π", "pi", 0), ("e", "e", 0)]
            teclas = [t for t in teclas if t[0] not in ("sen", "cos", "e^", "ln")]
        return teclas + extra

    def armar(self):
        """Calcula la ubicación de todo según el estado actual."""
        self.botones = [Boton((14, 12, 112, 40), "← Salir", self.atras, ui.aclarar(self.color, 0.5), tam=17)]
        self.capas = []
        if self.ej.grafico:
            # a la derecha va el dibujo de la región; el resto se corre a la izquierda
            self.cx, self.ancho = 480, 860
            g = ui.grafico(self.ej.grafico)
            self.capas.append((g, g.get_rect(topright=(ANCHO - 24, 104))))
        else:
            self.cx, self.ancho = ANCHO // 2, 1100
        cx, ancho = self.cx, self.ancho
        y = 104
        consigna = self.ej.consigna
        if self.i in self.repasos or self.practica:
            consigna = "**Repaso del cuaderno** · " + consigna
        s = ui.rico(consigna, 20, SUAVE, ancho=ancho)
        self.capas.append((s, s.get_rect(midtop=(cx, y))))
        y += s.get_height() + 4
        f = ui.formula(self.ej.formula, 44)
        s = ui.escalar_a(f.sup, ancho)
        self.capas.append((s, s.get_rect(midtop=(cx, y))))
        y += s.get_height() + 14
        # pasos ya hechos
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
        # pregunta
        n_pasos = len(self.ej.pasos)
        pregunta = self.paso.pregunta
        if n_pasos > 1:
            pregunta = f"**Paso {self.paso_i + 1} de {n_pasos}.** " + pregunta
        s = ui.rico(pregunta, 24, TINTA, ancho=ancho, color_negrita=LAVANDA_OSC)
        self.capas.append((s, s.get_rect(midtop=(cx, y))))
        y += s.get_height() + 16

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
                anchos = [max(46, ui.texto(et, 18, TINTA, negrita=True).get_width() + 22) for et, _, _ in teclas]
                total = sum(anchos) + 7 * (len(anchos) - 1)
                x = cx - total // 2
                for (et, ins, ret), w in zip(teclas, anchos):
                    self.botones.append(Boton((x, y, w, 38), et, (lambda a=ins, b=ret: self.campo.insertar(a, b)),
                                              FONDO_2, tam=18, radio=10))
                    x += w + 7
                y += 50
                fila = []
                if self.paso.pistas and not self.jefe and self.pistas_vistas < len(self.paso.pistas):
                    fila.append(("Pista (−5)", self.pista, AMARILLO))
                fila.append(("Comprobar  ↵", self.comprobar, LAVANDA))
                total = len(fila) * 230 + (len(fila) - 1) * 16
                x = cx - total // 2
                for txt, acc, col in fila:
                    self.botones.append(Boton((x, y, 230, 50), txt, acc, col, tam=20))
                    x += 246
                y += 58
        else:
            ops = self.paso.opciones
            con_texto = any(o.texto for o in ops)
            alto = 62 if con_texto else 84
            cols = 2
            w = min(540, (ancho - 18) // 2)
            x0 = cx - (cols * w + 18) // 2
            for k, o in enumerate(ops):
                fila, col = divmod(k, cols)
                rect = (x0 + col * (w + 18), y + fila * (alto + 14), w, alto)
                contenido = o.texto if o.texto else ui.formula(ui.fracciones_grandes(o.tex), 28).sup
                b = Boton(rect, contenido, (lambda k=k: self.elegir(k)), TARJETA, tam=21,
                          tecla=[pygame.K_1 + k, pygame.K_KP1 + k], habilitado=respondiendo and k not in self.marcadas,
                          etiqueta_tecla=str(k + 1))
                b.marcado = self.marcadas.get(k)
                self.botones.append(b)
            y += ((len(ops) + 1) // 2) * (alto + 14)
            if respondiendo and self.paso.pistas and not self.jefe and self.pistas_vistas < len(self.paso.pistas):
                self.botones.append(Boton((cx - 115, y, 230, 46), "Pista (−5)", self.pista, AMARILLO, tam=19))
                y += 54
        # panel de feedback o de pistas
        self.panel = None
        y += 4
        if self.feedback:
            self.panel = self._panel_feedback(y)
        elif self.pistas_vistas:
            cuerpo = "\n".join(self.paso.pistas[:self.pistas_vistas])
            self.panel = self._panel(y, "Pista", cuerpo, (240, 234, 252), LAVANDA_OSC)

    def _panel(self, y, titulo, cuerpo, color, color_titulo, con_boton=False):
        ancho = 1060 if not con_boton else 860
        t = ui.texto(titulo, 22, color_titulo, negrita=True)
        c = ui.rico(cuerpo, 19, TINTA, ancho=ancho, color_negrita=color_titulo) if cuerpo else None
        alto = 22 + t.get_height() + (c.get_height() + 8 if c else 0) + 16
        alto = max(alto, 84 if con_boton else 0)
        rect = pygame.Rect(60, y, ANCHO - 120, alto)
        if rect.bottom > ALTO - 8:
            rect.bottom = ALTO - 8
        if con_boton:
            b = Boton((rect.right - 196, rect.centery - 27, 176, 54), "Continuar  ↵", self.continuar, LAVANDA,
                      tam=19, tecla=[pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE])
            self.botones.append(b)
        return dict(rect=rect, color=color, titulo=t, cuerpo=c, borde=color_titulo)

    def _panel_feedback(self, y):
        fb = self.feedback
        if fb["tipo"] == "bien":
            return self._panel(y, fb["titulo"], fb["cuerpo"], (226, 246, 236), MENTA_OSC,
                               con_boton=self.auto_t is None)
        if fb["tipo"] == "info":
            return self._panel(y, fb["titulo"], fb["cuerpo"], (244, 240, 248), SUAVE)
        return self._panel(y, fb["titulo"], fb["cuerpo"], (253, 234, 238), ROSA_OSC,
                           con_boton=self.estado in ("revelado", "sin_vidas"))

    # ---------------------------------------------- acciones
    def atras(self):
        if self.practica:
            self.app.cambiar(Cuaderno(self.app))
        else:
            self.app.cambiar(Mapa(self.app, self.mundo.id))

    def _previsualizar(self, texto):
        if not texto.strip():
            self.preview = None
            return
        try:
            self.preview = ("ok", tex(self._parsear(texto)))
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
            if self.feedback and self.feedback["tipo"] != "bien":
                self.feedback = None
            self.armar()

    def _parsear(self, texto):
        return parsear(texto, self.paso.variables, permitir_c=self.paso.chequeo == "primitiva")

    def comprobar(self):
        if self.estado != "pregunta" or self.paso.tipo != "expresion":
            return
        try:
            r = self._parsear(self.campo.texto)
        except ErrorEntrada as ex:
            self.feedback = dict(tipo="info", titulo="No entiendo lo que escribiste",
                                 cuerpo=f"{ex} (Esto no te saca vidas. En el menú está la ayuda para escribir fórmulas.)")
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
                self.fallo(titulo, cuerpo)
            return
        if equivalentes(r, p.esperado):
            self.acierto()
        elif p.chequeo == "numero" and casi_igual(r, p.esperado):
            self.acierto(f"Está bien, pero en el parcial dejalo exacto: ${tex(p.esperado)}$.")
        else:
            _, titulo, cuerpo = diagnosticar(r, p.esperado, p.errores, p.original)
            self.fallo(titulo, cuerpo)

    def elegir(self, k):
        if self.estado != "pregunta":
            return
        o = self.paso.opciones[k]
        if o.correcta:
            self.marcadas[k] = "bien"
            self.acierto()
        else:
            self.marcadas[k] = "mal"
            titulo, cuerpo = ERRORES.get(o.error, ("Todavía no", "Esa no es."))
            self.fallo(titulo, cuerpo)

    def _festejo(self):
        cx = self.cx
        cy = self.campo.rect.centery if self.paso.tipo == "expresion" else 420
        self.particulas += [Particula(cx + random.uniform(-200, 200), cy) for _ in range(28)]

    def acierto(self, nota=""):
        self.racha += 1
        pts = 10 + 2 * min(self.racha - 1, 5)
        if self.tiempo:
            pts += max(0, int(self.tiempo - self.t_paso))
        self.puntos += pts
        self.estado = "bien"
        cuerpo = self.paso.explicacion
        if self.paso.tipo == "expresion" and self.paso.mostrar:
            cuerpo = f"${self.paso.prefijo} {self.paso.mostrar}$\n{cuerpo}"
        if nota:
            cuerpo = f"**{nota}**\n{cuerpo}" if cuerpo else f"**{nota}**"
        self.feedback = dict(tipo="bien", titulo=f"{random.choice(FRASES_BIEN)}   +{pts}", cuerpo=cuerpo)
        if (not self.paso.explicacion and not nota) or self.tiempo:
            self.auto_t = 0.9 if not self.tiempo else 1.6
        for k, o in enumerate(self.paso.opciones):
            if o.correcta:
                self.marcadas[k] = "bien"
        self._festejo()
        self.armar()

    def fallo(self, titulo, cuerpo, sin_reintento=False):
        self.vidas -= 1
        self.racha = 0
        self.errores += 1
        self.intentos += 1
        self.fallo_ej = True
        self.sacudir = 0.4
        if self.vidas <= 0 or sin_reintento or self.intentos >= self.paso.max_intentos:
            self.estado = "sin_vidas" if self.vidas <= 0 else "revelado"
            self.pasos_revelados.add(self.paso_i)
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
        faltas = self.errores + self.pistas_usadas
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
    def evento(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.atras()
            return True
        if self.estado == "pregunta" and self.paso.tipo == "expresion":
            if e.type == pygame.MOUSEBUTTONDOWN and not self.campo.rect.collidepoint(e.pos):
                pass
            elif self.campo.evento(e):
                return True
        if self.estado in ("bien",) and self.auto_t is not None and e.type == pygame.KEYDOWN and \
                e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            self.continuar()
            return True
        for b in list(self.botones):
            if b.evento(e):
                return True
        return False

    def actualizar(self, dt):
        self.campo.actualizar(dt)
        self.sacudir = max(0, self.sacudir - dt)
        for p in self.particulas:
            p.actualizar(dt)
        self.particulas = [p for p in self.particulas if p.vida > 0]
        if self.estado == "pregunta" and self.tiempo:
            self.t_paso += dt
            if self.t_paso >= self.tiempo:
                self.fallo("¡Se acabó el tiempo!", "", sin_reintento=True)
        if self.auto_t is not None and self.estado == "bien":
            self.auto_t -= dt
            if self.auto_t <= 0:
                self.auto_t = None
                self.continuar()

    def _dibujar_encabezado(self, sup):
        pygame.draw.rect(sup, ui.aclarar(self.color, 0.35), (0, 0, ANCHO, 64))
        pygame.draw.line(sup, ui.oscurecer(self.color, 0.85), (0, 64), (ANCHO, 64), 2)
        t = ui.texto(self.titulo, 22, TINTA, negrita=True)
        sup.blit(t, (142, 32 - t.get_height() // 2))
        x = 142 + t.get_width() + 14
        if self.jefe:
            et = ui.texto("JEFE", 15, TARJETA, negrita=True)
            r = pygame.Rect(x, 20, et.get_width() + 18, 26)
            pygame.draw.rect(sup, ROSA_OSC, r, border_radius=13)
            sup.blit(et, et.get_rect(center=r.center))
        # vidas
        x = ANCHO - 30
        for k in range(self.vidas_max - 1, -1, -1):
            ui.corazon(sup, (x, 32), 26, ROSA_OSC if k < self.vidas else GRIS)
            x -= 34
        x -= 20
        pts = ui.texto(str(self.puntos), 22, TINTA, negrita=True)
        sup.blit(pts, (x - pts.get_width(), 32 - pts.get_height() // 2))
        x -= pts.get_width() + 22
        ui.estrella(sup, (x, 32), 13, AMARILLO, AMARILLO_OSC)
        x -= 34
        if self.racha >= 2:
            rt = ui.texto(f"racha ×{self.racha}", 17, TINTA, negrita=True)
            r = pygame.Rect(0, 0, rt.get_width() + 22, 30)
            r.midright = (x, 32)
            pygame.draw.rect(sup, DURAZNO, r, border_radius=15)
            sup.blit(rt, rt.get_rect(center=r.center))
        # puntitos de progreso
        n = len(self.ejercicios)
        x0 = ANCHO // 2 - (n - 1) * 13
        for k in range(n):
            c = (x0 + k * 26, 82)
            if k < len(self.resultados):
                pygame.draw.circle(sup, MENTA_OSC if self.resultados[k] == "bien" else ROSA_OSC, c, 7)
            elif k == self.i:
                pygame.draw.circle(sup, LAVANDA_OSC, c, 9, 3)
            else:
                pygame.draw.circle(sup, GRIS, c, 6)
        if self.tiempo:
            restante = max(0.0, 1 - self.t_paso / self.tiempo) if self.estado == "pregunta" else \
                max(0.0, 1 - min(self.t_paso, self.tiempo) / self.tiempo)
            r = pygame.Rect(ANCHO // 2 - 220, 94, 440, 8)
            pygame.draw.rect(sup, (234, 228, 236), r, border_radius=4)
            col = MENTA_OSC if restante > 0.5 else (DURAZNO_OSC if restante > 0.25 else ROSA_OSC)
            pygame.draw.rect(sup, col, (r.left, r.top, int(r.width * restante), r.height), border_radius=4)

    def dibujar(self, sup):
        fondo(sup)
        self._dibujar_encabezado(sup)
        for s, r in self.capas:
            if s == "tilde":
                ui.tilde(sup, r, 18, MENTA_OSC, 3)
            elif s == "cruz":
                ui.cruz(sup, r, 18, ROSA_OSC, 3)
            else:
                sup.blit(s, r)
        if self.paso.tipo == "expresion":
            dx = int(math.sin(self.sacudir * 50) * 8 * (self.sacudir / 0.4)) if self.sacudir else 0
            orig = self.campo.rect
            self.campo.rect = orig.move(dx, 0)
            self.campo.dibujar(sup)
            self.campo.rect = orig
            if self.preview and self.estado == "pregunta":
                if self.preview[0] == "ok":
                    et = ui.texto("Leo:", 18, SUAVE)
                    fm = ui.escalar_a(ui.formula(self.preview[1], 26, LAVANDA_OSC).sup, 900)
                    w = et.get_width() + 12 + fm.get_width()
                    x = self.cx - w // 2
                    cy = self.y_preview + 18
                    sup.blit(et, (x, cy - et.get_height() // 2))
                    sup.blit(fm, (x + et.get_width() + 12, cy - fm.get_height() // 2))
                else:
                    centrar(sup, ui.texto(self.preview[1], 18, SUAVE), self.y_preview + 6, self.cx)
        if self.panel:
            p = self.panel
            ui.caja(sup, p["rect"], p["color"], radio=16, sombra=False, borde=p["borde"], grosor=2)
            sup.blit(p["titulo"], (p["rect"].left + 22, p["rect"].top + 14))
            if p["cuerpo"]:
                sup.blit(p["cuerpo"], (p["rect"].left + 22, p["rect"].top + 22 + p["titulo"].get_height()))
        self.dibujar_botones(sup)
        for part in self.particulas:
            part.dibujar(sup)


# =============================================================== FIN DE NIVEL

class FinNivel(Escena):
    def __init__(self, app, juego, gano, estrellas=0, nuevo_mundo=None):
        super().__init__(app)
        self.j = juego
        self.gano = gano
        self.estrellas = estrellas
        self.nuevo_mundo = nuevo_mundo
        self.t = 0
        cx = ANCHO // 2
        y = 560
        b = []
        if juego.practica:
            b.append(("Volver al cuaderno", lambda: app.cambiar(Cuaderno(app)), LAVANDA))
        else:
            m, i = juego.mundo, juego.nivel_idx
            if gano:
                if i + 1 < len(m.niveles):
                    b.append(("Siguiente nivel", lambda: app.cambiar(Juego(app, m.id, i + 1)), LAVANDA))
                elif nuevo_mundo:
                    b.append((f"Ir al {nuevo_mundo.nombre}", lambda: app.cambiar(Mapa(app, nuevo_mundo.id)), LAVANDA))
                b.append(("Repetir", lambda: app.cambiar(Juego(app, m.id, i)), MENTA))
            else:
                b.append(("Reintentar", lambda: app.cambiar(Juego(app, m.id, i)), LAVANDA))
            b.append(("Mapa", lambda: app.cambiar(Mapa(app, m.id)), FONDO_2))
        total = len(b) * 240 + (len(b) - 1) * 18
        x = cx - total // 2
        for k, (txt, acc, col) in enumerate(b):
            teclas = [pygame.K_RETURN, pygame.K_KP_ENTER] if k == 0 else None
            self.botones.append(Boton((x, y, 240, 58), txt, acc, col, tam=21, tecla=teclas))
            x += 258

    def atras(self):
        if self.j.practica:
            self.app.cambiar(Cuaderno(self.app))
        else:
            self.app.cambiar(Mapa(self.app, self.j.mundo.id))

    def actualizar(self, dt):
        self.t += dt

    def dibujar(self, sup):
        fondo(sup)
        tarjeta = pygame.Rect(ANCHO // 2 - 380, 60, 760, 470)
        ui.caja(sup, tarjeta, TARJETA, radio=28)
        j = self.j
        if self.gano:
            titulo = "¡Repaso terminado!" if j.practica else "¡Nivel superado!"
            color = MENTA_OSC
        else:
            titulo, color = "Te quedaste sin vidas", ROSA_OSC
        centrar(sup, ui.texto(titulo, 42, color, negrita=True), 92)
        y = 168
        if self.gano and not j.practica:
            for k in range(3):
                aparece = min(1.0, max(0.0, (self.t - 0.25 - k * 0.3) * 4))
                tam = 38 * (aparece + 0.25 * math.sin(aparece * math.pi)) if aparece else 0
                c = (ANCHO // 2 - 100 + k * 100, y + 44)
                ui.estrella(sup, c, 38, (240, 236, 242), GRIS)
                if k < self.estrellas and tam > 2:
                    ui.estrella(sup, c, tam, AMARILLO, AMARILLO_OSC)
            y += 110
            frase = {3: "¡Perfecto! Ni un error ni una pista.", 2: "¡Muy bien! Casi perfecto.",
                     1: "Aprobado. Repetilo para sacar las 3 estrellas."}[self.estrellas]
            centrar(sup, ui.texto(frase, 22, SUAVE), y)
            y += 46
        elif not self.gano:
            centrar(sup, ui.rico("No pasa nada: **así se aprende**. Mirá bien la explicación del error y volvé a intentarlo.",
                                 21, SUAVE, ancho=640, centrado=True), y + 10)
            y += 90
        bien = sum(1 for r in j.resultados if r == "bien")
        datos = [("Puntos", str(j.puntos)), ("Ejercicios sin errores", f"{bien} de {len(j.ejercicios)}"),
                 ("Errores", str(j.errores)), ("Pistas", str(j.pistas_usadas))]
        for k, (a, b) in enumerate(datos):
            col, fila = k % 2, k // 2
            x = ANCHO // 2 - 300 + col * 320
            sup.blit(ui.texto(a, 18, SUAVE), (x, y + fila * 52))
            sup.blit(ui.texto(b, 24, TINTA, negrita=True), (x, y + 20 + fila * 52))
        y += 116
        mensajes = []
        if self.nuevo_mundo:
            mensajes.append(f"¡Desbloqueaste el **{self.nuevo_mundo.nombre}: {self.nuevo_mundo.tema}**!")
        if j.al_cuaderno:
            mensajes.append(f"{j.al_cuaderno} ejercicio(s) fueron al **cuaderno de errores** para repasar.")
        if j.sacados:
            mensajes.append(f"Sacaste {j.sacados} ejercicio(s) del cuaderno. ¡Ya te salen!")
        for m in mensajes:
            s = ui.rico(m, 19, TINTA, ancho=680, centrado=True, color_negrita=LAVANDA_OSC)
            centrar(sup, s, y)
            y += s.get_height() + 4
        self.dibujar_botones(sup)


# =============================================================== CUADERNO

class Cuaderno(Escena):
    MAX = 8

    def __init__(self, app):
        super().__init__(app)
        self.items = list(app.progreso.cuaderno)
        self.botones = [Boton((40, 640, 170, 50), "← Menú", self.atras, FONDO_2, tam=20)]
        if self.items:
            self.botones.append(Boton((ANCHO - 340, 640, 300, 54), f"Practicar ({min(len(self.items), self.MAX)})",
                                      self.practicar, ROSA, tam=22, tecla=[pygame.K_RETURN, pygame.K_KP_ENTER]))

    def atras(self):
        self.app.cambiar(Menu(self.app))

    def practicar(self):
        claves = [c["clave"] for c in self.items[:self.MAX]]
        random.shuffle(claves)
        self.app.cambiar(Juego(self.app, None, None, practica=claves))

    def dibujar(self, sup):
        fondo(sup)
        sup.blit(ui.texto("Cuaderno de errores", 34, TINTA, negrita=True), (40, 30))
        sup.blit(ui.rico("Acá van los ejercicios en los que te equivocaste. Cada uno sale cuando lo resolvés **2 veces sin errores** "
                         "(acá o cuando te aparece de repaso en un nivel).", 19, SUAVE, ancho=1180), (40, 80))
        if not self.items:
            s = ui.rico("¡Está vacío! Cuando te equivoques en un ejercicio, va a aparecer acá para que lo repases.",
                        24, SUAVE, ancho=800, centrado=True)
            centrar(sup, s, 300)
        y = 140
        for item in self.items[:self.MAX]:
            r = pygame.Rect(40, y, ANCHO - 80, 50)
            ui.caja(sup, r, TARJETA, radio=14)
            c = item["clave"]
            try:
                m = mundo_por_id(c["mundo"])
                lugar = f"{m.nombre} · {m.niveles[c['nivel']].nombre}"
            except (KeyError, IndexError):
                lugar = ""
            sup.blit(ui.texto(lugar, 17, SUAVE), (r.left + 18, r.centery - 10))
            f = ui.escalar_a(ui.formula(item["formula"], 26).sup, 640)
            sup.blit(f, f.get_rect(midleft=(r.left + 360, r.centery)))
            rep = ui.texto(f"repasos {item['repasos']}/2", 17, LAVANDA_OSC, negrita=True)
            sup.blit(rep, rep.get_rect(midright=(r.right - 18, r.centery)))
            y += 58
        if len(self.items) > self.MAX:
            sup.blit(ui.texto(f"…y {len(self.items) - self.MAX} más", 18, SUAVE), (ANCHO // 2 - 40, 656))
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
        ("Fracción", "(x+1)/(x^2+1)", ["(x+1)/(x^2+1)"]),
        ("Seno al cuadrado", "sen(x)^2", ["sen(x)^2"]),
        ("Decimales", "0,5x", ["0,5x"]),
        ("Otras variables", "3x^2y + z", ["3x^2y+z"]),
        ("Constante de integración", "x^3/3 + C", ["x^3/3+C"]),
        ("Pi", "8pi/3", ["8pi/3"]),
    ]

    def __init__(self, app):
        super().__init__(app)
        self.botones = [Boton((40, 650, 170, 50), "← Menú", self.atras, FONDO_2, tam=20)]
        self.filas = [(nombre, ejemplo, r"\quad ".join(tex(parsear(m, (VAR_X, VAR_Y, VAR_Z), True)) for m in muestras))
                      for nombre, ejemplo, muestras in self.FILAS]

    def atras(self):
        self.app.cambiar(Menu(self.app))

    def dibujar(self, sup):
        fondo(sup)
        sup.blit(ui.texto("Cómo escribir fórmulas", 34, TINTA, negrita=True), (40, 30))
        x1, x2, x3 = 60, 290, 560
        y = 92
        for et, x in [("Para escribir…", x1), ("tipeás", x2), ("y se ve así", x3)]:
            sup.blit(ui.texto(et, 18, SUAVE, negrita=True), (x, y))
        y += 32
        for nombre, ejemplo, vista in self.filas:
            r = pygame.Rect(40, y, 760, 36)
            ui.caja(sup, r, TARJETA, radio=12, sombra=False)
            sup.blit(ui.texto(nombre, 18, TINTA), (x1, y + 8))
            sup.blit(ui.texto(ejemplo, 18, LAVANDA_OSC, mono=True, negrita=True), (x2, y + 8))
            if vista:
                f = ui.escalar_a(ui.formula(vista, 22).sup, 230)
                sup.blit(f, f.get_rect(midleft=(x3, y + 18)))
            y += 40
        consejos = ("**Consejos**\n"
                    "• Usá paréntesis: **e^2x** se lee como $e^2\\cdot x$. Para $e^{2x}$ escribí **e^(2x)**.\n"
                    "• Debajo del cuadro vas a ver «Leo: …» con cómo entendí lo que escribiste. Si no es lo que querías, agregá paréntesis.\n"
                    "• No hace falta simplificar: si es la misma función escrita distinto, está bien.\n"
                    "• Si tu teclado escribe â cuando apretás ^, no pasa nada: lo entiendo igual. También tenés los botones de abajo del cuadro.\n"
                    "• En las integrales podés poner **+ C** o no: se corrige derivando tu respuesta.\n"
                    "• Equivocarte al tipear (algo que no se entiende) **no** te saca vidas.")
        caja = pygame.Rect(830, 124, 410, 520)
        ui.caja(sup, caja, (240, 234, 252), radio=18, sombra=False)
        sup.blit(ui.rico(consejos, 18, TINTA, ancho=370, color_negrita=LAVANDA_OSC), (caja.left + 20, caja.top + 18))
        self.dibujar_botones(sup)
