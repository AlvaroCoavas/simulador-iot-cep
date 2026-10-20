"""Modelo termico del sensor simulado (modo local, sin Wokwi).

Reproduce el comportamiento de un DS18B20 en una cadena de frio:
  * inercia de primer orden hacia el ambiente (constante de tiempo TAU),
  * deriva aleatoria lenta (variabilidad propia del proceso),
  * ruido blanco de medicion,
  * cuantizacion a la resolucion real del DS18B20 (1/16 = 0.0625 C).
"""

from __future__ import annotations

import math
import random


class ModeloSensor:
    """Simula la temperatura de un proceso frente a una temperatura ambiente."""

    #: Constante de tiempo termico (s): cuanto tarda en seguir al ambiente.
    TAU = 18.0
    #: Desviacion estandar del ruido de medicion (C).
    RUIDO = 0.10
    #: Amplitud de la deriva lenta (C).
    DERIVA = 0.35
    #: Resolucion del DS18B20 (C).
    PASO = 0.0625

    def __init__(self, valor_inicial: float = 5.0, ambiente: float = 5.0):
        self.ambiente = float(ambiente)
        self.temperatura = float(valor_inicial)
        self._deriva = 0.0
        self._fase = random.uniform(0, 2 * math.pi)

    # ------------------------------ Control ------------------------------
    def set_ambiente(self, ambiente: float) -> None:
        """Fija la temperatura ambiente a la que tiende el proceso."""
        self.ambiente = float(ambiente)

    def reiniciar(self, valor: float | None = None) -> None:
        """Reinicia el modelo, opcionalmente a un valor concreto."""
        if valor is not None:
            self.temperatura = float(valor)
        else:
            self.temperatura = self.ambiente
        self._deriva = 0.0
        self._fase = random.uniform(0, 2 * math.pi)

    # ---------------------------- Evolucion ------------------------------
    def avanzar(self, dt: float = 1.0) -> float:
        """Avanza el modelo `dt` segundos y devuelve la nueva temperatura."""
        dt = max(0.0, float(dt))

        # Deriva lenta: oscilacion suave + paseo aleatorio acotado.
        self._fase += dt / 9.0
        deriva_objetivo = self.DERIVA * math.sin(self._fase) + random.uniform(-0.05, 0.05)
        self._deriva += 0.08 * (deriva_objetivo - self._deriva)

        # Inercia de primer orden hacia el ambiente (+ deriva).
        alfa = 1.0 - math.exp(-dt / self.TAU)
        objetivo = self.ambiente + self._deriva
        self.temperatura += (objetivo - self.temperatura) * alfa

        # Ruido de medicion.
        self.temperatura += random.gauss(0.0, self.RUIDO)

        # Cuantizacion a la resolucion del sensor real.
        self.temperatura = round(self.temperatura / self.PASO) * self.PASO
        return self.temperatura
