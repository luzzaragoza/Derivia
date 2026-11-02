# Derivia

Un juego para aprender a derivar e integrar, de a un paso por vez: desde la regla de la potencia hasta integrales triples en esféricas.

## Qué trae

**49 niveles en 10 mundos**, de derivadas básicas a integrales triples:

| Mundo | Tema | Niveles |
|---|---|---|
| 1 | Derivadas básicas | Potencias · Seno, coseno, e y ln · Sumas · Raíces y fracciones · **Jefe** |
| 2 | Producto y cociente | Producto · Producto paso a paso · Cociente · Cociente paso a paso · **Jefe** |
| 3 | Regla de la cadena | Cadena · Cadena paso a paso · ln, raíz y trigonométricas · Cadena + producto · **Jefe: cadena doble** |
| 3½ | ¿Qué regla va? | Contrarreloj: elegir la regla antes de derivar (con trampas como `5·sen(x)` o `sen²(x)`) |
| 4 | Derivadas parciales | Respecto de x · Respecto de y · Las dos parciales · Parciales con cadena · **Jefe: derivada segunda** |
| 5 | Integrales inmediatas | Potencias · Seno, coseno, e y 1/x · Sumas · Raíces y fracciones · Integral definida (Barrow) · **Jefe** |
| 6 | Sustitución | Adentro lineal · Elegir la u · Paso a paso · Acomodar constantes · **Jefe** |
| 7 | Integración por partes | ¿Quién es u? (LIATE) · Paso a paso · Con logaritmos · **Jefe** |
| 8 | Integrales dobles | Rectángulos · Regiones tipo I · Cambio de orden · Polares · **Jefe** |
| 9 | Integrales triples | Cajas · Límites variables · Cilíndricas · Esféricas · **Jefe final** |

- **Mezcla de opciones y tipeo**: los primeros niveles de cada mundo son de elegir; después tipeás vos.
- **Paso a paso**: en los niveles "paso a paso" primero identificás la regla o la función de adentro, después derivás cada parte y al final armás el resultado.
- **Te dice qué error cometiste**: por ejemplo "te faltó multiplicar por la derivada de adentro" o "(u·v)′ no es u′·v′".
- **3 vidas por nivel**, puntos, racha y de 1 a 3 estrellas.
- **Pistas** que cuestan 5 puntos (en los jefes no hay).
- **Cuaderno de errores**: todo ejercicio en el que te equivocás se guarda. Te vuelve a aparecer como repaso y sale cuando lo resolvés bien 2 veces.
- **Ejercicios infinitos**: se generan con números al azar cada vez.
- **Integrales**: se corrigen derivando tu respuesta, así que vale cualquier primitiva (con o sin `+ C`).
- **Integrales dobles**: te muestra el dibujo de la región.
- Abajo del cuadro de texto aparece **"Leo: …"** con cómo se entendió lo que escribiste.
- **Un gato naranja** te acompaña: festeja los aciertos, se pone triste con los errores y te da las pistas.
- **Mapa de islas**: cada mundo es una isla con un camino de niveles.
- **Sonidos 8-bit** (se prenden y apagan con la tecla **M** o con el botón del parlante), confeti, monedas que vuelan,
  racha con fueguito y transiciones con olas.

## Cómo jugar en Windows

### Opción A: armar el `.exe` (recomendada)

1. Instalá Python desde https://www.python.org/downloads/ (la 3.12 o una más nueva).
   En el instalador **marcá la casilla "Add python.exe to PATH"**.
2. Descomprimí la carpeta `derivia` donde quieras.
3. Hacé doble clic en **`construir_exe.bat`**. Tarda unos minutos la primera vez.
4. Cuando termina, el juego queda en **`dist\Derivia.exe`**. Copialo al Escritorio y listo:
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
| otras variables | `3x^2y + z` |
| constante de integración | `x^3/3 + C` |
| pi | `8pi/3` |

No hace falta simplificar: si tu respuesta es la misma función escrita de otra forma, cuenta como bien.
Si escribís algo que no se entiende, no perdés vidas.

## Dónde se guarda el progreso

En `%APPDATA%\Derivia\progreso.json`. Si lo borrás, el juego arranca de cero.

Si venías jugando cuando el juego se llamaba Calculandia, la primera vez que abras Derivia se copia solo tu progreso de `%APPDATA%\Calculandia`.

## Para programar

```
juego/mate.py         el "profe": entiende lo tipeado, compara respuestas y detecta errores típicos
juego/ejercicios.py   estructuras de los pasos y generadores de derivadas (mundos 1 a 3½)
juego/gen_integrales.py  derivadas parciales e integrales de una variable (mundos 4 a 7)
juego/gen_multiples.py   integrales dobles y triples (mundos 8 y 9)
juego/mundos.py       la lista de mundos y niveles
juego/escenas.py      pantallas (menú, mapa, nivel, resultados, cuaderno, ayuda)
juego/ui.py           dibujo: colores, tipografías, fórmulas, botones, cuadro de texto
juego/gato.py         el gato (dibujado con formas) y sus animaciones
juego/paisaje.py      cielo, mar, islas, palmeras y el pergamino de fondo
juego/fx.py           confeti, chispas, monedas que vuelan, fueguito
juego/sonido.py       los sonidos 8-bit (se sintetizan al arrancar, no hay archivos de audio)
juego/progreso.py     guardado
tests/                pruebas: genera cientos de ejercicios y verifica que todo esté bien
```

Para correr las pruebas: `python tests/test_ejercicios.py`

## Créditos

La tipografía de los títulos es **Fredoka One** (Milena Brandão), con licencia SIL Open Font License:
ver `juego/assets/fuentes/OFL.txt`.
