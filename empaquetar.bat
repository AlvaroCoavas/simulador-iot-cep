@echo off
REM ===========================================================================
REM  Empaqueta la carpeta "release" para entregar al cliente.
REM
REM  Genera un ZIP autocontenido con:
REM    - SimuladorCEP.exe   : el panel de monitoreo (no necesita Python)
REM    - firmware.bin/.elf  : el firmware ESP32 ya compilado
REM    - diagram.json       : el circuito simulado
REM    - wokwi.toml         : configuracion apuntando al firmware incluido
REM    - LEEME.txt          : instrucciones para el cliente
REM
REM  El cliente solo necesita: descomprimir, abrir en VS Code y darle a
REM  "Start Simulation" en la extension de Wokwi. Sin Python, sin PlatformIO.
REM ===========================================================================
setlocal
cd /d "%~dp0"

echo ============================================================
echo  Empaquetado de la entrega para el cliente
echo ============================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] No existe el entorno virtual .venv
    echo         Ejecuta primero:  instalar.bat
    echo.
    pause
    exit /b 1
)

echo [1/4] Compilando el firmware ESP32...
call ".venv\Scripts\activate.bat"
python -m platformio run
if errorlevel 1 goto :error
echo.

echo [2/4] Generando SimuladorCEP.exe...
python -m PyInstaller --onefile --windowed --name "SimuladorCEP" --icon "assets\app.ico" --noconfirm --clean --log-level WARN "simulador.py"
if errorlevel 1 goto :error
echo.

echo [3/4] Armando la carpeta release...
if exist "release" rmdir /s /q "release"
mkdir "release"
copy "dist\SimuladorCEP.exe" "release\" >nul
copy ".pio\build\esp32dev\firmware.bin" "release\" >nul
copy ".pio\build\esp32dev\firmware.elf" "release\" >nul
copy "diagram.json" "release\" >nul
copy "GUIA_CLIENTE.md" "release\LEEME.txt" >nul
copy "requirements.txt" "release\" >nul
echo       release\SimuladorCEP.exe
echo       release\firmware.bin
echo       release\firmware.elf
echo       release\diagram.json
echo       release\wokwi.toml
echo       release\LEEME.txt
echo.

REM wokwi.toml de la entrega: apunta al firmware incluido en la misma carpeta.
(
    echo [wokwi]
    echo version = 1
    echo firmware = 'firmware.bin'
    echo elf = 'firmware.elf'
) > "release\wokwi.toml"
echo.

echo [4/4] Comprimiendo...
if exist "SimuladorCEP-entrega.zip" del "SimuladorCEP-entrega.zip"
powershell -NoProfile -Command "Compress-Archive -Path 'release\*' -DestinationPath 'SimuladorCEP-entrega.zip' -Force"
echo.
echo ============================================================
echo  ENTREGA LISTA
echo ============================================================
echo   Carpeta : release\
echo   ZIP     : SimuladorCEP-entrega.zip
echo.
pause
exit /b 0

:error
echo.
echo [ERROR] Fallo el empaquetado (revisa el mensaje anterior).
echo.
pause
exit /b 1
