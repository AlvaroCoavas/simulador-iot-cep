"""Grafico de Control Individual (X) embebido con matplotlib."""

from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.collections import LineCollection
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from .. import theme


class ChartControl(FigureCanvas):
    """Carta de control individuals: LSC / LIC / objetivo + serie de temperatura."""

    def __init__(self, parent=None):
        self.figura = Figure(figsize=(8.0, 4.4), dpi=100)
        self.figura.patch.set_facecolor(theme.FONDO_CARD)
        super().__init__(self.figura)
        self.ax = self.figura.add_subplot(111)
        self.setStyleSheet(f"background-color: {theme.FONDO_CARD}; border-radius: 10px;")
        self._dinamicos: list = []
        self._configurar_ejes()

    # ------------------------------ Configuracion -------------------------
    def _configurar_ejes(self) -> None:
        ax = self.ax
        ax.set_facecolor(theme.FONDO_CARD)
        ax.set_title(
            "Gráfico de Control Individual (X)",
            color=theme.TEXTO,
            fontsize=11,
            fontweight="bold",
            pad=12,
        )
        ax.set_xlabel("Número de muestra", color=theme.TEXTO_SUAVE, fontsize=9)
        ax.set_ylabel("Temperatura (°C)", color=theme.TEXTO_SUAVE, fontsize=9)
        ax.tick_params(colors=theme.TEXTO_SUAVE, labelsize=9)
        for lado in ax.spines.values():
            lado.set_color(theme.BORDE)
        ax.grid(True, linestyle=":", linewidth=0.7, color="#3c3c3c", alpha=0.9)
        ax.set_axisbelow(True)

    def _limpiar(self) -> None:
        for artista in self._dinamicos:
            try:
                artista.remove()
            except (ValueError, NotImplementedError):
                pass
        self._dinamicos = []

    # ------------------------------ Actualizacion -------------------------
    def actualizar(self, x, y, fuera, lsc: float, lic: float, objetivo: float) -> None:
        """Redibuja la carta con la serie actual y los limites vigentes."""
        self._limpiar()
        ax = self.ax

        # --- Limites de control ---
        linea_lsc = ax.axhline(lsc, color=theme.ROJO, linestyle="--", linewidth=1.4, zorder=2)
        linea_lic = ax.axhline(lic, color=theme.ROJO, linestyle="--", linewidth=1.4, zorder=2)
        linea_obj = ax.axhline(objetivo, color=theme.AZUL, linewidth=1.5, zorder=2)
        self._dinamicos += [linea_lsc, linea_lic, linea_obj]

        # --- Serie de temperatura ---
        if len(x) >= 2:
            puntos = list(zip(x, y))
            segmentos = [[puntos[i], puntos[i + 1]] for i in range(len(puntos) - 1)]
            colores = [
                theme.ROJO if (fuera[i] or fuera[i + 1]) else theme.VERDE
                for i in range(len(segmentos))
            ]
            coleccion = LineCollection(
                segmentos, colors=colores, linewidths=1.7, zorder=3
            )
            ax.add_collection(coleccion)
            self._dinamicos.append(coleccion)

        if x:
            colores_puntos = [theme.ROJO if f else theme.VERDE for f in fuera]
            marcadores = ax.scatter(
                x, y, s=26, c=colores_puntos, zorder=4, edgecolors="#111111", linewidths=0.6
            )
            self._dinamicos.append(marcadores)

        # --- Leyenda (replica del prototipo del cliente) ---
        # Cada entrada usa el color de su linea. El marco va oscuro y
        # semitransparente con borde sutil, y el texto en gris claro.
        manejadores = [
            Line2D([], [], color=theme.ROJO, linestyle="--", linewidth=1.6,
                   label=f"LSC ({lsc:.1f}°C)"),
            Line2D([], [], color=theme.AZUL, linewidth=1.8, label="Objetivo"),
            Line2D([], [], color=theme.ROJO, linestyle="--", linewidth=1.6,
                   label=f"LIC ({lic:.1f}°C)"),
            Line2D([], [], color=theme.VERDE, linewidth=2.0, marker="o",
                   markersize=6, markeredgecolor="#111111", label="Temp. Actual"),
        ]
        leyenda = ax.legend(
            handles=manejadores,
            loc="upper left",
            fontsize=10,          # minimo 10 pt
            frameon=True,
            facecolor=theme.FONDO_ALT,
            edgecolor=theme.BORDE,
            framealpha=0.88,      # fondo oscuro semitransparente
            labelcolor=theme.TEXTO,
            borderpad=0.6,
            labelspacing=0.5,
            handlelength=2.2,
            handletextpad=0.8,
        )
        leyenda.get_frame().set_linewidth(0.8)
        self._dinamicos.append(leyenda)

        # --- Escala de los ejes ---
        if x:
            ax.set_xlim(min(x) - 1, max(x) + 1)
        valores = list(y) + [lsc, lic]
        if valores:
            ax.set_ylim(min(valores) - 1.0, max(valores) + 1.0)

        self.draw_idle()
