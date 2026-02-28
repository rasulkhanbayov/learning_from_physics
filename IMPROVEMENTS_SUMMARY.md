# Summary of Improvements: Learning Physics From Video

This document summarizes what was implemented, what was changed, and how it improved over the original CVPR 2025 pipeline.

---

## 1. What We Did (Overview)

We extended the original "Learning Physics From Video" codebase along five lines:

1. **Equation-family selection & VLM motion recognition** – Use a VLM (or path) to **recognize motion type from video** (pendulum, free_fall, dropped_ball, led, etc.) and choose which ODE applies, then estimate parameters. Narrative: *"We identify both equation form and parameters from video."* An improved VLM variant uses an enhanced prompt (per-class descriptions) and 5 frames for better accuracy.
2. **Multi-step loss** – Optional **latent_loss_multistep**: weighted MSE at horizons 1..5 (default weights 1, 1, 0.5, 0.5, 0.25) to improve long-horizon consistency and parameter identifiability; selectable via `--loss latent_loss_multistep`.
3. **Unified ECCV-style model** – One architecture for 1 and N objects (graph-structured physics, symplectic integrators, identifiability analysis).
4. **Pipeline and comparison tools** – Run the unified model over Delfys75, and compare baseline vs unified / original vs equation-family using ground-truth parameters.
5. **Bug fix** – Physics parameters (gamma) now receive gradients so they actually learn during training.

---

## 2. What We Changed

### 2.1 Main pipeline (`main.py`)

- **Narrative and stages**
  - **Stage 1 – Equation-family selection (VLM motion recognition):** A VLM (OpenRouter) looks at video frames and classifies the motion/dynamics (pendulum, sliding_block, dropped_ball, free_fall, led, torricelli); or path-based keyword is used. Improved variant: `vlm_improved` uses an enhanced prompt with per-class descriptions and 5 frames (start, 25%, 50%, 75%, end) for better accuracy. When `--use_vlm`, results folder gets `vlm_accuracy.txt`, `vlm_results.csv`, `vlm_confusion_matrix.csv`.
  - **Stage 2 – Parameter estimation:** The same physics model (EndPhys) estimates alpha, beta for the chosen ODE.
  - Docstring at top of `main.py` states: no new data needed; we identify both equation form and parameters from video.
- **In-code labels** in `iterate_folders_and_process`: comments mark "Stage 1: Equation-family selection" and "Stage 2: Parameter estimation."
- **CLI** – `--use_vlm` / `--vlm_improved` run Stage 1 with a VLM; `--loss latent_loss` (default, 1-step) or `--loss latent_loss_multistep` (weighted 1..5 step); help text updated to mention "Stage 1" and "select equation family from video."

### 2.2 Unified ECCV model (new code)

- **`src/integrators/integrators.py`** – Forward Euler (with position update including `dt²*zdd` so gradients flow), Störmer–Verlet, RK4, Yoshida4. Single interface: `(z, zd, dt, accel_fn) → (z_next, zd_next)`.
- **`src/losses/loss.py`** – Unified `physics_loss(Z_encoded, Z_predicted)` on `[batch, N, d]`; MSE + KL, no branching on N.
- **`src/models/interaction_graph.py`** – `CouplingFunction` (linear, contact, double_pendulum) and `InteractionPhysicsBlock`: per-object gamma, optional coupling edges; N=1 ⇒ zero edges, same code path.
- **`src/models/encoder_unified.py`** – `EncoderUnified`: strategies holistic / per_object / shared; always outputs `[batch, N, d]`.
- **`src/models/unified_model.py`** – `UnifiedPhysicsModel(config)`: one encoder + one physics block; `encode_sequence`, `predict_sequence`, `forward`; no branching on N.
- **`src/analysis/identifiability.py`** – `IdentifiabilityAnalyzer`: injectivity check, affine mapping (z_learned vs z_real), ODE residual, parameter comparison vs GT.
- **`src/analysis/energy_tracker.py`** – Energy over rollouts for symplectic evaluation.

### 2.3 Training and running

- **`scripts/train_unified.py`** – Train on one `.npy`; adaptive LR for physics params; log gamma and gradient norm; save model and run identifiability after training.
- **`scripts/run_unified_delfys75.py`** – Loop over all Delfys75 `.npy` files, train unified model per video, write CSV in the **same format as main.py** (run, alpha, beta, max_z, min_z, z0, z1) so results are comparable.
- **`scripts/compare_baseline_unified.py`** – Load two CSVs (any main.py-style), map alpha/beta to physical params (g, decay, damping, length_m, etc.) using `Delfys75/parameters.json`, compute errors vs GT; write `parameter_errors_baseline.csv`, `parameter_errors_unified.csv`, and `parameter_errors_comparison.txt` (Diff_err = second_run_err − first_run_err; negative ⇒ second run better).

### 2.4 Multi-step loss (main pipeline)

- **`src/loss_func.py`** – `latent_loss_multistep`: at horizons k = 1..num_steps (default 5), weighted MSE between encoder latents and physics-predicted latents (`z_enc[:, k:, :]` vs `z_phys[:, k:, :]`). Default step weights `[1.0, 1.0, 0.5, 0.5, 0.25]` emphasize earlier horizons. Plus KLD on encoder latents. Improves long-horizon consistency and can help parameter identifiability.
- **`main.py`** – `--loss latent_loss` (1-step) or `--loss latent_loss_multistep` (weighted 1..5 step).

### 2.5 Critical bug fix (integrator)

- **`src/integrators/integrators.py` – Forward Euler**  
  - **Before:** `z_next = z + dt*zd` (no dependence on acceleration ⇒ no gradient to gamma).  
  - **After:** `z_next = z + dt*zd + dt²*zdd` (paper’s Euler; gradients flow to gamma).  
  - **Effect:** Physics parameters (gamma_0, gamma_1) now update during training; previously they stayed at init.

---

## 3. How It Improved

**Result files (which comparison is which):**

| Experiment | Comparison file | First column | Second column | Negative Diff_err = |
|------------|-----------------|--------------|----------------|---------------------|
| **Multi-step loss** | `Results/delfys75/parameter_errors_comparison.txt` | Baseline (paper / 1-step) | Ours (multi-step loss) | Ours better |
| **Unified model** | `Results/delfys75_0437/parameter_errors_comparison.txt` | Baseline (main.py) | Unified (run_unified_delfys75.py) | Unified better |
| **Equation family (VLM)** | `Results/delfys75_equation_family/parameter_errors_comparison.txt` | Baseline (path-based) | Equation_family (VLM selection) | VLM run better |
| **All-in-one** | `Results/delfys75_all/parameter_errors_comparison.txt` | Baseline (main.py) | All-in-one (unified + VLM + multistep) | All-in-one better |
| **VLM eval (temporal)** | `Results/vlm_temporal_reasoning/vlm_eval_summary.txt` | — | 73.33% accuracy (1 call) | — |
| **VLM eval (describe-then-classify)** | `Results/vlm_describe_then_classify/vlm_eval_summary.txt` | — | 61.11% accuracy (2 calls) | — |

### 3.1 Multi-step loss vs 1-step baseline

**Source:** `Results/delfys75/parameter_errors_comparison.txt` (Ours = multi-step, Baseline = paper/1-step).

- **Where multi-step was better (negative Diff_err):**
  - **dropped_ball (large, medium, small) g** – Lower error with multi-step (e.g. −0.07, −0.03, −0.06).
  - **free_fall (mousepad, table, tennis) g** – Clear gains (−0.47, −0.90, −0.53).
  - **pendulum_150 length** – Slightly better with multi-step (−0.004); **pendulum_90** length and damping slightly better (−0.002, −0.04).
- **Where 1-step baseline was better (positive Diff_err):**
  - **led_10s decay** – Baseline better (Diff_err +5.37).
  - **pendulum_150 damping, pendulum_45** (damping and length) – Baseline better (+0.65, +0.14, +0.15).
  - **torricelli** (large, small k) – Baseline better (+0.27, +0.75).
- **Ties (Diff_err = 0):** sliding_block (all), led_2s/led_5s nearly tie.

**Takeaway:** Multi-step loss improves g estimates (dropped_ball and free_fall) and gives small gains on some pendulum settings; baseline remains better on led_10s, pendulum_45, and some torricelli.

### 3.2 Equation-family selection (VLM vs path)

**Source:** `Results/delfys75_equation_family/parameter_errors_comparison.txt` (Baseline = path-based dynamics, second column = equation_family run with VLM selection).

- **Where VLM helped (negative Diff_err):**
  - **free_fall (mousepad, table, tennis) g** – Lower error with VLM (−0.89, −0.90, −0.55).
  - **pendulum_45 length** – Large reduction with VLM (−71.1; length 24.1 vs baseline 95.2 vs GT 0.45).
  - **led_2s decay** – VLM better (−0.40).
- **Where path was better (positive Diff_err):**
  - **pendulum_150 length** – Path much better when VLM misclassifies (+42.3; unified 72.8 vs base 31.0 vs GT 1.5).
  - **pendulum_150 and pendulum_45 damping** – Path better (+0.82, +0.32).
- **Ties (Diff_err = 0):** dropped_ball, led_10s/led_5s, pendulum_90, sliding_block, torricelli.

**Takeaway:** VLM motion recognition improves parameter estimates when it selects the right dynamics (free_fall g, pendulum_45 length, led_2s) but can hurt when wrong (e.g. pendulum_150 length). Narrative: "we identify both equation form and parameters from video."

### 3.3 Unified model vs baseline (main.py)

**Source:** `Results/delfys75_0437/parameter_errors_comparison.txt` (Baseline = main.py EndPhys, Unified = run_unified_delfys75.py).

- **Where unified was better (negative Diff_err):**
  - **Pendulum length** – Unified much closer to GT (e.g. 1.52, 2.61, 6.10 m vs GT 1.5, 0.45, 0.9); baseline 16.3, 60.9, 50.8 m. Large Diff_err (−14.8, −58.1, −44.7).
  - **Sliding_block friction** – Unified 0.18–3.33 vs GT 0.21; baseline fixed at 10 (−6.6, −9.5, −7.5).
  - **Torricelli k** – Unified smaller error (−4.1, −2.1, −0.26).
  - **LED led_2s, led_5s** – Unified better (−1.67, −0.26); led_10s unified better by 0.53.
- **Where baseline was better (positive Diff_err):**
  - **dropped_ball & free_fall g** – Baseline g ~9.4–10; unified 2.99–11.17 (large positive Diff_err).
  - **Pendulum damping** – Baseline closer to GT −0.059; unified −3.3 to −2.2.

**Takeaway:** Unified model strongly improves pendulum length, sliding_block friction, torricelli k, and LED decay; baseline remains stronger on g and pendulum damping.

### 3.4 All-in-one (unified + VLM + multistep) vs baseline

**Source:** `Results/delfys75_all/parameter_errors_comparison.txt` (Baseline = main.py, second column = run with `--vlm_improved --multistep` in run_unified_delfys75.py).

- **Where all-in-one was better (negative Diff_err):**
  - **Pendulum length** – Large gains: pendulum_150 (−26.2; Unif 4.82 m vs Base 31.0 m vs GT 1.5), pendulum_45 (−90.6; Unif 4.60 m vs Base 95.2 m vs GT 0.45), pendulum_90 (−46.7; Unif 4.54 m vs Base 51.3 m vs GT 0.9). The unified model with multistep recovers reasonable length estimates even when VLM misclassifies some videos.
  - **Sliding_block friction** – All-in-one much closer to GT 0.21: high 3.75, low 0.04, mid 0.59 vs baseline fixed at 10 (−6.2, −9.6, −9.2).
  - **LED led_2s, led_5s decay** – All-in-one better (−1.89, −0.19); Unif_est 2.0 and 1.07 vs Base 0 (baseline had zero decay estimate).
  - **Torricelli medium k** – All-in-one better (−8.95; Unif 0.97 vs Base 9.94 vs GT 0.013).
- **Where baseline was better (positive Diff_err):**
  - **dropped_ball & free_fall g** – Baseline g ~8.75–10.1 (close to 9.81); all-in-one g 2.25–8.17 (larger errors: +8.1, +4.6, +4.8 for dropped_ball; +3.3, +6.5, +5.5 for free_fall). The unified pipeline underperforms on gravitational constant in this run.
  - **Pendulum damping** – Baseline closer to GT −0.059; all-in-one gave −4.88, −4.18, −3.16 (+4.7, +3.5, +2.8).
  - **led_10s decay** – Baseline better (+0.45).
  - **Torricelli large and small k** – Baseline better (+4.98, +0.28).
- **Ties (Diff_err = 0):** sliding_block angle_deg (both match GT 20, 25, 30).

**Takeaway:** Combining VLM equation-family selection, unified model, and multi-step loss yields strong gains on **pendulum length**, **sliding_block friction**, **led_2s/led_5s decay**, and **torricelli medium k**. Baseline (main.py) remains better on **g** (dropped_ball, free_fall), **pendulum damping**, led_10s, and torricelli large/small. The all-in-one run is best evaluated as a single pipeline for structure (length, friction, decay) rather than for g and damping in the current setup.

#### Is all-in-one better than each improvement separately?

**No.** All-in-one is a **trade-off**: it wins on some metrics and loses on others compared to each separate run. Comparison is by absolute error (|Err|) for the same (dynamics, setting, param).

| Metric | Best run (lowest |Err|) | All-in-one vs multi-step only | All-in-one vs unified only | All-in-one vs equation-family only |
|--------|----------------------------------|-------------------------------|-----------------------------|-----------------------------------|
| **g** (dropped_ball, free_fall) | Multi-step or equation-family | All-in-one **worse** (e.g. 8.36 vs 0.18 on dropped_ball large) | Mixed (all-in-one better on some free_fall) | All-in-one **worse** (eq-fam has g 0.15–0.53) |
| **Pendulum length** | **Unified only** (0.55, 2.34, 5.20) | Multi-step **better** (1.18, 0.50, 0.71 vs 3.32, 4.15, 3.64) | Unified only **better** than all-in-one | All-in-one **much better** (3.32 vs 71.87, etc.) |
| **Pendulum damping** | Equation-family or multi-step | Multi-step **better** (0.37–0.89 vs 3.10–4.82) | Unified only **better** | Equation-family **better** (0.29–0.94 vs 3.10–4.82) |
| **Sliding_block friction** | **All-in-one** (0.17, 0.55, 3.62) | All-in-one **better** (vs 9.79 fixed) | All-in-one **better** on low/mid | All-in-one **better** (vs 9.79) |
| **LED decay** (led_2s, led_5s) | **Unified or all-in-one** (~0.41–0.73) | All-in-one **better** (vs 7.45–8.44) | Similar | All-in-one **better** on led_2s (0.41 vs 1.90) |
| **Torricelli k** | Unified (large, small); all-in-one (medium) | Mixed (all-in-one better on medium/small) | Unified better large/small; all-in-one **better** medium (0.97 vs 7.85) | All-in-one **better** only on medium |

**Summary:** All-in-one is **not** uniformly better than the separate runs. It is **best** vs equation-family (huge gains on pendulum length, sliding_block, LED) and gives **good** sliding_block and LED. For **g** and **pendulum damping**, multi-step-only or equation-family (main.py) are better. For **pendulum length**, unified-only (path-based, no VLM, no multistep) actually has the lowest errors in the separate runs; all-in-one improves over equation-family but not over unified-only. So use **all-in-one** when you want one pipeline that does well on length/friction/decay without path-based dynamics; use **separate** runs (e.g. multi-step or equation-family for g/damping, unified-only for length) if you optimize per metric.

### 3.5 Physics parameters actually learning

- **Before (Euler bug):** gamma_0 and gamma_1 stayed at init (e.g. 0.5, 0.05) for all epochs; loss decreased only via encoder.
- **After (Euler fix):** gamma updates (e.g. 0.5 → ~4.65, 0.05 → ~1.11 on dropped_ball); gradient norm logged and non-zero. Training is meaningful for the physics block.

### 3.6 Multi-step loss (mechanism)

- **latent_loss_multistep** trains the model to match encoder and physics rollouts at several future steps (1..5), not just one. This encourages long-horizon consistency and can improve parameter identifiability; see §3.1 for the comparison vs 1-step (Results/delfys75). Use `--loss latent_loss_multistep` when running main.py.

### 3.7 Single architecture for N=1 and N>1

- One encoder, one physics block, one loss; N=1 is one node and zero edges, N>1 adds coupling edges. Same tensor contract `[batch, N, d]` everywhere; no `if num_objects == 1` or `squeeze(1)`. Reproducibility and ablation (integrators, coupling) are straightforward; switching between single and multi-body is config-only.

### 3.8 VLM dynamics recognition (accuracy on Delfys75)

Dynamics selection (Stage 1) can use path keywords, a baseline VLM, an improved VLM with reasoning, or a small trained video classifier. Accuracy is on the full Delfys75 set (90 videos, 6 classes, 15 per class).

| Method | Accuracy | Notes |
|--------|----------|--------|
| **Baseline VLM** (1 call, simple prompt) | ~61–67% | `evaluate_vlm_dynamics.py` |
| **Temporal reasoning** (1 call, first vs last frame) | **73.33%** | `vlm_improved` with `use_temporal_reasoning=True`; best single-call VLM. |
| **Describe-then-classify** (2 calls: describe motion, then classify from text) | **61.11%** | `--describe_then_classify` in `evaluate_vlm_dynamics_improved.py`. Dropped_ball 100%, free_fall 0%, sliding_block 80%, torricelli 73%, led 60%, pendulum 53%. |
| **VLM fine-tuning (LoRA)** | ~16.67% (collapse) | Model ignores image; scores identical for every video. Not recommended. See `src/utils/vlm_finetune/README.md`. |
| **VLM fine-tuning (frozen VLM + classifier head)** | ~16.67% (collapse) | Head collapses to one class (e.g. pendulum or torricelli). Class weights, label smoothing, best-by-val checkpoint did not fix. Not recommended. |
| **Video classifier** (ResNet18 + temporal mean, trained on Delfys75) | **100%** (eval set) | `scripts/train_video_classifier.py` + `evaluate_video_classifier.py`; no VLM. Eval is on same distribution as train; use held-out test for generalization. |

**Recommendation for pipeline:** Use **temporal reasoning** (`--vlm_improved`, default) for best VLM accuracy without training, or the **video classifier** for maximum accuracy when training on the same data is acceptable. See `src/utils/vlm_improved/VLM_REASONING_ALTERNATIVES.md` for other reasoning options (CoT, hierarchical, few-shot, self-consistency).

---

## 4. How to Run (Quick Reference)

```bash
# Baseline (path-based dynamics, 1-step loss)
python main.py --path ./delfys75 --outfolder delfys75_original --dt 0.05

# With multi-step loss (optional)
python main.py --path ./delfys75 --outfolder delfys75_multistep --dt 0.05 --loss latent_loss_multistep

# Equation-family selection (VLM motion recognition)
python main.py --path ./delfys75 --outfolder delfys75_equation_family --dt 0.05 --vlm_improved

# Compare original vs equation_family
python scripts/compare_baseline_unified.py --baseline Results/delfys75_original/delfys75_original.csv --unified Results/delfys75_equation_family/delfys75_equation_family.csv --out Results/delfys75_equation_family

# Unified model over Delfys75
python scripts/run_unified_delfys75.py --path ./delfys75 --outfolder delfys75_unified --dt 0.05

# All improvements together (VLM equation-family + unified model + multi-step loss)
python scripts/run_unified_delfys75.py --path ./delfys75 --outfolder delfys75_all --dt 0.05 --vlm_improved --multistep

# Compare baseline vs unified
python scripts/compare_baseline_unified.py --baseline Results/delfys75_original/delfys75_original.csv --unified Results/delfys75_unified/delfys75_unified.csv --out Results/delfys75

# VLM dynamics accuracy (temporal reasoning, 1 call, ~73%)
python scripts/evaluate_vlm_dynamics_improved.py --path ./delfys75 --out Results/vlm_temporal_reasoning

# VLM dynamics accuracy (describe-then-classify, 2 calls, ~61%)
python scripts/evaluate_vlm_dynamics_improved.py --path ./delfys75 --out Results/vlm_describe_then_classify --describe_then_classify
```

In the comparison output: **negative Diff_err** = second CSV has lower error (better); **positive Diff_err** = first CSV has lower error.

**Producing the three comparison files:**
- **Multi-step vs 1-step:** Run baseline (e.g. `delfys75_original` with default loss), run multi-step (`delfys75_multistep` with `--loss latent_loss_multistep`), then `compare_baseline_unified.py --baseline .../delfys75_original.csv --unified .../delfys75_multistep.csv --out Results/delfys75` → `Results/delfys75/parameter_errors_comparison.txt`.
- **Unified vs baseline:** Run `run_unified_delfys75.py` (e.g. `delfys75_unified` or `delfys75_0437`), then compare with baseline CSV → e.g. `Results/delfys75_0437/parameter_errors_comparison.txt`.
- **Equation family vs path:** Run with `--vlm_improved` (`delfys75_equation_family`), then compare with path-based baseline CSV → `Results/delfys75_equation_family/parameter_errors_comparison.txt`.

**Training all improvements together:** Use the unified pipeline with VLM and multi-step: `run_unified_delfys75.py --path ./delfys75 --outfolder delfys75_all --dt 0.05 --vlm_improved --multistep`. This runs equation-family selection from video (VLM improved), the unified physics model, and multi-step physics loss in one pass. Then compare to baseline: `compare_baseline_unified.py --baseline Results/delfys75_equation_family/delfys75_equation_family.csv --unified Results/delfys75_all/delfys75_all.csv --out Results/delfys75_all` → `Results/delfys75_all/parameter_errors_comparison.txt` (see §3.4 for analysis).

---

## 5. Files Touched / Added

| Area | Files |
|------|--------|
| Main pipeline | `main.py` (docstring, stage comments, argparse, `--loss`) |
| Loss (main) | `src/loss_func.py` (`latent_loss_multistep`, weighted 1..5 step) |
| VLM motion recognition | `src/utils/vlm_dynamics.py`, `src/utils/vlm_improved/` (temporal reasoning, describe-then-classify, `VLM_REASONING_ALTERNATIVES.md`); `scripts/evaluate_vlm_dynamics.py`, `scripts/evaluate_vlm_dynamics_improved.py` |
| VLM fine-tuning (optional, not recommended) | `src/utils/vlm_finetune/` (LoRA, frozen VLM + classifier), `scripts/train_vlm_dynamics.py`, `scripts/train_vlm_dynamics_classifier.py`, `scripts/evaluate_vlm_finetune.py`; see README for limitations |
| Video classifier (dynamics from frames) | `src/utils/video_classifier/`, `scripts/train_video_classifier.py`, `scripts/evaluate_video_classifier.py` |
| Integrators | `src/integrators/__init__.py`, `src/integrators/integrators.py` (Euler fix, Verlet, RK4, Yoshida4) |
| Loss | `src/losses/__init__.py`, `src/losses/loss.py` |
| Models | `src/models/interaction_graph.py`, `src/models/encoder_unified.py`, `src/models/unified_model.py` |
| Analysis | `src/analysis/__init__.py`, `src/analysis/identifiability.py`, `src/analysis/energy_tracker.py` |
| Scripts | `scripts/train_unified.py`, `scripts/run_unified_delfys75.py`, `scripts/compare_baseline_unified.py` |
| Config | `config_unified.yaml` |
| Tests | `tests/test_unified_n1.py` |

---

## 6. One-Sentence Summary

We added **VLM motion recognition** (equation-family selection from video: baseline VLM, **temporal reasoning** ~73%, **describe-then-classify** ~61%, plus optional **video classifier** 100% on eval set; VLM fine-tuning was tried but collapses to one class and is not recommended), **multi-step loss** (weighted 1..5 step latent consistency), a **unified physics model** (one architecture for 1 and N objects, symplectic integrators, identifiability), and **pipelines and comparison scripts** for Delfys75, plus a **gradient fix** for the Euler integrator. Comparisons show **VLM improves parameter estimates when it selects the right dynamics** (e.g. free_fall, pendulum_45) and the **unified model improves pendulum length, friction, and torricelli k**; the **all-in-one run** (unified + VLM + multistep) strongly improves pendulum length, sliding_block friction, LED decay (led_2s, led_5s), and torricelli medium, while baseline (main.py) remains better on g, pendulum damping, led_10s, and some torricelli settings.
