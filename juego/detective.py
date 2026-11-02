"""'Detective de errores': te muestran la resolución de otra persona y tenés que
decir si está bien y, si no, qué error cometió. Para cortar con la repetición."""

from .ejercicios import Ctx, Ejercicio, Opcion, Paso, g_cadena, g_cadena_producto, g_cadena_trasc, g_cociente, \
    g_producto, g_sumas, g_tabla
from .gen_integrales import g_int_sumas, g_lineal, g_parciales_cadena, g_partes, g_sust_acomodar
from .mate import ERRORES, tex

ERRORES["detective_estaba_bien"] = ("¡Estaba bien!",
                                    "Esa respuesta era correcta. A veces está escrita distinto de como la pensaste vos.")
ERRORES["detective_otro_error"] = ("Ese no fue el error", "Fijate bien qué parte de la cuenta se torció.")

_COMUNES = ["signo_general", "factor_constante", "constante_de_mas", "potencia_no_resta", "cadena_sin_interior",
            "producto_derivadas", "cociente_signo_mas", "integral_no_divide", "signo_cos", "integral_signo"]


def _detective(ctx, bases):
    rng = ctx.rng
    sub = Ctx(rng, "tipeo", False, ctx.dificultad)
    for _ in range(20):
        ej = rng.choice(bases)(sub)
        final = ej.pasos[-1]
        errores = [(e, c) for e, c in final.errores if c in ERRORES and c not in ("no_derivaste", "constante_mal")]
        if final.tipo == "expresion" and errores:
            break
    esta_bien = rng.random() < 0.35
    sufijo = r" + C" if final.chequeo == "primitiva" else ""
    correcto = f"{final.prefijo} {final.mostrar or tex(final.esperado)}{sufijo}"
    if esta_bien:
        mostrado, codigo = correcto, None
    else:
        expr, codigo = rng.choice(errores)
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
        candidatos = [c for _, c in errores] + _COMUNES
        rng.shuffle(candidatos)
        malas, vistos = [], {titulo}
        for c in candidatos:
            t = ERRORES[c][0]
            if t not in vistos:
                vistos.add(t)
                malas.append(Opcion(texto=t, error="detective_otro_error"))
            if len(malas) == 2:
                break
        ops2 = [Opcion(texto=titulo, correcta=True)] + malas
        rng.shuffle(ops2)
        pasos.append(Paso(pregunta="¿Qué error cometió?", tipo="opcion", opciones=ops2, max_intentos=2,
                          explicacion=f"{ERRORES[codigo][1]}\nLo correcto era: ${correcto}$",
                          resumen=f"Error: {titulo}"))
    return Ejercicio("**Detective de errores.** Alguien resolvió esto:", ej.formula, pasos)


def g_detective_basicas(ctx):
    return _detective(ctx, [g_sumas, g_tabla])


def g_detective_producto(ctx):
    return _detective(ctx, [g_producto, g_cociente])


def g_detective_cadena(ctx):
    return _detective(ctx, [g_cadena, g_cadena_trasc, g_cadena_producto])


def g_detective_parciales(ctx):
    return _detective(ctx, [g_parciales_cadena])


def g_detective_integrales(ctx):
    return _detective(ctx, [g_int_sumas, g_lineal])


def g_detective_sust_partes(ctx):
    return _detective(ctx, [g_sust_acomodar, g_partes])


GENERADORES_DETECTIVE = [g_detective_basicas, g_detective_producto, g_detective_cadena, g_detective_parciales,
                         g_detective_integrales, g_detective_sust_partes]
