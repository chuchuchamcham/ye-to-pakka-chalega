import { api } from "./client";

export type CameraState = "connecting" | "online" | "reconnecting" | "offline" | "stopped";
export type EventSeverity = "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface LiveCamera {
  camera_id: string;
  name: string;
  source_kind: "rtsp" | "file";
  loop: boolean;
  target_fps: number;
  location: string | null;
  state: CameraState;
  frames_read: number;
  frames_dropped: number;
  reconnect_count: number;
  frame_age_sec: number | null;
  measured_fps: number;
  width: number;
  height: number;
  source_fps: number;
  error: string | null;
  degraded: boolean;
  running: boolean;
  uptime_sec: number | null;
  modules: string[];
  reference_set_id: string | null;
  target_plate: string | null;
  zone_ids: string[];
  analysis_error: string | null;
  event_count: number;
}

export interface LiveEvent {
  event_id?: string;
  type: string;
  track_id: number | null;
  frame_index: number;
  timestamp_sec: number;
  zone?: string;
  camera_id: string;
  camera_name: string;
  severity: EventSeverity;
  reason: string;
  alarm: boolean;
  wall_time: number;
  data?: Record<string, unknown>;
  plate?: string;
  confidence?: number;
}

export interface AnalysisConfig {
  person_id: boolean;
  reference_set_id?: string | null;
  anpr: boolean;
  target_plate?: string | null;
  zone_ids: string[];
  behavior: boolean;
  lowlight: boolean;
}

export interface EvidenceBundle {
  bundle_id: string;
  camera_id: string;
  created_at: number;
  event_type: string | null;
  severity: EventSeverity | null;
  reason: string | null;
  camera_name: string | null;
  has_snapshot: boolean;
  has_clip: boolean;
  /** "unavailable" means assembly finished with nothing to record - not that it is still running. */
  clip_state: "ready" | "pending" | "unavailable";
  clip_size_bytes: number;
}

/** Evidence assets are served as files, used directly as <img>/<video> src. */
export function evidenceAssetUrl(bundle: EvidenceBundle, asset: "snapshot.jpg" | "clip.mp4"): string {
  return `/api/live/evidence/${bundle.camera_id}/${bundle.bundle_id}/${asset}`;
}

export const liveApi = {
  listEvidence: (limit = 50) => api.get<EvidenceBundle[]>(`/api/live/evidence?limit=${limit}`),
  listCameras: () => api.get<LiveCamera[]>("/api/live/cameras"),
  getCamera: (id: string) => api.get<LiveCamera>(`/api/live/cameras/${id}`),
  start: (id: string) => api.post<LiveCamera>(`/api/live/cameras/${id}/start`),
  stop: (id: string) => api.post<LiveCamera>(`/api/live/cameras/${id}/stop`),
  configureAnalysis: (id: string, config: AnalysisConfig) =>
    api.put<LiveCamera>(`/api/live/cameras/${id}/analysis`, config),
  createZone: (id: string, zone: { label: string; shape: "rectangle" | "polygon"; points: number[][] }) =>
    api.post<{ zone_id: string; label: string }>(`/api/live/cameras/${id}/zones`, zone),
  recentEvents: (limit = 100) => api.get<LiveEvent[]>(`/api/live/events?limit=${limit}`),
};

/** MJPEG feed URL. Used directly as an <img> src - the browser renders a
 * multipart stream natively, so no player library is involved. The cache
 * buster keeps a remounted <img> from reusing a dead connection. */
export function streamUrl(cameraId: string, fps = 12, nonce?: number): string {
  const bust = nonce === undefined ? "" : `&t=${nonce}`;
  return `/api/live/cameras/${cameraId}/stream?fps=${fps}${bust}`;
}

export function snapshotUrl(cameraId: string, nonce?: number): string {
  return `/api/live/cameras/${cameraId}/snapshot${nonce === undefined ? "" : `?t=${nonce}`}`;
}
