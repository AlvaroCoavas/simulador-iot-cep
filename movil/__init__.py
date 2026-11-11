"""Version movil del panel de Control Estadistico de Procesos (CEP).

App Android (Kivy) que recibe la telemetria del ESP32 simulado en Wokwi por
MQTT y muestra la carta de control, los indicadores y los ajustes.

REUTILIZA el motor CEP del panel de escritorio (`app/core/cep_engine.py`) y la
configuracion de broker/topicos (`app/config.py`) sin duplicarlos: la app
movil es un SEGUNDO observador del mismo sistema, no una copia.

Regla de oro: esta app NUNCA publica en el topico de limites. Los limites de
control los cambia unicamente el panel de escritorio; aqui solo se muestran.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "1.0.0"
