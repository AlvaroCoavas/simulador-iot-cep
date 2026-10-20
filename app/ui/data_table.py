"""Tabla de muestras del proceso (solo lectura)."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from ..core.cep_engine import Muestra

#: Numero maximo de lecturas visibles (la mas reciente arriba).
MAX_FILAS = 200


class TablaMuestras(QTableWidget):
    """Tabla de solo lectura con las ultimas lecturas del proceso.

    El estado y la marca de fuera de limite los calcula el motor CEP: esta
    tabla solo los muestra, sin duplicar ninguna regla.
    """

    COLUMNAS = ("Hora", "Temperatura (°C)", "Estado", "Fuera de límite")

    def __init__(self, parent: QWidget | None = None):
        super().__init__(0, len(self.COLUMNAS), parent)
        self.setHorizontalHeaderLabels(list(self.COLUMNAS))
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setShowGrid(True)
        self.setWordWrap(False)

        cabecera = self.verticalHeader()
        cabecera.setVisible(False)
        cabecera.setDefaultSectionSize(26)

        horizontal = self.horizontalHeader()
        horizontal.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        horizontal.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

    # ------------------------------ Actualizacion -------------------------
    def agregar(self, muestra: Muestra) -> None:
        """Inserta una lectura en la primera fila (la mas reciente arriba)."""
        self.insertRow(0)
        valores = (
            muestra.hora,
            f"{muestra.temperatura:.2f}",
            muestra.estado.value,
            "Sí" if muestra.fuera_de_limite else "No",
        )
        for columna, texto in enumerate(valores):
            item = QTableWidgetItem(texto)
            item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            if columna == 1:
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
            if columna == 2:
                item.setForeground(QColor(muestra.estado.color))
            if columna == 3 and muestra.fuera_de_limite:
                item.setForeground(QColor("#e53935"))
            self.setItem(0, columna, item)

        if self.rowCount() > MAX_FILAS:
            self.removeRow(self.rowCount() - 1)

    def limpiar(self) -> None:
        """Vacia la tabla."""
        self.setRowCount(0)
