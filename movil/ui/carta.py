"""Carta de control individual (X) dibujada con canvas de Kivy.

matplotlib no funciona en Android, asi que la grafica se dibuja a mano con
primitivas de canvas. Reproduce la carta de la imagen de referencia:

  * rejilla horizontal y vertical
  * banda verde entre los limites de control
  * lineas discontinuas verdes en LSC y LIC
  * serie azul de temperatura
  * marcador del ultimo punto con globo de informacion
"""

from __future__ import annotations

import math

from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.widget import Widget

from .. import theme as TEMA
from .widgets import rgba

# Margenes (en dp) para dejar sitio a las etiquetas de los ejes.
MARGEN_IZQ = 36
MARGEN_INF = 24
MARGEN_SUP = 12
MARGEN_DER = 12


class CartaControl(Widget):
    """Grafica de temperatura con limites de control."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.xs: list[float] = []
        self.ys: list[float] = []
        self.lsc = 8.0
        self.lic = 2.0
        self.objetivo = 5.0
        self.rango_x = (0.0, 24.0)
        self.ticks_x: list[tuple[float, str]] = []
        self.etiqueta_punto = ""
        self.subtitulo_punto = ""
        self._y_min = 0.0
        self._y_max = 1.0
        self.bind(pos=self._dibujar, size=self._dibujar)

    # ------------------------------- Datos ---------------------------------
    def set_datos(
        self,
        xs: list[float],
        ys: list[float],
        lsc: float,
        lic: float,
        objetivo: float,
        rango_x: tuple[float, float] | None = None,
        ticks_x: list[tuple[float, str]] | None = None,
        etiqueta_punto: str = "",
        subtitulo_punto: str = "",
    ) -> None:
        """Actualiza la serie y repinta."""
        self.xs = list(xs)
        self.ys = list(ys)
        self.lsc = lsc
        self.lic = lic
        self.objetivo = objetivo
        if rango_x is not None:
            self.rango_x = rango_x
        self.ticks_x = ticks_x if ticks_x is not None else self.ticks_x
        self.etiqueta_punto = etiqueta_punto
        self.subtitulo_punto = subtitulo_punto
        self._calcular_rango_y()
        self._dibujar()

    def _calcular_rango_y(self) -> None:
        """El eje vertical abarca los limites y la serie, con un margen."""
        valores = [self.lsc, self.lic, self.objetivo] + list(self.ys)
        valores = [v for v in valores if v is not None]
        if not valores:
            valores = [0.0, 1.0]
        y_min = min(valores)
        y_max = max(valores)
        if math.isclose(y_min, y_max):
            y_min -= 1.0
            y_max += 1.0
        margen = (y_max - y_min) * 0.12
        self._y_min = y_min - margen
        self._y_max = y_max + margen

    # ------------------------------ Utilidades ------------------------------
    def _area(self) -> tuple[float, float, float, float]:
        """(x0, y0, ancho, alto) del area de trazado."""
        x0 = self.x + dp(MARGEN_IZQ)
        y0 = self.y + dp(MARGEN_INF)
        w = max(dp(10), self.width - dp(MARGEN_IZQ + MARGEN_DER))
        h = max(dp(10), self.height - dp(MARGEN_INF + MARGEN_SUP))
        return x0, y0, w, h

    def _px(self, x_valor: float, x0: float, w: float) -> float:
        xa, xb = self.rango_x
        if math.isclose(xb, xa):
            return x0
        return x0 + (x_valor - xa) / (xb - xa) * w

    def _py(self, y_valor: float, y0: float, h: float) -> float:
        span = self._y_max - self._y_min
        if span <= 0:
            return y0
        return y0 + (y_valor - self._y_min) / span * h

    @staticmethod
    def _ticks_y(y_min: float, y_max: float, cantidad: int = 5) -> list[tuple[float, str]]:
        """Escala de valores redondos para el eje vertical."""
        span = y_max - y_min
        if span <= 0:
            return [(y_min, f"{y_min:.0f}°C")]
        bruto = span / max(1, cantidad - 1)
        paso = 1.0
        for candidato in (0.5, 1.0, 2.0, 2.5, 5.0, 10.0, 20.0, 25.0, 50.0):
            if bruto <= candidato:
                paso = candidato
                break
        else:
            paso = 100.0
        ticks = []
        valor = math.ceil(y_min / paso) * paso
        while valor <= y_max + 1e-9:
            ticks.append((valor, f"{valor:g}°C"))
            valor += paso
        return ticks

    # ------------------------------- Dibujo --------------------------------
    def _dibujar(self, *_args) -> None:
        self.canvas.clear()
        if self.width <= dp(MARGEN_IZQ + MARGEN_DER) or self.height <= dp(MARGEN_INF + MARGEN_SUP):
            return
        x0, y0, w, h = self._area()
        ticks_y = self._ticks_y(self._y_min, self._y_max)

        with self.canvas:
            # --- Fondo del area ---
            Color(rgba=rgba("#FFFFFF"))
            Rectangle(pos=(x0, y0), size=(w, h))

            # --- Banda de control (entre LIC y LSC) ---
            y_lsc = self._py(self.lsc, y0, h)
            y_lic = self._py(self.lic, y0, h)
            Color(rgba=rgba(TEMA.BANDA))
            Rectangle(pos=(x0, min(y_lsc, y_lic)), size=(w, abs(y_lsc - y_lic)))

            # --- Rejilla horizontal ---
            Color(rgba=rgba(TEMA.REJILLA))
            for valor, _ in ticks_y:
                y = self._py(valor, y0, h)
                Line(points=[x0, y, x0 + w, y], width=dp(0.8))

            # --- Rejilla vertical ---
            if self.ticks_x:
                Color(rgba=rgba(TEMA.REJILLA))
                for valor, _ in self.ticks_x:
                    x = self._px(valor, x0, w)
                    Line(points=[x, y0, x, y0 + h], width=dp(0.8))

            # --- Limites de control (discontinuos) ---
            Color(rgba=rgba(TEMA.LIMITE))
            Line(points=[x0, y_lsc, x0 + w, y_lsc], width=dp(1.6), dash_length=dp(7), dash_offset=dp(4))
            Line(points=[x0, y_lic, x0 + w, y_lic], width=dp(1.6), dash_length=dp(7), dash_offset=dp(4))

            # --- Etiquetas del eje vertical ---
            for valor, texto in ticks_y:
                y = self._py(valor, y0, h)
                self._texto(texto, (self.x, y - dp(8)), (dp(MARGEN_IZQ) - dp(6), dp(16)), TEMA.EJE, sp(10.5), align="right")

            # --- Etiquetas del eje horizontal ---
            for valor, texto in self.ticks_x:
                x = self._px(valor, x0, w)
                self._texto(texto, (x - dp(24), self.y), (dp(48), dp(16)), TEMA.EJE, sp(10.5), align="center")

            # --- Linea base ---
            Color(rgba=rgba(TEMA.REJILLA))
            Line(points=[x0, y0, x0 + w, y0], width=dp(1.1))

            # --- Serie de temperatura ---
            if len(self.xs) >= 2:
                puntos: list[float] = []
                for xv, yv in zip(self.xs, self.ys):
                    puntos.extend([self._px(xv, x0, w), self._py(yv, y0, h)])
                Color(rgba=rgba(TEMA.SERIE))
                Line(points=puntos, width=dp(2.0), joint="round", cap="round")
            elif len(self.xs) == 1:
                Color(rgba=rgba(TEMA.SERIE))
                cx = self._px(self.xs[0], x0, w)
                cy = self._py(self.ys[0], y0, h)
                Ellipse(pos=(cx - dp(3), cy - dp(3)), size=(dp(6), dp(6)))

            # --- Ultimo punto: marcador + globo ---
            if self.xs:
                cx = self._px(self.xs[-1], x0, w)
                cy = self._py(self.ys[-1], y0, h)
                Color(rgba=rgba("#FFFFFF"))
                Ellipse(pos=(cx - dp(5.5), cy - dp(5.5)), size=(dp(11), dp(11)))
                Color(rgba=rgba(TEMA.SERIE))
                Line(circle=(cx, cy, dp(5.5)), width=dp(2.2))
                if self.etiqueta_punto:
                    self._globo(cx, cy, x0, y0, w, h)

    def _globo(self, cx: float, cy: float, x0: float, y0: float, w: float, h: float) -> None:
        """Globo de informacion del ultimo punto (como en la imagen)."""
        ancho = dp(74)
        alto = dp(40)
        # El globo se situa encima del punto, dentro del area.
        gx = min(max(cx - ancho / 2, x0), x0 + w - ancho)
        gy = cy + dp(20)
        if gy + alto > y0 + h:
            gy = cy - dp(20) - alto
        with self.canvas:
            Color(rgba=rgba(TEMA.AZUL))
            RoundedRectangle(pos=(gx, gy), size=(ancho, alto), radius=[dp(8)] * 4)
            # Piquito del globo hacia el punto.
            punta_y = gy - dp(1) if gy > cy else gy + alto - dp(1)
            from kivy.graphics import Mesh

            vertices = [gx + ancho * 0.42, punta_y, gx + ancho * 0.58, punta_y, cx, cy]
            Mesh(vertices=vertices, indices=[0, 1, 2], mode="triangles")
            Color(rgba=rgba(TEMA.AZUL))
            self._texto(self.etiqueta_punto, (gx, gy + alto / 2 + dp(1)), (ancho, dp(15)), "#FFFFFF", sp(11.5), align="center", bold=True)
            self._texto(self.subtitulo_punto, (gx, gy + dp(3)), (ancho, dp(13)), "#D6E6FB", sp(9.5), align="center")

    def _texto(self, texto: str, pos: tuple[float, float], size: tuple[float, float], color: str, tam: float, align: str = "left", bold: bool = False) -> None:
        """Dibuja un texto como textura dentro del canvas."""
        if not texto:
            return
        etiqueta = CoreLabel(text=texto, font_size=tam, color=rgba(color), bold=bold)
        etiqueta.refresh()
        textura = etiqueta.texture
        if textura is None:
            return
        tx, ty = pos
        tw, th = size
        # Centrado vertical dentro del hueco dado.
        y = ty + (th - textura.height) / 2
        if align == "center":
            x = tx + (tw - textura.width) / 2
        elif align == "right":
            x = tx + tw - textura.width
        else:
            x = tx
        Color(rgba=rgba(color))
        Rectangle(texture=textura, pos=(x, y), size=textura.size)
