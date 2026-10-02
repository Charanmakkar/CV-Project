"""Steering angle gauge."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QColor, QFont
from PySide6.QtWidgets import QWidget


class SteeringWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.angle = 0.0
        self.setMinimumHeight(135)
        self.setMinimumWidth(245)

    def set_angle(self, angle: float) -> None:
        self.angle = angle
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#0d1820"))
        center = self.rect().center()
        center.setY(center.y() + 22)
        radius = min(self.width() // 2 - 20, 76)
        painter.setPen(QPen(QColor("#41606c"), 2))
        painter.drawArc(center.x() - radius, center.y() - radius, 2 * radius, 2 * radius, 30 * 16, 120 * 16)
        painter.setPen(QPen(QColor("#91a7b0"), 1))
        painter.drawLine(center.x() - radius, center.y(), center.x() + radius, center.y())
        painter.setPen(QPen(QColor("#e3edf0"), 2))
        painter.drawLine(center.x(), center.y() - radius, center.x(), center.y() + 4)
        needle_x = center.x() + int(radius * 0.80 * self.angle / 60.0)
        painter.setPen(QPen(QColor("#ffd166"), 4))
        painter.drawLine(center.x(), center.y(), needle_x, center.y() - radius + 14)
        painter.setPen(QColor("#e8f0f2"))
        painter.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        painter.drawText(10, 22, f"STEERING  {self.angle:+.1f}°")
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(12, self.height() - 10, "-60° LEFT                 0°                 +60° RIGHT")

