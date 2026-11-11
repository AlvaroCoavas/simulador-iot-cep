"""Historial local de lecturas (SQLite).

Guarda las lecturas que llegan por MQTT para poder dibujar los rangos
"Hoy / 7 dias / 30 dias" incluso con el simulador apagado.

El motor CEP sigue siendo `app/core/cep_engine.py`: aqui solo se archivan
lecturas ya clasificadas, no se recalcula nada.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta

from . import config


class Almacen:
    """Base de datos local de lecturas."""

    def __init__(self, ruta: str | None = None, intervalo_s: int = config.INTERVALO_POR_DEFECTO):
        self.ruta = ruta or config.ruta_base_datos()
        self.intervalo_s = int(intervalo_s)
        self._conexion: sqlite3.Connection | None = None
        self._ultimo_guardado: float | None = None

    # ------------------------------ Ciclo de vida --------------------------
    def abrir(self) -> None:
        """Crea la base si no existe y prepara el esquema."""
        carpeta = os.path.dirname(self.ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        self._conexion = sqlite3.connect(self.ruta)
        self._conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS lecturas (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                ts     REAL NOT NULL,
                t      REAL NOT NULL,
                estado TEXT NOT NULL
            )
            """
        )
        self._conexion.execute("CREATE INDEX IF NOT EXISTS idx_lecturas_ts ON lecturas(ts)")
        self._conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS meta (
                clave TEXT PRIMARY KEY,
                valor REAL
            )
            """
        )
        self._conexion.commit()

    def cerrar(self) -> None:
        if self._conexion is not None:
            self._conexion.close()
            self._conexion = None

    # ------------------------------- Guardado ------------------------------
    def set_intervalo(self, segundos: int) -> None:
        """Cambia cada cuanto se archiva una lectura."""
        self.intervalo_s = max(1, int(segundos))

    def guardar(self, temperatura: float, estado: str, ts: float | None = None) -> bool:
        """Archiva la lectura si ha pasado el intervalo. Devuelve True si se guardo."""
        if self._conexion is None:
            self.abrir()
        momento = float(ts if ts is not None else datetime.now().timestamp())
        if self._ultimo_guardado is not None:
            if momento - self._ultimo_guardado < self.intervalo_s:
                self._guardar_ultima(momento, temperatura, estado)
                return False
        self._conexion.execute(
            "INSERT INTO lecturas (ts, t, estado) VALUES (?, ?, ?)",
            (momento, float(temperatura), str(estado)),
        )
        self._conexion.execute(
            "INSERT OR REPLACE INTO meta (clave, valor) VALUES ('ultima_ts', ?)", (momento,)
        )
        self._conexion.commit()
        self._ultimo_guardado = momento
        return True

    def _guardar_ultima(self, ts: float, temperatura: float, estado: str) -> None:
        """Guarda SIEMPRE la ultima lectura, aunque no se archive en la tabla.

        Asi la carta puede mostrar el punto actual exacto aunque el intervalo
        de muestreo sea largo.
        """
        if self._conexion is None:
            return
        self._conexion.execute(
            "INSERT OR REPLACE INTO meta (clave, valor) VALUES ('ultima_ts', ?)", (ts,)
        )
        self._conexion.execute(
            "INSERT OR REPLACE INTO meta (clave, valor) VALUES ('ultima_t', ?)", (float(temperatura),)
        )
        self._conexion.execute(
            "INSERT OR REPLACE INTO meta (clave, valor) VALUES ('ultima_estado', ?)", (str(estado),)
        )
        self._conexion.commit()

    # ------------------------------- Consultas -----------------------------
    def ultima(self) -> tuple[float, float, str] | None:
        """(ts, temperatura, estado) de la ultima lectura conocida."""
        if self._conexion is None:
            return None
        fila = self._conexion.execute(
            "SELECT valor FROM meta WHERE clave = 'ultima_ts'"
        ).fetchone()
        if fila is None:
            return None
        t = self._conexion.execute("SELECT valor FROM meta WHERE clave = 'ultima_t'").fetchone()
        e = self._conexion.execute("SELECT valor FROM meta WHERE clave = 'ultima_estado'").fetchone()
        if t is None:
            return None
        return float(fila[0]), float(t[0]), str(e[0]) if e else ""

    def _filas(self, desde: float, hasta: float) -> list[tuple[float, float]]:
        if self._conexion is None:
            return []
        return [
            (float(ts), float(t))
            for ts, t in self._conexion.execute(
                "SELECT ts, t FROM lecturas WHERE ts BETWEEN ? AND ? ORDER BY ts",
                (desde, hasta),
            )
        ]

    @staticmethod
    def _reducir(filas: list[tuple[float, float]], max_puntos: int) -> list[tuple[float, float]]:
        """Reduce la serie a `max_puntos` promediando cada tramo."""
        if len(filas) <= max_puntos:
            return filas
        paso = (filas[-1][0] - filas[0][0]) / max_puntos or 1.0
        salida: list[tuple[float, float]] = []
        grupo: list[tuple[float, float]] = []
        referencia = filas[0][0]
        for fila in filas:
            grupo.append(fila)
            if fila[0] - referencia >= paso:
                salida.append((sum(f[0] for f in grupo) / len(grupo), sum(f[1] for f in grupo) / len(grupo)))
                grupo = []
                referencia = fila[0]
        if grupo:
            salida.append((sum(f[0] for f in grupo) / len(grupo), sum(f[1] for f in grupo) / len(grupo)))
        return salida

    def serie_hoy(self, max_puntos: int = config.MAX_PUNTOS_GRAFICA) -> tuple[list[float], list[float]]:
        """Serie de hoy -> (horas_del_dia, temperatura)."""
        ahora = datetime.now()
        medianoche = ahora.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        filas = self._reducir(self._filas(medianoche, ahora.timestamp() + 1), max_puntos)
        xs = [(ts - medianoche) / 3600.0 for ts, _ in filas]
        ys = [t for _, t in filas]
        return xs, ys

    def serie_dias(self, dias: int, max_puntos: int = config.MAX_PUNTOS_GRAFICA) -> tuple[list[float], list[float]]:
        """Serie de los ultimos `dias` dias -> (indice_dia, temperatura).

        El indice 0 es el dia mas antiguo de la ventana y `dias` el mas
        reciente (el de hoy).
        """
        ahora = datetime.now()
        fin = ahora.timestamp()
        inicio = (ahora - timedelta(days=int(dias))).timestamp()
        filas = self._reducir(self._filas(inicio, fin + 1), max_puntos)
        # Dias transcurridos desde el inicio de la ventana.
        xs = [(ts - inicio) / 86400.0 for ts, _ in filas]
        ys = [t for _, t in filas]
        return xs, ys

    # ------------------------------- Mantenimiento -------------------------
    def purgar(self, dias: int = config.DIAS_RETENIDOS) -> int:
        """Borra las lecturas mas antiguas que `dias`. Devuelve cuantas borro."""
        if self._conexion is None:
            return 0
        corte = (datetime.now() - timedelta(days=int(dias))).timestamp()
        cur = self._conexion.execute("DELETE FROM lecturas WHERE ts < ?", (corte,))
        self._conexion.commit()
        return cur.rowcount or 0

    def limpiar(self) -> None:
        """Borra todo el historial (tabla y meta)."""
        if self._conexion is None:
            return
        self._conexion.execute("DELETE FROM lecturas")
        self._conexion.execute("DELETE FROM meta")
        self._conexion.commit()
        self._ultimo_guardado = None

    def total(self) -> int:
        """Numero de lecturas archivadas."""
        if self._conexion is None:
            return 0
        fila = self._conexion.execute("SELECT COUNT(*) FROM lecturas").fetchone()
        return int(fila[0]) if fila else 0
