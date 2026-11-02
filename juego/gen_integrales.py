"""Versión 2: derivadas parciales (Mundo 4) e integrales de una variable
(Mundos 5, 6 y 7: inmediatas, sustitución y partes)."""

from dataclasses import dataclass

import sympy as sp

from .ejercicios import (COS, E, LN, RAIZ, SEN, Ejercicio, Opcion, Paso, _afuera, _FORMAS, _forma_tex,
                         _pot_tex, paso_derivada, paso_elegir, paso_numero, paso_primitiva)
from .mate import ERRORES, tex, tex_par, x, y

R = sp.Rational

ERRORES.update({
    "integral_constante": ("La integral de un número es ese número por x",
                           "$\\int k\\,dx = k\\,x + C$: por ejemplo $\\int 5\\,dx = 5x + C$."),
    "integral_exp_potencia": ("$e^x$ no se integra como potencia",
                              "En $e^x$ la $x$ está en el exponente: $\\int e^x\\,dx = e^x + C$, queda igual."),
    "barrow_falta": ("Te faltó restar $F(a)$",
                     "Regla de Barrow: $\\int_a^b f(x)\\,dx = F(b) - F(a)$. Evaluaste solo en el de arriba."),
    "barrow_integrando": ("Evaluaste la función, no la primitiva",
                          "En Barrow se evalúa la **primitiva** $F$, no la función $f$ de adentro de la integral."),
    "sust_u_todo": ("Esa es la función entera",
                    "Para $u$ conviene lo que está **adentro** de otra función, cuya derivada aparece multiplicando afuera."),
    "sust_u_derivada": ("Esa parte es la que va a formar el $du$",
                        "Lo que está multiplicando suelto suele ser (casi) la derivada de $u$: es lo que se junta con el $dx$ para armar $du$."),
})


def tex_int(f, var="x", a=None, b=None):
    lim = f"_{{{tex(a)}}}^{{{tex(b)}}}" if a is not None else ""
    return f"\\int{lim} {tex_par(f)}\\,d{var}"


# =============================================================== MUNDO 4: parciales

def _monomio(rng, n=None, m=None):
    a = rng.choice([1, 2, 3, 4, 5, -1, -2, -3])
    n = rng.randint(0, 3) if n is None else n
    m = rng.randint(0, 3) if m is None else m
    if n == 0 and m == 0:
        n = 1
    return a * x**n * y**m


def _func_parcial(rng, con_trig):
    """Polinomio en x, y con: un término mixto, uno solo-x y uno solo-y."""
    terminos = [_monomio(rng, rng.randint(1, 3), rng.randint(1, 3)),
                rng.choice([_monomio(rng, rng.randint(1, 4), 0), _monomio(rng, 0, rng.randint(1, 4))])]
    if rng.random() < 0.4:   # a veces, un tercer término
        terminos.append(_monomio(rng, rng.randint(1, 3), 0) if terminos[1].has(y) else _monomio(rng, 0, rng.randint(1, 3)))
    if con_trig:
        a = rng.choice([1, 2, 3, -1, -2])
        extra = rng.choice([a * x**rng.randint(1, 2) * SEN(y), a * E(x) * y**rng.randint(1, 2),
                            a * y * COS(x), a * x * E(y), a * LN(x) * y])
        terminos[0] = extra
    rng.shuffle(terminos)
    return terminos


def _errores_parcial(terminos, v, w):
    f = sum(terminos)
    ok = sp.diff(f, v)
    errs = [(sp.diff(f, w), "parcial_cambiada"), (ok + sp.diff(f, w), "parcial_no_constante")]
    for t in terminos:
        resto = ok - sp.diff(t, v)
        if not t.has(v):
            errs.append((resto + t, "parcial_termino_cero"))
            errs.append((resto + sp.diff(t, w), "parcial_no_constante"))
        elif t.has(w):
            errs.append((resto + sp.diff(t.subs(w, 1), v), "parcial_perdio_factor"))
    return errs


def _pistas_parcial(v, w):
    return [f"Derivás respecto de ${v}$: la ${w}$ es **una constante**, como si fuera un número.",
            f"Los términos sin ${v}$ se van (derivada 0). En los que tienen ${v}$ y ${w}$, la ${w}$ queda multiplicando."]


def _paso_parcial(ctx, f, terminos, v, w, prefijo=None, pistas=True):
    d = sp.diff(f, v)
    expl = (f"Con ${w}$ fija: " + ",  ".join(f"$({tex(t)})'_{v} = {tex(sp.diff(t, v))}$" for t in terminos) + ".")
    return paso_derivada(ctx, f"Derivá respecto de ${v}$:", prefijo or f"f'_{{{v}}} =", d,
                         _errores_parcial(terminos, v, w), _pistas_parcial(v, w) if pistas else [],
                         expl, original=f, var=v, variables=(x, y))


def g_parcial_x(ctx):
    terminos = _func_parcial(ctx.rng, False)
    f = sum(terminos)
    return Ejercicio("Derivada parcial:", f"f(x,y) = {tex(f)}", [_paso_parcial(ctx, f, terminos, x, y)])


def g_parcial_y(ctx):
    terminos = _func_parcial(ctx.rng, False)
    f = sum(terminos)
    return Ejercicio("Derivada parcial:", f"f(x,y) = {tex(f)}", [_paso_parcial(ctx, f, terminos, y, x)])


def g_parciales(ctx):
    terminos = _func_parcial(ctx.rng, True)
    f = sum(terminos)
    return Ejercicio("Calculá las dos derivadas parciales:", f"f(x,y) = {tex(f)}",
                     [_paso_parcial(ctx, f, terminos, x, y), _paso_parcial(ctx, f, terminos, y, x)])


def _func_cadena_xy(rng):
    while True:
        nombre = rng.choice(["exp", "sen", "cos", "ln", "pot", "raiz"])
        af = _afuera(rng, nombre)
        if nombre in ("ln", "raiz"):
            u = x**rng.randint(1, 2) + y**rng.randint(1, 2) + rng.randint(0, 3)
        elif nombre == "pot":
            u = _monomio(rng, rng.randint(1, 2), 0) + _monomio(rng, 0, rng.randint(1, 2))
        else:
            u = _monomio(rng, rng.randint(1, 2), rng.randint(1, 2))
        f = af.F(u)
        if f.has(u):
            return af, u, f


def _paso_parcial_cadena(ctx, af, u, f, v, w, pistas=True):
    du = sp.diff(u, v)
    d = sp.diff(f, v)
    errs = [(af.dF(u), "cadena_sin_interior"), (af.dF(u) * sp.diff(u, w), "parcial_cambiada"),
            (sp.diff(f, w), "parcial_cambiada"), (af.dF(u) * (du + sp.diff(u, w)), "parcial_no_constante")]
    expl = (f"Cadena con $u = {tex(u)}$ y $u'_{v} = {tex(du)}$ (la ${w}$ fija): "
            f"$f'_{v} = {tex_par(af.dF(u))}\\cdot {tex_par(du)}$.")
    p = [f"Es una cadena: {af.regla}", f"Al derivar $u = {tex(u)}$ respecto de ${v}$, la ${w}$ es constante."]
    return paso_derivada(ctx, f"Derivá respecto de ${v}$:", f"f'_{{{v}}} =", d, errs, p if pistas else [],
                         expl, original=f, var=v, variables=(x, y),
                         mostrar=f"{tex_par(af.dF(u))}\\cdot {tex_par(du)}")


def g_parciales_cadena(ctx):
    af, u, f = _func_cadena_xy(ctx.rng)
    return Ejercicio("Calculá las dos derivadas parciales:", f"f(x,y) = {tex(f)}",
                     [_paso_parcial_cadena(ctx, af, u, f, x, y), _paso_parcial_cadena(ctx, af, u, f, y, x)])


def g_jefe4(ctx):
    rng = ctx.rng
    if rng.random() < 0.5:
        terminos = _func_parcial(rng, True)
        f = sum(terminos)
        p1 = _paso_parcial(ctx, f, terminos, x, y, pistas=False)
    else:
        af, u, f = _func_cadena_xy(rng)
        p1 = _paso_parcial_cadena(ctx, af, u, f, x, y, pistas=False)
    fx = sp.diff(f, x)
    fxy = sp.diff(fx, y)
    errs = [(sp.diff(fx, x), "parcial_cambiada"), (sp.diff(f, y), "parcial_cambiada")]
    p2 = paso_derivada(ctx, "Ahora la derivada segunda cruzada: derivá $f'_x$ respecto de $y$.", "f''_{xy} =",
                       fxy, errs, [], "Se deriva el resultado anterior, ahora con la $x$ fija. "
                       "(Por el teorema de Schwarz, da lo mismo que $f''_{yx}$.)", original=fx, var=y,
                       variables=(x, y))
    return Ejercicio("Derivadas parciales (¡y una segunda!):", f"f(x,y) = {tex(f)}", [p1, p2])


# =============================================================== MUNDO 5: integrales inmediatas

@dataclass
class TerminoI:
    expr: object       # lo que se integra
    F: object          # una primitiva
    malos: list        # [(primitiva mal hecha, codigo)]
    pista: str


def ti_potencia(rng, n=None):
    a = rng.choice([1, 2, 3, 4, 5, 6, 8, -1, -2, -3])
    n = rng.randint(1, 5) if n is None else n
    F = a * x**(n + 1) / (n + 1)
    return TerminoI(a * x**n, F, [(a * x**(n + 1), "integral_no_divide"), (a * n * x**(n - 1), "integral_resto"),
                                  (a * x**(n + 1) / n, "integral_no_divide")],
                    "$\\int x^n\\,dx = \\dfrac{x^{n+1}}{n+1}$")


def ti_constante(rng):
    k = rng.choice([1, 2, 3, 4, 5, 7, -2, -3])
    return TerminoI(sp.Integer(k), k * x, [(k * x**2 / 2, "integral_constante")], "$\\int k\\,dx = k\\,x$")


def ti_sen(rng):
    a = rng.choice([1, 2, 3, 4, -1, -2])
    return TerminoI(a * SEN(x), -a * COS(x), [(a * COS(x), "integral_signo")],
                    "$\\int \\mathrm{sen}\\,x\\,dx = -\\cos x$")


def ti_cos(rng):
    a = rng.choice([1, 2, 3, 4, -1, -2])
    return TerminoI(a * COS(x), a * SEN(x), [(-a * SEN(x), "integral_signo")],
                    "$\\int \\cos x\\,dx = \\mathrm{sen}\\,x$")


def ti_exp(rng):
    a = rng.choice([1, 2, 3, 5, -1, -2])
    return TerminoI(a * E(x), a * E(x), [(a * E(x + 1) / (x + 1), "integral_exp_potencia")],
                    "$\\int e^x\\,dx = e^x$")


def ti_inv(rng):
    a = rng.choice([1, 2, 3, 4, 5, -1, -2])
    return TerminoI(a / x, a * LN(x), [(-a / x**2, "integral_derivaste"), (a * LN(x) / x, "integral_1_x")],
                    "$\\int \\frac{1}{x}\\,dx = \\ln|x|$")


TABLA_I = [ti_sen, ti_cos, ti_exp, ti_inv]


def _ejercicio_suma_int(ctx, terminos, consigna="Calculá la integral:"):
    f = sum(t.expr for t in terminos)
    F = sum(t.F for t in terminos)
    errores = []
    for i, t in enumerate(terminos):
        resto = sum(u.F for j, u in enumerate(terminos) if j != i)
        for malo, cod in t.malos:
            errores.append((resto + malo, cod))
    pistas = []
    if len(terminos) > 1:
        pistas.append("La integral de una suma es la suma de las integrales: **término a término**.")
    pistas.append("Acordate: " + ",  ".join(sorted({t.pista for t in terminos})) + ".")
    pistas.append("Para chequear: derivá tu respuesta. Tiene que darte lo de adentro de la integral.")
    expl = "Término a término: " + ",  ".join(f"$\\int {tex_par(t.expr)}\\,dx = {tex(t.F)}$" for t in terminos) + "."
    paso = paso_primitiva(ctx, "¿Cuánto da? (podés agregar $+\\,C$ o no)", "\\int f\\,dx =", F, f, errores,
                          pistas, expl)
    return Ejercicio(consigna, tex_int(f), [paso])


def g_int_potencia(ctx):
    rng = ctx.rng
    terminos = [ti_potencia(rng)]
    if rng.random() < 0.4:
        terminos.append(ti_constante(rng))
    return _ejercicio_suma_int(ctx, terminos)


def g_int_tabla(ctx):
    rng = ctx.rng
    terminos = [rng.choice(TABLA_I)(rng)]
    if rng.random() < 0.5:
        terminos.append(ti_potencia(rng))
    rng.shuffle(terminos)
    return _ejercicio_suma_int(ctx, terminos)


def g_int_sumas(ctx):
    rng = ctx.rng
    terminos = [ti_potencia(rng), rng.choice(TABLA_I)(rng)]
    if rng.random() < 0.35:
        terminos.append(ti_constante(rng))
    rng.shuffle(terminos)
    return _ejercicio_suma_int(ctx, terminos)


def g_int_raices(ctx):
    rng = ctx.rng
    p, forma = rng.choice(_FORMAS)
    a = rng.choice([1, 2, 3, 4, 6, -2])
    f = a * x**p
    cands = [(-p, "reescritura_signo"), (p + 1, "reescritura_raiz"), (p - 1, "reescritura_raiz")]
    if p.q != 1:
        cands.insert(0, (1 / p, "reescritura_raiz"))
    ops = [Opcion(tex=_pot_tex(a, p), correcta=True)]
    vistos = {p}
    for q, cod in cands:
        if q in vistos or q == 0:
            continue
        vistos.add(q)
        ops.append(Opcion(tex=_pot_tex(a, q), error=cod))
        if len(ops) == 4:
            break
    rng.shuffle(ops)
    paso1 = Paso(pregunta="Primero escribí lo de adentro como **potencia** de $x$:", tipo="opcion", opciones=ops,
                 explicacion="$\\sqrt{x} = x^{1/2}$ y lo de abajo sube con exponente negativo: $\\frac{1}{x^n} = x^{-n}$.",
                 resumen=f"$\\int {_pot_tex(a, p)}\\,dx$")
    if p == -1:
        F = a * LN(x)
        errs = [(-a / x**2, "integral_derivaste")]
        expl = ("¡Caso especial! Con exponente $-1$ la regla de la potencia dividiría por 0. "
                f"$\\int \\frac{{1}}{{x}}\\,dx = \\ln|x|$, así que da ${tex(F)}$.")
        pistas = ["Fijate el exponente: si es $-1$, no se usa la regla de la potencia.",
                  "$\\int x^{-1}\\,dx = \\int \\frac{1}{x}\\,dx = \\ln|x| + C$."]
    else:
        F = a * x**(p + 1) / (p + 1)
        errs = [(a * x**(p + 1), "integral_no_divide"), (a * p * x**(p - 1), "integral_resto")]
        expl = (f"$\\int x^{{{tex(p)}}}\\,dx = \\dfrac{{x^{{{tex(p)}+1}}}}{{{tex(p)}+1}} = "
                f"\\dfrac{{x^{{{tex(p + 1)}}}}}{{{tex(p + 1)}}}$. Con el ${a}$ adelante: ${tex(F)}$.")
        pistas = ["Regla de la potencia para integrar: sumás 1 al exponente y dividís por el nuevo exponente.",
                  f"El exponente nuevo es ${tex(p)} + 1 = {tex(p + 1)}$."]
    paso2 = paso_primitiva(ctx, "Ahora integrá:", "\\int f\\,dx =", F, f, errs, pistas, expl, forzar_tipeo=True)
    return Ejercicio("Calculá la integral:", f"\\int {_forma_tex(a, forma)}\\,dx", [paso1, paso2])


def g_barrow(ctx):
    rng = ctx.rng
    terminos = [ti_potencia(rng, rng.randint(1, 3)), rng.choice([ti_constante, ti_potencia])(rng)]
    if terminos[1].expr.is_polynomial(x) and sp.degree(terminos[1].expr, x) == sp.degree(terminos[0].expr, x):
        terminos[1] = ti_constante(rng)
    f = sum(t.expr for t in terminos)
    F = sum(t.F for t in terminos)
    a = rng.choice([0, 0, 1, -1])
    b = rng.choice([1, 2, 3]) if a <= 0 else rng.choice([2, 3])
    valor = F.subs(x, b) - F.subs(x, a)
    errores_F = []
    for i, t in enumerate(terminos):
        resto = sum(u.F for j, u in enumerate(terminos) if j != i)
        errores_F += [(resto + m, c) for m, c in t.malos]
    p1 = paso_primitiva(ctx, "Primero, una primitiva $F(x)$:", "F(x) =", F, f, errores_F,
                        ["Integrá término a término, como en los niveles anteriores."],
                        f"$F(x) = {tex(F)}$ (para Barrow no hace falta la $C$: se cancela).", forzar_tipeo=True)
    p1.resumen = f"$F(x) = {tex(F)}$"
    errs_v = [(F.subs(x, a) - F.subs(x, b), "barrow_orden"), (F.subs(x, b), "barrow_falta"),
              (f.subs(x, b) - f.subs(x, a), "barrow_integrando")]
    p2 = paso_numero(ctx, f"Ahora Barrow: $F({b}) - F({a})$", f"\\int_{{{a}}}^{{{b}}} f\\,dx =", valor, errs_v,
                     ["Regla de Barrow: $\\int_a^b f\\,dx = F(b) - F(a)$.",
                      f"$F({b}) = {tex(F.subs(x, b))}$ y $F({a}) = {tex(F.subs(x, a))}$."],
                     f"$F({b}) - F({a}) = {tex_par(F.subs(x, b))} - {tex_par(F.subs(x, a))} = {tex(valor)}$.",
                     forzar_tipeo=True)
    return Ejercicio("Calculá la integral definida:", tex_int(f, a=a, b=b), [p1, p2])


def g_jefe5(ctx):
    r = ctx.rng.random()
    if r < 0.35:
        return g_barrow(ctx)
    if r < 0.6:
        e = g_int_raices(ctx)
        return e
    return g_int_sumas(ctx)


# =============================================================== MUNDO 6: sustitución

def _adentro_sust(rng, tipos=("poly", "poly", "sen", "cos", "ln", "exp")):
    t = rng.choice(tipos)
    if t == "poly":
        n = rng.choice([1, 2, 2, 3])
        a = rng.choice([1, 2, 3]) if n > 1 else rng.choice([2, 3, 4, 5])
        b = rng.choice([1, 2, 3, 4, 5, -1])
        return t, a * x**n + b, x**(n - 1), a * n
    if t == "sen":
        return t, SEN(x), COS(x), 1
    if t == "cos":
        return t, COS(x), SEN(x), -1
    if t == "ln":
        return t, LN(x), 1 / x, 1
    b = rng.choice([1, 2, 3, 4])
    return t, E(x) + b, E(x), 1


class AfueraI:
    """h(u) y una primitiva H(u)."""

    def __init__(self, nombre, h, H, regla, malos_H):
        self.nombre, self.h, self.H, self.regla, self.malos_H = nombre, h, H, regla, malos_H


def _afuera_int(rng, nombre):
    if nombre == "pot":
        m = rng.randint(2, 5)
        return AfueraI(nombre, lambda u: u**m, lambda u: u**(m + 1) / (m + 1),
                       f"$\\int u^{{{m}}}\\,du = \\dfrac{{u^{{{m + 1}}}}}{{{m + 1}}}$",
                       lambda u: [(u**(m + 1), "integral_no_divide"), (m * u**(m - 1), "integral_resto")])
    if nombre == "cos":
        return AfueraI(nombre, COS, SEN, "$\\int \\cos u\\,du = \\mathrm{sen}\\,u$",
                       lambda u: [(-SEN(u), "integral_signo")])
    if nombre == "sen":
        return AfueraI(nombre, SEN, lambda u: -COS(u), "$\\int \\mathrm{sen}\\,u\\,du = -\\cos u$",
                       lambda u: [(COS(u), "integral_signo")])
    if nombre == "exp":
        return AfueraI(nombre, E, E, "$\\int e^u\\,du = e^u$", lambda u: [])
    if nombre == "inv":
        return AfueraI(nombre, lambda u: 1 / u, LN, "$\\int \\frac{1}{u}\\,du = \\ln|u|$",
                       lambda u: [(-1 / u**2, "integral_derivaste")])
    if nombre == "raiz":
        return AfueraI(nombre, RAIZ, lambda u: R(2, 3) * u**R(3, 2),
                       "$\\int \\sqrt{u}\\,du = \\dfrac{2}{3}u^{3/2}$",
                       lambda u: [(u**R(3, 2), "integral_no_divide"), (1 / (2 * RAIZ(u)), "integral_derivaste")])
    raise ValueError(nombre)


_PROHIBIDOS_SUST = {("ln", "exp"), ("exp", "pot"), ("exp", "raiz"), ("exp", "inv")}


def _armar_sust(rng, acomodar):
    while True:
        t, g, nucleo, c = _adentro_sust(rng)
        h = _afuera_int(rng, rng.choice(["pot", "cos", "sen", "exp", "inv", "raiz"]))
        if (t, h.nombre) in _PROHIBIDOS_SUST:
            continue
        if acomodar:
            if abs(c) == 1:
                continue
            k = rng.choice([1, 2]) if c % 2 == 0 else 1
            if k == c:
                continue
        else:
            k = c
        f = k * h.h(g) * nucleo
        F = sp.Rational(k, c) * h.H(g)
        if not f.has(g) and not (t == "ln"):
            continue
        return t, g, nucleo, c, h, k, f, F


def _paso_u(ctx, f, g, h, nucleo):
    malas = [(f"u = {tex(h.h(g))}", "sust_u_todo"), (f"u = {tex(nucleo)}", "sust_u_derivada"),
             ("u = x", "adentro_x"), (f"u = {tex(f)}", "sust_u_todo")]
    malas = [(t, c) for t, c in malas if t != f"u = {tex(g)}" and t != "u = 1"]
    return paso_elegir(ctx, "¿Qué conviene llamar $u$?", f"u = {tex(g)}", malas,
                       f"$u = {tex(g)}$: está adentro de otra función y su derivada aparece multiplicando.",
                       f"$u = {tex(g)}$")


def _errores_sust(g, h, k, c, F):
    errs = [(k * h.H(g), "sust_constante"), (k * c * h.H(g), "sust_constante"), (-F, "integral_signo")]
    errs += [(sp.Rational(k, c) * m, cod) for m, cod in h.malos_H(g)]
    return errs


def g_sust(ctx, acomodar=False):
    rng = ctx.rng
    t, g, nucleo, c, h, k, f, F = _armar_sust(rng, acomodar)
    dg = sp.diff(g, x)
    coef = "" if sp.Rational(k, c) == 1 else tex(sp.Rational(k, c)) + "\\,"
    pizarron = coef + tex_par(h.H(g)) if coef else tex(h.H(g))
    expl = (f"Con $u = {tex(g)}$, $du = {tex(dg)}\\,dx$. {h.regla}; después se vuelve a $x$"
            + (f" y se acomoda la constante: ${tex(k * nucleo)}\\,dx = \\dfrac{{{k}}}{{{c}}}\\,du$." if k != c else "."))
    pistas = [f"Tomá $u = {tex(g)}$. Entonces $du = {tex(dg)}\\,dx$.",
              f"En $u$ queda {'algo como ' if k != c else ''}{h.regla.split('=')[0]}$. Integrá y reemplazá $u$ por ${tex(g)}$."]
    final = paso_primitiva(ctx, "Resolvé la integral y volvé a $x$:", "\\int f\\,dx =", F, f,
                           _errores_sust(g, h, k, c, F), pistas, expl, mostrar=pizarron)
    if ctx.jefe:
        final.pistas = []
        return Ejercicio("Calculá la integral (sustitución):", tex_int(f), [final])
    if ctx.modo == "opciones":
        return Ejercicio("Calculá la integral (sustitución):", tex_int(f), [_paso_u(ctx, f, g, h, nucleo), final])
    paso_du = paso_derivada(ctx, f"Con $u = {tex(g)}$, ¿cuánto es $u'$? (o sea, $du = u'\\,dx$)", "u' =", dg, [],
                            [f"Derivá $u = {tex(g)}$."], "", original=g)
    return Ejercicio("Calculá la integral (sustitución):", tex_int(f), [_paso_u(ctx, f, g, h, nucleo), paso_du, final])


def g_sust_acomodar(ctx):
    return g_sust(ctx, acomodar=True)


def g_lineal(ctx):
    """∫ e^{kx}, sen(kx), (ax+b)^n...: se divide por la constante de adentro."""
    rng = ctx.rng
    k = rng.choice([2, 3, 4, 5, -2, -3])
    b = rng.choice([0, 0, 1, 2, -1, 3])
    u = k * x + b
    tipo = rng.choice(["exp", "sen", "cos", "pot", "inv"])
    h = _afuera_int(rng, tipo)
    f = h.h(u)
    F = h.H(u) / k
    errs = [(h.H(u), "integral_exp_k" if tipo == "exp" else "sust_constante"),
            (k * h.H(u), "integral_exp_k" if tipo == "exp" else "sust_constante"), (-F, "integral_signo")]
    errs += [(m / k, c) for m, c in h.malos_H(u)]
    expl = (f"Lo de adentro es ${tex(u)}$ y su derivada es ${k}$: hay que **dividir por {k}**. "
            f"{h.regla}, así que da $\\dfrac{{1}}{{{k}}}\\,{tex_par(h.H(u))}$.")
    pistas = [f"Pensalo como sustitución con $u = {tex(u)}$: $du = {k}\\,dx$, o sea $dx = \\dfrac{{du}}{{{k}}}$.",
              h.regla]
    paso = paso_primitiva(ctx, "¿Cuánto da?", "\\int f\\,dx =", F, f, errs, pistas if not ctx.jefe else [], expl,
                          mostrar=f"\\dfrac{{1}}{{{k}}}\\,{tex_par(h.H(u))}")
    return Ejercicio("Calculá la integral:", tex_int(f), [paso])


def g_jefe6(ctx):
    r = ctx.rng.random()
    if r < 0.3:
        return g_lineal(ctx)
    return g_sust(ctx, acomodar=r < 0.65)


# =============================================================== MUNDO 7: partes

def _caso_partes(rng, con_log=False, dificil=False):
    """Devuelve (f, u, dv_sin_dx) con la elección correcta."""
    if con_log:
        n = rng.choice([0, 1, 1, 2, 3])
        a = rng.choice([1, 1, 2, 3])
        dv = a * x**n
        return dv * LN(x), LN(x), dv
    if dificil and rng.random() < 0.5:
        p = x**2
    else:
        p = rng.choice([x, x, 2 * x, 3 * x, x + 1, x - 2, x + 3])
    k = rng.choice([1, 1, 2, 3])
    t = rng.choice([E(k * x), SEN(k * x), COS(k * x)])
    return p * t, p, t


def _paso_eleccion_partes(ctx, f, u, dv):
    correcta = f"u = {tex(u)},\\quad dv = {tex_par(dv)}\\,dx"
    malas = [(f"u = {tex(dv)},\\quad dv = {tex_par(u)}\\,dx", "partes_eleccion"),
             (f"u = {tex(f)},\\quad dv = dx", "partes_eleccion"),
             (f"u = 1,\\quad dv = {tex_par(f)}\\,dx", "partes_eleccion")]
    if dv.is_Number:
        malas = [(f"u = {tex(dv)},\\quad dv = {tex(u)}\\,dx", "partes_eleccion"),
                 (f"u = x,\\quad dv = {tex_par(f / x)}\\,dx", "partes_eleccion"),
                 (f"u = \\frac{{1}}{{x}},\\quad dv = {tex_par(f * x)}\\,dx", "partes_eleccion")]
    return paso_elegir(ctx, "¿Quién es $u$ y quién es $dv$?", correcta, malas,
                       "Regla LIATE: **L**ogaritmos, **I**nversas, **A**lgebraicas, **T**rigonométricas, **E**xponenciales. "
                       "La que aparece primero en la lista va como $u$ (se va a derivar).",
                       f"${correcta}$",
                       pistas=["LIATE: Logaritmos, Inversas, Algebraicas, Trigonométricas, Exponenciales.",
                               "Conviene como $u$ lo que se simplifica al derivar (un polinomio baja de grado, ln x se vuelve 1/x)."])


def g_partes_eleccion(ctx):
    rng = ctx.rng
    f, u, dv = _caso_partes(rng, con_log=rng.random() < 0.35)
    paso = _paso_eleccion_partes(ctx, f, u, dv)
    paso.max_intentos = 2
    return Ejercicio("Integración por partes: $\\int u\\,dv = u\\,v - \\int v\\,du$", tex_int(f), [paso])


def _resolver_partes(f, u, dv):
    du = sp.diff(u, x)
    v = sp.integrate(dv, x)
    F = sp.integrate(f, x)
    resto = sp.integrate(sp.expand(v * du), x)
    errs = [(u * v + resto, "partes_signo"), (u * v, "partes_sin_integral"), (-F, "integral_signo")]
    dv_der = sp.diff(dv, x)
    if dv_der != 0:
        errs.append((u * dv_der - sp.integrate(sp.expand(dv_der * du), x), "partes_v_derivada"))
    return du, v, F, errs


def g_partes(ctx, con_log=False):
    rng = ctx.rng
    f, u, dv = _caso_partes(rng, con_log=con_log, dificil=ctx.jefe)
    du, v, F, errs = _resolver_partes(f, u, dv)
    pizarron = f"{tex_par(u)}\\cdot {tex_par(v)} - \\int {tex_par(v)}\\cdot {tex_par(du)}\\,dx"
    expl = (f"$\\int u\\,dv = u\\,v - \\int v\\,du$ con $u = {tex(u)}$, $v = {tex(v)}$: "
            f"${pizarron}$, y esa última integral es inmediata.")
    if u.is_polynomial(x) and sp.degree(u, x) == 2:
        expl += " Como $u = x^2$, la integral que queda pide **partes otra vez**."
    final = paso_primitiva(ctx, "Armá $u\\,v - \\int v\\,du$ y resolvé lo que queda:", "\\int f\\,dx =", F, f, errs,
                           ["$\\int u\\,dv = u\\,v - \\int v\\,du$.", f"Te queda por resolver $\\int {tex_par(sp.expand(v * du))}\\,dx$."],
                           expl, forzar_tipeo=True)
    if ctx.jefe:
        final.pistas = []
        return Ejercicio("Calculá la integral (por partes):", tex_int(f), [final])
    p_du = paso_derivada(ctx, "¿Cuánto es $du$? (escribí lo que multiplica a $dx$)", "du =", du, [],
                         [f"Derivá $u = {tex(u)}$."], "", original=u, forzar_tipeo=True)
    p_du.resumen = f"$du = {tex(du)}\\,dx$"
    p_v = paso_primitiva(ctx, f"¿Cuánto es $v$? (integrá $dv = {tex_par(dv)}\\,dx$, sin $+\\,C$)", "v =", v, dv,
                         [(sp.diff(dv, x), "partes_v_derivada")],
                         [f"$v = \\int {tex_par(dv)}\\,dx$. Ojo: a $dv$ se lo **integra**."], "", forzar_tipeo=True)
    p_v.resumen = f"$v = {tex(v)}$"
    return Ejercicio("Calculá la integral (por partes):", tex_int(f),
                     [_paso_eleccion_partes(ctx, f, u, dv), p_du, p_v, final])


def g_partes_log(ctx):
    return g_partes(ctx, con_log=True)


def g_jefe7(ctx):
    return g_partes(ctx, con_log=ctx.rng.random() < 0.35)


GENERADORES_V2 = [g_parcial_x, g_parcial_y, g_parciales, g_parciales_cadena, g_jefe4,
                  g_int_potencia, g_int_tabla, g_int_sumas, g_int_raices, g_barrow, g_jefe5,
                  g_lineal, g_sust, g_sust_acomodar, g_jefe6,
                  g_partes_eleccion, g_partes, g_partes_log, g_jefe7]
