"""Cómo se ve un nivel: dónde va cada cosa en la pantalla y cómo se dibuja.

La franja de abajo es del gato (su globito o, si no habla, Pista y Saltear). El ejercicio va arriba
de esa franja y, si no entra, se compacta de a poco. Nada se pisa: lo controla tests/test_superposicion.py."""

import math
from dataclasses import dataclass

import pygame

from .. import lienzo as dibujo
from .. import paisaje, pincel, ui
from ..cache import CacheDibujos
from ..fx import rebote, suave
from ..lienzo import Lienzo
from ..ui import (
    ALTO,
    ANCHO,
    ARENA,
    ARENA_OSC,
    BORDE,
    CORAL,
    DURAZNO,
    GRIS,
    LAVANDA,
    LAVANDA_OSC,
    MADERA,
    MADERA_OSC,
    MENTA_OSC,
    ROSA_OSC,
    SOL,
    SOL_OSC,
    SUAVE,
    TARJETA,
    TINTA,
    Boton,
)
from .base import CREMA, centrar

_VELO = CacheDibujos()


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
    s = Lienzo(t.get_width() + 44 + 12, 30 + 12)
    pieza, m = pincel.pastilla(t.get_width() + 44, 30, color) if pincel.HAY_SKIA else (None, 0)
    if pieza is not None:
        s.blit(pieza, (6 - m, 6 - m))
    else:
        dibujo.rect(s, BORDE, (6, 6, t.get_width() + 44, 30), border_radius=15)
        dibujo.rect(s, color, pygame.Rect(6, 6, t.get_width() + 44, 30).inflate(-4, -4), border_radius=13)
    marco = s
    s = Lienzo(t.get_width() + 44, 30)   # el dibujo de adentro, después se pega con el margen

    if logica:   # lamparita
        dibujo.circle(s, (255, 236, 140), (17, 13), 7)
        dibujo.rect(s, (230, 230, 230), (14, 19, 7, 5), border_radius=2)
    else:        # lápiz
        dibujo.line(s, (255, 214, 102), (10, 22), (22, 9), 5)
        dibujo.polygon(s, (255, 236, 200), [(8, 25), (10, 19), (14, 23)])
    s.blit(t, (32, 15 - t.get_height() // 2))
    marco.blit(s, (6, 6))
    _VELO[clave] = marco
    return marco


def flecha_reiniciar(sup, centro, tam, color):
    cx, cy = centro
    r = pygame.Rect(0, 0, tam, tam)
    r.center = centro
    dibujo.arc(sup, color, r, 0.6, math.tau - 0.2, 4)
    dibujo.polygon(sup, color, [(cx + tam * 0.5, cy - tam * 0.42), (cx + tam * 0.52, cy), (cx + tam * 0.12, cy - tam * 0.14)])


# (etiqueta en LaTeX, lo que se inserta, cuántos lugares vuelve el cursor) — como en la calculadora.
# Van por grupos (cada uno con su color), en el orden en que se piensa una fórmula:
# operaciones, potencias y raíces, funciones. Los extras (y, z, +C, π, e) van al final.
@dataclass(frozen=True)
class Tecla:
    """Una tecla del teclado de fórmulas (como las de la calculadora Casio fx-991LA CW).
    etiqueta: lo que se ve (LaTeX sin $, o texto). texto: lo que escribe; retroceso: cuántos lugares
    vuelve el cursor después (para quedar adentro del paréntesis o del casillero). accion: en vez de
    escribir, mueve el cursor o borra ("izquierda", "derecha", "borrar", "limpiar")."""
    etiqueta: str
    texto: str = ""
    retroceso: int = 0
    estilo: str = "funcion"       # funcion | variable | numero | operacion | borrar
    accion: str = ""
    formula: bool = True          # la etiqueta se dibuja como fórmula
    icono: str = ""               # o se dibuja a mano (fracción, raíz enésima): ver _ICONOS


def _icono_fraccion(color):
    """□ arriba, rayita, □ abajo (como la tecla de fracción de la calculadora)."""
    s = Lienzo(24, 30)
    dibujo.rect(s, color, (6, 1, 12, 10), 2, border_radius=2)
    dibujo.line(s, color, (2, 15), (22, 15), 2)
    dibujo.rect(s, color, (6, 19, 12, 10), 2, border_radius=2)
    return s


def _icono_raiz_n(color):
    """Raíz con un □ chiquito de índice y un □ adentro."""
    raiz = ui.formula(r"\sqrt{□}", 24, color).sup
    s = Lienzo(raiz.get_width() + 9, 30)
    dibujo.rect(s, color, (1, 3, 9, 8), 2, border_radius=2)
    s.blit(raiz, (8, 30 - raiz.get_height()))
    return s


_ICONOS = {"fraccion": _icono_fraccion, "raiz_n": _icono_raiz_n}


# fila de arriba: las teclas oscuras de funciones, con casilleros □ como en la calculadora
TECLAS_FUNCIONES = [
    Tecla("□/□", "()/()", 4, icono="fraccion"),
    Tecla(r"\sqrt{□}", "raiz()", 1),
    Tecla("ⁿ√□", "raiz[]()", 3, icono="raiz_n"),
    Tecla("x^{2}", "^2"),
    Tecla("x^{□}", "^()", 1),
    Tecla("e^{□}", "e^()", 1),
    Tecla(r"\ln", "ln()", 1),
    Tecla(r"\mathrm{sen}", "sen()", 1),
    Tecla(r"\cos", "cos()", 1),
    Tecla(r"\mathrm{tg}", "tg()", 1),
    Tecla("(", "("),
    Tecla(")", ")"),
]
# fila de abajo: números y operaciones (claras), flechas, y DEL / AC
TECLAS_NUMEROS = [Tecla(n, n, estilo="numero", formula=False) for n in "1234567890,"]
TECLAS_OPERACIONES = [Tecla(r"\times", "*", estilo="operacion"), Tecla(r"\div", "/", estilo="operacion"),
                      Tecla("+", "+", estilo="operacion"), Tecla("-", "-", estilo="operacion")]
TECLAS_EDICION = [Tecla("◀", accion="izquierda", formula=False), Tecla("▶", accion="derecha", formula=False),
                  Tecla("DEL", accion="borrar", estilo="borrar", formula=False),
                  Tecla("AC", accion="limpiar", estilo="borrar", formula=False)]

def _otro_grupo(anterior, tecla):
    """Entre grupos de teclas (funciones, variables, números, operaciones, flechas, DEL/AC) va un espacio."""
    return tecla.estilo != anterior.estilo or (bool(tecla.accion) and not anterior.accion)


ESTILOS_TECLA = {             # (fondo, letra)
    "funcion": ((66, 72, 90), (255, 255, 255)),
    "variable": ((66, 72, 90), (255, 255, 255)),
    "numero": ((250, 248, 242), TINTA),
    "operacion": ((224, 228, 240), TINTA),
    "borrar": ((236, 120, 92), (255, 255, 255)),
}


PIE_GATO = (96, ALTO - 8)


BOCA_GATO = (150, ALTO - 120)


X_GLOBO = 196

# donde está sentado el gato (abajo a la izquierda): ahí no puede ir ningún botón
ZONA_GATO = pygame.Rect(0, ALTO - 165, X_GLOBO - 10, 165)


class PantallaNivel:
    """La parte visual de Juego (se usa como clase madre, junto con Escena)."""

    def _teclado(self):
        """Las dos filas del teclado para este paso: funciones (más x, y, z, + C o pi y e, según haga
        falta) y números con operaciones y edición."""
        extra = [Tecla(str(v), str(v), estilo="variable") for v in self.paso.variables]
        if self.paso.chequeo == "primitiva":
            extra.append(Tecla(r"+\,C", "+C", estilo="variable"))
        if self.paso.chequeo == "numero":
            extra += [Tecla(r"\pi", "pi", estilo="variable"), Tecla("e", "e", estilo="variable")]
        return [TECLAS_FUNCIONES + extra, TECLAS_NUMEROS + TECLAS_OPERACIONES + TECLAS_EDICION]

    def _boton_tecla(self, tecla, x, y, w):
        fondo, letra = ESTILOS_TECLA[tecla.estilo]
        if tecla.icono:
            contenido, tam = _ICONOS[tecla.icono](letra), 19
        elif tecla.formula:
            contenido, tam = ui.formula(tecla.etiqueta, 22, letra).sup, 19
        else:
            contenido, tam = tecla.etiqueta, (16 if len(tecla.etiqueta) > 1 else 19)
        acciones = {"izquierda": self.campo.izquierda, "derecha": self.campo.derecha,
                    "borrar": self.campo.borrar_atras, "limpiar": lambda: self.campo.poner("")}
        accion = acciones.get(tecla.accion) or (lambda t=tecla: self.campo.insertar(t.texto, t.retroceso))
        return Boton((x, y, w, 40), contenido, accion, fondo, letra, tam=tam, radio=10, relieve=4, sonido="tecla")

    def _ancho_tecla(self, tecla):
        if tecla.icono:
            return max(46, _ICONOS[tecla.icono]((0, 0, 0)).get_width() + 22)
        if tecla.formula:
            return max(46, ui.formula(tecla.etiqueta, 22).sup.get_width() + 22)
        return max(46, ui.texto(tecla.etiqueta, 16, negrita=True).get_width() + 24)

    def _boton_saltear(self, rect):
        """Saltear el ejercicio: una vez por nivel, cuesta monedas (en los jefes no se puede)."""
        if self.jefe:
            txt, ok = "Saltear: no (jefe)", False
        elif self.salteo_usado:
            txt, ok = "Ya salteaste uno", False
        else:
            txt = f"Saltear (−{self.COSTO_SALTEAR})"
            ok = self.app.progreso.monedas >= self.COSTO_SALTEAR
        return Boton(rect, txt, self.saltear, (186, 150, 236), TINTA, tam=18, habilitado=ok, sonido="salto")

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
            txt, ok = ("Pista (−5)" if n == 1 else f"Pista {vistas + 1}/{n} (−5)"), True
        return Boton(rect, txt, self.pista, SOL, TINTA, tam=18, habilitado=ok, sonido="pista")

    # ---------------------------------------------- distribución en la pantalla
    # Abajo de todo está la franja del gato: su globito (error, pista, charla) o, si no habla,
    # los botones de Pista y Saltear. El ejercicio va arriba de esa franja y NUNCA se pisa con ella:
    # si no entra, se va compactando de a poco (menos aire, fórmulas más chicas, pasos en una línea).
    COMPACTOS = (
        # aire, alto fórmula, alto gráfico, tam pregunta, tam pasos, pasos en línea, alto opciones, alto "Leo", tam globo
        dict(aire=1.0, formula=None, grafico=None, pregunta=24, pasos=20, en_linea=False, opcion=84, leo=44, globo=19),
        dict(aire=0.7, formula=96, grafico=300, pregunta=22, pasos=18, en_linea=False, opcion=72, leo=34, globo=19),
        dict(aire=0.5, formula=76, grafico=260, pregunta=21, pasos=17, en_linea=True, opcion=62, leo=30, globo=18),
        dict(aire=0.4, formula=62, grafico=220, pregunta=20, pasos=16, en_linea=True, opcion=54, leo=28, globo=17),
        dict(aire=0.3, formula=50, grafico=180, pregunta=19, pasos=15, en_linea=True, opcion=48, leo=26, globo=16),
    )

    MARGEN = 12          # entre la franja del gato y el borde de abajo

    ALTO_LADO = 46       # alto de los botones Pista / Saltear

    def armar(self):
        """Calcula la ubicación de todo según el estado actual (lo más compacto que haga falta para que entre)."""
        for c in self.COMPACTOS:
            if self._armar(c):
                return

    def _armar(self, c):
        """Arma la pantalla con un nivel de compactación. Devuelve True si todo entra sin pisarse."""
        icono = Lienzo(*((36, 36)))
        flecha_reiniciar(icono, (18, 18), 26, BORDE)
        self.botones = [Boton((14, 10, 108, 44), "Salir", self.atras, DURAZNO, tam=19, relieve=4),
                        self.boton_opciones((130, 10, 48, 44)),
                        Boton((186, 10, 48, 44), icono, self.reiniciar, ARENA, relieve=4)]
        self.capas = []
        respondiendo = self.estado == "pregunta"

        # 1) la franja del gato, de abajo para arriba: así se sabe cuánto lugar le queda al ejercicio
        self.panel = self._globito(c, respondiendo)
        if self.panel:
            limite = self.panel["rect"].top - 10
        elif respondiendo:
            r = self._rect_lado(ALTO - self.MARGEN - self.ALTO_LADO)
            self.botones.append(self._boton_pista(r[0]))
            self.botones.append(self._boton_saltear(r[1]))
            limite = r[0].top - 10
        else:
            limite = ALTO - self.MARGEN
        a = c["aire"]

        # 2) el ejercicio, de arriba para abajo
        if self.ej.grafico:
            self.cx, self.ancho = 480, 860
            g = ui.grafico(self.ej.grafico)
            if c["grafico"]:
                g = ui.escalar_caja(g, c["grafico"] * 1.07, c["grafico"])
            self.capas.append((g, g.get_rect(topright=(ANCHO - 24, 108))))
        else:
            self.cx, self.ancho = ANCHO // 2, 1100
        cx, ancho = self.cx, self.ancho
        y = 108 + (16 if self.tiempo else 0)   # con reloj, la barra de tiempo va arriba
        consigna = self.ej.consigna
        # solo lo que de verdad viene del cuaderno de errores lleva el cartel
        del_cuaderno = self.i in self.repasos or (self.practica and self.app.progreso.en_cuaderno(self.ej.clave))
        if del_cuaderno and not (self.practica and self.mundo is None):   # en el repaso del cuaderno ya lo dice el título
            consigna = "**Repaso del cuaderno** · " + consigna
        s = ui.rico(consigna, 20 if a == 1 else 18, SUAVE, ancho=ancho, color_negrita=ui.CORAL_OSC)
        self.capas.append((s, s.get_rect(midtop=(cx, y))))
        y += s.get_height() + 4 * a
        f = ui.formula(self.ej.formula, 46)
        s = ui.escalar_caja(f.sup, ancho, c["formula"])
        self.capas.append((s, s.get_rect(midtop=(cx, y))))
        y += s.get_height() + 14 * a
        if self.paso_i:
            y = self._pasos_hechos(c, y)
        n_pasos = len(self.ej.pasos)
        pregunta = self.paso.pregunta
        if n_pasos > 1:
            pregunta = f"**Paso {self.paso_i + 1} de {n_pasos}.** " + pregunta
        s = ui.rico(pregunta, c["pregunta"], TINTA, ancho=ancho - 150, color_negrita=LAVANDA_OSC)
        insignia = cartelito_consigna(self.es_logica)
        ancho_ins = insignia.get_width() - 12          # (la insignia trae 6 px de margen para su sombra)
        total = ancho_ins + 12 + s.get_width()
        x_ins = cx - total // 2
        self.capas.append((insignia, insignia.get_rect(topleft=(x_ins - 6, y + 1 - 6))))
        self.capas.append((s, s.get_rect(topleft=(x_ins + ancho_ins + 12, y))))
        y += max(s.get_height(), insignia.get_height() - 5) + 16 * a     # (la insignia arranca 5 px más arriba)

        if self.paso.tipo == "expresion":
            y = self._armar_respuesta(c, y, respondiendo)
        else:
            y = self._armar_opciones(c, y, respondiendo)
        contenido = [r for s, r in self.capas if isinstance(r, pygame.Rect)]
        fondo = max([y] + [r.bottom for r in contenido])
        # ningún botón puede tapar el ejercicio (por ejemplo, el teclado al gráfico de la región) ni al gato
        tapa = any(b.rect.colliderect(r) for b in self.botones[3:] for r in contenido + [ZONA_GATO])
        return fondo <= limite and not tapa

    def _rect_lado(self, y):
        """Lugar de los botones Pista y Saltear cuando el gato no está hablando: abajo, al lado del gato."""
        w = 236
        x = max(X_GLOBO + 10, self.cx - (2 * w + 14) // 2)
        return pygame.Rect(x, y, w, self.ALTO_LADO), pygame.Rect(x + w + 14, y, w, self.ALTO_LADO)

    def _pasos_hechos(self, c, y):
        """Lo que ya resolviste en los pasos anteriores (con tilde o cruz)."""
        cx, ancho = self.cx, self.ancho
        hechos = [(self.ej.pasos[k].resumen, k in self.pasos_revelados) for k in range(self.paso_i)]
        if c["en_linea"]:
            # todos en un renglón (o los que entren, achicados)
            piezas = [ui.rico(r, c["pasos"], ROSA_OSC if mal else MENTA_OSC, ancho=ancho) for r, mal in hechos]
            w = sum(p.get_width() + 30 for p in piezas) + 24 * (len(piezas) - 1)
            k = min(1.0, (ancho - 40) / max(1, w))
            if k < 1:
                piezas = [ui.escalar_a(p, max(1, int(p.get_width() * k))) for p in piezas]
            alto = max(p.get_height() for p in piezas)
            x = cx - int(w * k) // 2
            for p, (_, mal) in zip(piezas, hechos, strict=True):
                x += 24
                self.capas.append(("cruz" if mal else "tilde", (x - 4, y + alto // 2)))
                r = p.get_rect(midleft=(x + 10, y + alto // 2))
                self.capas.append((p, r))
                x = r.right + 24
            return y + alto + 10 * c["aire"]
        for resumen, mal in hechos:
            s = ui.escalar_a(ui.rico(resumen, c["pasos"], ROSA_OSC if mal else MENTA_OSC, ancho=ancho - 100),
                             ancho - 60)
            r = s.get_rect(midtop=(cx + 16, y))
            self.capas.append((s, r))
            self.capas.append(("cruz" if mal else "tilde", (r.left - 20, r.centery)))
            y += s.get_height() + 6 * c["aire"]
        return y + 6 * c["aire"]

    def _armar_respuesta(self, c, y, respondiendo):
        """Cuadro de texto (con Comprobar al lado), la línea "Leo:" y el teclado de fórmulas."""
        cx, ancho = self.cx, self.ancho
        w_comprobar = 196 if respondiendo else 0
        hueco_comp = 12 if respondiendo else 0
        pre = None
        if self.paso.prefijo:
            pre = ui.formula(ui.fracciones_grandes(self.paso.prefijo), 30).sup
            # el cuadro de texto tiene que quedar cómodo para escribir: el prefijo se achica si hace falta
            pre = ui.escalar_caja(pre, max(120, min(380, ancho - 40 - 400 - w_comprobar - hueco_comp - 14)),
                                  70 if c["aire"] == 1 else 56)
        pw = pre.get_width() + 14 if pre else 0
        ancho_campo = min(560, ancho - 40 - pw - w_comprobar - hueco_comp)
        x0 = cx - (pw + ancho_campo + hueco_comp + w_comprobar) // 2
        alto_campo = max(58, pre.get_height() + 6) if pre else 58
        if pre:
            self.capas.append((pre, pre.get_rect(midleft=(x0, y + alto_campo // 2))))
        self.campo.rect = pygame.Rect(x0 + pw, y + (alto_campo - 58) // 2, ancho_campo, 58)
        self.campo.habilitado = respondiendo
        if respondiendo:
            self.botones.append(Boton((self.campo.rect.right + hueco_comp, self.campo.rect.top + 3, w_comprobar, 52),
                                      "Comprobar  ↵", self.comprobar, CORAL, CREMA, tam=20, sonido=None))
        y += alto_campo + 8 * c["aire"]
        self.y_preview = y
        y += c["leo"]
        if not respondiendo:
            return y
        hueco = 16   # espacio entre grupos de teclas (funciones, números, operaciones, edición)
        for fila in self._teclado():
            anchos = [self._ancho_tecla(t) for t in fila]
            grupos = [k > 0 and _otro_grupo(fila[k - 1], fila[k]) for k in range(len(fila))]
            total = sum(anchos) + 6 * (len(fila) - 1) + hueco * sum(grupos)
            x = self._x_fila(total, y)
            for tecla, w, nuevo_grupo in zip(fila, anchos, grupos, strict=True):
                if nuevo_grupo:
                    x += hueco
                self.botones.append(self._boton_tecla(tecla, x, y, w))
                x += w + 6
            y += 48
        return y

    def _x_fila(self, total, y):
        """Dónde empieza una fila del teclado: centrada en el ejercicio, sin salirse de la pantalla y,
        si está tan abajo que llega a la altura del gato, corrida para no taparlo."""
        izquierda = ZONA_GATO.right + 8 if y + 40 > ZONA_GATO.top else 16
        return max(izquierda, min(self.cx - total // 2, ANCHO - 16 - total))

    def _armar_opciones(self, c, y, respondiendo):
        cx, ancho = self.cx, self.ancho
        ops = self.paso.opciones
        con_texto = any(o.texto for o in ops)
        alto = min(62, c["opcion"]) if con_texto else c["opcion"]
        hueco = max(8, round(16 * c["aire"]))
        w = min(540, (ancho - 18) // 2)
        x0 = cx - (2 * w + 18) // 2
        filas = (len(ops) + 1) // 2
        if y + filas * (alto + hueco) > ZONA_GATO.top:      # llegan a la altura del gato: se corren
            x0 = max(x0, ZONA_GATO.right + 8)
        self.rect_opciones = {}
        for k, o in enumerate(ops):
            fila, col = divmod(k, 2)
            rect = pygame.Rect(x0 + col * (w + 18), y + fila * (alto + hueco), w, alto)
            if o.texto:
                contenido = o.texto
            else:   # la fórmula se achica para entrar en el botón
                contenido = ui.escalar_caja(ui.formula(ui.fracciones_grandes(o.tex), 28).sup, w - 70, alto - 12)
            b = Boton(rect, contenido, (lambda k=k: self.elegir(k)), TARJETA, tam=21,
                      tecla=[pygame.K_1 + k, pygame.K_KP1 + k], habilitado=respondiendo and k not in self.marcadas,
                      etiqueta_tecla=str(k + 1), sonido=None, relieve=6)
            b.marcado = self.marcadas.get(k)
            b.t_marcado = self.t_marcas.get(k, 0) if hasattr(self, "t_marcas") else 0
            self.rect_opciones[k] = rect
            self.botones.append(b)
        return y + ((len(ops) + 1) // 2) * (alto + hueco) - hueco

    # ---------------------------------------------- el globito del gato
    def _globito(self, c, respondiendo):
        """Feedback, pista o charla. Mientras respondés, Pista y Saltear van adentro, a la derecha."""
        lado = respondiendo
        if self.feedback:
            fb = self.feedback
            if fb["tipo"] == "bien":
                return self._panel(c, fb["titulo"], fb["cuerpo"], (232, 248, 222), MENTA_OSC,
                                   con_boton=self.auto_t is None, lado=lado)
            if fb["tipo"] == "info":
                return self._panel(c, fb["titulo"], fb["cuerpo"], TARJETA, SUAVE, lado=lado)
            return self._panel(c, fb["titulo"], fb["cuerpo"], (255, 234, 226), ROSA_OSC,
                               con_boton=self.estado in ("revelado", "sin_vidas"), lado=lado)
        if self.pistas_vistas:
            cuerpo = "\n".join(self.paso.pistas[:self.pistas_vistas])
            return self._panel(c, "Pista", cuerpo, (255, 246, 214), SOL_OSC, lado=lado)
        if self.charla and self.t_charla > 0:
            return self._panel(c, self.charla, "", TARJETA, ui.CORAL_OSC, lado=lado)
        return None

    def _panel(self, c, titulo, cuerpo, color, color_titulo, con_boton=False, lado=False):
        """El globito, pegado abajo al lado del gato. `lado`: con Pista y Saltear adentro, a la derecha."""
        ancho = ANCHO - X_GLOBO - 24
        w_lado = 236 if lado else (210 if con_boton else 0)
        ancho_txt = ancho - 50 - w_lado
        t = ui.rico(f"**{titulo}**", c["globo"] + 4, color_titulo, ancho=ancho_txt, color_negrita=color_titulo)
        cu = ui.rico(cuerpo, c["globo"], TINTA, ancho=ancho_txt, color_negrita=color_titulo) if cuerpo else None
        alto = 22 + t.get_height() + (cu.get_height() + 8 if cu else 0) + 14
        if lado:
            alto = max(alto, 2 * self.ALTO_LADO + 10 + 28)
        elif con_boton:
            alto = max(alto, 86)
        rect = pygame.Rect(X_GLOBO, ALTO - self.MARGEN - alto, ancho, alto)
        if lado:
            x = rect.right - 22 - (w_lado - 22)
            y = rect.centery - self.ALTO_LADO - 5
            self.botones.append(self._boton_pista(pygame.Rect(x, y, w_lado - 22, self.ALTO_LADO)))
            self.botones.append(self._boton_saltear(pygame.Rect(x, y + self.ALTO_LADO + 10, w_lado - 22,
                                                                self.ALTO_LADO)))
        elif con_boton:
            b = Boton((rect.right - 206, rect.centery - 28, 184, 54), "Continuar  ↵", self.continuar, LAVANDA,
                      tam=20, tecla=[pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE], sonido="paso")
            self.botones.append(b)
        return dict(rect=rect, color=color, titulo=t, cuerpo=cu, borde=color_titulo)

    def _dibujar_encabezado(self, sup):
        r = pygame.Rect(-10, -10, ANCHO + 20, 74)
        ui.tabla_madera(sup, r, radio=0)
        t = ui.texto_borde(self.titulo, 24, CREMA, MADERA_OSC, 2)
        lugar = self.pos_monedas[0] - (90 if self.racha >= 2 else 20) - 248 - (80 if self.jefe else 0)
        if t.get_width() > lugar:      # título largo: se achica para no chocar con monedas y racha
            t = dibujo.escalar(t, (lugar, t.get_height() * lugar / t.get_width()))
        sup.blit(t, (248, 32 - t.get_height() // 2))
        x = 248 + t.get_width() + 12
        if self.jefe:
            et = ui.texto_borde("JEFE", 16, CREMA, ui.CORAL_OSC, 2)
            rr = pygame.Rect(x, 18, et.get_width() + 18, 28)
            if not (pincel.HAY_SKIA and ui._pegar(sup, pincel.pastilla(rr.width, rr.height, CORAL), rr.x, rr.y)):
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
                if not (pincel.HAY_SKIA and ui._pegar(sup, pincel.esfera(8, color), c[0] - 10, c[1] - 10)):
                    dibujo.circle(sup, BORDE, c, 10)
                    dibujo.circle(sup, color, c, 8)
            elif k == self.i:
                rr = round((10 + 2 * math.sin(self.t * 5)) * 2) / 2
                if not (pincel.HAY_SKIA and ui._pegar(sup, pincel.esfera(rr, SOL), c[0] - rr - 2, c[1] - rr - 2)):
                    dibujo.circle(sup, BORDE, c, rr + 2)
                    dibujo.circle(sup, SOL, c, rr)
            else:
                dibujo.circle(sup, ARENA_OSC, c, 7)
                dibujo.circle(sup, ARENA, c, 5)
        if self.tiempo:
            restante = max(0.0, 1 - min(self.t_paso, self.tiempo) / self.tiempo)
            rr = pygame.Rect(ANCHO // 2 - 220, 100, 440, 10)
            col = ui.PASTO if restante > 0.5 else (SOL if restante > 0.25 else CORAL)
            ui.barra(sup, rr, restante, col, (240, 228, 204))

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
                if p["rect"].contains(b.rect):      # los botones del globito (Pista, Saltear, Continuar)
                    b.dibujar(sup)
        self._dibujar_encabezado(sup)
        for b in self.botones[:3]:
            b.dibujar(sup)
        self.fx.dibujar(sup)
        self._dibujar_cartel(sup)

    # ---------------------------------------------- cartel con el nombre del nivel
    CARTEL = (0.30, 1.75)        # aparece cuando ya pasó la ola y se va solo (o con un clic)

    def _armar_cartel(self):
        if self.desafio:
            arriba, nombre, desc = self.mundo.nombre.upper(), "Desafío del jefe", "Si ganás, te salteás el mundo entero."
        elif self.practica:
            arriba, nombre, desc = "REPASO", self.titulo.replace("Repaso · ", ""), "Sin estrellas, pero con monedas."
        else:
            n = len(self.mundo.niveles)
            num = "JEFE" if self.jefe else f"NIVEL {self.nivel_idx + 1} DE {n - 1}"
            arriba, nombre, desc = f"{self.mundo.nombre.upper()} · {num}", self.nivel.nombre, self.nivel.descripcion
        tit = ui.texto_borde(nombre, 46, CREMA, MADERA_OSC, 3)
        sub = ui.texto_borde(arriba, 20, SOL if not self.jefe else (255, 190, 170), MADERA_OSC, 2)
        des = ui.rico(desc, 21, TINTA, ancho=640, centrado=True, color_negrita=ui.CORAL_OSC) if desc else None
        self.cartel = (tit, sub, des)

    def _dibujar_cartel(self, sup):
        ini, fin = self.CARTEL
        t = self.t_cartel
        if t < ini or t > fin:
            return
        if self.cartel is None:
            self._armar_cartel()
        tit, sub, des = self.cartel
        k_in = min(1.0, (t - ini) / 0.28)
        k_out = max(0.0, 1 - (fin - t) / 0.3)
        alfa = int(255 * min(suave(k_in), 1 - suave(k_out)))
        caida = (1 - rebote(k_in)) * -60 + suave(k_out) * 40
        capa = Lienzo(ANCHO, ALTO)
        capa.fill((40, 26, 20, 90))
        w = max(tit.get_width(), sub.get_width()) + 120
        plancha = pygame.Rect(0, 0, max(520, w), 132)
        plancha.center = (ANCHO // 2, int(ALTO // 2 - 50 + caida))
        ui.tabla_madera(capa, plancha, radio=18)
        capa.blit(sub, sub.get_rect(center=(plancha.centerx, plancha.top + 34)))
        capa.blit(tit, tit.get_rect(center=(plancha.centerx, plancha.top + 82)))
        if des is not None:
            caja = pygame.Rect(0, 0, des.get_width() + 48, des.get_height() + 26)
            caja.midtop = (plancha.centerx, plancha.bottom + 14)
            ui.tarjeta(capa, caja, ui.PERGAMINO, 18, ui.ARENA_OSC, 5)
            capa.blit(des, des.get_rect(center=caja.center))
        capa.set_alpha(alfa)
        sup.blit(capa, (0, 0))
