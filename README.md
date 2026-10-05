# Biblioteca de Generación y Validación de Números Pseudoaleatorios

Módulo en Python desarrollado desde cero (*from scratch*) para la generación, transformación y validación estadística de secuencias de números pseudoaleatorios, según los lineamientos teóricos del curso de **Simulación de computadores** (UPTC).

Los generadores no usan `random` ni `numpy.random`. La librería `scipy` se utiliza únicamente para obtener valores críticos de las distribuciones (Z, χ², KS) en las pruebas estadísticas.

Diseñado con una arquitectura modular para ser reutilizado en los puntos 2 (caminatas aleatorias) y 4 (EpiSim) del taller.

> **Pruebas incluidas:** medias, varianza, Chi-cuadrado, Kolmogorov-Smirnov y Póker. La prueba de rachas (*runs test*) no se incluye en este módulo por indicación del docente.

---

## Estructura del Módulo

```text
3_gui_psudo_gen/                # Raíz del proyecto (es a la vez la aplicación y el paquete)
├── gui.py                      # Interfaz gráfica (tkinter)
├── main.py                     # Interfaz de consola (menú interactivo y modo --demo)
├── requirements.txt            # Dependencias
├── ejemplos/
│   ├── semillas.txt            # Archivo de ejemplo de semillas (una por línea, admite comentarios #)
│   └── semillas.csv            # El mismo ejemplo en formato CSV
├── salidas/                    # Se crea al ejecutar: gráficos .png y tablas .csv
├── __init__.py                 # Exportación unificada de generadores, transformaciones y pruebas
├── generadores/
│   ├── __init__.py
│   ├── cuadrados_medios.py     # Von Neumann (1946): extracción de n dígitos centrales
│   ├── congruencial_lineal.py  # Lehmer / Mixto con verificación del Teorema de Hull-Dobell
│   ├── congruencial_multiplicativo.py  # Caso c=0 con validación de coprimalidad
│   ├── congruencial_aditivo.py # Fibonacci retrasado x_n = (x_{n-j} + x_{n-k}) mod m
│   └── transformaciones.py     # Uniforme U(a,b), Normal Box-Muller N(μ,σ²), Exponencial Exp(λ)
├── pruebas/
│   ├── __init__.py
│   ├── resultado.py            # Clase ResultadoPrueba (interfaz común de resultados)
│   ├── prueba_medias.py        # Propiedad 1: E[R_i] = 0.5 (Z normal)
│   ├── prueba_varianza.py      # Propiedad 1: Var(R_i) = 1/12 (Chi-cuadrado n-1 gl)
│   ├── prueba_chi2.py          # Propiedad 2: Uniformidad en [0, 1) con k intervalos
│   ├── prueba_ks.py            # Propiedad 2: Kolmogorov-Smirnov (D_max vs empírica)
│   └── prueba_poker.py         # Propiedad 3: Independencia (7 manos sobre 5 decimales)
└── utilidades/
    ├── __init__.py
    ├── archivo_manager.py      # Carga/guardado de semillas y secuencias en .txt y .csv
    └── visualizacion.py        # Gráficos estandarizados con Matplotlib
```

---

## Requisitos e Instalación

- Python 3.10+
- Dependencias (necesarias incluso si solo se usan los generadores, porque el paquete las importa al cargarse):
  ```bash
  pip install -r requirements.txt
  ```
- Todos los comandos se ejecutan desde la carpeta raíz del proyecto:
  ```bash
  python gui.py           # Interfaz gráfica
  python main.py          # Interfaz de consola
  ```
  `gui.py` y `main.py` registran automáticamente la carpeta raíz como el paquete `generador_numeros_pruebas`, por lo que no hay que instalar nada adicional.
- **Uso como biblioteca en otros puntos del taller.** El nombre de la carpeta raíz (`3_gui_psudo_gen`) no es un identificador válido de Python (empieza por un número), así que no se puede importar directamente. Copie la carpeta (sin `venv/` ni `salidas/`) dentro del proyecto donde se vaya a usar con el nombre `generador_numeros_pruebas/` (o agregue su carpeta padre al `sys.path`) e importe:
  ```python
  import generador_numeros_pruebas as gnp
  ```

---

## Interfaz gráfica (`gui.py`)

```bash
python gui.py
```

La interfaz usa `tkinter` (incluido con Python), por lo que no requiere dependencias adicionales.

**Panel izquierdo (configuración):**

1. **Semillas**
   - *Manual:* escribir las semillas separadas por coma y presionar «Aplicar» (o Enter).
   - *Automático:* «Examinar...» abre un archivo `.txt` o `.csv` (por defecto la carpeta `ejemplos/`).
   - *Semilla a usar:* selecciona cuál de las semillas cargadas usan los generadores en la ejecución.
2. **Métodos de generación:** casillas para elegir uno o varios métodos. El botón «Parámetros» de cada uno permite modificar `a`, `c`, `m`, `n`, `j`, `k`, límites de la uniforme, `μ` y `σ` (admite potencias como `2**32`). Para el Congruencial Lineal se advierte si los parámetros no cumplen Hull-Dobell.
3. **Pruebas estadísticas:** casillas para elegir cuáles de las 5 pruebas ejecutar.
4. **Configuración:** cantidad de números `n`, nivel de significancia `α`, intervalos de Chi² y subgrupos de los gráficos de medias y varianza.

Botones: **«Generar y validar»** ejecuta todo; **«Exportar tablas a CSV...»** guarda las secuencias y la tabla comparativa; **«Guardar todos los gráficos...»** guarda los histogramas y los gráficos de todas las pruebas en `.png`.

**Pestañas (resultados):**

| Pestaña | Contenido |
| :--- | :--- |
| Secuencias | Tabla `i, Xi, Ri, Ni` del método seleccionado (se muestran hasta 2000 filas; el CSV contiene todas). |
| Resultados | Tabla comparativa método × prueba (✓/✗, tiempo y período observado) y detalle de cada prueba con su estadístico y criterio de aceptación. Doble clic en una fila del detalle abre su gráfico. |
| Gráficos | Histograma de generación o gráfico de cualquier prueba, elegidos con dos listas desplegables. Incluye barra de herramientas para acercar, desplazar y guardar la imagen. |

---

## Interfaz de consola (`main.py`)

```bash
python main.py          # Menú interactivo
python main.py --demo   # Demostración completa sin preguntas (guarda todo en salidas/)
```

| Opción del menú | Función |
| :--- | :--- |
| 1. Semillas | Ingreso manual (lista separada por comas) o carga desde archivo `.txt` / `.csv` (por defecto `ejemplos/semillas.txt`). |
| 2. Seleccionar métodos | Selección múltiple (`1,3,5` o `t` para todos) entre Cuadrados Medios, Congruencial Lineal, Multiplicativo, Aditivo, Uniforme y Normal. Permite ajustar los parámetros de cada método o usar los valores por defecto. |
| 3. Generar secuencias | Genera `n` números por método, muestra la tabla `i, Xi, Ri, Ni` en consola y la exporta a `salidas/secuencia_<metodo>.csv`. |
| 4. Pruebas estadísticas | Selección múltiple de las 5 pruebas; imprime cada resultado y guarda sus gráficos en `salidas/prueba_<prueba>_<metodo>.png`. |
| 5. Histogramas | Histograma de cada método con la densidad teórica superpuesta, en `salidas/histograma_<metodo>.png`. |
| 6. Comparar métodos | Tabla resumen método × prueba (✓/✗), tiempo de generación y período observado; se exporta a `salidas/comparacion_metodos.csv`. |
| 7. Configuración | `n`, nivel de significancia α, intervalos de Chi², subgrupos de los gráficos, mostrar u ocultar gráficos y carpeta de salida. |
| 8. Demostración | Ejecuta todo lo anterior automáticamente con el archivo de semillas de ejemplo. |

**Semillas por método.** Cada método usa por defecto la primera semilla cargada, ajustada a su rango válido (p. ej., módulo `10^n` en Cuadrados Medios). El método aditivo usa directamente las semillas cargadas si hay al menos `k`; si no, genera las `k` semillas iniciales con un Congruencial Lineal.

**Uniforme y Normal.** Son transformaciones de los `R_i` de un Congruencial Lineal base (`a=1664525, c=1013904223, m=2^32`). Las tablas y los histogramas muestran los `N_i` transformados; las pruebas estadísticas se aplican a los `R_i` del generador base, porque todas las pruebas están definidas para `U(0, 1)`.

**Período observado.** En la tabla comparativa se reporta la primera repetición de estado dentro de la secuencia generada. Por ejemplo, Cuadrados Medios con semilla 5731 entra en un ciclo de longitud 4 a partir de la iteración 71. `> n` indica que no se repitió ningún estado en los `n` números generados.

---

## Inicio Rápido (uso como biblioteca)

```python
import generador_numeros_pruebas as gnp

# Generador Congruencial Lineal con parámetros de período completo 2^32
gen = gnp.CongruencialLineal(x0=12345, a=1664525, c=1013904223, m=2**32)

# Verificar condiciones de período completo (Hull-Dobell)
es_valido, detalles = gen.validar_hull_dobell()
print("¿Cumple Hull-Dobell?:", es_valido)

# Generar 1000 números
xi, ri = gen.generar(1000)

# Validar la secuencia
print(gnp.PruebaMedias(ri).ejecutar())
```

---

## Uso de los generadores en simulaciones

### Los generadores conservan su estado

Todos los generadores recuerdan en qué punto de la secuencia van. Cada llamada a `generar()` o `siguiente()` **continúa** donde quedó la anterior; no vuelve a empezar desde la semilla.

```python
gen = gnp.CongruencialLineal(x0=12345, a=1664525, c=1013904223, m=2**32)

xi, ri = gen.generar(5)   # R_1 ... R_5
r6 = gen.siguiente()      # R_6
xi, ri = gen.generar(5)   # R_7 ... R_11

gen.reiniciar()           # Vuelve a x0 = 12345
gen.reiniciar(x0=999)     # Cambia la semilla y reinicia
```

### Métodos comunes a todos los generadores

| Método | Descripción | Retorna |
| :--- | :--- | :--- |
| `generar(cantidad)` | Genera `cantidad` números a partir del estado actual. | `(xi_list, ri_list)`: `xi_list` contiene el estado previo seguido de los enteros generados (`len = cantidad + 1`; en la primera llamada `xi_list[0]` es la semilla). `ri_list` contiene los `R_i` (`len = cantidad`). |
| `siguiente()` | Genera un único número y avanza el estado. Útil cuando no se sabe de antemano cuántos números se necesitan (p. ej., EpiSim). | `float` (`R_i`) |
| `reiniciar(semilla=None)` | Regresa a la semilla original, o fija una nueva semilla y reinicia. | — |

### ¿`generar()` o `siguiente()`?

- **`generar(n)`**: cuando se conoce la cantidad de números necesaria (p. ej., 1.000.000 de pasos de una caminata aleatoria). Es más rápido que llamar `siguiente()` n veces, pero guarda las listas completas en memoria (≈ 70 MB por cada millón de números).
- **`siguiente()`**: cuando la cantidad depende del estado de la simulación (p. ej., número de contactos según infectados del día). No acumula memoria.

### Varias simulaciones independientes

Cada réplica debe usar una semilla distinta. Las semillas pueden leerse desde archivo:

```python
from generador_numeros_pruebas.utilidades import ArchivoManager

semillas = ArchivoManager.leer_semillas("semillas.txt")
gen = gnp.CongruencialLineal(x0=semillas[0], a=1664525, c=1013904223, m=2**32)

for s in semillas:
    gen.reiniciar(x0=s)
    # ... ejecutar una simulación usando gen.siguiente() o gen.generar(n)
```

### Parámetros recomendados

| Generador | Parámetros | Período | Uso recomendado |
| :--- | :--- | :--- | :--- |
| Congruencial Lineal (Numerical Recipes) | `a=1664525, c=1013904223, m=2**32` | 2³² ≈ 4.3 × 10⁹ | Simulaciones grandes (puntos 2 y 4) |
| Congruencial Multiplicativo (MINSTD, Park & Miller) | `a=16807, m=2**31 - 1`, `x0` en `[1, m-1]` | m − 1 ≈ 2.1 × 10⁹ | Simulaciones grandes (puntos 2 y 4) |
| Congruencial Lineal (parametrización de clase) | `desde_parametros_clase(x0, k, c, g)` → `a = 1+2k`, `m = 2^g` | hasta 2^g | Ejemplos didácticos |
| Cuadrados Medios | `n_digitos=4` | muy corto (decenas a miles) | Solo fines didácticos |

> **El período debe ser mucho mayor que la cantidad de números que usa la simulación.** Por ejemplo, un LCG con `m=1024` repite exactamente la misma secuencia cada 1024 números: en una caminata de 1.000.000 de pasos, el mismo patrón se repetiría casi 1000 veces. Del mismo modo, Cuadrados Medios con semilla 5731 entra en un ciclo de longitud 4 después de 71 iteraciones (verificable con `detectar_ciclo()`).

> **Normalización.** Por defecto `R_i = x_i / m ∈ [0, 1)`. La opción `normalizar_con_m_menos_1=True` usa `x_i / (m−1)` y puede producir `R_i = 1.0`, lo cual rompe cálculos como `int(R_i * n)` para escoger un índice. Para simulación se recomienda dejar el valor por defecto.

---

## Referencia de generadores

### `CuadradosMedios(x0, n_digitos=4)`

Método de Von Neumann: eleva `x_i` al cuadrado, rellena con ceros a `2n` dígitos y extrae los `n` dígitos centrales. `R_i = x_{i+1} / 10^n`.

| Parámetro | Tipo | Descripción |
| :--- | :--- | :--- |
| `x0` | `int` | Semilla inicial (≥ 0). |
| `n_digitos` | `int` | Número de dígitos de la semilla (típicamente 4, 6, 8 o 10). |

Método adicional: `detectar_ciclo(max_iter=10000)` → `(longitud_ciclo, inicio_ciclo)` o `(None, None)`. Siempre parte de `x0` y no altera el estado del generador.

```python
gen = gnp.CuadradosMedios(x0=2222, n_digitos=4)
xi, ri = gen.generar(3)   # ri = [0.9372, 0.8343, 0.6056]
```

### `CongruencialLineal(x0, a, c, m, normalizar_con_m_menos_1=False)`

`x_{i+1} = (a·x_i + c) mod m`.

| Parámetro | Tipo | Descripción |
| :--- | :--- | :--- |
| `x0` | `int` | Semilla, `0 ≤ x0 < m`. |
| `a` | `int` | Multiplicador, `0 < a < m`. |
| `c` | `int` | Incremento, `0 ≤ c < m` (idealmente `gcd(c, m) = 1`). |
| `m` | `int` | Módulo. |
| `normalizar_con_m_menos_1` | `bool` | Si `True`, `R_i = x_i/(m−1)`. |

Métodos adicionales:
- `desde_parametros_clase(x0, k, c, g)` (constructor): usa `a = 1 + 2k` y `m = 2^g`.
- `validar_hull_dobell()` → `(cumple_todo, detalles)`: verifica las tres condiciones del teorema de Hull-Dobell para período completo `m`.

### `CongruencialMultiplicativo(x0, a, m, normalizar_con_m_menos_1=False)`

`x_{i+1} = (a·x_i) mod m`.

| Parámetro | Tipo | Descripción |
| :--- | :--- | :--- |
| `x0` | `int` | Semilla, `1 ≤ x0 < m`, `gcd(x0, m) = 1` (se valida). |
| `a` | `int` | Multiplicador, `1 < a < m`. Para período máximo con `m` primo, `a` debe ser raíz primitiva módulo `m`. |
| `m` | `int` | Módulo (típicamente primo o potencia de 2). |
| `normalizar_con_m_menos_1` | `bool` | Si `True`, `R_i = x_i/(m−1)`. |

### `CongruencialAditivo(semillas_iniciales, j, k, m)`

Fibonacci retrasado: `x_n = (x_{n−j} + x_{n−k}) mod m`, `R_i = x_n / m`.

| Parámetro | Tipo | Descripción |
| :--- | :--- | :--- |
| `semillas_iniciales` | `list[int]` | Al menos `k` semillas. |
| `j` | `int` | Retardo menor, `j ≥ 1`. |
| `k` | `int` | Retardo mayor, `k > j`. |
| `m` | `int` | Módulo. |

Métodos adicionales:
- `desde_lcg(x0, a, c, m_lcg, j, k, m, n_semillas=None)` (constructor): genera las semillas iniciales con un congruencial lineal.
- `reiniciar(semillas_iniciales=None)`: recibe una lista de semillas en lugar de un único valor.

---

## Transformaciones

Funciones que convierten una lista de `R_i ~ U(0,1)` en otras distribuciones. Se importan desde el paquete raíz.

| Función | Fórmula | Parámetros | Notas |
| :--- | :--- | :--- | :--- |
| `uniforme(ri_list, a, b)` | `N_i = a + (b − a)·R_i` | `a < b` | Retorna `len(ri_list)` valores. |
| `normal_box_muller(ri_list, mu=0.0, sigma=1.0)` | `Z₁ = √(−2 ln R₁)·cos(2πR₂)`, `Z₂ = √(−2 ln R₁)·sin(2πR₂)` | `mu`, `sigma` | Consume los `R_i` en pares; si la lista es impar se descarta el último. |
| `exponencial(ri_list, lambd=1.0)` | `N_i = −(1/λ)·ln(R_i)` | `lambd > 0` | Transformada inversa. |

```python
ni_unif = gnp.uniforme(ri, a=0.3, b=0.5)
ni_norm = gnp.normal_box_muller(ri, mu=100, sigma=15)
ni_exp  = gnp.exponencial(ri, lambd=2.5)

# Un solo valor U(a, b) dentro de una simulación:
beta = gnp.uniforme([gen.siguiente()], 0.3, 0.5)[0]
```

---

## Pruebas estadísticas

Todas las pruebas operan exclusivamente sobre la secuencia normalizada `R_i ∈ [0, 1)` (no sobre `x_i` ni sobre números transformados). Se usan así: `Prueba(ri, ...).ejecutar()`, que retorna un objeto `ResultadoPrueba`.

| Clase | Parámetros | Propiedad evaluada |
| :--- | :--- | :--- |
| `PruebaMedias(ri, alpha=0.05)` | `alpha`: nivel de significancia | Aleatoriedad (Prop. I) |
| `PruebaVarianza(ri, alpha=0.05)` | `alpha` | Aleatoriedad (Prop. I) |
| `PruebaChi2(ri, k_intervalos=10, alpha=0.05, rango=(0.0, 1.0))` | `k_intervalos`: número de subintervalos | Uniformidad (Prop. II) |
| `PruebaKS(ri, alpha=0.05)` | `alpha` | Uniformidad (Prop. II) |
| `PruebaPoker(ri, alpha=0.05, n_digitos=5)` | `n_digitos`: decimales analizados | Independencia (Prop. III) |

```python
res_medias = gnp.PruebaMedias(ri, alpha=0.05).ejecutar()
res_var    = gnp.PruebaVarianza(ri, alpha=0.05).ejecutar()
res_chi2   = gnp.PruebaChi2(ri, k_intervalos=10, alpha=0.05).ejecutar()
res_ks     = gnp.PruebaKS(ri, alpha=0.05).ejecutar()
res_poker  = gnp.PruebaPoker(ri, alpha=0.05).ejecutar()
print(res_medias)
```

> La prueba de Póker analiza 5 decimales. Con Cuadrados Medios de 4 dígitos, `R_i` tiene solo 4 decimales y el quinto siempre es 0, lo que sesga el resultado.

### `ResultadoPrueba`

| Atributo | Descripción |
| :--- | :--- |
| `nombre` | Nombre de la prueba. |
| `aprobada` | `True` si no se rechaza H₀. |
| `estadistico` | Valor calculado del estadístico. |
| `valor_critico` | Valor de referencia (crítico o esperado). |
| `limite_inferior`, `limite_superior` | Límites del intervalo de aceptación (si aplica). |
| `alpha` | Nivel de significancia usado. |
| `detalles` | `dict` con los datos intermedios de cada prueba (frecuencias, límites, etc.), usados por los gráficos. |

### Fundamento teórico

| Prueba | Estadístico | Criterio de aceptación de H₀ |
| :--- | :--- | :--- |
| **Medias** | $\bar{R} = \frac{1}{N}\sum R_i$ | $0.5 - Z_{\alpha/2}\frac{1}{\sqrt{12N}} \le \bar{R} \le 0.5 + Z_{\alpha/2}\frac{1}{\sqrt{12N}}$ |
| **Varianza** | $S^2 = \frac{1}{N-1}\sum (R_i - \bar{R})^2$ | $\frac{\chi^2_{\alpha/2, N-1}}{12(N-1)} \le S^2 \le \frac{\chi^2_{1-\alpha/2, N-1}}{12(N-1)}$ |
| **Chi-Cuadrado** | $\chi_0^2 = \sum_{i=1}^k \frac{(O_i - E_i)^2}{E_i}$ | $\chi_0^2 \le \chi^2_{1-\alpha, k-1}$ |
| **Kolmogorov-Smirnov** | $D = \max(D^+, D^-)$ | $D \le D_{\alpha, N}$ |
| **Póker** | $\chi_0^2 = \sum_{i=1}^7 \frac{(O_i - E_i)^2}{E_i}$ | $\chi_0^2 \le \chi^2_{1-\alpha, 6}$ (D, O, T, K, F, P, Q) |

---

## Gestión de Archivos (`ArchivoManager`)

```python
from generador_numeros_pruebas.utilidades import ArchivoManager
```

| Método | Descripción |
| :--- | :--- |
| `leer_semillas(ruta)` | Lee enteros desde `.txt` o `.csv`. Acepta separadores coma, punto y coma, tabulador o salto de línea; ignora líneas vacías y comentarios que empiezan con `#`. Retorna `list[int]`. |
| `leer_secuencia_ri(ruta)` | Igual que el anterior, pero lee flotantes `R_i`. Retorna `list[float]`. |
| `exportar_csv(ruta, ri_list, xi_list=None, ni_list=None)` | Exporta una tabla con columnas `i, Xi, Ri, Ni` (las opcionales solo si se pasan). |
| `exportar_txt(ruta, ri_list)` | Exporta un `R_i` por línea. |

```python
semillas = ArchivoManager.leer_semillas("semillas.txt")
ArchivoManager.exportar_csv("resultados.csv", ri_list=ri, xi_list=xi, ni_list=ni_unif)
```

---

## Generación de Gráficos (`Visualizacion`)

```python
from generador_numeros_pruebas.utilidades import Visualizacion
```

Todos los métodos aceptan `guardar_en="archivo.png"` (guarda a 300 dpi) y `mostrar`:
`True` muestra la figura de inmediato, `False` la cierra tras guardarla y `None` la deja abierta para mostrar varias juntas después con `plt.show()`.

| Método | Gráfico |
| :--- | :--- |
| `histograma_generacion(datos, titulo, bins=20, densidad_teorica=None, etiqueta_teorica=...)` | Histograma de la distribución alcanzada. Si se pasa `densidad_teorica` (una función `f(x)`), se superpone la curva esperada. |
| `prueba_medias(resultado, ri=None, n_subgrupos=20)` | Con `ri`: divide la secuencia en subgrupos y muestra (a) el intervalo de confianza de la media de cada subgrupo frente a μ = 0.5 y (b) el histograma de las medias con su densidad teórica N(0.5, 1/(12b)), la región de aceptación y la media global. Sin `ri`: resumen en barras. |
| `prueba_varianza(resultado, ri=None, n_subgrupos=20)` | Con `ri`: (a) intervalo de confianza χ² de la varianza de cada subgrupo frente a 1/12 y (b) histograma de las varianzas con la región de aceptación y la varianza global. Sin `ri`: resumen en barras. |
| `prueba_chi2(resultado)` | Frecuencias observadas vs. esperadas por intervalo. |
| `prueba_ks(resultado)` | Función empírica acumulada vs. F(x) = x, destacando D_max. |
| `prueba_poker(resultado)` | Frecuencias observadas vs. esperadas por mano. |

```python
Visualizacion.histograma_generacion(ri, titulo="Congruencial Lineal", guardar_en="hist.png")
Visualizacion.prueba_medias(res_medias, ri=ri, n_subgrupos=20, guardar_en="medias.png")
Visualizacion.prueba_chi2(res_chi2, guardar_en="chi2.png", mostrar=False)
```

---

## Cuadro técnico del entorno de desarrollo

| Elemento | Especificación |
| :--- | :--- |
| Lenguaje | Python 3.14.7 |
| Librerías | NumPy 2.5.3, SciPy 1.18.1, Matplotlib 3.11.2 |
| Sistema operativo | Windows 11 Home Single Language (versión 10.0.26200), 64 bits |
| Procesador | Intel Ultra 7 155H (16 núcleos, 22 hilos) |
| Memoria RAM | 24 GB (23.7 GB utilizables) |
