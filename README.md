# Simulador IoT & Control Estadístico de Procesos (CEP)

ESP32 simulado en Wokwi + sensor Dallas DS18B20 → MQTT → panel de monitoreo en PyQt6.

El ESP32 publica la temperatura del sensor cada segundo y el panel calcula los
indicadores de control estadístico de procesos, dibuja la carta de control
individual (X) y avisa cuando el proceso sale de control.

> 📖 **[`GUIA_USUARIO.md`](GUIA_USUARIO.md)** — guía de acompañamiento: cómo
> explicar el proyecto sin ser programador, glosario de términos, mapa de
> rutas de cada componente visible en pantalla y comprobaciones previas a
> presentar.

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

| Tópico | Dirección | Payload |
|---|---|---|
| `telemetry` | ESP32 → panel | `{"t":21.12,"raw":21.06,"seq":128,"dev":"28-01-02-03-04-05-06"}` |
| `limits` | panel → ESP32 | `{"lsc":8.0,"lic":2.0,"obj":5.0}` |

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
*Gráfico de control* y *Muestras*.

**Fuente de datos** (desplegable *CONFIGURACIÓN*):

| Fuente | Deslizador | De dónde sale la temperatura |
|---|---|---|
| **Wokwi (MQTT)** *(por defecto)* | Deshabilitado | Del DS18B20 real, por MQTT |
| **Simulación local** | Habilitado | Del modelo térmico local (arrastrar el deslizador) |

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
```

---

## 4. Reglas del motor CEP

Idénticas en el firmware (`src/main.cpp`) y en el panel (`app/core/cep_engine.py`):

- `CRÍTICO` → `T > LSC` o `T < LIC`
- `ACEPTABLE` → dentro de `[LIC, LSC]`, en el **40 % exterior** de la banda
- `ESTABLE` → resto de la banda *(con 8/2/5 °C: estable en `[4.4, 5.6]`)*

Los límites deben cumplir `LIC < OBJ < LSC` y estar dentro del rango del
sensor (−55 … 125 °C). Si el usuario escribe un valor incorrecto, la interfaz
lo marca en rojo, **no lo aplica** y conserva los últimos límites válidos.

| Indicador | Definición |
|---|---|
| Media Temporal (X̄) | media de todas las muestras de la sesión |
| Puntos Fuera de Límite | nº de muestras fuera de `[LIC, LSC]` |
| Índice de Defectos | fuera de límite / total × 100 |

---

## 5. Constantes ajustables

| Constante | Archivo | Por defecto | Efecto |
|---|---|---|---|
| `VAR_AMP` | `include/config.h` | `0.15f` | Amplitud (± °C) de la variación de la lectura |
| `MAX_SLOPE` | `include/config.h` | `1.0f` | Tasa máxima de cambio del valor publicado (°C/s) |
| `BROKER` | `include/config.h` | `broker.emqx.io` | Broker MQTT (fallback: `test.mosquitto.org`) |
| `TOPIC_BASE` | `include/config.h` | `cep/sensor/diyin-cep-7k3q2026` | Prefijo de los tópicos |
| `LSC/LIC/OBJ` | `include/config.h` | `8.0 / 2.0 / 5.0` | Límites iniciales |

---

## 6. Notas de implementación

- **La tabla y el CSV** archivan una lectura cada N segundos (1/5/10/30/60,
  por defecto 5) según la **hora** de la lectura; el gráfico, los indicadores y
  los estados usan **todas** las lecturas.
- **CSV** en UTF-8 con BOM y separador `;` (con coma decimal), que es lo que
  Excel en configuración regional española abre directamente.
- **PubSubClient ≥ 2.8**: hay que construirlo con un `WiFiClient` global
  (`PubSubClient mqtt(netClient)`). El constructor por defecto deja `_client`
  en `NULL` y `connect()` peta con *IllegalInstruction*.
- **PyQt6**: los métodos conectados a señales deben tener identificadores
  **ASCII**; con acentos, PyQt6 6.11 sobre Python 3.14 provoca un
  *access violation* nativo.
- **Qt** no aplica las reglas `:disabled` a los sub-controles del slider: el
  estado deshabilitado se fuerza con un estilo inline (`theme.SLIDER_ACTIVO`).

---

## 7. Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| Panel no recibe nada | la simulación no corre | ▶ Start Simulation en VS Code |
| `ERROR: sin WiFi` | falta el gateway IoT | reinicia la simulación |
| `FALLO … rc=-4` | broker inalcanzable | `BROKER` → `test.mosquitto.org` y recompila |
| `no se pudo iniciar el SSD1306` | cableado I2C | `diagram.json`: SDA=21, SCL=22, VCC=3V3 |
| `el DS18B20 no responde` | pull-up o DQ | `esp:4` ↔ `temp1:DQ`, resistor 4.7 kΩ entre DQ y 3V3 |
| `Guru Meditation … IllegalInstruction` | `PubSubClient` con el constructor por defecto | ver la nota de implementación |

### Versiones de librerías fijadas (`platformio.ini`)

| Librería | Versión |
|---|---|
| PubSubClient | 2.8.0 |
| OneWire | 2.3.8 |
| DallasTemperature | 3.9.1 |
| Adafruit SSD1306 | 2.5.13 |
| Adafruit GFX Library | 1.11.9 |
| Adafruit BusIO | 1.14.5 |

Core Arduino-ESP32 3.3.12 (`espressif32@8.0.0`), con la pila de la tarea
`loop` ampliada a 12 KB.
