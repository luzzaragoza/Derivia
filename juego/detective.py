"""'Detective de errores': te muestran la resolución de otra persona y tenés que
decir si está bien y, si no, qué error cometió. Para cortar con la repetición."""

import sympy as sp

from .ejercicios import Ctx, Ejercicio, Opcion, Paso, g_cadena, g_cadena_producto, g_cadena_trasc, g_cociente, \
    g_producto, g_sumas, g_tabla
from .gen_integrales import g_int_sumas, g_lineal, g_parciales_cadena, g_partes, g_sust_acomodar
from .mate import ERRORES, equivalentes, tex, x

ERRORES["detective_estaba_bien"] = ("¡Estaba bien!",
                                    "Esa respuesta era correcta. A veces está escrita distinto de como la pensaste vos.")
ERRORES["detective_otro_error"] = ("Ese no fue el error", "Fijate bien qué parte de la cuenta se torció.")

# Familias: dos razones de la misma familia describen "el mismo tipo" de error (si una es correcta,
# la otra también lo parece). Nunca se ponen juntas como opciones.
FAMILIAS = {
    "signo": ["signo_sen", "signo_cos", "signo_general", "integral_signo", "producto_signo", "cociente_signo_mas",
              "cociente_orden", "partes_signo", "potencia_negativa_signo", "reescritura_signo"],
    "numero": ["factor_constante", "integral_factor", "integral_no_divide", "integral_exp_k", "sust_constante",
               "raiz_sin_2", "potencia_no_baja"],
    "constante": ["constante_de_mas", "constante_no_cero", "parcial_termino_cero"],
    "exponente": ["potencia_no_resta", "potencia_suma", "potencia_negativa", "integral_resto", "reescritura_raiz"],
    "cadena": ["cadena_sin_interior", "cadena_evaluar_derivada", "cadena_afuera_en_x", "cadena_doble_falta"],
    "producto": ["producto_derivadas", "producto_falta_termino"],
    "cociente": ["cociente_sin_cuadrado", "cociente_derivadas"],
    "parcial": ["parcial_cambiada", "parcial_no_constante", "parcial_perdio_factor"],
    "integrar": ["integral_derivaste", "no_integraste", "no_derivaste", "no_derivaste_termino"],
    "tabla": ["exp_como_potencia", "integral_exp_potencia", "ln_derivada", "integral_1_x"],
    "partes": ["partes_sin_integral", "partes_v_derivada"],
}
FAMILIA = {c: f for f, cs in FAMILIAS.items() for c in cs}

# Razones posibles según el tema (así nunca aparece "cociente" en una integral, por ejemplo)
POR_TEMA = {
    "basicas": ["potencia_no_resta", "potencia_suma", "potencia_no_baja", "signo_cos", "signo_sen", "exp_como_potencia",
                "ln_derivada", "constante_no_cero", "constante_de_mas"],
    "producto": ["producto_derivadas", "producto_falta_termino", "producto_signo", "cociente_signo_mas", "cociente_orden",
                 "cociente_sin_cuadrado", "cociente_derivadas", "potencia_no_resta", "signo_cos", "signo_sen"],
    "cadena": ["cadena_sin_interior", "cadena_afuera_en_x", "potencia_no_resta", "signo_cos", "signo_sen",
               "exp_como_potencia", "producto_falta_termino", "ln_derivada"],
    "parciales": ["parcial_cambiada", "parcial_no_constante", "parcial_termino_cero", "cadena_sin_interior",
                  "potencia_no_resta"],
    "integrales": ["integral_no_divide", "integral_resto", "integral_derivaste", "integral_signo", "integral_1_x",
                   "integral_exp_k", "integral_exp_potencia"],
    "sust_partes": ["sust_constante", "partes_signo", "partes_sin_integral", "partes_v_derivada", "integral_signo",
                    "integral_derivaste"],
}
# Errores que no se usan en el detective: dan expresiones que nadie escribiría (ej. 6480x^8)
NO_USAR = {"no_derivaste", "constante_mal", "cadena_evaluar_derivada", "numero_aprox"}


def _pega(codigo, formula, base=""):
    """¿Esta razón tiene que ver con la función del ejercicio? (base: el generador que lo armó)"""
    f = formula
    if (codigo.startswith("partes_") and base != "g_partes") or (codigo.startswith("sust_") and base == "g_partes"):
        return False
    necesita = {"signo_cos": ["cos"], "signo_sen": ["sen"], "exp_como_potencia": ["e^"], "integral_exp_potencia": ["e^"],
                "integral_exp_k": ["e^"], "ln_derivada": ["ln"], "integral_1_x": ["frac", "ln"]}
    if codigo in necesita and not any(n in f for n in necesita[codigo]):
        return False
    es_cociente = "\\frac" in f and "\\int" not in f
    if FAMILIA.get(codigo) == "cociente" or codigo in ("cociente_signo_mas", "cociente_orden"):
        return es_cociente
    if FAMILIA.get(codigo) == "producto" or codigo == "producto_signo":
        return not es_cociente
    return True


def _misma(a, b, primitiva=False):
    """¿Dan lo mismo? (en integrales, si difieren en una constante también es lo mismo).
    primitiva: False, o la variable de integración."""
    try:
        if primitiva is not False and primitiva is not None:
            v = x if primitiva is True else primitiva
            return equivalentes(sp.diff(sp.sympify(a) - sp.sympify(b), v), 0)
        return equivalentes(a, b)
    except Exception:
        return False


def _detective(ctx, bases, tema):
    rng = ctx.rng
    sub = Ctx(rng, "tipeo", False, ctx.dificultad)
    elegido = None
    for _ in range(30):
        gen = rng.choice(bases)
        ej = gen(sub)
        ej.base = gen.__name__
        final = ej.pasos[-1]
        if final.tipo != "expresion":
            continue
        errores = [(e, c) for e, c in final.errores if c in ERRORES and c not in NO_USAR]
        # sirven los errores que no dan lo mismo que la respuesta correcta y que no se confunden
        # con otro error de distinta familia (si no, habría dos razones correctas)
        prim = (final.var or x) if final.chequeo == "primitiva" else False
        limpios = []
        for e, c in errores:
            if _misma(e, final.esperado, prim):
                continue
            if any(c2 != c and FAMILIA.get(c2, c2) != FAMILIA.get(c, c) and _misma(e, e2, prim) for e2, c2 in errores):
                continue
            if not _pega(c, ej.formula, ej.base):
                continue
            limpios.append((e, c))
        if limpios:
            elegido = (ej, final, errores, limpios)
            break
    if elegido is None:      # muy raro: se muestra uno que está bien
        gen = rng.choice(bases)
        ej = gen(sub)
        ej.base = gen.__name__
        final, errores, limpios = ej.pasos[-1], [], []
    ej, final, errores, limpios = elegido or (ej, final, errores, limpios)
    esta_bien = not limpios or rng.random() < 0.35
    sufijo = r" + C" if final.chequeo == "primitiva" else ""
    correcto = f"{final.prefijo} {final.mostrar or tex(final.esperado)}{sufijo}"
    if esta_bien:
        mostrado, codigo = correcto, None
    else:
        expr, codigo = rng.choice(limpios)
        mostrado = f"{final.prefijo} {tex(expr)}{sufijo}"
    ops = [Opcion(texto="Sí, está bien", correcta=esta_bien, error=None if esta_bien else codigo),
           Opcion(texto="No, tiene un error", correcta=not esta_bien,
                  error="detective_estaba_bien" if esta_bien else None)]
    p1 = Paso(pregunta=f"Escribió  ${mostrado}$\n¿Está bien?", tipo="opcion", opciones=ops, max_intentos=1,
              explicacion=("¡Exacto, estaba bien!" if esta_bien else "Sí: hay un error. ¿Te animás a decir cuál?"),
              resumen=f"Escribió ${mostrado}$: " + ("bien" if esta_bien else "tiene un error"))
    pasos = [p1]
    if not esta_bien:
        titulo = ERRORES[codigo][0]
        # que no esté entre las opciones ninguna razón que TAMBIÉN explique lo que escribió
        prim = (final.var or x) if final.chequeo == "primitiva" else False
        explican = {c for e, c in errores if _misma(e, expr, prim)}
        prohibidas = {FAMILIA.get(c, c) for c in explican | {codigo}}
        propios = [c for _, c in errores]
        rng.shuffle(propios)
        resto = list(POR_TEMA[tema])
        rng.shuffle(resto)
        malas, vistos, familias = [], {titulo}, set(prohibidas)
        for c in propios + resto:
            if c in NO_USAR or c not in ERRORES or not _pega(c, ej.formula, getattr(ej, "base", "")):
                continue
            fam, t = FAMILIA.get(c, c), ERRORES[c][0]
            if t in vistos or fam in familias:
                continue
            vistos.add(t)
            familias.add(fam)
            malas.append(Opcion(texto=t, error="detective_otro_error"))
            if len(malas) == 2:
                break
        ops2 = [Opcion(texto=titulo, correcta=True)] + malas
        rng.shuffle(ops2)
        pasos.append(Paso(pregunta="¿Qué error cometió?", tipo="opcion", opciones=ops2, max_intentos=2,
                          explicacion=f"{ERRORES[codigo][1]}\nLo correcto era: ${correcto}$",
                          resumen=f"Error: {titulo}"))
    nuevo = Ejercicio("**Detective de errores.** Alguien resolvió esto:", ej.formula, pasos)
    nuevo.base = ej.base
    return nuevo


def g_detective_basicas(ctx):
    return _detective(ctx, [g_sumas, g_tabla], "basicas")


def g_detective_producto(ctx):
    return _detective(ctx, [g_producto, g_cociente], "producto")


def g_detective_cadena(ctx):
    return _detective(ctx, [g_cadena, g_cadena_trasc, g_cadena_producto], "cadena")


def g_detective_parciales(ctx):
    return _detective(ctx, [g_parciales_cadena], "parciales")


def g_detective_integrales(ctx):
    return _detective(ctx, [g_int_sumas, g_lineal], "integrales")


def g_detective_sust_partes(ctx):
    return _detective(ctx, [g_sust_acomodar, g_partes], "sust_partes")


GENERADORES_DETECTIVE = [g_detective_basicas, g_detective_producto, g_detective_cadena, g_detective_parciales,
                         g_detective_integrales, g_detective_sust_partes]
