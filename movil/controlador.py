"""Controlador de la app movil.

Concentra el estado (temperatura, estado CEP, limites, conexion e historial)
y es el unico que habla con MQTT y con la base de datos local.

REUTILIZA el motor del panel de escritorio:
  * `app.core.cep_engine.CepEngine`  -> clasificacion e indicadores
  * `app.core.sensor_model.ModeloSensor` -> simulacion local
  * `app.config` -> broker y topicos

La app movil NUNCA publica en el topico de limites: los cambia unicamente el
panel de escritorio; aqui solo se leen y se muestran.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty

from app.core.cep_engine import CepEngine, EstadoProceso
from app.core.sensor_model import ModeloSensor

from . import config, theme as TEMA
from .mqtt_client import ClienteMqtt
from .storage import Almacen

#: Etiquetas y colores de cada estado CEP en la version movil.
ESTADOS = {
    EstadoProceso.ESTABLE: ("En rango", TEMA.VERDE, TEMA.VERDE_CLARO),
    EstadoProceso.ACEPTABLE: ("Cerca del limite", TEMA.AMBAR, TEMA.AMBAR_CLARO),
    EstadoProceso.CRITICO: ("Fuera de rango", TEMA.ROJO, TEMA.ROJO_CLARO),
}


class Controlador(EventDispatcher):
    """Estado global de la app."""

    # ------------------------------ Propiedades ----------------------------
    temperatura = NumericProperty(0.0)
    estado_cep = StringProperty(EstadoProceso.ESTABLE.value)
    estado_etiqueta = StringProperty("En rango")
    estado_color = StringProperty(TEMA.VERDE)
    estado_fondo = StringProperty(TEMA.VERDE_CLARO)

    lsc = NumericProperty(8.0)
    lic = NumericProperty(2.0)
    objetivo = NumericProperty(5.0)

    conexion = StringProperty("conectando")
    conexion_texto = StringProperty("Conectando")
    conexion_color = StringProperty(TEMA.AMBAR)
    conexion_fondo = StringProperty(TEMA.AMBAR_CLARO)

    hay_datos = BooleanProperty(False)
    rango_texto = StringProperty("-2°C / 8°C")

    serie_hoy = ListProperty([])
    serie_7d = ListProperty([])
    serie_30d = ListProperty([])

    fuente = StringProperty(config.FUENTE_MQTT)
    intervalo = NumericProperty(config.INTERVALO_POR_DEFECTO)

    total_lecturas = NumericProperty(0)

    def __init__(self):
        super().__init__()
        # Motor CEP del escritorio (misma logica, misma clase).
        self.motor = CepEngine(lsc=8.0, lic=2.0, objetivo=5.0)
        self.almacen = Almacen(intervalo_s=config.INTERVALO_POR_DEFECTO)
        self.sensor = ModeloSensor(valor_inicial=5.0, ambiente=5.0)
        self._ultimo_dato = 0.0
        self._mqtt = ClienteMqtt(
            al_datos=self._al_datos,
            al_limites=self._al_limites,
            al_estado=self._al_estado,
        )
        self.bind(
            lsc=self._al_cambiar_limites,
            lic=self._al_cambiar_limites,
            objetivo=self._al_cambiar_limites,
        )

    # ------------------------------ Ciclo de vida --------------------------
    def iniciar(self) -> None:
        """Abre la base local, conecta MQTT y arranca el reloj."""
        self.almacen.abrir()
        self.almacen.set_intervalo(int(self.intervalo))
        self._mqtt.conectar()
        self._cargar_historial()
        # Reloj de 1 s: modo local, deteccion de "sin datos" y refresco.
        Clock.schedule_interval(self._tic, 1.0)

    def detener(self) -> None:
        self._mqtt.desconectar()
        self.almacen.cerrar()

    # ------------------------------- MQTT ----------------------------------
    def _al_datos(self, datos: dict) -> None:
        """Llega una lectura del ESP32 por MQTT."""
        try:
            temperatura = float(datos["t"])
        except (KeyError, TypeError, ValueError):
            return
        self._ultimo_dato = Clock.get_time()
        self.registrar(temperatura)

    def _al_limites(self, datos: dict) -> None:
        """Llegan los limites que publica el panel de escritorio (solo lectura)."""
        try:
            lsc = float(datos["lsc"])
            lic = float(datos["lic"])
            objetivo = float(datos["obj"])
        except (KeyError, TypeError, ValueError):
            return
        if not (lic < objetivo < lsc):
            return
        self.lsc = lsc
        self.lic = lic
        self.objetivo = objetivo
        self.motor.set_limites(lsc, lic, objetivo)

    def _al_estado(self, estado: str, detalle: str) -> None:
        """Cambia el estado de la conexion MQTT."""
        if estado == "conectado":
            texto, color, fondo = "Conectado", TEMA.VERDE, TEMA.VERDE_CLARO
        elif estado == "conectando":
            texto, color, fondo = "Conectando", TEMA.AMBAR, TEMA.AMBAR_CLARO
        elif estado == "error":
            texto, color, fondo = "Error", TEMA.ROJO, TEMA.ROJO_CLARO
        else:
            texto, color, fondo = "Sin conexion", TEMA.ROJO, TEMA.ROJO_CLARO
        # OJO: el color se actualiza ANTES que el texto, porque la interfaz
        # se refresca en cuanto cambia `conexion_texto`.
        self.conexion_color = color
        self.conexion_fondo = fondo
        self.conexion = estado
        self.conexion_texto = texto

    # ------------------------------ Procesamiento --------------------------
    def registrar(self, temperatura: float) -> None:
        """Clasifica la lectura (motor del escritorio) y actualiza la interfaz."""
        muestra = self.motor.agregar(temperatura)
        self.temperatura = muestra.temperatura
        self.estado_cep = muestra.estado.value
        etiqueta, color, fondo = ESTADOS[muestra.estado]
        self.estado_etiqueta = etiqueta
        self.estado_color = color
        self.estado_fondo = fondo
        self.hay_datos = True
        self.rango_texto = f"{self.lic:g}°C / {self.lsc:g}°C"

        self.almacen.guardar(muestra.temperatura, muestra.estado.value)
        self.total_lecturas = self.almacen.total()
        self._actualizar_series()

    def _tic(self, dt: float) -> None:
        """Reloj de un segundo."""
        if self.fuente == config.FUENTE_LOCAL:
            self.registrar(self.sensor.avanzar(1.0))
            if self.conexion != "conectado":
                self._al_estado("conectado", "Simulacion local")
        elif self._ultimo_dato and Clock.get_time() - self._ultimo_dato > config.TIMEOUT_SIN_DATOS:
            # El simulador esta apagado: se avisa, pero la app sigue viva.
            if self.conexion == "conectado":
                self._al_estado("desconectado", "Sin senal del sensor")

    # ------------------------------- Ajustes --------------------------------
    def cambiar_fuente(self, fuente: str) -> None:
        self.fuente = fuente
        if fuente == config.FUENTE_LOCAL:
            self.sensor.reiniciar(self.temperatura or 5.0)
            self._al_estado("conectado", "Simulacion local")
        else:
            self._mqtt.conectar()

    def set_intervalo(self, segundos: int) -> None:
        self.intervalo = int(segundos)
        self.almacen.set_intervalo(int(segundos))

    def _al_cambiar_limites(self, *_args) -> None:
        self.rango_texto = f"{self.lic:g}°C / {self.lsc:g}°C"
        self.motor.set_limites(self.lsc, self.lic, self.objetivo)

    # ------------------------------- Historial ------------------------------
    def _cargar_historial(self) -> None:
        self._actualizar_series()

    def _actualizar_series(self) -> None:
        """Recarga las tres series (hoy / 7 dias / 30 dias) del almacen local."""
        self.serie_hoy = self.almacen.serie_hoy()
        self.serie_7d = self.almacen.serie_dias(7)
        self.serie_30d = self.almacen.serie_dias(30)

    def limpiar_historial(self) -> None:
        """Borra el historial local y los indicadores del motor."""
        self.almacen.limpiar()
        self.motor.reiniciar()
        self.total_lecturas = 0
        self._actualizar_series()

    # ------------------------------- Utilidades -----------------------------
    def indicador_actual(self) -> tuple[float, int, float]:
        """(media temporal, puntos fuera de limite, indice de defectos)."""
        return (
            self.motor.media_temporal,
            self.motor.puntos_fuera_de_limite,
            self.motor.indice_defectos,
        )

    @staticmethod
    def ticks_hoy() -> list[tuple[float, str]]:
        """Marcas del eje horizontal para la vista de hoy."""
        return [(float(h), f"{h:02d}:00") for h in range(0, 25, 4)]

    @staticmethod
    def ticks_dias(dias: int) -> list[tuple[float, str]]:
        """Marcas del eje horizontal para las vistas de 7 y 30 dias."""
        hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        paso = 1 if dias <= 7 else 5
        marcas = []
        for d in range(0, dias + 1, paso):
            fecha = hoy - timedelta(days=dias - d)
            marcas.append((float(d), fecha.strftime("%d/%m")))
        return marcas
