"""
Módulo de visualización gráfica para generadores y pruebas estadísticas.
Genera los gráficos exigidos en el taller de simulación usando Matplotlib.
"""
import math

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import chi2, norm


class Visualizacion:
    """
    Colección de métodos estáticos para generar los gráficos requeridos por el taller.

    Parámetros comunes a todos los métodos:
        guardar_en (str, opcional): Ruta del archivo .png donde guardar la figura.
        mostrar (bool | None):
            True  → muestra la figura inmediatamente (bloquea hasta cerrarla).
            False → la cierra después de guardarla (útil en modo por lotes).
            None  → la deja abierta para mostrar varias juntas luego con plt.show().
    """

    @staticmethod
    def _finalizar_figura(fig, guardar_en=None, mostrar=True):
        fig.tight_layout()
        if guardar_en:
            fig.savefig(guardar_en, dpi=300)
        if mostrar is True:
            plt.show()
        elif mostrar is False:
            plt.close(fig)

    @staticmethod
    def _dividir_en_subgrupos(ri, n_subgrupos):
        """
        Divide la secuencia en subgrupos consecutivos del mismo tamaño.
        Los elementos sobrantes al final se descartan.

        Returns:
            tuple: (lista_de_subgrupos, tamaño_de_cada_subgrupo)
        """
        tam = len(ri) // n_subgrupos
        return [ri[i * tam:(i + 1) * tam] for i in range(n_subgrupos)], tam

    @staticmethod
    def _subgrupos_validos(ri, n_subgrupos, tam_minimo=5):
        """Ajusta la cantidad de subgrupos para que cada uno tenga al menos tam_minimo elementos."""
        if ri is None:
            return 0
        return max(0, min(n_subgrupos, len(ri) // tam_minimo))

    @staticmethod
    def histograma_generacion(datos, titulo="Histograma de Números Generados", bins=20,
                              densidad_teorica=None, etiqueta_teorica="Densidad teórica",
                              guardar_en=None, mostrar=True):
        """
        Histograma de frecuencias para visualizar la distribución alcanzada.

        Args:
            datos (list[float]): Valores a graficar (R_i o N_i).
            titulo (str): Título del gráfico.
            bins (int): Número de clases del histograma.
            densidad_teorica (callable, opcional): Función f(x) de la densidad esperada,
                que se superpone como curva para comparar (p. ej., la normal).
            etiqueta_teorica (str): Leyenda de la curva teórica.
        """
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.hist(datos, bins=bins, color="#4A90E2", edgecolor="#1C3F75", alpha=0.75,
                density=True, label="Frecuencia relativa observada")
        if densidad_teorica is not None and len(datos) > 0:
            xs = np.linspace(min(datos), max(datos), 300)
            ax.plot(xs, [densidad_teorica(x) for x in xs], color="#E74C3C",
                    linewidth=2, label=etiqueta_teorica)
            ax.legend()
        ax.set_title(titulo, fontsize=12, fontweight="bold")
        ax.set_xlabel("Valor", fontsize=10)
        ax.set_ylabel("Densidad de Frecuencia", fontsize=10)
        ax.grid(True, linestyle="--", alpha=0.5)
        Visualizacion._finalizar_figura(fig, guardar_en, mostrar)
        return fig

    @staticmethod
    def prueba_medias(resultado, ri=None, n_subgrupos=20, guardar_en=None, mostrar=True):
        """
        Gráfico para la Prueba de Medias.

        Si se entrega la secuencia `ri`, se divide en `n_subgrupos` subgrupos y se grafica:
            - Izquierda: la media de cada subgrupo con su intervalo de confianza
              (X̄_j ± Z_(α/2)·√(1/(12·b))) frente a la media teórica 0.5. Los intervalos
              que no contienen 0.5 se resaltan en rojo.
            - Derecha: el histograma de las medias de los subgrupos, la densidad
              teórica N(0.5, 1/(12·b)), la región de aceptación y la media global.
        Si no se entrega `ri`, se grafica un resumen de barras con la media global.
        """
        k = Visualizacion._subgrupos_validos(ri, n_subgrupos)
        if k >= 2:
            return Visualizacion._prueba_medias_distribucion(resultado, ri, k, guardar_en, mostrar)
        return Visualizacion._prueba_medias_resumen(resultado, guardar_en, mostrar)

    @staticmethod
    def _prueba_medias_distribucion(resultado, ri, n_subgrupos, guardar_en, mostrar):
        det = resultado.detalles
        alpha = resultado.alpha
        subgrupos, tam = Visualizacion._dividir_en_subgrupos(ri, n_subgrupos)
        medias = [sum(g) / tam for g in subgrupos]

        z = norm.ppf(1.0 - alpha / 2.0)
        error = z * math.sqrt(1.0 / (12.0 * tam))
        # Región de aceptación para un subgrupo de tamaño b
        li_sub, ls_sub = 0.5 - error, 0.5 + error

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

        # ── Izquierda: intervalos de confianza por subgrupo ──
        for j, m in enumerate(medias, start=1):
            contiene = (m - error) <= 0.5 <= (m + error)
            color = "#2980B9" if contiene else "#E74C3C"
            ax1.errorbar(j, m, yerr=error, fmt="o", color=color, capsize=3)
        ax1.axhline(0.5, color="#27AE60", linestyle="--", linewidth=2, label="Media teórica μ = 0.5")
        no_contienen = sum(1 for m in medias if not (m - error <= 0.5 <= m + error))
        ax1.set_title(f"IC {int((1 - alpha) * 100)}% de la media por subgrupo "
                      f"(b = {tam})\n{no_contienen} de {n_subgrupos} no contienen 0.5",
                      fontsize=11, fontweight="bold")
        ax1.set_xlabel("Subgrupo", fontsize=10)
        ax1.set_ylabel("Media del subgrupo", fontsize=10)
        ax1.grid(True, linestyle="--", alpha=0.5)
        ax1.legend(loc="upper right", fontsize=9)

        # ── Derecha: distribución de las medias ──
        ax2.hist(medias, bins=max(5, n_subgrupos // 3), density=True, color="#4A90E2",
                 edgecolor="#1C3F75", alpha=0.75, label="Medias de subgrupos")
        sigma = math.sqrt(1.0 / (12.0 * tam))
        xs = np.linspace(0.5 - 4 * sigma, 0.5 + 4 * sigma, 300)
        ax2.plot(xs, norm.pdf(xs, 0.5, sigma), color="#8E44AD", linewidth=2,
                 label="Teórica N(0.5, 1/(12b))")
        ax2.axvspan(li_sub, ls_sub, color="#27AE60", alpha=0.12, label="Región de aceptación (b)")
        ax2.axvline(0.5, color="#27AE60", linestyle="--", linewidth=2, label="Media teórica 0.5")
        ax2.axvline(det["media_calculada"], color="#E67E22", linewidth=2,
                    label=f"Media global = {det['media_calculada']:.5f}")
        ax2.set_title("Distribución de las medias calculadas", fontsize=11, fontweight="bold")
        ax2.set_xlabel("Media", fontsize=10)
        ax2.set_ylabel("Densidad", fontsize=10)
        ax2.legend(fontsize=8)
        ax2.grid(True, linestyle="--", alpha=0.5)

        fig.suptitle(f"Prueba de Medias (n = {det['n']}) - "
                     f"{'APROBADA' if resultado.aprobada else 'RECHAZADA'} | "
                     f"LI = {det['limite_inferior']:.5f}, LS = {det['limite_superior']:.5f}",
                     fontsize=12, fontweight="bold")
        Visualizacion._finalizar_figura(fig, guardar_en, mostrar)
        return fig

    @staticmethod
    def _prueba_medias_resumen(resultado, guardar_en=None, mostrar=True):
        """Resumen en barras: media calculada, límites de confianza y media teórica (0.5)."""
        det = resultado.detalles
        media_calc = det["media_calculada"]
        lim_inf = det["limite_inferior"]
        lim_sup = det["limite_superior"]
        media_teo = det["media_esperada"]

        fig, ax = plt.subplots(figsize=(8, 5))
        categorias = ["Límite Inferior", "Media Calculada", "Media Teórica", "Límite Superior"]
        valores = [lim_inf, media_calc, media_teo, lim_sup]
        colores = ["#E74C3C", "#2ECC71" if resultado.aprobada else "#E67E22", "#3498DB", "#E74C3C"]

        barras = ax.bar(categorias, valores, color=colores, width=0.5, edgecolor="black")
        ax.axhline(media_teo, color="#2980B9", linestyle="--", alpha=0.7, label=f"Teórica ({media_teo})")
        ax.set_title(f"Prueba de Medias - {'APROBADA' if resultado.aprobada else 'RECHAZADA'}",
                     fontsize=12, fontweight="bold")
        ax.set_ylabel("Valor Promedio", fontsize=10)

        for bar, val in zip(barras, valores):
            ax.annotate(f"{val:.5f}",
                        xy=(bar.get_x() + bar.get_width() / 2, val),
                        xytext=(0, 4), textcoords="offset points",
                        ha="center", va="bottom", fontsize=9)

        ax.legend()
        Visualizacion._finalizar_figura(fig, guardar_en, mostrar)
        return fig

    @staticmethod
    def prueba_varianza(resultado, ri=None, n_subgrupos=20, guardar_en=None, mostrar=True):
        """
        Gráfico para la Prueba de Varianza.

        Si se entrega la secuencia `ri`, se divide en `n_subgrupos` subgrupos y se grafica:
            - Izquierda: la varianza de cada subgrupo con su intervalo de confianza
              [(b−1)S²/χ²_(1−α/2), (b−1)S²/χ²_(α/2)] frente a la varianza teórica 1/12.
            - Derecha: el histograma de las varianzas de los subgrupos, la región de
              aceptación para tamaño b y la varianza global.
        Si no se entrega `ri`, se grafica un resumen de barras con la varianza global.
        """
        k = Visualizacion._subgrupos_validos(ri, n_subgrupos)
        if k >= 2:
            return Visualizacion._prueba_varianza_distribucion(resultado, ri, k, guardar_en, mostrar)
        return Visualizacion._prueba_varianza_resumen(resultado, guardar_en, mostrar)

    @staticmethod
    def _prueba_varianza_distribucion(resultado, ri, n_subgrupos, guardar_en, mostrar):
        det = resultado.detalles
        alpha = resultado.alpha
        var_teo = 1.0 / 12.0
        subgrupos, tam = Visualizacion._dividir_en_subgrupos(ri, n_subgrupos)
        gl = tam - 1

        varianzas = []
        for g in subgrupos:
            m = sum(g) / tam
            varianzas.append(sum((x - m) ** 2 for x in g) / gl)

        chi_inf = chi2.ppf(alpha / 2.0, gl)
        chi_sup = chi2.ppf(1.0 - alpha / 2.0, gl)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

        # ── Izquierda: intervalos de confianza por subgrupo ──
        no_contienen = 0
        for j, s2 in enumerate(varianzas, start=1):
            li = gl * s2 / chi_sup
            ls = gl * s2 / chi_inf
            contiene = li <= var_teo <= ls
            no_contienen += not contiene
            color = "#2980B9" if contiene else "#E74C3C"
            ax1.errorbar(j, s2, yerr=[[s2 - li], [ls - s2]], fmt="o", color=color, capsize=3)
        ax1.axhline(var_teo, color="#27AE60", linestyle="--", linewidth=2,
                    label=f"Varianza teórica 1/12 = {var_teo:.5f}")
        ax1.set_title(f"IC {int((1 - alpha) * 100)}% de la varianza por subgrupo "
                      f"(b = {tam})\n{no_contienen} de {n_subgrupos} no contienen 1/12",
                      fontsize=11, fontweight="bold")
        ax1.set_xlabel("Subgrupo", fontsize=10)
        ax1.set_ylabel("Varianza del subgrupo", fontsize=10)
        ax1.grid(True, linestyle="--", alpha=0.5)
        ax1.legend(loc="upper right", fontsize=9)

        # ── Derecha: distribución de las varianzas ──
        li_sub = chi_inf / (12.0 * gl)
        ls_sub = chi_sup / (12.0 * gl)
        ax2.hist(varianzas, bins=max(5, n_subgrupos // 3), density=True, color="#4A90E2",
                 edgecolor="#1C3F75", alpha=0.75, label="Varianzas de subgrupos")
        ax2.axvspan(li_sub, ls_sub, color="#27AE60", alpha=0.12, label="Región de aceptación (b)")
        ax2.axvline(var_teo, color="#27AE60", linestyle="--", linewidth=2, label="Varianza teórica 1/12")
        ax2.axvline(det["varianza_calculada"], color="#E67E22", linewidth=2,
                    label=f"Varianza global = {det['varianza_calculada']:.5f}")
        ax2.set_title("Distribución de las varianzas calculadas", fontsize=11, fontweight="bold")
        ax2.set_xlabel("Varianza", fontsize=10)
        ax2.set_ylabel("Densidad", fontsize=10)
        ax2.legend(fontsize=8)
        ax2.grid(True, linestyle="--", alpha=0.5)

        fig.suptitle(f"Prueba de Varianza (n = {det['n']}) - "
                     f"{'APROBADA' if resultado.aprobada else 'RECHAZADA'} | "
                     f"LI = {det['limite_inferior']:.5f}, LS = {det['limite_superior']:.5f}",
                     fontsize=12, fontweight="bold")
        Visualizacion._finalizar_figura(fig, guardar_en, mostrar)
        return fig

    @staticmethod
    def _prueba_varianza_resumen(resultado, guardar_en=None, mostrar=True):
        """Resumen en barras: varianza calculada, límites de confianza y varianza teórica (1/12)."""
        det = resultado.detalles
        var_calc = det["varianza_calculada"]
        lim_inf = det["limite_inferior"]
        lim_sup = det["limite_superior"]
        var_teo = det["varianza_esperada"]

        fig, ax = plt.subplots(figsize=(8, 5))
        categorias = ["Límite Inferior", "Varianza Calculada", "Varianza Teórica", "Límite Superior"]
        valores = [lim_inf, var_calc, var_teo, lim_sup]
        colores = ["#E74C3C", "#2ECC71" if resultado.aprobada else "#E67E22", "#3498DB", "#E74C3C"]

        barras = ax.bar(categorias, valores, color=colores, width=0.5, edgecolor="black")
        ax.axhline(var_teo, color="#2980B9", linestyle="--", alpha=0.7, label=f"Teórica ({var_teo:.5f})")
        ax.set_title(f"Prueba de Varianza - {'APROBADA' if resultado.aprobada else 'RECHAZADA'}",
                     fontsize=12, fontweight="bold")
        ax.set_ylabel("Varianza", fontsize=10)

        for bar, val in zip(barras, valores):
            ax.annotate(f"{val:.5f}",
                        xy=(bar.get_x() + bar.get_width() / 2, val),
                        xytext=(0, 4), textcoords="offset points",
                        ha="center", va="bottom", fontsize=9)

        ax.legend()
        Visualizacion._finalizar_figura(fig, guardar_en, mostrar)
        return fig

    @staticmethod
    def prueba_chi2(resultado, guardar_en=None, mostrar=True):
        """
        Gráfico para la Prueba Chi-Cuadrado:
        Barras comparando frecuencias observadas vs esperadas por intervalo.
        """
        det = resultado.detalles
        k = det["k_intervalos"]
        limites = det["limites_intervalos"]
        obs = det["frecuencias_observadas"]
        esp = det["frecuencia_esperada"]

        etiquetas = [f"[{limites[i]:.2f}, {limites[i+1]:.2f})" for i in range(k)]
        x = np.arange(k)
        ancho = 0.35

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(x - ancho/2, obs, ancho, label="Observada (Oi)", color="#3498DB", edgecolor="black")
        ax.bar(x + ancho/2, [esp] * k, ancho, label="Esperada (Ei)", color="#E67E22", alpha=0.8, edgecolor="black")

        ax.set_title(f"Prueba Chi-Cuadrado de Uniformidad - {'APROBADA' if resultado.aprobada else 'RECHAZADA'}\n"
                     f"χ₀² = {resultado.estadistico:.4f} | χ_crit² = {resultado.valor_critico:.4f}",
                     fontsize=12, fontweight="bold")
        ax.set_xlabel("Intervalos", fontsize=10)
        ax.set_ylabel("Frecuencia", fontsize=10)
        ax.set_xticks(x)
        ax.set_xticklabels(etiquetas, rotation=35, ha="right", fontsize=9)
        ax.legend()
        ax.grid(axis="y", linestyle="--", alpha=0.5)

        Visualizacion._finalizar_figura(fig, guardar_en, mostrar)
        return fig

    @staticmethod
    def prueba_ks(resultado, guardar_en=None, mostrar=True):
        """
        Gráfico para la Prueba Kolmogorov-Smirnov (KS):
        Función Empírica Acumulada (FEC) vs Teórica Uniforme F(x)=x, destacando D_max.
        """
        det = resultado.detalles
        ordenados = det["numeros_ordenados"]
        fec_y = det["fec_y"]
        d_max = det["d_max"]
        d_critico = det["d_critico"]
        punto_max = det["punto_d_max"]

        fig, ax = plt.subplots(figsize=(8, 6))
        # Curva empírica paso a paso
        ax.step(ordenados, fec_y, label="Empírica Acumulada Sn(x)", color="#2980B9", where="post", linewidth=2)
        # Curva teórica
        ax.plot([0, 1], [0, 1], label="Teórica F(x) = x", color="#E74C3C", linestyle="--", linewidth=2)

        # Destacar punto de máxima discrepancia. Si el máximo proviene de D⁻,
        # la distancia se mide contra el escalón anterior (i−1)/n y no contra i/n.
        x_max, sn_max = punto_max
        idx = fec_y.index(sn_max)
        if det["d_minus"][idx] > det["d_plus"][idx]:
            sn_max = sn_max - 1.0 / det["n"]
        ax.plot([x_max, x_max], [x_max, sn_max],
                color="#8E44AD", linestyle=":", linewidth=2.5,
                label=f"D_max = {d_max:.4f} (Crítico: {d_critico:.4f})")
        ax.scatter([x_max], [sn_max], color="#8E44AD", s=60, zorder=5)

        ax.set_title(f"Prueba Kolmogorov-Smirnov - {'APROBADA' if resultado.aprobada else 'RECHAZADA'}",
                     fontsize=12, fontweight="bold")
        ax.set_xlabel("x (Valor)", fontsize=10)
        ax.set_ylabel("Probabilidad Acumulada", fontsize=10)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(loc="upper left")

        Visualizacion._finalizar_figura(fig, guardar_en, mostrar)
        return fig

    @staticmethod
    def prueba_poker(resultado, guardar_en=None, mostrar=True):
        """
        Gráfico para la Prueba de Póker:
        Comparación de frecuencias observadas vs esperadas por cada una de las 7 manos.
        """
        det = resultado.detalles
        categorias = det["categorias"]
        obs = det["frecuencias_observadas"]
        esp = det["frecuencias_esperadas"]

        # Abreviaciones para el eje X
        nombres_cortos = ["D (Dif)", "O (1 Par)", "T (2 Pares)", "K (Tercia)",
                          "F (Full)", "P (Póker)", "Q (Quintilla)"]
        x = np.arange(len(nombres_cortos))
        ancho = 0.35

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(x - ancho/2, obs, ancho, label="Observadas (Oi)", color="#27AE60", edgecolor="black")
        ax.bar(x + ancho/2, esp, ancho, label="Esperadas (Ei)", color="#F39C12", alpha=0.8, edgecolor="black")

        ax.set_title(f"Prueba de Póker (5 dígitos) - {'APROBADA' if resultado.aprobada else 'RECHAZADA'}\n"
                     f"χ₀² = {resultado.estadistico:.4f} | χ_crit² = {resultado.valor_critico:.4f}",
                     fontsize=12, fontweight="bold")
        ax.set_xlabel("Manos de Póker", fontsize=10)
        ax.set_ylabel("Frecuencia", fontsize=10)
        ax.set_xticks(x)
        ax.set_xticklabels(nombres_cortos, fontsize=9)
        ax.legend()
        ax.grid(axis="y", linestyle="--", alpha=0.5)

        Visualizacion._finalizar_figura(fig, guardar_en, mostrar)
        return fig

    @staticmethod
    def prueba_rachas(resultado, guardar_en=None, mostrar=True):
        """
        Gráfico para la Prueba de Rachas:
        Cantidad de rachas observadas vs esperadas con intervalo de confianza.
        """
        det = resultado.detalles
        r_obs = det.get("rachas_observadas", resultado.estadistico)
        r_esp = det.get("rachas_esperadas", resultado.valor_critico)
        lim_inf = det.get("limite_inferior", 0)
        lim_sup = det.get("limite_superior", 0)

        fig, ax = plt.subplots(figsize=(8, 5))
        categorias = ["Límite Inferior", "Rachas Observadas", "Rachas Esperadas", "Límite Superior"]
        valores = [lim_inf, r_obs, r_esp, lim_sup]
        colores = ["#E74C3C", "#2ECC71" if resultado.aprobada else "#E67E22", "#3498DB", "#E74C3C"]

        barras = ax.bar(categorias, valores, color=colores, width=0.5, edgecolor="black")
        ax.set_title(f"Prueba de Rachas - {'APROBADA' if resultado.aprobada else 'RECHAZADA'}",
                     fontsize=12, fontweight="bold")
        ax.set_ylabel("Cantidad de Rachas", fontsize=10)

        for bar, val in zip(barras, valores):
            ax.annotate(f"{val:.2f}",
                        xy=(bar.get_x() + bar.get_width() / 2, val),
                        xytext=(0, 4), textcoords="offset points",
                        ha="center", va="bottom", fontsize=9)

        ax.grid(axis="y", linestyle="--", alpha=0.5)
        Visualizacion._finalizar_figura(fig, guardar_en, mostrar)
        return fig
