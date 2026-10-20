@echo off
REM ===========================================================================
REM  Panel de monitoreo IoT & Control Estadistico de Procesos (CEP)
REM ===========================================================================
cd /d "%~dp0"
py -m app.main %*
