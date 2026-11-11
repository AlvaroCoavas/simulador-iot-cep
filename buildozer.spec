[app]

# (str) Nombre de la aplicacion que aparece en el launcher del movil.
title = Simulador CEP

# (str) Identificador unico del paquete.
package.name = cepmovil
package.domain = org.diying.cep

# (str) Carpeta con el codigo fuente (la raiz del proyecto).
source.dir = .

# (list) Ficheros que se empaquetan en el APK.
# OJO: buildozer solo copia lo que aparece aqui. El motor CEP del escritorio
# (`app/core/cep_engine.py`) se incluye para reutilizarlo tal cual.
source.include_patterns = main.py,movil/*.py,app/__init__.py,app/config.py,app/core/__init__.py,app/core/cep_engine.py,assets/app_movil.png

# (list) Carpetas que nunca se copian (build, firmware, entregas...).
source.exclude_dirs = .git,.pio,.github,.agents,.vscode,build,dist,release,entrega,tools,src,include,__pycache__,preview_*.png

# (str) Version de la aplicacion.
version = 1.0.0

# (list) Dependencias que se compilan dentro del APK.
requirements = python3,kivy,paho-mqtt

# (str) Orientacion de la pantalla.
orientation = portrait

# (str) Icono y pantalla de inicio.
icon.filename = %(source.dir)s/assets/app_movil.png
presplash.filename = %(source.dir)s/assets/app_movil.png
android.presplash_color = #EAF2FB

# (list) Permisos: INTERNET es imprescindible para el MQTT.
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK

# (int) API de Android objetivo y minima.
android.api = 34
android.minapi = 24

# (str) Version del NDK que usa python-for-android.
android.ndk = 25b
android.ndk_api = 21

# (list) Arquitecturas: arm64 para telefonos modernos, x86_64 para el emulador.
android.archs = arm64-v8a,armeabi-v7a,x86_64

# (bool) Permitir copia de seguridad.
android.allow_backup = True

# (bool) Aceptar automaticamente las licencias del SDK al compilar.
android.accept_sdk_license = True

# (bool) Mantener la pantalla encendida mientras la app esta en primer plano.
android.wakelock = False

# (str) Formato del artefacto de release.
android.release_artifact = apk

[buildozer]

# (int) Nivel de log (2 = verbose).
log_level = 2

# (int) Avisar si se compila como root (0 = no avisar).
warn_on_root = 0

# (str) Directorio de salida de los artefactos.
build_dir = ./.buildozer
bin_dir = ./bin
