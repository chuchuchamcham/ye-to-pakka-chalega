import { useEffect, useMemo, useState } from "react";
import { Check, Loader2, Settings2 } from "lucide-react";
import { ApiError } from "../../api/client";
import { liveApi, snapshotUrl, type LiveCamera } from "../../api/live";
import type { Zone } from "../../api/types";
import { getZone } from "../../api/zones";
import { ReferencePhotoUpload } from "../analysis/ReferencePhotoUpload";
import { ZoneDrawer } from "../analysis/ZoneDrawer";

interface ModuleState {
  person_id: boolean;
  anpr: boolean;
  behavior: boolean;
  lowlight: boolean;
}

const MODULE_LABELS: { key: keyof ModuleState; label: string; hint: string }[] = [
  { key: "person_id", label: "Target Person ID", hint: "Needs reference photos" },
  { key: "anpr", label: "ANPR / Plate OCR", hint: "Reads vehicle number plates" },
  { key: "behavior", label: "Behaviour Analytics", hint: "Loitering, pacing, abnormal speed" },
  { key: "lowlight", label: "Low-Light Enhancement", hint: "Auto-detects and enhances dark frames" },
];

/**
 * Configures what one live camera analyses.
 *
 * Applying restarts the camera's analysis session, because the pipeline builds
 * its trackers, reference gallery and zone monitors once at startup - the
 * panel says so rather than letting a few seconds of black video look like a
 * fault.
 */
export function CameraSetupPanel({
  camera,
  onApplied,
}: {
  camera: LiveCamera;
  onApplied: () => void;
}) {
  const [modules, setModules] = useState<ModuleState>({
    person_id: false, anpr: false, behavior: false, lowlight: false,
  });
  const [referenceSetId, setReferenceSetId] = useState<string | null>(null);
  const [photoCount, setPhotoCount] = useState(0);
  const [targetPlate, setTargetPlate] = useState("");
  const [zones, setZones] = useState<Zone[]>([]);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [appliedAt, setAppliedAt] = useState<number | null>(null);

  // Snapshot is frozen when the panel opens: zone points are normalized, so
  // drawing on a still frame maps correctly onto the moving stream, and a
  // still is far easier to draw on than live video.
  const [snapshotNonce, setSnapshotNonce] = useState(() => Date.now());
  useEffect(() => {
    setSnapshotNonce(Date.now());
  }, [camera.camera_id]);

  // Load the zones this camera already monitors. Without this the panel would
  // open empty and "Apply" would quietly delete zones the operator drew
  // earlier, since the request replaces the camera's whole zone list.
  const activeZoneIds = camera.zone_ids.join(",");
  useEffect(() => {
    let cancelled = false;
    const ids = activeZoneIds ? activeZoneIds.split(",") : [];
    if (ids.length === 0) {
      setZones([]);
      return;
    }
    void Promise.all(ids.map((id) => getZone(id).catch(() => null))).then((loaded) => {
      if (!cancelled) setZones(loaded.filter((z): z is Zone => z !== null));
    });
    return () => {
      cancelled = true;
    };
  }, [camera.camera_id, activeZoneIds]);

  // Reflect what the camera is actually running, so the panel doesn't claim a
  // module is off when the backend has it on. The active enrolment comes back
  // too - otherwise changing one unrelated setting would force the operator to
  // re-upload the same reference photos just to satisfy validation.
  useEffect(() => {
    setModules({
      person_id: camera.modules.includes("person_id"),
      anpr: camera.modules.includes("anpr"),
      behavior: camera.modules.includes("behavior"),
      lowlight: camera.modules.includes("lowlight"),
    });
    setReferenceSetId(camera.reference_set_id);
    setTargetPlate(camera.target_plate ?? "");
  }, [camera.camera_id, camera.reference_set_id, camera.target_plate]);

  const blockedReason = useMemo(() => {
    if (modules.person_id && !referenceSetId) return "Upload at least one reference photo for Target Person ID";
    if (!modules.person_id && !modules.anpr && !modules.behavior && !modules.lowlight && zones.length === 0) {
      return "Enable at least one module, or draw a zone";
    }
    return null;
  }, [modules, referenceSetId, zones.length]);

  async function apply() {
    if (blockedReason) return;
    setApplying(true);
    setError(null);
    try {
      await liveApi.configureAnalysis(camera.camera_id, {
        person_id: modules.person_id,
        reference_set_id: referenceSetId,
        anpr: modules.anpr,
        target_plate: targetPlate.trim() || null,
        zone_ids: zones.map((z) => z.zone_id),
        behavior: modules.behavior,
        lowlight: modules.lowlight,
      });
      setAppliedAt(Date.now());
      onApplied();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to apply configuration");
    } finally {
      setApplying(false);
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col gap-2">
        <div className="text-[12.5px] font-bold uppercase tracking-wide text-text-secondary">
          Analysis modules
        </div>
        <div className="grid grid-cols-2 gap-2 max-[760px]:grid-cols-1">
          {MODULE_LABELS.map(({ key, label, hint }) => (
            <button
              key={key}
              onClick={() => setModules((m) => ({ ...m, [key]: !m[key] }))}
              className={`flex items-start gap-2.5 rounded border px-3 py-2.5 text-left transition-colors ${
                modules[key]
                  ? "border-accent-blue bg-accent-blue/10"
                  : "border-border-1 bg-bg-1 hover:border-border-2"
              }`}
            >
              <span
                className={`mt-[2px] flex h-4 w-4 shrink-0 items-center justify-center rounded-sm border ${
                  modules[key] ? "border-accent-blue bg-accent-blue text-[#051020]" : "border-border-2"
                }`}
              >
                {modules[key] && <Check size={11} strokeWidth={3} />}
              </span>
              <span className="min-w-0">
                <span className="block text-[12.5px] font-semibold text-text-primary">{label}</span>
                <span className="block text-[11px] text-text-tertiary">{hint}</span>
              </span>
            </button>
          ))}
        </div>
      </div>

      {modules.person_id && (
        <div className="flex flex-col gap-2">
          <div className="text-[12.5px] font-bold uppercase tracking-wide text-text-secondary">
            Target reference photos
          </div>
          <ReferencePhotoUpload
            onChange={({ referenceSetId: id, photoCount: count }) => {
              setReferenceSetId(id);
              setPhotoCount(count);
            }}
          />
          {photoCount > 0 && (
            <div className="text-[11.5px] text-text-tertiary">
              {photoCount} photo{photoCount === 1 ? "" : "s"} enrolled. More angles improve
              re-identification when the face is turned away.
            </div>
          )}
        </div>
      )}

      {modules.anpr && (
        <div className="flex flex-col gap-2">
          <div className="text-[12.5px] font-bold uppercase tracking-wide text-text-secondary">
            Watchlist plate <span className="font-normal normal-case text-text-tertiary">(optional)</span>
          </div>
          <input
            value={targetPlate}
            onChange={(e) => setTargetPlate(e.target.value.toUpperCase())}
            placeholder="e.g. DL8C1234 — leave blank to read every plate"
            className="rounded border border-border-2 bg-bg-3 px-3 py-2 font-mono text-[13px] tracking-wider text-text-primary placeholder:font-sans placeholder:tracking-normal placeholder:text-text-disabled focus:border-accent-blue focus:outline-none"
          />
        </div>
      )}

      <div className="flex flex-col gap-2">
        <div className="text-[12.5px] font-bold uppercase tracking-wide text-text-secondary">
          Restricted zones
        </div>
        <ZoneDrawer
          videoId={camera.camera_id}
          zones={zones}
          onZonesChange={setZones}
          imageUrl={snapshotUrl(camera.camera_id, snapshotNonce)}
          onCreateZone={async ({ shape, points, label }) => {
            const created = await liveApi.createZone(camera.camera_id, {
              label, shape, points: points.map(([x, y]) => [x, y]),
            });
            return { ...created, video_id: camera.camera_id, shape, points } as Zone;
          }}
        />
      </div>

      {error && (
        <div className="rounded border border-accent-red/35 bg-accent-red/10 px-3 py-2 text-[12px] text-accent-red">
          {error}
        </div>
      )}

      <div className="flex items-center gap-3">
        <button
          onClick={() => void apply()}
          disabled={!!blockedReason || applying}
          className="flex items-center gap-2 rounded bg-accent-blue px-4 py-2.5 text-[12.5px] font-semibold text-[#051020] disabled:opacity-40"
        >
          {applying ? <Loader2 size={14} className="animate-spin" /> : <Settings2 size={14} />}
          {applying ? "Restarting camera…" : "Apply to camera"}
        </button>
        <span className="text-[11.5px] text-text-tertiary">
          {blockedReason
            ? blockedReason
            : appliedAt
              ? "Applied — the camera restarted with these modules."
              : "Applying restarts this camera's analysis."}
        </span>
      </div>
    </div>
  );
}
