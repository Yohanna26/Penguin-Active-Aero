from pathlib import Path
import sys
import json
import numpy as np

project = Path(__file__).resolve().parent
qss = project.parent / "vehicle-analysis" / "packages" / "qss"
sys.path.insert(0, str(qss))

import lapsim
from vehicle_envelopes import load_ggv, load_yaw, load_coast_drag

envelope = (
    project / "envelopes" / "baseline"
    / "Penguin_2026-10-13_17hr05min48s" / "envelope.npz"
)
track_file = (
    qss / "comp_tracks_2026"
    / "autox26-windowed_2026-09-01_08-52-44_spacing0.1m.csv"
)

assert envelope.is_file(), f"Missing envelope: {envelope}"
assert track_file.is_file(), f"Missing track: {track_file}"

with np.load(envelope, allow_pickle=False) as data:
    speeds, counts = np.unique(data["v"], return_counts=True)

print("Converged points per speed:")
for speed, count in zip(speeds, counts):
    print(f"  {speed:5.1f} m/s: {count} points")
assert len(speeds) == 8, "Missing speed slices: inspect envelope first."

lapsim.V_MAX = float(speeds.max())

print("\nLoading Penguin envelope...", flush=True)
ggv = load_ggv(envelope)
yaw = load_yaw(envelope)
coast = load_coast_drag(envelope)
track = lapsim.parse_track(track_file)

assert np.all(np.diff(track["distance_m"]) > 0), "Invalid track distances."

print("Running Autocross baseline...", flush=True)
v_cap = lapsim.yaw_cap(yaw, track)
assert np.all(np.isfinite(v_cap)) and np.all(v_cap > 0), "Invalid speed cap."

v, v_cap, mode, gear, t, lap_time, ds = lapsim.solve(
    track, ggv, coast, v_cap
)
assert np.all(np.isfinite(v)) and np.all(v > 0), "Invalid speed result."
assert np.isfinite(lap_time), "Invalid lap time."

output = project / "results" / "baseline"
csv_path = lapsim.write_run(
    track, v, v_cap, mode, gear, t, ds, out_dir=output
)

summary = {
    "case": "Penguin baseline - preliminary",
    "envelope": str(envelope),
    "track": str(track_file),
    "lap_time_s": float(lap_time),
    "max_speed_kmh": float(v.max() * 3.6),
    "min_speed_kmh": float(v.min() * 3.6),
    "speed_limit_mps": lapsim.V_MAX,
    "shift_points_mps": lapsim.SHIFT_POINTS,
    "shift_lag_ms": lapsim.SHIFT_LAG,
    "points_below_envelope_speed_range": int((v < speeds.min()).sum()),
    "result_csv": str(csv_path),
}
Path(csv_path).with_suffix(".json").write_text(
    json.dumps(summary, indent=2)
)
print(json.dumps(summary, indent=2))
