"""Widgets reutilizables de la app movil.

Todo se dibuja con primitivas de canvas (sin ficheros de imagen): asi el APK
no depende de recursos y los iconos escalan sin pixeles borrosos.
"""

from __future__ import annotations

import math

from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from .. import theme as TEMA


def rgba(hex_color: str, alpha: float = 1.0) -> list[float]:
    """Convierte "#RRGGBB" en una tupla RGBA que Kivy entiende."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
    return [r, g, b, alpha]


class Etiqueta(Label):
    """Label con `text_size` automatico.

    En Kivy, `halign` y `valign` solo surten efecto si `text_size` esta
    definido; esta clase lo mantiene sincronizado con el tamano del widget.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self._sincronizar, texture_size=self._sincronizar)

    def _sincronizar(self, *_args) -> None:
        if self.text_size != self.size:
            self.text_size = self.size


# ================================ Iconos =====================================
class Icono(Widget):
    """Icono vectorial dibujado en el canvas.

    Nombres: `termometro`, `wifi`, `senal`, `grafica`, `casa`, `engranaje`,
    `check`, `alerta`.
    """

    def __init__(self, nombre: str = "termometro", color: str = TEMA.AZUL, **kwargs):
        super().__init__(**kwargs)
        self.nombre = nombre
        self.color_hex = color
        self.bind(pos=self._dibujar, size=self._dibujar)

    def set_color(self, color: str) -> None:
        self.color_hex = color
        self._dibujar()

    def _dibujar(self, *_args) -> None:
        self.canvas.clear()
        if self.width <= 1 or self.height <= 1:
            return
        # Todos los iconos se dibujan dentro de un cuadrado centrado.
        lado = min(self.width, self.height)
        ox = self.x + (self.width - lado) / 2
        oy = self.y + (self.height - lado) / 2
        with self.canvas:
            Color(rgba=rgba(self.color_hex))
            getattr(self, f"_dibujar_{self.nombre}")(ox, oy, lado)

    # -- Cada icono trabaja en un cuadrado (ox, oy, lado) ------------------
    def _dibujar_termometro(self, ox, oy, lado) -> None:
        x = ox + lado * 0.46
        y_bulbo = oy + lado * 0.22
        y_tope = oy + lado * 0.76
        r = lado * 0.13
        # Tubo del termometro.
        Line(points=[x, y_bulbo + r * 0.4, x, y_tope], width=dp(2.4), cap="round")
        # Bulbo.
        Line(circle=(x, y_bulbo, r), width=dp(2.4))
        # Mercurio.
        Line(points=[x, y_bulbo, x, y_bulbo + lado * 0.34], width=dp(3.2), cap="round")
        Ellipse(pos=(x - r * 0.45, y_bulbo - r * 0.45), size=(r * 0.9, r * 0.9))

    def _dibujar_wifi(self, ox, oy, lado) -> None:
        cx = ox + lado * 0.5
        cy = oy + lado * 0.20
        # Tres arcos concentricos (semicirculo superior) + punto emisor.
        for r in (lado * 0.24, lado * 0.38, lado * 0.52):
            pts = []
            for k in range(13):
                ang = math.pi * (1.0 - k / 12.0)
                pts.extend([cx + r * math.cos(ang), cy + r * math.sin(ang)])
            Line(points=pts, width=dp(2.2), cap="round", joint="round")
        Ellipse(pos=(cx - lado * 0.05, cy - lado * 0.04), size=(lado * 0.10, lado * 0.10))

    def _dibujar_senal(self, ox, oy, lado) -> None:
        base = oy + lado * 0.18
        for i in range(4):
            h = lado * (0.16 + i * 0.17)
            x = ox + lado * 0.16 + i * lado * 0.18
            RoundedRectangle(
                pos=(x, base),
                size=(lado * 0.11, h),
                radius=[dp(2)],
            )

    def _dibujar_grafica(self, ox, oy, lado) -> None:
        x0 = ox + lado * 0.18
        y0 = oy + lado * 0.22
        Line(points=[x0, y0, x0 + lado * 0.66, y0], width=dp(1.8), cap="round")
        Line(points=[x0, y0, x0, y0 + lado * 0.56], width=dp(1.8), cap="round")
        pts = []
        for k in range(4):
            px = x0 + lado * 0.10 * k
            py = y0 + lado * (0.12 + 0.10 * (k % 2)) + lado * 0.22
            pts.extend([px, py])
        Line(points=pts, width=dp(2.0), cap="round", joint="round")

    def _dibujar_casa(self, ox, oy, lado) -> None:
        x0 = ox + lado * 0.16
        y0 = oy + lado * 0.20
        w = lado * 0.68
        h = lado * 0.34
        Line(points=[x0, y0 + h, x0 + w / 2, y0 + h + lado * 0.24, x0 + w, y0 + h], width=dp(2.2), joint="round")
        Line(points=[x0 + lado * 0.08, y0 + h - lado * 0.02, x0 + lado * 0.08, y0, x0 + w - lado * 0.08, y0, x0 + w - lado * 0.08, y0 + h - lado * 0.02], width=dp(2.0), joint="round")

    def _dibujar_engranaje(self, ox, oy, lado) -> None:
        cx = ox + lado * 0.5
        cy = oy + lado * 0.5
        r = lado * 0.26
        Line(circle=(cx, cy, r), width=dp(2.2))
        Line(circle=(cx, cy, r * 0.42), width=dp(2.2))
        for k in range(8):
            ang = 2 * math.pi * k / 8
            x1 = cx + math.cos(ang) * r
            y1 = cy + math.sin(ang) * r
            x2 = cx + math.cos(ang) * (r + lado * 0.13)
            y2 = cy + math.sin(ang) * (r + lado * 0.13)
            Line(points=[x1, y1, x2, y2], width=dp(2.4), cap="round")

    def _dibujar_check(self, ox, oy, lado) -> None:
        Line(
            points=[ox + lado * 0.22, oy + lado * 0.52, ox + lado * 0.42, oy + lado * 0.32, ox + lado * 0.78, oy + lado * 0.70],
            width=dp(2.6),
            cap="round",
            joint="round",
        )

    def _dibujar_alerta(self, ox, oy, lado) -> None:
        Line(
            points=[ox + lado * 0.5, oy + lado * 0.80, ox + lado * 0.88, oy + lado * 0.24, ox + lado * 0.12, oy + lado * 0.24, ox + lado * 0.5, oy + lado * 0.80],
            width=dp(2.2),
            joint="round",
        )
        Line(points=[ox + lado * 0.5, oy + lado * 0.30, ox + lado * 0.5, oy + lado * 0.52], width=dp(2.2), cap="round")
        Ellipse(pos=(ox + lado * 0.47, oy + lado * 0.22), size=(lado * 0.06, lado * 0.06))


# =============================== Tarjetas ===================================
class Tarjeta(BoxLayout):
    """Tarjeta blanca redondeada con borde suave (vertical por defecto)."""

    def __init__(self, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        super().__init__(**kwargs)
        self._fondo = None
        self._borde = None
        with self.canvas.before:
            self._color_fondo = Color(rgba=rgba(TEMA.TARJETA))
            self._fondo = RoundedRectangle(radius=[dp(TEMA.RADIO)] * 4)
            self._color_borde = Color(rgba=rgba(TEMA.TARJETA_BORDE))
            self._borde = Line(width=dp(1))
        self.bind(pos=self._sincronizar, size=self._sincronizar)

    def _sincronizar(self, *_args) -> None:
        self._fondo.pos = self.pos
        self._fondo.size = self.size
        self._borde.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(TEMA.RADIO))


class CirculoIcono(Widget):
    """Circulo claro con un icono en el centro (como en la imagen)."""

    def __init__(self, nombre: str = "termometro", color_icono: str = TEMA.AZUL, **kwargs):
        super().__init__(**kwargs)
        self.icono = Icono(nombre=nombre, color=color_icono)
        self.add_widget(self.icono)
        self.bind(pos=self._sincronizar, size=self._sincronizar)

    def _sincronizar(self, *_args) -> None:
        lado = min(self.width, self.height)
        self.icono.pos = (self.x + (self.width - lado) / 2, self.y + (self.height - lado) / 2)
        self.icono.size = (lado, lado)


# ================================ Badge =====================================
class Badge(Etiqueta):
    """Capsula de estado: "Conectado" / "Sin conexion".

    Ancho fijo: asi el texto no puede realimentar el tamano del widget.
    """

    ANCHO = dp(104)

    def __init__(self, texto: str = "", color: str = TEMA.VERDE, fondo: str = TEMA.VERDE_CLARO, **kwargs):
        kwargs.setdefault("halign", "center")
        kwargs.setdefault("valign", "middle")
        kwargs.setdefault("shorten", True)
        kwargs.setdefault("shorten_from", "right")
        super().__init__(**kwargs)
        self.color_fondo = fondo
        self.color_texto = color
        self.text = texto
        self.font_size = sp(12)
        self.bold = True
        self.size_hint = (None, None)
        self.size = (self.ANCHO, dp(32))
        self.color = rgba(color)
        with self.canvas.before:
            self._color = Color(rgba=rgba(self.color_fondo))
            self._rect = RoundedRectangle(radius=[dp(16)] * 4)
        self.bind(pos=self._pintar_fondo, size=self._pintar_fondo)
        self._pintar_fondo()

    def actualizar(self, texto: str, color: str, fondo: str) -> None:
        self.text = texto
        self.color_texto = color
        self.color_fondo = fondo
        self.color = rgba(color)
        self._color.rgba = rgba(fondo)
        self._pintar_fondo()

    def _pintar_fondo(self, *_args) -> None:
        self._rect.pos = self.pos
        self._rect.size = self.size


# ========================= Selector segmentado ==============================
class SelectorSegmentado(BoxLayout):
    """Grupo de opciones tipo pastilla: Hoy / 7 dias / 30 dias."""

    def __init__(self, opciones: list[str], seleccionado: str = "", al_cambiar=None, **kwargs):
        super().__init__(**kwargs)
        self.opciones = opciones
        self.al_cambiar = al_cambiar
        self.seleccionado = seleccionado
        self.botones: dict[str, Label] = {}
        self._fondo = None
        with self.canvas.before:
            self._color = Color(rgba=rgba("#EDF2F8"))
            self._fondo = RoundedRectangle(radius=[dp(16)] * 4)
        for opcion in opciones:
            boton = Etiqueta(
                text=opcion,
                font_size=sp(12),
                bold=True,
                halign="center",
                valign="middle",
            )
            boton.bind(on_touch_down=lambda _w, toque, o=opcion: self._pulsado(o, toque))
            self.add_widget(boton)
            self.botones[opcion] = boton
        self.bind(pos=self._sincronizar, size=self._sincronizar)
        self._pintar()

    def _pulsado(self, opcion: str, toque) -> None:
        if not self.collide_point(*toque.pos):
            return
        self.set_seleccionado(opcion)
        if self.al_cambiar:
            self.al_cambiar(opcion)

    def set_seleccionado(self, opcion: str) -> None:
        """Selecciona una opcion desde codigo y repinta."""
        self.seleccionado = opcion
        self._pintar()

    def _pintar(self) -> None:
        for opcion, boton in self.botones.items():
            activo = opcion == self.seleccionado
            boton.color = rgba(TEMA.TEXTO if not activo else "#FFFFFF")
            with boton.canvas.before:
                boton.canvas.before.clear()
                if activo:
                    Color(rgba=rgba(TEMA.AZUL))
                    RoundedRectangle(pos=boton.pos, size=boton.size, radius=[dp(13)] * 4)

    def _sincronizar(self, *_args) -> None:
        self._fondo.pos = self.pos
        self._fondo.size = self.size
        n = max(1, len(self.opciones))
        ancho = self.width / n
        for i, opcion in enumerate(self.opciones):
            boton = self.botones[opcion]
            boton.size = (ancho, self.height)
            boton.pos = (self.x + i * ancho, self.y)
            self._pintar()


# ============================ Barra inferior ================================
class ItemNav(Widget):
    """Un destino de la barra inferior: icono + etiqueta."""

    def __init__(self, nombre: str, etiqueta: str, icono: str, al_pulsar, **kwargs):
        super().__init__(**kwargs)
        self.al_pulsar = al_pulsar
        self.etiqueta = etiqueta
        self.icono = Icono(nombre=icono, color=TEMA.TEXTO_SUAVE)
        self.texto = Etiqueta(
            text=etiqueta,
            font_size=sp(10.5),
            color=rgba(TEMA.TEXTO_SUAVE),
            halign="center",
            valign="middle",
        )
        self.add_widget(self.icono)
        self.add_widget(self.texto)
        self.activo = False
        self.bind(pos=self._sincronizar, size=self._sincronizar)

    def set_activo(self, activo: bool) -> None:
        self.activo = activo
        color = TEMA.AZUL if activo else TEMA.TEXTO_SUAVE
        self.icono.set_color(color)
        self.texto.color = rgba(color)

    def on_touch_down(self, toque):
        if self.collide_point(*toque.pos):
            self.al_pulsar()
            return True
        return super().on_touch_down(toque)

    def _sincronizar(self, *_args) -> None:
        alto_icono = min(self.height * 0.52, dp(26))
        self.icono.size = (alto_icono, alto_icono)
        self.icono.pos = (self.x + (self.width - alto_icono) / 2, self.y + self.height * 0.44)
        self.texto.size = (self.width, self.height * 0.36)
        self.texto.pos = (self.x, self.y)


class BarraInferior(BoxLayout):
    """Barra de navegacion inferior con tres destinos."""

    def __init__(self, destinos: list[tuple[str, str, str]], al_navegar, **kwargs):
        super().__init__(**kwargs)
        self.al_navegar = al_navegar
        self.items: dict[str, ItemNav] = {}
        for clave, etiqueta, icono in destinos:
            item = ItemNav(clave, etiqueta, icono, lambda c=clave: self.al_navegar(c))
            self.add_widget(item)
            self.items[clave] = item
        with self.canvas.before:
            Color(rgba=rgba("#FFFFFF"))
            self._fondo = Rectangle(pos=self.pos, size=self.size)
            Color(rgba=rgba("#E4EBF3"))
            self._linea = Line(width=dp(1))
        self.bind(pos=self._sincronizar, size=self._sincronizar)

    def set_activo(self, clave: str) -> None:
        for c, item in self.items.items():
            item.set_activo(c == clave)

    def _sincronizar(self, *_args) -> None:
        self._fondo.pos = self.pos
        self._fondo.size = self.size
        self._linea.points = [self.x, self.top, self.right, self.top]
        n = max(1, len(self.items))
        ancho = self.width / n
        for i, (clave, item) in enumerate(self.items.items()):
            item.size = (ancho, self.height)
            item.pos = (self.x + i * ancho, self.y)


# ============================ Fila de opcion ================================
class FilaRadio(BoxLayout):
    """Fila seleccionable con un indicador de radio (para Ajustes)."""

    def __init__(self, titulo: str, subtitulo: str = "", seleccionado: bool = False, al_seleccionar=None, **kwargs):
        super().__init__(**kwargs)
        self.al_seleccionar = al_seleccionar
        self.seleccionado = seleccionado

        self.indicador = Widget(size_hint=(None, None), size=(dp(22), dp(22)))
        self.indicador.bind(pos=self._pintar_indicador, size=self._pintar_indicador)
        self.titulo = Etiqueta(text=titulo, font_size=sp(14), color=rgba(TEMA.TEXTO), bold=True, halign="left", valign="middle")
        self.subtitulo = Etiqueta(text=subtitulo, font_size=sp(11.5), color=rgba(TEMA.TEXTO_SUAVE), halign="left", valign="middle")
        textos = BoxLayout(orientation="vertical", spacing=dp(1))
        textos.add_widget(self.titulo)
        if subtitulo:
            textos.add_widget(self.subtitulo)

        self.add_widget(self.indicador)
        self.add_widget(textos)

        with self.indicador.canvas:
            Color(rgba=rgba(TEMA.AZUL if seleccionado else "#FFFFFF"))
            self._anillo = Line(width=dp(1.8))
            Color(rgba=rgba(TEMA.AZUL if seleccionado else "#C3CEDB"))
            self._borde = Line(width=dp(1.2))
            if seleccionado:
                Color(rgba=rgba(TEMA.AZUL))
                self._punto = Ellipse()
            else:
                self._punto = None

        self.bind(on_touch_down=self._tocar)
        self.bind(pos=self._alinear_indicador, size=self._alinear_indicador)
        self._alinear_indicador()
        self._pintar_indicador()

    def _alinear_indicador(self, *_args) -> None:
        """Pega el radio a la parte alta de la fila (alineado con el titulo)."""
        self.indicador.y = self.top - self.indicador.height

    def _pintar_indicador(self, *_args) -> None:
        """Dibuja el radio. OJO: el canvas usa coordenadas absolutas."""
        ind = self.indicador
        cx = ind.x + ind.width / 2
        cy = ind.y + ind.height / 2
        r = min(ind.width, ind.height) * 0.42
        self._anillo.circle = (cx, cy, r)
        self._borde.circle = (cx, cy, r + dp(1))
        if self._punto is not None:
            self._punto.pos = (cx - r * 0.42, cy - r * 0.42)
            self._punto.size = (r * 0.84, r * 0.84)

    def set_seleccionado(self, seleccionado: bool) -> None:
        self.seleccionado = seleccionado
        with self.indicador.canvas:
            self.indicador.canvas.clear()
            Color(rgba=rgba(TEMA.AZUL if seleccionado else "#FFFFFF"))
            self._anillo = Line(width=dp(1.8))
            Color(rgba=rgba(TEMA.AZUL if seleccionado else "#C3CEDB"))
            self._borde = Line(width=dp(1.2))
            if seleccionado:
                Color(rgba=rgba(TEMA.AZUL))
                self._punto = Ellipse()
            else:
                self._punto = None
        self._pintar_indicador()

    def _tocar(self, widget, toque) -> None:
        if not self.collide_point(*toque.pos):
            return False
        if self.al_seleccionar:
            self.al_seleccionar()
        return True


# ============================ Marca de leyenda ===============================
class MarcaColor(Widget):
    """Small colored rectangle used as a legend marker."""

    def __init__(self, color: str = TEMA.SERIE, **kwargs):
        super().__init__(**kwargs)
        self.color_hex = color
        with self.canvas:
            Color(rgba=rgba(color))
            self._rect = RoundedRectangle(radius=[dp(2)] * 4)
        self.bind(pos=self._sincronizar, size=self._sincronizar)

    def _sincronizar(self, *_args) -> None:
        self._rect.pos = self.pos
        self._rect.size = self.size


# ============================== Logo de la app ===============================
class LogoApp(Widget):
    """Cuadrado azul redondeado con el termometro blanco (cabecera)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(rgba=rgba(TEMA.AZUL))
            self._fondo = RoundedRectangle(radius=[dp(14)] * 4)
        self._icono = Icono(nombre="termometro", color="#FFFFFF")
        self.add_widget(self._icono)
        self.bind(pos=self._sincronizar, size=self._sincronizar)

    def _sincronizar(self, *_args) -> None:
        self._fondo.pos = self.pos
        self._fondo.size = self.size
        lado = min(self.width, self.height) * 0.62
        self._icono.pos = (self.x + (self.width - lado) / 2, self.y + (self.height - lado) / 2)
        self._icono.size = (lado, lado)
