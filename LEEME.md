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
- **Cada mundo es una isla distinta**: de la Isla Serena a la Isla Calavera, cada vez un poco más misteriosas.
- **Tu michi tiene nombre**: se lo ponés la primera vez (y lo cambiás tocando su cartelito en el menú).
- **Teclado de fórmulas** como el de la calculadora (x², xⁿ, √, ⁿ√, +, −, AC) y un teclado numérico que se
  despliega con **123** (para usarlo con pantalla táctil). Los paréntesis se colorean por pareja. El punto
  también multiplica (`2.x`); los decimales van con coma (`0,5`).
- **Detective de errores**: a veces te muestran la resolución de otra persona y tenés que encontrar el error.
- **PENSÁ / CALCULÁ**: cada consigna dice si es de razonar o de hacer la cuenta (y cambia la música).
- **Al terminar un nivel** podés revisar tus errores; en cada isla hay un botón para **repasar todo el mundo**.
- Abajo del cuadro de texto aparece **"Leo: …"** con cómo se entendió lo que escribiste.
- **Un gato naranja** te acompaña: festeja los aciertos, se pone triste con los errores y te da las pistas.
- **Mapa de islas**: cada mundo es una isla con un camino de niveles.
- **Tienda del michi**: las monedas que ganás en los niveles se guardan y sirven para comprarle ropa al gato
  (sombreros, pelucas, anteojos, collares, vestidos, capa, alitas, varita...) y **conjuntos** completos
  (astronauta, bruja, princesa, hada, chef, pirata...). Lo que le ponés lo lleva en todo el juego.
- **Música de fondo** tranquila y **sonidos 8-bit**. En **Opciones** (el engranaje) se prenden, apagan y ajustan
  por separado; la tecla **M** silencia todo.
- Confeti, monedas que vuelan, racha con fueguito, transiciones con olas y una fanfarria con el gato saltando
  cuando arrancás un nivel.
- **Pantalla completa** con **F11** (o desde Opciones). Al agrandar la ventana la imagen se suaviza en vez de pixelarse.

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
| raíz cúbica (o la que sea) | `raiz3(x)`, `raiz4(x)`, ... |
| fracción | `(x+1)/(x^2+1)` |
| seno al cuadrado | `sen(x)^2` o `sen^2(x)` |
| otras variables | `3x^2y + z` |
| constante de integración | `x^3/3 + C` |
| pi | `8pi/3` |

No hace falta simplificar: si tu respuesta es la misma función escrita de otra forma, cuenta como bien.
Si escribís algo que no se entiende, no perdés vidas.

## Dónde se guarda el progreso

En `%APPDATA%\Derivia\progreso.json` (normalmente `C:\Users\TU_USUARIO\AppData\Roaming\Derivia\progreso.json`).
Para abrir la carpeta: tecla Windows + R, escribí `%APPDATA%\Derivia` y Enter.

- **Copia de seguridad:** copiá `progreso.json` a otro lado. Para recuperarla, cerrá el juego y volvé a ponerla en esa carpeta.
- **Empezar de cero:** Opciones → *Borrar progreso*. Pide confirmación y antes de borrar deja una copia
  `progreso_respaldo_<fecha>.json` en la misma carpeta (para volver atrás, renombrala a `progreso.json`).

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
juego/lienzo.py       todo se piensa en 1280×720 pero se dibuja a la resolución real de tu pantalla
juego/pincel.py       piezas dibujadas con Skia (el motor gráfico de Chrome): botones, paneles, islas,
                      palmeras, globitos... con degradés, brillos y sombras suaves. Si Skia no está,
                      el juego usa dibujos más simples y anda igual.
juego/gato.py         el gato (dibujado con formas) y sus animaciones
juego/paisaje.py      cielo, mar, islas, palmeras y el pergamino de fondo
juego/fx.py           confeti, chispas, monedas que vuelan, fueguito
juego/sonido.py       los sonidos 8-bit (se sintetizan al arrancar, no hay archivos de audio)
juego/progreso.py     guardado
tests/                pruebas: genera cientos de ejercicios y verifica que todo esté bien
```

Pruebas:

```
python tests/test_ejercicios.py   # cientos de ejercicios de cada nivel: respuestas y errores típicos bien armados
python tests/test_detective.py    # el detective: una sola razón correcta y todas con sentido
python tests/test_e2e.py          # el juego entero: arranque, tamaños de ventana, todos los botones,
                                  # los 49 niveles y borrar progreso (--rapido para una versión corta)
```

## Gráficos

Derivia usa dos motores juntos:

- **pygame-ce** arma la pantalla 60 veces por segundo (rápido).
- **Skia** (`pip install skia-python`) pinta una sola vez las piezas lindas (botones, islas,
  paneles, monedas, estrellas) y quedan guardadas. Así se ve prolijo sin trabarse.

Todo se dibuja a la resolución real de tu monitor (en Full HD, 2K o 4K se ve nítido) y el juego
le avisa a Windows que maneja él la escala, para que Windows no lo estire y lo vuelva borroso.

## Créditos

La tipografía de los títulos es **Fredoka One** (Milena Brandão), con licencia SIL Open Font License:
ver `juego/assets/fuentes/OFL.txt`.
