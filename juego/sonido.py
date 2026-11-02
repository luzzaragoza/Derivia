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
    s["trueno"] = _mezclar(_ruido(1.4, vol=0.5, caida=0.5, suavizar=90), _nota(55, 1.0, "triangulo", vol=0.25, caida=0.6))
    s["fuegos"] = _mezclar(_nota(1800, 0.25, duty=0.125, vol=0.08, caida=0.3, desliza_a=600),
                           _seq(_silencio(0.22), _ruido(0.35, vol=0.4, caida=1.2, suavizar=8)))
    melodia = [("G4", .09), ("C5", .09), ("E5", .09), ("G5", .18), ("E5", .09), ("G5", .36),
               ("A5", .12), ("B5", .12), ("C6", .12), ("D6", .12), ("E6", .7)]
    voz = _seq(*[_nota(n, d, duty=0.25, vol=0.36, caida=0.45) for n, d in melodia])
    segunda = _seq(_silencio(0.9), *[_nota(n, .12, duty=0.5, vol=0.15, caida=0.4) for n in ("F5", "G5", "A5", "B5")],
                   _nota("C6", 0.7, duty=0.5, vol=0.15, caida=0.6))
    bajo = _seq(*[_nota(n, d, "triangulo", vol=0.5, caida=0.3) for n, d in
                  [("C3", .27), ("G3", .27), ("C4", .54), ("F3", .24), ("G3", .24), ("C4", .8)]])
    tambor = _seq(*[_seq(_ruido(0.06, vol=0.3, caida=2.5), _silencio(0.21)) for _ in range(4)],
                  _seq(*[_seq(_ruido(0.04, vol=0.25, caida=3), _silencio(0.08)) for _ in range(4)]),
                  _ruido(0.5, vol=0.35, caida=0.8, suavizar=3))
    s["jefe"] = _mezclar(voz, segunda, bajo, tambor)
    s["tic"] = _nota(1760, 0.025, duty=0.25, vol=0.15, caida=1.0)
    s["salto"] = _nota(300, 0.14, duty=0.25, vol=0.3, caida=0.5, desliza_a=900)
    return s


# ------------------------------------------------------------ música de fondo

def _colocar(buf, inicio, onda):
    a = int(inicio * FS)
    b = min(len(buf), a + len(onda))
    if a < len(buf):
        buf[a:b] += onda[:b - a]


def _pista(bpm, compases, acordes, melodia=(), arpegio_vol=0.07, bajo_vol=0.32, mel_vol=0.16, shaker=0.025,
           campanitas=()):
    """Arma un loop chiptune. acordes: [(raíz_bajo, [notas del arpegio]), ...] (uno por compás)."""
    pulso = 60 / bpm
    total = compases * 4 * pulso
    buf = np.zeros(int(total * FS) + 1)
    for c in range(compases):
        raiz, notas = acordes[c % len(acordes)]
        t0 = c * 4 * pulso
        quinta = NOTAS[raiz] * 1.5
        _colocar(buf, t0, _nota(raiz, pulso * 1.6, "triangulo", vol=bajo_vol, caida=0.35))
        _colocar(buf, t0 + 2 * pulso, _nota(quinta, pulso * 1.6, "triangulo", vol=bajo_vol * 0.8, caida=0.35))
        if arpegio_vol:
            secuencia = notas + notas[-2:0:-1]
            for k in range(8):
                n = secuencia[k % len(secuencia)]
                _colocar(buf, t0 + k * pulso / 2, _nota(n, pulso * 0.45, duty=0.125, vol=arpegio_vol, caida=0.9))
        if shaker:
            for k in range(4):
                _colocar(buf, t0 + (k + 0.5) * pulso, _ruido(0.05, vol=shaker, caida=3.0))
    t = 0.0
    for nota, beats in melodia:
        if nota:
            onda = _nota(nota, beats * pulso * 0.95, "triangulo", vol=mel_vol, caida=0.25, vibrato=0.004)
            _colocar(buf, t, onda)
        t += beats * pulso
    for compas, nota in campanitas:
        _colocar(buf, compas * 4 * pulso, _nota(nota, pulso * 3, "seno", vol=0.12, caida=0.5))
    # que el final empalme con el principio
    cola = int(FS * 0.02)
    buf[-cola:] *= np.linspace(1, 0, cola)
    pico = np.max(np.abs(buf)) or 1
    return buf / pico * 0.8


def _musica_isla():
    acordes = [("C3", ["C4", "E4", "G4", "C5"]), ("A2", ["A3", "C4", "E4", "A4"]),
               ("F2", ["F3", "A3", "C4", "F4"]), ("G2", ["G3", "B3", "D4", "G4"])]
    mel = [("E5", 1), ("G5", 1), ("A5", 1.5), ("G5", .5), ("E5", 2), ("C5", 1), ("D5", 1),
           ("C5", 1), ("A4", 1), ("C5", 1), ("D5", 1), ("D5", 3), (None, 1),
           ("E5", 1), ("G5", 1), ("C6", 1.5), ("A5", .5), ("G5", 2), ("E5", 1), ("G5", 1),
           ("A5", 1), ("G5", 1), ("E5", 1), ("D5", 1), ("C5", 3), (None, 1)]
    return _pista(100, 8, acordes, mel)


def _musica_estudio():
    acordes = [("F2", ["F3", "A3", "C4", "E4"]), ("E2", ["E3", "G3", "B3", "D4"]),
               ("D2", ["D3", "F3", "A3", "C4"]), ("C2", ["C3", "E3", "G3", "B3"])]
    return _pista(76, 8, acordes, (), arpegio_vol=0.05, bajo_vol=0.28, shaker=0.0,
                  campanitas=[(0, "E6"), (2, "C6"), (4, "A5"), (6, "G5")])


def _musica_pensar():
    """Para las preguntas de lógica: más liviana y 'curiosa' (en menor, con pizzicatos)."""
    acordes = [("A2", ["A4", "C5", "E5", "A5"]), ("F2", ["F4", "A4", "C5", "F5"]),
               ("C3", ["E4", "G4", "C5", "E5"]), ("G2", ["D4", "G4", "B4", "D5"])]
    mel = [(None, 4), ("E6", .5), (None, 1.5), ("C6", .5), (None, 1.5), (None, 4), ("D6", .5), (None, .5), ("B5", .5),
           (None, 2.5), (None, 4), ("A5", .5), (None, 1.5), ("C6", .5), (None, 1.5), (None, 4), ("B5", 1), (None, 3)]
    return _pista(108, 8, acordes, mel, arpegio_vol=0.055, bajo_vol=0.22, mel_vol=0.13, shaker=0.018)


def _jingle_inicio():
    """Fanfarria corta de 'arranca el nivel' (original)."""
    voz = _seq(*[_nota(n, 0.075, duty=0.25, vol=0.4, caida=0.3) for n in ("G4", "C5", "E5", "G5", "E5", "G5")],
               _silencio(0.04), _nota("C6", 0.12, duty=0.25, vol=0.4, caida=0.2),
               _silencio(0.03), _nota("C6", 0.45, duty=0.25, vol=0.4, caida=0.6, vibrato=0.01))
    segunda = _seq(_silencio(0.45 + 0.04), _nota("E5", 0.12, duty=0.5, vol=0.18, caida=0.2),
                   _silencio(0.03), _nota("G5", 0.45, duty=0.5, vol=0.18, caida=0.6))
    bajo = _seq(_nota("C3", 0.22, "triangulo", vol=0.5, caida=0.2), _nota("G3", 0.22, "triangulo", vol=0.5, caida=0.2),
                _silencio(0.05), _nota("C4", 0.6, "triangulo", vol=0.5, caida=0.5))
    return _mezclar(voz, segunda, bajo)


class Sonidos:
    """Efectos y música, cada uno con su interruptor y su volumen."""

    def __init__(self):
        self.ok = False
        self.activo = True            # efectos
        self.volumen = 0.6
        self.musica_activa = True
        self.volumen_musica = 0.5
        self._sonidos = {}
        self._musicas = {}
        self._actual = None
        self._canal_musica = 0
        self._agachar = 0.0

    def _a_sonido(self, w, freq, canales, ganancia=0.8):
        if freq != FS:
            x_viejo = np.linspace(0, 1, len(w))
            w = np.interp(np.linspace(0, 1, int(len(w) * freq / FS)), x_viejo, w)
        datos = np.clip(w * 32767 * ganancia, -32767, 32767).astype(np.int16)
        if canales > 1:
            datos = np.repeat(datos[:, None], canales, axis=1)
        return pygame.sndarray.make_sound(np.ascontiguousarray(datos))

    def iniciar(self):
        """Arma los sonidos y la música. Si no hay placa de audio, el juego sigue mudo."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(FS, -16, 1, 512)
            freq, _, canales = pygame.mixer.get_init()
        except pygame.error:
            return
        pygame.mixer.set_num_channels(18)
        pygame.mixer.set_reserved(2)          # los canales 0 y 1 son de la música
        efectos = _diseñar()
        efectos["inicio"] = _jingle_inicio()
        for nombre, w in efectos.items():
            try:
                self._sonidos[nombre] = self._a_sonido(w, freq, canales)
            except Exception:
                continue
        for nombre, f in (("isla", _musica_isla), ("estudio", _musica_estudio), ("pensar", _musica_pensar)):
            try:
                self._musicas[nombre] = self._a_sonido(f(), freq, canales, 0.55)
            except Exception:
                continue
        self.ok = bool(self._sonidos)
        self._aplicar_volumen()

    def _aplicar_volumen(self):
        for s in self._sonidos.values():
            s.set_volume(self.volumen)
        self._volumen_canal_musica()

    def _volumen_canal_musica(self):
        if not self.ok:
            return
        v = self.volumen_musica * 0.6 * (0.3 if self._agachar > 0 else 1.0)
        for k in (0, 1):
            pygame.mixer.Channel(k).set_volume(v)

    # ------------------------------------------------ efectos
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

    # ------------------------------------------------ música
    def musica(self, nombre):
        """Cambia la música de fondo con un fundido suave (None = silencio)."""
        if nombre == self._actual:
            return
        self._actual = nombre
        if not self.ok:
            return
        viejo = pygame.mixer.Channel(self._canal_musica)
        viejo.fadeout(1200)
        if nombre and self.musica_activa and nombre in self._musicas:
            self._canal_musica = 1 - self._canal_musica
            nuevo = pygame.mixer.Channel(self._canal_musica)
            nuevo.play(self._musicas[nombre], loops=-1, fade_ms=1200)
            self._volumen_canal_musica()

    def agachar(self, segundos=1.5):
        """Baja la música un ratito (para que se escuche una fanfarria)."""
        self._agachar = max(self._agachar, segundos)
        self._volumen_canal_musica()

    def actualizar(self, dt):
        if self._agachar > 0:
            self._agachar -= dt
            if self._agachar <= 0:
                self._volumen_canal_musica()

    # ------------------------------------------------ interruptores
    def poner_musica(self, activa):
        self.musica_activa = activa
        if not self.ok:
            return
        if activa:
            actual, self._actual = self._actual, None
            self.musica(actual)
        else:
            for k in (0, 1):
                pygame.mixer.Channel(k).fadeout(400)

    def poner_efectos(self, activos):
        self.activo = activos

    def poner_volumenes(self, efectos=None, musica=None):
        if efectos is not None:
            self.volumen = efectos
        if musica is not None:
            self.volumen_musica = musica
        self._aplicar_volumen()

    def alternar(self):
        """Tecla M: silencia o vuelve a prender todo."""
        prender = not (self.activo or self.musica_activa)
        self.poner_efectos(prender)
        self.poner_musica(prender)
        if prender:
            self.tocar("click")
        return prender


sonidos = Sonidos()
