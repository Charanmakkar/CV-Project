# CV-Project

# Computer Vision Autonomous Patrol Simulator

A software-only computer-vision navigation demonstrator. A USB/web camera or prerecorded video is processed by an optional Ultralytics YOLO model, then converted into explainable obstacle-risk, navigation, steering, and differential-drive wheel commands. It is a research/education simulator; it does not control real motors and is not a safety-certified autonomous-driving system.

## Highlights

- PySide6 ADAS-style single-screen dashboard.
- Webcam and repeatable video-file modes.
- YOLO11/Ultralytics adapter with CPU fallback and graceful no-model mode.
- Configurable 3-zone or 5-zone navigation (5 by default).
- Monocular estimated distance plus relative proximity bands: SAFE, CAUTION, NEAR, CRITICAL.
- Multi-object risk model using proximity, size, corridor occupancy, vertical position, confidence, type, and approach rate.
- Center-obstacle side selection using cumulative left/right corridor risk; STOP/EMERGENCY STOP when neither side is safe.
- Dependency-free IoU tracker with stable IDs and approaching/moving-away classification.
- Smoothed steering angle from -60° (left) to +60° (right), wheel-speed simulation, predicted trajectory, radar view, risk map, CSV logging, screenshots-ready display.
- All tunable parameters in `config.yaml`.

## Installation (Windows)

Python 3.11 or 3.12 is recommended for the broadest compatibility; Python 3.13 may work depending on the installed wheel versions.

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

The first YOLO run may download the configured lightweight model (`yolo11n.pt`). For a dashboard smoke test without a model:

```powershell
python main.py --no-model
```

For repeatable testing with a video:

```powershell
python main.py --video path\to\test_video.mp4
```

## Dashboard controls

`START CAMERA` opens the webcam/video source. `START PATROL` marks the software patrol mode active; `PAUSE` leaves perception visible while pausing patrol intent. `EMERGENCY STOP` forces simulated wheel speeds to zero. Detection, trajectory, zone, and debug overlays can be toggled live. Confidence, maximum steering angle, zone count, and smoothing can be changed from the right panel.

The dashboard intentionally labels distance as estimated. A single RGB camera cannot provide reliable metric depth without calibration, scene assumptions, or an additional depth sensor.

## Architecture

```text
CameraManager → ObjectDetector → ObjectTracker → ZoneAnalyzer
                                      ↓
DistanceEstimator → RiskEngine → OccupancyAnalyzer
                                      ↓
DecisionEngine → SteeringController → WheelController
                                      ↓
                     Trajectory + Visualization + GUI + CSV logger
```

The GUI is in `gui/`; reusable perception and navigation logic is in `src/`. The test suite exercises the decision path without a camera, GPU, OpenCV, or YOLO model.

## Navigation logic

Each detection receives a zone and a risk score. Risk combines proximity, normalized bounding-box size, lower-frame occupancy, collision-corridor membership, confidence, object type, and approach rate. The occupancy analyzer combines zone risks into left/right corridor risk using a noisy-OR aggregation. A center obstacle therefore does not cause an arbitrary turn: the engine selects the lower-risk corridor or stops if both are unsafe.

Steering convention:

- negative angle = left;
- zero = straight;
- positive angle = right.

Wheel simulation slows the inside wheel and slightly increases the outside wheel. STOP and EMERGENCY STOP set both wheels to zero.

## Configuration

`config.yaml` controls camera resolution/source, model/confidence, zone geometry, estimated-distance thresholds, risk thresholds, steering sensitivity/smoothing, tracking persistence, logging, and UI update rate. No hardware actuator configuration exists because the project is deliberately software-only.

## Logging and artifacts

CSV telemetry is written to `logs/navigation_events.csv` when logging is enabled. The default project directories are `logs/`, `recordings/`, and `screenshots/`. The report generator creates `Computer_Vision_Object_Detection_Patrol_System.docx`.

```powershell
python docs\generate_report.py
```

## Testing

```powershell
pytest -q
```

The tests cover no-object straight motion, center-obstacle side selection, blocked corridors, zone boundaries, wheel sign convention, and steering clamping. Manual scenarios to try include a clear scene, far/near objects on each side, a center object, multiple side objects, a fully blocked scene, and an approaching object.

## Troubleshooting

- **Camera unavailable:** check Windows camera privacy permissions, close other camera applications, and try `camera.index: 1` in `config.yaml`.
- **Model unavailable:** run with `--no-model` to validate the GUI, or check that `ultralytics` is installed and the machine can download the configured weights.
- **Low FPS:** reduce `camera.width/height`, `detection.image_size`, or use a smaller model; YOLO inference is the dominant cost.
- **No detections:** lower `detection.confidence`, confirm the configured class names, and check the model status in the bottom metrics bar.
- **Video ends:** the application stops capture gracefully and reports the last camera error.

## Limitations and future work

The monocular distance estimate is a visual heuristic, not a measured distance. Occlusion, camera tilt, object pose, lens distortion, lighting, and unknown object dimensions can make it inaccurate. Future versions could add calibration, stereo/depth cameras, LiDAR/radar/ultrasonic input, ROS 2/Nav2 integration, a stronger tracker, recording controls, and a calibrated vehicle model. Never connect this prototype directly to a real vehicle.

