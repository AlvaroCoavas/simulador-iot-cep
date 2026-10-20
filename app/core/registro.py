"""Registro de muestras para la tabla y la exportacion a CSV.

El motor CEP guarda TODAS las lecturas (grafico, indicadores y estados usan
todas). Este registro es el que decide que lecturas se archivan en la tabla y
en el CSV: una cada N segundos, segun la HORA de la lectura (no segun la
cantidad de mensajes recibidos).
"""

from __future__ import annotations

from .cep_engine import Muestra


class RegistroMuestras:
    """Archivo de lecturas muestreadas cada N segundos."""

    def __init__(self, intervalo_s: int = 5):
        self.intervalo_s = int(intervalo_s)
        self.muestras: list[Muestra] = []
        self._ultimo_registro = None

    # ------------------------------ Registro ------------------------------
    def registrar(self, muestra: Muestra) -> bool:
        """Guarda la muestra si ha pasado el intervalo. Devuelve True si se guardo."""
        if self._ultimo_registro is not None:
            transcurrido = (muestra.instante - self._ultimo_registro).total_seconds()
            if transcurrido < self.intervalo_s:
                return False
        self.muestras.append(muestra)
        self._ultimo_registro = muestra.instante
        return True

    # ------------------------------ Configuracion -------------------------
    def set_intervalo(self, segundos: int) -> None:
        """Cambia el intervalo de registro.

        No borra el historial ni reinicia el conteo: solo afecta a las
        lecturas nuevas.
        """
        self.intervalo_s = int(segundos)

    def limpiar(self) -> None:
        """Borra el historial de lecturas registradas."""
        self.muestras.clear()
        self._ultimo_registro = None
