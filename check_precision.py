from pathlib import Path
import sys

project = Path(__file__).resolve().parent
qss = project.parent / "vehicle-analysis" / "packages" / "qss"
sys.path.insert(0, str(qss))

import lapsim
lapsim.V_BISECT_TOL = 0.001

code = (project / "check_common_points.py").read_text()
code = code.replace(
    'project / "results" / "common_points"',
    'project / "results" / "precision_check"'
).replace(
    '"common_points_comparison.csv"',
    '"precision_check_comparison.csv"'
)

print("Speed search tolerance:", lapsim.V_BISECT_TOL, "m/s", flush=True)

exec(compile(code, "<precision check>", "exec"), {
    "__name__": "__main__",
    "__file__": str(project / "check_common_points.py"),
})
