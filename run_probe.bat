@echo off
REM ===========================================================================
REM  Lector de telemetria MQTT del simulador IoT & CEP
REM ===========================================================================
cd /d "%~dp0"
py tools\mqtt_probe.py %*
