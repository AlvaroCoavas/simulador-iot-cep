@echo off
REM ===========================================================================
REM  Simulador IoT & CEP - Instalacion del entorno de DESARROLLO
REM
REM  Crea un entorno virtual, instala las dependencias de Python y de
REM  PlatformIO, y compila el firmware ESP32.
REM
REM  (El cliente final no necesita este script: usa la carpeta "release".)
REM ===========================================================================
setlocal
cd /d "%~dp0"
set PY=py

echo ============================================================
echo  Simulador IoT ^& Control Estadistico de Procesos (CEP)
echo  Instalacion del entorno de desarrollo
echo ============================================================
echo.

where %PY% >nul 2>nul
if errorlevel 1 (
    echo [ERROR] No se encontro Python.
    echo         Instala Python 3.11 o superior desde https://python.org
    echo         y marca "Add Python to PATH" durante la instalacion.
    echo.
    pause
    exit /b 1
)

echo [1/5] Comprobando Python...
%PY% --version
echo.

echo [2/5] Creando el entorno virtual (.venv)...
if not exist ".venv" (
    %PY% -m venv .venv
) else (
    echo       .venv ya existe, se reutiliza.
)
call ".venv\Scripts\activate.bat"
echo.

echo [3/5] Actualizando pip e instalando las dependencias de Python...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt
if errorlevel 1 goto :error
echo.

echo [4/5] Instalando PlatformIO (compilador del firmware ESP32)...
python -m pip install platformio
if errorlevel 1 goto :error
echo.

echo [5/5] Compilando el firmware ESP32...
echo       (la primera vez descarga el toolchain, puede tardar varios minutos)
python -m platformio run
if errorlevel 1 goto :error

echo.
echo ============================================================
echo  INSTALACION COMPLETADA
echo ============================================================
echo.
echo  Panel de monitoreo:
echo      .venv\Scripts\python -m app.main
echo.
echo  Simulador Wokwi:
echo      1) Abre esta carpeta en VS Code
echo      2) Panel Wokwi  ->  Start Simulation
echo.
pause
exit /b 0

:error
echo.
echo [ERROR] La instalacion fallo. Revisa el mensaje anterior.
echo         Si es un error de PlatformIO, revisa tu conexion a internet:
echo         la primera compilacion descarga el toolchain del ESP32.
echo.
pause
exit /b 1
