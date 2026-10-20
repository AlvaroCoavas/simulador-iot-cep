"""Panel izquierdo: HARDWARE SIMULADO."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
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

# Rango valido del sensor DS18B20 (C).
RANGO_SENSOR_MIN = -55.0
RANGO_SENSOR_MAX = 125.0

# Limites de control por defecto (C).
LSC_POR_DEFECTO = 8.0
LIC_POR_DEFECTO = 2.0
OBJ_POR_DEFECTO = 5.0

# Opciones del intervalo de registro (s) para la tabla y el CSV.
INTERVALOS = (1, 5, 10, 30, 60)
INTERVALO_POR_DEFECTO = 5


class HardwarePanel(QWidget):
    """Estado del hardware virtual: valor de temperatura, LED y controles."""

    reiniciar = pyqtSignal()
    fuente_cambiada = pyqtSignal(str)
    ambiente_cambiado = pyqtSignal(float)
    limites_cambiados = pyqtSignal(float, float, float)
    intervalo_cambiado = pyqtSignal(int)

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
        for texto, valor in (
            ("LSC", LSC_POR_DEFECTO),
            ("LIC", LIC_POR_DEFECTO),
            ("OBJ", OBJ_POR_DEFECTO),
        ):
            etiqueta = QLabel(texto)
            etiqueta.setObjectName("Etiqueta")
            layout_limites.addWidget(etiqueta)

            campo = QDoubleSpinBox()
            campo.setRange(RANGO_SENSOR_MIN, RANGO_SENSOR_MAX)
            campo.setDecimals(1)
            campo.setSingleStep(0.5)
            campo.setValue(valor)
            campo.setSuffix(" °C")
            # Se valida al cambiar el valor y tambien al salir del campo
            # o pulsar Enter.
            campo.valueChanged.connect(self._emit_limites)
            campo.editingFinished.connect(self._emit_limites)
            layout_limites.addWidget(campo)
            if texto == "LSC":
                self.campo_lsc = campo
            elif texto == "LIC":
                self.campo_lic = campo
            else:
                self.campo_obj = campo
        layout_config.addLayout(layout_limites)

        # Mensaje de error de los limites (oculto mientras sean validos).
        self.etiqueta_error_limites = QLabel("")
        self.etiqueta_error_limites.setStyleSheet(f"color: {theme.ROJO}; font-size: 11px;")
        self.etiqueta_error_limites.setWordWrap(True)
        self.etiqueta_error_limites.setVisible(False)
        layout_config.addWidget(self.etiqueta_error_limites)

        # --- Intervalo de registro (tabla y CSV) ---
        layout_intervalo = QHBoxLayout()
        etiqueta_intervalo = QLabel("Intervalo de registro")
        etiqueta_intervalo.setObjectName("Etiqueta")
        layout_intervalo.addWidget(etiqueta_intervalo, 1)
        self.combo_intervalo = QComboBox()
        for segundos in INTERVALOS:
            self.combo_intervalo.addItem(f"{segundos} s", segundos)
        self.combo_intervalo.setCurrentIndex(INTERVALOS.index(INTERVALO_POR_DEFECTO))
        self.combo_intervalo.currentIndexChanged.connect(self._emit_intervalo)
        layout_intervalo.addWidget(self.combo_intervalo)
        layout_config.addLayout(layout_intervalo)

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

    def _emit_limites(self, _valor: float | None = None) -> None:
        """Valida los limites y los aplica solo si son correctos.

        Si la combinacion es invalida NO se emite nada: el motor CEP y el
        firmware se quedan con los ultimos limites validos.
        """
        try:
            ok, mensaje, campo = self._validar_limites()
            if not ok:
                self._mostrar_error_limites(mensaje, campo)
                return
            self._mostrar_error_limites("", None)
            self.limites_cambiados.emit(
                self.campo_lsc.value(), self.campo_lic.value(), self.campo_obj.value()
            )
        except Exception as exc:  # noqa: BLE001
            # PyQt aborta el proceso si una excepcion escapa de un slot.
            self.etiqueta_error_limites.setText(f"No se pudieron validar los limites: {exc}")
            self.etiqueta_error_limites.setVisible(True)

    def _emit_intervalo(self, _indice: int) -> None:
        """El intervalo de registro solo afecta a la tabla y al CSV."""
        self.intervalo_cambiado.emit(int(self.combo_intervalo.currentData()))

    # ------------------------------ Validacion ----------------------------
    def _validar_limites(self) -> tuple[bool, str, str | None]:
        """Comprueba los limites de control.

        Devuelve (valido, mensaje, campo_problematico) donde el campo es
        "lsc", "lic" u "obj".
        """
        lsc = self.campo_lsc.value()
        lic = self.campo_lic.value()
        obj = self.campo_obj.value()

        if not (RANGO_SENSOR_MIN <= lic <= RANGO_SENSOR_MAX):
            return (
                False,
                f"LIC debe estar entre {RANGO_SENSOR_MIN:g} y {RANGO_SENSOR_MAX:g} °C "
                f"(rango del sensor)",
                "lic",
            )
        if not (RANGO_SENSOR_MIN <= lsc <= RANGO_SENSOR_MAX):
            return (
                False,
                f"LSC debe estar entre {RANGO_SENSOR_MIN:g} y {RANGO_SENSOR_MAX:g} °C "
                f"(rango del sensor)",
                "lsc",
            )
        if lic >= obj:
            return False, "LIC debe ser menor que el objetivo", "lic"
        if lsc <= obj:
            return False, "LSC debe ser mayor que el objetivo", "lsc"
        if not (lic < obj < lsc):
            return False, "El objetivo debe estar entre LIC y LSC", "obj"
        return True, "", None

    def _mostrar_error_limites(self, mensaje: str, campo: str | None) -> None:
        """Marca en rojo el campo problema y muestra el mensaje."""
        for nombre, widget in (
            ("lsc", self.campo_lsc),
            ("lic", self.campo_lic),
            ("obj", self.campo_obj),
        ):
            marcado = nombre == campo
            if bool(widget.property("error")) != marcado:
                widget.setProperty("error", marcado)
                # Repintar el widget para que el estilo tenga en cuenta la
                # propiedad dinamica. Ojo: el metodo polish() vive en el
                # estilo, no en el widget.
                widget.style().unpolish(widget)
                widget.style().polish(widget)
        self.etiqueta_error_limites.setText(mensaje)
        self.etiqueta_error_limites.setVisible(bool(mensaje))

    def limites_son_validos(self) -> bool:
        """True si los limites del formulario cumplen las reglas."""
        return self._validar_limites()[0]

    def restablecer_limites_si_invalidos(self) -> bool:
        """Vuelve a los limites por defecto si los actuales no son validos.

        Devuelve True si los restauro.
        """
        if self.limites_son_validos():
            return False
        for campo, valor in (
            (self.campo_lsc, LSC_POR_DEFECTO),
            (self.campo_lic, LIC_POR_DEFECTO),
            (self.campo_obj, OBJ_POR_DEFECTO),
        ):
            campo.blockSignals(True)
            campo.setValue(valor)
            campo.blockSignals(False)
        self._emit_limites()
        return True

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
