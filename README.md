# Simulador IoT & Control Estadístico de Procesos (CEP)

ESP32 simulado en Wokwi + sensor Dallas DS18B20 → MQTT → panel de monitoreo en PyQt6.

El ESP32 publica la temperatura del sensor cada segundo y el panel calcula los
indicadores de control estadístico de procesos, dibuja la carta de control
individual (X) y avisa cuando el proceso sale de control.

> 📖 **[`GUIA_USUARIO.md`](GUIA_USUARIO.md)** — guía de acompañamiento: cómo
> explicar el proyecto sin ser programador, glosario de términos, mapa de
> rutas de cada componente visible en pantalla y comprobaciones previas a
> presentar.

> 📱 **[`movil/LEEME-ANDROID.md`](movil/LEEME-ANDROID.md)** — la misma
> aplicación en Android (Kivy): cómo compilar el APK, cómo probarlo en el
> emulador o en un teléfono y cómo se conecta con el broker.

---

## 0. Las dos aplicaciones

| | Panel de escritorio | App móvil Android |
|---|---|---|
| Tecnología | Python + **PyQt6** + matplotlib | Python + **Kivy** |
| Ejecutable | `SimuladorCEP.exe` (PyInstaller) | `.apk` (buildozer) |
| Motor CEP | `app/core/cep_engine.py` | **el mismo fichero** |
| Cambia los límites | ✅ (los publica al ESP32) | ❌ solo los muestra |
| Instalar | Windows | Android 7.0+ |

Ambas se suscriben al mismo tópico MQTT y muestran el mismo estado CEP. La
app móvil es un **segundo observador** del sistema, no una copia: por eso
los límites de control los cambia **solo** el panel de escritorio.

---

## 1. Arquitectura

```
  ┌──────────── Wokwi (VS Code) ────────────┐
  │  ESP32 DevKit C V4                       │
  │   ├── DS18B20  DQ=GPIO4 (+ pull-up 4.7k) │
  │   └── SSD1306   SDA=21, SCL=22 (0x3C)    │
  │                                           │
  │  publica cada 1 s ──► broker.emqx.io    │
  └──────────────────────┬───────────────────┘
                         │  MQTT
              ┌──────────┴───────────┐
              │  app/  (PyQt6)        │  límites ──► .../limits ──► ESP32
              │  carta de control (X) │
              │  tabla + export CSV   │
              └──────────────────────┘
```

**Tópicos** (prefijo `cep/sensor/diyin-cep-7k3q2026/`, broker `broker.emqx.io:1883`):

| Tópico      | Dirección     | Payload                                                          |
| ----------- | ------------- | ---------------------------------------------------------------- |
| `telemetry` | ESP32 → panel | `{"t":21.12,"raw":21.06,"seq":128,"dev":"28-01-02-03-04-05-06"}` |
| `limits`    | panel → ESP32 | `{"lsc":8.0,"lic":2.0,"obj":5.0}`                                |

`t` es la lectura con la variación controlada aplicada (la que va al CEP y al
OLED); `raw` es la lectura cruda del sensor.

---

## 2. Puesta en marcha (desarrollo)

```powershell
.\instalar.bat          # entorno virtual + dependencias + PlatformIO + compilación
py -m app.main         # panel de monitoreo
```

Instalación manual equivalente:

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install platformio
python -m platformio run
```

### Firmware

1. `py -m platformio run` (o el botón ✓ de PlatformIO).
2. Abrir en VS Code la **raíz** del proyecto (donde están `wokwi.toml`,
   `diagram.json` y `platformio.ini` a la vez).
3. Barra lateral **Wokwi** → **▶ Start Simulation**.
4. La consola serie debe mostrar `mqtt=OK` y líneas `T=… C (raw …)`.

> Log a archivo: `py -m serial.tools.miniterm rfc2217://localhost:4000 115200 > serial.log`

### Panel

```powershell
py -m app.main          # o:  .\run_panel.bat
```

Izquierda: `HARDWARE SIMULADO` (temperatura, LED de estado, límites,
intervalo de registro). Derecha: `SISTEMA DIGITAL DE MONITOREO (CEP)`
(banner, carta de control, barra de indicadores) con las pestañas
_Gráfico de control_ y _Muestras_.

**Fuente de datos** (desplegable _CONFIGURACIÓN_):

| Fuente                           | Deslizador    | De dónde sale la temperatura                       |
| -------------------------------- | ------------- | -------------------------------------------------- |
| **Wokwi (MQTT)** _(por defecto)_ | Deshabilitado | Del DS18B20 real, por MQTT                         |
| **Simulación local**             | Habilitado    | Del modelo térmico local (arrastrar el deslizador) |

### App móvil (Android)

```powershell
py -3.14 -m movil.main     # ventana con proporciones de móvil en el escritorio (Kivy)
```

Ojo: Kivy **no tiene ruedas para Python 3.15**; usa `py -3.14`.

Para generar el `.apk`:

```powershell
.\compilar-apk.bat          # local, con Docker
```

o desde **GitHub Actions → Compilar APK Android → Run workflow** (el APK
queda como artefacto descargable). El detalle completo está en
[`movil/LEEME-ANDROID.md`](movil/LEEME-ANDROID.md).

---

## 3. Estructura

```
app/
├── main.py            punto de entrada
├── config.py          broker, tópicos, ventana del gráfico
├── theme.py           hoja de estilos (QSS) e iconos vectoriales
├── core/
│   ├── cep_engine.py  motor CEP: clasificación, media, índice de defectos
│   ├── registro.py    archivo de lecturas para tabla y CSV (cada N segundos)
│   ├── sensor_model.py modelo térmico local (inercia, ruido, cuantización)
│   └── mqtt_link.py   cliente MQTT no bloqueante con reconexión
└── ui/
    ├── main_window.py coordina hardware ↔ motor ↔ MQTT
    ├── hardware_panel.py  HARDWARE SIMULADO
    ├── cep_panel.py       MONITOREO (CEP) + indicadores
    ├── chart.py           carta de control individual (matplotlib)
    ├── data_table.py      tabla de muestras
    └── widgets.py         Card, Led, Banner, iconos

src/main.cpp           firmware ESP32 (PlatformIO)
include/config.h       broker, tópicos, pines, constantes de simulación
tools/mqtt_probe.py    lector MQTT de consola

movil/                 app Android (Kivy) — comparte motor con el escritorio
├── main.py            aplicación Kivy (pantallas + barra inferior)
├── config.py          broker y tópicos heredados de app/config.py
├── theme.py           paleta clara de la imagen de referencia
├── controlador.py     estado global: MQTT ↔ motor CEP ↔ historial
├── mqtt_client.py     cliente MQTT de SOLO LECTURA (telemetry + limits)
├── storage.py         historial local en SQLite (Hoy / 7 días / 30 días)
└── ui/
    ├── inicio.py      pantalla 1: temperatura actual, rango, estado
    ├── grafica.py     pantalla 2: historial con selector de rango
    ├── ajustes.py     pantalla 3: fuente, intervalo y límites (solo lectura)
    ├── carta.py       carta de control dibujada en canvas (sin matplotlib)
    └── widgets.py     tarjetas, iconos vectoriales, barra inferior

main.py                punto de entrada que exige buildozer (Android)
buildozer.spec         configuración del APK
compilar-apk.bat       compilación local del APK con Docker
```

---

## 4. Reglas del motor CEP

Idénticas en el firmware (`src/main.cpp`) y en el panel (`app/core/cep_engine.py`):

- `CRÍTICO` → `T > LSC` o `T < LIC`
- `ACEPTABLE` → dentro de `[LIC, LSC]`, en el **40 % exterior** de la banda
- `ESTABLE` → resto de la banda _(con 8/2/5 °C: estable en `[4.4, 5.6]`)_

Los límites deben cumplir `LIC < OBJ < LSC` y estar dentro del rango del
sensor (−55 … 125 °C). Si el usuario escribe un valor incorrecto, la interfaz
lo marca en rojo, **no lo aplica** y conserva los últimos límites válidos.

| Indicador              | Definición                               |
| ---------------------- | ---------------------------------------- |
| Media Temporal (X̄)     | media de todas las muestras de la sesión |
| Puntos Fuera de Límite | nº de muestras fuera de `[LIC, LSC]`     |
| Índice de Defectos     | fuera de límite / total × 100            |

---

## 5. Constantes ajustables

| Constante     | Archivo            | Por defecto                     | Efecto                                           |
| ------------- | ------------------ | ------------------------------- | ------------------------------------------------ |
| `VAR_AMP`     | `include/config.h` | `0.15f`                         | Amplitud (± °C) de la variación de la lectura    |
| `MAX_SLOPE`   | `include/config.h` | `1.0f`                          | Tasa máxima de cambio del valor publicado (°C/s) |
| `BROKER`      | `include/config.h` | `broker.emqx.io`                | Broker MQTT (fallback: `test.mosquitto.org`)     |
| `TOPIC_BASE`  | `include/config.h` | `cep/sensor/diyin-cep-7k3q2026` | Prefijo de los tópicos                           |
| `LSC/LIC/OBJ` | `include/config.h` | `8.0 / 2.0 / 5.0`               | Límites iniciales                                |

---

## 6. Notas de implementación

- **La tabla y el CSV** archivan una lectura cada N segundos (1/5/10/30/60,
  por defecto 5) según la **hora** de la lectura; el gráfico, los indicadores y
  los estados usan **todas** las lecturas.
- **CSV** en UTF-8 con BOM y separador `;` (con coma decimal), que es lo que
  Excel en configuración regional española abre directamente.
- **PubSubClient ≥ 2.8**: hay que construirlo con un `WiFiClient` global
  (`PubSubClient mqtt(netClient)`). El constructor por defecto deja `_client`
  en `NULL` y `connect()` peta con _IllegalInstruction_.
- **PyQt6**: los métodos conectados a señales deben tener identificadores
  **ASCII**; con acentos, PyQt6 6.11 sobre Python 3.14 provoca un
  _access violation_ nativo.
- **Qt** no aplica las reglas `:disabled` a los sub-controles del slider: el
  estado deshabilitado se fuerza con un estilo inline (`theme.SLIDER_ACTIVO`).

---

## 7. Problemas frecuentes

| Síntoma                                | Causa                                         | Solución                                             |
| -------------------------------------- | --------------------------------------------- | ---------------------------------------------------- |
| Panel no recibe nada                   | la simulación no corre                        | ▶ Start Simulation en VS Code                        |
| `ERROR: sin WiFi`                      | falta el gateway IoT                          | reinicia la simulación                               |
| `FALLO … rc=-4`                        | broker inalcanzable                           | `BROKER` → `test.mosquitto.org` y recompila          |
| `no se pudo iniciar el SSD1306`        | cableado I2C                                  | `diagram.json`: SDA=21, SCL=22, VCC=3V3              |
| `el DS18B20 no responde`               | pull-up o DQ                                  | `esp:4` ↔ `temp1:DQ`, resistor 4.7 kΩ entre DQ y 3V3 |
| `Guru Meditation … IllegalInstruction` | `PubSubClient` con el constructor por defecto | ver la nota de implementación                        |

### Versiones de librerías fijadas (`platformio.ini`)

| Librería             | Versión |
| -------------------- | ------- |
| PubSubClient         | 2.8.0   |
| OneWire              | 2.3.8   |
| DallasTemperature    | 3.9.1   |
| Adafruit SSD1306     | 2.5.13  |
| Adafruit GFX Library | 1.11.9  |
| Adafruit BusIO       | 1.14.5  |

Core Arduino-ESP32 3.3.12 (`espressif32@8.0.0`), con la pila de la tarea
`loop` ampliada a 12 KB.
3