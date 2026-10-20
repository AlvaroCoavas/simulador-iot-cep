# Simulador IoT & Control Estadístico de Procesos (CEP)

ESP32 simulado en Wokwi + sensor Dallas DS18B20 → MQTT → panel de monitoreo (PyQt6).

---

## 1. Ejecutar el firmware en Wokwi

1. **Compilar** (desde la raíz del proyecto):
   ```powershell
   py -m platformio run
   ```
2. **Abrir en VS Code** la carpeta raíz del proyecto (la que contiene `wokwi.toml`,
   `diagram.json` y `platformio.ini` a la vez).
3. Bar lateral **Wokwi** → **▶ Start Simulation** (o `F1` → *Wokwi: Start Simulator*).
   No hace falta *Select Config File*: hay un único `wokwi.toml` en la raíz.
4. Mirar la **consola serie**: debe aparecer `mqtt=OK` y líneas `T=… C (raw …)`.

> Capturar el log: `py -m serial.tools.miniterm rfc2217://localhost:4000 115200 > serial.log`

## 2. Ejecutar el panel

```powershell
py -m app.main          # o:  .\run_panel.bat
```

Ventana con dos paneles: **izquierda** `HARDWARE SIMULADO` (valor grande, LED de estado,
límites editables, botón *Reiniciar Métricas CEP*) y **derecha** `SISTEMA DIGITAL DE
MONITOREO (CEP)` (banner, *Gráfico de Control Individual (X)* y barra de indicadores:
*Media Temporal (X̄)*, *Puntos Fuera de Límite*, *Índice de Defectos*).

## 3. Cambiar la fuente de datos

Desplegable **Fuente de datos** de la tarjeta *CONFIGURACIÓN*:

| Fuente | Slider | De dónde sale la temperatura |
|---|---|---|
| **Wokwi (MQTT)** *(por defecto)* | Deshabilitado → *«Ajuste en el popup del DS18B20 en Wokwi»* | Del DS18B20 real, por MQTT |
| **Simulación local** | Habilitado → *«Deslizador activo en simulación local»* | Del modelo térmico local (arrastrar el slider) |

## 4. Guion de demo (5 pasos)

Antes de empezar: **DS18B20 en 5 °C**, límites **LSC 8.0 / LIC 2.0 / OBJ 5.0 °C**
y pulsar **«Reiniciar Métricas CEP»**.

| # | Acción (en Wokwi) | Lo que debe verse en el panel |
|---|---|---|
| 1 | DS18B20 → **5 °C** | Banner verde *PROCESO BAJO CONTROL ESTADÍSTICO*, LED verde, `ESTABLE`, serie plana sobre el objetivo azul |
| 2 | DS18B20 → **7 °C** | Banner ámbar *PROCESO EN ZONA DE ACEPTACIÓN*, LED ámbar, `ACEPTABLE` (7 > 5.6) |
| 3 | DS18B20 → **9 °C** | Banner rojo *¡ALERTA! PROCESO FUERA DE CONTROL*, LED rojo, `CRÍTICO`, la serie se pone **roja** al cruzar el LSC y el *Índice de Defectos* sube |
| 4 | DS18B20 → **5 °C** | Vuelve a verde / `ESTABLE`; el gráfico conserva la excursion histórica |
| 5 | — | Revisar la barra inferior: *Media Temporal (X̄)*, *Puntos Fuera de Límite* e *Índice de Defectos* (%), que resumen todo el ensayo |

> La lectura fluctúa ±0.15 °C alrededor del valor real del sensor (variación controlada
> del firmware). El valor crudo se publica en `raw` dentro del payload MQTT.

## 5. Referencia rápida

**Tópicos** (`cep/sensor/diyin-cep-7k3q2026/`) · broker `broker.emqx.io:1883`

| Tópico | Dirección | Payload |
|---|---|---|
| `telemetry` | ESP32 → panel | `{"t":21.12,"raw":21.06,"seq":128,"dev":"28-01-02-03-04-05-06"}` |
| `limits` | panel → ESP32 | `{"lsc":8.0,"lic":2.0,"obj":5.0}` |

**Reglas del motor CEP** (idénticas en el firmware y en el panel):

- `CRÍTICO` → `T > LSC` o `T < LIC`
- `ACEPTABLE` → dentro de `[LIC, LSC]`, en el **40 % exterior** de la banda
- `ESTABLE` → resto de la banda *(con 8/2/5 °C: estable en `[4.4, 5.6]`)*

**Ajuste de la variación** → `VAR_AMP` en `include/config.h` (por defecto `0.15f`).

**Si algo falla**

| Síntoma | Causa | Solución |
|---|---|---|
| Panel no recibe nada | la simulación no corre | ▶ Start Simulation en VS Code |
| `ERROR: sin WiFi` | falta el gateway IoT | reinicia la simulación |
| `FALLO … rc=-4` | broker inalcanzable | cambia `BROKER` en `include/config.h` a `test.mosquitto.org` y recompila |
| `no se pudo iniciar el SSD1306` | cableado I2C | `diagram.json`: SDA=21, SCL=22, VCC=3V3 |
| `el DS18B20 no responde` | pull-up o DQ | `esp:4` ↔ `temp1:DQ`, resistor 4.7 kΩ entre DQ y 3V3 |
