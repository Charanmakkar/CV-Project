"""Small dependency-free IoU tracker for stable IDs and approach-rate estimates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import Detection, MotionStatus


def _iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix1, iy1 = max(ax, bx), max(ay, by)
    ix2, iy2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    union = aw * ah + bw * bh - inter
    return inter / union if union else 0.0


@dataclass
class _Track:
    track_id: int
    label: str
    bbox: tuple[int, int, int, int]
    areas: list[float] = field(default_factory=list)
    missing: int = 0


class ObjectTracker:
    def __init__(self, config: Any) -> None:
        self.config = config
        self.tracks: dict[int, _Track] = {}
        self.next_id = 1

    def update(self, detections: list[Detection]) -> list[Detection]:
        unmatched = set(range(len(detections)))
        matched_ids: set[int] = set()
        for track_id, track in list(self.tracks.items()):
            best_index, best_score = None, 0.0
            for index in unmatched:
                detection = detections[index]
                if detection.label != track.label:
                    continue
                score = _iou(track.bbox, detection.bbox)
                if score > best_score:
                    best_index, best_score = index, score
            if best_index is not None and best_score >= self.config.match_iou:
                detection = detections[best_index]
                unmatched.remove(best_index)
                matched_ids.add(track_id)
                track.bbox = detection.bbox
                track.areas.append(detection.area_ratio)
                track.areas = track.areas[-self.config.approach_window :]
                track.missing = 0
                detection.track_id = track_id
                detection.motion = self._motion(track)
            else:
                track.missing += 1
                if track.missing > self.config.max_missing_frames:
                    del self.tracks[track_id]
        for index in unmatched:
            detection = detections[index]
            track = _Track(self.next_id, detection.label, detection.bbox, [detection.area_ratio])
            self.tracks[self.next_id] = track
            detection.track_id = self.next_id
            self.next_id += 1
        return detections

    @staticmethod
    def _motion(track: _Track) -> MotionStatus:
        if len(track.areas) < 3:
            return MotionStatus.UNKNOWN
        delta = track.areas[-1] - track.areas[0]
        relative = delta / max(track.areas[0], 1.0)
        if relative > 0.08:
            return MotionStatus.APPROACHING
        if relative < -0.08:
            return MotionStatus.MOVING_AWAY
        return MotionStatus.STATIONARY

