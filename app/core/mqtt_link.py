"""Enlace MQTT entre el ESP32 simulado en Wokwi y el panel de monitoreo.

Recibe la telemetria publicada en `TOPIC_TELEMETRY` y publica los limites de
control en `TOPIC_LIMITS` para que el firmware (y el OLED) los conozca.

Los callbacks de paho-mqtt llegan desde su propio hilo: se reemiten como
senales de Qt para que la interfaz se toque solo en el hilo principal.
"""

from __future__ import annotations

import json
import time

import paho.mqtt.client as mqtt
from PyQt6.QtCore import QObject, pyqtSignal


class MqttLink(QObject):
    """Cliente MQTT no bloqueante con reconexion automatica."""

    mensaje_recibido = pyqtSignal(dict)
    conexion_cambiada = pyqtSignal(str)
    detalle_error = pyqtSignal(str)

    def __init__(
        self,
        broker: str,
        puerto: int,
        topic_telemetria: str,
        topic_limites: str,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self.broker = broker
        self.puerto = puerto
        self.topic_telemetria = topic_telemetria
        self.topic_limites = topic_limites
        self.conectado = False
        self.ultimo_mensaje: dict | None = None

        self._cliente = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"cep-panel-{int(time.time())}",
            protocol=mqtt.MQTTv311,
        )
        self._cliente.reconnect_delay_set(min_delay=1, max_delay=8)
        self._cliente.on_connect = self._on_connect
        self._cliente.on_disconnect = self._on_disconnect
        self._cliente.on_message = self._on_message

    # ------------------------------ Ciclo de vida -------------------------
    def conectar(self) -> None:
        """Arranca la conexion en segundo plano (no bloquea la interfaz)."""
        try:
            self._cliente.connect_async(self.broker, self.puerto, keepalive=30)
            self._cliente.loop_start()
        except Exception as exc:  # noqa: BLE001
            self.detalle_error.emit(f"No se pudo iniciar MQTT: {exc}")
            self.conexion_cambiada.emit("error")

    def desconectar(self) -> None:
        """Cierra la conexion y detiene el bucle de red."""
        try:
            self._cliente.loop_stop()
            self._cliente.disconnect()
        except Exception:  # noqa: BLE001
            pass
        self.conectado = False

    def publicar_limites(self, lsc: float, lic: float, objetivo: float) -> None:
        """Envia los limites de control al firmware."""
        if not self.conectado:
            return
        payload = json.dumps({"lsc": round(lsc, 2), "lic": round(lic, 2), "obj": round(objetivo, 2)})
        try:
            self._cliente.publish(self.topic_limites, payload)
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------- Callbacks ----------------------------
    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            self.conectado = True
            client.subscribe(self.topic_telemetria)
            self.conexion_cambiada.emit("conectado")
        else:
            self.conectado = False
            self.conexion_cambiada.emit("error")
            self.detalle_error.emit(f"MQTT rechazado por {self.broker} (rc={reason_code})")

    def _on_disconnect(self, client, userdata, disconnect_flags=None, reason_code=None, properties=None):
        self.conectado = False
        self.conexion_cambiada.emit("desconectado")

    def _on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8", errors="replace"))
        except (ValueError, UnicodeDecodeError):
            return
        if not isinstance(data, dict) or "t" not in data:
            return
        self.ultimo_mensaje = data
        self.mensaje_recibido.emit(data)
