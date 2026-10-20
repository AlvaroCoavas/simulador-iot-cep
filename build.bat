@echo off
REM ===========================================================================
REM  Compila el firmware ESP32 del simulador IoT & CEP
REM ===========================================================================
cd /d "%~dp0"
echo [1/2] Compilando firmware (PlatformIO)...
py -m platformio run
if errorlevel 1 (
    echo.
    echo [ERROR] La compilacion fallo. Revisa el log de arriba.
    pause
    exit /b 1
)
echo.
echo [2/2] Compilacion OK.
echo Artefactos:
dir /b ".pio\build\esp32dev\firmware.*"
echo.
echo Ahora en VS Code: "Wokwi: Start Simulator"
pause
