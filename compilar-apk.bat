@echo off
setlocal enabledelayedexpansion
rem ============================================================================
rem  Compila el APK de la app movil (Kivy) usando buildozer dentro de Docker.
rem
rem  OJO: Gradle y aapt2 NO soportan rutas con espacios ni caracteres
rem  especiales, asi que el proyecto se copia a C:\build\cepmovil (ASCII)
rem  antes de compilar y el APK se devuelve a la carpeta bin\ del proyecto.
rem
rem  Uso:  compilar-apk.bat  [debug^|release]
rem ============================================================================

set "MODO=%~1"
if "%MODO%"=="" set "MODO=debug"

set "RAIZ=%~dp0"
set "ORIGEN=%RAIZ%"
set "TRABAJO=C:\build\cepmovil"
set "SALIDA=%RAIZ%bin"

echo.
echo ============================================================
echo   Compilando el APK de la app movil  (modo: %MODO%)
echo ============================================================
echo.

rem --- 1. Docker disponible y en marcha ---------------------------------------
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker no esta en marcha.
    echo         Abre "Docker Desktop" y vuelve a ejecutar este script.
    echo         Alternativa: compila el APK desde GitHub Actions
    echo         (pestana Actions ^> workflow "Compilar APK Android" ^> Run workflow).
    exit /b 1
)

rem --- 2. Copia el codigo a una ruta sin espacios -----------------------------
echo [1/4] Preparando %TRABAJO% ...
if exist "%TRABAJO%" rmdir /s /q "%TRABAJO%"
mkdir "%TRABAJO%" 2>nul
mkdir "%TRABAJO%\movil" 2>nul
mkdir "%TRABAJO%\movil\ui" 2>nul
mkdir "%TRABAJO%\app" 2>nul
mkdir "%TRABAJO%\app\core" 2>nul
mkdir "%TRABAJO%\assets" 2>nul

copy "%ORIGEN%main.py"                 "%TRABAJO%\"        >nul
copy "%ORIGEN%buildozer.spec"          "%TRABAJO%\"        >nul
copy "%ORIGEN%movil\*.py"              "%TRABAJO%\movil\"   >nul
copy "%ORIGEN%movil\ui\*.py"           "%TRABAJO%\movil\ui\" >nul
copy "%ORIGEN%app\__init__.py"         "%TRABAJO%\app\"     >nul
copy "%ORIGEN%app\config.py"           "%TRABAJO%\app\"     >nul
copy "%ORIGEN%app\core\__init__.py"    "%TRABAJO%\app\core\" >nul
copy "%ORIGEN%app\core\cep_engine.py"  "%TRABAJO%\app\core\" >nul
copy "%ORIGEN%assets\app_movil.png"    "%TRABAJO%\assets\"  >nul

if not exist "%TRABAJO%\movil\main.py" (
    echo [ERROR] No se ha copiado el codigo. Revisa las rutas.
    exit /b 1
)
echo       codigo copiado.

rem --- 3. Compila dentro del contenedor ---------------------------------------
echo [2/4] Compilando (la primera vez descarga el SDK de Android, puede tardar 20-40 min)...
echo.
docker run --rm ^
    -v "%TRABAJO%:/home/user/hostcwd" ^
    -v "%USERPROFILE%\.buildozer:/home/user/.buildozer" ^
    kivy/buildozer:latest android %MODO%
if errorlevel 1 (
    echo.
    echo [ERROR] La compilacion ha fallado. Revisa el log de arriba.
    exit /b 1
)

rem --- 4. Recoge el APK ------------------------------------------------------
echo.
echo [3/4] Recogiendo el APK ...
if not exist "%TRABAJO%\bin" (
    echo [ERROR] No se ha generado ningun APK en %TRABAJO%\bin
    exit /b 1
)
if not exist "%SALIDA%" mkdir "%SALIDA%"
copy "%TRABAJO%\bin\*.apk" "%SALIDA%\" >nul

echo.
echo [4/4] Listo.
echo.
echo ============================================================
echo   APK generado en:
for %%f in ("%SALIDA%\*.apk") do echo     %%~nxf   (%%~zf bytes)
echo.
echo   Para instalarlo en un telefono:
echo     adb install "%SALIDA%\*.apk"
echo   Para instalarlo en el emulador:
echo     adb -e install "%SALIDA%\*.apk"
echo ============================================================
echo.

endlocal
