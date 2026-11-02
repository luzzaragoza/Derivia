"""Versión 3: integrales dobles (Mundo 8) y triples (Mundo 9)."""

import mpmath
import sympy as sp

from .ejercicios import Ejercicio, paso_derivada, paso_elegir, paso_numero
from .mate import ERRORES, tex, tex_par, x, y, z

R = sp.Rational
PI = sp.pi
r, t, p = sp.symbols("r theta phi", nonnegative=True)   # polares / cilíndricas / esféricas (rho = r)

ERRORES.update({
    "doble_sin_evaluar": ("Falta evaluar entre los límites",
                          "Después de integrar hay que hacer Barrow con los límites de esa integral: la variable integrada **no puede quedar**."),
    "doble_variable": ("Integraste en la otra variable",
                       "Fijate el diferencial de adentro: con $dy$ se integra en $y$ y la $x$ queda fija (como en las derivadas parciales)."),
    "cambio_letras": ("No alcanza con cambiar las letras",
                      "Para cambiar el orden hay que **despejar**: si $y = x^2$, entonces $x = \\sqrt{y}$. Mirá el dibujo y leé la región de izquierda a derecha."),
    "limites_afuera": ("Afuera van números",
                       "Los límites de la integral de **afuera** tienen que ser números fijos. Las curvas van en la de adentro."),
    "polar_f": ("Revisá cómo queda la función en polares",
                "Con $x = r\\cos\\theta$, $y = r\\,\\mathrm{sen}\\,\\theta$: $x^2 + y^2 = r^2$ y $\\sqrt{x^2+y^2} = r$."),
    "angulo_mal": ("Revisá el rango de $\\theta$",
                   "Círculo entero: $0 \\leq \\theta \\leq 2\\pi$. Mitad de arriba: $0 \\leq \\theta \\leq \\pi$. Primer cuadrante: $0 \\leq \\theta \\leq \\frac{\\pi}{2}$."),
    "radio_mal": ("Revisá el rango de $r$",
                  "$r$ va del borde de adentro al de afuera. Si $x^2 + y^2 \\leq 4$, el radio es $2$ (no $4$)."),
    "phi_mal": ("Revisá el rango de $\\varphi$",
                "$\\varphi$ se mide desde el eje $z$ positivo: esfera entera $0 \\leq \\varphi \\leq \\pi$, mitad de arriba $0 \\leq \\varphi \\leq \\frac{\\pi}{2}$."),
})


def _lim(a, b):
    return f"_{{{tex(a)}}}^{{{tex(b)}}}"


# =============================================================== MUNDO 8: dobles

_FUNCS_2 = [sp.Integer(1), x, y, x * y, 2 * x, x + y, 6 * x * y, 3 * y**2, x**2, 4 * x * y]


def _f_simple(rng, opciones=_FUNCS_2):
    return rng.choice(opciones)


def _paso_interior(ctx, f, var, a, b, otra, pistas=True, prefijo_extra=""):
    """∫_a^b f d(var), con la otra variable fija."""
    esperado = sp.integrate(f, (var, a, b))
    errs = [(sp.integrate(f, var), "doble_sin_evaluar"), (sp.integrate(f, (var, b, a)), "barrow_orden"),
            (sp.integrate(f, var).subs(var, b), "barrow_falta")]
    if otra is not None:
        errs.append((sp.integrate(f, (otra, a, b)), "doble_variable"))
    prim = sp.integrate(f, var)
    expl = (f"Primitiva en ${var}$: ${tex(prim)}$. Evaluada entre ${tex(a)}$ y ${tex(b)}$: "
            f"${tex_par(prim.subs(var, b))} - {tex_par(prim.subs(var, a))} = {tex(esperado)}$.")
    p_ = [f"Integrá en ${var}$ dejando {'las otras letras' if otra is None else f'la ${otra}$'} fija(s), como si fueran números.",
          f"No te olvides de evaluar: $F({tex(b)}) - F({tex(a)})$."] if pistas else []
    paso = paso_derivada(ctx, f"Integral de adentro (en ${var}$):", f"\\int{_lim(a, b)} {tex_par(f)}\\,d{var} =",
                         esperado, errs, p_, expl, forzar_tipeo=True, variables=(x, y, z))
    paso.resumen = f"$\\int{_lim(a, b)} {tex_par(f)}\\,d{var} = {tex(esperado)}$"
    return paso, esperado


def _paso_exterior(ctx, g, var, a, b, valor, pistas=True, prefijo="\\iint_R f\\,dA ="):
    errs = [(-valor, "barrow_orden"), (sp.integrate(g, var).subs(var, b), "barrow_falta")]
    prim = sp.integrate(g, var)
    expl = (f"$\\int{_lim(a, b)} {tex_par(g)}\\,d{var} = \\left[{tex(prim)}\\right]{_lim(a, b)} = {tex(valor)}$.")
    return paso_numero(ctx, f"Integral de afuera (en ${var}$):", prefijo, valor, errs,
                       [f"Ahora integrá ${tex(g)}$ en ${var}$ entre ${tex(a)}$ y ${tex(b)}$."] if pistas else [],
                       expl, forzar_tipeo=True)


def g_doble_rect(ctx):
    rng = ctx.rng
    a, b = 0, rng.choice([1, 2, 3])
    c, d = rng.choice([(0, 1), (0, 2), (1, 2), (0, 3), (1, 3)])
    f = _f_simple(rng, _FUNCS_2[1:])
    valor = sp.integrate(f, (y, c, d), (x, a, b))
    formula = f"\\int{_lim(a, b)}\\int{_lim(c, d)} {tex_par(f)}\\,dy\\,dx"
    graf = {"tipo": "rect", "a": a, "b": b, "c": c, "d": d}
    if ctx.jefe:
        return Ejercicio("Calculá la integral doble:", formula,
                         [paso_numero(ctx, "¿Cuánto da?", "I =", valor, [], [], "", forzar_tipeo=True)], grafico=graf)
    p1, g = _paso_interior(ctx, f, y, c, d, x)
    p2 = _paso_exterior(ctx, g, x, a, b, valor)
    return Ejercicio("Calculá la integral doble (de adentro hacia afuera):", formula, [p1, p2], grafico=graf)


# regiones: tipo I (x de a a b, y de g1 a g2) y su versión tipo II (y de c a d, x de h1 a h2)
_REGIONES = [
    dict(a=0, b=1, g1=sp.Integer(0), g2=x, c=0, d=1, h1=y, h2=sp.Integer(1)),
    dict(a=0, b=1, g1=x**2, g2=x, c=0, d=1, h1=y, h2=sp.sqrt(y)),
    dict(a=0, b=2, g1=sp.Integer(0), g2=x**2, c=0, d=4, h1=sp.sqrt(y), h2=sp.Integer(2)),
    dict(a=0, b=4, g1=sp.Integer(0), g2=sp.sqrt(x), c=0, d=2, h1=y**2, h2=sp.Integer(4)),
    dict(a=0, b=2, g1=x**2, g2=2 * x, c=0, d=4, h1=y / 2, h2=sp.sqrt(y)),
    dict(a=0, b=2, g1=sp.Integer(0), g2=2 - x, c=0, d=2, h1=sp.Integer(0), h2=2 - y),
    dict(a=0, b=3, g1=sp.Integer(0), g2=3 - x, c=0, d=3, h1=sp.Integer(0), h2=3 - y),
    dict(a=0, b=1, g1=x, g2=sp.Integer(1), c=0, d=1, h1=sp.Integer(0), h2=y),
    dict(a=0, b=2, g1=sp.Integer(0), g2=x, c=0, d=2, h1=y, h2=sp.Integer(2)),
]


def _tex_iter(a, b, c, d, f="f", orden="dy\\,dx"):
    return f"\\int{_lim(a, b)}\\int{_lim(c, d)} {f}\\,{orden}"


def _graf_I(reg):
    return {"tipo": "I", "a": reg["a"], "b": reg["b"], "g1": reg["g1"], "g2": reg["g2"]}


def _paso_limites_I(ctx, reg, f_tex="f"):
    a, b, g1, g2 = reg["a"], reg["b"], reg["g1"], reg["g2"]
    correcta = _tex_iter(a, b, g1, g2, f_tex)
    malas = [(_tex_iter(a, b, g2, g1, f_tex), "limites_al_reves"),
             (_tex_iter(g1, g2, a, b, f_tex), "limites_afuera"),
             (_tex_iter(reg["c"], reg["d"], g1, g2, f_tex), "limites_mal"),
             (_tex_iter(a, b, a, b, f_tex), "limites_mal")]
    return paso_elegir(ctx, "Mirá el dibujo. ¿Cuál es la integral iterada (primero $dy$)?", correcta, malas,
                       f"Para cada $x$ entre ${tex(a)}$ y ${tex(b)}$, la $y$ va de la curva de abajo, $y = {tex(g1)}$, "
                       f"a la de arriba, $y = {tex(g2)}$.", f"${correcta}$",
                       pistas=["Tipo I: la $x$ va entre números fijos y la $y$, entre dos curvas.",
                               "Adentro: de la curva de **abajo** a la de **arriba**."])


def g_doble_tipo1(ctx):
    rng = ctx.rng
    reg = rng.choice(_REGIONES)
    f = _f_simple(rng)
    a, b, g1, g2 = reg["a"], reg["b"], reg["g1"], reg["g2"]
    valor = sp.integrate(f, (y, g1, g2), (x, a, b))
    region_tex = f"R:\\ {tex(a)} \\leq x \\leq {tex(b)},\\ {tex(g1)} \\leq y \\leq {tex(g2)}"
    formula = f"\\iint_R {tex_par(f)}\\,dA"
    consigna = f"Calculá la integral sobre la región sombreada ${region_tex}$:"
    if ctx.jefe:
        return Ejercicio(consigna, formula, [paso_numero(ctx, "¿Cuánto da?", "I =", valor, [], [], "",
                                                         forzar_tipeo=True)], grafico=_graf_I(reg))
    p0 = _paso_limites_I(ctx, reg, tex_par(f) if f != 1 else "1")
    p1, gx = _paso_interior(ctx, f, y, g1, g2, None)
    p2 = _paso_exterior(ctx, gx, x, a, b, valor)
    return Ejercicio(consigna, formula, [p0, p1, p2], grafico=_graf_I(reg))


def g_cambio_orden(ctx):
    rng = ctx.rng
    reg = rng.choice(_REGIONES)
    a, b, g1, g2, c, d, h1, h2 = (reg[k] for k in ("a", "b", "g1", "g2", "c", "d", "h1", "h2"))
    correcta = _tex_iter(c, d, h1, h2, orden="dx\\,dy")
    letras = lambda e: sp.sympify(e).subs(x, y)  # noqa: E731
    malas = [(_tex_iter(c, d, h2, h1, orden="dx\\,dy"), "limites_al_reves"),
             (_tex_iter(c, d, letras(g1), letras(g2), orden="dx\\,dy"), "cambio_letras"),
             (_tex_iter(h1, h2, c, d, orden="dx\\,dy"), "limites_afuera"),
             (_tex_iter(a, b, letras(g1), letras(g2), orden="dx\\,dy"), "cambio_letras")]
    paso = paso_elegir(ctx, "¿Cuál es la misma integral con el orden cambiado (primero $dx$)?", correcta, malas,
                       f"Leída de izquierda a derecha: $y$ entre ${tex(c)}$ y ${tex(d)}$, y para cada $y$ la $x$ va de "
                       f"$x = {tex(h1)}$ a $x = {tex(h2)}$ (se despeja $x$ de cada curva).", f"${correcta}$",
                       pistas=["Ahora la $y$ va entre números fijos: el punto más bajo y el más alto de la región.",
                               "Para los límites de $x$ despejá $x$ de cada curva: izquierda abajo, derecha arriba."])
    return Ejercicio("Cambiá el orden de integración:", _tex_iter(a, b, g1, g2), [paso], grafico=_graf_I(reg))


# ---- polares
_POLARES = [
    ("disco", lambda a: dict(r1=0, r2=a, t1=0, t2=2 * PI, desc=f"x^2 + y^2 \\leq {a**2}")),
    ("anillo", None),
    ("medio", lambda a: dict(r1=0, r2=a, t1=0, t2=PI, desc=f"x^2 + y^2 \\leq {a**2},\\ y \\geq 0")),
    ("cuarto", lambda a: dict(r1=0, r2=a, t1=0, t2=PI / 2, desc=f"x^2 + y^2 \\leq {a**2},\\ x \\geq 0,\\ y \\geq 0")),
]


def _region_polar(rng):
    tipo = rng.choice(["disco", "disco", "anillo", "medio", "cuarto"])
    if tipo == "anillo":
        a, b = rng.choice([(1, 2), (1, 3), (2, 3)])
        return tipo, dict(r1=a, r2=b, t1=0, t2=2 * PI, desc=f"{a**2} \\leq x^2 + y^2 \\leq {b**2}")
    a = rng.choice([1, 2, 3])
    return tipo, dict(_POLARES[[n for n, _ in _POLARES].index(tipo)][1](a))


def _f_polar(rng, tipo):
    """(f cartesiana tex, f(x,y) sympy, f en polares)"""
    opciones = [("1", sp.Integer(1), sp.Integer(1)),
                ("x^2 + y^2", x**2 + y**2, r**2),
                ("\\sqrt{x^2 + y^2}", sp.sqrt(x**2 + y**2), r)]
    if tipo in ("medio", "cuarto"):
        opciones.append(("y", y, r * sp.sin(t)))
    if tipo == "cuarto":
        opciones.append(("x", x, r * sp.cos(t)))
    if tipo == "disco":
        opciones.append(("e^{x^2 + y^2}", sp.exp(x**2 + y**2), sp.exp(r**2)))
    if tipo == "anillo":
        opciones.append(("\\dfrac{1}{x^2 + y^2}", 1 / (x**2 + y**2), 1 / r**2))
    return rng.choice(opciones)


def _verif_polar(fxy, reg):
    f = sp.lambdify((x, y), fxy, "mpmath")
    r1, r2, t1, t2 = (float(reg[k]) for k in ("r1", "r2", "t1", "t2"))
    return lambda: mpmath.quad(lambda tt, rr: f(rr * mpmath.cos(tt), rr * mpmath.sin(tt)) * rr, [t1, t2], [r1, r2])


def g_polares(ctx):
    rng = ctx.rng
    tipo, reg = _region_polar(rng)
    ftex, fxy, fp = _f_polar(rng, tipo)
    valor = sp.simplify(sp.integrate(fp * r, (r, reg["r1"], reg["r2"]), (t, reg["t1"], reg["t2"])))
    formula = f"\\iint_R {ftex}\\,dA"
    consigna = f"Pasá a polares y calculá, con $R:\\ {reg['desc']}$:"
    graf = {"tipo": "polar", "r1": reg["r1"], "r2": reg["r2"], "t1": reg["t1"], "t2": reg["t2"]}
    errs_v = [(sp.integrate(fp, (r, reg["r1"], reg["r2"]), (t, reg["t1"], reg["t2"])), "jacobiano_polar")]
    if ctx.jefe:
        e = Ejercicio(consigna, formula, [paso_numero(ctx, "¿Cuánto da?", "I =", valor, errs_v, [], "",
                                                      forzar_tipeo=True)], grafico=graf)
        e.verificar = _verif_polar(fxy, reg)
        return e
    fp_tex = tex(fp)
    pre = "" if fp == 1 else f"{fp_tex} \\cdot "
    correcta = f"{pre}r\\,dr\\,d\\theta" if fp != 1 else "r\\,dr\\,d\\theta"
    malas = [(f"{fp_tex}\\,dr\\,d\\theta", "jacobiano_polar"),
             (f"{pre}r^{{2}}\\,dr\\,d\\theta", "jacobiano_polar")]
    if fp == r**2:
        malas.append(("r \\cdot r\\,dr\\,d\\theta", "polar_f"))
    elif fp == r:
        malas.append(("r^{2} \\cdot r\\,dr\\,d\\theta", "polar_f"))
    else:
        malas.append((f"{pre}2\\pi\\,dr\\,d\\theta", "jacobiano_polar"))
    p1 = paso_elegir(ctx, f"Con $x = r\\cos\\theta$, $y = r\\,\\mathrm{{sen}}\\,\\theta$: ¿en qué se transforma ${ftex}\\,dx\\,dy$?",
                     correcta, malas, "La función se escribe en $r$ y $\\theta$, y $dx\\,dy = r\\,dr\\,d\\theta$ "
                     "(la $r$ es el jacobiano).", f"${ftex}\\,dx\\,dy = {correcta}$",
                     pistas=["$x^2 + y^2 = r^2$.", "No te olvides del jacobiano: $dx\\,dy = r\\,dr\\,d\\theta$."])
    p1.repetitivo = True
    r1, r2, t1, t2 = reg["r1"], reg["r2"], reg["t1"], reg["t2"]

    def lims(a1, a2, b1, b2):
        return f"{tex(a1)} \\leq r \\leq {tex(a2)},\\quad {tex(b1)} \\leq \\theta \\leq {tex(b2)}"
    otros_t = [v for v in (PI / 2, PI, 2 * PI) if v != t2]
    malas_l = [(lims(r1, r2, t1, otros_t[0]), "angulo_mal"), (lims(r1, r2, t1, otros_t[1]), "angulo_mal"),
               (lims(r1, r2**2, t1, t2), "radio_mal")]
    if r1 != 0:
        malas_l.insert(0, (lims(0, r2, t1, t2), "radio_mal"))
    p2 = paso_elegir(ctx, "Mirá el dibujo: ¿qué límites tienen $r$ y $\\theta$?", lims(r1, r2, t1, t2), malas_l,
                     "El radio va del borde de adentro al de afuera, y el ángulo barre la parte que está sombreada.",
                     f"${lims(r1, r2, t1, t2)}$",
                     pistas=["El radio de $x^2 + y^2 \\leq a^2$ es $a$ (la raíz).",
                             "Círculo entero $2\\pi$, la mitad $\\pi$, un cuarto $\\frac{\\pi}{2}$."])
    p3 = paso_numero(ctx, "Calculá la integral:", "I =", valor, errs_v,
                     [f"$I = \\int{_lim(t1, t2)}\\int{_lim(r1, r2)} {correcta}$. Primero en $r$, después en $\\theta$."],
                     f"$\\int{_lim(t1, t2)}\\int{_lim(r1, r2)} {correcta} = {tex(valor)}$.", forzar_tipeo=True)
    e = Ejercicio(consigna, formula, [p1, p2, p3], grafico=graf)
    e.verificar = _verif_polar(fxy, reg)
    return e


def g_jefe8(ctx):
    v = ctx.rng.random()
    if v < 0.33:
        return g_doble_rect(ctx)
    if v < 0.66:
        return g_doble_tipo1(ctx)
    return g_polares(ctx)


# =============================================================== MUNDO 9: triples

_FUNCS_3 = [x * y * z, 2 * z, x * z, x + y + z, y**2, x * y + z, 8 * x * y * z, 3 * z**2]


def g_triple_caja(ctx):
    rng = ctx.rng
    a, b, c = rng.choice([1, 2]), rng.choice([1, 2, 3]), rng.choice([1, 2, 3])
    f = rng.choice(_FUNCS_3)
    valor = sp.integrate(f, (z, 0, c), (y, 0, b), (x, 0, a))
    formula = f"\\int_{{0}}^{{{a}}}\\int_{{0}}^{{{b}}}\\int_{{0}}^{{{c}}} {tex_par(f)}\\,dz\\,dy\\,dx"
    if ctx.jefe:
        return Ejercicio("Calculá la integral triple:", formula,
                         [paso_numero(ctx, "¿Cuánto da?", "I =", valor, [], [], "", forzar_tipeo=True)])
    p1, g1 = _paso_interior(ctx, f, z, 0, c, None)
    p2, g2 = _paso_interior(ctx, g1, y, 0, b, None)
    p2.pregunta = "Ahora la del medio (en $y$):"
    p3 = _paso_exterior(ctx, g2, x, 0, a, valor, prefijo="\\iiint_E f\\,dV =")
    return Ejercicio("Calculá la integral triple (de adentro hacia afuera):", formula, [p1, p2, p3])


def _verif_cart3(f, lims):
    """lims: [(z, z1(x,y), z2(x,y)), (y, y1(x), y2(x)), (x, a, b)] -> integral numérica."""
    (vz, z1, z2), (vy, y1, y2), (vx, a, b) = lims
    F = sp.lambdify((x, y, z), f, "mpmath")
    Z1, Z2 = sp.lambdify((x, y), z1, "mpmath"), sp.lambdify((x, y), z2, "mpmath")
    Y1, Y2 = sp.lambdify(x, y1, "mpmath"), sp.lambdify(x, y2, "mpmath")

    def calc():
        return mpmath.quad(lambda xx: mpmath.quad(
            lambda yy: mpmath.quad(lambda zz: F(xx, yy, zz), [Z1(xx, yy), Z2(xx, yy)]),
            [Y1(xx), Y2(xx)]), [float(a), float(b)])
    return calc


def g_triple_region(ctx):
    rng = ctx.rng
    k = rng.choice([1, 2, 3])
    if rng.random() < 0.6:
        f = rng.choice([sp.Integer(1), x, z, 2 * y, sp.Integer(6)])
        z2, y2 = k - x - y, k - x
        desc = f"E:\\ x \\geq 0,\\ y \\geq 0,\\ z \\geq 0,\\ x + y + z \\leq {k}"
        malas = [(f"0 \\leq z \\leq {k}", "limites_mal"), (f"0 \\leq z \\leq {tex(k - x)}", "limites_mal"),
                 (f"{tex(k - x - y)} \\leq z \\leq {k}", "limites_al_reves")]
        expl = f"Desde el piso $z = 0$ hasta el plano $x + y + z = {k}$, o sea $z = {tex(z2)}$."
    else:
        f = rng.choice([sp.Integer(1), x, 2 * z])
        z2, y2 = x + y, sp.Integer(k)
        desc = f"E:\\ 0 \\leq x \\leq {k},\\ 0 \\leq y \\leq {k},\\ 0 \\leq z \\leq x + y"
        malas = [(f"0 \\leq z \\leq {k}", "limites_mal"), (f"x + y \\leq z \\leq {2 * k}", "limites_al_reves"),
                 ("0 \\leq z \\leq x", "limites_mal")]
        expl = "Desde el piso $z = 0$ hasta el plano $z = x + y$."
    valor = sp.integrate(f, (z, 0, z2), (y, 0, y2), (x, 0, k))
    formula = f"\\iiint_E {tex_par(f)}\\,dV"
    consigna = f"Calculá, con ${desc}$:"
    if ctx.jefe:
        e = Ejercicio(consigna, formula, [paso_numero(ctx, "¿Cuánto da?", "I =", valor, [], [], "", forzar_tipeo=True)])
        e.verificar = _verif_cart3(f, [(z, 0, z2), (y, 0, y2), (x, 0, k)])
        return e
    p0 = paso_elegir(ctx, "¿Entre qué valores va la $z$?", f"0 \\leq z \\leq {tex(z2)}", malas, expl,
                     f"$0 \\leq z \\leq {tex(z2)}$",
                     pistas=["La $z$ va del «piso» al «techo» de la región.", "El techo es el plano: despejá $z$."])
    p1, g1 = _paso_interior(ctx, f, z, 0, z2, None)
    resto = f"Después: $y$ de $0$ a ${tex(y2)}$ y $x$ de $0$ a ${k}$."
    p2 = paso_numero(ctx, f"Terminá la cuenta. {resto}", "\\iiint_E f\\,dV =", valor, [(-valor, "barrow_orden")],
                     [resto, f"$\\int_0^{{{k}}}\\int_0^{{{tex(y2)}}} {tex_par(g1)}\\,dy\\,dx$."],
                     f"$\\int_0^{{{k}}}\\int_0^{{{tex(y2)}}} {tex_par(g1)}\\,dy\\,dx = {tex(valor)}$.",
                     forzar_tipeo=True)
    e = Ejercicio(consigna, formula, [p0, p1, p2])
    e.verificar = _verif_cart3(f, [(z, 0, z2), (y, 0, y2), (x, 0, k)])
    return e


def g_cilindricas(ctx):
    rng = ctx.rng
    a = rng.choice([1, 2, 3])
    forma = rng.choice(["cilindro", "paraboloide", "cono"])
    if forma == "cilindro":
        h = rng.choice([1, 2, 3, 4])
        z1, z2 = sp.Integer(0), sp.Integer(h)
        desc = f"E:\\ x^2 + y^2 \\leq {a**2},\\ 0 \\leq z \\leq {h}"
    elif forma == "paraboloide":
        z1, z2 = r**2, sp.Integer(a**2)
        desc = f"E:\\ x^2 + y^2 \\leq z \\leq {a**2}"
    else:
        z1, z2 = r, sp.Integer(a)
        desc = f"E:\\ \\sqrt{{x^2 + y^2}} \\leq z \\leq {a}"
    ftex, fxyz, fc = rng.choice([("1", sp.Integer(1), sp.Integer(1)), ("z", z, z),
                                 ("x^2 + y^2", x**2 + y**2, r**2)])
    valor = sp.simplify(sp.integrate(fc * r, (z, z1, z2), (r, 0, a), (t, 0, 2 * PI)))
    consigna = f"Pasá a cilíndricas y calculá, con ${desc}$:"
    formula = f"\\iiint_E {ftex}\\,dV"
    errs = [(sp.integrate(fc, (z, z1, z2), (r, 0, a), (t, 0, 2 * PI)), "jacobiano_cilindricas")]

    def verif():
        F = sp.lambdify((x, y, z), fxyz, "mpmath")
        Z1, Z2 = sp.lambdify(r, z1, "mpmath"), sp.lambdify(r, z2, "mpmath")
        return mpmath.quad(lambda tt, rr: mpmath.quad(lambda zz: F(rr * mpmath.cos(tt), rr * mpmath.sin(tt), zz) * rr,
                                                      [Z1(rr), Z2(rr)]), [0, 2 * mpmath.pi], [0, a])
    if ctx.jefe:
        e = Ejercicio(consigna, formula, [paso_numero(ctx, "¿Cuánto da?", "I =", valor, errs, [], "", forzar_tipeo=True)])
        e.verificar = verif
        return e
    p1 = paso_elegir(ctx, "En cilíndricas, ¿en qué se transforma $dx\\,dy\\,dz$?", "r\\,dz\\,dr\\,d\\theta",
                     [("dz\\,dr\\,d\\theta", "jacobiano_cilindricas"), ("r^{2}\\,dz\\,dr\\,d\\theta", "jacobiano_cilindricas"),
                      ("\\rho^{2}\\,\\mathrm{sen}\\,\\varphi\\;dz\\,dr\\,d\\theta", "jacobiano_cilindricas")],
                     "Cilíndricas son polares + $z$: el jacobiano sigue siendo $r$.", "$dV = r\\,dz\\,dr\\,d\\theta$",
                     pistas=["Es como polares, con la $z$ que queda igual."])
    p1.repetitivo = True
    zl = f"{tex(z1)} \\leq z \\leq {tex(z2)}"
    malas = [(f"{tex(z2)} \\leq z \\leq {tex(z1)}", "limites_al_reves"),
             ("r \\leq z \\leq " + tex(z2), "limites_mal"), ("r^{2} \\leq z \\leq " + tex(z2), "limites_mal"),
             (f"0 \\leq z \\leq {a**2}", "limites_mal"), (f"0 \\leq z \\leq {a}", "limites_mal"),
             (f"0 \\leq z \\leq {tex(2 * z2)}", "limites_mal")]
    p2 = paso_elegir(ctx, f"Con $0 \\leq r \\leq {a}$ y $0 \\leq \\theta \\leq 2\\pi$, ¿entre qué va la $z$?", zl, malas,
                     f"La $z$ va del piso al techo escritos en $r$: $x^2 + y^2 = r^2$ y $\\sqrt{{x^2+y^2}} = r$. Queda ${zl}$.",
                     f"${zl}$", pistas=["Reemplazá $x^2 + y^2$ por $r^2$ en las superficies."])
    fc_tex = "" if fc == 1 else tex(fc) + " \\cdot "
    integ = f"\\int_0^{{2\\pi}}\\int_0^{{{a}}}\\int_{{{tex(z1)}}}^{{{tex(z2)}}} {fc_tex}r\\,dz\\,dr\\,d\\theta"
    p3 = paso_numero(ctx, "Calculá la integral:", "I =", valor, errs, [f"$I = {integ}$. Primero $z$, después $r$, después $\\theta$."],
                     f"${integ} = {tex(valor)}$.", forzar_tipeo=True)
    e = Ejercicio(consigna, formula, [p1, p2, p3])
    e.verificar = verif
    return e


def g_esfericas(ctx):
    rng = ctx.rng
    a = rng.choice([1, 2, 3])
    medio = rng.random() < 0.5
    p2_ = PI / 2 if medio else PI
    desc = f"E:\\ x^2 + y^2 + z^2 \\leq {a**2}" + (",\\ z \\geq 0" if medio else "")
    opciones = [("1", sp.Integer(1), sp.Integer(1)), ("x^2 + y^2 + z^2", x**2 + y**2 + z**2, r**2),
                ("\\sqrt{x^2 + y^2 + z^2}", sp.sqrt(x**2 + y**2 + z**2), r)]
    if medio:
        opciones.append(("z", z, r * sp.cos(p)))
    ftex, fxyz, fe = rng.choice(opciones)
    jac = r**2 * sp.sin(p)
    valor = sp.simplify(sp.integrate(fe * jac, (r, 0, a), (p, 0, p2_), (t, 0, 2 * PI)))
    consigna = f"Pasá a esféricas y calculá, con ${desc}$:"
    formula = f"\\iiint_E {ftex}\\,dV"
    errs = [(sp.integrate(fe * r**2, (r, 0, a), (p, 0, p2_), (t, 0, 2 * PI)), "jacobiano_esfericas"),
            (sp.integrate(fe, (r, 0, a), (p, 0, p2_), (t, 0, 2 * PI)), "jacobiano_esfericas")]

    def verif():
        F = sp.lambdify((x, y, z), fxyz, "mpmath")
        return mpmath.quad(lambda tt, pp, rr: F(rr * mpmath.sin(pp) * mpmath.cos(tt), rr * mpmath.sin(pp) * mpmath.sin(tt),
                                                 rr * mpmath.cos(pp)) * rr**2 * mpmath.sin(pp),
                           [0, 2 * mpmath.pi], [0, float(p2_)], [0, a])
    if ctx.jefe:
        e = Ejercicio(consigna, formula, [paso_numero(ctx, "¿Cuánto da?", "I =", valor, errs, [], "", forzar_tipeo=True)])
        e.verificar = verif
        return e
    p1 = paso_elegir(ctx, "En esféricas, ¿en qué se transforma $dx\\,dy\\,dz$?",
                     "\\rho^{2}\\,\\mathrm{sen}\\,\\varphi\\;d\\rho\\,d\\varphi\\,d\\theta",
                     [("\\rho\\,d\\rho\\,d\\varphi\\,d\\theta", "jacobiano_esfericas"),
                      ("\\rho^{2}\\,d\\rho\\,d\\varphi\\,d\\theta", "jacobiano_esfericas"),
                      ("\\rho^{2}\\cos\\varphi\\;d\\rho\\,d\\varphi\\,d\\theta", "jacobiano_esfericas")],
                     "El jacobiano de esféricas es $\\rho^2\\,\\mathrm{sen}\\,\\varphi$.",
                     "$dV = \\rho^2\\,\\mathrm{sen}\\,\\varphi\\;d\\rho\\,d\\varphi\\,d\\theta$",
                     pistas=["Es $\\rho$ al cuadrado por el seno del ángulo que se mide desde el eje $z$."])

    p1.repetitivo = True
    def lims(rmax, pmax, tmax):
        return f"0 \\leq \\rho \\leq {tex(rmax)},\\ 0 \\leq \\varphi \\leq {tex(pmax)},\\ 0 \\leq \\theta \\leq {tex(tmax)}"
    otro_p = PI if medio else PI / 2
    malas = [(lims(a, otro_p, 2 * PI), "phi_mal"), (lims(a, p2_, PI), "angulo_mal"),
             (lims(a**2, p2_, 2 * PI), "radio_mal"), (lims(a, 2 * PI, PI), "phi_mal")]
    correcta = lims(a, p2_, 2 * PI)
    p2 = paso_elegir(ctx, "¿Qué límites tienen $\\rho$, $\\varphi$ y $\\theta$?", correcta, malas,
                     "$\\varphi$ se mide desde el eje $z$: va hasta $\\pi$ en la esfera entera y hasta $\\frac{\\pi}{2}$ "
                     "si es solo la mitad de arriba. $\\theta$ da toda la vuelta.", f"${correcta}$",
                     pistas=["$\\rho$ es la distancia al origen: va de 0 al radio.", "Mitad de arriba ($z \\geq 0$): $\\varphi$ hasta $\\frac{\\pi}{2}$."])
    fe_tex = "" if fe == 1 else tex(fe).replace("r", "\\rho").replace("\\phi", "\\varphi") + " \\cdot "
    integ = (f"\\int_0^{{2\\pi}}\\int_0^{{{tex(p2_)}}}\\int_0^{{{a}}} {fe_tex}"
             "\\rho^{2}\\,\\mathrm{sen}\\,\\varphi\\;d\\rho\\,d\\varphi\\,d\\theta")
    p3 = paso_numero(ctx, "Calculá la integral:", "I =", valor, errs,
                     [f"$I = {integ}$.", "Las tres integrales se separan: una en $\\rho$, una en $\\varphi$ y una en $\\theta$."],
                     f"${integ} = {tex(valor)}$.", forzar_tipeo=True)
    e = Ejercicio(consigna, formula, [p1, p2, p3])
    e.verificar = verif
    return e


def g_jefe9(ctx):
    v = ctx.rng.random()
    if v < 0.25:
        return g_triple_caja(ctx)
    if v < 0.5:
        return g_triple_region(ctx)
    if v < 0.75:
        return g_cilindricas(ctx)
    return g_esfericas(ctx)


GENERADORES_V3 = [g_doble_rect, g_doble_tipo1, g_cambio_orden, g_polares, g_jefe8,
                  g_triple_caja, g_triple_region, g_cilindricas, g_esfericas, g_jefe9]
