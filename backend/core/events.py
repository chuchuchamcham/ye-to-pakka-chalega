"""Deduplicated event stream shared by all module pipelines.

The point of EventBus is to stop pipelines from emitting hundreds of
near-duplicate events for the same object. Emission is keyed by
(event_type, track_id); a repeat of the same key is dropped unless the
configured cooldown has elapsed, or the emitter explicitly marks a state
transition (e.g. ENTER -> DWELL -> EXIT) via `state`.
"""
from __future__ import annotations

from dataclasses import dataclass, field

INFO = "INFO"
LOW = "LOW"
MEDIUM = "MEDIUM"
HIGH = "HIGH"
CRITICAL = "CRITICAL"

# Severity is a property of the *rule that fired*, not of a model's confidence
# score. A confirmed target crossing a restricted boundary is critical whether
# the match scored 0.71 or 0.94 - what makes it critical is which rule it
# satisfied. Confidence still travels on the event for the operator to weigh;
# it just isn't what decides urgency.
EVENT_SEVERITY: dict[str, str] = {
    # A known target inside a restricted area, or acting on it - the events
    # the whole system exists to surface.
    "TARGET_ZONE_INTRUSION": CRITICAL,
    "TARGET_BEHAVIOR_ALERT": CRITICAL,
    # Crossing into a restricted area is the incident a zone exists to catch,
    # whether or not the person is a known target, so it sounds the siren on
    # its own. ZONE_APPROACH below is the warning that precedes it and stays
    # deliberately below alarm severity: something that has not happened yet
    # must not be able to cry wolf.
    "ZONE_ENTRY": CRITICAL,
    # A watched person or vehicle positively identified on camera.
    "TARGET_CONFIRMED": HIGH,
    "TARGET_REACQUIRED": HIGH,
    "TARGET_VEHICLE_FOUND": HIGH,
    "TARGET_VEHICLE_REACQUIRED": HIGH,
    "TARGET_CROSS_CAMERA_MATCH": HIGH,
    "CAMERA_OFFLINE": HIGH,
    # Something worth an operator's attention, but not an alarm.
    "ZONE_APPROACH": MEDIUM,
    "LONG_DWELL": MEDIUM,
    "LOITERING": MEDIUM,
    "PLATE_CONFIRMED": MEDIUM,
    "TARGET_LOST": MEDIUM,
    "TARGET_VEHICLE_LOST": MEDIUM,
    "CAMERA_DEGRADED": MEDIUM,
    # Context: real, logged, but routine on its own.
    "ZONE_EXIT": LOW,
    "SUDDEN_DIRECTION_CHANGE": LOW,
    "ABNORMAL_SPEED": LOW,
    "REPEATED_BACK_AND_FORTH": LOW,
    "PLATE_DETECTED": LOW,
    # Routine observations that belong in the log, not in anyone's face.
    "VEHICLE_DETECTED": INFO,
    "LOW_LIGHT": INFO,
    "CAMERA_ONLINE": INFO,
}

# What an external siren/alarm responds to. Deliberately narrow: an alarm that
# fires on routine events stops being treated as an alarm.
ALARM_SEVERITIES = frozenset({HIGH, CRITICAL})


def severity_of(event_type: str) -> str:
    """Severity for an event type; unknown types default to INFO rather than
    raising, so adding a new event can never crash the alert path."""
    return EVENT_SEVERITY.get(event_type, INFO)


def severity_for(event: dict) -> str:
    """Severity for a specific event, which for some types depends on what
    actually triggered it rather than on the type alone.

    TARGET_BEHAVIOR_ALERT is raised by behaviour/state.py in two different
    situations: the *confirmed target* behaving oddly, or *anyone* behaving
    oddly inside a restricted zone. Only the first is a person of interest, so
    only the first is allowed to reach alarm severity and sound the siren. The
    zone-driven case is still logged and shown - it just doesn't claim to be
    something it isn't.
    """
    etype = event.get("type", "")
    if etype == "TARGET_BEHAVIOR_ALERT":
        return CRITICAL if (event.get("data") or {}).get("is_target") else MEDIUM
    return severity_of(etype)


def should_alarm(event: dict) -> bool:
    return event.get("severity", severity_of(event.get("type", ""))) in ALARM_SEVERITIES


def describe_event(event: dict) -> str:
    """One plain-language sentence explaining why this event fired.

    Every alert an operator is expected to act on has to say what triggered
    it. "Suspicious activity: 91%" is not something a guard can verify,
    escalate or dismiss; "entered restricted zone and stayed 18 seconds" is.
    The numbers behind the decision stay on the event either way - this is
    the human-readable summary of them, not a replacement.
    """
    etype = event.get("type", "UNKNOWN")
    data = event.get("data") or {}
    track = event.get("track_id")
    who = f"Track #{track}" if track is not None else "Subject"
    # Prefer the operator's own name for the zone ("BORDER LINE") over its
    # internal id - the id means nothing to the person reading the alert.
    label = event.get("zone_label")
    zone = event.get("zone")
    zone_label = f"'{label}'" if label else (f"zone {zone}" if zone else "restricted zone")

    def num(key, fmt="{:.1f}"):
        value = data.get(key)
        return fmt.format(value) if isinstance(value, (int, float)) else None

    if etype == "TARGET_CONFIRMED":
        votes, sim = data.get("votes"), data.get("similarity")
        detail = []
        if votes is not None:
            detail.append(f"{votes} reference photo match{'es' if votes != 1 else ''}")
        if sim is not None:
            detail.append(f"similarity {sim}")
        return "Target person identified" + (f" ({', '.join(detail)})" if detail else "")
    if etype == "TARGET_CROSS_CAMERA_MATCH":
        sim = data.get("similarity")
        detail = f" (appearance match {sim})" if sim is not None else ""
        return f"Target picked up on this camera from another camera's sighting{detail}"
    if etype == "TARGET_REACQUIRED":
        return f"Target re-identified after being out of view ({who})"
    if etype == "TARGET_LOST":
        return "Target no longer visible on this camera"
    if etype == "TARGET_ZONE_INTRUSION":
        return f"Confirmed target crossed into {zone_label}"
    if etype == "TARGET_BEHAVIOR_ALERT":
        trigger = str(data.get("trigger_behavior", "unusual movement")).replace("_", " ").lower()
        # Same event type, two very different meanings - and claiming a
        # confirmed target when none is enrolled is exactly the kind of
        # overclaim that destroys trust in the whole alert stream.
        if data.get("is_target"):
            return f"Confirmed target showed {trigger}"
        return f"{who} showed {trigger} inside {zone_label}"
    if etype == "ZONE_APPROACH":
        secs = num("eta_sec")
        timing = f" within about {secs} seconds" if secs else " shortly"
        return f"{who} is heading toward {zone_label} and is predicted to enter{timing}"
    if etype == "ZONE_ENTRY":
        return f"{who} crossed into {zone_label}"
    if etype == "ZONE_EXIT":
        return f"{who} left {zone_label}"
    if etype == "LONG_DWELL":
        secs = num("duration_sec")
        return f"{who} stayed in {zone_label}" + (f" for {secs} seconds" if secs else "")
    if etype == "LOITERING":
        secs = num("duration_sec")
        return f"{who} remained in a small area" + (f" for {secs} seconds" if secs else "")
    if etype == "REPEATED_BACK_AND_FORTH":
        count = data.get("reversal_count")
        return f"{who} reversed direction repeatedly" + (f" ({count} times)" if count else "")
    if etype == "SUDDEN_DIRECTION_CHANGE":
        deg = num("angle_degrees", "{:.0f}")
        return f"{who} changed direction sharply" + (f" ({deg} degrees)" if deg else "")
    if etype == "ABNORMAL_SPEED":
        return f"{who} moved unusually fast"
    if etype == "PLATE_CONFIRMED":
        plate = event.get("plate") or data.get("text")
        conf = event.get("confidence", data.get("confidence"))
        detail = f" at {conf:.0f}% confidence" if isinstance(conf, (int, float)) else ""
        return f"Number plate {plate} confirmed across multiple reads{detail}"
    if etype == "PLATE_DETECTED":
        return f"Number plate located on vehicle {who.lower()}, not yet confirmed"
    if etype == "TARGET_VEHICLE_FOUND":
        return "Vehicle matching the searched number plate identified"
    if etype == "TARGET_VEHICLE_REACQUIRED":
        return "Searched vehicle re-identified after being out of view"
    if etype == "TARGET_VEHICLE_LOST":
        return "Searched vehicle no longer visible on this camera"
    if etype == "VEHICLE_DETECTED":
        return f"Vehicle detected ({who})"
    if etype == "LOW_LIGHT":
        return "Low-light conditions detected; image enhancement applied"
    if etype == "CAMERA_OFFLINE":
        return "Camera stopped responding"
    if etype == "CAMERA_DEGRADED":
        return "Camera is connected but frames have stopped updating"
    if etype == "CAMERA_ONLINE":
        return "Camera connected"
    return etype.replace("_", " ").capitalize()


@dataclass
class Event:
    type: str
    track_id: int | None
    frame_index: int
    timestamp_sec: float
    data: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "type": self.type,
            "track_id": self.track_id,
            "frame_index": self.frame_index,
            "timestamp_sec": round(self.timestamp_sec, 3),
            **self.data,
        }


class EventBus:
    def __init__(self):
        self._events: list[Event] = []
        # (event_type, track_id) -> (last_emit_timestamp_sec, last_state)
        self._last: dict[tuple[str, int | None], tuple[float, str | None]] = {}

    def emit(
        self,
        event_type: str,
        track_id: int | None,
        frame_index: int,
        timestamp_sec: float,
        cooldown_sec: float = 0.0,
        state: str | None = None,
        **data,
    ) -> Event | None:
        """Emit an event unless it's a duplicate within the cooldown window.

        A change in `state` (e.g. moving from ENTER to DWELL) always bypasses
        the cooldown, since that's a real transition, not a repeat.
        """
        key = (event_type, track_id)
        prev = self._last.get(key)
        if prev is not None:
            prev_ts, prev_state = prev
            same_state = state is None or state == prev_state
            if same_state and (timestamp_sec - prev_ts) < cooldown_sec:
                return None

        event = Event(
            type=event_type,
            track_id=track_id,
            frame_index=frame_index,
            timestamp_sec=timestamp_sec,
            data=data,
        )
        self._events.append(event)
        self._last[key] = (timestamp_sec, state)
        return event

    @property
    def events(self) -> list[Event]:
        return list(self._events)

    def as_dicts(self) -> list[dict]:
        return [e.as_dict() for e in self._events]
