"""The person tracker under detection_stride.

Covers the failure that made live Target Person ID find nothing at all: with
a stride above 1, anyone who was not already in frame when the camera started
was never tracked, so face recognition was never even offered a crop. It went
unnoticed because forensic clips tend to open with the subject already
visible, which is the one case that worked.
"""
from __future__ import annotations

import cv2
import numpy as np
import pytest

from backend.config import OSNET_MODEL_PATH, PersonIDConfig, TrackerConfig
from backend.modules.person_id.custom_tracker import PersonBotSortTracker
from backend.modules.person_id.person_reid import PersonReID
from backend.config import REPO_ROOT

VIDEO_PATH = REPO_ROOT / "uploads" / "smoke_person_id.mp4"

pytestmark = pytest.mark.skipif(not VIDEO_PATH.exists(), reason="person-id smoke fixture not present")


@pytest.fixture(scope="module")
def clip_frames() -> list[np.ndarray]:
    cap = cv2.VideoCapture(str(VIDEO_PATH))
    frames = []
    try:
        while len(frames) < 60:
            ok, frame = cap.read()
            if not ok:
                break
            frames.append(frame)
    finally:
        cap.release()
    assert frames, "could not read the smoke fixture"
    return frames


@pytest.fixture(scope="module")
def reid() -> PersonReID:
    return PersonReID(OSNET_MODEL_PATH)


def _tracker(reid: PersonReID, stride: int) -> PersonBotSortTracker:
    config = TrackerConfig()
    return PersonBotSortTracker(
        model_path=str(config.model_path), reid=reid, detection_stride=stride,
        confidence=config.confidence, track_buffer=PersonIDConfig().gap_tolerance_frames,
        frame_rate=30,
    )


def _frames_tracked(tracker: PersonBotSortTracker, frames: list[np.ndarray]) -> int:
    return sum(1 for frame in frames if tracker.update(frame))


def test_a_person_entering_after_the_first_frame_is_still_tracked(clip_frames, reid):
    """The live case: the camera is already running when someone walks in.

    Skipped frames used to be handed an empty detection list, which the
    tracker reads as "nobody is there" rather than "nothing was looked at". A
    new track has to be matched again on the very next step to be confirmed,
    and the next two steps always claimed an empty frame - so every track born
    after the first was discarded, forever.
    """
    empty = np.full_like(clip_frames[0], 30)  # nobody in shot
    frames = [empty] * 6 + clip_frames[:40]

    tracked = _frames_tracked(_tracker(reid, stride=3), frames)
    assert tracked > 0, "a person who entered after the first frame was never tracked"
    # Not merely non-zero: they should be tracked for most of their time on
    # screen, the same as if detection ran on every frame.
    assert tracked >= 20, f"only {tracked} of {len(frames)} frames tracked the person"


def test_striding_detection_does_not_cost_coverage(clip_frames, reid):
    """Striding is a performance choice, so it must not change what is found."""
    empty = np.full_like(clip_frames[0], 30)
    frames = [empty] * 6 + clip_frames[:40]

    every_frame = _frames_tracked(_tracker(reid, stride=1), frames)
    strided = _frames_tracked(_tracker(reid, stride=3), frames)
    assert every_frame > 0
    # Allow a small margin: the strided run still associates on a third of the
    # frames, so it can pick the target up a frame or two later.
    assert strided >= every_frame - 6, f"stride=3 tracked {strided} frames vs {every_frame} at stride=1"


def test_tracks_persist_between_detections(clip_frames, reid):
    """A box that only exists on detection frames flickers at 1/stride.

    The overlay, face sampling and ReID all read this every frame, so the last
    known tracks are re-reported in between rather than vanishing.
    """
    tracker = _tracker(reid, stride=3)
    counts = [len(tracker.update(frame)) for frame in clip_frames[:30]]
    tracked_frames = sum(1 for c in counts if c)
    assert tracked_frames > len(counts) * 0.8, (
        f"tracks reported on only {tracked_frames}/{len(counts)} frames - "
        "they are disappearing between detections"
    )
