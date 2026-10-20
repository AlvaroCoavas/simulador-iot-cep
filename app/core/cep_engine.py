"""Motor de Control Estadistico de Procesos (CEP).

Reglas de clasificacion (definidas por el cliente):
  * CRITICO   : T > LSC  o  T < LIC
  * ACEPTABLE : dentro de [LIC, LSC] pero en el 40 % exterior de la banda
  * ESTABLE   : resto de la banda
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class EstadoProceso(str, Enum):
    """Estado del proceso segun las reglas de control."""

    CRITICO = "CRÍTICO"
    ACEPTABLE = "ACEPTABLE"
    ESTABLE = "ESTABLE"

    @property
    def color(self) -> str:
        return {
            EstadoProceso.CRITICO: "#e53935",
            EstadoProceso.ACEPTABLE: "#ffb300",
            EstadoProceso.ESTABLE: "#4caf50",
        }[self]


@dataclass
class Muestra:
    """Una lectura del sensor."""

    n: int
    temperatura: float
    estado: EstadoProceso

    @property
    def fuera_de_limite(self) -> bool:
        return self.estado is EstadoProceso.CRITICO


class CepEngine:
    """Acumula muestras y calcula los indicadores de control."""

    #: Porcentaje exterior de la banda [LIC, LSC] que se considera ACEPTABLE.
    ZONA_ACEPTABLE = 0.40

    def __init__(self, lsc: float = 8.0, lic: float = 2.0, objetivo: float = 5.0):
        self.lsc = float(lsc)
        self.lic = float(lic)
        self.objetivo = float(objetivo)
        self.muestras: list[Muestra] = []
        self._n = 0

    # ------------------------------ Limites ------------------------------
    def set_limites(self, lsc: float, lic: float, objetivo: float) -> None:
        """Actualiza los limites y reclasifica las muestras ya tomadas."""
        self.lsc = float(lsc)
        self.lic = float(lic)
        self.objetivo = float(objetivo)
        for m in self.muestras:
            m.estado = self.clasificar(m.temperatura)

    # ------------------------------ Muestras -----------------------------
    def agregar(self, temperatura: float) -> Muestra:
        """Registra una lectura y devuelve la muestra resultante."""
        self._n += 1
        m = Muestra(self._n, float(temperatura), self.clasificar(temperatura))
        self.muestras.append(m)
        return m

    def reiniciar(self) -> None:
        """Borra todas las muestras y reinicia la numeracion."""
        self.muestras.clear()
        self._n = 0

    # --------------------------- Clasificacion ---------------------------
    def clasificar(self, temperatura: float) -> EstadoProceso:
        """Clasifica una temperatura segun los limites de control."""
        t = float(temperatura)
        if t > self.lsc or t < self.lic:
            return EstadoProceso.CRITICO

        ancho = self.lsc - self.lic
        exterior = self.ZONA_ACEPTABLE * ancho
        if t < self.lic + exterior or t > self.lsc - exterior:
            return EstadoProceso.ACEPTABLE
        return EstadoProceso.ESTABLE

    # ---------------------------- Indicadores ----------------------------
    @property
    def total(self) -> int:
        return len(self.muestras)

    @property
    def media_temporal(self) -> float:
        """Media de TODAS las muestras registradas."""
        if not self.muestras:
            return 0.0
        return sum(m.temperatura for m in self.muestras) / len(self.muestras)

    @property
    def puntos_fuera_de_limite(self) -> int:
        """Numero de muestras fuera de [LIC, LSC]."""
        return sum(1 for m in self.muestras if m.fuera_de_limite)

    @property
    def indice_defectos(self) -> float:
        """Porcentaje de muestras fuera de limite respecto del total."""
        if not self.muestras:
            return 0.0
        return 100.0 * self.puntos_fuera_de_limite / len(self.muestras)

    # ------------------------------ Grafica ------------------------------
    def serie(self, ventana: int = 60) -> tuple[list[int], list[float], list[bool]]:
        """Ultimas `ventana` muestras -> (x, y, bandera de fuera de limite)."""
        ultimas = self.muestras[-ventana:] if ventana > 0 else self.muestras
        x = [m.n for m in ultimas]
        y = [m.temperatura for m in ultimas]
        fuera = [m.fuera_de_limite for m in ultimas]
        return x, y, fuera

    def estado_actual(self) -> EstadoProceso:
        """Estado de la ultima muestra (ESTABLE si no hay muestras)."""
        return self.muestras[-1].estado if self.muestras else EstadoProceso.ESTABLE
