"""Punto de entrada de la app movil (Kivy).

Estructura de la ventana:
    +---------------------------------+
    |  barra de estado (espacio)      |
    |  pantalla activa (Inicio/       |
    |  Grafica/Ajustes)               |
    |  barra inferior de navegacion   |
    +---------------------------------+

Ejecucion en el escritorio:
    py -3.14 -m movil.main
"""

from __future__ import annotations

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import NoTransition, Screen, ScreenManager

from . import theme as TEMA
from .controlador import Controlador
from .ui.ajustes import PantallaAjustes
from .ui.grafica import PantallaGrafica
from .ui.inicio import PantallaInicio
from .ui.widgets import BarraInferior, rgba

DESTINOS = (
    ("inicio", "Inicio", "casa"),
    ("grafica", "Gráfica", "grafica"),
    ("ajustes", "Ajustes", "engranaje"),
)


class FondoApp(BoxLayout):
    """Fondo con degradado azul muy claro (como en la imagen)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(rgba=rgba(TEMA.FONDO))
            self._sup = Rectangle(pos=self.pos, size=self.size)
            Color(rgba=rgba(TEMA.FONDO_ALT))
            self._inf = Rectangle(pos=self.pos, size=(self.width, self.height / 2))
        self.bind(pos=self._sincronizar, size=self._sincronizar)

    def _sincronizar(self, *_args) -> None:
        self._sup.pos = self.pos
        self._sup.size = self.size
        self._inf.pos = (self.x, self.y)
        self._inf.size = (self.width, self.height / 2)


class SimuladorApp(App):
    """Aplicacion movil del panel CEP."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Temperatura - CEP"
        self.controlador = Controlador()

    def build(self):
        raiz = FondoApp(orientation="vertical")

        # Espacio de la barra de estado del sistema.
        raiz.add_widget(BoxLayout(size_hint_y=None, height=dp(26)))

        self.gestor = ScreenManager(transition=NoTransition())
        for clave, etiqueta, icono in DESTINOS:
            pantalla = Screen(name=clave)
            if clave == "inicio":
                pantalla.add_widget(PantallaInicio(self.controlador))
            elif clave == "grafica":
                pantalla.add_widget(PantallaGrafica(self.controlador))
            else:
                pantalla.add_widget(PantallaAjustes(self.controlador))
            self.gestor.add_widget(pantalla)
        raiz.add_widget(self.gestor)

        self.barra = BarraInferior(DESTINOS, self._navegar, size_hint_y=None, height=dp(TEMA.ALTO_BARRA))
        raiz.add_widget(self.barra)

        self.controlador.iniciar()
        self.barra.set_activo("inicio")
        return raiz

    def _navegar(self, clave: str) -> None:
        self.gestor.current = clave
        self.barra.set_activo(clave)

    def on_stop(self) -> None:
        self.controlador.detener()


def main() -> int:
    from kivy.utils import platform

    if platform != "android":
        # En el escritorio se abre con proporciones de telefono para
        # comprobar el diseno sin necesidad del emulador.
        Window.size = (420, 860)
        Window.minimum_width, Window.minimum_height = 360, 640
    Window.clearcolor = rgba(TEMA.FONDO)
    SimuladorApp().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
