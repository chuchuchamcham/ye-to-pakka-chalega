# BorderWatch — AI Video Intelligence for Border Surveillance

Live video analytics on **existing CCTV infrastructure**, built for SIH 2026
(PS #26187, MHA/SSB). Runs on an ordinary CPU — no GPU required.

Two modes, one analysis pipeline:

- **Live Monitor** — continuous camera feeds with real-time detection, alerts
  and an audible siren
- **Forensic Analysis** — upload a recording and search it after the fact

## What it does

| Module | What it finds |
|---|---|
| **Target Person ID** | A specific person, from 1–6 reference photos. Face recognition confirms identity; appearance ReID keeps the lock when the face turns away. |
| **ANPR** | Reads number plates, confirms them across multiple frames, and raises an alarm on a watchlist match. |
| Zone Intrusion | Someone entering a drawn restricted area. |
| Behaviour Analytics | Loitering, pacing, sudden direction changes, abnormal speed. |
| Low-Light | Enhances dark footage before analysis. |

Supporting: multi-camera health monitoring with auto-reconnect, evidence
capture (snapshot + surrounding clip), a tamper-evident hash-chained event
log, role-based access control, a phone-as-camera page, and an Android siren
app that buzzes when a threat is detected.

## Setup

Requires **Python 3.11+** and **Node 18+**.

```bash
# 1. Backend
python -m venv .venv
.venv\Scripts\activate          # Windows;  source .venv/bin/activate on Linux/Mac
pip install -r requirements.txt  # ~2GB, mostly PyTorch - be patient

# 2. Frontend
cd frontend && npm install && npm run build && cd ..

# 3. Run
python scripts/serve.py
```

Open **http://127.0.0.1:8000**. The first screen asks you to create an admin
account — there is no default password.

## Testing it

Two cameras start automatically, looping the demo clips in `uploads/`:

- **CAM-01** — a pedestrian scene. Press *Configure*, enable **Target Person
  ID**, and upload a reference photo of the person in the clip. You should get
  `TARGET_CONFIRMED` with a red box and the siren.
- **CAM-02** — a vehicle with plate `TEST123`. Press *Configure*, enable
  **ANPR**, and set the watchlist plate to `TEST123`. You should get
  `PLATE_CONFIRMED` at ~100% and `TARGET_VEHICLE_FOUND`.

Add your own camera with any RTSP URL or a video file path. To use a phone as
a camera, open **Connect Device** — that page needs HTTPS, which
`scripts/make_dev_cert.py` sets up on port 8443.

Forensic mode: **Analysis** → upload a video → pick modules → **Results**. The
siren sounds as playback reaches each alert, not when the job finishes.

```bash
pytest backend/tests -q      # 248 tests
```

## Performance

Measured on CPU (no GPU), 960px analysis width:

| | fps |
|---|---|
| Detection + tracking | 10.9 |
| ANPR | 11.0 |
| Target Person ID | 8.4 |
| 4 cameras concurrently | 8.7 each |

Running several analysis cameras at once on one CPU costs each of them frame
rate — stop the ones you are not watching.

## Honest limits

- **ANPR needs plate pixels.** A plate under roughly 100px wide will not be
  read no matter how it is processed. The UI warns when a plate is too small.
  It works at a checkpoint where vehicles approach the camera; it struggles on
  fast, distant, oblique traffic.
- **No GPU acceleration.** DeepStream/TensorRT were designed for and are the
  Phase 2 path, but they are NVIDIA-only and none of this was built or
  measured on that hardware.
- Model weights in `models/` carry their own licences — YOLOv8n is AGPL-3.0
  (Ultralytics).

## Layout

```
backend/     FastAPI app, analysis pipeline, live camera manager
  modules/   person_id, anpr, zone, behavior, lowlight
  live/      camera manager, event store, evidence recorder
frontend/    React + TypeScript UI
siren-app/   Capacitor Android siren app
scripts/     serve.py, benchmarks, dev certificate
```
