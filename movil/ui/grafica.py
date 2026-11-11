"""Pantalla 2: Grafica.

Historial de temperatura a pantalla completa con el selector Hoy / 7 dias /
30 dias.
"""

from __future__ import annotations

from datetime import datetime

from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout

from .. import theme as TEMA
from .carta import CartaControl
from .widgets import Etiqueta, Icono, MarcaColor, SelectorSegmentado, rgba

RANGOS = ("Hoy", "7 días", "30 días")


class PantallaGrafica(BoxLayout):
    """Vista de historial."""

    def __init__(self, controlador, **kwargs):
        super().__init__(
            orientation="vertical",
            padding=(dp(TEMA.ESPACIO), dp(10), dp(TEMA.ESPACIO), dp(10)),
            spacing=dp(8),
            **kwargs,
        )
        self.controlador = controlador
        self.rango_seleccionado = "Hoy"

        # Cabecera: titulo (izquierda) y selector de rango (derecha).
        cabecera = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(7))
        cabecera.add_widget(Icono(nombre="grafica", color=TEMA.AZUL, size_hint=(None, None), size=(dp(22), dp(22))))
        cabecera.add_widget(
            Etiqueta(
                text="Historial de temperatura",
                font_size=sp(15),
                bold=True,
                color=rgba(TEMA.TEXTO),
                halign="left",
                valign="middle",
                shorten=True,
                shorten_from="right",
            )
        )
        self.selector = SelectorSegmentado(
            opciones=list(RANGOS),
            seleccionado=self.rango_seleccionado,
            al_cambiar=self._cambiar_rango,
            size_hint=(None, None),
            size=(dp(176), dp(30)),
        )
        cabecera.add_widget(self.selector)
        self.add_widget(cabecera)

        # Leyenda de los limites.
        leyenda = BoxLayout(size_hint_y=None, height=dp(20), spacing=dp(14))
        self.etiqueta_lsc = self._leyenda_item(TEMA.LIMITE, "LSC")
        self.etiqueta_lic = self._leyenda_item(TEMA.LIMITE, "LIC")
        leyenda.add_widget(self.etiqueta_lsc)
        leyenda.add_widget(self.etiqueta_lic)
        leyenda.add_widget(self._leyenda_item(TEMA.SERIE, "Temperatura"))
        self.add_widget(leyenda)

        self.carta = CartaControl(size_hint_y=1)
        self.add_widget(self.carta)

        # Resumen de indicadores (los mismos del panel de escritorio).
        self.resumen = Etiqueta(text="", font_size=sp(11.5), color=rgba(TEMA.TEXTO_SUAVE), halign="left", valign="top", size_hint_y=None, height=dp(34))
        self.add_widget(self.resumen)

        controlador.bind(
            temperatura=self._refrescar,
            lsc=self._refrescar,
            lic=self._refrescar,
            objetivo=self._refrescar,
            serie_hoy=self._refrescar,
            serie_7d=self._refrescar,
            serie_30d=self._refrescar,
        )
        Clock.schedule_once(lambda _dt: self._refrescar(), 0)

    @staticmethod
    def _leyenda_item(color: str, texto: str) -> BoxLayout:
        item = BoxLayout(spacing=dp(5), size_hint_x=None, width=dp(104))
        item.add_widget(MarcaColor(color=color, size_hint=(None, None), size=(dp(14), dp(4))))
        item.add_widget(Etiqueta(text=texto, font_size=sp(11), color=rgba(TEMA.TEXTO_MEDIO), halign="left", valign="middle"))
        return item

    def _cambiar_rango(self, rango: str) -> None:
        self.rango_seleccionado = rango
        self._refrescar()

    def _refrescar(self, *_args) -> None:
        ctrl = self.controlador
        if self.rango_seleccionado == "Hoy":
            serie = ctrl.serie_hoy
            rango_x = (0.0, 24.0)
            ticks = ctrl.ticks_hoy()
        elif self.rango_seleccionado == "7 días":
            serie = ctrl.serie_7d
            rango_x = (0.0, 7.0)
            ticks = ctrl.ticks_dias(7)
        else:
            serie = ctrl.serie_30d
            rango_x = (0.0, 30.0)
            ticks = ctrl.ticks_dias(30)

        self.carta.set_datos(
            *serie,
            ctrl.lsc,
            ctrl.lic,
            ctrl.objetivo,
            rango_x=rango_x,
            ticks_x=ticks,
            etiqueta_punto=f"{ctrl.temperatura:.1f}°C" if ctrl.hay_datos else "",
            subtitulo_punto=datetime.now().strftime("%H:%M"),
        )

        media, fuera, indice = ctrl.indicador_actual()
        self.etiqueta_lsc.children[1].text = f"LSC {ctrl.lsc:g}°C"
        self.etiqueta_lic.children[1].text = f"LIC {ctrl.lic:g}°C"
        self.resumen.text = (
            f"Media temporal: {media:.2f}°C    Puntos fuera de límite: {fuera}\n"
            f"Índice de defectos: {indice:.1f}%"
        )
