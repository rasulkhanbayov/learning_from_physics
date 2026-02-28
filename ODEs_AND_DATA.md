# ODEs and data (six dynamics)

This document lists the **six dynamical systems** supported by the pipeline, aligned with the data we have: **dropped_ball**, **free_fall**, **led**, **pendulum**, **sliding_block**, **torricelli**. No additional ODE types are added beyond these; each corresponds to one motion type in Delfys75.

---

## 1. dropped_ball

- **Physics:** Ball falling under gravity (e.g. side view). Second-order linear ODE.
- **ODE form:** \( z'' + \beta z' + \alpha z = 0 \), with **α ≈ g** (gravitational constant).
- **Latent → physical:** `g = alpha` (α > 0).
- **Ground truth:** g = 9.80665 (standard); not in `parameters.json`, hardcoded in evaluation.
- **Data:** `delfys75/dropped_ball/{large,medium,small}/...`

---

## 2. free_fall

- **Physics:** Ball in free fall filmed from above; apparent size shrinks as it moves away.
- **ODE form:** Same as dropped_ball: \( z'' + \beta z' + \alpha z = 0 \), **α ≈ g**.
- **Latent → physical:** `g = alpha`.
- **Ground truth:** g = 9.80665.
- **Data:** `delfys75/free_fall/{mousepad,table,tennis}/...`

---

## 3. led

- **Physics:** Exponential decay of light intensity (or similar scalar decay).
- **ODE form:** First-order \( z' = -\lambda z \) → decay rate λ.
- **Latent → physical:** `decay = beta` (β used as decay rate).
- **Ground truth:** In `parameters.json` under `led` per setting (e.g. led_2s, led_5s, led_10s).
- **Data:** `delfys75/led/{led_2s,led_5s,led_10s}/...`

---

## 4. pendulum

- **Physics:** Damped pendulum; \( \theta'' + (b/m)\theta' + (g/L)\theta = 0 \) (small angle).
- **ODE form:** \( z'' + \beta z' + \alpha z = 0 \) with **α = g/L** (ω₀²), **β** related to damping.
- **Latent → physical:** `length = g/alpha`, `damping = -beta` (g = 9.80665).
- **Ground truth:** In `parameters.json` under `pendulum` (length_m, damping per setting).
- **Data:** `delfys75/pendulum/{pendulum_45,pendulum_90,pendulum_150}/...`

---

## 5. sliding_block

- **Physics:** Block sliding on inclined plane; friction and angle.
- **ODE form:** Motion along slope; angle from setting; friction coefficient μ from β.
- **Latent → physical:** `angle` from setting name (low=20°, mid=25°, high=30°); `friction = beta`.
- **Ground truth:** In `parameters.json` under `sliding_block` (angle_deg, friction).
- **Data:** `delfys75/sliding_block/{low,mid,high}/...`

---

## 6. torricelli

- **Physics:** Torricelli’s law; drain rate ∝ √(height); simplified as scalar evolution with coefficient k.
- **ODE form:** Model uses **α** as the drain coefficient k.
- **Latent → physical:** `k = alpha`.
- **Ground truth:** In `parameters.json` under `torricelli` (k per setting: large, medium, small).
- **Data:** `delfys75/torricelli/{large,medium,small}/...`

---

## Summary table

| Data (motion)   | ODE / model           | Main physical params | GT source        |
|-----------------|------------------------|----------------------|------------------|
| dropped_ball    | z'' + βz' + αz = 0     | g = α                | g = 9.80665      |
| free_fall       | z'' + βz' + αz = 0     | g = α                | g = 9.80665      |
| led             | z' = −λz (decay)       | decay = β            | parameters.json  |
| pendulum        | z'' + βz' + αz = 0     | length = g/α, damping = −β | parameters.json  |
| sliding_block   | slope + friction       | angle (setting), friction = β | parameters.json  |
| torricelli      | drain k                | k = α                | parameters.json  |

The pipeline (main.py, run_unified_delfys75.py, compare_baseline_unified.py) uses these six dynamics only; parameter extraction and evaluation are implemented for these. Adding a new ODE type would require new data and updates to the dynamics list, VLM choices, and `alpha_beta_to_physical` (and optionally `parameters.json`).
