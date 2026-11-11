"""Pantalla 3: Ajustes.

Fuente de datos, intervalo de muestreo del historial y los limites de control
(solo lectura: los cambia el panel de escritorio, no esta app).
"""

from __future__ import annotations

from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView

from .. import config
from .. import theme as TEMA
from .widgets import Etiqueta, FilaRadio, SelectorSegmentado, Tarjeta, rgba

INTERVALOS_TEXTO = ("1 s", "5 s", "10 s", "30 s", "60 s")


class PantallaAjustes(BoxLayout):
    """Ajustes del movil."""

    def __init__(self, controlador, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.controlador = controlador

        self.add_widget(self._cabecera())

        desplazamiento = ScrollView(do_scroll_x=False, bar_width=dp(2))
        contenido = BoxLayout(
            orientation="vertical",
            spacing=dp(TEMA.ESPACIO),
            padding=(dp(TEMA.ESPACIO), dp(TEMA.ESPACIO), dp(TEMA.ESPACIO), dp(TEMA.ESPACIO)),
        )
        contenido.size_hint_y = None
        contenido.bind(minimum_height=contenido.setter("height"))
        contenido.add_widget(self._tarjeta_fuente())
        contenido.add_widget(self._tarjeta_intervalo())
        contenido.add_widget(self._tarjeta_limites())
        contenido.add_widget(self._tarjeta_indicadores())
        desplazamiento.add_widget(contenido)
        self.add_widget(desplazamiento)

        controlador.bind(
            lsc=self._refrescar,
            lic=self._refrescar,
            objetivo=self._refrescar,
            intervalo=self._refrescar,
            total_lecturas=self._refrescar,
        )
        Clock.schedule_once(lambda _dt: self._refrescar(), 0)

    # ------------------------------- Cabecera -------------------------------
    def _cabecera(self) -> BoxLayout:
        cabecera = BoxLayout(
            size_hint_y=None,
            height=dp(52),
            padding=(dp(TEMA.ESPACIO), dp(6), dp(TEMA.ESPACIO), dp(6)),
        )
        cabecera.add_widget(Etiqueta(text="Ajustes", font_size=sp(21), bold=True, color=rgba(TEMA.TEXTO), halign="left", valign="middle"))
        return cabecera

    # --------------------------- Tarjeta fuente -----------------------------
    def _tarjeta_fuente(self) -> Tarjeta:
        tarjeta = Tarjeta(size_hint_y=None, height=dp(146), padding=(dp(16), dp(14), dp(16), dp(10)), spacing=dp(4))
        tarjeta.add_widget(self._titulo("Fuente de datos"))

        self.fila_mqtt = FilaRadio(
            titulo="Wokwi (MQTT)",
            subtitulo="Recibe la temperatura del ESP32 simulado",
            seleccionado=self.controlador.fuente == config.FUENTE_MQTT,
            al_seleccionar=lambda: self._elegir_fuente(config.FUENTE_MQTT),
            size_hint_y=None,
            height=dp(44),
        )
        self.fila_local = FilaRadio(
            titulo="Simulación local",
            subtitulo="Modelo térmico en el propio móvil",
            seleccionado=self.controlador.fuente == config.FUENTE_LOCAL,
            al_seleccionar=lambda: self._elegir_fuente(config.FUENTE_LOCAL),
            size_hint_y=None,
            height=dp(44),
        )
        tarjeta.add_widget(self.fila_mqtt)
        tarjeta.add_widget(self.fila_local)
        return tarjeta

    def _elegir_fuente(self, fuente: str) -> None:
        self.controlador.cambiar_fuente(fuente)
        self.fila_mqtt.set_seleccionado(fuente == config.FUENTE_MQTT)
        self.fila_local.set_seleccionado(fuente == config.FUENTE_LOCAL)

    # ------------------------- Tarjeta intervalo ----------------------------
    def _tarjeta_intervalo(self) -> Tarjeta:
        tarjeta = Tarjeta(size_hint_y=None, height=dp(126), padding=(dp(16), dp(14), dp(16), dp(12)), spacing=dp(6))
        tarjeta.add_widget(self._titulo("Intervalo de muestreo del historial"))
        self.selector_intervalo = SelectorSegmentado(
            opciones=list(INTERVALOS_TEXTO),
            seleccionado=INTERVALOS_TEXTO[config.INTERVALOS.index(self.controlador.intervalo)],
            al_cambiar=self._cambiar_intervalo,
            size_hint_y=None,
            height=dp(34),
        )
        tarjeta.add_widget(self.selector_intervalo)
        tarjeta.add_widget(
            Etiqueta(
                text="Cada cuánto se guarda una lectura en el historial del móvil.",
                font_size=sp(11),
                color=rgba(TEMA.TEXTO_SUAVE),
                halign="left",
                valign="top",
            )
        )
        return tarjeta

    def _cambiar_intervalo(self, texto: str) -> None:
        try:
            indice = INTERVALOS_TEXTO.index(texto)
        except ValueError:
            return
        self.controlador.set_intervalo(config.INTERVALOS[indice])

    # -------------------------- Tarjeta limites -----------------------------
    def _tarjeta_limites(self) -> Tarjeta:
        tarjeta = Tarjeta(size_hint_y=None, height=dp(196), padding=(dp(16), dp(14), dp(16), dp(12)), spacing=dp(2))
        tarjeta.add_widget(self._titulo("Límites de control"))

        self.valor_lsc = self._fila_valor("Límite superior (LSC)")
        self.valor_obj = self._fila_valor("Objetivo")
        self.valor_lic = self._fila_valor("Límite inferior (LIC)")
        tarjeta.add_widget(self.valor_lsc)
        tarjeta.add_widget(self.valor_obj)
        tarjeta.add_widget(self.valor_lic)

        tarjeta.add_widget(
            Etiqueta(
                text="Los límites se modifican desde el panel de escritorio.\nEsta app solo los muestra.",
                font_size=sp(11),
                color=rgba(TEMA.TEXTO_SUAVE),
                halign="left",
                valign="top",
                size_hint_y=None,
                height=dp(40),
            )
        )
        return tarjeta

    # ------------------------ Tarjeta indicadores ---------------------------
    def _tarjeta_indicadores(self) -> Tarjeta:
        tarjeta = Tarjeta(size_hint_y=None, height=dp(104), padding=(dp(16), dp(14), dp(16), dp(12)), spacing=dp(4))
        tarjeta.add_widget(self._titulo("Historial local"))
        self.detalle = Etiqueta(text="", font_size=sp(12), color=rgba(TEMA.TEXTO_MEDIO), halign="left", valign="top")
        tarjeta.add_widget(self.detalle)
        return tarjeta

    # -------------------------------- Auxiliares ----------------------------
    @staticmethod
    def _titulo(texto: str) -> Etiqueta:
        return Etiqueta(
            text=texto,
            font_size=sp(14.5),
            bold=True,
            color=rgba(TEMA.TEXTO),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(26),
        )

    @staticmethod
    def _fila_valor(etiqueta: str) -> BoxLayout:
        fila = BoxLayout(size_hint_y=None, height=dp(26))
        fila.add_widget(Etiqueta(text=etiqueta, font_size=sp(12.5), color=rgba(TEMA.TEXTO_SUAVE), halign="left", valign="middle"))
        valor = Etiqueta(text="-", font_size=sp(13.5), bold=True, color=rgba(TEMA.TEXTO), halign="right", valign="middle")
        fila.add_widget(valor)
        fila.valor = valor
        return fila

    # ------------------------------- Refresco -------------------------------
    def _refrescar(self, *_args) -> None:
        ctrl = self.controlador
        self.valor_lsc.valor.text = f"{ctrl.lsc:.1f} °C"
        self.valor_obj.valor.text = f"{ctrl.objetivo:.1f} °C"
        self.valor_lic.valor.text = f"{ctrl.lic:.1f} °C"
        self.detalle.text = f"{ctrl.total_lecturas} lecturas archivadas en este dispositivo."
