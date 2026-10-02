"""Five-zone occupancy risk map."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtWidgets import QWidget


class RiskWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.risks = [0.0] * 5
        self.names = ["FAR\nLEFT", "LEFT", "CENTER", "RIGHT", "FAR\nRIGHT"]
        self.setMinimumHeight(142)

    def set_risks(self, risks: list[float], names: list[str]) -> None:
        self.risks = risks
        self.names = [name.replace(" ", "\n") for name in names]
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#0d1820"))
        painter.setPen(QColor("#d7e5e9"))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.drawText(12, 21, "ZONE RISK MAP  /  CUMULATIVE OCCUPANCY")
        count = len(self.risks)
        width = max(1, (self.width() - 24) // count)
        for index, risk in enumerate(self.risks):
            x = 12 + index * width
            color = QColor("#4ddf95") if risk < 35 else QColor("#ffd166") if risk < 70 else QColor("#ff6b6b")
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(x, 39, width - 5, 48, 4, 4)
            painter.setPen(QColor("#081018"))
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            painter.drawText(x + 5, 58, self.names[index])
            painter.drawText(x + 5, 80, f"{risk:.0f}%")

