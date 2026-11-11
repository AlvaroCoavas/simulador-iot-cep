"""Pantalla 1: Inicio.

Cabecera con el estado de conexion, tarjeta de temperatura actual, miniatura
del historial y tarjeta de conexion, tal como en la imagen de referencia.
"""

from __future__ import annotations

from datetime import datetime

from kivy.clock import Clock
from kivy.graphics import Color, Line
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from .. import config
from .. import theme as TEMA
from .carta import CartaControl
from .widgets import Badge, CirculoIcono, Etiqueta, Icono, LogoApp, SelectorSegmentado, Tarjeta, rgba

RANGOS = ("Hoy", "7 días", "30 días")


class PantallaInicio(BoxLayout):
    """Home del movil."""

    def __init__(self, controlador, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.controlador = controlador
        self.rango_seleccionado = "Hoy"

        self.add_widget(self._cabecera())

        desplazamiento = ScrollView(do_scroll_x=False, bar_width=dp(2))
        contenido = BoxLayout(
            orientation="vertical",
            spacing=dp(TEMA.ESPACIO),
            padding=(dp(TEMA.ESPACIO), dp(TEMA.ESPACIO), dp(TEMA.ESPACIO), dp(TEMA.ESPACIO)),
        )
        contenido.size_hint_y = None
        contenido.bind(minimum_height=contenido.setter("height"))
        contenido.add_widget(self._tarjeta_temperatura())
        contenido.add_widget(self._tarjeta_historial())
        contenido.add_widget(self._tarjeta_conexion())
        desplazamiento.add_widget(contenido)
        self.add_widget(desplazamiento)

        # Se repinta cuando llegan datos o cambian los limites.
        controlador.bind(
            temperatura=self._refrescar,
            lsc=self._refrescar,
            lic=self._refrescar,
            objetivo=self._refrescar,
            serie_hoy=self._refrescar,
            serie_7d=self._refrescar,
            serie_30d=self._refrescar,
            conexion_texto=self._refrescar,
        )
        Clock.schedule_once(lambda _dt: self._refrescar(), 0)

    # ------------------------------- Cabecera -------------------------------
    def _cabecera(self) -> BoxLayout:
        cabecera = BoxLayout(
            size_hint_y=None,
            height=dp(66),
            padding=(dp(TEMA.ESPACIO), dp(6), dp(TEMA.ESPACIO), dp(6)),
            spacing=dp(11),
        )
        cabecera.add_widget(LogoApp(size_hint=(None, None), size=(dp(48), dp(48))))

        textos = BoxLayout(orientation="vertical", spacing=dp(1))
        titulo = Etiqueta(text=config.TITULO, font_size=sp(21), bold=True, color=rgba(TEMA.TEXTO), halign="left", valign="bottom")
        subtitulo = Etiqueta(text=config.SUBTITULO, font_size=sp(12.5), color=rgba(TEMA.TEXTO_SUAVE), halign="left", valign="top")
        textos.add_widget(titulo)
        textos.add_widget(subtitulo)
        cabecera.add_widget(textos)

        self.badge = Badge(texto="Conectando")
        cabecera.add_widget(self.badge)
        return cabecera

    # --------------------------- Tarjeta temperatura ------------------------
    def _tarjeta_temperatura(self) -> Tarjeta:
        tarjeta = Tarjeta(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(116),
            padding=(dp(16), dp(14), dp(16), dp(14)),
            spacing=dp(13),
        )
        tarjeta.add_widget(CirculoIcono(nombre="termometro", size_hint=(None, None), size=(dp(60), dp(60))))

        centro = BoxLayout(orientation="vertical", spacing=dp(1))
        etiqueta = Etiqueta(text="Temperatura actual", font_size=sp(13), color=rgba(TEMA.TEXTO_SUAVE), halign="left", valign="bottom")
        self.valor = Etiqueta(text="--.-°C", font_size=sp(33), bold=True, color=rgba(TEMA.TEXTO), halign="left", valign="middle")
        self.estado = BoxLayout(size_hint_y=None, height=dp(20), spacing=dp(4))
        self.icono_estado = Icono(nombre="check", color=TEMA.VERDE, size_hint=(None, None), size=(dp(16), dp(16)))
        self.texto_estado = Etiqueta(text="En rango", font_size=sp(13), bold=True, color=rgba(TEMA.VERDE), halign="left", valign="middle")
        self.estado.add_widget(self.icono_estado)
        self.estado.add_widget(self.texto_estado)
        centro.add_widget(etiqueta)
        centro.add_widget(self.valor)
        centro.add_widget(self.estado)
        tarjeta.add_widget(centro)

        # Separador vertical.
        separador = Widget(size_hint=(None, None), size=(dp(1), dp(70)))
        with separador.canvas:
            Color(rgba=rgba(TEMA.TARJETA_BORDE))
            separador._linea = Line(points=[0, 0, 0, 70], width=dp(1))
        separador.bind(pos=self._sincronizar_separador, size=self._sincronizar_separador)
        tarjeta.add_widget(separador)

        derecha = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_x=None, width=dp(104))
        derecha.add_widget(Etiqueta(text="Rango permitido", font_size=sp(12.5), color=rgba(TEMA.TEXTO_SUAVE), halign="right", valign="bottom"))
        self.rango = Etiqueta(text="-2°C / 8°C", font_size=sp(18), bold=True, color=rgba(TEMA.TEXTO), halign="right", valign="top")
        derecha.add_widget(self.rango)
        tarjeta.add_widget(derecha)
        return tarjeta

    # --------------------------- Tarjeta historial --------------------------
    def _tarjeta_historial(self) -> Tarjeta:
        tarjeta = Tarjeta(size_hint_y=None, height=dp(246), padding=(dp(14), dp(12), dp(14), dp(10)), spacing=dp(4))

        cabecera = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(7))
        cabecera.add_widget(Icono(nombre="grafica", color=TEMA.AZUL, size_hint=(None, None), size=(dp(21), dp(21))))
        cabecera.add_widget(
            Etiqueta(
                text="Historial de temperatura",
                font_size=sp(14),
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
            size=(dp(168), dp(28)),
        )
        cabecera.add_widget(self.selector)
        tarjeta.add_widget(cabecera)

        self.carta = CartaControl()
        tarjeta.add_widget(self.carta)
        return tarjeta

    # --------------------------- Tarjeta conexion ---------------------------
    def _tarjeta_conexion(self) -> Tarjeta:
        tarjeta = Tarjeta(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(74),
            padding=(dp(16), dp(12), dp(16), dp(12)),
            spacing=dp(13),
        )
        tarjeta.add_widget(CirculoIcono(nombre="wifi", size_hint=(None, None), size=(dp(46), dp(46))))
        textos = BoxLayout(orientation="vertical", spacing=dp(1))
        textos.add_widget(Etiqueta(text="Conexión WiFi", font_size=sp(14.5), bold=True, color=rgba(TEMA.TEXTO), halign="left", valign="bottom"))
        self.detalle_conexion = Etiqueta(text="Datos en tiempo real", font_size=sp(11.5), color=rgba(TEMA.TEXTO_SUAVE), halign="left", valign="top")
        textos.add_widget(self.detalle_conexion)
        tarjeta.add_widget(textos)
        tarjeta.add_widget(Icono(nombre="senal", color=TEMA.VERDE, size_hint=(None, None), size=(dp(28), dp(28))))
        return tarjeta

    # ------------------------------ Refresco --------------------------------
    @staticmethod
    def _sincronizar_separador(separador, *_args) -> None:
        separador._linea.points = [separador.x, separador.y, separador.x, separador.top]

    def _cambiar_rango(self, rango: str) -> None:
        self.rango_seleccionado = rango
        self._refrescar()

    def _refrescar(self, *_args) -> None:
        ctrl = self.controlador
        self.valor.text = f"{ctrl.temperatura:.1f}°C" if ctrl.hay_datos else "--.-°C"
        self.texto_estado.text = ctrl.estado_etiqueta
        self.texto_estado.color = rgba(ctrl.estado_color)
        self.icono_estado.nombre = "check" if ctrl.estado_cep == "ESTABLE" else "alerta"
        self.icono_estado.color = ctrl.estado_color
        self.icono_estado._dibujar()
        self.rango.text = ctrl.rango_texto
        self.badge.actualizar(ctrl.conexion_texto, ctrl.conexion_color, ctrl.conexion_fondo)
        self.detalle_conexion.text = "Datos en tiempo real" if ctrl.conexion == "conectado" else ctrl.conexion_texto

        self.carta.set_datos(
            *self._serie(),
            ctrl.lsc,
            ctrl.lic,
            ctrl.objetivo,
            rango_x=self._rango_x(),
            ticks_x=self._ticks_x(),
            etiqueta_punto=f"{ctrl.temperatura:.1f}°C" if ctrl.hay_datos else "",
            subtitulo_punto=datetime.now().strftime("%H:%M"),
        )

    def _serie(self) -> tuple[list[float], list[float]]:
        ctrl = self.controlador
        if self.rango_seleccionado == "Hoy":
            return ctrl.serie_hoy
        if self.rango_seleccionado == "7 días":
            return ctrl.serie_7d
        return ctrl.serie_30d

    def _rango_x(self) -> tuple[float, float]:
        if self.rango_seleccionado == "Hoy":
            return (0.0, 24.0)
        return (0.0, 7.0 if self.rango_seleccionado == "7 días" else 30.0)

    def _ticks_x(self) -> list[tuple[float, str]]:
        ctrl = self.controlador
        if self.rango_seleccionado == "Hoy":
            return ctrl.ticks_hoy()
        return ctrl.ticks_dias(7 if self.rango_seleccionado == "7 días" else 30)
