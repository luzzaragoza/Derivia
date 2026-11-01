# Calculandia

Un juego para aprender a derivar (y, en las próximas versiones, a integrar), de a un paso por vez.

## Versión 1: qué trae

| Mundo | Tema | Niveles |
|---|---|---|
| 1 | Derivadas básicas | Potencias · Seno, coseno, e y ln · Sumas · Raíces y fracciones · **Jefe** |
| 2 | Producto y cociente | Producto · Producto paso a paso · Cociente · Cociente paso a paso · **Jefe** |
| 3 | Regla de la cadena | Cadena · Cadena paso a paso · ln, raíz y trigonométricas · Cadena + producto · **Jefe: cadena doble** |
| 3½ | ¿Qué regla va? | Contrarreloj: elegir la regla antes de derivar (con trampas como `5·sen(x)` o `sen²(x)`) |

- **Mezcla de opciones y tipeo**: los primeros niveles de cada mundo son de elegir; después tipeás vos.
- **Paso a paso**: en los niveles "paso a paso" primero identificás la regla o la función de adentro, después derivás cada parte y al final armás el resultado.
- **Te dice qué error cometiste**: por ejemplo "te faltó multiplicar por la derivada de adentro" o "(u·v)′ no es u′·v′".
- **3 vidas por nivel**, puntos, racha y de 1 a 3 estrellas.
- **Pistas** que cuestan 5 puntos (en los jefes no hay).
- **Cuaderno de errores**: todo ejercicio en el que te equivocás se guarda. Te vuelve a aparecer como repaso y sale cuando lo resolvés bien 2 veces.
- **Ejercicios infinitos**: se generan con números al azar cada vez.
- Abajo del cuadro de texto aparece **"Leo: …"** con cómo se entendió lo que escribiste.

## Cómo jugar en Windows

### Opción A: armar el `.exe` (recomendada)

1. Instalá Python desde https://www.python.org/downloads/ (la versión 3.12 o 3.13).
   En el instalador **marcá la casilla "Add python.exe to PATH"**.
2. Descomprimí la carpeta `calculandia` donde quieras.
3. Hacé doble clic en **`construir_exe.bat`**. Tarda unos minutos la primera vez.
4. Cuando termina, el juego queda en **`dist\Calculandia.exe`**. Copialo al Escritorio y listo:
   desde ahí se abre con doble clic, sin necesitar nada más.

> La primera vez que lo abras, Windows puede mostrar "Windows protegió su PC" porque el
> `.exe` no está firmado. Tocá **Más información → Ejecutar de todas formas**.
> Tarda unos segundos en abrir porque lleva Python adentro.

### Opción B: jugar sin armar el `.exe`

Con Python instalado (paso 1 de arriba), hacé doble clic en **`jugar.bat`**.

## Cómo escribir las respuestas

| Para | Tipeás |
|---|---|
| potencia | `x^3` |
| multiplicar | `3x` o `3*x` |
| seno, coseno, tangente | `sen(x)`, `cos(x)`, `tg(x)` |
| e a la algo | `e^(2x)`, con paréntesis |
| logaritmo natural | `ln(x)` |
| raíz | `raiz(x)` |
| fracción | `(x+1)/(x^2+1)` |
| seno al cuadrado | `sen(x)^2` o `sen^2(x)` |

No hace falta simplificar: si tu respuesta es la misma función escrita de otra forma, cuenta como bien.
Si escribís algo que no se entiende, no perdés vidas.

## Dónde se guarda el progreso

En `%APPDATA%\Calculandia\progreso.json`. Si lo borrás, el juego arranca de cero.

## Para programar

```
juego/mate.py         el "profe": entiende lo tipeado, compara respuestas y detecta errores típicos
juego/ejercicios.py   generadores de ejercicios y lista de mundos y niveles
juego/escenas.py      pantallas (menú, mapa, nivel, resultados, cuaderno, ayuda)
juego/ui.py           dibujo: fórmulas, botones, cuadro de texto
juego/progreso.py     guardado
tests/                pruebas: genera cientos de ejercicios y verifica que todo esté bien
```

Para correr las pruebas: `python tests/test_ejercicios.py`
