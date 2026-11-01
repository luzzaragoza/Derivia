"""El "profe" que corrige: entiende lo que tipeás, lo compara con la respuesta
correcta y, si está mal, intenta decir cuál fue el error."""

import re

import mpmath
import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

x = sp.Symbol("x")

_TRANSFORMACIONES = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)

# Solo dejamos que el texto tipeado use estas funciones y nombres.
_GLOBALES = {
    "Symbol": sp.Symbol,
    "Integer": sp.Integer,
    "Float": sp.Float,
    "Rational": sp.Rational,
    "Function": sp.Function,
    "__builtins__": {},
}
_LOCALES = {
    "x": x,
    "e": sp.E,
    "pi": sp.pi,
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "log": sp.log,
    "sqrt": sp.sqrt,
    "exp": sp.exp,
}
_FUNCIONES = "sin|cos|tan|log|sqrt|exp"

# Caracteres "lindos" o que aparecen con teclas muertas del teclado en español.
_CARACTERES = {
    "²": "^2", "³": "^3", "·": "*", "×": "*", "÷": "/", "−": "-", "–": "-",
    "√": "sqrt", "π": "pi",
    "â": "^a", "ê": "^e", "î": "^i", "ô": "^o", "û": "^u",
    "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
    "[": "(", "]": ")", "{": "(", "}": ")",
}
_PERMITIDOS = re.compile(r"^[0-9a-z+\-*/^().\s]*$")


class ErrorEntrada(Exception):
    """Lo que tipeó no se puede entender como fórmula (no cuesta vidas)."""


def _potencia_de_funcion(s):
    """sin^2(x)  ->  (sin(x))^2  (respetando paréntesis anidados)."""
    patron = re.compile(r"\b(sin|cos|tan|log)\s*\^\s*(\d+)\s*\(")
    while True:
        m = patron.search(s)
        if not m:
            return s
        inicio_par = m.end() - 1
        nivel = 0
        fin = None
        for i in range(inicio_par, len(s)):
            if s[i] == "(":
                nivel += 1
            elif s[i] == ")":
                nivel -= 1
                if nivel == 0:
                    fin = i
                    break
        if fin is None:
            raise ErrorEntrada("Falta cerrar un paréntesis.")
        adentro = s[inicio_par + 1:fin]
        s = s[:m.start()] + f"({m.group(1)}({adentro}))^{m.group(2)}" + s[fin + 1:]


def normalizar(texto):
    s = texto.strip().lower()
    for viejo, nuevo in _CARACTERES.items():
        s = s.replace(viejo, nuevo)
    s = s.replace(",", ".").replace("**", "^")
    # nombres en castellano
    s = s.replace("raiz", "sqrt").replace("sen", "sin").replace("tg", "tan")
    s = s.replace("ln", "log")
    return s


def parsear(texto):
    """Convierte lo que tipeó en una expresión de SymPy. Lanza ErrorEntrada."""
    if not texto or not texto.strip():
        raise ErrorEntrada("Todavía no escribiste nada.")
    if len(texto) > 200:
        raise ErrorEntrada("Es muy larga, revisala.")
    s = normalizar(texto)
    if not _PERMITIDOS.match(s):
        raise ErrorEntrada("Hay algún símbolo que no conozco.")
    if s.count("(") != s.count(")"):
        raise ErrorEntrada("Los paréntesis no están parejos.")
    s = _potencia_de_funcion(s)
    # separar los nombres de función para que "xcos(x)" sea x·cos(x)
    s = re.sub(rf"({_FUNCIONES})", r" \1 ", s)
    try:
        expr = parse_expr(s, local_dict=dict(_LOCALES), global_dict=dict(_GLOBALES),
                          transformations=_TRANSFORMACIONES)
    except Exception:
        raise ErrorEntrada("No entiendo la fórmula. ¿Falta algún paréntesis o un signo?")
    if not isinstance(expr, sp.Basic):
        raise ErrorEntrada("No entiendo la fórmula.")
    expr = sp.sympify(expr)
    raras = expr.atoms(sp.core.function.AppliedUndef)
    if raras:
        nombre = sorted(str(f.func) for f in raras)[0]
        raise ErrorEntrada(f"No conozco la función «{nombre}».")
    otras = sorted(str(s) for s in expr.free_symbols - {x})
    if otras:
        raise ErrorEntrada(f"Usá solo la variable x (encontré: {', '.join(otras)}).")
    if expr.has(sp.zoo, sp.nan, sp.oo):
        raise ErrorEntrada("Ahí hay una división por cero.")
    return expr


# ------------------------------------------------------------ LaTeX lindo

def tex(expr):
    """LaTeX con la notación de la facultad: sen, tg, ln."""
    s = sp.latex(sp.sympify(expr), ln_notation=True)
    s = s.replace(r"\sin", r"\mathrm{sen}").replace(r"\tan", r"\mathrm{tg}")
    s = s.replace(r"\left(", "(").replace(r"\right)", ")")
    s = s.replace(r"\left[", "[").replace(r"\right]", "]")
    s = s.replace(r"\operatorname", r"\mathrm")
    return s


def tex_par(expr):
    """Igual que tex() pero con paréntesis si es una suma."""
    expr = sp.sympify(expr)
    if expr.is_Add or (expr.could_extract_minus_sign() and not expr.is_Number):
        return f"({tex(expr)})"
    return tex(expr)


def tex_base(expr):
    """Para usar como base de una potencia: (4x^4)^2 y no 4x^4^2."""
    expr = sp.sympify(expr)
    if expr.is_Symbol or (expr.is_Function and expr.func != sp.exp):
        return tex(expr)
    return f"({tex(expr)})"


# ------------------------------------------------------------ comparar

_PUNTOS = [0.37, 0.81, 1.23, 1.71, 2.29, 2.83, 3.41]


def _valores(expr):
    f = sp.lambdify(x, expr, modules="mpmath")
    vals = []
    for p in _PUNTOS:
        try:
            v = mpmath.mpc(f(mpmath.mpf(p)))
            if mpmath.isnan(v.real) or mpmath.isinf(v.real) or mpmath.isnan(v.imag) or mpmath.isinf(v.imag):
                v = None
        except Exception:
            v = None
        vals.append(v)
    return vals


def _cerca(a, b):
    return abs(a - b) <= 1e-7 * (1 + abs(b))


def equivalentes(a, b):
    """True si a y b son la misma función (aunque estén escritas distinto)."""
    a, b = sp.sympify(a), sp.sympify(b)
    va, vb = _valores(a), _valores(b)
    validos = 0
    for p, q in zip(va, vb):
        if q is None:
            continue
        if p is None or not _cerca(p, q):
            return False
        validos += 1
    if validos >= 3:
        return True
    try:
        return sp.simplify(a - b) == 0
    except Exception:
        return False


def _razon_constante(a, b):
    """Si a = k·b para un número k (≠1), devuelve k; si no, None."""
    va, vb = _valores(a), _valores(b)
    k = None
    n = 0
    for p, q in zip(va, vb):
        if p is None or q is None or abs(q) < 1e-9:
            continue
        r = p / q
        if k is None:
            k = r
        elif not _cerca(r, k):
            return None
        n += 1
    if n < 3 or k is None or _cerca(k, 1) or abs(k) < 1e-9:
        return None
    return k


def _difiere_en_constante(a, b):
    va, vb = _valores(a), _valores(b)
    c = None
    n = 0
    for p, q in zip(va, vb):
        if p is None or q is None:
            continue
        d = p - q
        if c is None:
            c = d
        elif not _cerca(d, c):
            return False
        n += 1
    return n >= 3 and c is not None and abs(c) > 1e-7


# ------------------------------------------------------------ errores típicos

ERRORES = {
    # potencias
    "potencia_no_resta": ("Te faltó restarle 1 al exponente",
                          "Regla de la potencia: $(x^n)' = n\\,x^{n-1}$. El exponente baja multiplicando **y** se le resta 1."),
    "potencia_no_baja": ("Te faltó bajar el exponente",
                         "En $(x^n)' = n\\,x^{n-1}$ el exponente $n$ baja multiplicando adelante. Restaste 1 pero no lo bajaste."),
    "potencia_suma": ("Le sumaste 1 al exponente",
                      "Al **derivar** se resta 1 al exponente. Sumar 1 es lo que se hace al **integrar**."),
    "potencia_negativa": ("Ojo con el exponente negativo",
                          "Restar 1 a un exponente negativo lo hace **más** negativo: por ejemplo $-2-1=-3$, no $-1$."),
    "potencia_negativa_signo": ("Se te perdió el signo menos",
                                "Cuando el exponente es negativo, al bajar multiplicando trae el signo menos con él."),
    "constante_no_cero": ("La derivada de una constante es 0",
                          "Un número solo (sin $x$) no cambia, así que su derivada es 0: desaparece."),
    "no_derivaste_termino": ("Hay un término sin derivar",
                             "Revisá término por término: alguno quedó igual que en la función original."),
    "no_derivaste": ("Eso es la función original",
                     "Escribiste la misma función que te dieron. Hay que derivarla."),
    # tabla
    "signo_sen": ("La derivada del seno no lleva menos",
                  "$(\\mathrm{sen}\\,x)' = \\cos x$, sin signo menos. El menos aparece en la del coseno."),
    "signo_cos": ("La derivada del coseno lleva un menos",
                  "$(\\cos x)' = -\\mathrm{sen}\\,x$. Es el error más común: ¡acordate del menos!"),
    "exp_como_potencia": ("$e^x$ no se deriva como potencia",
                          "En $e^x$ la $x$ está en el exponente, así que **no** se usa la regla de la potencia. $(e^x)' = e^x$: queda igual."),
    "ln_derivada": ("La derivada de ln no es esa",
                    "$(\\ln x)' = \\frac{1}{x}$."),
    "raiz_sin_2": ("Te faltó el 2 de abajo",
                   "$(\\sqrt{x})' = \\frac{1}{2\\sqrt{x}}$: sale de $(x^{1/2})' = \\frac{1}{2}x^{-1/2}$. El $\\frac{1}{2}$ que baja es el 2 del denominador."),
    "reescritura_signo": ("Lo de abajo sube con exponente negativo",
                          "$\\frac{1}{x^n} = x^{-n}$: al pasar del denominador al numerador, el exponente cambia de signo."),
    "reescritura_raiz": ("La raíz es un exponente fraccionario",
                         "$\\sqrt{x} = x^{1/2}$ y $\\sqrt[3]{x} = x^{1/3}$: el índice de la raíz va **abajo** en la fracción."),
    # producto
    "producto_derivadas": ("La derivada de un producto no es el producto de las derivadas",
                           "$(u\\cdot v)' \\neq u'\\cdot v'$. La regla es $(u\\cdot v)' = u'\\,v + u\\,v'$: se deriva **de a uno** y se suman."),
    "producto_falta_termino": ("Te falta uno de los dos términos",
                               "$(u\\cdot v)' = u'\\,v + u\\,v'$ tiene **dos** términos: primero derivás $u$ y dejás $v$; después dejás $u$ y derivás $v$."),
    "producto_signo": ("En el producto los términos se suman",
                       "$(u\\cdot v)' = u'\\,v + u\\,v'$ va con **más**. El menos es de la regla del cociente."),
    # cociente
    "cociente_signo_mas": ("En el cociente el numerador va con menos",
                           "$\\left(\\frac{u}{v}\\right)' = \\frac{u'\\,v - u\\,v'}{v^2}$: es una **resta**, no una suma."),
    "cociente_orden": ("El orden de la resta está al revés",
                       "Primero va la derivada de **arriba**: $u'\\,v - u\\,v'$. Si lo das vuelta, te queda todo con el signo cambiado."),
    "cociente_sin_cuadrado": ("Te faltó elevar al cuadrado el denominador",
                              "$\\left(\\frac{u}{v}\\right)' = \\frac{u'\\,v - u\\,v'}{v^2}$: abajo va $v$ **al cuadrado**."),
    "cociente_derivadas": ("La derivada de un cociente no es el cociente de las derivadas",
                           "$\\left(\\frac{u}{v}\\right)' \\neq \\frac{u'}{v'}$. Usá $\\frac{u'\\,v - u\\,v'}{v^2}$."),
    # cadena
    "cadena_sin_interior": ("Te faltó multiplicar por la derivada de adentro",
                            "Regla de la cadena: derivada de afuera (con lo de adentro **sin tocar**) **por la derivada de adentro**."),
    "cadena_evaluar_derivada": ("Lo de adentro va sin derivar dentro de la función",
                                "En $f'(u)\\cdot u'$, la derivada de afuera se evalúa en $u$ (lo de adentro tal cual), no en $u'$. $u'$ va multiplicando afuera."),
    "cadena_afuera_en_x": ("Lo de adentro tiene que seguir adentro",
                           "Al derivar la de afuera, lo de adentro queda igual: si era $\\cos(x^2)$, la derivada de afuera es $-\\mathrm{sen}(x^2)$, con el $x^2$ adentro."),
    "cadena_doble_falta": ("Te faltó una de las derivadas de adentro",
                           "Con funciones metidas una dentro de otra, multiplicás la derivada de **cada capa**, de afuera hacia adentro."),
    "adentro_x": ("Si fuera x no habría cadena",
                  "La de adentro es lo que está «metido» en la otra función: lo que está entre paréntesis, en el exponente o debajo de la raíz."),
    "adentro_todo": ("Esa es la función entera",
                     "Buscá qué parte está metida **dentro** de otra función: esa es $u$, la de adentro."),
    "adentro_parte": ("Es todo lo que está adentro, no solo una parte",
                      "La función de adentro es **todo** lo que está metido en la de afuera, con todos sus términos."),
    # generales
    "signo_general": ("Te quedó el signo cambiado",
                      "El resultado tiene el signo al revés. Revisá los menos: en el coseno, en exponentes negativos o en restas."),
    "factor_constante": ("Te sobra o te falta un número multiplicando",
                         "La forma está bien pero hay un factor numérico de más o de menos. Revisá los exponentes que bajan y las derivadas de adentro."),
    "constante_de_mas": ("Te sobra un número sumando",
                         "Casi: hay un número sumando que no va. ¿Derivaste todas las constantes sueltas a 0?"),
    # elegir regla
    "regla_producto": ("Es un producto",
                       "Hay dos funciones de $x$ multiplicándose: va la regla del producto."),
    "regla_cociente": ("Es un cociente",
                       "Hay una función de $x$ dividida por otra: va la regla del cociente."),
    "regla_cadena": ("Es una composición",
                     "Hay una función metida adentro de otra: va la regla de la cadena."),
    "regla_tabla": ("Alcanza con la tabla",
                    "Son derivadas directas de la tabla (y los números que multiplican salen afuera)."),
}

_GENERICO = ("Todavía no",
             "No es la respuesta correcta. Revisá las cuentas paso a paso.")


def diagnosticar(respuesta, esperado, errores=(), original=None):
    """Devuelve (codigo, titulo, explicacion) del error más probable."""
    for expr, codigo in errores:
        try:
            if equivalentes(respuesta, expr):
                return (codigo,) + ERRORES[codigo]
        except Exception:
            pass
    if original is not None and equivalentes(respuesta, original):
        return ("no_derivaste",) + ERRORES["no_derivaste"]
    if equivalentes(respuesta, -esperado):
        return ("signo_general",) + ERRORES["signo_general"]
    if _razon_constante(respuesta, esperado) is not None:
        return ("factor_constante",) + ERRORES["factor_constante"]
    if _difiere_en_constante(respuesta, esperado):
        return ("constante_de_mas",) + ERRORES["constante_de_mas"]
    return (None,) + _GENERICO
