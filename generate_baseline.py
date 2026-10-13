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
car_select.vehicle.aero_map_toggle = False

output = project / "envelopes" / "baseline"
output.mkdir(parents=True, exist_ok=True)

v = car_select.vehicle
metadata = {
    "case": "Penguin baseline",
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
