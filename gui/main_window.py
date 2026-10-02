"""Professional PySide6 dashboard for the software-only autonomy simulator."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QFrame, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QSlider,
    QSpinBox, QSplitter, QVBoxLayout, QWidget,
)

from src.camera_manager import CameraManager
from src.config import AppConfig
from src.logger import DecisionLogger
from src.pipeline import NavigationPipeline
from src.visualization import FrameVisualizer
from .camera_widget import CameraWidget
from .radar_widget import RadarWidget
from .risk_widget import RiskWidget
from .steering_widget import SteeringWidget
from .wheel_widget import WheelWidget


class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.camera = CameraManager(config.camera)
        self.pipeline = NavigationPipeline(config)
        self.pipeline.initialize()
        self.visualizer = FrameVisualizer()
        self.logger = DecisionLogger(config.logging.directory, config.logging.enabled)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_frame)
        self.last_frame_time = time.perf_counter()
        self.fps = 0.0
        self.patrol_active = False
        self.emergency = False
        self.latest_rendered = None
        self.video_writer = None
        self.setWindowTitle("Computer Vision Autonomous Patrol Simulator")
        self.resize(1500, 940)
        self.setStyleSheet(self._stylesheet())
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        title = QLabel("COMPUTER VISION AUTONOMOUS PATROL SIMULATOR")
        title.setObjectName("title")
        subtitle = QLabel("SOFTWARE-ONLY NAVIGATION DECISION PLATFORM  •  RGB CAMERA  →  RISK  →  STEERING  →  WHEEL SIMULATION")
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        split = QSplitter(Qt.Orientation.Horizontal)
        split.addWidget(self._build_camera_panel())
        split.addWidget(self._build_side_panel())
        split.setSizes([980, 470])
        layout.addWidget(split, 1)
        layout.addWidget(self._build_status_bar())

    def _build_camera_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        self.camera_view = CameraWidget()
        layout.addWidget(self.camera_view, 1)
        controls = QHBoxLayout()
        for text, callback in [("START CAMERA", self.start_camera), ("STOP CAMERA", self.stop_camera), ("START PATROL", self.start_patrol), ("PAUSE", self.pause_patrol), ("EMERGENCY STOP", self.emergency_stop), ("SAVE FRAME", self.capture_screenshot), ("RECORD", self.toggle_recording), ("RESET", self.reset)] :
            button = QPushButton(text)
            button.clicked.connect(callback)
            if text == "RECORD":
                self.record_button = button
            if "EMERGENCY" in text:
                button.setObjectName("danger")
            controls.addWidget(button)
        layout.addLayout(controls)
        toggles = QHBoxLayout()
        self.detect_check = QCheckBox("Detection")
        self.detect_check.setChecked(self.config.detection.enabled)
        self.detect_check.stateChanged.connect(lambda state: setattr(self.config.detection, "enabled", bool(state)))
        self.trajectory_check = QCheckBox("Trajectory")
        self.trajectory_check.setChecked(True)
        self.zones_check = QCheckBox("Zones")
        self.zones_check.setChecked(True)
        self.debug_check = QCheckBox("Debug")
        self.debug_check.setChecked(self.config.ui.show_debug)
        for check in (self.detect_check, self.trajectory_check, self.zones_check, self.debug_check):
            toggles.addWidget(check)
        toggles.addStretch()
        layout.addLayout(toggles)
        return panel

    def _build_side_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        self.object_panel = QLabel("OBJECT INFORMATION\n\nNo detections in current frame.")
        self.object_panel.setObjectName("info")
        self.object_panel.setMinimumHeight(130)
        layout.addWidget(self._group("OBJECT INFORMATION", self.object_panel))
        self.decision_panel = QLabel("DECISION ENGINE\n\nWaiting for camera input.")
        self.decision_panel.setObjectName("info")
        self.decision_panel.setWordWrap(True)
        self.decision_panel.setMinimumHeight(170)
        layout.addWidget(self._group("DECISION ENGINE", self.decision_panel))
        self.radar = RadarWidget()
        layout.addWidget(self.radar)
        self.settings_panel = self._build_settings()
        layout.addWidget(self.settings_panel)
        return panel

    def _build_settings(self) -> QGroupBox:
        group = QGroupBox("LIVE PARAMETERS")
        form = QFormLayout(group)
        self.confidence = QDoubleSpinBox(); self.confidence.setRange(0.05, 0.95); self.confidence.setSingleStep(0.05); self.confidence.setValue(self.config.detection.confidence)
        self.max_angle = QSpinBox(); self.max_angle.setRange(20, 60); self.max_angle.setValue(int(self.config.steering.max_angle))
        self.zone_combo = QComboBox(); self.zone_combo.addItems(["3 zones", "5 zones"]); self.zone_combo.setCurrentIndex(0 if self.config.navigation.zones == 3 else 1)
        self.smoothing = QDoubleSpinBox(); self.smoothing.setRange(0.0, 0.95); self.smoothing.setSingleStep(0.05); self.smoothing.setValue(self.config.steering.smoothing)
        self.confidence.valueChanged.connect(lambda value: setattr(self.config.detection, "confidence", value))
        self.max_angle.valueChanged.connect(lambda value: setattr(self.config.steering, "max_angle", float(value)))
        self.zone_combo.currentIndexChanged.connect(lambda index: setattr(self.config.navigation, "zones", 3 if index == 0 else 5))
        self.smoothing.valueChanged.connect(lambda value: setattr(self.config.steering, "smoothing", value))
        form.addRow("YOLO confidence", self.confidence)
        form.addRow("Max steering", self.max_angle)
        form.addRow("Navigation zones", self.zone_combo)
        form.addRow("Smoothing", self.smoothing)
        return group

    def _build_status_bar(self) -> QWidget:
        bar = QWidget(); layout = QGridLayout(bar); layout.setContentsMargins(0, 0, 0, 0)
        self.steering = SteeringWidget(); self.wheels = WheelWidget(); self.risk = RiskWidget(); self.state_label = QLabel("STATE: INITIALIZING")
        layout.addWidget(self.steering, 0, 0, 2, 1); layout.addWidget(self.wheels, 0, 1, 2, 1); layout.addWidget(self.risk, 0, 2, 2, 1); layout.addWidget(self.state_label, 0, 3)
        self.metrics = QLabel("FPS 0.0  •  CAMERA OFFLINE  •  MODEL NOT LOADED")
        layout.addWidget(self.metrics, 1, 3)
        return bar

    @staticmethod
    def _group(title: str, widget: QWidget) -> QGroupBox:
        group = QGroupBox(title); layout = QVBoxLayout(group); layout.addWidget(widget); return group

    def start_camera(self) -> None:
        if not self.camera.is_open and not self.camera.open():
            self.camera_view.setText(f"CAMERA ERROR\n\n{self.camera.last_error}")
            return
        self.timer.start(self.config.ui.update_ms)

    def stop_camera(self) -> None:
        self.timer.stop(); self.camera.release(); self._stop_recording(); self.metrics.setText("FPS 0.0  •  CAMERA STOPPED")

    def start_patrol(self) -> None:
        self.patrol_active = True; self.emergency = False

    def pause_patrol(self) -> None:
        self.patrol_active = False

    def emergency_stop(self) -> None:
        self.emergency = True; self.patrol_active = False

    def reset(self) -> None:
        self.emergency = False; self.patrol_active = False; self.pipeline.steering.reset(); self.pipeline.state_machine.current = self.pipeline.state_machine.current.SEARCHING

    def capture_screenshot(self) -> None:
        if self.latest_rendered is None:
            return
        import cv2
        from datetime import datetime
        directory = Path("screenshots")
        directory.mkdir(parents=True, exist_ok=True)
        filename = directory / f"patrol_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        cv2.imwrite(str(filename), self.latest_rendered)

    def toggle_recording(self) -> None:
        if self.video_writer is not None:
            self._stop_recording()
            return
        if self.latest_rendered is None:
            return
        import cv2
        from datetime import datetime
        directory = Path("recordings")
        directory.mkdir(parents=True, exist_ok=True)
        height, width = self.latest_rendered.shape[:2]
        filename = directory / f"patrol_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        self.video_writer = cv2.VideoWriter(str(filename), cv2.VideoWriter_fourcc(*"mp4v"), max(1.0, self.config.camera.fps), (width, height))
        if not self.video_writer.isOpened():
            self.video_writer.release(); self.video_writer = None
            return
        self.record_button.setText("STOP REC")

    def _stop_recording(self) -> None:
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
        if hasattr(self, "record_button"):
            self.record_button.setText("RECORD")

    def process_frame(self) -> None:
        ok, frame, _ = self.camera.read()
        if not ok:
            self.stop_camera(); self.camera_view.setText(f"CAMERA ERROR\n\n{self.camera.last_error}"); return
        now = time.perf_counter(); interval = now - self.last_frame_time; self.last_frame_time = now
        self.fps = 1.0 / interval if interval > 0 else 0.0
        analysis = self.pipeline.analyze(frame, self.fps)
        if self.emergency:
            analysis.decision.action = "EMERGENCY STOP"; analysis.decision.angle_deg = 0.0; analysis.wheels = self.pipeline.wheels.command(0.0, "EMERGENCY STOP")
        rendered = self.visualizer.render(analysis, self.pipeline.zones.names, self.zones_check.isChecked(), self.trajectory_check.isChecked(), self.debug_check.isChecked())
        self.latest_rendered = rendered
        if self.video_writer is not None:
            self.video_writer.write(rendered)
        self.camera_view.set_frame(rendered)
        self._update_panels(analysis)
        self.logger.log(analysis.detections, analysis.decision, analysis.wheels)

    def _update_panels(self, analysis: Any) -> None:
        decision = analysis.decision; threat = decision.primary_threat
        self.steering.set_angle(decision.angle_deg); self.wheels.set_values(analysis.wheels.left, analysis.wheels.right, analysis.wheels.motion); self.risk.set_risks(decision.assessment.zone_risks, self.pipeline.zones.names); self.radar.set_detections(analysis.detections)
        self.state_label.setText(f"STATE: {decision.state.value}\nTRANSITION: {self.pipeline.state_machine.transition_text}")
        self.metrics.setText(f"FPS {analysis.fps:.1f}  •  INFERENCE {analysis.inference_ms:.1f} ms  •  {analysis.model_status}  •  PATROL {'ACTIVE' if self.patrol_active else 'PAUSED'}")
        if threat:
            distance = f"{threat.distance_m:.1f} m (estimated)" if threat.distance_m is not None else "unavailable"
            self.object_panel.setText(f"PRIMARY THREAT: {threat.label.upper()} #{threat.track_id or '-'}\nCONFIDENCE: {threat.confidence * 100:.1f}%\nZONE: {self.pipeline.zones.zone_name(threat.zone)}\nDISTANCE: {distance}\nPROXIMITY: {threat.proximity.value}\nRISK: {threat.risk_score:.0f}%\nMOTION: {threat.motion.value}")
        else:
            self.object_panel.setText("OBJECT INFORMATION\n\nNo detections in current frame.")
        self.decision_panel.setText(f"ACTION: {decision.action}\nSTEERING: {decision.angle_deg:+.1f}°\nLEFT PATH RISK: {decision.assessment.left_risk:.0f}%\nRIGHT PATH RISK: {decision.assessment.right_risk:.0f}%\nLEFT WHEEL: {analysis.wheels.left:.1f}%\nRIGHT WHEEL: {analysis.wheels.right:.1f}%\n\nREASON:\n{decision.reason}")

    def closeEvent(self, event) -> None:  # noqa: N802
        self.stop_camera(); self.logger.close(); event.accept()

    @staticmethod
    def _stylesheet() -> str:
        return """
        QWidget { background:#0a131a; color:#d7e5e9; font-family:'Segoe UI'; font-size:10px; }
        #title { color:#eaf4f5; font-size:20px; font-weight:700; padding-top:4px; }
        #subtitle { color:#6ea5ad; font-size:9px; letter-spacing:1px; padding-bottom:4px; }
        QGroupBox { border:1px solid #29434e; border-radius:4px; margin-top:10px; padding-top:10px; color:#7ed7d8; font-weight:700; }
        QGroupBox::title { subcontrol-origin:margin; left:10px; padding:0 5px; }
        #info { color:#c8d9dc; line-height:1.3; }
        QPushButton { background:#17313a; border:1px solid #2d6470; padding:8px 9px; border-radius:3px; color:#dff7f5; font-weight:700; }
        QPushButton:hover { background:#24535c; }
        #danger { background:#702e36; border-color:#c4565c; }
        QCheckBox { color:#9fc0c3; }
        QDoubleSpinBox, QSpinBox, QComboBox { background:#111f27; border:1px solid #2c4b55; padding:3px; }
        """


def run_app(config: AppConfig) -> int:
    app = QApplication.instance() or QApplication([])
    window = MainWindow(config)
    window.show()
    return app.exec()
