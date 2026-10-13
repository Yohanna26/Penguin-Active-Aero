from pathlib import Path
import numpy as np

project = Path(__file__).resolve().parent
cases = {
    "baseline": "Penguin_2026-10-13_17hr05min48s",
    "mass_only": "Penguin_2026-10-13_17hr22min04s",
    "front_high": "Penguin_2026-10-13_17hr22min33s",
    "rear_high": "Penguin_2026-10-13_17hr23min02s",
}

datasets = {}
reference_grid = None
common = None

for name, folder in cases.items():
    path = project / "envelopes" / name / folder / "envelope_full.npz"
    with np.load(path, allow_pickle=False) as z:
        data = z["data"].copy()
        notes = z["note"].copy()

    if reference_grid is None:
        reference_grid = data[:, :5]
    else:
        assert np.array_equal(reference_grid, data[:, :5]), "Grid mismatch"

    valid = (notes == "converged") & np.isfinite(data[:, :8]).all(axis=1)
    common = valid.copy() if common is None else common & valid
    datasets[name] = data

print("Shared converged points:", int(common.sum()), flush=True)

for name, folder in cases.items():
    data = datasets[name][common]
    output = project / "envelopes" / "common_points" / name / folder
    output.mkdir(parents=True, exist_ok=True)
    np.savez(
        output / "envelope.npz",
        delta=data[:, 0], throttle=data[:, 1], beta=data[:, 2],
        v=data[:, 3], w=data[:, 4],
        ax=data[:, 5], ay=data[:, 6], awz=data[:, 7],
    )

# Reuse the same comparison, with separate inputs and outputs.
code = (project / "compare_cases.py").read_text()
old = 'template = (project / "run_baseline.py").read_text()'
new = old + '''
template = template.replace(
    'project / "envelopes"',
    'project / "envelopes" / "common_points"'
).replace(
    'project / "results"',
    'project / "results" / "common_points"'
)
'''
assert code.count(old) == 1
code = code.replace(old, new).replace(
    '"fixed_state_comparison.csv"',
    '"common_points_comparison.csv"'
)
exec(compile(code, "<common-points comparison>", "exec"), {
    "__name__": "__main__",
    "__file__": str(project / "compare_cases.py"),
})
