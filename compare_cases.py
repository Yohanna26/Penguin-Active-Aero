from pathlib import Path
import csv

project = Path(__file__).resolve().parent
template = (project / "run_baseline.py").read_text()

cases = [
    ("baseline", "Penguin_2026-10-13_17hr05min48s"),
    ("mass_only", "Penguin_2026-10-13_17hr22min04s"),
    ("front_high", "Penguin_2026-10-13_17hr22min33s"),
    ("rear_high", "Penguin_2026-10-13_17hr23min02s"),
]

results = []

for name, folder in cases:
    print(f"\nRunning case: {name}", flush=True)

    code = template.replace(
        '"baseline"', repr(name)
    ).replace(
        "Penguin_2026-10-13_17hr05min48s", folder
    ).replace(
        "Penguin baseline - preliminary",
        f"Penguin {name} - fixed-state sensitivity"
    )

    namespace = {
        "__name__": "__main__",
        "__file__": str(project / "run_baseline.py"),
    }
    exec(compile(code, f"<{name}>", "exec"), namespace)

    summary = namespace["summary"]
    results.append({
        "case": name,
        "lap_time_s": summary["lap_time_s"],
        "max_speed_kmh": summary["max_speed_kmh"],
        "result_csv": summary["result_csv"],
    })

baseline_time = results[0]["lap_time_s"]
mass_time = results[1]["lap_time_s"]

for row in results:
    row["delta_vs_baseline_s"] = row["lap_time_s"] - baseline_time
    row["delta_vs_mass_only_s"] = row["lap_time_s"] - mass_time

output = project / "results" / "fixed_state_comparison.csv"
with output.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(results[0]))
    writer.writeheader()
    writer.writerows(results)

print("\nCOMPARISON: positive delta = slower, negative = faster")
for row in results:
    print(
        f"{row['case']:12s} "
        f"lap={row['lap_time_s']:.4f} s | "
        f"vs original={row['delta_vs_baseline_s']:+.4f} s | "
        f"vs mass only={row['delta_vs_mass_only_s']:+.4f} s"
    )
print("\nSaved:", output)
