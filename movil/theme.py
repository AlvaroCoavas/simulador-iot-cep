"""Paleta de colores y metricas de la app movil.

Los valores salen de la imagen de referencia: fondo azul muy claro, tarjetas
blancas redondeadas, azul de marca, verde de "en rango" y gris suave para los
textos secundarios.
"""

from __future__ import annotations

# ------------------------------- Fondos -------------------------------------
FONDO = "#EAF2FB"
FONDO_ALT = "#DCE9F7"
TARJETA = "#FFFFFF"
TARJETA_BORDE = "#E6EEF7"
SOMBRA = "#C9D8EA"

# -------------------------------- Textos -----------------------------------
TEXTO = "#12283F"
TEXTO_SUAVE = "#6B7C93"
TEXTO_MEDIO = "#3C4E63"

# --------------------------------- Azul ------------------------------------
AZUL = "#1A73E8"
AZUL_OSCURO = "#0B57D0"
AZUL_CLARO = "#E3EEFC"
AZUL_PALIDO = "#F2F7FE"

# --------------------------- Semaforo de estado ----------------------------
VERDE = "#16A34A"
VERDE_CLARO = "#E7F6EC"
AMBAR = "#D97706"
AMBAR_CLARO = "#FDF2E0"
ROJO = "#DC2626"
ROJO_CLARO = "#FDECEC"

# -------------------------------- Grafica ----------------------------------
REJILLA = "#E8EEF5"
BANDA = "#D8F0E2"
LIMITE = "#2FBF71"
SERIE = "#1A73E8"
EJE = "#9AA9BC"

# -------------------------------- Metricas ---------------------------------
RADIO = 22
"""Radio de esquina de las tarjetas (dp)."""

ESPACIO = 16
"""Separacion estandar entre tarjetas (dp)."""

ALTO_BARRA = 62
"""Alto de la barra inferior de navegacion (dp)."""

FUENTE = "Roboto"
"""Familia tipografica de Android (Kivy la resuelve en el dispositivo)."""
