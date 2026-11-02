"""Pruebas "de punta a punta": arranca el juego de verdad (sin ventana) y lo usa como una persona.

- arranque: primera vez, con nombre, y con pantalla completa guardada,
- tamaños de ventana raros (los que hacían cerrar el juego) cambiando de pantalla con transiciones,
- aprieta TODOS los botones de TODAS las pantallas y se fija que nada se rompa,
- juega los 49 niveles (equivocándose a veces, pidiendo pistas y salteando),
- borrar el progreso (con su copia de respaldo).

Correr con:  python tests/test_e2e.py            (completo, tarda unos minutos)
              python tests/test_e2e.py --rapido   (solo algunos mundos)"""

import math
import os
import random
import shutil
import sys
import tempfile
import time
import traceback
import warnings

CARPETA = tempfile.mkdtemp(prefix="derivia_e2e_")
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["XDG_DATA_HOME"] = CARPETA
os.environ["APPDATA"] = CARPETA
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1280, 720), pygame.RESIZABLE)

from sympy import sstr  # noqa: E402
from sympy.utilities.exceptions import SymPyDeprecationWarning  # noqa: E402

warnings.filterwarnings("ignore", category=SymPyDeprecationWarning)   # entradas raras al apretar todo

from juego import escenas as E  # noqa: E402
from juego import ropa  # noqa: E402
from juego.app import App  # noqa: E402
from juego.mundos import MUNDOS  # noqa: E402
from juego.progreso import Progreso  # noqa: E402

RAPIDO = "--rapido" in sys.argv


# ------------------------------------------------------------------ ayudas
def borrar_datos():
    shutil.rmtree(os.path.join(CARPETA, "Derivia"), ignore_errors=True)


def nueva_app(tam=(1280, 720), **progreso):
    """Arranca el juego como si lo abrieras, con el progreso guardado que se pida."""
    borrar_datos()
    if progreso:
        p = Progreso()
        for k, v in progreso.items():
            setattr(p, k, v)
        p.guardar()
    pantalla = pygame.display.set_mode(tam, pygame.RESIZABLE)
    return App(pantalla)


def cuadros(app, n=3, dt=0.016):
    for _ in range(n):
        app.escena.actualizar(dt)
        app.escena.dibujar(app.lienzo)
        app._componer(dt)


def clic(app, boton):
    """Un clic de verdad, en el centro del botón (como lo haría el mouse)."""
    app.escena.evento(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=boton.rect.center))


def escribir(app, texto):
    for ch in texto:
        app.escena.evento(pygame.event.Event(pygame.TEXTINPUT, text=ch))


# ------------------------------------------------------------------ pruebas
def prueba_arranque():
    app = nueva_app()
    cuadros(app, 10)
    assert isinstance(app.escena, E.NombreGato), "la primera vez tiene que pedir el nombre del michi"
    escribir(app, "Mandarina")
    app.escena.evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode="\r"))
    cuadros(app, 40)
    assert app.progreso.nombre_gato == "Mandarina"

    app = nueva_app(nombre_gato="Mandarina")
    cuadros(app, 10)
    assert isinstance(app.escena, E.Menu)

    # se cerraba al arrancar con la pantalla completa guardada
    app = nueva_app(nombre_gato="Mandarina", pantalla_completa=True)
    cuadros(app, 10)
    app.poner_pantalla_completa(False)
    cuadros(app, 5)
    app.poner_pantalla_completa(True)
    cuadros(app, 5)


def _tamaños_malos(n):
    """Tamaños de ventana donde la cuenta de la escala se pasa por un píxel."""
    malos = []
    for w in range(1100, 2600, 7):
        for h in range(600, 1500, 5):
            e = min(w / 1280, h / 720)
            if math.ceil(1280 * e) > w or math.ceil(720 * e) > h:
                malos.append((w, h))
    random.Random(1).shuffle(malos)
    return malos[:n]


def prueba_tamaños():
    tamaños = [(1280, 720), (1366, 768), (1536, 864), (1920, 1080), (1280, 800), (1000, 700), (800, 600),
               (2560, 1440)] + _tamaños_malos(4 if RAPIDO else 12)
    if not RAPIDO:
        tamaños.append((3840, 2160))
    app = nueva_app(nombre_gato="Mandarina", todo_desbloqueado=True)
    for w, h in tamaños:
        app.ventana = pygame.display.set_mode((w, h), pygame.RESIZABLE)
        app._ajustar()
        app._rearmar()
        for escena, transicion in [(lambda: E.Menu(app), "fundido"), (lambda: E.Mapa(app, "1"), "ola"),
                                   (lambda: E.Juego(app, "1", 0), "fundido"), (lambda: E.Tienda(app), "ola")]:
            app.cambiar(escena(), transicion)
            cuadros(app, 25)


def _pantallas(app):
    """Todas las pantallas del juego (cada una se arma de nuevo para cada botón)."""
    p = app.progreso
    pantallas = [("Menú", lambda: E.Menu(app)), ("Ayuda", lambda: E.Ayuda(app)),
                 ("Opciones", lambda: E.Opciones(app, E.Menu(app))), ("Nombre", lambda: E.NombreGato(app)),
                 ("Cuaderno", lambda: E.Cuaderno(app))]
    for m in MUNDOS:
        pantallas.append((f"Mapa {m.id}", lambda m=m: E.Mapa(app, m.id)))
    for lugar in ["conjuntos"] + [c for c, _ in ropa.LUGARES]:
        def tienda(lugar=lugar):
            t = E.Tienda(app)
            t.elegir_lugar(lugar)
            return t
        pantallas.append((f"Tienda {lugar}", tienda))
    for mid, idx in [("1", 2), ("2", 0), ("3b", 0), ("5", 4), ("8", 2), ("9", 4)]:
        pantallas.append((f"Nivel {mid}-{idx}", lambda mid=mid, idx=idx: E.Juego(app, mid, idx)))

    def fin(gano, jefe):
        j = E.Juego(app, "1", 4 if jefe else 0)
        j.errores_log = []
        return E.FinNivel(app, j, gano, 3 if gano else 0)
    pantallas.append(("Desafío", lambda: E.DesafioIntro(app, E.Mapa(app, "2"), MUNDOS[1])))
    pantallas += [("Fin ganado", lambda: fin(True, False)), ("Fin perdido", lambda: fin(False, False)),
                  ("Fin jefe", lambda: fin(True, True))]
    p.monedas = 5000
    return pantallas


def prueba_botones():
    app = nueva_app(nombre_gato="Mandarina", todo_desbloqueado=True, monedas=5000)
    # algo en el cuaderno para que tenga botones
    j = E.Juego(app, "1", 2)
    app.progreso.anotar_error(j.ej.clave, j.ej.formula)
    total = 0
    for nombre, hacer in _pantallas(app):
        app.cambiar(hacer(), None)
        cuadros(app, 3)
        n = len(app.escena.botones)
        for k in range(n):
            app.corriendo = True
            escena = hacer()
            app.cambiar(escena, None)
            cuadros(app, 2)
            if k >= len(escena.botones):
                continue
            try:
                clic(app, escena.botones[k])
                cuadros(app, 6)
            except Exception as e:
                raise AssertionError(f"pantalla '{nombre}', botón {k}: {e!r}") from e
            total += 1
    print(f"   {total} botones apretados")


def _resolver(app, j, equivocarse):
    p = j.paso
    if p.tipo == "opcion":
        malas = [k for k, o in enumerate(p.opciones) if not o.correcta]
        if equivocarse and malas:
            j.elegir(malas[0])
        if j.estado == "pregunta":
            j.elegir([k for k, o in enumerate(p.opciones) if o.correcta][0])
    else:
        j.campo.poner("")
        if equivocarse:
            escribir(app, "7" if p.chequeo == "numero" else "x+1")
            j.comprobar()
            j.campo.poner("")
        if j.estado == "pregunta":
            escribir(app, sstr(p.esperado).replace("**", "^"))
            j.comprobar()
    if j.estado == "pregunta":
        raise AssertionError(f"no aceptó la respuesta correcta {sstr(p.esperado)} ({j.feedback})")


def _jugar_hasta_el_final(app, j, equivocarse_siempre=False):
    pasos = 0
    while app.escena is j:
        pasos += 1
        assert pasos < 400, "no termina nunca"
        if equivocarse_siempre and j.estado == "pregunta":
            p = j.paso
            if p.tipo == "opcion":
                j.elegir([k for k, o in enumerate(p.opciones) if not o.correcta][0])
            else:
                j.campo.poner("")
                escribir(app, "7" if p.chequeo == "numero" else "x+1")
                j.comprobar()
        else:
            _resolver(app, j, False)
        cuadros(app, 2)
        if j.estado in ("bien", "revelado"):
            j.continuar()
        cuadros(app, 1)
        if app.escena is j and j.estado == "sin_vidas":
            j.continuar()


def prueba_desafio_jefe():
    app = nueva_app(nombre_gato="Mandarina", monedas=100,
                    niveles={f"1-{i}": {"estrellas": 3, "puntos": 10} for i in range(5)} | {"2-0": {"estrellas": 1, "puntos": 5}})
    p = app.progreso
    m = MUNDOS[1]
    assert not p.mundo_desbloqueado("3")
    mapa = E.Mapa(app, "2")
    app.cambiar(mapa, None)
    cuadros(app, 3)
    mapa.desafio()
    cuadros(app, 5)
    assert isinstance(app.escena, E.DesafioIntro)
    regalo = sum(n.cantidad * 14 for i, n in enumerate(m.niveles) if i > 0)   # el 2-0 ya estaba hecho
    app.escena.empezar()
    cuadros(app, 5)
    j = app.escena
    assert j.desafio and j.jefe and j.vidas_max == 2
    assert len(j.ejercicios) == sum(1 for n in m.niveles if not n.jefe) + 3
    assert all(len(e.pasos) == 1 for e in j.ejercicios), "el desafío no tiene pasos guiados"
    antes = p.monedas
    _jugar_hasta_el_final(app, j)
    assert isinstance(app.escena, E.FinNivel) and app.escena.gano
    assert all(p.estrellas("2", i) == 3 for i in range(len(m.niveles))), "no quedaron todas con 3 estrellas"
    assert p.monedas - antes >= regalo, f"no dio las monedas de regalo ({p.monedas - antes} < {regalo})"
    assert j.bonus_desafio == regalo
    assert p.mundo_desbloqueado("3"), "no abrió el mundo siguiente"
    cuadros(app, 30)
    # perdiendo: no se gana nada, y "Reintentar" vuelve a ser un desafío
    app.cambiar(E.Juego(app, "3", None, desafio=True), None)
    j = app.escena
    _jugar_hasta_el_final(app, j, equivocarse_siempre=True)
    assert isinstance(app.escena, E.FinNivel) and not app.escena.gano
    assert not p.aprobado("3", 0), "perdiendo el desafío no se tiene que aprobar nada"
    fin = app.escena
    fin.botones[-1].accion()     # Reintentar
    cuadros(app, 3)
    assert isinstance(app.escena, E.Juego) and app.escena.desafio, "Reintentar tiene que volver al desafío"


def prueba_jugar_todo():
    app = nueva_app(nombre_gato="Mandarina")
    rng = random.Random(11)
    mundos = [m for m in MUNDOS if not RAPIDO or m.id in ("1", "2", "9")]
    if RAPIDO:
        app.progreso.todo_desbloqueado = True
    jugados = 0
    for m in mundos:
        for i, n in enumerate(m.niveles):
            assert app.progreso.desbloqueado(m.id, i), f"no se abrió el nivel {m.id}-{i}"
            app.cambiar(E.Juego(app, m.id, i))
            j = app.escena
            usar_ayudas = i == 1          # en el segundo nivel de cada mundo: pista y saltear
            salteado = False
            pasos = 0
            while app.escena is j:
                pasos += 1
                assert pasos < 400, "el nivel no termina nunca"
                if usar_ayudas and j.estado == "pregunta" and not j.jefe:
                    j.pista()
                    if not salteado and app.progreso.monedas >= E.Juego.COSTO_SALTEAR and j.i > 0:
                        j.saltear()
                        salteado = True
                        cuadros(app, 2)
                        continue
                _resolver(app, j, rng.random() < 0.08 and j.vidas > 2)
                cuadros(app, 2)
                if j.estado in ("bien", "revelado"):
                    j.continuar()
                cuadros(app, 1)
                if app.escena is j and j.estado == "sin_vidas":
                    j.continuar()
            assert isinstance(app.escena, E.FinNivel)
            assert app.escena.gano, f"perdió el nivel {m.id}-{i} ({n.nombre})"
            cuadros(app, 20)
            jugados += 1
    print(f"   {jugados} niveles ganados")


def prueba_borrar_progreso():
    app = nueva_app(nombre_gato="Mandarina", monedas=900, niveles={"1-0": {"estrellas": 3, "puntos": 10}},
                    ropa_comprada=["corona"], ropa_puesta={"cabeza": "corona"}, sonido=False)
    op = E.Opciones(app, E.Menu(app))
    app.cambiar(op, None)
    cuadros(app, 3)
    op.preguntar_borrar()
    cuadros(app, 3)
    op._botones_normales()                      # "No, dejalo"
    assert app.progreso.monedas == 900
    op.preguntar_borrar()
    op.borrar()
    cuadros(app, 30)
    p = Progreso()
    assert (p.monedas, p.nombre_gato, p.niveles, p.ropa_comprada) == (0, "", {}, []), "no se borró todo"
    assert p.sonido is False, "los ajustes de sonido no se tienen que borrar"
    carpeta = os.path.join(CARPETA, "Derivia")
    assert any(f.startswith("progreso_respaldo_") for f in os.listdir(carpeta)), "no dejó copia de respaldo"
    assert isinstance(app.escena, E.NombreGato)


PRUEBAS = [prueba_arranque, prueba_tamaños, prueba_botones, prueba_borrar_progreso, prueba_desafio_jefe,
           prueba_jugar_todo]


def main():
    fallas = 0
    for prueba in PRUEBAS:
        t0 = time.time()
        print(f"· {prueba.__name__} ...", flush=True)
        try:
            prueba()
            print(f"   ok ({time.time() - t0:.0f} s)")
        except Exception:
            fallas += 1
            print("   FALLA")
            traceback.print_exc()
    shutil.rmtree(CARPETA, ignore_errors=True)
    print("Todo OK" if not fallas else f"{fallas} prueba(s) fallaron")
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
