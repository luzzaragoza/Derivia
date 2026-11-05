"""La pantalla de un nivel: ejercicios, pasos, pistas, vidas y el globito del gato."""

import random

import pygame

from .. import escenas, ui
from ..fx import Efectos, Fueguito
from ..gato import Gato
from ..mate import (
    ERRORES,
    C,
    ErrorEntrada,
    casi_igual,
    diagnosticar,
    diagnosticar_primitiva,
    equivalentes,
    es_primitiva,
    parsear,
    tex,
)
from ..mundos import MUNDOS, VIDAS_DESAFIO, generar, generar_desafio, generar_nivel, monedas_de_regalo, mundo_por_id
from ..sonido import sonidos
from ..ui import (
    ANCHO,
    MADERA_OSC,
    CampoTexto,
)
from .base import CREMA, Escena
from .nivel_pantalla import PantallaNivel

FRASES_BIEN = ["¡Bien!", "¡Excelente!", "¡Eso!", "¡Perfecto!", "¡Muy bien!", "¡Genial!", "¡Impecable!", "¡Miau, sí!"]


FRASES_MAL = ["Uy...", "Casi...", "Mmm, no.", "¡Ups!"]


FRASES_INICIO = ["¡Vamos! Yo te acompaño.", "¡A practicar!", "¡Miau! ¿Arrancamos?", "Tranqui, de a un paso."]


class Juego(PantallaNivel, Escena):
    """Un nivel: qué ejercicio toca, qué respondiste, vidas, pistas, monedas y racha.
    Cómo se ve (dónde va cada cosa y cómo se dibuja) está en PantallaNivel."""

    musica = "estudio"

    def __init__(self, app, mundo_id, nivel_idx, practica=None, titulo_practica=None, desafio=False):
        super().__init__(app)
        self.practica = practica is not None
        self.desafio = desafio and not self.practica
        self.bonus_desafio = 0
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
        elif self.desafio:
            # desafío del jefe: te salteás el mundo entero si le ganás
            self.mundo = mundo_por_id(mundo_id)
            self.nivel_idx = len(self.mundo.niveles) - 1
            self.nivel = self.mundo.niveles[self.nivel_idx]
            self.ejercicios = generar_desafio(mundo_id)
            self.vidas_max = VIDAS_DESAFIO
            self.titulo = f"{self.mundo.nombre} · Desafío del jefe"
            self.color = self.mundo.color
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
        self.charla = ("¡Desafío! Si le ganás al jefe, te salteás todo el mundo." if self.desafio
                       else "¡Es un jefe! Acá no hay pistas, pero vos podés." if self.jefe
                       else random.choice(FRASES_INICIO))
        self.t_charla = 3.5
        self.sacudir = 0
        self.t = 0.0
        self.t_entrada = 0.0
        self.t_cartel = 0.0          # cartel con el nombre del nivel al empezar
        self.cartel = None
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


    # ---------------------------------------------- acciones
    def atras(self):
        if self.practica and not self.mundo:
            self.app.cambiar(escenas.Cuaderno(self.app))
        else:
            self.app.cambiar(escenas.Mapa(self.app, self.mundo.id), "ola")

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
            self.app.cambiar(escenas.FinNivel(self.app, self, gano=False))
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
            if self.desafio:
                # ¡mundo salteado! todos los niveles con 3 estrellas y sus monedas, como si los hubieras jugado
                estrellas = 3
                self.bonus_desafio = monedas_de_regalo(self.mundo, prog)
                prog.monedas += self.bonus_desafio
                for k, n in enumerate(self.mundo.niveles):
                    prog.registrar(self.mundo.id, k, 3, n.cantidad * 14)
            prog.registrar(self.mundo.id, self.nivel_idx, estrellas, self.puntos)
            if era_ultimo and not ya and pos + 1 < len(MUNDOS):
                nuevo_mundo = MUNDOS[pos + 1]
        self.app.cambiar(escenas.FinNivel(self.app, self, gano=True, estrellas=estrellas, nuevo_mundo=nuevo_mundo))

    # ---------------------------------------------- loop
    @property
    def pos_monedas(self):
        """La moneda del contador: siempre a la izquierda de los corazones, según cuántas vidas haya
        y lo ancho que sea el número (así nunca se pisan)."""
        borde_corazones = ANCHO - 34 - (self.vidas_max - 1) * 38 - 18
        ancho_num = ui.texto_borde(str(int(round(getattr(self, "monedas_vistas", 0)))), 24, CREMA, MADERA_OSC, 2).get_width()
        ancho = max(22 + ancho_num, ui.texto(f"+{self.puntos} en este nivel", 12, CREMA, negrita=True).get_width() - 8)
        return (min(ANCHO - 230, borde_corazones - 16 - ancho), 32)

    def evento(self, e):
        ini, fin = self.CARTEL
        if ini <= self.t_cartel < fin - 0.3 and e.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
            self.t_cartel = fin - 0.3          # un clic (o una tecla) lo saca más rápido
            return True
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
        self.t_cartel += dt
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


