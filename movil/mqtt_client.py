"""Cliente MQTT de la app movil.

Se suscribe a DOS topicos:

  * `.../telemetry` -> la temperatura que publica el ESP32 de Wokwi.
  * `.../limits`    -> los limites de control que publica el panel de
                       escritorio (esta app solo los LEE, nunca los escribe).

Los callbacks de paho-mqtt llegan en su propio hilo: se reemiten con
`Clock.schedule_once` para que la interfaz de Kivy se toque unicamente desde
el hilo principal.
"""

from __future__ import annotations

import json
import time
from typing import Callable

import paho.mqtt.client as mqtt
from kivy.clock import Clock

from . import config


class ClienteMqtt:
    """Suscripcion MQTT de solo lectura para la app movil."""

    def __init__(
        self,
        al_datos: Callable[[dict], None],
        al_limites: Callable[[dict], None],
        al_estado: Callable[[str, str], None],
        broker: str = config.BROKER,
        puerto: int = config.PUERTO,
        topic_telemetria: str = config.TOPIC_TELEMETRIA,
        topic_limites: str = config.TOPIC_LIMITES,
    ):
        self.al_datos = al_datos
        self.al_limites = al_limites
        self.al_estado = al_estado
        self.broker = broker
        self.puerto = puerto
        self.topic_telemetria = topic_telemetria
        self.topic_limites = topic_limites
        self.conectado = False
        self.ultimo_mensaje: dict | None = None

        self._cliente = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"cep-movil-{int(time.time())}",
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
            self._estado("conectando", f"Conectando a {self.broker}")
        except Exception as exc:  # noqa: BLE001
            self._estado("error", f"No se pudo iniciar MQTT: {exc}")

    def desconectar(self) -> None:
        """Cierra la conexion y detiene el bucle de red."""
        try:
            self._cliente.loop_stop()
            self._cliente.disconnect()
        except Exception:  # noqa: BLE001
            pass
        self.conectado = False

    # ------------------------------- Callbacks ----------------------------
    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            self.conectado = True
            # Dos suscripciones: datos del sensor y limites del escritorio.
            client.subscribe(self.topic_telemetria)
            client.subscribe(self.topic_limites)
            self._estado("conectado", f"Conectado a {self.broker}")
        else:
            self.conectado = False
            self._estado("error", f"MQTT rechazado por {self.broker} (rc={reason_code})")

    def _on_disconnect(self, client, userdata, disconnect_flags=None, reason_code=None, properties=None):
        self.conectado = False
        self._estado("desconectado", "Sin conexion con el broker")

    def _on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8", errors="replace"))
        except (ValueError, UnicodeDecodeError):
            return
        if not isinstance(data, dict):
            return
        topic = msg.topic or ""
        if topic == self.topic_limites:
            self._limites(data)
        elif "t" in data:
            self.ultimo_mensaje = data
            self._datos(data)

    # ------------------------------ Salto al hilo UI ----------------------
    def _datos(self, data: dict) -> None:
        Clock.schedule_once(lambda _dt: self.al_datos(data), 0)

    def _limites(self, data: dict) -> None:
        Clock.schedule_once(lambda _dt: self.al_limites(data), 0)

    def _estado(self, estado: str, detalle: str) -> None:
        Clock.schedule_once(lambda _dt: self.al_estado(estado, detalle), 0)
