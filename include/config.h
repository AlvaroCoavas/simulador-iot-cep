#pragma once
// ============================================================================
// Simulador IoT & Control Estadistico de Procesos (CEP)
// Configuracion del firmware ESP32 simulado en Wokwi
// ============================================================================

// ------------------------------ Broker MQTT --------------------------------
#define BROKER    "broker.emqx.io"
// Fallback si broker.emqx.io no responde (descomentar la linea siguiente):
// #define BROKER  "test.mosquitto.org"
#define MQTT_PORT 1883

// --------------------------------- Topicos ---------------------------------
// Tópico unico del proyecto para no mezclarse con otros datos del broker.
#define TOPIC_BASE       "cep/sensor/diyin-cep-7k3q2026"
#define TOPIC_TELEMETRY  TOPIC_BASE "/telemetry"   // ESP32 -> Panel
#define TOPIC_LIMITS     TOPIC_BASE "/limits"      // Panel  -> ESP32

// ID fijo del cliente MQTT + ultimo byte de la MAC (sin random()).
#define MQTT_CLIENT_ID     "cep-esp32-diyin"
#define CLIENT_BUFFER_SIZE 256

// ------------------- WiFi virtual de Wokwi (AP abierto) ---------------------
#define WIFI_SSID      "Wokwi-GUEST"
#define WIFI_PASSWORD  ""
#define WIFI_CHANNEL   6

// -------------------------------- Hardware ---------------------------------
#define ONE_WIRE_PIN 4     // DQ del DS18B20
#define OLED_SDA_PIN 21
#define OLED_SCL_PIN 22
#define OLED_ADDR    0x3C
#define SCREEN_WIDTH  128
#define SCREEN_HEIGHT 64

// --------------------- Limites de control (CEP) -----------------------------
// Editables en caliente desde el panel via TOPIC_LIMITS.
#define LSC_DEFAULT 8.0f   // Limite Superior de Control
#define LIC_DEFAULT 2.0f   // Limite Inferior de Control
#define OBJ_DEFAULT 5.0f   // Valor objetivo

// ------------------------------ Publicacion --------------------------------
#define PUBLISH_INTERVAL_MS 1000
#define MQTT_RETRY_DELAY_MS  2000   // espera entre reintentos de MQTT

// ------------------- Variacion controlada de la lectura ---------------------
// Amplitud (C) de la variacion que se aplica a la lectura cruda del DS18B20
// antes de publicarla. El valor publicado ("t") es el varied; el crudo va en
// "raw". Generador congruencial lineal con semilla fija: reproducible en cada
// ejecucion y sin depender del RNG del sistema.
#define VAR_AMP  0.15f
#define VAR_SEED 0x2545F491u

// ------------------------- Limitador de tasa de cambio ----------------------
// Tasa maxima de cambio de la lectura publicada (C/s). El valor que se
// publica ("t") no sigue al instante al sensor: avanza hacia la lectura real
// como maximo a esta velocidad, de modo que un salto brusco del DS18B20 se ve
// como una rampa en la carta de control. "raw" sigue siendo la lectura cruda.
#define MAX_SLOPE 1.0f
