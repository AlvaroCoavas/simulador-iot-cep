#!/usr/bin/env python
"""
mqtt_probe.py  -  Lector de consola para el simulador IoT & CEP.

Se suscribe al topic de telemetria del ESP32 simulado en Wokwi y muestra
cada lectura que llega del sensor DS18B20.

Uso:
    python tools/mqtt_probe.py
    python tools/mqtt_probe.py --broker test.mosquitto.org --duration 60
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
import time
from datetime import datetime

import paho.mqtt.client as mqtt

DEFAULT_BROKER = "broker.emqx.io"
DEFAULT_PORT = 1883
DEFAULT_TOPIC = "cep/sensor/diyin-cep-7k3q2026/telemetry"
FALLBACK_BROKERS = ["test.mosquitto.org", "broker.hivemq.com"]

# Variables globales para el modo --dump (escribe cada mensaje a un archivo).
received: list[str] = []
running = True


def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def make_callbacks(broker_name: str, topic: str, dump_file: str | None):
    state = {"count": 0, "connected": False, "last": None}

    def on_connect(client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            state["connected"] = True
            print(f"[{_now()}] CONECTADO a {broker_name}")
            print(f"[{_now()}] Suscribiendome a: {topic}")
            client.subscribe(topic)
        else:
            state["connected"] = False
            print(f"[{_now()}] CONEXION RECHAZADA a {broker_name} (rc={reason_code})")

    def on_disconnect(client, userdata, disconnect_flags=None, reason_code=None, properties=None):
        state["connected"] = False
        print(f"[{_now()}] DESCONECTADO de {broker_name} (rc={reason_code})")

    def on_message(client, userdata, msg):
        state["count"] += 1
        state["last"] = msg.payload.decode("utf-8", errors="replace")
        try:
            data = json.loads(state["last"])
            temp = data.get("t")
            seq = data.get("seq")
            dev = data.get("dev")
            print(f"[{_now()}] #{seq:<5} T={temp} C   dev={dev}   raw={state['last']}")
        except Exception:
            print(f"[{_now()}] {state['last']}")
        if dump_file:
            with open(dump_file, "a", encoding="utf-8") as fh:
                fh.write(f"{_now()}\t{state['last']}\n")

    return on_connect, on_disconnect, on_message, state


def connect_and_listen(
    broker: str, port: int, topic: str, duration: int, dump_file: str | None
) -> int:
    """Conecta, escucha y devuelve el numero de mensajes recibidos."""
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"cep-probe-{int(time.time())}",
        protocol=mqtt.MQTTv311,
    )
    client.reconnect_delay_set(min_delay=1, max_delay=8)

    on_connect, on_disconnect, on_message, state = make_callbacks(broker, topic, dump_file)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    print("=" * 74)
    print(" SIMULADOR IoT & CEP  -  Lector de telemetria MQTT")
    print("=" * 74)
    print(f" Broker : {broker}:{port}")
    print(f" Topico : {topic}")
    print("-" * 74)
    print(" Esperando lecturas del ESP32... (Ctrl+C para salir)")
    print()

    try:
        client.connect(broker, port, keepalive=30)
    except Exception as exc:  # noqa: BLE001
        print(f"[{_now()}] ERROR al conectar a {broker}: {exc}")
        return -1

    client.loop_start()

    deadline = time.time() + duration if duration > 0 else None
    try:
        while running:
            time.sleep(0.25)
            if deadline and time.time() > deadline:
                break
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        try:
            client.disconnect()
        except Exception:  # noqa: BLE001
            pass

    print()
    print("-" * 74)
    print(f" Mensajes recibidos: {state['count']}")
    if state["last"]:
        print(f" Ultimo payload    : {state['last']}")
    print("-" * 74)
    return state["count"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Lector MQTT del simulador CEP")
    parser.add_argument("--broker", default=DEFAULT_BROKER, help="Broker MQTT")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Puerto MQTT")
    parser.add_argument("--topic", default=DEFAULT_TOPIC, help="Topico de telemetria")
    parser.add_argument(
        "--duration", type=int, default=0, help="Segundos a escuchar (0 = infinito)"
    )
    parser.add_argument(
        "--fallback",
        action="store_true",
        help="Si el broker falla, prueba automaticamente los brokers alternativos",
    )
    parser.add_argument("--dump", default=None, help="Archivo donde guardar cada mensaje")
    args = parser.parse_args()

    brokers = [args.broker]
    if args.fallback:
        brokers += [b for b in FALLBACK_BROKERS if b != args.broker]

    for broker in brokers:
        count = connect_and_listen(broker, args.port, args.topic, args.duration, args.dump)
        if count > 0:
            print(f"\n[OK] Datos recibidos correctamente desde {broker}")
            return 0
        if count == 0 and args.duration == 0:
            print(
                f"\n[WARN] No llego ningun mensaje desde {broker}.\n"
                "       Revisa: (1) la simulacion de Wokwi esta corriendo,\n"
                "       (2) el ESP32 se conecto al WiFi Wokwi-GUEST,\n"
                "       (3) el broker es alcanzable desde esta PC."
            )
        if not args.fallback or broker == brokers[-1]:
            break
        print(f"\n[INFO] {broker} no sirvio datos, probando {brokers[brokers.index(broker) + 1]}...")

    return 1


def _handle_sigint(signum, frame):  # noqa: ARG001
    global running
    running = False
    print("\n[INFO] Interrumpido por el usuario.")


signal.signal(signal.SIGINT, _handle_sigint)

if __name__ == "__main__":
    sys.exit(main())
