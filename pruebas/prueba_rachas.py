"""
Prueba de Rachas (Runs Test) (Propiedad 3 - Independencia Serial).

Evalúa si los números de la secuencia aparecen de forma independiente o si
existen patrones cíclicos o tendencias (rachas).

Se implementa la prueba de rachas por encima y por debajo de la media (o mediana 0.5):
    - Se asigna '+' si Ri >= umbral (por defecto 0.5) y '-' si Ri < umbral.
    - n1 = cantidad de signos '+'
    - n2 = cantidad de signos '-'
    - b  = número total de rachas observadas

Bajo H0 (independencia):
    Media esperada:
        μ_b = (2 * n1 * n2 / N) + 1
    Varianza:
        σ_b^2 = [2 * n1 * n2 * (2 * n1 * n2 - N)] / [N^2 * (N - 1)]
    Estadístico Z:
        Z₀ = (b - μ_b) / σ_b

Intervalo de aceptación para el número de rachas:
    LI = μ_b - Z_(α/2) * σ_b
    LS = μ_b + Z_(α/2) * σ_b
"""
import math
from scipy.stats import norm
from .resultado import ResultadoPrueba


class PruebaRachas:
    """
    Prueba de Rachas para evaluar independencia serial en R_i ∈ [0, 1).
    """

    def __init__(self, ri_nums, alpha=0.05, umbral=0.5):
        if len(ri_nums) < 2:
            raise ValueError("Se requieren al menos 2 números para la prueba de rachas")
        self.ri = list(ri_nums)
        self.n = len(self.ri)
        self.alpha = alpha
        self.umbral = umbral

    def ejecutar(self):
        """
        Ejecuta la prueba de rachas.

        Returns:
            ResultadoPrueba: Objeto con el veredicto y estadísticas detalladas.
        """
        # 1. Generar secuencia de signos
        signos = ['+' if x >= self.umbral else '-' for x in self.ri]
        n1 = signos.count('+')
        n2 = signos.count('-')

        # Si todos los elementos son del mismo signo no hay variabilidad
        if n1 == 0 or n2 == 0:
            return ResultadoPrueba(
                nombre="Prueba de Rachas",
                aprobada=False,
                estadistico=1,
                valor_critico=0.0,
                limite_inferior=0.0,
                limite_superior=0.0,
                alpha=self.alpha,
                detalles={"error": "Todos los números cayeron a un mismo lado del umbral"}
            )

        # 2. Contar cantidad de rachas (b)
        rachas_obs = 1
        for i in range(1, len(signos)):
            if signos[i] != signos[i - 1]:
                rachas_obs += 1

        # 3. Media y varianza teórica
        n = self.n
        mu_b = (2.0 * n1 * n2 / n) + 1.0
        numerador_var = 2.0 * n1 * n2 * (2.0 * n1 * n2 - n)
        denominador_var = (n ** 2) * (n - 1)
        var_b = max(1e-9, numerador_var / denominador_var)
        sigma_b = math.sqrt(var_b)

        # 4. Valor crítico Z y límites del intervalo de confianza
        z_critico = norm.ppf(1.0 - (self.alpha / 2.0))
        lim_inf = mu_b - z_critico * sigma_b
        lim_sup = mu_b + z_critico * sigma_b

        z_calc = (rachas_obs - mu_b) / sigma_b
        aprobada = lim_inf <= rachas_obs <= lim_sup

        detalles = {
            "n": n,
            "n1_arriba": n1,
            "n2_abajo": n2,
            "rachas_observadas": rachas_obs,
            "rachas_esperadas": mu_b,
            "varianza_rachas": var_b,
            "desviacion_rachas": sigma_b,
            "z_calculado": z_calc,
            "z_critico": z_critico,
            "limite_inferior": lim_inf,
            "limite_superior": lim_sup,
            "umbral": self.umbral,
        }

        return ResultadoPrueba(
            nombre="Prueba de Rachas",
            aprobada=aprobada,
            estadistico=rachas_obs,
            valor_critico=mu_b,
            limite_inferior=lim_inf,
            limite_superior=lim_sup,
            alpha=self.alpha,
            detalles=detalles
        )
