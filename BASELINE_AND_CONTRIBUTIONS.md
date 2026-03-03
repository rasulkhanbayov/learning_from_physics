# Baseline vs Our Improvements — ECCV Submission

This document clarifies **what the baseline did**, **what we improved**, and **how to run one pipeline** to compare them on Delfys75. Use it to stay unblocked and to write your contributions section.

---

## 1. What the baseline was doing

The **baseline** is the original “Learning Physics From Video” code (CVPR 2025–style pipeline) as in `main.py` with **path-based dynamics** and **1-step loss**.

| Aspect | Baseline behavior |
|--------|-------------------|
| **Input** | Folder of `.npy` files (e.g. `delfys75/`). Each file = one video clip, shape `(N, 10, 1, 56, 100)`. |
| **Dynamics (equation) selection** | **From folder path only.** The code looks for keywords in the path (`pendulum`, `dropped_ball`, `led`, `free_fall`, `sliding_block`, `torricelli`) and picks the corresponding ODE. No vision—just the path. |
| **Model** | One **encoder** (MLP) + one **physics block** per dynamics type (`PhysModels.py`: e.g. `free_fall`, `Pendulum`, `led`, `torricelli`, …). Each block has learnable **alpha, beta** (or similar). |
| **Training** | For each `.npy` file: encode frames → predict next latent with the chosen ODE → **1-step loss** (MSE between encoder latent and physics-predicted latent at t+1, plus KL). |
| **Output** | One CSV per run: columns like `run, alpha, beta, max_z, min_z, z0, z1` (one row per video). |
| **Limitation** | You must **organize data in folders by dynamics**. In the wild you don’t have that; the baseline cannot “see” the motion type from the video. |

So: **baseline = path says which ODE → train that ODE’s parameters (alpha, beta) with 1-step loss.**

---

## 2. What we improved (contributions)

We added **four main improvements** and one critical **bug fix**. You can present them as separate contributions or group them as “improved pipeline.”

### Contribution 1: Equation-family selection from video (VLM motion recognition)

- **Baseline:** Dynamics = from **path only** (e.g. folder name `pendulum`).
- **Ours:** **Stage 1** — use a **Vision–Language Model (VLM)** to look at video frames and **choose the dynamics** (pendulum, free_fall, dropped_ball, led, sliding_block, torricelli). **Stage 2** — same parameter estimation as before for the chosen ODE.
- **Narrative:** “We identify **both equation form and parameters** from video,” without relying on folder structure.
- **Accuracy:** Improved VLM (temporal reasoning, 5 frames): **~73%** on Delfys75; optional video classifier: 100% on eval set (same distribution).
- **CLI:** `main.py --path ./delfys75 --outfolder delfys75_equation_family --dt 0.05 --vlm_improved`

### Contribution 2: Multi-step physics loss

- **Baseline:** Loss only at **one step ahead** (t → t+1).
- **Ours:** **Multi-step loss**: match encoder and physics rollouts at **several horizons** (e.g. 1..5 steps) with weights. Improves long-horizon consistency and can help parameter identifiability.
- **Result:** Better **g** (gravity) on dropped_ball and free_fall; mixed vs baseline on pendulum/LED/torricelli (see IMPROVEMENTS_SUMMARY.md §3.1).
- **CLI:** `main.py --path ./delfys75 --outfolder delfys75_multistep --dt 0.05 --loss latent_loss_multistep`

### Contribution 3: Unified physics model (one architecture for 1 and N objects)

- **Baseline:** Separate physics blocks per dynamics; single-body only; original Euler step had a **bug** (position update did not depend on acceleration → **no gradient to physics parameters**).
- **Ours:**  
  - **One** graph-structured physics block: **N=1** = original single-body; **N>1** = same block with coupling (linear, contact, double_pendulum).  
  - **Euler fix:** Position update includes `dt² * z''` so **gamma (physics params) get gradients** and actually learn.  
  - **Extra integrators:** Störmer–Verlet, RK4, Yoshida4 (symplectic / higher-order).  
- **Result:** Unified model **strongly improves** pendulum length, sliding_block friction, torricelli k, LED decay; baseline remains better on g and pendulum damping in some runs.
- **CLI:** `scripts/run_unified_delfys75.py --path ./delfys75 --outfolder delfys75_unified --dt 0.05`

### Contribution 4: Pipelines and comparison vs ground truth

- **Baseline:** No standard way to compare runs to **ground-truth** physical parameters.
- **Ours:**  
  - Same CSV format for baseline and improved runs.  
  - **compare_baseline_unified.py**: maps alpha/beta to physical params (g, length, decay, friction, k, etc.), loads GT from `parameters.json`, computes errors, writes **parameter_errors_comparison.txt** (Diff_err = second_run − first_run; **negative** = second run better).

### Bug fix (critical for training)

- **Before:** In the Euler integrator, `z_next = z + dt*zd` → no dependence on acceleration → **gamma never updated**.  
- **After:** `z_next = z + dt*zd + dt²*zdd` → gradients flow to physics parameters. Training is now meaningful for the physics block.

---

## 3. One pipeline: baseline vs improved on Delfys75

You can reproduce **baseline** and **improved** runs and compare them with **one script**.

### Option A: Use the all-in-one script (recommended)

From the **project root** (`learning_from_physics`):

```bash
# Run baseline then improved (unified), then compare
bash scripts/run_baseline_vs_improved.sh
```

Or with custom paths:

```bash
bash scripts/run_baseline_vs_improved.sh ./delfys75 0.05
```

This will:

1. Run **baseline**: `main.py --path <path> --outfolder delfys75_baseline --dt <dt>`
2. Run **improved (unified)**: `run_unified_delfys75.py --path <path> --outfolder delfys75_improved --dt <dt>`
3. Run **compare**: `compare_baseline_unified.py` with baseline CSV vs improved CSV
4. Write results under `Results/`: CSVs + `parameter_errors_baseline.csv`, `parameter_errors_improved.csv`, `parameter_errors_comparison.txt`

Interpretation: in `parameter_errors_comparison.txt`, **negative Diff_err** = improved run has **lower** error than baseline.

### Option B: Run steps by hand

```bash
# 1) Baseline (path-based dynamics, 1-step loss)
python main.py --path ./delfys75 --outfolder delfys75_baseline --dt 0.05

# 2) Improved — pick ONE (or run multiple and compare separately):
#    (a) Equation-family (VLM)
python main.py --path ./delfys75 --outfolder delfys75_vlm --dt 0.05 --vlm_improved
#    (b) Multi-step loss
python main.py --path ./delfys75 --outfolder delfys75_multistep --dt 0.05 --loss latent_loss_multistep
#    (c) Unified model
python scripts/run_unified_delfys75.py --path ./delfys75 --outfolder delfys75_unified --dt 0.05

# 3) Compare baseline vs improved (use the improved folder you ran)
python scripts/compare_baseline_unified.py \
  --baseline Results/delfys75_baseline/delfys75_baseline.csv \
  --unified Results/delfys75_unified/delfys75_unified.csv \
  --out Results/delfys75_comparison
```

**Ground truth:** The comparison script looks for `Delfys75/parameters.json` or `delfys75/parameters.json`; the run script tries both. If your GT is elsewhere, pass `--params path/to/parameters.json` to `compare_baseline_unified.py`.

---

## 4. How to describe contributions in the paper (short)

- **Problem:** Baseline requires **manual/path-based** choice of dynamics and uses **1-step loss** and **single-body** physics; physics parameters did not receive gradients in the original Euler step.
- **Contributions:**  
  1. **Automatic equation-family selection** from video via VLM (and optional video classifier), so both equation form and parameters are identified from video.  
  2. **Multi-step physics loss** for better long-horizon consistency and parameter identifiability.  
  3. **Unified physics model** (single architecture for 1 and N objects, gradient-correct Euler, optional symplectic integrators).  
  4. **Reproducible evaluation**: same CSV format and comparison script against ground-truth parameters on Delfys75.
- **Evaluation:** We report parameter error (vs GT) for baseline vs each improvement (and optionally “all-in-one”) on Delfys75; **negative Diff_err** means the improved run is better for that (dynamics, setting, param).

---

## 5. Where to find more detail

- **IMPROVEMENTS_SUMMARY.md** — Full list of changes, result files, which comparison file corresponds to which experiment, and how to run each variant.
- **ODEs_AND_DATA.md** — The six dynamics (ODEs) and how alpha/beta map to physical parameters.

You have **one pipeline** (script + commands above) to test baseline and new version on Delfys75 and to support reasonable, clearly stated contributions for ECCV.
