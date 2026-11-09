"""Que nada se pise en la pantalla de un nivel.

Arma TODOS los pasos de ejercicios de todos los niveles en las situaciones que agrandan el globito
del gato (te equivocaste, pediste pistas, se reveló la respuesta, acertaste con explicación),
con el teclado numérico abierto y cerrado, y se fija que:

- el globito no tape el ejercicio (consigna, fórmula, pasos, pregunta, campo de texto),
- ningún botón tape el ejercicio (ni el gráfico de la región),
- ningún botón quede encima del globito ni el globito encima de un botón (salvo los suyos, como "Continuar"),
- los botones no se pisen entre ellos ni queden donde está sentado el gato,
- todo entre en la pantalla (1280×720).

Correr con:  python tests/test_superposicion.py        (5 ejercicios por nivel)
              python tests/test_superposicion.py 20     (más ejercicios)"""

import os
import random
import sys
import tempfile

CARPETA = tempfile.mkdtemp(prefix="derivia_sup_")
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["APPDATA"] = CARPETA
os.environ["XDG_DATA_HOME"] = CARPETA
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1280, 720))

from juego import escenas as E  # noqa: E402
from juego.app import App  # noqa: E402
from juego.escenas.nivel_pantalla import ZONA_GATO  # noqa: E402
from juego.lienzo import ALTO, ANCHO  # noqa: E402
from juego.mundos import MUNDOS  # noqa: E402

CUERPO_LARGO = ("Los límites de la integral de **afuera** tienen que ser números fijos. Las curvas van en la "
                "de adentro.  **¡Probá de nuevo!**")


def _situaciones(j):
    """Pone el nivel en cada situación (y lo vuelve a armar). Devuelve el nombre de cada una."""
    yield "sin globito"
    j.charla, j.t_charla = "¡Vamos que se puede!", 3.0
    j.armar()
    yield "charla"
    j.charla = None
    # te equivocaste y podés seguir probando
    j.estado = "pregunta"
    j.feedback = dict(tipo="mal", titulo="Uy, casi. Esa no es la regla.", cuerpo=CUERPO_LARGO)
    j.armar()
    yield "error"
    j.feedback = None
    if j.paso.pistas and not j.jefe:
        j.pistas_vistas = len(j.paso.pistas)
        j.armar()
        yield "todas las pistas"
        j.pistas_vistas = 0
    # se acabaron los intentos: muestra la respuesta
    j.estado = "revelado"
    extra = f"La respuesta era:  {j._respuesta_tex()}"
    if j.paso.explicacion:
        extra += "\n" + j.paso.explicacion
    j.feedback = dict(tipo="mal", titulo="Uy. Esa no era.", cuerpo=CUERPO_LARGO + "\n" + extra)
    j.armar()
    yield "revelado"
    j.estado = "bien"
    cuerpo = j.paso.explicacion
    if j.paso.tipo == "expresion" and j.paso.mostrar:
        cuerpo = f"${j.paso.prefijo} {j.paso.mostrar}$\n{cuerpo}"
    j.feedback = dict(tipo="bien", titulo="¡Bien!   +12", cuerpo=cuerpo)
    j.auto_t = None
    j.armar()
    yield "bien"
    j.estado, j.feedback = "pregunta", None


def _nombre(j, b):
    for accion, nombre in ((j.pista, "Pista"), (j.saltear, "Saltear"), (j.comprobar, "Comprobar"),
                           (j.continuar, "Continuar")):
        if b.accion == accion:
            return nombre
    return "opción" if b.rect.height >= 60 else "tecla"


def _problemas(j):
    """Lista de cosas que se pisan en la pantalla tal como quedó armada."""
    mal = []
    pantalla = pygame.Rect(0, 0, ANCHO, ALTO)
    botones = j.botones[3:]                     # (los 3 primeros son Salir, Opciones y Reiniciar)
    contenido = [r for s, r in j.capas if isinstance(r, pygame.Rect)]
    if j.paso.tipo == "expresion":
        contenido.append(j.campo.rect)
    for b in j.botones:
        if b.rect.colliderect(ZONA_GATO):
            mal.append(f"el botón «{_nombre(j, b)}» tapa (o queda tapado por) el gato {b.rect}")
        if not pantalla.contains(b.rect):
            mal.append(f"el botón «{_nombre(j, b)}» se sale de la pantalla {b.rect}")
    for k, a in enumerate(botones):
        for b in botones[k + 1:]:
            if a.rect.colliderect(b.rect):
                mal.append(f"se pisan «{_nombre(j, a)}» y «{_nombre(j, b)}» {a.rect} {b.rect}")
    for b in botones:
        for r in contenido:
            if b.rect.colliderect(r) and b.rect != j.campo.rect:
                mal.append(f"el botón «{_nombre(j, b)}» tapa el ejercicio {b.rect} {r}")
    if j.panel:
        p = j.panel["rect"]
        if not pantalla.contains(p):
            mal.append(f"el globito se sale de la pantalla {p}")
        for r in contenido:
            if p.colliderect(r):
                mal.append(f"el globito tapa el ejercicio {p} {r}")
        for b in botones:
            if p.colliderect(b.rect) and not p.contains(b.rect):
                mal.append(f"el botón «{_nombre(j, b)}» se pisa con el globito {b.rect} {p}")
    return mal


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    app = App(pygame.display.get_surface())
    rng = random.Random(1)
    fallas = {}
    total = 0
    for m in MUNDOS:
        for idx, nivel in enumerate(m.niveles):
            for _ in range(n):
                random.seed(rng.randrange(10**9))
                j = E.Juego(app, m.id, idx)
                j.charla = None
                for ej_i in range(min(3, len(j.ejercicios))):
                    j.i = ej_i
                    j.empezar_ejercicio()
                    j.charla = None
                    for paso_i in range(len(j.ej.pasos)):
                        j.paso_i = paso_i
                        j.empezar_paso()
                        j.charla = None
                        for teclado in (False, True):
                            app.progreso.teclado_numerico = teclado
                            j.armar()
                            for situacion in _situaciones(j):
                                total += 1
                                for p in _problemas(j):
                                    clave = (m.nombre, nivel.nombre, situacion, p.split(" <")[0])
                                    fallas.setdefault(clave, (p, j.ej.formula, j.paso.pregunta))
    if fallas:
        print(f"{len(fallas)} problemas (en {total} pantallas):")
        for (mundo, nivel, sit, _), (p, formula, pregunta) in sorted(fallas.items()):
            print(f"  [{mundo} · {nivel} · {sit}] {p}\n      {formula}  ·  {pregunta[:70]}")
        sys.exit(1)
    print(f"Todo OK: {total} pantallas sin nada pisado")


if __name__ == "__main__":
    main()
