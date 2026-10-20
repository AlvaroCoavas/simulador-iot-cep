"""Tema oscuro de la interfaz (replica del prototipo del cliente)."""

from __future__ import annotations

# ------------------------------- Paleta -----------------------------------
FONDO = "#1b1b1b"
FONDO_CARD = "#242424"
FONDO_ALT = "#2b2b2b"
BORDE = "#333333"

TEXTO = "#e8e8e8"
TEXTO_SUAVE = "#9d9d9d"
TEXTO_TITULO = "#f2f2f2"

AZUL = "#2196f3"
VERDE = "#4caf50"
AMBAR = "#ffb300"
ROJO = "#e53935"

QSS = f"""
QWidget {{
    background-color: {FONDO};
    color: {TEXTO};
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}}

/* Las etiquetas no deben pintar fondo: se transparentan sobre las tarjetas. */
QLabel {{
    background: transparent;
}}

QCheckBox, QRadioButton {{
    background: transparent;
}}

QFrame#Card {{
    background-color: {FONDO_CARD};
    border: 1px solid {BORDE};
    border-radius: 10px;
}}

QFrame#SubCard {{
    background-color: {FONDO_ALT};
    border: 1px solid {BORDE};
    border-radius: 8px;
}}

QLabel#TituloPanel {{
    color: {TEXTO_TITULO};
    font-size: 16px;
    font-weight: 600;
    letter-spacing: 0.4px;
}}

QLabel#Subtitulo {{
    color: {TEXTO_SUAVE};
    font-size: 12px;
}}

QLabel#ValorGrande {{
    color: {TEXTO};
    font-size: 46px;
    font-weight: 300;
}}

QLabel#EstadoTexto {{
    font-size: 15px;
    font-weight: 600;
}}

QLabel#Etiqueta {{
    color: {TEXTO_SUAVE};
    font-size: 12px;
}}

QLabel#MetricaValor {{
    font-size: 20px;
    font-weight: 600;
}}

QFrame#Banner {{
    border-radius: 8px;
    border: 1px solid transparent;
}}

QPushButton {{
    background-color: {FONDO_ALT};
    border: 1px solid {BORDE};
    border-radius: 6px;
    padding: 8px 14px;
    color: {TEXTO};
}}

QPushButton:hover  {{
    background-color: #353535;
    border-color: #4a4a4a;
}}

QPushButton:pressed {{
    background-color: #2f2f2f;
}}

QPushButton:disabled {{
    color: #5c5c5c;
    background-color: #202020;
}}

QComboBox {{
    background-color: {FONDO_ALT};
    border: 1px solid {BORDE};
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 18px;
}}

QComboBox:hover {{
    border-color: #4a4a4a;
}}

QComboBox::drop-down {{
    border: none;
    width: 18px;
}}

QComboBox QAbstractItemView {{
    background-color: {FONDO_ALT};
    border: 1px solid {BORDE};
    selection-background-color: {AZUL};
    color: {TEXTO};
}}

QDoubleSpinBox, QSpinBox {{
    background-color: {FONDO_ALT};
    border: 1px solid {BORDE};
    border-radius: 5px;
    padding: 4px 6px;
    min-width: 64px;
}}

QDoubleSpinBox:focus, QSpinBox:focus {{
    border-color: {AZUL};
}}

QDoubleSpinBox::up-button, QSpinBox::up-button,
QDoubleSpinBox::down-button, QSpinBox::down-button {{
    background: {FONDO_CARD};
    border: none;
    width: 14px;
}}

QSlider::groove:horizontal {{
    background-color: #3a3a3a;
    height: 5px;
    border-radius: 2px;
}}

QSlider::sub-page:horizontal {{
    background-color: {AZUL};
    height: 5px;
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background-color: {AZUL};
    width: 15px;
    height: 15px;
    margin: -6px 0;
    border-radius: 7px;
}}

QSlider::handle:horizontal:hover {{
    background-color: #42a5f5;
}}

QSlider:disabled::sub-page:horizontal {{
    background-color: #3a3a3a;
}}

QSlider:disabled::handle:horizontal {{
    background-color: #555555;
}}

QScrollArea, QScrollArea > QWidget > QWidget {{
    background: transparent;
    border: none;
}}

QSplitter::handle {{
    background-color: transparent;
}}

QTabWidget::pane {{
    border: 1px solid {BORDE};
    border-radius: 8px;
    background: transparent;
}}

QTabBar::tab {{
    background-color: {FONDO_CARD};
    color: {TEXTO_SUAVE};
    border: 1px solid {BORDE};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 7px 18px;
    margin-right: 3px;
}}

QTabBar::tab:selected {{
    background-color: {FONDO_ALT};
    color: {TEXTO};
}}

QTableWidget {{
    background-color: #1f1f1f;
    alternate-background-color: {FONDO_CARD};
    gridline-color: {BORDE};
    border: 1px solid {BORDE};
    border-radius: 6px;
}}

QTableWidget::item {{
    padding: 4px 8px;
}}

QTableWidget::item:selected {{
    background-color: {AZUL};
    color: #ffffff;
}}

QHeaderView {{
    background-color: {FONDO_ALT};
}}

QHeaderView::section {{
    background-color: {FONDO_ALT};
    color: {TEXTO_SUAVE};
    border: none;
    border-bottom: 1px solid {BORDE};
    padding: 6px 8px;
    font-weight: 600;
}}
"""

# Qt NO aplica las reglas ":disabled" a los sub-controles del slider (::sub-page y
# ::handle): el control se ve identico al habilitado. Por eso el estado
# deshabilitado se fuerza con un estilo inline, que si tiene prioridad sobre la
# hoja global de la aplicacion.
SLIDER_ACTIVO = """
QSlider::groove:horizontal {{
    background-color: #3a3a3a; height: 5px; border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background-color: #3a3a3a; height: 5px; border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background-color: #555555; width: 15px; height: 15px; margin: -6px 0; border-radius: 7px;
}}
"""
