"""Parametros de configuracion del panel de monitoreo CEP."""

from __future__ import annotations

# ------------------------------- Broker MQTT -------------------------------
BROKER = "broker.emqx.io"
PUERTO = 1883

# --------------------------------- Topicos ---------------------------------
TOPIC_BASE = "cep/sensor/diyin-cep-7k3q2026"
TOPIC_TELEMETRIA = f"{TOPIC_BASE}/telemetry"
TOPIC_LIMITES = f"{TOPIC_BASE}/limits"

# ------------------------------- Presentacion ------------------------------
#: Numero de muestras visibles en la carta de control.
VENTANA_GRAFICO = 60
#: Periodo del temporizador de la simulacion local (ms).
PERIODO_LOCAL_MS = 1000
#: Titulo de la ventana.
TITULO = "Simulador IoT & Control Estadístico de Procesos (CEP)"
