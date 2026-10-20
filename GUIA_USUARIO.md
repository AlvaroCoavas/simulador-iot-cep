# Guía de usuario — Simulador IoT & Control Estadístico de Procesos (CEP)

Documento de acompañamiento para presentar y explicar el proyecto.
Está pensado para que **alguien que no sabe programar** pueda entenderlo y
explicarlo con soltura, y para que se pueda localizar en el código cualquier
pieza que se haya mostrado en pantalla.

---

## 1. Qué es esto, en una frase

> Es un **sensor de temperatura simulado** que manda sus lecturas por internet
> a una **pantalla de control** que dibuja la evolución de la temperatura y
> avisa cuando el proceso se sale de los límites permitidos.

---

## 2. Cómo contarlo (explicación en lenguaje llano)

Imagina una **cámara frigorífica** (o cualquier proceso con temperatura) que hay
que vigilar. Necesitas saber si se está mantendo dentro de la franja
temperatura buena, y si no, avisar.

El proyecto tiene **dos piezas** que hablan entre sí por internet:

**La primera: el sensor (a la izquierda de tu pantalla, dentro de Wokwi).**
Es una placa ESP32 —un minuscule ordenador del tamaño de una tarjeta— con un
sensor de temperatura **DS18B20** conectado. Wokwi es un simulador: te dibuja
la placa, el sensor y los cables en pantalla, y tú puedes "tocar" el sensor
para cambiar la temperatura que mide, como si le|subieras el termostato.
La placa va publicando la temperatura por internet una vez por segundo.

**La segunda: el panel de control (la aplicación del PC).** Es una ventana con
dos mitades. A la izquierda, el "estado del hardware": la temperatura que ha
llegado del sensor, un **LED** de colores y la etiqueta `ESTABLE`,
`ACEPTABLE` o `CRÍTICO`. A la derecha, el **gráfico de control**: la línea
roja discontinua de arriba es el **límite máximo** permitido, la de abajo el
**límite mínimo**, la azul el **valor objetivo**, y la línea verde es la
temperatura real. Abajo, tres números que resumen el ensayo.

**El mensaje clave para la explicación:**

> "El sensor está en un sitio y el panel está en otro, y se hablan por
> internet. El panel además le devuelve al sensor los límites que ha
> configurado el usuario, para que **las dos pantallas muestren exactamente
> el mismo estado**."

**El concepto de control estadístico en una frase:**

> "Una temperatura que siempre sube y baja un poco es normal. Lo peligroso es
> que se salga de la franja. Por eso no miramos cada lectura por separado:
> miramos la serie completa en la gráfica y, además, le ponemos una banda
> verde/ámbar/roja según lo cerca o lejos que esté de la zona buena."

**Los tres estados:**

| Estado | Cuándo | Color |
|---|---|---|
| `ESTABLE` | La temperatura está en la franja central de control | 🟢 verde |
| `ACEPTABLE` | Está dentro de los límites pero cerca del borde (el 40 % exterior de la franja) | 🟠 ámbar |
| `CRÍTICO` | Se ha salido de los límites | 🔴 rojo |

**El detalle que da puntos extra:** la temperatura publicada no da saltos
bruscos. El firmware le aplica una **variación controlada de ±0.15 °C** (como
el ruido real de un sensor) y además un **límite de cambio de 1 °C/s**, así
que si mueves el sensor de golpe, la curva dibuja una **rampa**, como ocurre
en un proceso térmico real. En el payload MQTT se publica el valor con
variación en `t` y el valor crudo en `raw`.

---

## 3. Glosario (para no perderte en una conversación)

| Término | Qué significa |
|---|---|
| **Wokwi** | Simulador de electrónica en el navegador/extensión de VS Code. Aquí se "enciende" la placa virtual. |
| **ESP32** | Microcontrolador (el cerebro de la placa). En este proyecto, simulado. |
| **DS18B20** | Sensor de temperatura digital de Dallas Instruments. Rango −55…125 °C, resolución 0.0625 °C. |
| **SSD1306 / OLED** | Pantallita de 128×64 píxeles del circuito, donde el firmware muestra la temperatura y el estado. |
| **1-Wire** | Protocolo con el que el ESP32 lee el DS18B20 (un solo cable de datos). |
| **I²C** | Protocolo con el que el ESP32 habla con la pantalla OLED. |
| **Firmware** | El programa que corre dentro del ESP32. Aquí: `src/main.cpp`. |
| **MQTT** | Protocolo sencillo para enviar mensajes por internet (mucho usados por sensores). |
| **Broker** | El "buzón" central donde se dejan los mensajes MQTT. Aquí: `broker.emqx.io`, público y gratuito. |
| **Tópico** | La "etiqueta" del buzón donde se publica. Ej.: `.../telemetry`. |
| **Payload** | El contenido del mensaje. Ej.: `{"t":21.12,"raw":21.06,...}`. |
| **Carta / gráfico de control (X)** | La gráfica con los límites y la serie de temperaturas. |
| **LSC / LIC** | Límite Superior e Inferior de Control (la franja permitida). |
| **OBJ** | Valor objetivo (donde queremos que esté la temperatura). |
| **X̄ (media)** | El promedio de todas las lecturas tomadas. |
| **Índice de defectos** | Porcentaje de lecturas que se salieron de los límites. |
| **Variación controlada** | El ±0.15 °C que el firmware añade a la lectura para simular el ruido del sensor. |
| **Limitador de tasa** | El tope de 1 °C/s con el que el valor publicado persigue la lectura real. |
| **v. Code / VS Code** | El editor de código donde se escribe y donde corre la simulación. |
| **PlatformIO** | La herramienta que compila el firmware del ESP32. |
| **\.exe** | El programa del panel ya empaquetado, para abrirlo con doble clic. |

---

## 4. Mapa de rutas: dónde está cada cosa que se ve en pantalla

### 4.1 En el **panel del PC** (aplicación)

| Lo que se ve | Archivo | Dónde mirar dentro |
|---|---|---|
| La ventana completa | `app/ui/main_window.py` | clase `MainWindow` (línea 24) |
| **Panel izquierdo** `HARDWARE SIMULADO` | `app/ui/hardware_panel.py` | clase `HardwarePanel` (línea 42) |
| Valor grande de temperatura (`5.1 °C`) | `app/ui/hardware_panel.py` | `set_lectura()` |
| **LED** de color con halo | `app/ui/widgets.py` | clase `Led` (línea 21) |
| `ESTABLE` / `ACEPTABLE` / `CRÍTICO` | `app/core/cep_engine.py` | enum `EstadoProceso` (línea 17) → se pinta en `hardware_panel.set_lectura()` |
| Tarjeta `Tarjeta ESP32 (Virtual)` y estado | `app/ui/hardware_panel.py` | `set_conexion()` |
| Deslizador de ambiente | `app/ui/hardware_panel.py` | `deslizador` → `set_fuente()` |
| Selector **Fuente de datos** | `app/ui/hardware_panel.py` | `combo_fuente` |
| Campos **LSC / LIC / OBJ** y validación | `app/ui/hardware_panel.py` | `_validar_limites()` y `_mostrar_error_limites()` |
| Selector **Intervalo de registro** | `app/ui/hardware_panel.py` | `combo_intervalo` |
| Botón **Reiniciar Métricas CEP** | `app/ui/hardware_panel.py` | `boton_reiniciar` → `main_window.reiniciar_metricas()` (línea 164) |
| **Panel derecho** `MONITOREO (CEP)` | `app/ui/cep_panel.py` | clase `CepPanel` (línea 55) |
| **Banner** (verde / ámbar / rojo) | `app/ui/cep_panel.py` | `set_banner()`; el marco en `app/ui/widgets.py` clase `Banner` |
| Pestañas *Gráfico de control* / *Muestras* | `app/ui/cep_panel.py` | `pestanas` (QTabWidget) |
| **Gráfico de control (X)** | `app/ui/chart.py` | clase `ChartControl` (línea 13), `actualizar()` (línea 53) |
| Líneas LSC / LIC / objetivo | `app/ui/chart.py` | dentro de `actualizar()` (`ax.axhline`) |
| Leyenda de la gráfica | `app/ui/chart.py` | dentro de `actualizar()` (`ax.legend`) |
| **Tabla de muestras** | `app/ui/data_table.py` | clase `TablaMuestras` (línea 21), `agregar()` (línea 49) |
| Botón **Exportar CSV** | `app/ui/cep_panel.py` | `boton_exportar` → `main_window.exportar_csv()` (línea 180) |
| **Barra de indicadores** (X̄, fuera de límite, índice de defectos) | `app/ui/cep_panel.py` | clase `Metrica` (línea 28) y `set_indicadores()` |
| Colores oscuros de toda la ventana | `app/theme.py` | paleta (líneas 6-18) y hoja de estilos `QSS` (línea 20) |
| Iconos (chip, termómetro, ondas, panel) | `app/ui/widgets.py` | `icon_pixmap()` (línea 81) |

### 4.2 En el **motor** (la lógica, sin interfaz)

| Qué hace | Archivo | Detalle |
|---|---|---|
| Decide si una temperatura es estable, aceptable o crítica | `app/core/cep_engine.py` | `clasificar()` (línea 98) |
| Calcula media, puntos fuera de límite e índice de defectos | `app/core/cep_engine.py` | propiedades `media_temporal`, `puntos_fuera_de_limite`, `indice_defectos` |
| Guarda cada lectura con su hora | `app/core/cep_engine.py` | `Muestra` (línea 34), `agregar()` (línea 80) |
| Decide qué lecturas van a la tabla y al CSV | `app/core/registro.py` | `RegistroMuestras.registrar()` (línea 23) |
| Temperatura simulada cuando no hay sensor real | `app/core/sensor_model.py` | `ModeloSensor.avanzar()` (línea 49) |
| Escucha y publica por MQTT | `app/core/mqtt_link.py` | `MqttLink` (línea 19) |
| Broker, tópicos y ventanas | `app/config.py` | líneas 6-20 |
| Arranque de la aplicación | `app/main.py` | `main()` (línea 17) |

### 4.3 En el **sensor simulado** (Wokwi)

| Lo que se ve | Archivo |
|---|---|
| La placa, el sensor, la pantalla y los cables | `diagram.json` |
| Qué archivo se simula y con qué configuración | `wokwi.toml` |
| El programa que corre en la placa | `src/main.cpp` |
| Broker, tópicos, pines y constantes de simulación | `include/config.h` |
| Cómo se compila y con qué librerías | `platformio.ini` |
| Cómo se lee la temperatura y se publica | `src/main.cpp` → `publishReading()` |
| Cómo se dibuja el OLED | `src/main.cpp` → `updateDisplay()` |
| Cómo se calcula el estado en la placa | `src/main.cpp` → `estadoDe()` |
| La variación ±0.15 °C | `src/main.cpp` → `variacionControlada()` |
| El límite de cambio de 1 °C/s | `src/main.cpp` → bloque "Limitador de tasa" |
| La recepción de los límites del panel | `src/main.cpp` → `onMqttMessage()` |

### 4.4 En la **entrega al cliente** (fuera del repositorio)

| Archivo | Qué es |
|---|---|
| `entrega/GUIA_CLIENTE.md` | La guía de instalación y el guion de demo que se le da al cliente |
| `SimuladorCEP-entrega.zip` | El paquete final: `.exe` + firmware ya compilado + diagrama + guía |
| `release/SimuladorCEP.exe` | El panel empaquetado (doble clic y funciona, sin Python) |
| `release/firmware.bin` | El firmware ya compilado (el cliente no necesita compilar) |
| `release/LEEME.txt` | La guía del cliente, dentro del ZIP |

### 4.5 Scripts de ayuda

| Archivo | Para qué |
|---|---|
| `instalar.bat` | Prepara el entorno de desarrollo (entorno virtual, librerías, PlatformIO, compila) |
| `empaquetar.bat` | Genera el ZIP de entrega para el cliente |
| `build.bat` | Solo compila el firmware |
| `run_panel.bat` | Arranca el panel |
| `run_probe.bat` | Lanza el lector MQTT de consola (`tools/mqtt_probe.py`), que imprime cada lectura que llega. Sirve para **enseñar el enlace sin interfaz** |

---

## 5. Los dos caminos para enseñarlo

**A) Con sensor real (Wokwi).** Es lo que impresiona:
1. VS Code → extensión Wokwi → **▶ Start Simulation**.
2. En el diagrama, clic sobre el **DS18B20** → mover su control *Temperature*.
3. `py -m app.main` (o doble clic en `SimuladorCEP.exe`).
4. El LED y el banner reaccionan al instante.

**B) Sin sensor (solo el PC).** Para explicar en un aula sin internet o sin
licencia de Wokwi: en *CONFIGURACIÓN* → *Fuente de datos* → **Simulación
local**, y arrastrar el deslizador. **La mitad del CEP (gráfica, banner, LED,
indicadores, tabla y CSV) funciona igual.**

**C) Solo el enlace, sin ventanas.** `py tools\mqtt_probe.py` imprime en la
consola cada mensaje que llega del sensor. Útil para explicar el MQTT.

---

## 6. Guion de demostración (5 pasos)

Antes: sensor en **5 °C**, límites **8.0 / 2.0 / 5.0 °C**, y pulsar
**«Reiniciar Métricas CEP»**.

| # | Acción | Lo que se ve |
|---|---|---|
| 1 | Sensor a **5 °C** | Banner verde, LED verde, `ESTABLE`, la curva plana sobre la línea azul |
| 2 | Sensor a **7 °C** | Banner ámbar, LED ámbar, `ACEPTABLE` (7 °C está en el 40 % exterior) |
| 3 | Sensor a **9 °C** | Banner rojo, LED rojo, `CRÍTICO`, **la curva se pone roja** al cruzar el límite de 8 °C |
| 4 | Sensor a **5 °C** | Vuelve a verde; la gráfica conserva la excursión anterior |
| 5 | Pestaña **Muestras** → **Exportar CSV** | La tabla con el historial y el CSV que se abre en Excel |

> Entre un movimiento y otro, **espera 4-5 segundos**: el firmware limita el
> cambio a 1 °C/s y la curva tarda un poco en llegar (es intencionado).

---

## 7. Preguntas que te pueden hacer (y qué responder)

**«¿Esto es un sensor real o simulado?»**
Es simulado. Wokwi simula la placa y el sensor en el navegador, pero el
programa que corre dentro (el firmware) es el mismo que correría en un ESP32
de verdad, con la misma biblioteca de lectura del sensor.

**«¿Por qué pasa por internet y no por un cable?»**
Porque el objetivo es monitorizar en remoto: el sensor puede estar en una
cámara frigorífica y el panel en el office. MQTT es el protocolo habitual para
eso porque es ligero y funciona incluso con redes muy lentas.

**«¿Y si dos personas lo ejecutan a la vez?»**
Como el broker y el tópico son públicos, ambas verían los datos de la otra.
Se resuelve dando a cada instalación un tópico propio (cambiando
`TOPIC_BASE` en `include/config.h` y en `app/config.py`).

**«¿El gráfico es el de un gráfico normal de Excel?»**
No: se dibuja con la librería matplotlib, y las franjas de color (estable /
aceptable / crítico) son la aportación del control estadístico de procesos.

**«¿Y la desviación de la curva?»**
Es intencionado. Un sensor real nunca da un valor constante: tiene ruido
(±0.15 °C) y el proceso tarda en responder (1 °C/s). Sin eso, la gráfica
parecería irreal y el control estadístico no tendría sentido.

**«¿Qué pasa si escribo mal un límite?»**
El panel lo rechaza: marca el campo en rojo, escribe el motivo debajo
("LIC debe ser menor que el objetivo") y **conserva los últimos límites
correctos**, así que ni la gráfica ni el sensor se descuadran.

**«¿Dónde se guardan los datos?»**
En la tabla de la pestaña *Muestras* (hasta 200 lecturas) y en el CSV que
exportes. El CSV sale en UTF-8 con BOM y separado por punto y coma, que es lo
que Excel en español abre directamente con los acentos correctos.

---

## 8. Si hay que cambiar algo: dónde tocar

| Quiero cambiar… | Tocar |
|---|---|
| El broker o el tópico MQTT | `include/config.h` (líneas 8-17) **y** `app/config.py` (líneas 6-12) |
| La amplitud de la variación (±0.15 °C) | `include/config.h` → `VAR_AMP` (línea 51) |
| La velocidad máxima de cambio (1 °C/s) | `include/config.h` → `MAX_SLOPE` (línea 59) |
| Los límites por defecto (8/2/5) | `include/config.h` → `LSC_DEFAULT`/`LIC_DEFAULT`/`OBJ_DEFAULT` |
| La regla de clasificación del CEP | `app/core/cep_engine.py` → `clasificar()` **y** `src/main.cpp` → `estadoDe()` (¡los dos, para que coincidan!) |
| Los textos de la interfaz | `app/ui/cep_panel.py` (banner) y `app/ui/hardware_panel.py` |
| Los colores | `app/theme.py` (paleta, líneas 6-18) |
| Cuántas lecturas guarda la tabla | `app/ui/data_table.py` → `MAX_FILAS` (línea 18) |
| Cada cuánto se registra en la tabla y el CSV | `app/ui/hardware_panel.py` → `INTERVALOS` (línea 38) |
| El cableado del circuito simulado | `diagram.json` |
| Qué se ve en la pantalla OLED | `src/main.cpp` → `updateDisplay()` |

> **Regla de oro:** el motor CEP está **duplicado a propósito** en el firmware
> (`src/main.cpp`) y en el panel (`app/core/cep_engine.py`). Si cambias una
> regla, cámbiala en los dos sitios o el OLED y el panel discreparán.

---

## 9. Comprobaciones antes de presentar

```powershell
py -m platformio run     # el firmware compila
py -m app.main           # el panel abre
py tools\mqtt_probe.py   # el enlace MQTT responde (con la simulación corriendo)
```

Si los tres funcionan, se puede presentar sin riesgo.
