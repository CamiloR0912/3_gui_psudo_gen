"""
Interfaz gráfica (tkinter) del módulo de generación y validación de números
pseudoaleatorios.

Modos de uso:
    - Manual: se escriben las semillas separadas por coma.
    - Automático: se carga un archivo .txt o .csv con las semillas.

Luego se seleccionan los métodos de generación y las pruebas, y con el botón
"Generar y validar" se obtienen:
    - Pestaña "Secuencias": tabla i, Xi, Ri, Ni de cada método.
    - Pestaña "Resultados": tabla comparativa y detalle de cada prueba.
    - Pestaña "Gráficos": histogramas y gráficos de cada prueba.

Uso:
    python gui.py

La lógica de generación y validación se reutiliza de main.py; este archivo
solo contiene la interfaz.
"""
import os
import sys

DIR_PAQUETE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(DIR_PAQUETE))
sys.path.insert(0, DIR_PAQUETE)

import matplotlib
matplotlib.use("Agg")  # Las figuras se incrustan en la ventana, no en ventanas aparte

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import main as nucleo
from main import METODOS, PRUEBAS, PARAMETROS_DEFECTO, ABREVIATURAS_PRUEBAS
from generador_numeros_pruebas.utilidades import ArchivoManager


# Nombres legibles de los parámetros de cada método
ETIQUETAS_PARAMETROS = {
    "n_digitos": "Número de dígitos (n)",
    "a": "Multiplicador (a)",
    "c": "Incremento (c)",
    "m": "Módulo (m)",
    "j": "Retardo menor (j)",
    "k": "Retardo mayor (k)",
    "a_unif": "Límite inferior (a)",
    "b_unif": "Límite superior (b)",
    "mu": "Media (μ)",
    "sigma": "Desviación estándar (σ)",
}

FILAS_MAXIMAS_TABLA = 2000
OPCION_HISTOGRAMA = "Histograma de generación"


def convertir_numero(texto, tipo):
    """
    Convierte un texto a int o float. Acepta potencias como 2**32 o 2**31-1
    para facilitar el ingreso de módulos grandes.
    """
    texto = texto.strip()
    if "*" in texto:
        # Solo se permiten dígitos y operadores aritméticos básicos
        if not all(ch in "0123456789+-*/(). " for ch in texto):
            raise ValueError(f"Expresión no válida: {texto}")
        return tipo(eval(texto, {"__builtins__": {}}, {}))
    return tipo(texto)


class DialogoParametros(tk.Toplevel):
    """Ventana modal para editar los parámetros de un método de generación."""

    def __init__(self, padre, clave, parametros):
        super().__init__(padre)
        self.title(f"Parámetros - {METODOS[clave]}")
        self.resizable(False, False)
        self.transient(padre)
        self.clave = clave
        self.resultado = None
        self.entradas = {}

        marco = ttk.Frame(self, padding=15)
        marco.pack(fill="both", expand=True)
        ttk.Label(marco, text=METODOS[clave], font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        for fila, (nombre, valor) in enumerate(parametros.items(), start=1):
            ttk.Label(marco, text=ETIQUETAS_PARAMETROS.get(nombre, nombre)).grid(
                row=fila, column=0, sticky="w", padx=(0, 10), pady=3)
            var = tk.StringVar(value=str(valor))
            ttk.Entry(marco, textvariable=var, width=18).grid(row=fila, column=1, pady=3)
            self.entradas[nombre] = (var, type(valor))

        ttk.Label(marco, text="Se admiten potencias, p. ej. 2**32 o 2**31-1.",
                  foreground="gray").grid(row=len(parametros) + 1, column=0, columnspan=2,
                                          sticky="w", pady=(8, 0))

        botones = ttk.Frame(marco)
        botones.grid(row=len(parametros) + 2, column=0, columnspan=2, pady=(12, 0))
        ttk.Button(botones, text="Restaurar valores por defecto",
                   command=self._restaurar).pack(side="left", padx=4)
        ttk.Button(botones, text="Aceptar", command=self._aceptar).pack(side="left", padx=4)
        ttk.Button(botones, text="Cancelar", command=self.destroy).pack(side="left", padx=4)

        self.grab_set()
        self.wait_window(self)

    def _restaurar(self):
        for nombre, valor in PARAMETROS_DEFECTO[self.clave].items():
            self.entradas[nombre][0].set(str(valor))

    def _aceptar(self):
        nuevos = {}
        try:
            for nombre, (var, tipo) in self.entradas.items():
                nuevos[nombre] = convertir_numero(var.get(), tipo)
            self._validar(nuevos)
        except (ValueError, ZeroDivisionError) as e:
            messagebox.showerror("Parámetro no válido", str(e), parent=self)
            return

        # Advertencia de período incompleto para el Congruencial Lineal
        if self.clave == "lineal":
            import generador_numeros_pruebas as gnp
            cumple, detalles = gnp.CongruencialLineal(0, nuevos["a"], nuevos["c"],
                                                      nuevos["m"]).validar_hull_dobell()
            if not cumple:
                fallas = "\n".join(f"  ✗ {cond}" for cond, ok in detalles.items() if not ok)
                if not messagebox.askyesno(
                        "Hull-Dobell",
                        f"Los parámetros no cumplen el Teorema de Hull-Dobell:\n{fallas}\n\n"
                        "El período será menor que m. ¿Desea usarlos de todas formas?",
                        parent=self):
                    return
        self.resultado = nuevos
        self.destroy()

    def _validar(self, p):
        """Validaciones que no dependen de la semilla."""
        if self.clave == "cm" and p["n_digitos"] < 2:
            raise ValueError("El número de dígitos debe ser al menos 2.")
        if self.clave in ("lineal", "multiplicativo"):
            if p["m"] < 3:
                raise ValueError("El módulo m debe ser mayor que 2.")
            if not (0 < p["a"] < p["m"]):
                raise ValueError(f"El multiplicador a debe estar entre 1 y {p['m'] - 1}.")
        if self.clave == "lineal" and not (0 <= p["c"] < p["m"]):
            raise ValueError(f"El incremento c debe estar entre 0 y {p['m'] - 1}.")
        if self.clave == "multiplicativo" and p["a"] < 2:
            raise ValueError("El multiplicador a debe ser mayor que 1.")
        if self.clave == "aditivo":
            if p["j"] < 1 or p["k"] <= p["j"]:
                raise ValueError("Debe cumplirse 1 ≤ j < k.")
            if p["m"] < 2:
                raise ValueError("El módulo m debe ser mayor que 1.")
        if self.clave == "uniforme" and p["b_unif"] <= p["a_unif"]:
            raise ValueError("El límite superior b debe ser mayor que a.")
        if self.clave == "normal" and p["sigma"] <= 0:
            raise ValueError("La desviación estándar σ debe ser positiva.")


class Aplicacion(tk.Tk):
    """Ventana principal."""

    def __init__(self):
        super().__init__()
        self.title("Generador y Validador de Números Pseudoaleatorios - Simulación UPTC")
        self.geometry("1400x840")
        self.minsize(1150, 700)

        self.estado = nucleo.Estado()
        self.estado.mostrar_graficos = False
        self.parametros = {c: dict(PARAMETROS_DEFECTO[c]) for c in METODOS}
        self.figura_actual = None
        self.canvas_actual = None
        self.toolbar_actual = None

        self._construir_barra_estado()
        self._construir_panel_control()
        self._construir_pestanas()
        self._cargar_semillas_manual(silencioso=True)

    # ════════════════════════════════════════════════════════════════════
    #  Construcción de la interfaz
    # ════════════════════════════════════════════════════════════════════

    def _construir_panel_control(self):
        panel = ttk.Frame(self, padding=10)
        panel.pack(side="left", fill="y")

        # ── 1. Semillas ──
        marco = ttk.LabelFrame(panel, text=" 1. Semillas ", padding=8)
        marco.pack(fill="x", pady=(0, 8))

        self.modo = tk.StringVar(value="manual")
        ttk.Radiobutton(marco, text="Manual (separadas por coma)", value="manual",
                        variable=self.modo).grid(row=0, column=0, columnspan=2, sticky="w")
        self.texto_semillas = tk.StringVar(value="5731, 2222, 5678, 12345")
        entrada = ttk.Entry(marco, textvariable=self.texto_semillas, width=34)
        entrada.grid(row=1, column=0, sticky="we", padx=(18, 4))
        entrada.bind("<Return>", lambda e: self._cargar_semillas_manual())
        entrada.bind("<FocusIn>", lambda e: self.modo.set("manual"))
        ttk.Button(marco, text="Aplicar", width=8,
                   command=self._cargar_semillas_manual).grid(row=1, column=1)

        ttk.Radiobutton(marco, text="Automático (archivo .txt / .csv)", value="archivo",
                        variable=self.modo).grid(row=2, column=0, columnspan=2, sticky="w",
                                                 pady=(8, 0))
        self.ruta_archivo = tk.StringVar(value="Ningún archivo seleccionado")
        ttk.Label(marco, textvariable=self.ruta_archivo, foreground="gray",
                  width=34).grid(row=3, column=0, sticky="w", padx=(18, 4))
        ttk.Button(marco, text="Examinar...", width=10,
                   command=self._cargar_semillas_archivo).grid(row=3, column=1)

        ttk.Separator(marco).grid(row=4, column=0, columnspan=2, sticky="we", pady=8)
        ttk.Label(marco, text="Semilla a usar:").grid(row=5, column=0, sticky="w")
        self.combo_semilla = ttk.Combobox(marco, state="readonly", width=14)
        self.combo_semilla.grid(row=5, column=1, sticky="e")
        self.info_semillas = tk.StringVar()
        ttk.Label(marco, textvariable=self.info_semillas, foreground="#1C3F75",
                  wraplength=280).grid(row=6, column=0, columnspan=2, sticky="w", pady=(4, 0))

        # ── 2. Métodos ──
        marco = ttk.LabelFrame(panel, text=" 2. Métodos de generación ", padding=8)
        marco.pack(fill="x", pady=(0, 8))
        self.vars_metodos = {}
        for fila, (clave, nombre) in enumerate(METODOS.items()):
            var = tk.BooleanVar(value=clave in ("cm", "lineal", "multiplicativo"))
            self.vars_metodos[clave] = var
            ttk.Checkbutton(marco, text=nombre.replace(" (transformación)", ""),
                            variable=var).grid(row=fila, column=0, sticky="w")
            ttk.Button(marco, text="Parámetros", width=11,
                       command=lambda c=clave: self._editar_parametros(c)).grid(
                row=fila, column=1, padx=(6, 0), pady=1)

        # ── 3. Pruebas ──
        marco = ttk.LabelFrame(panel, text=" 3. Pruebas estadísticas ", padding=8)
        marco.pack(fill="x", pady=(0, 8))
        self.vars_pruebas = {}
        for i, (clave, nombre) in enumerate(PRUEBAS.items()):
            var = tk.BooleanVar(value=True)
            self.vars_pruebas[clave] = var
            texto = "Kolmogorov-Smirnov" if clave == "ks" else ABREVIATURAS_PRUEBAS[clave]
            ttk.Checkbutton(marco, text=texto, variable=var).grid(
                row=i // 2, column=i % 2, sticky="w", padx=(0, 12))

        # ── 4. Configuración ──
        marco = ttk.LabelFrame(panel, text=" 4. Configuración ", padding=8)
        marco.pack(fill="x", pady=(0, 8))
        self.var_cantidad = tk.StringVar(value="1000")
        self.var_alpha = tk.StringVar(value="0.05")
        self.var_k = tk.StringVar(value="10")
        self.var_subgrupos = tk.StringVar(value="20")
        campos = [("Cantidad de números (n)", ttk.Entry(marco, textvariable=self.var_cantidad, width=10)),
                  ("Nivel de significancia α", ttk.Combobox(marco, textvariable=self.var_alpha, width=8,
                                                            values=["0.01", "0.05", "0.10"])),
                  ("Intervalos Chi² (k)", ttk.Entry(marco, textvariable=self.var_k, width=10)),
                  ("Subgrupos (medias/varianza)", ttk.Entry(marco, textvariable=self.var_subgrupos, width=10))]
        for fila, (texto, widget) in enumerate(campos):
            ttk.Label(marco, text=texto).grid(row=fila, column=0, sticky="w", pady=2)
            widget.grid(row=fila, column=1, sticky="e", padx=(10, 0))

        # ── Acciones ──
        estilo = ttk.Style(self)
        estilo.configure("Accion.TButton", font=("Segoe UI", 11, "bold"), padding=8)
        ttk.Button(panel, text="▶  Generar y validar", style="Accion.TButton",
                   command=self._ejecutar).pack(fill="x", pady=(4, 6))
        ttk.Button(panel, text="Exportar tablas a CSV...",
                   command=self._exportar_csv).pack(fill="x", pady=2)
        ttk.Button(panel, text="Guardar todos los gráficos...",
                   command=self._guardar_graficos).pack(fill="x", pady=2)

    def _construir_pestanas(self):
        self.pestanas = ttk.Notebook(self)
        self.pestanas.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=10)

        # ── Pestaña Secuencias ──
        tab = ttk.Frame(self.pestanas, padding=8)
        self.pestanas.add(tab, text="  Secuencias  ")
        barra = ttk.Frame(tab)
        barra.pack(fill="x", pady=(0, 6))
        ttk.Label(barra, text="Método:").pack(side="left")
        self.combo_tabla = ttk.Combobox(barra, state="readonly", width=45)
        self.combo_tabla.pack(side="left", padx=6)
        self.combo_tabla.bind("<<ComboboxSelected>>", lambda e: self._mostrar_tabla())
        self.info_tabla = tk.StringVar()
        ttk.Label(barra, textvariable=self.info_tabla, foreground="gray").pack(side="left", padx=10)

        self.tabla = self._crear_treeview(tab, ["i", "Xi", "Ri", "Ni"], [80, 200, 160, 160])

        # ── Pestaña Resultados ──
        tab = ttk.Frame(self.pestanas, padding=8)
        self.pestanas.add(tab, text="  Resultados  ")
        ttk.Label(tab, text="Comparación de métodos", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        columnas = ["Método"] + [ABREVIATURAS_PRUEBAS[p] for p in PRUEBAS] \
            + ["Aprobadas", "Tiempo (ms)", "Período observado"]
        anchos = [260] + [70] * len(PRUEBAS) + [80, 90, 150]
        marco = ttk.Frame(tab, height=190)
        marco.pack(fill="x", pady=(4, 10))
        marco.pack_propagate(False)
        self.tabla_comparacion = self._crear_treeview(marco, columnas, anchos)

        ttk.Label(tab, text="Detalle de las pruebas (doble clic para ver el gráfico)",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.tabla_detalle = self._crear_treeview(
            tab, ["Método", "Prueba", "Estadístico", "Criterio de aceptación", "Resultado"],
            [260, 190, 120, 260, 110])
        self.tabla_detalle.bind("<Double-1>", self._abrir_grafico_desde_detalle)
        ttk.Label(tab, foreground="gray",
                  text="Uniforme y Normal se validan sobre los R_i de su generador base "
                       "(Congruencial Lineal), ya que las pruebas están definidas para U(0, 1).").pack(
            anchor="w", pady=(6, 0))

        for tabla in (self.tabla_comparacion, self.tabla_detalle):
            tabla.tag_configure("aprobada", background="#E8F6EC")
            tabla.tag_configure("rechazada", background="#FDECEA")

        # ── Pestaña Gráficos ──
        tab = ttk.Frame(self.pestanas, padding=8)
        self.pestanas.add(tab, text="  Gráficos  ")
        barra = ttk.Frame(tab)
        barra.pack(fill="x", pady=(0, 6))
        ttk.Label(barra, text="Método:").pack(side="left")
        self.combo_graf_metodo = ttk.Combobox(barra, state="readonly", width=45)
        self.combo_graf_metodo.pack(side="left", padx=6)
        ttk.Label(barra, text="Gráfico:").pack(side="left", padx=(12, 0))
        self.combo_graf_tipo = ttk.Combobox(barra, state="readonly", width=32)
        self.combo_graf_tipo.pack(side="left", padx=6)
        self.combo_graf_metodo.bind("<<ComboboxSelected>>", lambda e: self._mostrar_grafico())
        self.combo_graf_tipo.bind("<<ComboboxSelected>>", lambda e: self._mostrar_grafico())
        self.marco_grafico = ttk.Frame(tab)
        self.marco_grafico.pack(fill="both", expand=True)
        self.aviso_grafico = ttk.Label(self.marco_grafico, foreground="gray",
                                       text="Presione «Generar y validar» para ver los gráficos.")
        self.aviso_grafico.pack(expand=True)

    def _crear_treeview(self, padre, columnas, anchos):
        marco = ttk.Frame(padre)
        marco.pack(fill="both", expand=True)
        tabla = ttk.Treeview(marco, columns=columnas, show="headings")
        for col, ancho in zip(columnas, anchos):
            tabla.heading(col, text=col)
            tabla.column(col, width=ancho, anchor="w" if col in ("Método", "Prueba") else "center")
        barra_v = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
        barra_h = ttk.Scrollbar(marco, orient="horizontal", command=tabla.xview)
        tabla.configure(yscrollcommand=barra_v.set, xscrollcommand=barra_h.set)
        tabla.grid(row=0, column=0, sticky="nsew")
        barra_v.grid(row=0, column=1, sticky="ns")
        barra_h.grid(row=1, column=0, sticky="we")
        marco.rowconfigure(0, weight=1)
        marco.columnconfigure(0, weight=1)
        return tabla

    def _construir_barra_estado(self):
        self.mensaje_estado = tk.StringVar(value="Listo.")
        barra = ttk.Label(self, textvariable=self.mensaje_estado, relief="sunken",
                          anchor="w", padding=(8, 2))
        barra.pack(side="bottom", fill="x")

    def _estado(self, texto):
        self.mensaje_estado.set(texto)
        self.update_idletasks()

    # ════════════════════════════════════════════════════════════════════
    #  Semillas
    # ════════════════════════════════════════════════════════════════════

    def _aplicar_semillas(self, semillas, origen):
        self.estado.semillas = semillas
        self.estado.origen_semillas = origen
        # Se conserva la semilla elegida si sigue estando en la nueva lista
        anterior = self.combo_semilla.get()
        valores = [str(s) for s in semillas]
        self.combo_semilla["values"] = valores
        self.combo_semilla.current(valores.index(anterior) if anterior in valores else 0)
        vista = ", ".join(str(s) for s in semillas[:8]) + (" ..." if len(semillas) > 8 else "")
        self.info_semillas.set(f"{len(semillas)} semilla(s) desde {origen}: {vista}")

    def _cargar_semillas_manual(self, silencioso=False):
        self.modo.set("manual")
        texto = self.texto_semillas.get().replace(";", ",")
        try:
            semillas = [int(p) for p in texto.split(",") if p.strip()]
        except ValueError:
            messagebox.showerror("Semillas", "Las semillas deben ser números enteros separados por coma.")
            return
        if not semillas or any(s < 0 for s in semillas):
            messagebox.showerror("Semillas", "Ingrese al menos una semilla entera no negativa.")
            return
        self._aplicar_semillas(semillas, "ingreso manual")
        if not silencioso:
            self._estado(f"Se cargaron {len(semillas)} semilla(s) manualmente.")

    def _cargar_semillas_archivo(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo de semillas",
            initialdir=os.path.join(nucleo.DIR_PAQUETE, "ejemplos"),
            filetypes=[("Archivos de semillas", "*.txt *.csv"), ("Todos los archivos", "*.*")])
        if not ruta:
            return
        try:
            semillas = [s for s in ArchivoManager.leer_semillas(ruta) if s >= 0]
        except (OSError, UnicodeDecodeError) as e:
            messagebox.showerror("Semillas", f"No se pudo leer el archivo:\n{e}")
            return
        if not semillas:
            messagebox.showerror("Semillas", "El archivo no contiene semillas enteras válidas.")
            return
        self.modo.set("archivo")
        self.ruta_archivo.set(os.path.basename(ruta))
        self._aplicar_semillas(semillas, f"archivo {os.path.basename(ruta)}")
        self._estado(f"Se cargaron {len(semillas)} semilla(s) desde {ruta}")

    # ════════════════════════════════════════════════════════════════════
    #  Parámetros y ejecución
    # ════════════════════════════════════════════════════════════════════

    def _editar_parametros(self, clave):
        dialogo = DialogoParametros(self, clave, self.parametros[clave])
        if dialogo.resultado is not None:
            self.parametros[clave] = dialogo.resultado
            self.vars_metodos[clave].set(True)
            self._estado(f"Parámetros actualizados: {METODOS[clave]}")

    def _leer_configuracion(self):
        """Lee y valida la configuración general. Lanza ValueError si algo es inválido."""
        try:
            cantidad = int(self.var_cantidad.get())
            alpha = float(self.var_alpha.get())
            k = int(self.var_k.get())
            subgrupos = int(self.var_subgrupos.get())
        except ValueError:
            raise ValueError("La configuración contiene valores no numéricos.")
        if cantidad < 10:
            raise ValueError("La cantidad de números debe ser al menos 10.")
        if not (0 < alpha < 0.5):
            raise ValueError("El nivel de significancia α debe estar entre 0 y 0.5.")
        if k < 2:
            raise ValueError("El número de intervalos de Chi² debe ser al menos 2.")
        if subgrupos < 2:
            raise ValueError("El número de subgrupos debe ser al menos 2.")
        self.estado.cantidad = cantidad
        self.estado.alpha = alpha
        self.estado.k_intervalos = k
        self.estado.n_subgrupos = subgrupos

    def _ejecutar(self):
        # Si el modo es manual, se toman las semillas escritas en ese momento
        if self.modo.get() == "manual":
            self._cargar_semillas_manual(silencioso=True)
        metodos = [c for c, v in self.vars_metodos.items() if v.get()]
        pruebas = [p for p, v in self.vars_pruebas.items() if v.get()]
        if not metodos:
            messagebox.showwarning("Métodos", "Seleccione al menos un método de generación.")
            return

        try:
            self._leer_configuracion()
            semilla = int(self.combo_semilla.get())
            self.estado.metodos = {}
            for clave in metodos:
                config = dict(self.parametros[clave])
                config["semilla"] = nucleo.adaptar_semilla(clave, semilla, config)
                self.estado.metodos[clave] = config
        except ValueError as e:
            messagebox.showerror("Configuración", str(e))
            return

        self.config(cursor="watch")
        try:
            self._estado("Generando secuencias...")
            nucleo.generar_secuencias(self.estado, silencioso=True)
            for i, (clave, datos) in enumerate(self.estado.secuencias.items(), start=1):
                self._estado(f"Ejecutando pruebas: {METODOS[clave]} ({i}/{len(metodos)})...")
                for p in pruebas:
                    resultado = nucleo.ejecutar_prueba(p, datos["ri"], self.estado)
                    self.estado.resultados.append((clave, p, resultado))
        except (ValueError, ZeroDivisionError, OverflowError) as e:
            messagebox.showerror("Error durante la ejecución", str(e))
            self._estado("La ejecución terminó con errores.")
            return
        finally:
            self.config(cursor="")

        self._actualizar_vistas()
        aprobadas = sum(r.aprobada for _, _, r in self.estado.resultados)
        self._estado(f"Listo: {len(metodos)} método(s), n = {self.estado.cantidad}, semilla = {semilla}. "
                     f"Pruebas aprobadas: {aprobadas}/{len(self.estado.resultados)}.")

    # ════════════════════════════════════════════════════════════════════
    #  Vistas
    # ════════════════════════════════════════════════════════════════════

    def _actualizar_vistas(self):
        nombres = [METODOS[c] for c in self.estado.secuencias]
        for combo in (self.combo_tabla, self.combo_graf_metodo):
            combo["values"] = nombres
            combo.current(0)
        self._mostrar_tabla()
        self._mostrar_resultados()
        self.combo_graf_tipo["values"] = [OPCION_HISTOGRAMA] + [
            PRUEBAS[p] for p in PRUEBAS if any(pr == p for _, pr, _ in self.estado.resultados)]
        self.combo_graf_tipo.current(0)
        self._mostrar_grafico()

    def _clave_por_nombre(self, nombre, catalogo):
        return next(c for c, n in catalogo.items() if n == nombre)

    def _mostrar_tabla(self):
        clave = self._clave_por_nombre(self.combo_tabla.get(), METODOS)
        datos = self.estado.secuencias[clave]
        xi, ri, ni = datos["xi"], datos["ri"], datos["ni"]
        desfase = len(xi) - len(ri)  # El aditivo incluye las k semillas iniciales al inicio

        self.tabla.delete(*self.tabla.get_children())
        for i in range(min(len(ri), FILAS_MAXIMAS_TABLA)):
            valor_ni = f"{ni[i]:.6f}" if ni is not None and i < len(ni) else "—"
            self.tabla.insert("", "end", values=(i + 1, xi[i + desfase], f"{ri[i]:.6f}", valor_ni))

        nota = f" (se muestran {FILAS_MAXIMAS_TABLA}; exporte a CSV para verlas todas)" \
            if len(ri) > FILAS_MAXIMAS_TABLA else ""
        self.info_tabla.set(f"{nucleo.descripcion_parametros(clave, self.estado.metodos[clave])} | "
                            f"{len(ri)} números en {datos['tiempo'] * 1000:.2f} ms{nota}")

    def _mostrar_resultados(self):
        self.tabla_comparacion.delete(*self.tabla_comparacion.get_children())
        for fila in nucleo.filas_comparacion(self.estado):
            marcas = [{"SI": "✓", "NO": "✗"}.get(fila[f"{p}_aprobada"], "—") for p in PRUEBAS]
            aprob, total = fila["pruebas_aprobadas"].split("/")
            etiqueta = "aprobada" if total != "0" and aprob == total else "rechazada"
            self.tabla_comparacion.insert(
                "", "end", tags=(etiqueta,),
                values=[fila["metodo"]] + marcas + [fila["pruebas_aprobadas"], fila["tiempo_ms"],
                                                    fila["periodo_observado"]])

        self.tabla_detalle.delete(*self.tabla_detalle.get_children())
        for clave, p, r in self.estado.resultados:
            if r.limite_inferior is not None:
                criterio = f"{r.limite_inferior:.5f} ≤ estadístico ≤ {r.limite_superior:.5f}"
            else:
                criterio = f"estadístico ≤ {r.valor_critico:.5f}"
            self.tabla_detalle.insert(
                "", "end", tags=("aprobada" if r.aprobada else "rechazada",),
                values=(METODOS[clave], PRUEBAS[p], f"{r.estadistico:.5f}", criterio,
                        "APROBADA ✓" if r.aprobada else "RECHAZADA ✗"))

    def _abrir_grafico_desde_detalle(self, _evento):
        seleccion = self.tabla_detalle.selection()
        if not seleccion:
            return
        metodo, prueba = self.tabla_detalle.item(seleccion[0], "values")[:2]
        self.combo_graf_metodo.set(metodo)
        self.combo_graf_tipo.set(prueba)
        self.pestanas.select(2)
        self._mostrar_grafico()

    def _crear_figura(self, clave_metodo, tipo, guardar_en=None, mostrar=None):
        """Crea la figura de un histograma o de una prueba para un método."""
        if tipo == OPCION_HISTOGRAMA:
            return nucleo.graficar_histograma(self.estado, clave_metodo, guardar_en, mostrar)
        clave_prueba = self._clave_por_nombre(tipo, PRUEBAS)
        resultado = next(r for m, p, r in self.estado.resultados
                         if m == clave_metodo and p == clave_prueba)
        return nucleo.graficar_prueba(clave_prueba, resultado, self.estado.secuencias[clave_metodo]["ri"],
                                      guardar_en, self.estado, mostrar)

    def _mostrar_grafico(self):
        if not self.estado.secuencias:
            return
        clave = self._clave_por_nombre(self.combo_graf_metodo.get(), METODOS)
        figura = self._crear_figura(clave, self.combo_graf_tipo.get())

        # Se libera la figura anterior antes de mostrar la nueva
        self.aviso_grafico.pack_forget()
        if self.canvas_actual is not None:
            self.canvas_actual.get_tk_widget().destroy()
            self.toolbar_actual.destroy()
            plt.close(self.figura_actual)

        # Recalcula márgenes cada vez que la figura cambia de tamaño con la ventana
        figura.set_layout_engine("tight")
        self.figura_actual = figura
        self.canvas_actual = FigureCanvasTkAgg(figura, master=self.marco_grafico)
        # La barra de herramientas permite hacer zoom y guardar la imagen
        self.toolbar_actual = NavigationToolbar2Tk(self.canvas_actual, self.marco_grafico,
                                                   pack_toolbar=False)
        self.toolbar_actual.pack(side="bottom", fill="x")
        self.canvas_actual.get_tk_widget().pack(fill="both", expand=True)
        self.canvas_actual.draw()

    # ════════════════════════════════════════════════════════════════════
    #  Exportación
    # ════════════════════════════════════════════════════════════════════

    def _pedir_carpeta(self):
        if not self.estado.secuencias:
            messagebox.showwarning("Exportar", "Primero presione «Generar y validar».")
            return None
        carpeta = filedialog.askdirectory(title="Carpeta de destino",
                                          initialdir=self.estado.carpeta_salida
                                          if os.path.isdir(self.estado.carpeta_salida)
                                          else nucleo.DIR_PAQUETE)
        return carpeta or None

    def _exportar_csv(self):
        carpeta = self._pedir_carpeta()
        if not carpeta:
            return
        self.estado.carpeta_salida = carpeta
        nucleo.exportar_secuencias(self.estado)
        archivos = [f"secuencia_{c}.csv" for c in self.estado.secuencias]
        if self.estado.resultados:
            nucleo.exportar_comparacion(self.estado, os.path.join(carpeta, "comparacion_metodos.csv"))
            archivos.append("comparacion_metodos.csv")
        messagebox.showinfo("Exportar", f"Se exportaron {len(archivos)} archivo(s) en:\n{carpeta}\n\n"
                            + "\n".join(archivos))
        self._estado(f"Tablas exportadas en {carpeta}")

    def _guardar_graficos(self):
        carpeta = self._pedir_carpeta()
        if not carpeta:
            return
        self.estado.carpeta_salida = carpeta
        self.config(cursor="watch")
        total = 0
        try:
            for clave in self.estado.secuencias:
                self._estado(f"Guardando gráficos de {METODOS[clave]}...")
                self._crear_figura(clave, OPCION_HISTOGRAMA,
                                   os.path.join(carpeta, f"histograma_{clave}.png"), mostrar=False)
                total += 1
                for m, p, _ in self.estado.resultados:
                    if m == clave:
                        self._crear_figura(clave, PRUEBAS[p],
                                           os.path.join(carpeta, f"prueba_{p}_{clave}.png"), mostrar=False)
                        total += 1
        finally:
            self.config(cursor="")
        messagebox.showinfo("Gráficos", f"Se guardaron {total} gráficos en:\n{carpeta}")
        self._estado(f"{total} gráficos guardados en {carpeta}")


if __name__ == "__main__":
    Aplicacion().mainloop()
