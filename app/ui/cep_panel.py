"""Panel derecho: SISTEMA DIGITAL DE MONITOREO (CEP)."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .. import theme
from ..core.cep_engine import EstadoProceso, Muestra
from .chart import ChartControl
from .data_table import TablaMuestras
from .widgets import Banner, Card, TituloPanel, tarjeta

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
    """Carta de control, banner de estado, tabla de muestras e indicadores."""

    #: Se emite cuando el usuario pulsa "Exportar CSV".
    exportar_solicitado = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._construir_ui()

    # --------------------------------- UI ---------------------------------
    def _construir_ui(self) -> None:
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(12)

        raiz.addWidget(TituloPanel("SISTEMA DIGITAL DE MONITOREO (CEP)", "panel"))

        self.banner = Banner()
        self.banner.set_estado(TEXTO_ESTABLE, theme.VERDE)
        raiz.addWidget(self.banner)

        # --- Pestanas: grafico / tabla de muestras ---
        # El grafico conserva su tamano actual: la tabla va en otra pestana.
        self.pestanas = QTabWidget()
        self.pestanas.setDocumentMode(True)

        tarjeta_grafico = Card()
        layout_grafico = QVBoxLayout(tarjeta_grafico)
        layout_grafico.setContentsMargins(10, 8, 10, 8)
        self.chart = ChartControl()
        layout_grafico.addWidget(self.chart)
        self.pestanas.addTab(tarjeta_grafico, "Gráfico de control")

        self.pestanas.addTab(self._crear_pestana_muestras(), "Muestras")
        raiz.addWidget(self.pestanas, 1)

        # --- Barra de indicadores ---
        barra = QHBoxLayout()
        barra.setSpacing(12)
        self.metrica_media = Metrica("Media Temporal (X̄):", "0.00 °C", theme.AZUL)
        self.metrica_fuera = Metrica("Puntos Fuera de Límite:", "0", theme.TEXTO)
        self.metrica_defectos = Metrica("Índice de Defectos:", "0.0 %", theme.VERDE)
        for metrica in (self.metrica_media, self.metrica_fuera, self.metrica_defectos):
            barra.addWidget(metrica, 1)
        raiz.addLayout(barra)

    def _crear_pestana_muestras(self) -> QWidget:
        """Construye la pestana con la tabla de muestras y el boton de export."""
        tarjeta_muestras, layout = tarjeta()

        fila = QHBoxLayout()
        fila.setSpacing(10)
        titulo = QLabel("MUESTRAS DEL PROCESO")
        titulo.setObjectName("TituloPanel")
        fila.addWidget(titulo)

        self.etiqueta_conteo = QLabel("0 muestras")
        self.etiqueta_conteo.setObjectName("Subtitulo")
        fila.addWidget(self.etiqueta_conteo)
        fila.addStretch(1)

        self.boton_exportar = QPushButton("Exportar CSV")
        self.boton_exportar.clicked.connect(self.exportar_solicitado.emit)
        fila.addWidget(self.boton_exportar)
        layout.addLayout(fila)

        self.tabla = TablaMuestras()
        layout.addWidget(self.tabla, 1)
        return tarjeta_muestras

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

    def set_muestra(self, muestra: Muestra) -> None:
        """Anade una lectura a la tabla (estado ya calculado por el motor CEP)."""
        self.tabla.agregar(muestra)
        self.etiqueta_conteo.setText(f"{self.tabla.rowCount()} muestras")

    def limpiar_tabla(self) -> None:
        """Vacia la tabla de muestras."""
        self.tabla.limpiar()
        self.etiqueta_conteo.setText("0 muestras")

    def set_indicadores(
        self, media: float, fuera: int, indice: float, estado: EstadoProceso
    ) -> None:
        """Actualiza la barra inferior con los tres indicadores."""
        self.metrica_media.set_valor(f"{media:.2f} °C", theme.AZUL)
        self.metrica_fuera.set_valor(str(fuera), theme.TEXTO)
        color_defectos = theme.ROJO if fuera > 0 else theme.VERDE
        self.metrica_defectos.set_valor(f"{indice:.1f} %", color_defectos)
