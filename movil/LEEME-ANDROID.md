# App móvil Android — guía paso a paso

Versión móvil del panel de Control Estadístico de Procesos (CEP), escrita en
**Kivy** (Python). Recibe los datos del ESP32 simulado en Wokwi por MQTT y
muestra las mismas cuatro pantallas de la imagen de referencia.

---

## 1. Qué hace y qué NO hace

| | |
|---|---|
| ✅ **Hace** | Recibe la temperatura por MQTT, calcula el estado CEP, dibuja la carta de control, guarda historial local, permite elegir fuente de datos e intervalo de muestreo. |
| ❌ **NO hace** | **No cambia los límites de control**: los modifica el panel de escritorio y esta app **solo los muestra**. Es la única forma de que el móvil, el escritorio y el OLED del ESP32 coincidan siempre. |

La lógica del CEP **no está duplicada**: la app importa el mismo motor del
panel de escritorio.

```
app/core/cep_engine.py   <- motor CEP (clasificación, media, índice de defectos)
      ^                              ^
      |                              |
app/ui/*  (PyQt6)          movil/*  (Kivy)   <- el panel de escritorio y la app móvil
```

---

## 2. Requisitos

| Para… | Necesitas |
|---|---|
| Probar en el PC | Python **3.14** (`py -3.14`) + Kivy. Ojo: Kivy no tiene ruedas para Python 3.15. |
| Compilar el APK (CI) | Nada: se hace en GitHub Actions. |
| Compilar el APK (local) | Docker Desktop en marcha. |
| Probar en el emulador | Android SDK con `emulator` + una imagen del sistema. |
| Probar en un teléfono | El teléfono con **depuración USB** activada. |

```powershell
# Instalar las dependencias de la app móvil (Python 3.14)
py -3.14 -m pip install -r movil\requirements.txt
```

---

## 3. Opción A — Compilar el APK en GitHub Actions (recomendada)

No instala nada en tu ordenador y no consume disco. El APK sale como
**artefacto descargable**.

1. Sube los cambios al repositorio:
   ```powershell
   git add -A
   git commit -m "Actualiza la app movil"
   git push origin main
   ```
2. Abre el repositorio en GitHub → pestaña **Actions**.
3. En la lista de la izquierda, elige **Compilar APK Android**.
4. Clic en **Run workflow** → **Run workflow** (rama `main`).
5. Espera a que termine (la primera vez tarda **20-40 minutos**: descarga el
   SDK de Android, el NDK y compila Python para Android). Las siguientes
   tardan menos gracias a la caché.
6. Al terminar, en la parte inferior de la ejecución hay un artefacto:
   **`SimuladorCEP-movil-apk`**. Descárgalo (es un ZIP con el `.apk`).
7. Para publicarlo como descarga para el cliente, crea una etiqueta y súbela:
   ```powershell
   git tag v1.1.0
   git push origin v1.1.0
   ```
   La workflow se dispara sola y adjunta el `.apk` a la *release*.

### Automatizarlo desde la terminal

```powershell
gh workflow run android.yml --repo AlvaroCoavas/simulador-iot-cep
gh run watch --repo AlvaroCoavas/simulador-iot-cep
```

---

## 4. Opción B — Compilar en local con Docker

> Gradle y `aapt2` **no admiten rutas con espacios ni acentos**, así que el
> script copia el proyecto a `C:\build\cepmovil` antes de compilar y devuelve
> el APK a la carpeta `bin\` del proyecto.

1. Arranca **Docker Desktop** y espera a que el icono deje de girar.
2. Ejecuta:
   ```powershell
   .\compilar-apk.bat            # APK de depuracion
   .\compilar-apk.bat release    # APK optimizado
   ```
3. El APK queda en `bin\SimuladorCEP-movil-1.0.0-arm64-v8a_armeabi-v7a_x86_64-debug.apk`.

La primera compilación descarga ~4 GB (SDK + NDK) en `%USERPROFILE%\.buildozer`;
las siguientes son mucho más rápidas.

---

## 5. Probar en el emulador de Android Studio

### 5.1 Instalar el emulador y una imagen del sistema (por consola)

```powershell
$sdk = "$env:LOCALAPPDATA\Android\Sdk"

# Ver los paquetes disponibles
& "$sdk\cmdline-tools\latest\bin\sdkmanager.bat" --list

# Instalar el emulador y la imagen de Android 35 (unos 1,8 GB)
& "$sdk\cmdline-tools\latest\bin\sdkmanager.bat" "emulator" "system-images;android-35;google_apis;x86_64"

# Aceptar las licencias (escribe "y" repetidas veces)
& "$sdk\cmdline-tools\latest\bin\sdkmanager.bat" --licenses
```

También puedes hacerlo desde **Android Studio → More Actions → SDK Manager →
SDK Tools → Android Emulator** y **SDK Platforms → Android 15 → Google APIs
Intel x86_64 Atom System Image**.

### 5.2 Crear el dispositivo virtual

Desde **Android Studio → Device Manager → + (Create Virtual Device)**:

1. Tipo: **Phone** → modelo **Pixel 7** → *Next*.
2. Imagen: **Google APIs Intel x86_64 Atom System Image** (API 35) → *Next*.
3. Cámara y almacenamiento: los valores por defecto → *Finish*.
4. Clic en la flecha ▶ para **arrancar el emulador**.

O desde la consola:

```powershell
$emulador = "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe"
& $emulador -list-avds
& $emulador -avd Pixel_7_API_35      # arranca el emulador
```

### 5.3 Instalar la app en el emulador

```powershell
# El emulador debe estar arrancado (tarda 1-2 minutos en levantar)
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" wait-for-device

# Instalar el APK
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" install bin\*.apk

# Ver los logs de la app
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" logcat -s python
```

### 5.4 Comprobar que funciona

1. En VS Code: extensión **Wokwi** → **▶ Start Simulation**.
2. En el emulador: la app debe abrir y mostrar **"Conectado"** en verde.
3. Mueve el control *Temperature* del DS18B20 en el diagrama de Wokwi: la
   temperatura, el LED y la gráfica del móvil cambian al instante.
4. **Prueba de desconexión**: para la simulación en Wokwi y observa cómo el
   badge pasa a **"Sin conexión"** (en rojo) y la app **no se cierra**.
5. Comprueba que el móvil y el panel de escritorio muestran **lo mismo**.

> El emulador y el PC comparten la red del ordenador, así que ambos ven la
> misma telemetría del broker.

---

## 6. Probar en un teléfono real

1. En el teléfono: **Ajustes → Ajustes del sistema → Ajustes de desarrollador**
   → activa **Depuración USB**.
2. Conecta el cable USB y acepta el diálogo *¿Permitir depuración?*.
3. Comprueba que el ordenador lo ve:
   ```powershell
   & "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" devices
   ```
4. Instala:
   ```powershell
   & "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" install bin\*.apk
   ```

Si instalas el `.apk` a mano (sin `adb`), el teléfono pedirá permitir
*"instalar apps de origen desconocido"* para la app que lo abrió (el
explorador de archivos o el correo).

**El teléfono necesita internet**: los datos llegan por MQTT al broker
público `broker.emqx.io`.

---

## 7. Cómo funciona por dentro

```
  ESP32 en Wokwi                Broker                App móvil (Kivy)
  ┌──────────────┐   publica   ┌───────────┐  suscribe ┌──────────────────┐
  │  DS18B20     │ ──────────► │ broker.   │ ◄──────── │ telemetry (datos)│
  │  + variación │  1 s        │ emqx.io  │           │ limits (limites) │
  │  + rampa     │             │ (público)│           └────────┬─────────┘
  └──────┬───────┘             └───────────┘                    │
         │ suscribe          ┌─────────────────┐                 │
         └──────────────────►│ Panel escritorio │                 │
           limits (limites)  │  (PyQt6)        │                 ▼
                             └─────────────────┘   CepEngine  →  carta, tabla,
                                    ▲                (el mismo)    indicadores
                                    └── publica limits ─────────────┘
```

- **Dos escritores de límites, no uno**: el panel de escritorio escribe en
  `.../limits` y el móvil **solo lee**. Si el móvil publicara, el escritorio
  y el OLED del ESP32 se quedarían con valores distintos.
- **Si no llega nunca un mensaje de `.../limits`** (porque nadie ha cambiado
  los límites), el móvil usa **8,0 / 2,0 / 5,0 °C**, que es exactamente el
  valor por defecto del firmware. Por eso siempre coinciden.
- **Historial local**: cada lectura recibida se guarda en un SQLite del
  dispositivo (`app_storage_path()/cep_movil.db` en Android). De ahí salen las
  vistas *Hoy / 7 días / 30 días*. El móvil guarda **su propio** historial:
  un teléfono que se enciende hoy no tiene datos de ayer.

---

## 8. Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `No module named 'kivy'` al compilar | falta la dependencia en el APK | `requirements = python3,kivy,paho-mqtt` en `buildozer.spec` |
| La app abre pero no entra nada | el broker no es accesible desde el móvil | prueba con datos del móvil; revisa la cobertura |
| Se queda en "Conectando" | el broker rechaza la conexión | `broker.emqx.io` puede estar limitado; prueba `test.mosquitto.org` |
| El emulador no arranca | falta la aceleración por hardware | en el administrador de tareas de la BIOS activa **Intel VT-x / AMD-V** |
| `aapt2` falla al compilar en local | la ruta tiene espacios o acentos | usa `compilar-apk.bat` (copia a `C:\build\cepmovil`) |
| `Kivy no tiene instalador` | Python 3.15 | usa `py -3.14`: Kivy solo tiene ruedas hasta 3.14 |
| La gráfica sale vacía | no ha llegado ninguna lectura | enciende la simulación de Wokwi |
| El APK no instala en el teléfono | firm's con una clave de depuración | `buildozer android debug` genera una clave de depuración; para producción hace falta una clave propia (`buildozer android release`) |

---

## 9. Limitaciones conocidas

- Los **límites no se pueden cambiar** desde el móvil (decisión de diseño).
- El **historial es por dispositivo**, no global.
- La app **no sigue funcionando en segundo plano** de forma indefinida:
  Android puede cerrarla si no está en primer plano.
- No hay **notificaciones push** ni **exportación a CSV** en la versión móvil.
- El MQTT va en **texto plano** por el broker público (sin TLS). Para producción
  haría falta `broker.emqx.io:8883` con `tls_set()`.

---

## 10. Estructura del código

```
main.py                     punto de entrada que exige buildozer
buildozer.spec              configuración del APK
compilar-apk.bat            compilación local con Docker
movil/
├── main.py                 aplicación Kivy (pantallas + barra inferior)
├── config.py               broker y tópicos (heredados de app/config.py)
├── theme.py                paleta clara de la imagen de referencia
├── controlador.py          estado global: MQTT, motor CEP e historial
├── mqtt_client.py          cliente MQTT de SOLO LECTURA
├── storage.py              historial local en SQLite (Hoy / 7d / 30d)
├── generar_icono.py        genera assets/app_movil.png
└── ui/
    ├── inicio.py           pantalla 1
    ├── grafica.py          pantalla 2
    ├── ajustes.py          pantalla 3
    ├── carta.py            carta de control dibujada en canvas
    └── widgets.py          tarjetas, iconos vectoriales, barra inferior
```
