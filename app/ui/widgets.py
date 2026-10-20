"""Widgets reutilizables de la interfaz."""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from .. import theme


class Card(QFrame):
    """Tarjeta redondeada con fondo ligeramente mas claro."""

    def __init__(self, parent: QWidget | None = None, estilo: str = "Card"):
        super().__init__(parent)
        self.setObjectName(estilo)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)


class Led(QWidget):
    """Indicador luminoso (la 'lucecita' del prototipo)."""

    def __init__(self, diameter: int = 22, parent: QWidget | None = None):
        super().__init__(parent)
        self._diameter = diameter
        self._color = QColor(theme.VERDE)
        self.setFixedSize(diameter + 14, diameter + 14)

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()

    def color(self) -> QColor:
        return self._color

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        centro = QPointF(self.width() / 2, self.height() / 2)
        radio = self._diameter / 2

        # Halo: degradado radial del color hacia transparente.
        halo = QColor(self._color)
        halo.setAlpha(110)
        painter.setBrush(QBrush(halo))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(centro, radio + 7, radio + 7)

        # Nucleo.
        painter.setBrush(QBrush(self._color))
        painter.setPen(QPen(QColor(255, 255, 255, 90), 1))
        painter.drawEllipse(centro, radio, radio)
        painter.end()


class Banner(QFrame):
    """Franja de estado a todo el ancho del panel."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Banner")
        self.setFixedHeight(46)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        self.etiqueta = QLabel("")
        self.etiqueta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.etiqueta.setStyleSheet("font-size: 15px; font-weight: 700; color: #ffffff;")
        layout.addWidget(self.etiqueta)

    def set_estado(self, texto: str, color: str) -> None:
        self.etiqueta.setText(texto)
        self.setStyleSheet(
            f"QFrame#Banner {{ background-color: {color}; border: 1px solid {color};"
            f" border-radius: 8px; }}"
        )


# ============================== Iconos ======================================
def icon_pixmap(tipo: str, size: int = 18, color: str = theme.TEXTO_SUAVE) -> QPixmap:
    """Dibuja un icono vectorial simple (evita los emojis rotos del prototipo)."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color))
    pen.setWidthF(max(1.2, size / 12))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    s = size
    if tipo == "chip":  # microcontrolador
        p.drawRoundedRect(QRectF(s * 0.22, s * 0.22, s * 0.56, s * 0.56), 2, 2)
        p.drawRect(QRectF(s * 0.38, s * 0.38, s * 0.24, s * 0.24))
        for i in range(3):
            off = s * (0.34 + i * 0.16)
            p.drawLine(QPointF(off, s * 0.12), QPointF(off, s * 0.22))
            p.drawLine(QPointF(off, s * 0.78), QPointF(off, s * 0.88))
            p.drawLine(QPointF(s * 0.12, off), QPointF(s * 0.22, off))
            p.drawLine(QPointF(s * 0.78, off), QPointF(s * 0.88, off))
    elif tipo == "termo":  # termometro
        p.drawLine(QPointF(s * 0.5, s * 0.18), QPointF(s * 0.5, s * 0.62))
        p.drawEllipse(QRectF(s * 0.34, s * 0.60, s * 0.32, s * 0.32))
        p.setBrush(QBrush(QColor(color)))
        p.drawEllipse(QRectF(s * 0.42, s * 0.40, s * 0.16, s * 0.42))
    elif tipo == "radio":  # ondas de senal
        p.drawLine(QPointF(s * 0.20, s * 0.62), QPointF(s * 0.20, s * 0.38))
        p.drawArc(QRectF(s * 0.28, s * 0.22, s * 0.44, s * 0.56), 300 * 16, 120 * 16)
        p.drawArc(QRectF(s * 0.40, s * 0.30, s * 0.30, s * 0.40), 300 * 16, 120 * 16)
    elif tipo == "panel":  # dashboard
        p.drawRoundedRect(QRectF(s * 0.14, s * 0.20, s * 0.72, s * 0.60), 2, 2)
        p.drawLine(QPointF(s * 0.20, s * 0.62), QPointF(s * 0.40, s * 0.44))
        p.drawLine(QPointF(s * 0.40, s * 0.44), QPointF(s * 0.56, s * 0.56))
        p.drawLine(QPointF(s * 0.56, s * 0.56), QPointF(s * 0.80, s * 0.32))
    elif tipo == "ajustes":  # engranaje simple
        p.drawEllipse(QRectF(s * 0.30, s * 0.30, s * 0.40, s * 0.40))
        for i in range(6):
            import math

            ang = i * math.pi / 3
            p.drawLine(
                QPointF(s * 0.5 + math.cos(ang) * s * 0.24, s * 0.5 + math.sin(ang) * s * 0.24),
                QPointF(s * 0.5 + math.cos(ang) * s * 0.40, s * 0.5 + math.sin(ang) * s * 0.40),
            )
    p.end()
    return pixmap


class Icono(QLabel):
    """Etiqueta con un icono dibujado."""

    def __init__(self, tipo: str, size: int = 18, color: str = theme.TEXTO_SUAVE, parent=None):
        super().__init__(parent)
        self.setPixmap(icon_pixmap(tipo, size, color))
        self.setFixedSize(size, size)


class TituloPanel(QWidget):
    """Cabecera de un panel: icono + texto."""

    def __init__(self, texto: str, icono: str = "panel", parent: QWidget | None = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(9)
        layout.addWidget(Icono(icono, 19, theme.TEXTO_TITULO))
        etiqueta = QLabel(texto)
        etiqueta.setObjectName("TituloPanel")
        layout.addWidget(etiqueta)
        layout.addStretch(1)


def tarjeta(titulo: str | None = None, icono: str = "panel") -> tuple[QFrame, QVBoxLayout]:
    """Crea una tarjeta con su layout vertical. Devuelve (tarjeta, layout)."""
    card = Card()
    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 14, 16, 16)
    layout.setSpacing(10)
    if titulo:
        layout.addWidget(TituloPanel(titulo, icono))
    return card, layout
