"""Ventana principal: coordina hardware simulado, motor CEP y enlace MQTT."""

from __future__ import annotations

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QHBoxLayout, QWidget

from .. import config
from ..core.cep_engine import CepEngine, EstadoProceso
from ..core.mqtt_link import MqttLink
from ..core.sensor_model import ModeloSensor
from .cep_panel import CepPanel
from .hardware_panel import FUENTE_LOCAL, FUENTE_MQTT, HardwarePanel


class MainWindow(QWidget):
    """Panel de monitoreo con hardware simulado (izq.) y control CEP (der.)."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(config.TITULO)
        self.resize(1400, 880)

        # --- Modelo ---
        self.motor = CepEngine(lsc=8.0, lic=2.0, objetivo=5.0)
        self.sensor = ModeloSensor(valor_inicial=5.0, ambiente=5.0)
        self.fuente = FUENTE_MQTT

        # --- Interfaz ---
        self.panel_hardware = HardwarePanel()
        self.panel_cep = CepPanel()

        raiz = QHBoxLayout(self)
        raiz.setContentsMargins(18, 16, 18, 16)
        raiz.setSpacing(18)
        raiz.addWidget(self.panel_hardware)
        raiz.addWidget(self.panel_cep, 1)

        # --- Senales ---
        # OJO: los metodos conectados a senales deben tener identificadores ASCII.
        # PyQt6 6.11 sobre Python 3.14 provoca un access violation nativo al
        # conectar una senal a un metodo cuyo identificador lleva acentos.
        self.panel_hardware.reiniciar.connect(self.reiniciar_metricas)
        self.panel_hardware.fuente_cambiada.connect(self.cambiar_fuente)
        self.panel_hardware.ambiente_cambiado.connect(self.fijar_ambiente)
        self.panel_hardware.limites_cambiados.connect(self.cambiar_limites)

        # --- Enlace MQTT ---
        self.mqtt = MqttLink(
            broker=config.BROKER,
            puerto=config.PUERTO,
            topic_telemetria=config.TOPIC_TELEMETRIA,
            topic_limites=config.TOPIC_LIMITES,
            parent=self,
        )
        self.mqtt.mensaje_recibido.connect(self.recibir_lectura)
        self.mqtt.conexion_cambiada.connect(self.estado_conexion)

        # --- Temporizador de la simulacion local ---
        self.temporizador = QTimer(self)
        self.temporizador.setInterval(config.PERIODO_LOCAL_MS)
        self.temporizador.timeout.connect(self.tic_local)
        self.temporizador.start()

        # --- Estado inicial ---
        self.panel_hardware.set_fuente(self.fuente)
        self.panel_hardware.set_conexion(False, "Conectando al broker MQTT...")
        self.panel_hardware.set_lectura(0.0, EstadoProceso.ESTABLE)
        self.panel_cep.set_banner(EstadoProceso.ESTABLE)
        self.panel_cep.set_grafico(*self.motor.serie(config.VENTANA_GRAFICO), 8.0, 2.0, 5.0)
        self.panel_cep.set_indicadores(0.0, 0, 0.0, EstadoProceso.ESTABLE)
        self.mqtt.conectar()

    # ============================== Acciones ================================
    def tic_local(self) -> None:
        """Reloj de la simulacion local (1 lectura por segundo)."""
        if self.fuente != FUENTE_LOCAL:
            return
        temperatura = self.sensor.avanzar(config.PERIODO_LOCAL_MS / 1000.0)
        self.procesar_lectura(temperatura)

    def recibir_lectura(self, datos: dict) -> None:
        """Llega una lectura del ESP32 en Wokwi por MQTT."""
        if self.fuente != FUENTE_MQTT:
            return
        try:
            temperatura = float(datos["t"])
        except (KeyError, TypeError, ValueError):
            return
        self.procesar_lectura(temperatura)

    def procesar_lectura(self, temperatura: float) -> None:
        """Registra la muestra y refresca toda la interfaz."""
        muestra = self.motor.agregar(temperatura)

        self.panel_hardware.set_lectura(muestra.temperatura, muestra.estado)
        self.panel_cep.set_banner(muestra.estado)
        self.panel_cep.set_grafico(
            *self.motor.serie(config.VENTANA_GRAFICO),
            self.motor.lsc,
            self.motor.lic,
            self.motor.objetivo,
        )
        self.panel_cep.set_indicadores(
            self.motor.media_temporal,
            self.motor.puntos_fuera_de_limite,
            self.motor.indice_defectos,
            muestra.estado,
        )

    def cambiar_fuente(self, fuente: str) -> None:
        """Cambia entre MQTT (Wokwi) y simulacion local."""
        self.fuente = fuente
        self.panel_hardware.set_fuente(fuente)
        if fuente == FUENTE_LOCAL:
            # El deslizador y el modelo local deben partir del mismo ambiente.
            self.panel_hardware.set_ambiente_valor(self.sensor.ambiente)
            self.sensor.set_ambiente(self.sensor.ambiente)
            self.panel_hardware.set_conexion(True, "Estado: Simulación local activa")
        else:
            self.panel_hardware.set_conexion(
                self.mqtt.conectado,
                "Estado: Transmitiendo cada 1s"
                if self.mqtt.conectado
                else "Estado: Sin señal del sensor",
            )
            self.mqtt.conectar()

    def fijar_ambiente(self, ambiente: float) -> None:
        """El deslizador fija la temperatura ambiente de la simulacion local."""
        self.sensor.set_ambiente(ambiente)

    def cambiar_limites(self, lsc: float, lic: float, objetivo: float) -> None:
        """Actualiza los limites de control y los difunde al firmware."""
        self.motor.set_limites(lsc, lic, objetivo)
        self.mqtt.publicar_limites(lsc, lic, objetivo)
        self.panel_cep.set_grafico(
            *self.motor.serie(config.VENTANA_GRAFICO), lsc, lic, objetivo
        )
        self.panel_cep.set_indicadores(
            self.motor.media_temporal,
            self.motor.puntos_fuera_de_limite,
            self.motor.indice_defectos,
            self.motor.estado_actual(),
        )
        self.panel_cep.set_banner(self.motor.estado_actual())

    def reiniciar_metricas(self) -> None:
        """Borra las muestras acumuladas (no cambia los limites)."""
        self.motor.reiniciar()
        self.panel_cep.set_grafico(
            *self.motor.serie(config.VENTANA_GRAFICO),
            self.motor.lsc,
            self.motor.lic,
            self.motor.objetivo,
        )
        self.panel_cep.set_indicadores(0.0, 0, 0.0, EstadoProceso.ESTABLE)

    def estado_conexion(self, estado: str) -> None:
        """Refleja el estado del enlace MQTT en el panel de hardware."""
        if self.fuente != FUENTE_MQTT:
            return
        if estado == "conectado":
            self.panel_hardware.set_conexion(True, "Estado: Transmitiendo cada 1s")
        elif estado == "desconectado":
            self.panel_hardware.set_conexion(False, "Estado: Sin señal del sensor")
        else:
            self.panel_hardware.set_conexion(False, "Estado: Error de conexión MQTT")

    def closeEvent(self, event) -> None:  # noqa: N802
        self.temporizador.stop()
        self.mqtt.desconectar()
        super().closeEvent(event)
