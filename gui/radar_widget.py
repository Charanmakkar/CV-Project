"""Simulated spatial view, clearly labeled as monocular approximation."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtWidgets import QWidget


class RadarWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.detections: list[Any] = []
        self.setMinimumHeight(190)

    def set_detections(self, detections: list[Any]) -> None:
        self.detections = detections
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#0d1820"))
        w, h = self.width(), self.height()
        cx, cy = w // 2, h - 28
        painter.setPen(QPen(QColor("#375360"), 1))
        for radius in (35, 65, 95):
            painter.drawArc(cx - radius, cy - radius, 2 * radius, 2 * radius, 0, 180 * 16)
        painter.drawLine(cx, cy, 16, cy - 100)
        painter.drawLine(cx, cy, w - 16, cy - 100)
        painter.setBrush(QColor("#e7edf0"))
        painter.drawEllipse(cx - 5, cy - 5, 10, 10)
        painter.setPen(QColor("#d7e5e9"))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.drawText(12, 19, "SIMULATED SPATIAL VIEW  /  MONOCULAR")
        for detection in self.detections:
            x = int(cx + (detection.zone - 2) * (w / 6))
            distance = min(100.0, detection.distance_m or 10.0)
            y = int(cy - max(18, 100 - distance * 10))
            color = QColor("#ff6b6b") if detection.risk_score >= 70 else QColor("#ffd166")
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(x - 6, y - 6, 12, 12)

