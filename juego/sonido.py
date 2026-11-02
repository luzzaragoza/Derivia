"""Efectos de sonido 8-bit, sintetizados al arrancar (no hay archivos de audio).

Uso:  from .sonido import sonidos;  sonidos.tocar("bien")"""

import random

import numpy as np
import pygame

FS = 22050

# frecuencias de notas (Hz)
NOTAS = {}
for _i, _n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]):
    for _oct in range(2, 8):
        NOTAS[f"{_n}{_oct}"] = 440.0 * 2 ** ((_i - 9) / 12 + (_oct - 4))


def _t(dur):
    return np.arange(int(FS * dur)) / FS


def _envolvente(n, ataque=0.004, caida=0.6):
    """Ataque corto y caída exponencial (suena a 'pling')."""
    env = np.ones(n)
    a = max(1, int(FS * ataque))
    env[:a] = np.linspace(0, 1, a)
    env *= np.exp(-np.linspace(0, 1, n) * caida * 6)
    fin = min(n, int(FS * 0.006))
    env[-fin:] *= np.linspace(1, 0, fin)
    return env


def _onda(frec, dur, forma="cuadrada", duty=0.5, vibrato=0.0, desliza_a=None):
    t = _t(dur)
    if desliza_a is not None:
        f = np.linspace(frec, desliza_a, len(t))
    else:
        f = np.full(len(t), float(frec))
    if vibrato:
        f = f * (1 + vibrato * np.sin(2 * np.pi * 7 * t))
    fase = np.cumsum(f) / FS
    frac = fase % 1.0
    if forma == "cuadrada":
        return np.where(frac < duty, 1.0, -1.0)
    if forma == "triangulo":
        return 4 * np.abs(frac - 0.5) - 1
    if forma == "sierra":
        return 2 * frac - 1
    return np.sin(2 * np.pi * fase)


def _nota(nombre_o_frec, dur, forma="cuadrada", duty=0.5, vol=0.5, caida=0.6, **kw):
    f = NOTAS[nombre_o_frec] if isinstance(nombre_o_frec, str) else nombre_o_frec
    w = _onda(f, dur, forma, duty, **kw)
    return w * _envolvente(len(w), caida=caida) * vol


def _silencio(dur):
    return np.zeros(int(FS * dur))


def _ruido(dur, vol=0.3, caida=1.5, suavizar=1):
    w = np.random.default_rng(7).uniform(-1, 1, int(FS * dur))
    if suavizar > 1:
        w = np.convolve(w, np.ones(suavizar) / suavizar, mode="same")
    return w * _envolvente(len(w), caida=caida) * vol


def _seq(*partes):
    return np.concatenate(partes)


def _mezclar(*partes):
    n = max(len(p) for p in partes)
    out = np.zeros(n)
    for p in partes:
        out[:len(p)] += p
    return out


def _diseñar():
    """Cada sonido es un array de -1 a 1."""
    s = {}
    s["click"] = _nota(1046, 0.045, duty=0.25, vol=0.35, caida=1.2)
    s["tecla"] = _nota(1568, 0.018, duty=0.125, vol=0.12, caida=2.0)
    s["hover"] = _nota(2093, 0.02, duty=0.125, vol=0.06, caida=2.0)
    s["bien"] = _seq(*[_nota(n, 0.06, duty=0.25, vol=0.4, caida=0.4) for n in ("C5", "E5", "G5")],
                     _nota("C6", 0.22, duty=0.25, vol=0.4, caida=0.7))
    s["bien_racha"] = _seq(*[_nota(n, 0.05, duty=0.25, vol=0.4, caida=0.4) for n in ("E5", "G5", "B5", "D6")],
                           _nota("E6", 0.25, duty=0.25, vol=0.4, caida=0.7))
    s["mal"] = _seq(_nota("D#4", 0.11, duty=0.5, vol=0.35, caida=0.5),
                    _nota("A3", 0.26, duty=0.5, vol=0.35, caida=0.8, desliza_a=NOTAS["A3"] * 0.92))
    s["pista"] = _seq(*[_nota(n, 0.05, "triangulo", vol=0.5, caida=0.5) for n in ("G6", "B6", "D7", "G7")])
    s["moneda"] = _seq(_nota("B5", 0.05, duty=0.5, vol=0.3, caida=0.2), _nota("E6", 0.2, duty=0.5, vol=0.3, caida=0.8))
    s["estrella"] = _seq(_nota("G5", 0.05, duty=0.25, vol=0.4, caida=0.2), _nota("D6", 0.05, duty=0.25, vol=0.4, caida=0.2),
                         _nota("G6", 0.28, duty=0.25, vol=0.4, caida=0.9))
    melodia = [("C5", .1), ("E5", .1), ("G5", .1), ("C6", .2), ("G5", .1), ("C6", .45)]
    voz = _seq(*[_nota(n, d, duty=0.25, vol=0.35, caida=0.5) for n, d in melodia])
    bajo = _seq(*[_nota(n, d, "triangulo", vol=0.5, caida=0.3) for n, d in
                  [("C3", .3), ("G3", .2), ("C4", .65)]])
    s["nivel"] = _mezclar(voz, bajo)
    s["perder"] = _seq(*[_nota(n, 0.16, duty=0.5, vol=0.3, caida=0.4) for n in ("G4", "F#4", "F4")],
                       _nota("E4", 0.5, duty=0.5, vol=0.3, caida=0.6, vibrato=0.02))
    s["miau"] = _mezclar(_seq(_nota(620, 0.12, "triangulo", vol=0.55, caida=0.05, desliza_a=900),
                              _nota(900, 0.26, "triangulo", vol=0.55, caida=0.9, desliza_a=520, vibrato=0.03)),
                         _seq(_nota(1240, 0.12, duty=0.125, vol=0.08, caida=0.05, desliza_a=1800),
                              _nota(1800, 0.26, duty=0.125, vol=0.08, caida=0.9, desliza_a=1040)))
    s["fuego"] = _seq(*[_nota(f, 0.035, duty=0.25, vol=0.3, caida=0.3) for f in (523, 659, 784, 1047, 1319, 1568)])
    s["ola"] = _ruido(0.45, vol=0.25, caida=0.9, suavizar=24)
    s["desbloqueo"] = _seq(*[_nota(n, 0.07, duty=0.25, vol=0.35, caida=0.3) for n in ("C5", "G5", "C6", "E6")],
                           _nota("G6", 0.4, "triangulo", vol=0.5, caida=0.8))
    s["paso"] = _nota("A5", 0.06, duty=0.25, vol=0.25, caida=0.6)
    s["tic"] = _nota(1760, 0.025, duty=0.25, vol=0.15, caida=1.0)
    s["salto"] = _nota(300, 0.14, duty=0.25, vol=0.3, caida=0.5, desliza_a=900)
    return s


class Sonidos:
    def __init__(self):
        self.ok = False
        self.activo = True
        self.volumen = 0.6
        self._sonidos = {}

    def iniciar(self):
        """Arma los sonidos. Si no hay placa de audio, el juego sigue mudo."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(FS, -16, 1, 512)
            freq, _, canales = pygame.mixer.get_init()
        except pygame.error:
            return
        pygame.mixer.set_num_channels(16)
        for nombre, w in _diseñar().items():
            if freq != FS:
                x_viejo = np.linspace(0, 1, len(w))
                w = np.interp(np.linspace(0, 1, int(len(w) * freq / FS)), x_viejo, w)
            datos = np.clip(w * 32767 * 0.8, -32767, 32767).astype(np.int16)
            if canales > 1:
                datos = np.repeat(datos[:, None], canales, axis=1)
            try:
                self._sonidos[nombre] = pygame.sndarray.make_sound(np.ascontiguousarray(datos))
            except Exception:
                continue
        self.ok = bool(self._sonidos)
        self._aplicar_volumen()

    def _aplicar_volumen(self):
        for s in self._sonidos.values():
            s.set_volume(self.volumen)

    def tocar(self, nombre, volumen=1.0, variar=False):
        if not (self.ok and self.activo):
            return
        s = self._sonidos.get(nombre)
        if s is None:
            return
        canal = s.play()
        if canal is not None:
            v = self.volumen * volumen * (random.uniform(0.85, 1.0) if variar else 1.0)
            canal.set_volume(v)

    def alternar(self):
        self.activo = not self.activo
        if self.activo:
            self.tocar("click")
        return self.activo


sonidos = Sonidos()
