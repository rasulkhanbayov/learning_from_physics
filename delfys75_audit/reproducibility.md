# Delfys75 reproducibility audit (IRIS paper, Tables 4 and 5)

Handoff notes for a new working session (human or Claude) on the compute server.
Read this whole file before running or changing anything.

- **Audit dates:** 2026-10-08 to 2026-10-13
- **Paper:** *IRIS: A Real-World Benchmark …*, ECCV 2026 (submission ID 13771). The camera-ready Tables 4 and 5 are identical to the submission.
- **Code:** public repo `github.com/KurbanIntelligenceLab/iris-bench`. The dev history is in `github.com/rasulkhanbayov/learning_from_physics`.

---

## 1. Why this exists

An external researcher reproducing the **Delfys75** experiments (Table 4 and Table 5, Sec. 6.2) emailed us. Their questions concern Delfys75 only, not the IRIS dataset or the IRIS tables. The audit found that their observations are correct and that Table 4 has further problems they did not mention.

**Nothing was fabricated.** Every Table 4 and Table 5 value traces exactly to a released CSV and a script in the repo. The problems are pipeline and evaluation errors. The goal now is to **re-run Delfys75 correctly**, produce trustworthy numbers, and use them in a reply to the researcher and in an erratum or update.

### What the researcher raised

1. `Results/delfys75_baseline/delfys75_baseline.csv` has 48 all-zero rows and `Results/delfys75_improved/delfys75_improved.csv` has 45. These look like exceptions written as zeros. Their own run had 1 and 0.
2. Pendulum, LED and Torricelli in Table 4 match the released CSVs. Dropped Ball, Free Fall and Sliding Block do not: the CSV gives a g error of about 9.81, while the paper says 0.00 and attributes it to "g stays at g₀ = 9.81".
3. Table 4's "corrected, one-step" numbers differ from Table 5's one-step numbers.
4. Preprocessing uses stride 6 at 60 fps (dt = 0.1 s), but the Delfys75 scripts default to `--dt 0.05`. Which was used?
5. They ask which commit, `.npy` files, dt/stride, CSVs and evaluation script produced Table 4, and how failed runs were handled.

### Reply status

A draft reply exists but has **not been sent**. The co-authors need to agree first because it admits errors. Do not tell the researcher that the Delfys75 results were not released: they are in the public repo and the researcher quotes them. Do not say IRIS is "all fine" until it has been audited (section 7).

---

## 2. Where the published numbers come from

| Paper item | Source file(s) | Produced by |
|---|---|---|
| Table 4 "Base." | `Results/delfys75_baseline/delfys75_baseline.csv` | `main.py` (per-system blocks in `src/models/PhysModels.py`), `--dt 0.05`, 1-step loss |
| Table 4 "Corr." | `Results/delfys75_improved/delfys75_improved.csv` | `scripts/run_unified_delfys75.py` (unified model, `integrator: euler`, 1-step, 500 epochs), `--dt 0.05` |
| Table 4 values | `Results/delfys75_comparison/parameter_errors_comparison.txt` | `scripts/compare_baseline_unified.py` |
| Table 5 "1-step" | `Results/delfys75_original/delfys75.csv` (earlier run) | `main.py`, 1-step |
| Table 5 "Multi" | `Results/delfys75/delfys75.csv` | `main.py`. This folder also has VLM routing output (`vlm_accuracy.txt`, 73.33%), and its rows show VLM misrouting, so it is **not a confirmed pure path-based multi-step run** |
| Table 5 values | `Results/delfys75/parameter_errors_comparison.txt` | **Unreleased script.** `scripts/evaluate_parameter_errors.py` and `scripts/compare_results.py` are 0-byte files in every commit and every copy |

The Table 4 CSVs were committed on 2026-03-03 (dev commit `eae47d9`). All `Results/` files are byte-identical across the dev repo, the public `iris-bench` repo and the `KIL/learning_from_physics` working copy.

**Not retained anywhere:** the preprocessed Delfys75 `.npy` files, the logs of the Table 4 runs, and the Table 5 evaluation script. Ask the co-authors and check the compute server, in case they exist there.

---

## 3. Confirmed problems

### 3.1 Failed runs written as zeros (Table 4)

- `main.py` and `run_unified_delfys75.py` catch any exception and write `alpha = beta = … = 0`.
- In both Table 4 CSVs, **every** `dropped_ball`, `free_fall` and `sliding_block` clip (45 clips) failed. The baseline CSV also has one failed clip each in `led/led_5s`, `torricelli/large` and `torricelli/medium`.
- The cause was data loading: the `.npy` files for those classes did not load as `(N, 10, 1, 56, 100)`. An archived log from the same period, `Results/delfys75_1/delfys75.log`, shows "too many indices for array: array is 1-dimensional". The exact file state cannot be reconstructed.
- `compare_baseline_unified.py` does **not** filter failed rows. They enter the MAE as estimate 0 (n = 5).

### 3.2 Wrong 0.00 entries and footnote (Table 4)

- For Dropped Ball, Free Fall and Sliding Block, the paper printed the **estimate** (0, from the failed runs) as the MAE.
- The true MAE in the released files is 9.81, 9.81 and 0.21 in both columns, i.e. no valid result.
- The footnote is false: `main.py` initializes physics parameters with `init_phys = 10.0`, not 9.81, and the baseline free-fall block does learn g.

### 3.3 Parameter-mapping bug in the evaluation (Table 4 headline)

`alpha_beta_to_physical()` in `scripts/compare_baseline_unified.py` assumes the unified model's conventions. The `PhysModels.py` blocks that `main.py` uses define their parameters differently:

| System | `PhysModels` block (`main.py`) | Script maps | Effect |
|---|---|---|---|
| Pendulum | `y_hat = 2y1 − y0 − dt(β(y1−y0) + dt·(g/|α|)·sin y1)`, so **α = L** | L = g/α | α ≈ 0.10 becomes about 95 m |
| LED | `y_hat = y1 − dt·α·y1`, so **decay = α**; β fixed at 0 | decay = β | estimate is always 0, error always equals GT (2.30) |
| Sliding block | `y_hat = 2y1 − y0 + 10·α·dt²`; **β never enters the model** | μ = β | μ is not estimable from this block |
| Free fall / dropped ball | `y_hat = 2y1 − y0 − α·dt²`, so α is g in latent units | g = α | consistent |
| Torricelli | `y_hat = |y1| − dt·α·√|y1|`, so k = α | k = α | consistent |

Table 4 rows recomputed from the released CSVs:

| Row | GT | Paper Base / Corr | Released files, script mapping (Base / Corr) | Base with model-consistent mapping | Failed clips (B/C) |
|---|---|---|---|---|---|
| dropped_ball/large g | 9.81 | 0.00 / 0.00 | 9.81 / 9.81 | 9.81 (failed) | 5/5 |
| free_fall/mousepad g | 9.81 | 0.00 / 0.00 | 9.81 / 9.81 | 9.81 (failed) | 5/5 |
| led/led_2s γ | 2.30 | 2.30 / 0.40 | 2.30 / 0.40 | 7.45 | 0/0 |
| pendulum_45 L | 0.45 | 95.07 / 3.80 | 95.07 / 3.80 | **0.35** | 0/0 |
| pendulum_90 L | 0.90 | 50.15 / 2.93 | 50.15 / 2.93 | **0.71** | 0/0 |
| pendulum_150 L | 1.50 | 29.83 / 0.71 | 29.83 / 0.71 | **1.19** | 0/0 |
| sliding_block/mid μ | 0.21 | 0.00 / 0.00 | 0.21 / 0.21 | 0.21 (failed) | 5/5 |
| torricelli/large k | 0.016 | 6.07 / 2.91 | 6.07 / 2.91 | 6.07 | 1/0 |
| torricelli/small k | 0.010 | 7.67 / 5.69 | 7.67 / 5.69 | 7.67 | 0/0 |

Consequences:

- The claim that the gradient correction cuts pendulum-length error from 95.07 to 3.80 m is **not supported**. With consistent mapping, the baseline beats "Corr." on two of the three pendulum settings.
- Table 5's 1-step pendulum_45 value (0.35) is exactly this consistent-mapping number from a different run, because the unreleased Table 5 script used L = α.
- Torricelli: both columns are 2–3 orders of magnitude above GT, so neither recovers k.

### 3.4 "Corr." is not "baseline + fixed integrator"

- `run_unified_delfys75.py` fits one generic damped oscillator, **z″ + γ₁z′ + γ₀z = 0**, to every Delfys75 system, including LED, Torricelli, free fall and sliding block. `config_for_dynamics()` only changes settings for multi-object systems. The CSV stores `alpha = γ₀` and `beta = γ₁`.
- So Table 4 compares two different models, not one model with and without an integrator fix.
- For free fall (constant acceleration), LED (first-order decay) and Torricelli (√h law), mapping γ₀ or γ₁ to g, decay or k is not physically meaningful.

### 3.5 The "gradient-flow bug in Garcia et al." claim needs verification

- The paper says the original pipeline's Euler step omits the acceleration term, so physics parameters get no gradient.
- `main.py` never calls `ForwardEuler`. Its blocks are the finite-difference updates above, and every one includes α. Gradients do flow: in the released baseline runs the pendulum α moved from 10.0 to about 0.10.
- The current `main` branch of Garcia et al.'s repo (`github.com/Alejandro-neuro/Learning_physics_from_video`, `src/models/PhysModels.py`) has the **same** blocks as our `PhysModels.py`, with acceleration terms included.
- `ForwardEuler` in `src/integrators/integrators.py` has had the dt² term since it was first committed (`82c42ba`). `BASELINE_AND_CONTRIBUTIONS.md` describes the bug under the *unified model* contribution.
- **Most likely explanation (not proven):** an early, uncommitted version of *our own* unified-model integrator lacked the term and was fixed, and the bug was then attributed to Garcia et al.'s pipeline.
- **Action:** compare against the exact version of the Garcia et al. code we started from before claiming the bug is theirs in any reply or erratum.

### 3.6 Failed-run handling differs between the tables

- Table 4's script counts failed runs as estimate 0.
- Table 5's script **excluded** them (e.g. N = 4 for `free_fall/mousepad` in `Results/delfys75/parameter_errors_baseline.csv`).
- The paper (Sec. 4, "Data and reproducibility") says MAE uses a 2-clip test split per setting. The Delfys75 evaluation used all 5 clips.

### 3.7 dt and frame stride

- Original Garcia et al. `video2npy.py`: fixed stride 6 at 60 fps, so **Δt = 0.1 s**. Their example command uses `--dt 0.1`.
- Our `src/utils/video2npy.py` uses an adaptive stride: 6 for clips of at least 60 frames, 2 for 20–59 frames, 1 for 10–19 frames. That gives Δt = 0.1, 1/30 or 1/60 s, depending on clip length. Clips shorter than 10 frames are not saved.
- All Delfys75 runs passed a single `--dt 0.05`, which matches none of these strides. α scales with Δt⁻² and β with Δt⁻¹, so all estimates are affected.
- The supplement's sentence "Delfys75 uses Δt = 0.05 s as in the original codebase" is **incorrect**.
- `main.py` hard-codes `dt = 1/60` inside `evaluate_model()`, but only for plotting.
- The public README shows `python src/utils/video2npy.py --input_dir … --output_dir …`, but the script takes no CLI arguments (its `base_path` is hard-coded).

---

## 4. What a re-run will and will not reproduce

| Table 4 item | Re-run with released code + `compare_baseline_unified.py` |
|---|---|
| Pendulum Base 95 / 50 / 30 m | Roughly the same, because the mapping bug causes it. This confirms the bug, not the result |
| LED Base 2.30 | Exactly the same, because the estimate is always 0 |
| Dropped ball / free fall / sliding (0.00) | **No.** If loading works you get real errors. Even the released CSV gives 9.81 |
| Corr. column, Torricelli | Close but not identical: depends on the `.npy` stride, CPU vs GPU, and run-to-run noise |

The purpose of the re-run is to get **correct** numbers, not to match the paper.

---

## 5. Reproduction plan

### 5.1 Data

- Download Delfys75 from Kaggle: `kaggle datasets download -d jaswar/physical-parameter-prediction`. Check its layout and license.
- The pipeline expects `delfys75/<dynamics>/<setting>/<run>/<run>.npy`, with dynamics in {`dropped_ball`, `free_fall`, `led`, `pendulum`, `sliding_block`, `torricelli`}. Settings:
  - `dropped_ball`: `large`, `medium`, `small`
  - `free_fall`: `mousepad`, `table`, `tennis`
  - `led`: `led_2s`, `led_5s`, `led_10s`
  - `pendulum`: `pendulum_45`, `pendulum_90`, `pendulum_150`
  - `sliding_block`: `low`, `mid`, `high`
  - `torricelli`: `large`, `medium`, `small`
- That is 5 clips per setting, 90 clips in total. The paper text says "75 videos"; reconcile this with the Kaggle contents.
- Ground truth: `compare_baseline_unified.py` looks for `delfys75/parameters.json` or `Delfys75/parameters.json`. Check that Kaggle provides it. The GT values used in the released comparison files:
  - g = 9.80665 (hard-coded)
  - pendulum length 0.45 / 0.90 / 1.50 m; damping −0.0592
  - LED decay 2.30 / 0.92 / 0.46 (led_2s / led_5s / led_10s)
  - sliding block friction 0.2076; angle 20 / 25 / 30° (low / mid / high, taken from the setting name)
  - Torricelli k 0.0162 / 0.0128 / 0.0096 (large / medium / small)

### 5.2 Preprocessing (fixed stride)

- Add CLI arguments to `src/utils/video2npy.py` (`--input_dir`, `--output_dir`, `--stride`) and an option to **disable the adaptive stride**.
- Main setting: **stride 6, dt = 0.1** (matches the original code).
- Optional sensitivity run: stride 3, dt = 0.05.
- Log the frame count, stride and number of samples for every clip, and **list clips too short to produce samples** instead of skipping them silently.
- Before any training, check that every `.npy` loads with shape `(N, 10, 1, 56, 100)`, N > 0, and save a SHA-256 manifest.

### 5.3 Runs

All runs are path-based (no VLM), seed 42, with the same `--dt` as the stride (0.1 for stride 6):

```bash
python main.py --path ./delfys75 --outfolder d75_base_1step  --dt 0.1 --loss latent_loss
python main.py --path ./delfys75 --outfolder d75_base_multi  --dt 0.1 --loss latent_loss_multistep
python scripts/run_unified_delfys75.py --path ./delfys75 --outfolder d75_unified_1step --dt 0.1
python scripts/run_unified_delfys75.py --path ./delfys75 --outfolder d75_unified_multi --dt 0.1 --multistep
```

- Keep stdout and stderr logs for every run: `… 2>&1 | tee Results/<outfolder>/run.log`.
- Record the git commit hash, GPU/CPU, and the torch and CUDA versions.
- Make the exception handler also record the failure: add a `status`/`error` column, or a separate `failures.csv`. Never write silent zeros.

### 5.4 Fixed evaluation script

Write a new script (e.g. `scripts/evaluate_delfys75.py`) rather than patching the old one in place, so the old behaviour stays documented:

- **Model-specific mappings.** For the baseline (`PhysModels`):
  - pendulum L = |α|
  - LED decay = α
  - Torricelli k = α
  - g = α
  - sliding-block μ: report as not estimable (or derive it from α with a stated assumption)

  For the unified model (z″ + γ₁z′ + γ₀z = 0): pendulum L = g/γ₀, damping = γ₁. For non-oscillator systems, flag that the mapping is not physically meaningful.
- **Pendulum damping sign:** the block's damping coefficient is β, but the old script reports −β and the GT is −0.0592. Decide on and document one convention.
- **Failed runs:** exclude them, report N_ok / N_total for every row, and never count them as zero.
- **Output:** per-clip errors plus MAE ± std per (dynamics, setting, param), as CSV and LaTeX.
- **Validation:** run the new script on the old released CSVs and confirm it reproduces the "model-consistent mapping" column in section 3.3 (pendulum 0.35 / 0.71 / 1.19, LED 7.45). Also run the old script on the new CSVs, so the two can be compared side by side.

### 5.5 Deliverables

- New CSVs, logs, `.npy` manifest, evaluation script and corrected Table 4 and Table 5, all committed.
- A short changelog that explains each difference from the published tables, referencing section 3.
- Updated README instructions that match the actual CLI.

---

## 6. Paper statements that need correcting (Delfys75)

- Table 4: the dropped ball, free fall and sliding block rows; the footnote ("g₀ = 9.81 … prevents learning"); the pendulum and LED baseline values; the caption and Sec. 6.2 claim of 95.07 → 3.80 m.
- Sec. 5.1 and 6.1: "Baseline = original uncorrected Euler integrator" and "+Corrected = gradient-corrected Euler step" do not describe what was run (see 3.4 and 3.5).
- Table 5: confirm what the "Multi" column actually is (VLM-routed?) and recompute it.
- Sec. 4: the "test partition (2 clips per setting)" statement, for Delfys75.
- Supplement: "Delfys75 uses Δt = 0.05 s as in the original codebase".
- Intro and contributions: the "gradient-flow bug in the state-of-the-art pipeline [Garcia et al.]" claim, pending the check in 3.5.

---

## 7. Open item: audit IRIS the same way

The IRIS experiments share `compare_baseline_unified.py`, `video2npy.py` (adaptive stride) and the zeros-on-exception handling. The supplement says IRIS uses Δt = 1/60 s, which only matches stride 1. Before telling anyone that IRIS is fine, check `Results/iris_*`:

- all-zero rows;
- the mapping used for each model (especially any `main.py`/`PhysModels` numbers, such as pendulum length);
- the dt and stride actually used;
- which CSV and script produced each IRIS table.

---

## 8. Ground rules for whoever continues

- Report what the files show, including when that is unfavourable. Do not tune or select runs to match published numbers.
- Never overwrite existing `Results/` folders. Write new runs to new folders.
- Do not claim the Delfys75 results were unreleased or lost: the CSVs are public. What is genuinely missing is the `.npy` files, the run logs and the Table 5 evaluation script.
- Do not send anything to the researcher or publish an erratum without the authors' sign-off.
