// ============================================================================
// Simulador IoT & Control Estadistico de Procesos (CEP)
// ESP32 (Wokwi) + DS18B20 + SSD1306 -> MQTT -> Panel de monitoreo CEP
//
// Publica cada 1 s:  {"t":21.06,"seq":128,"dev":"28-01-02-03-04-05-06"}
// Suscribe TOPIC_LIMITS para recibir LSC / LIC / objetivo del panel.
//
// IMPORTANTE (fix del panic Guru Meditation / IllegalInstruction):
//   PubSubClient >= 2.8 tiene este constructor:
//       PubSubClient::PubSubClient() { this->_client = NULL; ... }
//   y connect() hace una llamada VIRTUAL a traves de ese puntero nulo,
//   lo que salta a la direccion 0xffffffff -> "IllegalInstruction".
//   Por eso se usa SIEMPRE el constructor con Client&:
//       PubSubClient mqtt(netClient);   con  WiFiClient netClient global.
// ============================================================================

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#include <math.h>
#include <string.h>

#include "config.h"

// ============================ Objetos globales ==============================
// El orden importa: netClient debe existir antes que mqtt.
WiFiClient netClient;           // <- Client real (obligatorio)
PubSubClient mqtt(netClient);   // <- constructor con Client&, nunca el de defecto

OneWire oneWire(ONE_WIRE_PIN);
DallasTemperature sensors(&oneWire);
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// ======================= Buffers globales (no en la pila) ===================
char payloadBuf[160];   // payload JSON de telemetria
char rxBuf[200];        // mensaje MQTT recibido
char dispBuf[40];       // texto del OLED
char keyBuf[24];        // patron de clave JSON
char devAddr[32] = "28-01-02-03-04-05-06";

// ============================== Estado global ===============================
String mqttClientId;
float  lsc = LSC_DEFAULT;
float  lic = LIC_DEFAULT;
float  obj = OBJ_DEFAULT;
uint32_t seq = 0;
uint32_t lastPublish = 0;
bool    wifiConnected = false;
uint8_t mqttAttempts = 0;

// Limitador de tasa: estado del valor publicado.
float    tPublicado = 0.0f;      // valor publicado (acotado por MAX_SLOPE)
bool     tPublicadoOk = false;   // ya se publico alguna lectura
uint32_t ultimoCiclo = 0;        // marca de tiempo del ciclo anterior

// =============================== Prototipos ================================
static void connectWifi();
static bool connectMqtt();
static void publishReading();
static void updateDisplay(float temp, const char *estado);
static void printDeviceAddress();
static const char *estadoDe(float temp);
static const char *mqttStateName(int state);
static void onMqttMessage(char *topic, byte *payload, unsigned int length);
static float jsonFloat(const char *json, const char *key, float &out);
static String buildClientId();
static float variacionControlada();

// ================================== SETUP ===================================
void setup() {
  Serial.begin(115200);
  delay(300);
  Serial.println();
  Serial.println(F("[CEP] =========================================="));
  Serial.println(F("[CEP] Simulador IoT - DS18B20 -> MQTT -> Panel CEP"));
  Serial.println(F("[CEP] =========================================="));

  // Inicializa el driver WiFi (necesario para leer la MAC).
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  mqttClientId = buildClientId();
  Serial.print(F("[CEP] Client ID MQTT: "));
  Serial.println(mqttClientId);

  // ---- OLED (I2C) ----
  Wire.begin(OLED_SDA_PIN, OLED_SCL_PIN);
  if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
    Serial.println(F("[CEP] ERROR: no se pudo iniciar el SSD1306"));
  } else {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.println(F("MONITOREO IoT CEP"));
    display.setCursor(0, 12);
    display.println(F("Iniciando..."));
    display.display();
    Serial.println(F("[CEP] OLED SSD1306 OK (I2C 0x3C, SDA=21, SCL=22)"));
  }

  // ---- Sensor 1-Wire ----
  sensors.begin();
  printDeviceAddress();

  // ---- MQTT: configuracion una sola vez ----
  mqtt.setServer(BROKER, MQTT_PORT);
  mqtt.setCallback(onMqttMessage);
  mqtt.setBufferSize(CLIENT_BUFFER_SIZE);   // antes de connect()
  mqtt.setKeepAlive(30);
  mqtt.setSocketTimeout(5);
  Serial.print(F("[CEP] MQTT buffer: "));
  Serial.print(mqtt.getBufferSize());
  Serial.println(F(" bytes"));

  connectWifi();
}

// =================================== LOOP ====================================
void loop() {
  if (!wifiConnected) {
    connectWifi();
    if (!wifiConnected) {
      delay(500);
      return;
    }
  }

  if (!mqtt.connected()) {
    connectMqtt();   // si falla, ya espera 2 s antes de reintentar
  }
  mqtt.loop();

  uint32_t now = millis();
  if (now - lastPublish >= PUBLISH_INTERVAL_MS) {
    lastPublish = now;
    publishReading();
  }
}

// ================================ WiFi ======================================
static void connectWifi() {
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    return;
  }

  Serial.print(F("[CEP] WiFi: conectando a "));
  Serial.print(WIFI_SSID);
  Serial.print(F(" ... "));
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD, WIFI_CHANNEL);

  uint32_t t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < 15000) {
    delay(250);
    Serial.print('.');
  }

  if (WiFi.status() != WL_CONNECTED) {
    // Reintento con escaneo de redes (sin canal fijo).
    Serial.println(F(" | reintento con escaneo..."));
    WiFi.disconnect();
    delay(500);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    t0 = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - t0 < 15000) {
      delay(250);
      Serial.print('.');
    }
  }

  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.print(F("[CEP] WiFi OK. IP="));
    Serial.print(WiFi.localIP());
    Serial.print(F(" RSSI="));
    Serial.println(WiFi.RSSI());
  } else {
    wifiConnected = false;
    Serial.println(F("[CEP] ERROR: sin WiFi. Revisa que la simulacion este corriendo "
                     "y que el gateway IoT de Wokwi este activo."));
  }
}

// ================================ MQTT ======================================
static bool connectMqtt() {
  Serial.print(F("[CEP] MQTT: conectando a "));
  Serial.print(BROKER);
  Serial.print(':');
  Serial.print(MQTT_PORT);
  Serial.print(F(" ... "));

  bool ok = mqtt.connect(mqttClientId.c_str());

  if (ok) {
    Serial.println(F("OK"));
    mqtt.subscribe(TOPIC_LIMITS);
    Serial.print(F("[CEP] MQTT: suscrito a "));
    Serial.println(TOPIC_LIMITS);
    mqttAttempts = 0;
  } else {
    mqttAttempts++;
    Serial.print(F("FALLO (intento "));
    Serial.print(mqttAttempts);
    Serial.print(F(") rc="));
    Serial.print(mqtt.state());
    Serial.print(F(" -> "));
    Serial.println(mqttStateName(mqtt.state()));

    // Cierra el socket para que el siguiente intento parta limpio.
    netClient.stop();
    // Espera antes de reintentar. NO reinicia el ESP32.
    delay(MQTT_RETRY_DELAY_MS);
  }
  return ok;
}

// ========================= Publicacion de la lectura ========================
static void publishReading() {
  sensors.requestTemperatures();
  float raw = sensors.getTempCByIndex(0);

  if (raw == DEVICE_DISCONNECTED_C) {
    Serial.println(F("[CEP] ERROR: el DS18B20 no responde (DQ=GPIO4, pull-up 4.7k)"));
    return;
  }

  // Objetivo: lectura real + variacion controlada.
  float tObjetivo = raw + variacionControlada();

  // Limitador de tasa (slew rate): el valor publicado avanza hacia el objetivo
  // como maximo MAX_SLOPE C/s, para que un salto brusco del sensor se vea como
  // una rampa y no como un escalon en la carta de control.
  uint32_t ahora = millis();
  if (!tPublicadoOk) {
    tPublicado = tObjetivo;          // primera lectura: sin rampa
    tPublicadoOk = true;
  } else {
    float dt = (ahora - ultimoCiclo) / 1000.0f;
    if (dt < 0.0f) dt = 0.0f;
    if (dt > 5.0f) dt = 5.0f;         // evita saltos tras un bloqueo largo
    float maxDelta = MAX_SLOPE * dt;
    float delta = tObjetivo - tPublicado;
    if (delta >  maxDelta) delta =  maxDelta;
    if (delta < -maxDelta) delta = -maxDelta;
    tPublicado += delta;
  }
  ultimoCiclo = ahora;

  float t = tPublicado;

  seq++;

  snprintf(payloadBuf, sizeof(payloadBuf),
           "{\"t\":%.2f,\"raw\":%.2f,\"seq\":%lu,\"dev\":\"%s\"}",
           t, raw, (unsigned long)seq, devAddr);

  if (mqtt.connected()) {
    if (!mqtt.publish(TOPIC_TELEMETRY, payloadBuf)) {
      Serial.println(F("[CEP] ERROR: no se pudo publicar en MQTT"));
    }
  }

  const char *estado = estadoDe(t);
  Serial.print(F("[CEP] T="));
  Serial.print(t, 2);
  Serial.print(F(" C (raw "));
  Serial.print(raw, 2);
  Serial.print(F(")  seq="));
  Serial.print((unsigned long)seq);
  Serial.print(F("  estado="));
  Serial.print(estado);
  Serial.print(F("  mqtt="));
  Serial.println(mqtt.connected() ? F("OK") : F("OFF"));

  updateDisplay(t, estado);
}

// ================= Variacion controlada de la lectura =======================
// Generador congruencial lineal (LCG) con semilla fija: secuencia reproducible
// en cada ejecucion, sin usar random() ni el RNG del sistema.
//   estado = (estado * 1103515245 + 12345) mod 2^32
// Los 15 bits altos dan un entero uniforme en [0, 32767], que se mapea a
// [-VAR_AMP, +VAR_AMP].
static uint32_t varEstado = VAR_SEED;

static float variacionControlada() {
  varEstado = varEstado * 1103515245u + 12345u;
  uint32_t u = (varEstado >> 16) & 0x7FFFu;
  return (2.0f * (float)u / 32767.0f - 1.0f) * VAR_AMP;
}

// ================================= OLED ======================================
static void updateDisplay(float temp, const char *estado) {
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);

  display.setTextSize(1);
  display.setCursor(0, 0);
  display.print(F("MONITOREO IoT CEP"));
  display.drawLine(0, 9, SCREEN_WIDTH - 1, 9, SSD1306_WHITE);

  display.setTextSize(2);
  display.setCursor(0, 16);
  snprintf(dispBuf, sizeof(dispBuf), "%.1f C", temp);
  display.print(dispBuf);

  display.setTextSize(1);
  display.setCursor(0, 40);
  display.print(F("ESTADO: "));
  display.print(estado);

  display.setCursor(0, 52);
  snprintf(dispBuf, sizeof(dispBuf), "SEQ:%lu MQTT:%s", (unsigned long)seq,
           mqtt.connected() ? "OK" : "ERR");
  display.print(dispBuf);

  display.display();
}

// ======================== Estado del proceso (CEP) ==========================
// Misma regla que el panel PyQt6 (app/core/cep_engine.py):
//   CRITICO   : fuera de [LIC, LSC]
//   ACEPTABLE : dentro de la banda, en el 40 % exterior
//   ESTABLE   : resto de la banda
static const char *estadoDe(float temp) {
  if (temp > lsc || temp < lic) return "CRITICO";
  float ancho = lsc - lic;
  float exterior = 0.40f * ancho;
  if (temp < lic + exterior || temp > lsc - exterior) return "ACEPTABLE";
  return "ESTABLE";
}

// ============================ Direccion 1-Wire ==============================
// DallasTemperature 3.9.x: getAddress(uint8_t* rom, uint8_t indice)
// rom[0] = codigo de familia (0x28), rom[1..6] = serial, rom[7] = CRC.
static void printDeviceAddress() {
  uint8_t rom[8] = {0};
  if (!sensors.getAddress(rom, 0)) {
    Serial.println(F("[CEP] DS18B20: no se encontro ningun sensor en el bus"));
    return;
  }
  snprintf(devAddr, sizeof(devAddr), "%02X-%02X-%02X-%02X-%02X-%02X-%02X",
           rom[0], rom[1], rom[2], rom[3], rom[4], rom[5], rom[6]);
  Serial.print(F("[CEP] DS18B20 encontrado. Direccion 1-Wire: "));
  Serial.println(devAddr);
}

// ====================== Client ID fijo + ultimo byte de MAC ================
static String buildClientId() {
  String id = String(MQTT_CLIENT_ID);
  String mac = WiFi.macAddress();               // "AA:BB:CC:DD:EE:FF"
  if (mac.length() >= 2) {
    id += '-';
    id += mac.substring(mac.length() - 2);       // ultimo byte de la MAC
  }
  return id;
}

// ====================== Nombre de los codigos de error MQTT =================
static const char *mqttStateName(int state) {
  switch (state) {
    case -1: return "conexion rechazada";
    case -2: return "no se pudo abrir el socket";
    case -3: return "fallo al publicar";
    case -4: return "tiempo agotado (timeout)";
    case -5: return "5 bytes de buffer libres";
    case -6: return "payload demasiado largo";
    default: return "error desconocido";
  }
}

// ==================== Recepcion de limites desde el panel ===================
static void onMqttMessage(char *topic, byte *payload, unsigned int length) {
  if (length >= sizeof(rxBuf)) length = sizeof(rxBuf) - 1;
  memcpy(rxBuf, payload, length);
  rxBuf[length] = '\0';

  Serial.print(F("[CEP] RX "));
  Serial.print(topic);
  Serial.print(F(" -> "));
  Serial.println(rxBuf);

  float v;
  if (jsonFloat(rxBuf, "lsc", v)) lsc = v;
  if (jsonFloat(rxBuf, "lic", v)) lic = v;
  if (jsonFloat(rxBuf, "obj", v)) obj = v;

  Serial.print(F("[CEP] Limites CEP -> LSC="));
  Serial.print(lsc, 1);
  Serial.print(F(" LIC="));
  Serial.print(lic, 1);
  Serial.print(F(" OBJ="));
  Serial.println(obj, 1);
}

// Lector minimal de float dentro de un JSON plano: {"lsc":8.0,...}
static float jsonFloat(const char *json, const char *key, float &out) {
  snprintf(keyBuf, sizeof(keyBuf), "\"%s\":", key);
  const char *p = strstr(json, keyBuf);
  if (!p) return 0;
  out = strtof(p + strlen(keyBuf), nullptr);
  return 1;
}
