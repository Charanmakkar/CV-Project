"""Create a deterministic synthetic video for testing the video-file mode.

The graphics are intentionally simple and do not replace real YOLO detections;
they are useful for validating camera playback, overlays, recording, and GUI
timing without a webcam.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


WIDTH, HEIGHT, FPS = 960, 540, 30
OUTPUT = Path(__file__).resolve().parents[1] / "recordings" / "sample_patrol.mp4"


def road_background(frame_index: int) -> np.ndarray:
    frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    frame[:300] = (48, 74, 92)
    frame[300:] = (34, 38, 40)
    # Horizon and road perspective.
    cv2.line(frame, (0, 300), (WIDTH, 300), (120, 145, 150), 2)
    cv2.fillPoly(frame, [np.array([(330, 300), (630, 300), (900, HEIGHT), (60, HEIGHT)], np.int32)], (43, 47, 48))
    for offset in range(-1, 3):
        x = int(WIDTH / 2 + offset * 175)
        cv2.line(frame, (WIDTH // 2, 315), (x, HEIGHT), (75, 80, 80), 2)
    dash_offset = (frame_index * 9) % 75
    for y in range(330 + dash_offset, HEIGHT, 75):
        cv2.line(frame, (WIDTH // 2 - 5, y), (WIDTH // 2 + 5, y), (210, 210, 190), 3)
    return frame


def draw_vehicle(frame: np.ndarray, center_x: int, bottom_y: int, scale: float, color: tuple[int, int, int], label: str) -> None:
    width = max(18, int(110 * scale))
    height = max(22, int(110 * scale))
    x1, y1 = center_x - width // 2, bottom_y - height
    x2, y2 = center_x + width // 2, bottom_y
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, -1)
    cv2.rectangle(frame, (x1 + width // 8, y1 + height // 6), (x2 - width // 8, y1 + height // 2), (160, 200, 215), -1)
    cv2.rectangle(frame, (x1 + width // 10, y2 - height // 5), (x1 + width // 4, y2 + 3), (15, 18, 20), -1)
    cv2.rectangle(frame, (x2 - width // 4, y2 - height // 5), (x2 - width // 10, y2 + 3), (15, 18, 20), -1)
    cv2.putText(frame, label, (x1, max(22, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (245, 245, 245), 1, cv2.LINE_AA)


def draw_person(frame: np.ndarray, center_x: int, bottom_y: int, scale: float) -> None:
    radius = max(8, int(15 * scale))
    body = max(20, int(55 * scale))
    cv2.circle(frame, (center_x, bottom_y - body - radius), radius, (50, 175, 235), -1)
    cv2.rectangle(frame, (center_x - radius, bottom_y - body), (center_x + radius, bottom_y), (50, 115, 220), -1)
    cv2.putText(frame, "PERSON", (center_x - 35, max(22, bottom_y - body - radius * 2)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (245, 245, 245), 1, cv2.LINE_AA)


def make_video() -> Path:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(OUTPUT), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (WIDTH, HEIGHT))
    if not writer.isOpened():
        raise RuntimeError("Could not create MP4 writer. Install opencv-python with video codec support.")
    total_frames = FPS * 24
    for index in range(total_frames):
        frame = road_background(index)
        seconds = index / FPS
        # 0-4: clear path; 4-9: approaching center vehicle; 9-14: left obstacle;
        # 14-19: right obstacle; 19-24: both sides occupied.
        if 4 <= seconds < 9:
            progress = (seconds - 4) / 5
            draw_vehicle(frame, WIDTH // 2, int(370 + progress * 135), 0.38 + progress * 0.9, (45, 85, 205), "CAR - APPROACHING")
        elif 9 <= seconds < 14:
            progress = (seconds - 9) / 5
            draw_vehicle(frame, int(260 + progress * 80), 420, 0.85, (50, 150, 70), "TRUCK - LEFT")
            draw_person(frame, 700, 405, 1.4)
        elif 14 <= seconds < 19:
            progress = (seconds - 14) / 5
            draw_vehicle(frame, int(700 - progress * 70), 425, 0.9, (190, 90, 40), "CAR - RIGHT")
        elif seconds >= 19:
            draw_vehicle(frame, 270, 430, 0.95, (50, 150, 70), "TRUCK")
            draw_vehicle(frame, 690, 430, 0.95, (190, 90, 40), "CAR")
            draw_vehicle(frame, WIDTH // 2, 500, 1.15, (45, 85, 205), "BLOCKED PATH")
        cv2.rectangle(frame, (18, 18), (410, 65), (10, 18, 24), -1)
        cv2.putText(frame, "SYNTHETIC PATROL TEST VIDEO", (30, 47), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (105, 225, 210), 2, cv2.LINE_AA)
        writer.write(frame)
    writer.release()
    return OUTPUT


if __name__ == "__main__":
    print(make_video())

