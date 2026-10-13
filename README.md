## Baseline settings

| Parameter | Value |
|---|---|
| Vehicle | Penguin |
| Total mass, including driver | 279.4 kg |
| CLA | 3.6 m² |
| CDA | 1.2 m² — repository placeholder, unvalidated |
| Rear aero fraction | 55% |
| Aero map | Disabled |
| Tire | SES_combined.tir |
| Fx / Fy / Mz scales | 0.60 / 0.60 / 0.60 |
| Track | 2026 Autocross, 0.1 m spacing |
| Start speed | 10 m/s |
| Speed ceiling | 35 m/s |
| Shift delay | 150 ms |
| Shift speeds | 15.336, 19.692, 23.355, 27.009, 29.628 m/s |
| Refined speed-search tolerance | 0.001 m/s |

Track file:
`packages/qss/comp_tracks_2026/autox26-windowed_2026-09-01_08-52-44_spacing0.1m.csv`

Shift settings were inherited and have not been confirmed as optimal for Penguin.

## Modification assumptions

Front and rear modifications were tested separately.

- Added mass: **1.5 kg per modified case**, giving 280.9 kg total.
- CG and inertia inputs unchanged.
- The motor alone is reportedly at least 1.5 kg, so the modeled mass understates the complete mechanism.
- Front: two flaps, each **15.88 × 5.79 in**, with combined rectangular area **0.118639 m²**.
- Rear: one flap, **37.60 × 4.16 in**, with rectangular area **0.100913 m²**.
- Assumed coefficient changes: **ΔCL = +0.5**, **ΔCD = +0.1**, multiplied by movable area.
- Incremental downforce assigned to the corresponding axle.
- Two modest flap angles are intended, but no specific angles or angle-to-coefficient mapping were modeled.

These coefficient changes are hypothetical sensitivity inputs, not CFD or measured results.

| State | Mass (kg) | CLA (m²) | CDA (m²) | Rear aero fraction |
|---|---:|---:|---:|---:|
| Baseline | 279.4 | 3.600000 | 1.200000 | 0.550000 |
| Mass only / low state | 280.9 | 3.600000 | 1.200000 | 0.550000 |
| Front high | 280.9 | 3.659319 | 1.211864 | 0.541084 |
| Rear high | 280.9 | 3.650457 | 1.210091 | 0.556220 |

## Switching strategy

The switching schedule was derived from the mass-only reference run.

Low state requires:

- Both segment endpoints have absolute corner radius ≥100 m.
- Both segment endpoints have speed ≥15 m/s.
- The starting reference mode is acceleration, shifting, or cruising.

Other segments use high state. Low state covers approximately **17.95% of track distance**.

Low state retains the original aero with added mass; it does not reduce drag below the original car.

Actuator delay, electrical power consumption, and transient aero effects are not modeled.

## Refined results

Positive lap-time change means slower than the original Penguin.

| Case | Lap time (s) | Change vs baseline (s) | Change vs mass only (s) |
|---|---:|---:|---:|
| Baseline | 51.1112 | +0.0000 | -0.2253 |
| Mass only | 51.3365 | +0.2253 | +0.0000 |
| Front fixed high | 51.3087 | +0.1975 | -0.0278 |
| Front switching | 51.3076 | +0.1964 | -0.0289 |
| Rear fixed high | 51.3575 | +0.2463 | +0.0210 |
| Rear switching | 51.3569 | +0.2457 | +0.0204 |

Neither modification beats the original car under the tested assumptions.

Front switching partially offsets the mass penalty. Rear switching remains slower than the mass-only case. Switching improves on fixed-high by only approximately 1.1 ms for the front and 0.6 ms for the rear; these differences are too small to treat as validated physical benefits.

### Initial runs

Before refining the speed-search tolerance from 0.01 to 0.001 m/s:

| Case | Lap time (s) | Maximum speed (km/h) |
|---|---:|---:|
| Baseline | 51.1198 | 101.535 |
| Mass only | 51.3474 | 101.407 |
| Front fixed high | 51.3179 | 101.369 |
| Rear fixed high | 51.3675 | 101.337 |

Minimum speed was approximately 17.750 km/h in all four initial runs. Use the refined results for the main comparison.

## Numerical checks and limitations

Each envelope sweep contains 2,744 input combinations:

- 8 speeds from 5 to 35 m/s.
- 7 steering-wheel angles from -45° to +45°.
- 7 throttle inputs from -1 to +1.
- 7 body-slip angles from -11° to +11°.
- Yaw rate fixed at zero.

Unconverged or failed points:

| Case | Failed / total |
|---|---:|
| Baseline | 149 / 2744 |
| Mass only | 147 / 2744 |
| Front high | 148 / 2744 |
| Rear high | 147 / 2744 |

Comparisons were checked using common converged input points across cases.

Remaining limitations:

- At 35 m/s, only 196 of 343 points converged in each case.
- Tire slip-ratio and slip-angle clipping warnings occurred.
- One lap point lies below the envelope's 5 m/s minimum.
- Baseline drag, modified aero coefficients, and total mechanism mass need validation.
- Tighter numerical tolerance does not establish physical accuracy.

A straight-line full-throttle check at 20 m/s converged with longitudinal acceleration of 6.68484 m/s² and zero lateral acceleration.

## Running the study

From this repository, with the neighboring `vehicle-analysis` checkout and its dependencies installed:

```bash
# Generate baseline and modified envelopes
python -u generate_baseline.py
python -u generate_sensitivity_mass_only.py
python -u generate_sensitivity_front_high.py
python -u generate_sensitivity_rear_high.py

# Run baseline and fixed-state comparisons
python -u run_baseline.py
python -u compare_cases.py

# Check common inputs and numerical precision
python -u check_common_points.py
python -u check_precision.py

# Run the switching cases
python -u run_switching.py

# Generate the comparison chart
python plot_summary.py
```

Some scripts may contain local paths or select timestamped envelope folders. Check these before running on another machine.

The simple plotting script contains the recorded lap times directly; update its values after new simulation runs.

## Outputs

- `envelopes/`: generated vehicle performance envelopes.
- `results/`: lap simulation CSVs and comparisons.
- `results/switching/`: front and rear switching results.
- `penguin_comparison.png`: simple lap-time comparison chart.

## Data needed next

- Front and rear CLA, CDA, and aero balance at both intended flap angles.
- Full mechanism mass, including motor, mounts, linkages, and wiring.
- Actuator response time and power requirements.
- Validated Penguin drag and shift settings.
- Track data for checking simulated speed profiles and lap times.

This study is an initial sensitivity exercise, not a validated prediction of active-aero performance.
EOF
```
