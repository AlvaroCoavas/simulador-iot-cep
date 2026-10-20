"""Panel derecho: SISTEMA DIGITAL DE MONITOREO (CEP)."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .. import theme
from ..core.cep_engine import EstadoProceso
from .chart import ChartControl
from .widgets import Banner, Card, TituloPanel

# Textos del banner (replican el prototipo del cliente).
TEXTO_ESTABLE = "PROCESO BAJO CONTROL ESTADÍSTICO"
TEXTO_ACEPTABLE = "PROCESO EN ZONA DE ACEPTACIÓN"
TEXTO_CRITICO = "¡ALERTA! PROCESO FUERA DE CONTROL (DESVIACIÓN TÉRMICA)"


class Metrica(QFrame):
    """Tarjeta de un indicador de la barra inferior."""

    def __init__(self, titulo: str, valor: str, color: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("SubCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 10)
        layout.setSpacing(2)

        self.etiqueta = QLabel(titulo)
        self.etiqueta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.etiqueta.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 600;")
        layout.addWidget(self.etiqueta)

        self.etiqueta_valor = QLabel(valor)
        self.etiqueta_valor.setObjectName("MetricaValor")
        self.etiqueta_valor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.etiqueta_valor.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: 600;")
        layout.addWidget(self.etiqueta_valor)

    def set_valor(self, valor: str, color: str | None = None) -> None:
        self.etiqueta_valor.setText(valor)
        if color:
            self.etiqueta_valor.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: 600;")


class CepPanel(QWidget):
    """Carta de control, banner de estado e indicadores."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._construir_ui()

    def _construir_ui(self) -> None:
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(12)

        raiz.addWidget(TituloPanel("SISTEMA DIGITAL DE MONITOREO (CEP)", "panel"))

        self.banner = Banner()
        self.banner.set_estado(TEXTO_ESTABLE, theme.VERDE)
        raiz.addWidget(self.banner)

        # --- Grafico ---
        tarjeta_grafico = Card()
        layout_grafico = QVBoxLayout(tarjeta_grafico)
        layout_grafico.setContentsMargins(10, 8, 10, 8)
        self.chart = ChartControl()
        layout_grafico.addWidget(self.chart)
        raiz.addWidget(tarjeta_grafico, 1)

        # --- Barra de indicadores ---
        barra = QHBoxLayout()
        barra.setSpacing(12)
        self.metrica_media = Metrica("Media Temporal (X̄):", "0.00 °C", theme.AZUL)
        self.metrica_fuera = Metrica("Puntos Fuera de Límite:", "0", theme.TEXTO)
        self.metrica_defectos = Metrica("Índice de Defectos:", "0.0 %", theme.VERDE)
        for metrica in (self.metrica_media, self.metrica_fuera, self.metrica_defectos):
            barra.addWidget(metrica, 1)
        raiz.addLayout(barra)

    # ------------------------------ Actualizacion -------------------------
    def set_banner(self, estado: EstadoProceso) -> None:
        """Pinta el banner segun el estado del proceso."""
        if estado is EstadoProceso.CRITICO:
            self.banner.set_estado(TEXTO_CRITICO, theme.ROJO)
        elif estado is EstadoProceso.ACEPTABLE:
            self.banner.set_estado(TEXTO_ACEPTABLE, theme.AMBAR)
        else:
            self.banner.set_estado(TEXTO_ESTABLE, theme.VERDE)

    def set_grafico(self, x, y, fuera, lsc: float, lic: float, objetivo: float) -> None:
        self.chart.actualizar(x, y, fuera, lsc, lic, objetivo)

    def set_indicadores(
        self, media: float, fuera: int, indice: float, estado: EstadoProceso
    ) -> None:
        """Actualiza la barra inferior con los tres indicadores."""
        self.metrica_media.set_valor(f"{media:.2f} °C", theme.AZUL)
        self.metrica_fuera.set_valor(str(fuera), theme.TEXTO)
        color_defectos = theme.ROJO if fuera > 0 else theme.VERDE
        self.metrica_defectos.set_valor(f"{indice:.1f} %", color_defectos)
