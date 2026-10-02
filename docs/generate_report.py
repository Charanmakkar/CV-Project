"""Generate the engineering report requested by the project prompt."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "Computer_Vision_Object_Detection_Patrol_System.docx"


DIAGRAMS = {
    "System architecture": "CAMERA\n  ↓\nFRAME CAPTURE → YOLO DETECTION → IOU TRACKING\n  ↓                         ↓\nZONES + DISTANCE → RISK / OCCUPANCY → DECISION\n                                      ↓\n                         STEERING → WHEELS → GUI / LOG",
    "Data flow": "Webcam or video → frame → detections → tracks → zones → distance/proximity\n→ risk score → corridor occupancy → navigation state → angle → wheel command → overlay",
    "State machine": "INITIALIZING → SEARCHING → PATH_CLEAR ↔ FOLLOWING_PATH\n                         ↓\n                OBSTACLE_DETECTED → ANALYZING_OBSTACLE\n                    ↙          ↓          ↘\n              TURN_LEFT  SLOW_DOWN  TURN_RIGHT\n                         ↓\n                 STOPPED / EMERGENCY_STOP",
    "Decision tree": "OBJECTS? ── no ──> STRAIGHT\n   │ yes\nPRIMARY THREAT → CENTER BLOCKED? → compare LEFT RISK / RIGHT RISK\n                                      ├─ both high → STOP\n                                      ├─ left lower → TURN LEFT\n                                      └─ right lower → TURN RIGHT",
    "Five-zone camera": "| FAR LEFT | LEFT | CENTER | RIGHT | FAR RIGHT |\n      0–20%     20–40%  40–60%  60–80%     80–100%",
    "Collision corridor": "          camera frame\n       ┌────────────────┐\n       │                │\n       │   ┌────────┐   │  projected corridor\n       │  /          \\  │\n       │ /            \\ │\n       └────────────────┘",
    "Steering logic": "risk ↑ + proximity ↑ + corridor occupancy ↑\n                         ↓\n          continuous steering angle [-60°, +60°]\n             negative LEFT | 0 STRAIGHT | positive RIGHT",
    "Software modules": "camera_manager / object_detector / object_tracker / distance_estimator\nzone_analyzer / occupancy_analyzer / risk_engine / decision_engine\nsteering_controller / wheel_controller / trajectory_generator / state_machine\nvisualization / logger / gui",
    "GUI layout": "+---------------------------+------------------+\n| annotated live camera     | threat + decision |\n+---------------------------+------------------+\n| steering | wheels | risk map | radar | metrics |",
}


SECTIONS = [
    ("1. Executive Summary", "This project is a software-only computer vision navigation decision simulator. It demonstrates how live RGB video can be transformed into object detections, relative proximity, scene risk, explainable obstacle avoidance, steering, and differential-drive wheel commands."),
    ("2. Project Objectives", "Provide a professional educational dashboard with live perception overlays, configurable navigation zones, multi-object risk reasoning, stable commands, state-machine visibility, trajectory prediction, simulated wheel output, and engineering telemetry."),
    ("3. Scope", "In scope are webcam/video capture, optional Ultralytics YOLO inference, dependency-free tracking, monocular distance heuristics, navigation and visualization. Physical actuation, safety certification, metric-grade depth, SLAM, and production autonomy are out of scope."),
    ("4. Hardware Requirements", "A standard USB/web camera and a Windows or Linux PC/laptop. No motors, motor driver, microcontroller, Raspberry Pi, LiDAR, radar, ultrasonic sensor, or robot chassis is required."),
    ("5. Software Requirements", "Python 3.11 or 3.12 is recommended. Dependencies are listed in requirements.txt: NumPy, OpenCV, PySide6, PyYAML, Ultralytics, python-docx, and pytest."),
    ("6. System Architecture", "The application is organized into camera, perception, navigation, control simulation, visualization, GUI, and logging layers. Interfaces use typed dataclasses so perception can be replaced without rewriting decision logic."),
    ("7. Computer Vision Pipeline", "Frames are captured, passed to YOLO when enabled, converted to Detection records, assigned persistent IDs, annotated with zones and corridor membership, scored for risk, and passed to the decision engine."),
    ("8. Object Detection", "ObjectDetector wraps Ultralytics and filters configurable classes including person, bicycle, car, motorcycle, bus, truck, and chair. Model loading failures are visible in the GUI and do not crash the application."),
    ("9. Object Tracking", "ObjectTracker uses class-aware intersection-over-union matching. Track histories estimate whether a bounding box is approaching, moving away, or stationary. Missing tracks expire after a configurable persistence window."),
    ("10. Navigation Zones", "ZoneAnalyzer supports three or five horizontal zones. Five zones are the default: FAR LEFT, LEFT, CENTER, RIGHT, FAR RIGHT. Zone boundaries and labels are drawn on the camera overlay."),
    ("11. Distance Estimation", "DistanceEstimator uses focal-length and approximate object-height priors. It is intentionally labeled estimated and translated to SAFE, CAUTION, NEAR, or CRITICAL bands. It is not a calibrated safety measurement."),
    ("12. Collision Corridor", "A trapezoidal projected corridor occupies the lower/central image. Objects in the corridor receive additional risk because they are more likely to intersect the hypothetical vehicle path."),
    ("13. Risk Calculation", "Risk combines proximity, bounding-box size, lower-frame position, corridor membership, class weight, confidence, and approach rate. The result is capped at 100 and is aggregated by zone."),
    ("14. Obstacle Avoidance Algorithm", "The highest-risk detection is selected as the primary threat, but side selection uses cumulative left/right occupancy. A center threat turns toward the lower-risk side. If neither side is below the stop threshold, the command is STOP or EMERGENCY STOP."),
    ("15. Steering Angle Calculation", "Angle magnitude scales continuously with threat risk and is capped by the configured maximum. Negative is left, zero is straight, and positive is right. SteeringController applies exponential smoothing and command-duration hysteresis."),
    ("16. Differential Drive Simulation", "WheelController slows the inside wheel and slightly increases the outside wheel. Straight motion uses equal positive speeds. STOP and EMERGENCY STOP set both simulated wheel commands to zero."),
    ("17. Navigation State Machine", "NavigationStateMachine records INITIALIZING, SEARCHING, PATH_CLEAR, FOLLOWING_PATH, OBSTACLE_DETECTED, ANALYZING_OBSTACLE, TURN_LEFT, TURN_RIGHT, SLOW_DOWN, STOPPED, and EMERGENCY_STOP transitions."),
    ("18. GUI Architecture", "PySide6 renders a camera panel, object information, decision explanation, simulated radar, steering gauge, wheel bars, zone risk map, status metrics, and live tunables. OpenCV remains responsible for image overlays."),
    ("19. Data Flow", "The complete flow is Camera → Detection → Tracking → Zones → Distance → Risk → Occupancy → Decision → Steering → Wheels → Trajectory → GUI/CSV."),
    ("20. Class / Module Architecture", "Core modules are small and independently testable. The GUI consumes FrameAnalysis, a typed aggregate containing frame, detections, decision, wheel command, FPS, inference time, model status, and timestamp."),
    ("21. Configuration Parameters", "config.yaml controls camera source, model, confidence, IOU, zone count, corridor geometry, distance thresholds, risk thresholds, max steering, smoothing, tracking persistence, logging, and UI rate."),
    ("22. Logging", "DecisionLogger appends one CSV row per detection with timestamp, object identity, class, confidence, bounding box, zone, estimated distance, risk, state, angle, wheel values, and action."),
    ("23. Test Procedure", "Run pytest -q for headless deterministic tests. Then run python main.py --no-model to validate the GUI and camera handling. Finally test webcam/video inference with model status visible in the bottom metrics bar."),
    ("24. Test Cases", "The automated suite covers an empty scene, center threat with a safer left route, fully blocked corridors, exact zone boundaries, differential-drive sign convention, and steering clamping. Manual cases cover far/near left/right objects, center blockage, multiple objects, approaching objects, and camera/video errors."),
    ("25. Results", "The navigation core is deterministic and testable without hardware. The runtime uses graceful fallbacks when optional camera, YOLO, GPU, or GUI dependencies are absent. Runtime FPS and inference time are displayed when the application is installed and launched."),
    ("26. Screenshots", "The live dashboard is designed to be captured using the operating system screenshot tool. The dashboard itself displays the annotated frame, threat explanation, steering, wheels, risk map, radar, and metrics on one screen."),
    ("27. Limitations", "A monocular RGB camera cannot reliably recover safety-grade distance. Unknown object dimensions, perspective, occlusion, lighting, camera motion, model mistakes, and lack of calibration affect the estimates. This software must not control a real vehicle."),
    ("28. Future Improvements", "Potential extensions include calibration, depth/stereo sensing, LiDAR/radar/ultrasonic fusion, ByteTrack/BoT-SORT, learned free-space segmentation, ROS 2/Nav2 integration, SLAM, scenario playback, and formal safety validation."),
    ("29. Conclusion", "The project demonstrates the requested camera-to-decision-to-wheel-simulation chain with modular engineering structure, explainable decisions, and visible state. It is suitable for academic demonstration and experimentation, not production autonomy."),
]


def add_code_block(document: Document, text: str) -> None:
    paragraph = document.add_paragraph()
    paragraph.style = document.styles["No Spacing"]
    run = paragraph.add_run(text)
    run.font.name = "Consolas"
    run.font.size = Pt(8)


def build_report() -> Path:
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    title = document.add_heading("Computer Vision Object Detection Patrol System", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle = document.add_paragraph("Engineering Design and Implementation Report")
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    document.add_paragraph("Software-only navigation decision simulator • Generated from the project source tree")
    document.add_page_break()
    document.add_heading("Table of Contents", 1)
    for heading, _ in SECTIONS:
        document.add_paragraph(heading)
    document.add_page_break()
    for heading, body in SECTIONS:
        document.add_heading(heading, 1)
        document.add_paragraph(body)
        diagram = next((value for key, value in DIAGRAMS.items() if key.lower() == heading[3:].lower()), None)
        if diagram:
            add_code_block(document, diagram)
    document.add_heading("Appendix A — Project Tree", 1)
    add_code_block(document, "main.py\nconfig.yaml\nrequirements.txt\nsrc/\n  camera_manager.py ... logger.py\ngui/\n  main_window.py, camera_widget.py, steering_widget.py\ntests/test_navigation.py\ndocs/generate_report.py")
    document.add_heading("Appendix B — Safety Notice", 1)
    document.add_paragraph("This prototype produces simulated commands only. Do not connect its output to motors or use it as an autonomous-driving controller. Estimated distance is not a physical measurement.")
    document.save(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    print(build_report())
