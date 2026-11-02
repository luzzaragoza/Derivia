"""Generadores de ejercicios y definición de los mundos y niveles.

Cada ejercicio se arma con números al azar a partir de una semilla, así se
puede volver a generar idéntico (para el cuaderno de errores)."""

from dataclasses import dataclass, field

import sympy as sp

from .mate import equivalentes, tex, tex_base, tex_par, x

E = sp.exp
SEN = sp.sin
COS = sp.cos
LN = sp.log
RAIZ = sp.sqrt
R = sp.Rational


# ======================================================== estructuras

@dataclass
class Opcion:
    tex: str = ""            # fórmula (LaTeX sin $)
    texto: str = ""          # o texto común (con $...$ adentro si hace falta)
    correcta: bool = False
    error: str | None = None  # código de error si la elige


@dataclass
class Paso:
    pregunta: str
    tipo: str                               # "opcion" | "expresion"
    opciones: list = field(default_factory=list)
    esperado: object = None
    errores: list = field(default_factory=list)   # [(expr, codigo)]
    original: object = None                 # para detectar "no derivaste"
    prefijo: str = ""                       # LaTeX antes del cuadro, ej. f'(x) =
    pistas: list = field(default_factory=list)
    explicacion: str = ""                   # se muestra al acertar o al revelar
    resumen: str = ""                       # renglón en la lista de pasos hechos
    max_intentos: int = 2
    mostrar: str = ""                       # la respuesta como en el pizarrón (LaTeX)
    chequeo: str = "igual"                  # "igual" | "primitiva" | "numero"
    var: object = None                      # variable respecto de la que se deriva/integra
    variables: tuple = (x,)                 # letras que se pueden tipear
    integrando: object = None               # para chequeo "primitiva"


@dataclass
class Ejercicio:
    consigna: str
    formula: str             # LaTeX grande del enunciado
    pasos: list
    clave: dict = field(default_factory=dict)
    grafico: dict | None = None   # dibujo de la región (integrales dobles)


class Ctx:
    """Contexto que recibe cada generador."""

    def __init__(self, rng, modo, jefe=False, dificultad=1):
        self.rng = rng
        self.modo = modo          # "opciones" | "tipeo"
        self.jefe = jefe
        self.dificultad = dificultad


# ======================================================== helpers

def _coef(rng, maxi=6, negativos=True, uno=True):
    vals = [k for k in range(1 if uno else 2, maxi + 1)]
    if negativos:
        vals += [-k for k in range(1 if uno else 2, maxi)]
    return rng.choice(vals)


def _num_tex(a):
    """Coeficiente delante de algo: 1 -> '', -1 -> '-', 3 -> '3'."""
    if a == 1:
        return ""
    if a == -1:
        return "-"
    return tex(a)


def _distintos(esperado, candidatos, cuantos, iguales=equivalentes):
    """Filtra candidatos que sean distintos entre sí y del correcto."""
    elegidos = []
    for expr, codigo in candidatos:
        expr = sp.sympify(expr)
        if iguales(expr, esperado):
            continue
        if any(iguales(expr, e) for e, _ in elegidos):
            continue
        elegidos.append((expr, codigo))
        if len(elegidos) == cuantos:
            break
    return elegidos


def errores_validos(esperado, candidatos):
    """Saca los 'errores' que en realidad dan bien (pasa con algunos números)."""
    return [(sp.sympify(e), c) for e, c in candidatos if not equivalentes(e, esperado)]


def paso_derivada(ctx, pregunta, prefijo, esperado, errores, pistas, explicacion,
                  original=None, resumen_prefijo=None, forzar_tipeo=False, mostrar=None,
                  var=x, variables=(x,)):
    """Paso cuya respuesta es una expresión: se tipea o se elige según el modo.
    `mostrar` es la respuesta escrita como en el pizarrón (sin que SymPy la reordene)."""
    errores = errores_validos(esperado, errores)
    resumen = f"${resumen_prefijo or prefijo} {mostrar or tex(esperado)}$"
    if ctx.modo == "opciones" and not forzar_tipeo:
        relleno = [(-esperado, "signo_general"), (2 * esperado, "factor_constante"),
                   (esperado + 1, "constante_de_mas"), (esperado * x, "factor_constante")]
        malos = _distintos(esperado, errores + relleno, 3)
        ops = [Opcion(tex=tex(esperado), correcta=True)]
        ops += [Opcion(tex=tex(e), error=c) for e, c in malos]
        ctx.rng.shuffle(ops)
        return Paso(pregunta=pregunta, tipo="opcion", opciones=ops, esperado=esperado,
                    prefijo=prefijo, pistas=pistas, explicacion=explicacion, resumen=resumen,
                    original=original, var=var, variables=variables)
    return Paso(pregunta=pregunta, tipo="expresion", esperado=esperado, errores=errores,
                original=original, prefijo=prefijo, pistas=pistas,
                explicacion=explicacion, resumen=resumen, mostrar=mostrar or "",
                var=var, variables=variables)


def _misma_primitiva(var):
    def iguales(a, b):
        return equivalentes(sp.diff(a, var), sp.diff(b, var))
    return iguales


def paso_primitiva(ctx, pregunta, prefijo, primitiva, integrando, errores, pistas, explicacion,
                   var=x, variables=(x,), mostrar=None, forzar_tipeo=False):
    """Integral indefinida: se acepta cualquier F con F' = integrando (con o sin + C)."""
    iguales = _misma_primitiva(var)
    errores = [(sp.sympify(e), c) for e, c in errores if not iguales(e, primitiva)]
    resumen = f"${prefijo} {mostrar or tex(primitiva)} + C$"
    if ctx.modo == "opciones" and not forzar_tipeo:
        relleno = [(sp.diff(integrando, var), "integral_derivaste"), (-primitiva, "integral_signo"),
                   (2 * primitiva, "integral_factor"), (primitiva * var, "integral_factor")]
        malos = _distintos(primitiva, errores + relleno, 3, iguales)
        ops = [Opcion(tex=f"{tex(primitiva)} + C", correcta=True)]
        ops += [Opcion(tex=f"{tex(e)} + C", error=c) for e, c in malos]
        ctx.rng.shuffle(ops)
        return Paso(pregunta=pregunta, tipo="opcion", opciones=ops, esperado=primitiva, prefijo=prefijo,
                    pistas=pistas, explicacion=explicacion, resumen=resumen, chequeo="primitiva",
                    var=var, variables=variables, integrando=integrando, mostrar=mostrar or "")
    return Paso(pregunta=pregunta, tipo="expresion", esperado=primitiva, errores=errores, prefijo=prefijo,
                pistas=pistas, explicacion=explicacion, resumen=resumen, mostrar=mostrar or "",
                chequeo="primitiva", var=var, variables=variables, integrando=integrando)


def paso_numero(ctx, pregunta, prefijo, valor, errores, pistas, explicacion, mostrar=None,
                forzar_tipeo=False):
    """La respuesta es un número (puede tener pi, e, fracciones, raíces)."""
    valor = sp.nsimplify(valor) if isinstance(valor, float) else sp.sympify(valor)
    errores = [(sp.sympify(e), c) for e, c in errores if not equivalentes(e, valor)]
    resumen = f"${prefijo} {mostrar or tex(valor)}$"
    if ctx.modo == "opciones" and not forzar_tipeo:
        relleno = [(-valor, "signo_general"), (2 * valor, "factor_constante"),
                   (valor / 2, "factor_constante"), (valor + 1, "constante_de_mas")]
        malos = _distintos(valor, errores + relleno, 3)
        ops = [Opcion(tex=tex(valor), correcta=True)] + [Opcion(tex=tex(e), error=c) for e, c in malos]
        ctx.rng.shuffle(ops)
        return Paso(pregunta=pregunta, tipo="opcion", opciones=ops, esperado=valor, prefijo=prefijo,
                    pistas=pistas, explicacion=explicacion, resumen=resumen, chequeo="numero", variables=())
    return Paso(pregunta=pregunta, tipo="expresion", esperado=valor, errores=errores, prefijo=prefijo,
                pistas=pistas, explicacion=explicacion, resumen=resumen, mostrar=mostrar or "",
                chequeo="numero", variables=())


def paso_elegir(ctx, pregunta, correcta, malas, explicacion, resumen, pistas=(), es_tex=True):
    """Opción múltiple genérica. correcta: str; malas: [(str, codigo_error)]."""
    ops = [Opcion(tex=correcta, correcta=True) if es_tex else Opcion(texto=correcta, correcta=True)]
    vistos = {correcta}
    for t, cod in malas:
        if t in vistos:
            continue
        vistos.add(t)
        ops.append(Opcion(tex=t, error=cod) if es_tex else Opcion(texto=t, error=cod))
        if len(ops) == 4:
            break
    ctx.rng.shuffle(ops)
    return Paso(pregunta=pregunta, tipo="opcion", opciones=ops, explicacion=explicacion,
                resumen=resumen, pistas=list(pistas))


REGLAS = {
    "tabla": "Tabla (derivada directa)",
    "producto": "Regla del producto",
    "cociente": "Regla del cociente",
    "cadena": "Regla de la cadena",
}


def paso_regla(ctx, correcta, explicacion, pregunta="¿Qué regla usás **primero**?"):
    ops = []
    for clave, nombre in REGLAS.items():
        ops.append(Opcion(texto=nombre, correcta=(clave == correcta),
                          error=None if clave == correcta else f"regla_{correcta}"))
    return Paso(pregunta=pregunta, tipo="opcion", opciones=ops, explicacion=explicacion,
                resumen=f"Regla: {REGLAS[correcta].lower()}", max_intentos=2)


# ======================================================== MUNDO 1: básicas

@dataclass
class Termino:
    expr: object
    d: object
    malos: list         # [(derivada mal hecha, codigo)]
    pista: str


def t_potencia(rng, a=None, n=None):
    a = a if a is not None else _coef(rng)
    n = n if n is not None else rng.randint(2, 6)
    return Termino(a * x**n, a * n * x**(n - 1),
                   [(a * n * x**n, "potencia_no_resta"), (a * x**(n - 1), "potencia_no_baja"),
                    (a * n * x**(n + 1), "potencia_suma")],
                   f"$(x^{{{n}}})' = {n}\\,x^{{{n - 1}}}$")


def t_lineal(rng):
    a = _coef(rng, uno=False)
    return Termino(a * x, sp.Integer(a), [(a * x, "no_derivaste_termino")], "$(a\\,x)' = a$")


def t_constante(rng):
    c = rng.choice([1, 2, 3, 4, 5, 7, 8, 9, -1, -2, -3, -4, -5, -7])
    return Termino(sp.Integer(c), sp.Integer(0), [(sp.Integer(c), "constante_no_cero")],
                   "las constantes solas se derivan a 0")


def t_sen(rng):
    a = _coef(rng)
    return Termino(a * SEN(x), a * COS(x), [(-a * COS(x), "signo_sen")],
                   "$(\\mathrm{sen}\\,x)' = \\cos x$")


def t_cos(rng):
    a = _coef(rng)
    return Termino(a * COS(x), -a * SEN(x), [(a * SEN(x), "signo_cos")],
                   "$(\\cos x)' = -\\mathrm{sen}\\,x$")


def t_exp(rng):
    a = _coef(rng)
    return Termino(a * E(x), a * E(x), [(a * x * E(x - 1), "exp_como_potencia")],
                   "$(e^x)' = e^x$")


def t_ln(rng):
    a = _coef(rng)
    return Termino(a * LN(x), a / x, [(a / LN(x), "ln_derivada"), (a * E(x), "ln_derivada")],
                   "$(\\ln x)' = \\frac{1}{x}$")


TABLA = [t_sen, t_cos, t_exp, t_ln]


def _ejercicio_suma(ctx, terminos, consigna="Derivá la función:"):
    f = sum(t.expr for t in terminos)
    d = sum(t.d for t in terminos)
    errores = []
    for i, t in enumerate(terminos):
        resto = sum(u.d for j, u in enumerate(terminos) if j != i)
        for malo, codigo in t.malos:
            errores.append((resto + malo, codigo))
    pistas_regla = sorted({t.pista for t in terminos})
    pistas = []
    if len(terminos) > 1:
        pistas.append("La derivada de una suma es la suma de las derivadas: derivá **cada término por separado**.")
    pistas.append("Acordate: " + ",  ".join(pistas_regla) + ".")
    pistas.append("Los números que multiplican quedan multiplicando: $(k\\,f)' = k\\,f'$.")
    partes = [f"$({tex(t.expr)})' = {tex(t.d)}$" for t in terminos]
    explicacion = "Término a término: " + ",  ".join(partes) + "."
    paso = paso_derivada(ctx, "¿Cuánto da la derivada?", "f'(x) =", d, errores, pistas,
                         explicacion, original=f)
    return Ejercicio(consigna, f"f(x) = {tex(f)}", [paso])


def g_potencia(ctx):
    return _ejercicio_suma(ctx, [t_potencia(ctx.rng)])


def g_tabla(ctx):
    rng = ctx.rng
    terminos = [rng.choice(TABLA)(rng)]
    if rng.random() < 0.5:
        terminos.append(t_potencia(rng))
    rng.shuffle(terminos)
    return _ejercicio_suma(ctx, terminos)


def g_sumas(ctx):
    rng = ctx.rng
    # 2 o 3 términos (no más: alarga sin enseñar nada nuevo)
    terminos = [t_potencia(rng), rng.choice(TABLA)(rng)]
    if rng.random() < 0.35:
        terminos.append(rng.choice([t_constante, t_lineal])(rng))
    rng.shuffle(terminos)
    return _ejercicio_suma(ctx, terminos)


# raíces y potencias negativas: primero reescribir, después derivar
_FORMAS = [
    (R(1, 2), "\\sqrt{x}"), (R(1, 3), "\\sqrt[3]{x}"), (sp.Integer(-1), "\\frac{1}{x}"),
    (sp.Integer(-2), "\\frac{1}{x^{2}}"), (sp.Integer(-3), "\\frac{1}{x^{3}}"),
    (R(-1, 2), "\\frac{1}{\\sqrt{x}}"), (R(3, 2), "x\\sqrt{x}"), (R(2, 3), "\\sqrt[3]{x^{2}}"),
]


def _forma_tex(a, forma):
    if forma.startswith("\\frac{1}"):
        if a < 0:
            return "-" + forma.replace("\\frac{1}", f"\\frac{{{-a}}}", 1)
        return forma.replace("\\frac{1}", f"\\frac{{{a}}}", 1)
    return _num_tex(a) + forma


def _pot_tex(a, p):
    return f"{_num_tex(a)}x^{{{tex(p)}}}"


def g_raices(ctx):
    rng = ctx.rng
    p, forma = rng.choice(_FORMAS)
    a = rng.choice([1, 2, 3, 4, 5, 6, -2, -3])
    f = a * x**p
    # paso 1: reescribir
    cands = [(-p, "reescritura_signo"), (p + 1, "reescritura_raiz"), (p - 1, "reescritura_raiz")]
    if p.q != 1:
        cands.insert(0, (1 / p, "reescritura_raiz"))
    vistos = {p}
    ops = [Opcion(tex=_pot_tex(a, p), correcta=True)]
    for q, cod in cands:
        if q in vistos or q == 0:
            continue
        vistos.add(q)
        ops.append(Opcion(tex=_pot_tex(a, q), error=cod))
        if len(ops) == 4:
            break
    rng.shuffle(ops)
    paso1 = Paso(
        pregunta="Primero escribila como **potencia** de $x$:",
        tipo="opcion", opciones=ops,
        explicacion="Las raíces son exponentes fraccionarios ($\\sqrt{x} = x^{1/2}$) y lo que está abajo sube con exponente negativo ($\\frac{1}{x^n} = x^{-n}$).",
        resumen=f"$f(x) = {_pot_tex(a, p)}$",
    )
    d = a * p * x**(p - 1)
    errores = [(a * p * x**p, "potencia_no_resta"), (a * x**(p - 1), "potencia_no_baja"),
               (a * p * x**(p + 1), "potencia_negativa" if p < 0 else "potencia_suma"),
               (-a * p * x**(p - 1), "potencia_negativa_signo" if p < 0 else "signo_general")]
    if p == R(1, 2):
        errores.append((a / RAIZ(x), "raiz_sin_2"))
    pistas = ["Ahora usá la regla de la potencia: $(x^n)' = n\\,x^{n-1}$, aunque $n$ sea fracción o negativo.",
              f"El exponente ${tex(p)}$ baja multiplicando. El nuevo exponente es ${tex(p)} - 1 = {tex(p - 1)}$."]
    explicacion = (f"$({_pot_tex(a, p)})' = {tex(a)}\\cdot {tex_par(p)}\\,x^{{{tex(p)}-1}} = {tex(d)}$. "
                   "Podés dejarla con exponente negativo o fraccionario: también vale.")
    paso2 = paso_derivada(ctx, "Ahora derivala:", "f'(x) =", d, errores, pistas, explicacion,
                          original=f, forzar_tipeo=True)
    return Ejercicio("Derivá la función:", f"f(x) = {_forma_tex(a, forma)}", [paso1, paso2])


def g_jefe1(ctx):
    rng = ctx.rng
    p, _ = rng.choice(_FORMAS[:6])
    a = rng.choice([1, 2, 3, -2, 4])
    t_raiz = Termino(a * x**p, a * p * x**(p - 1),
                     [(a * p * x**p, "potencia_no_resta"), (a * x**(p - 1), "potencia_no_baja")],
                     "$(x^n)' = n\\,x^{n-1}$")
    terminos = [t_raiz, rng.choice(TABLA)(rng)]
    if rng.random() < 0.5:
        terminos.append(t_potencia(rng))
    rng.shuffle(terminos)
    return _ejercicio_suma(ctx, terminos)


# ======================================================== MUNDO 2: producto y cociente

def _pieza(rng, tipo):
    """(expr, derivada, malas_derivadas)"""
    if tipo == "pot":
        a = rng.choice([1, 1, 2, 3, 4, 5])
        n = rng.randint(1, 4)
        return a * x**n, a * n * x**(n - 1), [(a * n * x**n, "potencia_no_resta")]
    if tipo == "poly":
        n = rng.choice([1, 2, 2, 3])
        a = rng.choice([1, 1, 2, 3])
        b = rng.choice([1, 2, 3, 4, 5, -1, -2, -3])
        return a * x**n + b, a * n * x**(n - 1), [(a * n * x**(n - 1) + b, "constante_no_cero")]
    if tipo == "sen":
        return SEN(x), COS(x), [(-COS(x), "signo_sen")]
    if tipo == "cos":
        return COS(x), -SEN(x), [(SEN(x), "signo_cos")]
    if tipo == "exp":
        return E(x), E(x), [(x * E(x - 1), "exp_como_potencia")]
    if tipo == "ln":
        return LN(x), 1 / x, [(1 / LN(x), "ln_derivada")]
    raise ValueError(tipo)


_TRASC = ["sen", "cos", "exp", "ln"]


def _par_producto(rng):
    if rng.random() < 0.75:
        a, b = rng.choice(["pot", "poly"]), rng.choice(_TRASC)
    else:
        a, b = rng.sample(_TRASC, 2)
    return a, b


def _par_cociente(rng):
    opciones = [("pot", "poly"), ("sen", "pot"), ("exp", "pot"), ("ln", "pot"), ("pot", "exp"),
                ("poly", "exp"), ("sen", "poly"), ("pot", "ln"), ("cos", "pot"), ("exp", "poly"),
                ("poly", "pot"), ("pot", "sen"), ("pot", "cos")]
    return rng.choice(opciones)


def _uv(rng, par):
    u, du, mu = _pieza(rng, par[0])
    v, dv, mv = _pieza(rng, par[1])
    if par == ("pot", "poly") or par == ("poly", "pot"):
        # evitar que se simplifique (x / x)
        if sp.simplify(u / v).is_polynomial(x) or sp.simplify(v / u).is_polynomial(x):
            v = x**2 + 1
            dv = 2 * x
            mv = [(2 * x + 1, "constante_no_cero")]
    return u, du, mu, v, dv, mv


def _errores_producto(u, du, mu, v, dv, mv):
    errs = [(du * dv, "producto_derivadas"), (du * v, "producto_falta_termino"),
            (u * dv, "producto_falta_termino"), (du * v - u * dv, "producto_signo")]
    for m, c in mu:
        errs.append((m * v + u * dv, c))
    for m, c in mv:
        errs.append((du * v + u * m, c))
    return errs


def _errores_cociente(u, du, mu, v, dv, mv):
    errs = [((du * v + u * dv) / v**2, "cociente_signo_mas"), ((u * dv - du * v) / v**2, "cociente_orden"),
            ((du * v - u * dv) / v, "cociente_sin_cuadrado"), (du / dv, "cociente_derivadas")]
    for m, c in mu:
        errs.append(((m * v - u * dv) / v**2, c))
    for m, c in mv:
        errs.append(((du * v - u * m) / v**2, c))
    return errs


def _prod_tex(u, v):
    return f"{tex_par(u)} \\cdot {tex_par(v)}"


def _coc_tex(u, v):
    return f"\\frac{{{tex(u)}}}{{{tex(v)}}}"


def g_producto(ctx):
    rng = ctx.rng
    u, du, mu, v, dv, mv = _uv(rng, _par_producto(rng))
    d = du * v + u * dv
    errs = _errores_producto(u, du, mu, v, dv, mv)
    pizarron = f"{tex_par(du)}\\cdot {tex_par(v)} + {tex_par(u)}\\cdot {tex_par(dv)}"
    expl = f"$(u\\cdot v)' = u'\\,v + u\\,v'$ con $u = {tex(u)}$, $v = {tex(v)}$."
    pistas = ["Regla del producto: $(u\\cdot v)' = u'\\,v + u\\,v'$.",
              f"Acá $u = {tex(u)}$ y $v = {tex(v)}$. Derivá cada una por separado."]
    f = u * v
    if ctx.modo == "opciones":
        pasos = [paso_regla(ctx, "producto", "Son dos funciones de $x$ multiplicándose."),
                 paso_derivada(ctx, "¿Cuánto da la derivada?", "f'(x) =", d, errs, pistas, expl, original=f, mostrar=pizarron)]
    elif ctx.jefe:
        pasos = [paso_derivada(ctx, "¿Cuánto da la derivada?", "f'(x) =", d, errs, [], expl, original=f, mostrar=pizarron)]
    else:
        pasos = [
            paso_derivada(ctx, f"Llamemos $u = {tex(u)}$ y $v = {tex(v)}$. Primero: ¿cuánto es $u'$?",
                          "u' =", du, mu, [f"Derivá solo $u = {tex(u)}$."], "", original=u),
            paso_derivada(ctx, f"Ahora derivá $v = {tex(v)}$:", "v' =", dv, mv,
                          [f"Derivá solo $v = {tex(v)}$."], "", original=v),
            paso_derivada(ctx, "Armá la derivada con $(u\\cdot v)' = u'\\,v + u\\,v'$:", "f'(x) =", d, errs,
                          pistas, expl, original=f, mostrar=pizarron),
        ]
    return Ejercicio("Derivá la función:", f"f(x) = {_prod_tex(u, v)}", pasos)


def g_cociente(ctx):
    rng = ctx.rng
    u, du, mu, v, dv, mv = _uv(rng, _par_cociente(rng))
    d = (du * v - u * dv) / v**2
    errs = _errores_cociente(u, du, mu, v, dv, mv)
    pizarron = (f"\\frac{{{tex_par(du)}\\cdot {tex_par(v)} - {tex_par(u)}\\cdot {tex_par(dv)}}}"
                f"{{{tex_base(v)}^2}}")
    expl = (f"$\\left(\\frac{{u}}{{v}}\\right)' = \\frac{{u'\\,v - u\\,v'}}{{v^2}}$ "
            f"con $u = {tex(u)}$ (arriba) y $v = {tex(v)}$ (abajo).")
    pistas = ["Regla del cociente: $\\left(\\frac{u}{v}\\right)' = \\frac{u'\\,v - u\\,v'}{v^2}$. Primero va la derivada de arriba.",
              f"Acá $u = {tex(u)}$ (arriba) y $v = {tex(v)}$ (abajo)."]
    f = u / v
    if ctx.modo == "opciones":
        pasos = [paso_regla(ctx, "cociente", "Es una función de $x$ dividida por otra."),
                 paso_derivada(ctx, "¿Cuánto da la derivada?", "f'(x) =", d, errs, pistas, expl, original=f, mostrar=pizarron)]
    elif ctx.jefe:
        pasos = [paso_derivada(ctx, "¿Cuánto da la derivada?", "f'(x) =", d, errs, [], expl, original=f, mostrar=pizarron)]
    else:
        pasos = [
            paso_derivada(ctx, f"Llamemos $u = {tex(u)}$ (arriba) y $v = {tex(v)}$ (abajo). ¿Cuánto es $u'$?",
                          "u' =", du, mu, [f"Derivá solo $u = {tex(u)}$."], "", original=u),
            paso_derivada(ctx, f"Ahora derivá $v = {tex(v)}$:", "v' =", dv, mv,
                          [f"Derivá solo $v = {tex(v)}$."], "", original=v),
            paso_derivada(ctx, "Armá la derivada con $\\frac{u'\\,v - u\\,v'}{v^2}$:", "f'(x) =", d, errs,
                          pistas, expl, original=f, mostrar=pizarron),
        ]
    return Ejercicio("Derivá la función:", f"f(x) = {_coc_tex(u, v)}", pasos)


def g_jefe2(ctx):
    return (g_producto if ctx.rng.random() < 0.5 else g_cociente)(ctx)


# ======================================================== MUNDO 3: cadena

class Afuera:
    """Función de afuera F(u): sabe derivarse y equivocarse."""

    def __init__(self, nombre, F, dF, tex_u, regla, malos):
        self.nombre, self.F, self.dF, self.tex_u, self.regla, self.malos = nombre, F, dF, tex_u, regla, malos


def _afuera(rng, nombre):
    if nombre == "pot":
        n = rng.randint(2, 5)
        return Afuera(f"pot{n}", lambda u: u**n, lambda u: n * u**(n - 1),
                      lambda t: f"({t})^{{{n}}}", f"$(u^{{{n}}})' = {n}\\,u^{{{n - 1}}}\\cdot u'$",
                      lambda u, du: [(n * u**(n - 1), "cadena_sin_interior"),
                                     (n * u**n * du, "potencia_no_resta"),
                                     (n * du**(n - 1), "cadena_evaluar_derivada"),
                                     (n * x**(n - 1) * du, "cadena_afuera_en_x")])
    if nombre == "sen":
        return Afuera("sen", SEN, COS, lambda t: f"\\mathrm{{sen}}({t})",
                      "$(\\mathrm{sen}\\,u)' = \\cos u\\cdot u'$",
                      lambda u, du: [(COS(u), "cadena_sin_interior"), (-COS(u) * du, "signo_sen"),
                                     (COS(du), "cadena_evaluar_derivada"), (COS(x) * du, "cadena_afuera_en_x")])
    if nombre == "cos":
        return Afuera("cos", COS, lambda u: -SEN(u), lambda t: f"\\cos({t})",
                      "$(\\cos u)' = -\\mathrm{sen}\\,u\\cdot u'$",
                      lambda u, du: [(-SEN(u), "cadena_sin_interior"), (SEN(u) * du, "signo_cos"),
                                     (-SEN(du), "cadena_evaluar_derivada"), (-SEN(x) * du, "cadena_afuera_en_x")])
    if nombre == "exp":
        return Afuera("exp", E, E, lambda t: f"e^{{{t}}}", "$(e^u)' = e^u\\cdot u'$",
                      lambda u, du: [(E(u), "cadena_sin_interior"), (u * E(u - 1), "exp_como_potencia"),
                                     (E(du), "cadena_evaluar_derivada"), (E(x) * du, "cadena_afuera_en_x")])
    if nombre == "ln":
        return Afuera("ln", LN, lambda u: 1 / u, lambda t: f"\\ln({t})", "$(\\ln u)' = \\frac{1}{u}\\cdot u'$",
                      lambda u, du: [(1 / u, "cadena_sin_interior"), (1 / du, "cadena_evaluar_derivada"),
                                     (du / x, "cadena_afuera_en_x"), (u / du, "cadena_evaluar_derivada")])
    if nombre == "raiz":
        return Afuera("raiz", RAIZ, lambda u: 1 / (2 * RAIZ(u)), lambda t: f"\\sqrt{{{t}}}",
                      "$(\\sqrt{u})' = \\frac{1}{2\\sqrt{u}}\\cdot u'$",
                      lambda u, du: [(1 / (2 * RAIZ(u)), "cadena_sin_interior"), (du / RAIZ(u), "raiz_sin_2"),
                                     (1 / (2 * RAIZ(du)), "cadena_evaluar_derivada")])
    raise ValueError(nombre)


def _adentro_poly(rng):
    while True:
        n = rng.choice([1, 2, 2, 3])
        a = rng.choice([1, 2, 3, 4, 5, -1, -2]) if n > 1 else rng.choice([2, 3, 4, 5, -2, -3])
        b = rng.choice([0, 1, 2, 3, 5, -1, -3, -4]) if n > 1 else rng.choice([0, 0, 1, 2, -1, -5])
        if n == 1 and b == 0 and abs(a) == 1:
            continue
        if n > 1 and b == 0 and rng.random() < 0.5:
            continue
        return a * x**n + b, a * n * x**(n - 1)


def _adentro_trasc(rng):
    return rng.choice([(SEN(x), COS(x)), (COS(x), -SEN(x)), (E(x), E(x)), (LN(x), 1 / x)])


def _tex_compuesta(af, u):
    """Cómo se ve F(u) escrita a mano (sen²(x) en vez de (sen x)²)."""
    if af.nombre.startswith("pot") and not u.is_Add:
        return tex(af.F(u))
    if af.nombre == "exp":
        return f"e^{{{tex(u)}}}"
    if af.nombre in ("sen", "cos", "ln"):
        return tex(af.F(u))
    if af.nombre == "raiz":
        return f"\\sqrt{{{tex(u)}}}"
    return af.tex_u(tex(u))


def _paso_adentro(ctx, f, u, af):
    rng = ctx.rng
    ops = [Opcion(tex=f"u = {tex(u)}", correcta=True),
           Opcion(tex=f"u = {tex(f)}", error="adentro_todo")]
    usados = {sp.srepr(u), sp.srepr(f)}
    if u.is_Add:
        parte = max(u.args, key=lambda t: sp.degree(t, x) if t.is_polynomial(x) else 0)
        if sp.srepr(parte) not in usados:
            ops.append(Opcion(tex=f"u = {tex(parte)}", error="adentro_parte"))
            usados.add(sp.srepr(parte))
    if sp.srepr(x) not in usados:
        ops.append(Opcion(tex="u = x", error="adentro_x"))
    if len(ops) < 4:
        g = af.F(x)
        if sp.srepr(g) not in usados:
            ops.append(Opcion(tex=f"u = {tex(g)}", error="adentro_x"))
    ops = ops[:4]
    rng.shuffle(ops)
    return Paso(pregunta="¿Cuál es la función **de adentro** ($u$)?", tipo="opcion", opciones=ops,
                explicacion=f"La de adentro es $u = {tex(u)}$: está metida dentro de la otra función.",
                resumen=f"$u = {tex(u)}$")


def _cadena(ctx, nombres_afuera, adentro):
    rng = ctx.rng
    while True:
        af = _afuera(rng, rng.choice(nombres_afuera))
        u, du = adentro(rng)
        if af.nombre == "exp" and u.func == LN or af.nombre == "ln" and u.func == E:
            continue
        if af.nombre in ("ln", "raiz") and u.is_polynomial(x) and any(c < 0 for c in sp.Poly(u, x).coeffs()):
            continue  # nada de ln o raíz de cosas negativas
        f = af.F(u)
        if not f.has(u):
            continue  # SymPy la simplificó sola, ej. (2x^2)^3 = 8x^6
        return af, u, du, f


def g_cadena(ctx, nombres_afuera=("pot", "sen", "cos", "exp"), adentro=_adentro_poly):
    af, u, du, f = _cadena(ctx, nombres_afuera, adentro)
    d = af.dF(u) * du
    errs = af.malos(u, du)
    pizarron = f"{tex_par(af.dF(u))}\\cdot {tex_par(du)}"
    expl = (f"Cadena: derivada de afuera (con $u = {tex(u)}$ adentro, sin tocar) por $u' = {tex(du)}$. "
            f"{af.regla}.")
    pistas = [f"Regla de la cadena: {af.regla}", f"Acá $u = {tex(u)}$ y $u' = {tex(du)}$."]
    formula = f"f(x) = {_tex_compuesta(af, u)}"
    if ctx.jefe:
        pasos = [paso_derivada(ctx, "¿Cuánto da la derivada?", "f'(x) =", d, errs, [], expl, original=f, mostrar=pizarron)]
    elif ctx.modo == "opciones":
        pasos = [_paso_adentro(ctx, f, u, af),
                 paso_derivada(ctx, "¿Cuánto da la derivada?", "f'(x) =", d, errs, pistas, expl, original=f, mostrar=pizarron)]
    else:
        pasos = [_paso_adentro(ctx, f, u, af),
                 paso_derivada(ctx, f"Derivá la de adentro, $u = {tex(u)}$:", "u' =", du, [],
                               [f"Derivá solo $u = {tex(u)}$, como en el Mundo 1."], "", original=u),
                 paso_derivada(ctx, "Ahora la derivada completa: (derivada de afuera en $u$) $\\cdot\\ u'$",
                               "f'(x) =", d, errs, pistas, expl, original=f, mostrar=pizarron)]
    return Ejercicio("Derivá la función:", formula, pasos)


def g_cadena_trasc(ctx):
    rng = ctx.rng
    if rng.random() < 0.5:
        return g_cadena(ctx, ("ln", "raiz"), _adentro_poly)
    return g_cadena(ctx, ("pot", "exp", "ln", "raiz", "sen", "cos"), _adentro_trasc)


def g_cadena_producto(ctx):
    rng = ctx.rng
    while True:
        p, dp, mp = _pieza(rng, rng.choice(["pot", "pot", "poly", "exp"]))
        af, u, du, g = _cadena(ctx, ("sen", "cos", "exp", "pot"), _adentro_poly)
        f = p * g
        if f.has(g) and f.has(p) and not (p.func == E and af.nombre == "exp"):
            break
    dg = af.dF(u) * du
    d = dp * g + p * dg
    errs = [(dp * g + p * af.dF(u), "cadena_sin_interior"), (dp * dg, "producto_derivadas"),
            (p * dg, "producto_falta_termino"), (dp * g, "producto_falta_termino")]
    errs += [(dp * g + p * m, c) for m, c in af.malos(u, du)]
    pizarron = f"{tex_par(dp)}\\cdot {_tex_compuesta(af, u)} + {tex_par(p)}\\cdot {tex_par(dg)}"
    expl = (f"Producto: $u'\\,v + u\\,v'$ con $u = {tex(p)}$ y $v = {_tex_compuesta(af, u)}$, "
            f"donde $v' = {tex(dg)}$ sale por cadena.")
    formula = f"f(x) = {tex_par(p)} \\cdot {_tex_compuesta(af, u)}"
    if ctx.jefe:
        return Ejercicio("Derivá la función:", formula,
                         [paso_derivada(ctx, "¿Cuánto da la derivada?", "f'(x) =", d, errs, [], expl, original=f, mostrar=pizarron)])
    ops = [Opcion(texto="Producto, y un factor lleva cadena", correcta=True),
           Opcion(texto="Solo cadena", error="regla_producto"),
           Opcion(texto="Solo producto, sin cadena", error="cadena_sin_interior"),
           Opcion(texto="Regla del cociente", error="regla_producto")]
    rng.shuffle(ops)
    regla = Paso(pregunta="¿Qué reglas vas a necesitar?", tipo="opcion", opciones=ops,
                 explicacion=f"Afuera hay un producto. Y ${_tex_compuesta(af, u)}$ tiene algo adentro: ese factor se deriva con cadena.",
                 resumen="Reglas: producto + cadena")
    pasos = [regla,
             paso_derivada(ctx, f"Llamemos $u = {tex(p)}$. ¿Cuánto es $u'$?", "u' =", dp, mp,
                           [f"Derivá solo ${tex(p)}$."], "", original=p),
             paso_derivada(ctx, f"Ahora $v = {_tex_compuesta(af, u)}$. ¿Cuánto es $v'$? (¡cadena!)", "v' =", dg,
                           af.malos(u, du), [af.regla, f"Lo de adentro es ${tex(u)}$ y su derivada ${tex(du)}$."],
                           "", original=g),
             paso_derivada(ctx, "Armá todo con $u'\\,v + u\\,v'$:", "f'(x) =", d, errs,
                           ["Regla del producto: $(u\\cdot v)' = u'\\,v + u\\,v'$."], expl, original=f, mostrar=pizarron)]
    return Ejercicio("Derivá la función:", formula, pasos)


def g_cadena_doble(ctx):
    rng = ctx.rng
    prohibidos = {("exp", "ln"), ("ln", "exp"), ("raiz", "pot"), ("pot", "pot"), ("ln", "pot")}
    while True:
        n1 = rng.choice(["pot", "sen", "cos", "exp", "raiz", "ln"])
        n2 = rng.choice(["sen", "cos", "exp", "pot"])
        if (n1, n2) in prohibidos or n1 == n2:
            continue
        af1, af2 = _afuera(rng, n1), _afuera(rng, n2)
        h, dh = _adentro_poly(rng)
        g = af2.F(h)
        f = af1.F(g)
        if f.has(g) and g.has(h):
            break
    dg_ok = af2.dF(h) * dh
    d = af1.dF(g) * dg_ok
    errs = [(af1.dF(g) * af2.dF(h), "cadena_doble_falta"), (af1.dF(g) * dh, "cadena_doble_falta"),
            (af1.dF(g), "cadena_sin_interior")]
    formula = f"f(x) = {_tex_compuesta(af1, g)}"
    pizarron = f"{tex_par(af1.dF(g))}\\cdot {tex_par(af2.dF(h))}\\cdot {tex_par(dh)}"
    expl = (f"Tres capas: afuera, en el medio $u = {tex(g)}$, y adentro de todo ${tex(h)}$. "
            "Se multiplica la derivada de cada capa, de afuera hacia adentro.")
    return Ejercicio("Derivá la función (¡cadena doble!):", formula,
                     [paso_derivada(ctx, "¿Cuánto da la derivada?", "f'(x) =", d, errs, [], expl, original=f, mostrar=pizarron)])


def g_jefe3(ctx):
    r = ctx.rng.random()
    if r < 0.45:
        return g_cadena_doble(ctx)
    if r < 0.75:
        return g_cadena_producto(ctx)
    return g_cadena_trasc(ctx)


# ======================================================== MUNDO 3½: ¿qué regla va?

def _item_regla(rng, dificultad):
    """Devuelve (tex, regla_correcta, explicación)."""
    trampas = dificultad >= 2 and rng.random() < 0.45
    anidado = dificultad >= 3 and rng.random() < 0.5
    tipo = rng.choice(["tabla", "producto", "cociente", "cadena"])
    pz = lambda t: _pieza(rng, t)[0]  # noqa: E731

    if anidado:
        caso = rng.randint(0, 5)
        if caso == 0:
            u, _ = _adentro_poly(rng)
            return (f"{tex_par(pz('pot'))} \\cdot \\mathrm{{sen}}({tex(u)})", "producto",
                    "Lo primero que ves es un producto. Después, uno de los factores lleva cadena.")
        if caso == 1:
            return ("e^{x\\,\\mathrm{sen}(x)}", "cadena",
                    "Lo de afuera es una exponencial con algo en el exponente: primero cadena. El producto aparece recién al derivar lo de adentro.")
        if caso == 2:
            u, _ = _adentro_poly(rng)
            return (f"\\frac{{\\mathrm{{sen}}({tex(u)})}}{{{tex(pz('pot'))}}}", "cociente",
                    "Afuera hay una división. La cadena aparece después, al derivar el numerador.")
        if caso == 3:
            return ("\\left(x\\,e^{x}\\right)^{3}", "cadena",
                    "Es algo **elevado a la 3**: primero cadena. Adentro hay un producto, pero eso viene después.")
        if caso == 4:
            return (f"\\ln(x)\\cdot\\cos({tex(_adentro_poly(rng)[0])})", "producto",
                    "Dos funciones multiplicándose: primero producto.")
        return (f"\\sqrt{{\\frac{{{tex(pz('pot'))}}}{{{tex(x**2 + rng.randint(1, 5))}}}}}", "cadena",
                "Es una raíz con algo adentro: primero cadena. El cociente es lo de adentro.")

    if trampas:
        caso = rng.randint(0, 4)
        if caso == 0:
            k = rng.choice([2, 3, 4, 5, 7])
            g = rng.choice(["\\mathrm{sen}(x)", "e^{x}", "\\ln(x)", "\\cos(x)"])
            return (f"{k}\\,{g}", "tabla",
                    f"El {k} es una **constante**: sale afuera. No hace falta la regla del producto.")
        if caso == 1:
            g = rng.choice(["\\mathrm{sen}^{2}(x)", "\\cos^{3}(x)", "\\ln^{2}(x)"])
            return (g, "cadena",
                    "$\\mathrm{sen}^2(x)$ significa $(\\mathrm{sen}\\,x)^2$: es una potencia con una función adentro, o sea, **cadena**.")
        if caso == 2:
            k = rng.choice([2, 3, 5])
            return (f"\\frac{{x^{{{rng.randint(2, 5)}}}}}{{{k}}}", "tabla",
                    f"Dividir por {k} es multiplicar por $\\frac{{1}}{{{k}}}$: una constante. Alcanza con la potencia.")
        if caso == 3:
            k = rng.choice([2, 3, 4, 5])
            return (f"\\mathrm{{sen}}({k}x)", "cadena",
                    f"Aunque sea simple, ${k}x$ está **adentro** del seno: es cadena (y $u' = {k}$).")
        return ("\\mathrm{sen}(x)\\cdot\\cos(x)", "producto",
                "Son dos funciones distintas de $x$ multiplicándose: producto.")

    if tipo == "tabla":
        t1 = rng.choice([t_potencia, t_sen, t_cos, t_exp, t_ln])(rng)
        t2 = rng.choice([t_potencia, t_constante, t_lineal])(rng)
        return (tex(t1.expr + t2.expr), "tabla",
                "Es una suma de funciones de la tabla: se deriva término a término, sin reglas especiales.")
    if tipo == "producto":
        a, b = _par_producto(rng)
        u, _, _, v, _, _ = _uv(rng, (a, b))
        return (_prod_tex(u, v), "producto", "Son dos funciones de $x$ multiplicándose.")
    if tipo == "cociente":
        u, _, _, v, _, _ = _uv(rng, _par_cociente(rng))
        return (_coc_tex(u, v), "cociente", "Una función de $x$ dividida por otra función de $x$.")
    af, u, du, f = _cadena(Ctx(rng, "opciones"), ("pot", "sen", "cos", "exp", "ln", "raiz"), _adentro_poly)
    return (_tex_compuesta(af, u), "cadena", f"Hay algo metido adentro de otra función: $u = {tex(u)}$.")


def g_regla(ctx):
    formula, correcta, expl = _item_regla(ctx.rng, ctx.dificultad)
    paso = paso_regla(ctx, correcta, expl)
    paso.max_intentos = 1
    return Ejercicio("¿Qué regla va?", f"f(x) = {formula}", [paso])
