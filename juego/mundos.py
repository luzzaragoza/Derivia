"""Los mundos y sus niveles, y cómo se arma cada ejercicio a partir de su clave."""

import random
from dataclasses import dataclass

from .ejercicios import (Ctx, g_cadena, g_cadena_doble, g_cadena_producto, g_cadena_trasc, g_cociente, g_jefe1,
                         g_jefe2, g_jefe3, g_potencia, g_producto, g_raices, g_regla, g_sumas, g_tabla)
from .gen_integrales import (GENERADORES_V2, g_barrow, g_int_potencia, g_int_raices, g_int_sumas, g_int_tabla,
                             g_jefe4, g_jefe5, g_jefe6, g_jefe7, g_lineal, g_parcial_x, g_parcial_y, g_parciales,
                             g_parciales_cadena, g_partes, g_partes_eleccion, g_partes_log, g_sust, g_sust_acomodar)
from .detective import (GENERADORES_DETECTIVE, g_detective_basicas, g_detective_cadena, g_detective_integrales,
                        g_detective_parciales, g_detective_producto, g_detective_sust_partes)
from .gen_multiples import (GENERADORES_V3, g_cambio_orden, g_cilindricas, g_doble_rect, g_doble_tipo1, g_esfericas,
                            g_jefe8, g_jefe9, g_polares, g_triple_caja, g_triple_region)


@dataclass
class Nivel:
    nombre: str
    descripcion: str
    generadores: list
    modo: str = "tipeo"
    cantidad: int = 5
    jefe: bool = False
    tiempo: float | None = None
    dificultad: int = 1
    vidas: int = 3
    # cuántos ejercicios del nivel vienen guiados paso a paso (u', v', armar...). Los demás piden
    # solo la respuesta final, cortitos como en los jefes. None: todos guiados (solo se saca el
    # "¿cuál es u?" repetido a partir del segundo).
    guiados: int | None = None


@dataclass
class Mundo:
    id: str
    nombre: str
    tema: str
    color: tuple
    niveles: list


GENERADORES = {f.__name__: f for f in [
    g_potencia, g_tabla, g_sumas, g_raices, g_jefe1,
    g_producto, g_cociente, g_jefe2,
    g_cadena, g_cadena_trasc, g_cadena_producto, g_cadena_doble, g_jefe3,
    g_regla,
] + GENERADORES_V2 + GENERADORES_V3 + GENERADORES_DETECTIVE}

MUNDOS = [
    Mundo("1", "Mundo 1", "Derivadas básicas", (170, 205, 240), [
        Nivel("Potencias", "La regla de la potencia: $(x^n)' = n\\,x^{n-1}$.", [g_potencia], "opciones", 4),
        Nivel("Seno, coseno, e y ln", "Las derivadas de la tabla.", [g_tabla], "opciones", 4),
        Nivel("Sumas de términos", "Ahora tipeás vos: derivar término a término.", [g_sumas, g_sumas, g_detective_basicas], "tipeo", 4),
        Nivel("Raíces y fracciones", "Reescribir como potencia y derivar.", [g_raices], "tipeo", 4),
        Nivel("Jefe: todo junto", "Sumas con de todo. Sin pistas.", [g_jefe1], "tipeo", 3, jefe=True),
    ]),
    Mundo("2", "Mundo 2", "Producto y cociente", (168, 222, 196), [
        Nivel("Producto paso a paso", "$(u\\cdot v)' = u'\\,v + u\\,v'$: derivás $u$, derivás $v$ y armás.", [g_producto],
              "tipeo", 3, guiados=2),
        Nivel("Producto de una", "Ya sabés la fórmula: directo a la derivada.", [g_producto, g_producto, g_detective_producto],
              "tipeo", 3, guiados=0),
        Nivel("Cociente paso a paso", "$(u/v)' = (u'v - uv')\\,/\\,v^2$: derivás $u$, derivás $v$ y armás.", [g_cociente],
              "tipeo", 3, guiados=2),
        Nivel("Cociente de una", "Directo a la derivada.", [g_cociente, g_cociente, g_detective_producto],
              "tipeo", 3, guiados=0),
        Nivel("Jefe: producto o cociente", "De una, sin pasos intermedios ni pistas.", [g_jefe2], "tipeo", 3, jefe=True),
    ]),
    Mundo("3", "Mundo 3", "Regla de la cadena", (200, 186, 240), [
        Nivel("Cadena paso a paso", "Una función adentro de otra: $f'(u)\\cdot u'$. Encontrás $u$, la derivás y armás.",
              [g_cadena], "tipeo", 3, guiados=2),
        Nivel("Cadena de una", "Directo a la derivada.", [g_cadena, g_cadena, g_detective_cadena], "tipeo", 3, guiados=0),
        Nivel("ln, raíz y trigonométricas", "Cadenas con ln, raíces y funciones adentro.", [g_cadena_trasc, g_cadena_trasc, g_detective_cadena], "tipeo", 3, guiados=1),
        Nivel("Cadena + producto", "Un producto donde un factor lleva cadena.", [g_cadena_producto, g_cadena_producto, g_detective_cadena], "tipeo", 3, guiados=1),
        Nivel("Jefe: cadena doble", "Capas dentro de capas. Sin pistas.", [g_jefe3], "tipeo", 3, jefe=True),
    ]),
    Mundo("3b", "Mundo 3½", "¿Qué regla va?", (252, 206, 160), [
        Nivel("Calentamiento", "Elegí la regla. 15 segundos por función.", [g_regla], "opciones", 6, tiempo=15, dificultad=1),
        Nivel("Trampas", "Constantes, $\\mathrm{sen}^2$ y otras trampitas. 10 segundos.", [g_regla], "opciones", 6, tiempo=10, dificultad=2),
        Nivel("Reglas anidadas", "¿Qué va primero? 8 segundos.", [g_regla], "opciones", 6, tiempo=8, dificultad=3),
        Nivel("Jefe: contrarreloj", "6 segundos por función.", [g_regla], "opciones", 8, jefe=True, tiempo=6, dificultad=3),
    ]),
    Mundo("4", "Mundo 4", "Derivadas parciales", (246, 190, 206), [
        Nivel("Respecto de x", "La $y$ es una constante, como un número.", [g_parcial_x], "opciones", 4),
        Nivel("Respecto de y", "Ahora la constante es la $x$.", [g_parcial_y], "opciones", 4),
        Nivel("Las dos parciales", "Tipeás $f'_x$ y $f'_y$.", [g_parciales], "tipeo", 3),
        Nivel("Parciales con cadena", "$e^{xy}$, $\\mathrm{sen}(x^2y)$, $\\ln(x^2+y^2)$...", [g_parciales_cadena, g_parciales_cadena, g_detective_parciales], "tipeo", 3),
        Nivel("Jefe: derivada segunda", "$f'_x$ y después $f''_{xy}$. Sin pistas.", [g_jefe4], "tipeo", 3, jefe=True),
    ]),
    Mundo("5", "Mundo 5", "Integrales inmediatas", (176, 220, 232), [
        Nivel("Potencias", "$\\int x^n\\,dx = \\frac{x^{n+1}}{n+1} + C$", [g_int_potencia], "opciones", 4),
        Nivel("Seno, coseno, e y 1/x", "Las integrales de la tabla.", [g_int_tabla], "opciones", 4),
        Nivel("Sumas de términos", "Ahora tipeás vos: término a término.", [g_int_sumas, g_int_sumas, g_detective_integrales], "tipeo", 4),
        Nivel("Raíces y fracciones", "Reescribir como potencia (¡ojo con $x^{-1}$!).", [g_int_raices], "tipeo", 4),
        Nivel("Integral definida", "Primitiva y regla de Barrow: $F(b) - F(a)$.", [g_barrow], "tipeo", 3),
        Nivel("Jefe: integrales", "De todo un poco. Sin pistas.", [g_jefe5], "tipeo", 3, jefe=True),
    ]),
    Mundo("6", "Mundo 6", "Sustitución", (222, 206, 246), [
        Nivel("Adentro lineal", "$\\int e^{3x}\\,dx$, $\\int \\mathrm{sen}(5x)\\,dx$: se divide por la constante.", [g_lineal], "opciones", 4),
        Nivel("Elegir la u", "¿Qué conviene sustituir?", [g_sust], "opciones", 4),
        Nivel("Sustitución paso a paso", "Elegís $u$, calculás $du$ y resolvés.", [g_sust], "tipeo", 3, guiados=2),
        Nivel("Acomodar constantes", "Cuando a $du$ le sobra un número.", [g_sust_acomodar, g_sust_acomodar, g_detective_sust_partes], "tipeo", 3),
        Nivel("Jefe: sustitución", "De una, sin pistas.", [g_jefe6], "tipeo", 3, jefe=True),
    ]),
    Mundo("7", "Mundo 7", "Integración por partes", (252, 222, 160), [
        Nivel("¿Quién es u?", "La regla LIATE para elegir bien.", [g_partes_eleccion], "opciones", 4),
        Nivel("Partes paso a paso", "$\\int u\\,dv = u\\,v - \\int v\\,du$", [g_partes], "tipeo", 3, guiados=2),
        Nivel("Partes con logaritmos", "$\\int x^n \\ln x\\,dx$ y $\\int \\ln x\\,dx$.", [g_partes_log, g_partes_log, g_detective_sust_partes], "tipeo", 3),
        Nivel("Jefe: partes", "Algunas piden partes dos veces. Sin pistas.", [g_jefe7], "tipeo", 3, jefe=True),
    ]),
    Mundo("8", "Mundo 8", "Integrales dobles", (190, 226, 200), [
        Nivel("Rectángulos", "De adentro hacia afuera.", [g_doble_rect], "tipeo", 4),
        Nivel("Regiones tipo I", "La $y$ entre dos curvas.", [g_doble_tipo1], "tipeo", 3),
        Nivel("Cambio de orden", "De $dy\\,dx$ a $dx\\,dy$, mirando el dibujo.", [g_cambio_orden], "opciones", 4),
        Nivel("Coordenadas polares", "$dx\\,dy = r\\,dr\\,d\\theta$", [g_polares], "tipeo", 3),
        Nivel("Jefe: dobles", "Solo el resultado. Sin pistas.", [g_jefe8], "tipeo", 3, jefe=True),
    ]),
    Mundo("9", "Mundo 9", "Integrales triples", (240, 196, 180), [
        Nivel("Cajas", "Tres integrales, una adentro de otra.", [g_triple_caja], "tipeo", 3),
        Nivel("Límites variables", "Tetraedros y regiones bajo un plano.", [g_triple_region], "tipeo", 3),
        Nivel("Cilíndricas", "$dV = r\\,dz\\,dr\\,d\\theta$", [g_cilindricas], "tipeo", 3),
        Nivel("Esféricas", "$dV = \\rho^2\\,\\mathrm{sen}\\,\\varphi\\;d\\rho\\,d\\varphi\\,d\\theta$", [g_esfericas], "tipeo", 3),
        Nivel("Jefe final", "Triples de todo tipo. Sin pistas.", [g_jefe9], "tipeo", 3, jefe=True),
    ]),
]


def mundo_por_id(mid):
    for m in MUNDOS:
        if m.id == mid:
            return m
    raise KeyError(mid)


def generar(mundo_id, nivel_idx, gen_nombre, semilla):
    """Arma un ejercicio exacto a partir de su clave."""
    nivel = mundo_por_id(mundo_id).niveles[nivel_idx]
    ctx = Ctx(random.Random(semilla), nivel.modo, nivel.jefe, nivel.dificultad)
    ej = GENERADORES[gen_nombre](ctx)
    ej.clave = {"mundo": mundo_id, "nivel": nivel_idx, "gen": gen_nombre, "semilla": semilla}
    return ej


_RASGOS = [r"\mathrm{sen}", r"\cos", "e^", r"\ln", r"\sqrt", r"\frac", r"\mathrm{tg}", "Detective", r"\int"]


def _rasgos(ej):
    texto = ej.formula + ej.consigna
    return {r for r in _RASGOS if r in texto}


def generar_nivel(mundo_id, nivel_idx, rng=None):
    """Arma los ejercicios de un nivel buscando variedad (que no salga seno y coseno mil veces)
    y dejando las preguntas de andamiaje solo en el primero."""
    rng = rng or random.Random()
    nivel = mundo_por_id(mundo_id).niveles[nivel_idx]
    ejercicios, vistos = [], set()
    usados = {}
    intentos = 0
    while len(ejercicios) < nivel.cantidad and intentos < nivel.cantidad * 8:
        intentos += 1
        candidatos = []
        for _ in range(4):
            gen = rng.choice(nivel.generadores).__name__
            ej = generar(mundo_id, nivel_idx, gen, rng.randrange(10**9))
            if (ej.consigna, ej.formula) not in vistos:
                anterior = getattr(ejercicios[-1], "gen", None) if ejercicios else None
                repetido = sum(usados.get(r, 0) for r in _rasgos(ej)) + (3 if gen == anterior and "detective" in gen else 0)
                candidatos.append((repetido, rng.random(), ej, gen))
        if not candidatos:
            continue
        _, _, ej, gen = min(candidatos, key=lambda c: (c[0], c[1]))
        ej.gen = gen
        vistos.add((ej.consigna, ej.formula))
        for r in _rasgos(ej):
            usados[r] = usados.get(r, 0) + 1
        if nivel.guiados is not None and len(ejercicios) >= nivel.guiados and "detective" not in gen:
            ej.pasos = ej.pasos[-1:]     # ya lo practicaste guiado: ahora de una
        elif ejercicios:   # el andamiaje (¿cuál es u?, ¿qué jacobiano?...) solo en el primero
            sin_andamio = [p for p in ej.pasos if not p.repetitivo]
            if sin_andamio:
                ej.pasos = sin_andamio
        ejercicios.append(ej)
    return ejercicios
