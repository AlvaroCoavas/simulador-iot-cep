"""Panel izquierdo: HARDWARE SIMULADO."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from .. import theme
from ..core.cep_engine import EstadoProceso
from .widgets import Card, Icono, Led, TituloPanel, tarjeta

FUENTE_MQTT = "mqtt"
FUENTE_LOCAL = "local"

# Rango del control de entorno simulado (C).
AMBIENTE_MIN = -10.0
AMBIENTE_MAX = 30.0


class HardwarePanel(QWidget):
    """Estado del hardware virtual: valor de temperatura, LED y controles."""

    reiniciar = pyqtSignal()
    fuente_cambiada = pyqtSignal(str)
    ambiente_cambiado = pyqtSignal(float)
    limites_cambiados = pyqtSignal(float, float, float)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedWidth(350)
        self._construir_ui()

    # --------------------------------- UI ---------------------------------
    def _construir_ui(self) -> None:
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(12)

        raiz.addWidget(TituloPanel("HARDWARE SIMULADO", "chip"))

        # --- Tarjeta de la placa ---
        tarjeta_placa = Card()
        layout_placa = QVBoxLayout(tarjeta_placa)
        layout_placa.setContentsMargins(14, 12, 14, 14)
        layout_placa.setSpacing(6)

        fila_titulo = QHBoxLayout()
        fila_titulo.setSpacing(8)
        self.etiqueta_placa = QLabel("Tarjeta ESP32 (Virtual)")
        self.etiqueta_placa.setStyleSheet(f"color: {theme.VERDE}; font-size: 13px; font-weight: 600;")
        fila_titulo.addWidget(self.etiqueta_placa)
        fila_titulo.addStretch(1)
        layout_placa.addLayout(fila_titulo)

        fila_estado = QHBoxLayout()
        fila_estado.setSpacing(8)
        fila_estado.addWidget(Icono("radio", 15, theme.TEXTO_SUAVE))
        self.etiqueta_estado = QLabel("Estado: Transmitiendo cada 1s")
        self.etiqueta_estado.setObjectName("Subtitulo")
        fila_estado.addWidget(self.etiqueta_estado)
        fila_estado.addStretch(1)
        layout_placa.addLayout(fila_estado)

        raiz.addWidget(tarjeta_placa)

        # --- Tarjeta de la lectura ---
        tarjeta_lectura, layout_lectura = tarjeta()

        self.etiqueta_ambiente = QLabel("Manipular Entorno / Sensor:")
        self.etiqueta_ambiente.setObjectName("Etiqueta")
        layout_lectura.addWidget(self.etiqueta_ambiente)

        self.etiqueta_pista = QLabel("(Arrastra para simular pérdida de frío)")
        self.etiqueta_pista.setObjectName("Etiqueta")
        layout_lectura.addWidget(self.etiqueta_pista)

        fila_deslizador = QHBoxLayout()
        fila_deslizador.setSpacing(10)
        self.deslizador = QSlider(Qt.Orientation.Horizontal)
        self.deslizador.setRange(int(AMBIENTE_MIN), int(AMBIENTE_MAX))
        self.deslizador.setValue(5)
        self.deslizador.setEnabled(False)
        self.deslizador.valueChanged.connect(self._emit_ambiente)
        fila_deslizador.addWidget(self.deslizador, 1)

        self.etiqueta_ambiente_valor = QLabel("5.0 °C")
        self.etiqueta_ambiente_valor.setMinimumWidth(64)
        self.etiqueta_ambiente_valor.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.etiqueta_ambiente_valor.setStyleSheet(f"color: {theme.AZUL}; font-size: 13px;")
        fila_deslizador.addWidget(self.etiqueta_ambiente_valor)
        layout_lectura.addLayout(fila_deslizador)

        separador = QLabel("")
        separador.setFixedHeight(1)
        separador.setStyleSheet(f"background-color: {theme.BORDE};")
        layout_lectura.addWidget(separador)

        # Lectura grande.
        self.etiqueta_valor = QLabel("--.- °C")
        self.etiqueta_valor.setObjectName("ValorGrande")
        self.etiqueta_valor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_lectura.addWidget(self.etiqueta_valor)

        # LED + nombre del estado.
        fila_led = QHBoxLayout()
        fila_led.setSpacing(10)
        self.led = Led(20)
        fila_led.addWidget(self.led)
        self.etiqueta_proceso = QLabel("ESTABLE")
        self.etiqueta_proceso.setObjectName("EstadoTexto")
        self.etiqueta_proceso.setStyleSheet(f"color: {theme.VERDE}; font-size: 15px; font-weight: 700;")
        fila_led.addWidget(self.etiqueta_proceso)
        fila_led.addStretch(1)
        layout_lectura.addLayout(fila_led)

        raiz.addWidget(tarjeta_lectura)

        # --- Tarjeta de configuracion ---
        tarjeta_config, layout_config = tarjeta("CONFIGURACIÓN", "ajustes")

        layout_fuente = QHBoxLayout()
        etiqueta_fuente = QLabel("Fuente de datos")
        etiqueta_fuente.setObjectName("Etiqueta")
        layout_fuente.addWidget(etiqueta_fuente, 1)
        self.combo_fuente = QComboBox()
        self.combo_fuente.addItem("Wokwi (MQTT)", FUENTE_MQTT)
        self.combo_fuente.addItem("Simulación local", FUENTE_LOCAL)
        self.combo_fuente.currentIndexChanged.connect(self._emit_fuente)
        layout_fuente.addWidget(self.combo_fuente)
        layout_config.addLayout(layout_fuente)

        layout_limites = QHBoxLayout()
        layout_limites.setSpacing(8)
        for texto, valor, sufijo in (
            ("LSC", 8.0, "°C"),
            ("LIC", 2.0, "°C"),
            ("OBJ", 5.0, "°C"),
        ):
            etiqueta = QLabel(texto)
            etiqueta.setObjectName("Etiqueta")
            layout_limites.addWidget(etiqueta)
            from PyQt6.QtWidgets import QDoubleSpinBox

            campo = QDoubleSpinBox()
            campo.setRange(-50.0, 80.0)
            campo.setDecimals(1)
            campo.setSingleStep(0.5)
            campo.setValue(valor)
            campo.setSuffix(" °C")
            campo.valueChanged.connect(self._emit_limites)
            layout_limites.addWidget(campo)
            if texto == "LSC":
                self.campo_lsc = campo
            elif texto == "LIC":
                self.campo_lic = campo
            else:
                self.campo_obj = campo
        layout_config.addLayout(layout_limites)

        self.boton_reiniciar = QPushButton("Reiniciar Métricas CEP")
        self.boton_reiniciar.clicked.connect(self.reiniciar.emit)
        layout_config.addWidget(self.boton_reiniciar)

        raiz.addWidget(tarjeta_config)
        raiz.addStretch(1)

    # ------------------------------ Señales -------------------------------
    def _emit_ambiente(self, valor: int) -> None:
        # Con la fuente Wokwi el ambiente se ajusta en el popup del sensor de
        # Wokwi, asi que el deslizador queda deshabilitado y no manda nada.
        if not self.deslizador.isEnabled():
            return
        self.etiqueta_ambiente_valor.setText(f"{valor:.1f} °C")
        self.ambiente_cambiado.emit(float(valor))

    def _emit_fuente(self, _indice: int) -> None:
        self.fuente_cambiada.emit(self.combo_fuente.currentData())

    def _emit_limites(self, _valor: float) -> None:
        self.limites_cambiados.emit(
            self.campo_lsc.value(), self.campo_lic.value(), self.campo_obj.value()
        )

    # ------------------------------ Actualizacion -------------------------
    def set_lectura(self, temperatura: float, estado: EstadoProceso) -> None:
        """Actualiza el valor grande, el LED y el nombre del estado."""
        self.etiqueta_valor.setText(f"{temperatura:.1f} °C")
        color = estado.color
        self.led.set_color(color)
        self.etiqueta_proceso.setText(estado.value)
        self.etiqueta_proceso.setStyleSheet(f"color: {color}; font-size: 15px; font-weight: 700;")

    def set_fuente(self, fuente: str) -> None:
        """Activa o desactiva el deslizador segun la fuente de datos.

        - Wokwi (MQTT): el ambiente se ajusta en el popup del DS18B20 de Wokwi,
          por lo que el deslizador queda deshabilitado.
        - Simulacion local: el deslizador fija la temperatura ambiente.
        """
        local = fuente == FUENTE_LOCAL
        self.deslizador.setEnabled(local)
        # Qt ignora el estilo :disabled del slider: se fuerza con estilo inline.
        self.deslizador.setStyleSheet("" if local else theme.SLIDER_ACTIVO)
        # Mantiene el desplegable sincronizado aunque la fuente se fije desde
        # codigo (no solo desde la UI).
        indice = self.combo_fuente.findData(fuente)
        if indice >= 0 and self.combo_fuente.currentIndex() != indice:
            self.combo_fuente.blockSignals(True)
            self.combo_fuente.setCurrentIndex(indice)
            self.combo_fuente.blockSignals(False)
        self.etiqueta_ambiente.setStyleSheet(
            f"color: {theme.TEXTO_SUAVE if not local else theme.TEXTO};"
        )
        if local:
            self.etiqueta_pista.setText("Deslizador activo en simulación local")
            self.etiqueta_ambiente_valor.setText(f"{self.deslizador.value():.1f} °C")
        else:
            self.etiqueta_pista.setText("Ajuste en el popup del DS18B20 en Wokwi")
            self.etiqueta_ambiente_valor.setText("--")

    def set_ambiente_valor(self, ambiente: float) -> None:
        """Sincroniza el deslizador y su etiqueta con el ambiente del modelo."""
        self.deslizador.blockSignals(True)
        self.deslizador.setValue(int(round(ambiente)))
        self.deslizador.blockSignals(False)
        self.etiqueta_ambiente_valor.setText(f"{int(round(ambiente)):.1f} °C")

    def set_conexion(self, conectado: bool, mensaje: str) -> None:
        """Actualiza la linea de estado de la placa."""
        color = theme.VERDE if conectado else theme.AMBAR
        self.etiqueta_estado.setText(mensaje)
        self.etiqueta_estado.setStyleSheet(f"color: {color}; font-size: 12px;")
