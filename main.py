"""
Interfaz de consola del módulo de generación y validación de números pseudoaleatorios.

Permite:
    - Cargar semillas desde archivo plano (.txt / .csv) o ingresarlas manualmente.
    - Seleccionar uno o varios métodos de generación y configurar sus parámetros.
    - Ver las secuencias generadas en tablas y exportarlas a .csv.
    - Seleccionar una o varias pruebas estadísticas y ejecutarlas.
    - Generar histogramas y gráficos de cada prueba (se guardan en la carpeta de salida).
    - Comparar todos los métodos seleccionados en una tabla resumen exportable.

Uso:
    python main.py            → menú interactivo
    python main.py --demo     → ejecuta la demostración completa sin preguntas
"""
import csv
import math
import os
import sys
import time

import matplotlib
import matplotlib.pyplot as plt

# Permite ejecutar este archivo directamente (python main.py) incluso si
# la carpeta fue renombrada (por ejemplo a 'punto_3') o importando el
# paquete desde su carpeta padre.
DIR_PAQUETE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(DIR_PAQUETE))
sys.path.insert(0, DIR_PAQUETE)

if "generador_numeros_pruebas" not in sys.modules:
    try:
        import generador_numeros_pruebas as gnp
    except ModuleNotFoundError:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "generador_numeros_pruebas",
            os.path.join(DIR_PAQUETE, "__init__.py"),
            submodule_search_locations=[DIR_PAQUETE],
        )
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            sys.modules["generador_numeros_pruebas"] = mod
            spec.loader.exec_module(mod)
        import generador_numeros_pruebas as gnp
else:
    import generador_numeros_pruebas as gnp

from generador_numeros_pruebas.utilidades import ArchivoManager, Visualizacion

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass


# ════════════════════════════════════════════════════════════════════════
#  Catálogos de métodos y pruebas
# ════════════════════════════════════════════════════════════════════════

# Cada método se identifica con una clave corta. Los métodos "uniforme" y
# "normal" son transformaciones: usan como base un Congruencial Lineal.
METODOS = {
    "cm": "Cuadrados Medios",
    "lineal": "Congruencial Lineal (mixto)",
    "multiplicativo": "Congruencial Multiplicativo",
    "aditivo": "Congruencial Aditivo (Fibonacci retrasado)",
    "uniforme": "Uniforme U(a, b) (transformación)",
    "normal": "Normal N(μ, σ²) Box-Muller (transformación)",
}

PRUEBAS = {
    "medias": "Prueba de Medias",
    "varianza": "Prueba de Varianza",
    "chi2": "Prueba Chi-Cuadrado",
    "ks": "Prueba Kolmogorov-Smirnov",
    "poker": "Prueba de Póker",
}

# Parámetros por defecto. Los congruenciales usan parámetros de período largo.
PARAMETROS_DEFECTO = {
    "cm": {"n_digitos": 4},
    "lineal": {"a": 1664525, "c": 1013904223, "m": 2 ** 32},
    "multiplicativo": {"a": 16807, "m": 2 ** 31 - 1},
    "aditivo": {"j": 24, "k": 55, "m": 2 ** 32},
    "uniforme": {"a_unif": 0.0, "b_unif": 10.0},
    "normal": {"mu": 0.0, "sigma": 1.0},
}

# Parámetros del Congruencial Lineal base de las transformaciones y del
# generador de semillas iniciales del método aditivo.
LCG_BASE = {"a": 1664525, "c": 1013904223, "m": 2 ** 32}


class Estado:
    """Configuración y resultados de la sesión actual."""

    def __init__(self):
        self.semillas = [5731]
        self.origen_semillas = "valor por defecto"
        self.cantidad = 1000
        self.alpha = 0.05
        self.k_intervalos = 10
        self.n_subgrupos = 20
        self.mostrar_graficos = True
        self.carpeta_salida = os.path.join(DIR_PAQUETE, "salidas")
        # clave → {"semilla": int, **parametros}
        self.metodos = {}
        # clave → {"xi": list, "ri": list, "ni": list | None, "tiempo": float, "generador": obj}
        self.secuencias = {}
        # [(clave_metodo, clave_prueba, ResultadoPrueba)]
        self.resultados = []


# ════════════════════════════════════════════════════════════════════════
#  Utilidades de entrada por consola
# ════════════════════════════════════════════════════════════════════════

def pedir_texto(mensaje, defecto=None):
    sufijo = f" [{defecto}]" if defecto is not None else ""
    valor = input(f"{mensaje}{sufijo}: ").strip()
    return valor if valor else (str(defecto) if defecto is not None else "")


def pedir_numero(mensaje, defecto, tipo=int, minimo=None, maximo=None):
    """Pide un número hasta que sea válido. Enter acepta el valor por defecto."""
    while True:
        texto = pedir_texto(mensaje, defecto)
        try:
            # Permite escribir expresiones como 2**32 para el módulo
            valor = tipo(eval(texto, {"__builtins__": {}}, {})) if "*" in texto else tipo(texto)
        except Exception:
            print("  ✗ Valor no válido, intente de nuevo.")
            continue
        if minimo is not None and valor < minimo:
            print(f"  ✗ Debe ser mayor o igual a {minimo}.")
            continue
        if maximo is not None and valor > maximo:
            print(f"  ✗ Debe ser menor o igual a {maximo}.")
            continue
        return valor


def pedir_si_no(mensaje, defecto=True):
    texto = pedir_texto(f"{mensaje} (s/n)", "s" if defecto else "n").lower()
    return texto.startswith("s")


def pedir_seleccion(catalogo, titulo):
    """
    Muestra un catálogo numerado y permite seleccionar varios elementos
    separados por coma (p. ej., "1,3,5") o "t" para todos.

    Returns:
        list[str]: Claves seleccionadas, en el orden del catálogo.
    """
    claves = list(catalogo)
    print(f"\n{titulo}")
    for i, clave in enumerate(claves, start=1):
        print(f"  {i}. {catalogo[clave]}")
    while True:
        texto = pedir_texto("Seleccione números separados por coma, o 't' para todos", "t").lower()
        if texto in ("t", "todos"):
            return claves
        try:
            indices = sorted({int(p) for p in texto.split(",") if p.strip()})
            if indices and all(1 <= i <= len(claves) for i in indices):
                return [claves[i - 1] for i in indices]
        except ValueError:
            pass
        print("  ✗ Selección no válida.")


def titulo(texto):
    print("\n" + "═" * 70)
    print(f"  {texto}")
    print("═" * 70)


def asegurar_carpeta(estado):
    os.makedirs(estado.carpeta_salida, exist_ok=True)
    return estado.carpeta_salida


# ════════════════════════════════════════════════════════════════════════
#  1. Semillas
# ════════════════════════════════════════════════════════════════════════

def menu_semillas(estado):
    titulo("Semillas")
    print(f"Semillas actuales ({estado.origen_semillas}): {estado.semillas}")
    print("  1. Ingresar semillas manualmente")
    print("  2. Cargar semillas desde archivo (.txt / .csv)")
    print("  0. Volver")
    opcion = pedir_texto("Opción", "0")

    if opcion == "1":
        texto = pedir_texto("Escriba las semillas separadas por coma (p. ej. 5731, 2222, 12345)")
        try:
            semillas = [int(p) for p in texto.replace(";", ",").split(",") if p.strip()]
        except ValueError:
            print("  ✗ Todas las semillas deben ser enteros.")
            return
        if not semillas or any(s < 0 for s in semillas):
            print("  ✗ Debe ingresar al menos una semilla entera no negativa.")
            return
        estado.semillas = semillas
        estado.origen_semillas = "ingreso manual"
    elif opcion == "2":
        ruta_defecto = os.path.join(DIR_PAQUETE, "ejemplos", "semillas.txt")
        ruta = pedir_texto("Ruta del archivo", ruta_defecto)
        cargar_semillas_archivo(estado, ruta)
        return
    else:
        return
    print(f"  ✓ {len(estado.semillas)} semilla(s) cargada(s): {estado.semillas}")


def cargar_semillas_archivo(estado, ruta):
    try:
        semillas = ArchivoManager.leer_semillas(ruta)
    except FileNotFoundError as e:
        print(f"  ✗ {e}")
        return False
    semillas = [s for s in semillas if s >= 0]
    if not semillas:
        print("  ✗ El archivo no contiene semillas enteras válidas.")
        return False
    estado.semillas = semillas
    estado.origen_semillas = f"archivo {os.path.basename(ruta)}"
    print(f"  ✓ {len(semillas)} semilla(s) cargada(s) desde {ruta}: {semillas}")
    return True


# ════════════════════════════════════════════════════════════════════════
#  2. Selección y configuración de métodos
# ════════════════════════════════════════════════════════════════════════

def menu_metodos(estado):
    titulo("Métodos de generación")
    seleccion = pedir_seleccion(METODOS, "Métodos disponibles:")
    configurar = pedir_si_no("¿Desea configurar los parámetros de cada método? "
                             "(si responde 'n' se usan los valores por defecto)", False)
    estado.metodos = {}
    for clave in seleccion:
        estado.metodos[clave] = configurar_metodo(clave, estado, interactivo=configurar)
    estado.secuencias = {}
    estado.resultados = []
    print(f"\n  ✓ Métodos seleccionados: {', '.join(METODOS[c] for c in seleccion)}")


def adaptar_semilla(clave, semilla, config):
    """
    Ajusta una semilla al rango válido del método según sus parámetros
    (p. ej., módulo 10^n en Cuadrados Medios o módulo m en los congruenciales).
    """
    if clave == "cm":
        return semilla % 10 ** config["n_digitos"]
    if clave == "lineal":
        return semilla % config["m"]
    if clave == "multiplicativo":
        x0 = semilla % config["m"]
        if x0 == 0 or math.gcd(x0, config["m"]) != 1:
            raise ValueError(f"La semilla {semilla} no es válida para el Congruencial "
                             f"Multiplicativo: debe ser coprima con m = {config['m']}.")
        return x0
    # Aditivo, Uniforme y Normal: semilla del Congruencial Lineal auxiliar
    return semilla % LCG_BASE["m"]


def configurar_metodo(clave, estado, interactivo=True):
    config = dict(PARAMETROS_DEFECTO[clave])
    config["semilla"] = adaptar_semilla(clave, estado.semillas[0], config)
    if not interactivo:
        return config

    print(f"\n── {METODOS[clave]} (Enter = valor por defecto) ──")
    if clave == "cm":
        config["n_digitos"] = pedir_numero("  Número de dígitos n", config["n_digitos"], minimo=2)
        config["semilla"] = pedir_numero("  Semilla x0", config["semilla"] % 10 ** config["n_digitos"],
                                         minimo=1, maximo=10 ** config["n_digitos"] - 1)
    elif clave == "lineal":
        config["m"] = pedir_numero("  Módulo m (admite 2**32)", config["m"], minimo=2)
        config["a"] = pedir_numero("  Multiplicador a", config["a"], minimo=1, maximo=config["m"] - 1)
        config["c"] = pedir_numero("  Incremento c", config["c"], minimo=0, maximo=config["m"] - 1)
        config["semilla"] = pedir_numero("  Semilla x0", config["semilla"] % config["m"],
                                         minimo=0, maximo=config["m"] - 1)
    elif clave == "multiplicativo":
        config["m"] = pedir_numero("  Módulo m (admite 2**31-1)", config["m"], minimo=3)
        config["a"] = pedir_numero("  Multiplicador a", config["a"], minimo=2, maximo=config["m"] - 1)
        while True:
            config["semilla"] = pedir_numero("  Semilla x0 (coprima con m)",
                                             config["semilla"] % config["m"] or 1,
                                             minimo=1, maximo=config["m"] - 1)
            if math.gcd(config["semilla"], config["m"]) == 1:
                break
            print("  ✗ La semilla debe ser coprima con m.")
    elif clave == "aditivo":
        config["m"] = pedir_numero("  Módulo m", config["m"], minimo=2)
        config["j"] = pedir_numero("  Retardo menor j", config["j"], minimo=1)
        config["k"] = pedir_numero("  Retardo mayor k", config["k"], minimo=config["j"] + 1)
        config["semilla"] = pedir_numero("  Semilla del LCG que genera las k semillas iniciales",
                                         config["semilla"], minimo=0, maximo=LCG_BASE["m"] - 1)
    elif clave == "uniforme":
        config["a_unif"] = pedir_numero("  Límite inferior a", config["a_unif"], tipo=float)
        config["b_unif"] = pedir_numero("  Límite superior b", config["b_unif"], tipo=float,
                                        minimo=config["a_unif"] + 1e-12)
        config["semilla"] = pedir_numero("  Semilla del LCG base", config["semilla"],
                                         minimo=0, maximo=LCG_BASE["m"] - 1)
    elif clave == "normal":
        config["mu"] = pedir_numero("  Media μ", config["mu"], tipo=float)
        config["sigma"] = pedir_numero("  Desviación σ", config["sigma"], tipo=float, minimo=1e-12)
        config["semilla"] = pedir_numero("  Semilla del LCG base", config["semilla"],
                                         minimo=0, maximo=LCG_BASE["m"] - 1)
    return config


def crear_generador(clave, config, semillas):
    """Construye el generador correspondiente a un método configurado."""
    if clave == "cm":
        return gnp.CuadradosMedios(config["semilla"], config["n_digitos"])
    if clave == "lineal":
        return gnp.CongruencialLineal(config["semilla"], config["a"], config["c"], config["m"])
    if clave == "multiplicativo":
        return gnp.CongruencialMultiplicativo(config["semilla"], config["a"], config["m"])
    if clave == "aditivo":
        # Si el usuario cargó al menos k semillas se usan directamente;
        # si no, se generan las k semillas iniciales con un LCG.
        if len(semillas) >= config["k"]:
            return gnp.CongruencialAditivo([s % config["m"] for s in semillas],
                                           config["j"], config["k"], config["m"])
        return gnp.CongruencialAditivo.desde_lcg(
            config["semilla"], LCG_BASE["a"], LCG_BASE["c"], LCG_BASE["m"],
            config["j"], config["k"], config["m"])
    # Transformaciones: el generador base es un Congruencial Lineal
    return gnp.CongruencialLineal(config["semilla"], **LCG_BASE)


def descripcion_parametros(clave, config):
    if clave == "cm":
        return f"x0={config['semilla']}, n={config['n_digitos']}"
    if clave == "lineal":
        return f"x0={config['semilla']}, a={config['a']}, c={config['c']}, m={config['m']}"
    if clave == "multiplicativo":
        return f"x0={config['semilla']}, a={config['a']}, m={config['m']}"
    if clave == "aditivo":
        return f"j={config['j']}, k={config['k']}, m={config['m']}, semillas iniciales vía LCG x0={config['semilla']}"
    if clave == "uniforme":
        return f"U({config['a_unif']}, {config['b_unif']}), LCG base x0={config['semilla']}"
    return f"N({config['mu']}, {config['sigma']}²), LCG base x0={config['semilla']}"


# ════════════════════════════════════════════════════════════════════════
#  3. Generación y tablas
# ════════════════════════════════════════════════════════════════════════

def generar_secuencias(estado, silencioso=False):
    if not estado.metodos:
        print("  ✗ Primero seleccione al menos un método (opción 2).")
        return False
    estado.secuencias = {}
    estado.resultados = []
    for clave, config in estado.metodos.items():
        generador = crear_generador(clave, config, estado.semillas)
        inicio = time.perf_counter()
        xi, ri = generador.generar(estado.cantidad)
        ni = None
        if clave == "uniforme":
            ni = gnp.uniforme(ri, config["a_unif"], config["b_unif"])
        elif clave == "normal":
            ni = gnp.normal_box_muller(ri, config["mu"], config["sigma"])
        tiempo = time.perf_counter() - inicio
        estado.secuencias[clave] = {"xi": xi, "ri": ri, "ni": ni,
                                    "tiempo": tiempo, "generador": generador}
        if not silencioso:
            print(f"  ✓ {METODOS[clave]}: {len(ri)} números en {tiempo * 1000:.2f} ms "
                  f"({descripcion_parametros(clave, config)})")
    return True


def menu_generar(estado):
    titulo("Generación de secuencias")
    estado.cantidad = pedir_numero("Cantidad de números a generar por método", estado.cantidad, minimo=10)
    if not generar_secuencias(estado):
        return
    filas = pedir_numero("Filas a mostrar en cada tabla", 15, minimo=1)
    for clave in estado.secuencias:
        mostrar_tabla(estado, clave, filas)
    if pedir_si_no("¿Exportar las secuencias a CSV?", True):
        exportar_secuencias(estado)


def mostrar_tabla(estado, clave, filas=15):
    datos = estado.secuencias[clave]
    xi, ri, ni = datos["xi"], datos["ri"], datos["ni"]
    # En el aditivo, xi incluye las k semillas iniciales al comienzo
    desfase = len(xi) - len(ri)

    print(f"\n{METODOS[clave]}  ({descripcion_parametros(clave, estado.metodos[clave])})")
    encabezado = f"{'i':>6} | {'Xi':>14} | {'Ri':>10}"
    if ni is not None:
        encabezado += f" | {'Ni':>12}"
    print(encabezado)
    print("-" * len(encabezado))
    for i in range(min(filas, len(ri))):
        linea = f"{i + 1:>6} | {xi[i + desfase]:>14} | {ri[i]:>10.6f}"
        if ni is not None:
            linea += f" | {ni[i]:>12.6f}" if i < len(ni) else f" | {'—':>12}"
        print(linea)
    if len(ri) > filas:
        print(f"{'...':>6} | ({len(ri) - filas} filas más; exporte a CSV para ver la tabla completa)")


def exportar_secuencias(estado):
    carpeta = asegurar_carpeta(estado)
    for clave, datos in estado.secuencias.items():
        ruta = os.path.join(carpeta, f"secuencia_{clave}.csv")
        xi = datos["xi"]
        # Se exportan solo los Xi que corresponden a cada Ri
        xi_alineado = xi[len(xi) - len(datos["ri"]):]
        ArchivoManager.exportar_csv(ruta, datos["ri"], xi_list=xi_alineado, ni_list=datos["ni"])
        print(f"  ✓ Exportado: {ruta}")


# ════════════════════════════════════════════════════════════════════════
#  4. Pruebas estadísticas
# ════════════════════════════════════════════════════════════════════════

def ejecutar_prueba(clave_prueba, ri, estado):
    if clave_prueba == "medias":
        return gnp.PruebaMedias(ri, alpha=estado.alpha).ejecutar()
    if clave_prueba == "varianza":
        return gnp.PruebaVarianza(ri, alpha=estado.alpha).ejecutar()
    if clave_prueba == "chi2":
        return gnp.PruebaChi2(ri, k_intervalos=estado.k_intervalos, alpha=estado.alpha).ejecutar()
    if clave_prueba == "ks":
        return gnp.PruebaKS(ri, alpha=estado.alpha).ejecutar()
    return gnp.PruebaPoker(ri, alpha=estado.alpha).ejecutar()


def graficar_prueba(clave_prueba, resultado, ri, ruta, estado, mostrar):
    """Genera el gráfico de una prueba. Returns: matplotlib.figure.Figure"""
    if clave_prueba == "medias":
        return Visualizacion.prueba_medias(resultado, ri=ri, n_subgrupos=estado.n_subgrupos,
                                           guardar_en=ruta, mostrar=mostrar)
    if clave_prueba == "varianza":
        return Visualizacion.prueba_varianza(resultado, ri=ri, n_subgrupos=estado.n_subgrupos,
                                             guardar_en=ruta, mostrar=mostrar)
    if clave_prueba == "chi2":
        return Visualizacion.prueba_chi2(resultado, guardar_en=ruta, mostrar=mostrar)
    if clave_prueba == "ks":
        return Visualizacion.prueba_ks(resultado, guardar_en=ruta, mostrar=mostrar)
    return Visualizacion.prueba_poker(resultado, guardar_en=ruta, mostrar=mostrar)


def menu_pruebas(estado, pruebas=None, graficar=None, silencioso=False):
    if not silencioso:
        titulo("Pruebas estadísticas")
    if not estado.secuencias:
        print("  ✗ Primero genere las secuencias (opción 3).")
        return
    if pruebas is None:
        pruebas = pedir_seleccion(PRUEBAS, "Pruebas disponibles:")
    if graficar is None:
        graficar = pedir_si_no("¿Generar los gráficos de cada prueba?", True)

    carpeta = asegurar_carpeta(estado)
    mostrar = None if estado.mostrar_graficos else False
    estado.resultados = [r for r in estado.resultados if r[1] not in pruebas]

    for clave_metodo, datos in estado.secuencias.items():
        ri = datos["ri"]
        print(f"\n▶ {METODOS[clave_metodo]}")
        if clave_metodo in ("uniforme", "normal"):
            print("  (Las pruebas se aplican a los R_i del generador base, no a los N_i transformados)")
        for clave_prueba in pruebas:
            resultado = ejecutar_prueba(clave_prueba, ri, estado)
            estado.resultados.append((clave_metodo, clave_prueba, resultado))
            if not silencioso:
                print(resultado)
            else:
                marca = "APROBADA" if resultado.aprobada else "RECHAZADA"
                print(f"  {PRUEBAS[clave_prueba]:<28} {marca}")
            if graficar:
                ruta = os.path.join(carpeta, f"prueba_{clave_prueba}_{clave_metodo}.png")
                graficar_prueba(clave_prueba, resultado, ri, ruta, estado, mostrar)

        # Se muestran los gráficos de un método a la vez para no saturar la pantalla
        if graficar and estado.mostrar_graficos:
            print("  (Cierre las ventanas de los gráficos para continuar con el siguiente método)")
            plt.show()

    if graficar:
        print(f"\n  ✓ Gráficos guardados en: {carpeta}")


# ════════════════════════════════════════════════════════════════════════
#  5. Histogramas de generación
# ════════════════════════════════════════════════════════════════════════

def densidad_normal(mu, sigma):
    return lambda x: math.exp(-((x - mu) ** 2) / (2 * sigma ** 2)) / (sigma * math.sqrt(2 * math.pi))


def graficar_histograma(estado, clave, guardar_en=None, mostrar=None):
    """
    Histograma de un método con su densidad teórica superpuesta.
    Uniforme y Normal grafican los N_i transformados; el resto, los R_i.

    Returns:
        matplotlib.figure.Figure
    """
    datos = estado.secuencias[clave]
    config = estado.metodos[clave]
    if clave == "uniforme":
        a, b = config["a_unif"], config["b_unif"]
        datos_hist = datos["ni"]
        teorica, etiqueta = (lambda x: 1.0 / (b - a)), f"Teórica U({a}, {b})"
    elif clave == "normal":
        datos_hist = datos["ni"]
        teorica = densidad_normal(config["mu"], config["sigma"])
        etiqueta = f"Teórica N({config['mu']}, {config['sigma']}²)"
    else:
        datos_hist = datos["ri"]
        teorica, etiqueta = (lambda x: 1.0), "Teórica U(0, 1)"

    return Visualizacion.histograma_generacion(
        datos_hist,
        titulo=f"{METODOS[clave]} (n = {len(datos['ri'])})\n{descripcion_parametros(clave, config)}",
        bins=20, densidad_teorica=teorica, etiqueta_teorica=etiqueta,
        guardar_en=guardar_en, mostrar=mostrar)


def menu_histogramas(estado):
    titulo("Histogramas de generación")
    if not estado.secuencias:
        print("  ✗ Primero genere las secuencias (opción 3).")
        return
    carpeta = asegurar_carpeta(estado)
    mostrar = None if estado.mostrar_graficos else False

    for clave in estado.secuencias:
        ruta = os.path.join(carpeta, f"histograma_{clave}.png")
        graficar_histograma(estado, clave, guardar_en=ruta, mostrar=mostrar)
        print(f"  ✓ {ruta}")

    if estado.mostrar_graficos:
        print("  (Cierre las ventanas de los gráficos para continuar)")
        plt.show()


# ════════════════════════════════════════════════════════════════════════
#  6. Comparación de métodos
# ════════════════════════════════════════════════════════════════════════

def periodo_observado(clave, datos):
    """
    Busca la primera repetición de estado dentro de la secuencia generada.
    Para el aditivo el estado son los últimos k valores, por lo que no se evalúa.
    """
    if clave == "aditivo":
        return "N/D"
    vistos = {}
    for i, x in enumerate(datos["xi"]):
        if x in vistos:
            return f"{i - vistos[x]} (desde i={vistos[x]})"
        vistos[x] = i
    return f"> {len(datos['xi']) - 1}"


ABREVIATURAS_PRUEBAS = {"medias": "Medias", "varianza": "Varianza", "chi2": "Chi²",
                        "ks": "KS", "poker": "Póker"}


def filas_comparacion(estado):
    """
    Construye la tabla comparativa con una fila por método generado.
    Las pruebas que no se hayan ejecutado quedan vacías.

    Returns:
        list[dict]: Filas con estadístico y veredicto de cada prueba, pruebas
                    aprobadas, tiempo de generación y período observado.
    """
    resultados = {(m, p): r for m, p, r in estado.resultados}
    filas = []
    for clave, datos in estado.secuencias.items():
        fila = {"metodo": METODOS[clave],
                "parametros": descripcion_parametros(clave, estado.metodos[clave])}
        aprobadas = ejecutadas = 0
        for p in PRUEBAS:
            r = resultados.get((clave, p))
            if r is None:
                fila[f"{p}_estadistico"] = ""
                fila[f"{p}_aprobada"] = ""
                continue
            ejecutadas += 1
            aprobadas += r.aprobada
            fila[f"{p}_estadistico"] = f"{r.estadistico:.6f}"
            fila[f"{p}_aprobada"] = "SI" if r.aprobada else "NO"
        fila.update({"pruebas_aprobadas": f"{aprobadas}/{ejecutadas}",
                     "tiempo_ms": f"{datos['tiempo'] * 1000:.3f}",
                     "periodo_observado": periodo_observado(clave, datos)})
        filas.append(fila)
    return filas


def exportar_comparacion(estado, ruta):
    filas = filas_comparacion(estado)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(filas[0]))
        writer.writeheader()
        writer.writerows(filas)


def menu_comparacion(estado, exportar=None):
    titulo("Comparación de métodos")
    if not estado.secuencias:
        print("  ✗ Primero genere las secuencias (opción 3).")
        return
    pruebas_hechas = {p for _, p, _ in estado.resultados}
    faltantes = [p for p in PRUEBAS if p not in pruebas_hechas]
    if faltantes:
        print("Ejecutando las pruebas que aún no se han corrido (sin gráficos)...")
        menu_pruebas(estado, pruebas=faltantes, graficar=False, silencioso=True)

    encabezado = f"{'Método':<30}" + "".join(f"{ABREVIATURAS_PRUEBAS[p]:>10}" for p in PRUEBAS) \
        + f"{'Aprob.':>8}{'Tiempo(ms)':>12}  Período observado"
    print("\n" + encabezado)
    print("-" * len(encabezado))

    for fila in filas_comparacion(estado):
        celdas = "".join(f"{'✓' if fila[f'{p}_aprobada'] == 'SI' else '✗':>10}" for p in PRUEBAS)
        print(f"{fila['metodo'][:29]:<30}{celdas}{fila['pruebas_aprobadas']:>8}"
              f"{float(fila['tiempo_ms']):>12.2f}  {fila['periodo_observado']}")

    print(f"\nn = {estado.cantidad}, α = {estado.alpha}. "
          "Uniforme y Normal se validan sobre los R_i de su LCG base.")

    if exportar is None:
        exportar = pedir_si_no("¿Exportar la tabla comparativa a CSV?", True)
    if exportar:
        ruta = os.path.join(asegurar_carpeta(estado), "comparacion_metodos.csv")
        exportar_comparacion(estado, ruta)
        print(f"  ✓ Exportado: {ruta}")


# ════════════════════════════════════════════════════════════════════════
#  7. Configuración general
# ════════════════════════════════════════════════════════════════════════

def menu_configuracion(estado):
    titulo("Configuración general")
    estado.cantidad = pedir_numero("Cantidad de números por método", estado.cantidad, minimo=10)
    estado.alpha = pedir_numero("Nivel de significancia α", estado.alpha, tipo=float,
                                minimo=0.001, maximo=0.5)
    estado.k_intervalos = pedir_numero("Intervalos k para Chi-cuadrado", estado.k_intervalos, minimo=2)
    estado.n_subgrupos = pedir_numero("Subgrupos para los gráficos de medias y varianza",
                                      estado.n_subgrupos, minimo=2)
    estado.mostrar_graficos = pedir_si_no("¿Mostrar los gráficos en pantalla además de guardarlos?",
                                          estado.mostrar_graficos)
    estado.carpeta_salida = pedir_texto("Carpeta de salida", estado.carpeta_salida)


# ════════════════════════════════════════════════════════════════════════
#  Demostración completa (no interactiva)
# ════════════════════════════════════════════════════════════════════════

def demostracion(estado):
    """
    Ejecuta el flujo completo con valores por defecto: carga el archivo de
    semillas de ejemplo, genera con todos los métodos, ejecuta las 5 pruebas,
    guarda todos los gráficos y exporta las tablas.
    """
    titulo("Demostración completa")
    mostrar_original = estado.mostrar_graficos
    estado.mostrar_graficos = False
    ruta = os.path.join(DIR_PAQUETE, "ejemplos", "semillas.txt")
    cargar_semillas_archivo(estado, ruta)

    estado.metodos = {c: configurar_metodo(c, estado, interactivo=False) for c in METODOS}
    print(f"\nGenerando {estado.cantidad} números con cada método...")
    generar_secuencias(estado)
    for clave in estado.secuencias:
        mostrar_tabla(estado, clave, filas=5)
    exportar_secuencias(estado)

    print("\nHistogramas:")
    menu_histogramas(estado)

    print("\nPruebas estadísticas:")
    menu_pruebas(estado, pruebas=list(PRUEBAS), graficar=True, silencioso=True)

    menu_comparacion(estado, exportar=True)
    estado.mostrar_graficos = mostrar_original
    print(f"\n✓ Demostración terminada. Resultados en: {estado.carpeta_salida}")


# ════════════════════════════════════════════════════════════════════════
#  Menú principal
# ════════════════════════════════════════════════════════════════════════

def resumen_estado(estado):
    metodos = ", ".join(METODOS[c].split(" (")[0] for c in estado.metodos) or "ninguno"
    print(f"\n  Semillas: {estado.semillas[:5]}{' ...' if len(estado.semillas) > 5 else ''} "
          f"({estado.origen_semillas})")
    print(f"  Métodos: {metodos}")
    print(f"  n = {estado.cantidad} | α = {estado.alpha} | "
          f"Secuencias generadas: {'sí' if estado.secuencias else 'no'}")


def menu_principal():
    estado = Estado()
    if "--demo" in sys.argv:
        matplotlib.use("Agg")
        demostracion(estado)
        return

    opciones = {
        "1": ("Semillas (ingreso manual o desde archivo)", menu_semillas),
        "2": ("Seleccionar métodos de generación", menu_metodos),
        "3": ("Generar secuencias y ver tablas", menu_generar),
        "4": ("Seleccionar y ejecutar pruebas estadísticas", menu_pruebas),
        "5": ("Histogramas de generación", menu_histogramas),
        "6": ("Comparar métodos (tabla resumen)", menu_comparacion),
        "7": ("Configuración general", menu_configuracion),
        "8": ("Demostración completa (todo automático)", demostracion),
    }
    while True:
        titulo("GENERADOR Y VALIDADOR DE NÚMEROS PSEUDOALEATORIOS")
        resumen_estado(estado)
        print()
        for clave, (texto, _) in opciones.items():
            print(f"  {clave}. {texto}")
        print("  0. Salir")
        opcion = pedir_texto("\nOpción")
        if opcion == "0":
            print("Fin del programa.")
            break
        if opcion in opciones:
            try:
                opciones[opcion][1](estado)
            except ValueError as e:
                print(f"  ✗ Error: {e}")
        else:
            print("  ✗ Opción no válida.")


if __name__ == "__main__":
    try:
        menu_principal()
    except (KeyboardInterrupt, EOFError):
        print("\nFin del programa.")
