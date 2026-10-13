from pathlib import Path
import sys
import inspect
import csv
import json
import numpy as np

project = Path(__file__).resolve().parent
qss = project.parent / "vehicle-analysis" / "packages" / "qss"
sys.path.insert(0, str(qss))

import lapsim
from vehicle_envelopes import load_ggv, load_yaw, load_coast_drag

lapsim.V_BISECT_TOL = 0.001
lapsim.V_MAX = 35.0

folders = {
    "mass_only": "Penguin_2026-10-13_17hr22min04s",
    "front_high": "Penguin_2026-10-13_17hr22min33s",
    "rear_high": "Penguin_2026-10-13_17hr23min02s",
}

track_path = (
    qss / "comp_tracks_2026"
    / "autox26-windowed_2026-09-01_08-52-44_spacing0.1m.csv"
)
track = lapsim.parse_track(track_path)

def load_case(name):
    path = (
        project / "envelopes" / "common_points"
        / name / folders[name] / "envelope.npz"
    )
    return load_ggv(path), load_yaw(path), load_coast_drag(path)

low_ggv, low_yaw, low_coast = load_case("mass_only")
low_cap = lapsim.yaw_cap(low_yaw, track)
reference = lapsim.solve(track, low_ggv, low_coast, low_cap)
ref_v, _, ref_mode, _, _, ref_time, _ = reference

# Predetermined segment schedule from the mass-only reference run.
eligible = (
    (np.abs(track["radius_m"]) >= 100.0)
    & (ref_v >= 15.0)
)
low_segment = (
    eligible[:-1] & eligible[1:]
    & np.isin(ref_mode[:-1], ["accel", "shift", "cruise"])
)

# Adapt only envelope selection in the original lap solver.
source = inspect.getsource(lapsim.solve)
for braking, segment in [("False", "i"), ("True", "i - 1")]:
    for velocity in ["v[i]", "0.5 * (v[i] + v_pred)"]:
        old = (
            f"ax_available(ggv, {velocity}, r[i], braking={braking})"
        )
        new = (
            f"ax_available(select_ggv({segment}), "
            f"{velocity}, r[i], braking={braking})"
        )
        assert source.count(old) == 1, f"Source changed: {old}"
        source = source.replace(old, new)

old = "coast.ax(v[i])"
assert source.count(old) == 1
source = source.replace(old, "select_coast(i).ax(v[i])")

out = project / "results" / "switching"
out.mkdir(parents=True, exist_ok=True)
rows = []

for name in ["front_high", "rear_high"]:
    print(f"Running switching case: {name}", flush=True)
    high_ggv, high_yaw, high_coast = load_case(name)
    high_cap = lapsim.yaw_cap(high_yaw, track)

    segment_start_cap = np.where(
        low_segment, low_cap[:-1], high_cap[:-1]
    )
    segment_end_cap = np.where(
        low_segment, low_cap[1:], high_cap[1:]
    )

    # At a state boundary, satisfy both adjacent segment limits.
    cap = np.empty(len(ref_v))
    cap[0] = segment_start_cap[0]
    cap[-1] = segment_end_cap[-1]
    cap[1:-1] = np.minimum(
        segment_end_cap[:-1], segment_start_cap[1:]
    )
    assert np.isfinite(cap).all() and (cap > 0).all()

    scope = dict(vars(lapsim))
    scope["select_ggv"] = (
        lambda i: low_ggv if low_segment[i] else high_ggv
    )
    scope["select_coast"] = (
        lambda i: low_coast if low_segment[i] else high_coast
    )
    exec(compile(source, "<switched solver>", "exec"), scope)

    result = scope["solve"](track, low_ggv, low_coast, cap)
    v, cap, mode, gear, t, lap_time, ds = result
    assert np.isfinite(v).all() and (v > 0).all()
    assert np.isfinite(lap_time)

    result_path = lapsim.write_run(
        track, v, cap, mode, gear, t, ds, out_dir=out / name
    )
    row = {
        "case": name + "_switching",
        "lap_time_s": float(lap_time),
        "delta_vs_original_s": float(lap_time - 51.1112),
        "delta_vs_mass_only_s": float(lap_time - ref_time),
        "low_state_distance_pct": float(
            100 * ds[low_segment].sum() / ds.sum()
        ),
        "result_csv": str(result_path),
    }
    rows.append(row)
    print(json.dumps(row, indent=2), flush=True)

with (out / "schedule.csv").open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["segment_start_m", "segment_end_m", "state"])
    for i, low in enumerate(low_segment):
        writer.writerow([
            track["distance_m"][i], track["distance_m"][i + 1],
            "original_aero" if low else "high_downforce",
        ])

with (out / "comparison.csv").open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

(out / "assumptions.json").write_text(json.dumps({
    "strategy": "Predetermined from mass-only reference",
    "minimum_radius_m": 100,
    "minimum_reference_speed_mps": 15,
    "switch_time_s": 0,
    "actuator_energy_included": False,
    "aero_parameters": "Hypothetical fixed-state sensitivity cases",
    "baseline_reference_s_rounded": 51.1112,
}, indent=2))

print("\nSaved results to:", out)
