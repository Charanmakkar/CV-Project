"""Differential-drive wheel bar visualization."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtWidgets import QWidget


class WheelWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.left = 0.0
        self.right = 0.0
        self.motion = "STOP"
        self.setMinimumHeight(142)

    def set_values(self, left: float, right: float, motion: str) -> None:
        self.left, self.right, self.motion = left, right, motion
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#0d1820"))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.setPen(QColor("#d7e5e9"))
        painter.drawText(12, 22, "LEFT WHEEL")
        painter.drawText(self.width() // 2 + 12, 22, "RIGHT WHEEL")
        for x, value, color in [(12, self.left, QColor("#4ddf95")), (self.width() // 2 + 12, self.right, QColor("#56b7ff"))]:
            bar_width = self.width() // 2 - 28
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#23343c"))
            painter.drawRoundedRect(x, 37, bar_width, 20, 5, 5)
            painter.setBrush(color if value >= 0 else QColor("#ff7070"))
            painter.drawRoundedRect(x, 37, int(bar_width * min(1.0, abs(value) / 100.0)), 20, 5, 5)
            painter.setPen(QColor("#d7e5e9"))
            painter.drawText(x, 78, f"{value:+.1f}%")
        painter.setPen(QColor("#ffd166"))
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        painter.drawText(12, 112, f"VEHICLE MOTION: {self.motion}")

