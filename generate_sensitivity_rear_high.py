from pathlib import Path
import sys
import json
import subprocess

project = Path(__file__).resolve().parent
repo = project.parent / "vehicle-analysis"
qss = repo / "packages" / "qss"

sys.path.insert(0, str(repo / "packages" / "ss_param_model"))
sys.path.insert(0, str(qss))

import car_select
car_select.CAR = "Penguin"
car_select.vehicle = car_select.VEHICLES["Penguin"]

v = car_select.vehicle
v.total_vehicle_mass += 1.5

# Hypothetical increments, NOT CFD-derived or mapped to flap angle.
old_rear_cla = v.cl_a * v.rear_cop_bias_pct
v.cl_a += 0.05045667328000001
v.cd_a += 0.010091334656000003
rear_increment = 0.05045667328000001 if 'rear' == "rear" else 0.0
v.rear_cop_bias_pct = (old_rear_cla + rear_increment) / v.cl_a
v.aero_map_toggle = False


output = project / "envelopes" / "rear_high"
output.mkdir(parents=True, exist_ok=True)

v = car_select.vehicle
metadata = {
    "case": "Penguin rear_high - assumed sensitivity",
    "source_commit": subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        text=True
    ).strip(),
    "total_mass_kg": v.total_vehicle_mass + v.driver_mass,
    "CLA": v.cl_a,
    "CDA": v.cd_a,
    "CDA_note": "Repository placeholder, not validated",
    "rear_aero_fraction": v.rear_cop_bias_pct,
    "aero_map_enabled": False,
    "tire": car_select.TIRE_PATH,
}
metadata["assumptions"] = {'added_mass_kg': 1.5, 'movable_area_m2': 0.10091334656000002, 'assumed_delta_CL': 0.5, 'assumed_delta_CD': 0.1, 'increment_assigned_to_axle': 'rear', 'CG_and_inertia': 'unchanged', 'mode': 'fixed state, no active switching', 'angle_mapping': 'unknown'}
print(json.dumps(metadata, indent=2), flush=True)
(output / "case.json").write_text(json.dumps(metadata, indent=2))

# 调用团队的生成程序，仅把输出位置改到本项目。
script = qss / "envelope_generation.py"
code = script.read_text()
original = 'ENVELOPES_DIR = QSS_DIR / "envelopes"'
assert code.count(original) == 1, "Source changed: check output path first."
code = code.replace(original, f"ENVELOPES_DIR = Path({str(output)!r})")

exec(compile(code, str(script), "exec"), {
    "__name__": "__main__",
    "__file__": str(script),
})
