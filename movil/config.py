"""Configuracion propia de la app movil.

El broker y los topicos NO se duplican aqui: se importan de `app/config.py`,
que es la unica fuente de verdad del proyecto.
"""

from __future__ import annotations

import os

from app import config as config_comun

# --------------------------- Broker y topicos ------------------------------
# (heredados del panel de escritorio: una sola fuente de verdad)
BROKER = config_comun.BROKER
PUERTO = config_comun.PUERTO
TOPIC_TELEMETRIA = config_comun.TOPIC_TELEMETRIA
TOPIC_LIMITES = config_comun.TOPIC_LIMITES

# ------------------------------- Presentacion -------------------------------
TITULO = "Temperatura"
SUBTITULO = "Monitoreo en tiempo real"

#: Ventana de puntos que se dibujan en la carta (se reduce si hay mas).
MAX_PUNTOS_GRAFICA = 900

#: Intervalos de muestreo del historial local (segundos).
INTERVALOS = (1, 5, 10, 30, 60)
INTERVALO_POR_DEFECTO = 5

#: Dias de historial que se conservan en la base local.
DIAS_RETENIDOS = 31

#: Fuentes de datos disponibles.
FUENTE_MQTT = "Wokwi (MQTT)"
FUENTE_LOCAL = "Simulacion local"

#: Segundos sin recibir telemetria antes de marcar la conexion como perdida.
TIMEOUT_SIN_DATOS = 8


def ruta_base_datos() -> str:
    """Ruta del fichero SQLite donde se guarda el historial local.

    En Android la carpeta privada de la aplicacion (`app.user_data_dir`) es
    la unica escritura con permiso; en escritorio cae en el directorio del
    usuario.
    """
    try:
        from kivy.utils import platform  # noqa: PLC0415

        if platform == "android":
            from android.storage import app_storage_path  # noqa: PLC0415

            return os.path.join(app_storage_path(), "cep_movil.db")
    except Exception:  # noqa: BLE001 - cualquier fallo cae al caso de escritorio
        pass
    return os.path.join(os.path.expanduser("~"), ".cep_movil", "cep_movil.db")
