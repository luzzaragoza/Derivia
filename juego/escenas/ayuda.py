"""Cómo escribir las fórmulas."""


import pygame

from .. import escenas, paisaje, ui
from .. import lienzo as dibujo
from ..gato import Gato
from ..mate import parsear, tex
from ..mate import x as VAR_X
from ..mate import y as VAR_Y
from ..mate import z as VAR_Z
from ..ui import ALTO, ANCHO, DURAZNO, LAVANDA_OSC, SUAVE, TARJETA, TINTA, Boton
from .base import Escena, letrero


class Ayuda(Escena):
    FILAS = [
        ("Potencia", "x^3", ["x^3"]),
        ("Multiplicar", "3x   o   3*x", ["3x"]),
        ("Seno y coseno", "sen(x)   cos(x)", ["sen(x)", "cos(x)"]),
        ("Tangente", "tg(x)", ["tg(x)"]),
        ("e a la algo", "e^(2x)", ["e^(2x)"]),
        ("Logaritmo natural", "ln(x)", ["ln(x)"]),
        ("Raíz cuadrada", "raiz(x)", ["raiz(x)"]),
        ("Raíz cúbica, cuarta…", "raiz[3](x)", ["raiz[3](x)", "raiz3(x)"]),
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
        self.app.cambiar(escenas.Menu(self.app))

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
                    "• En una fracción del teclado, con **▶** pasás del numerador al denominador.\n"
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
