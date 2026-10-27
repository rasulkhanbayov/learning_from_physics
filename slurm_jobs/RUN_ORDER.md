# Delfys75 re-run: run order

Re-runs the Delfys75 experiments behind paper Tables 4 and 5 correctly (see `delfys75_audit/reproducibility.md`).
Submit everything **from the repo root**. Every result goes to a new folder under `Results/repro_d75/`;
no existing `Results/` folder is touched, and a job stops rather than overwrite its own folder.
Large files (code snapshots, videos, `.npy`) go to `repro_d75_work/` — keep that folder out of git.

| Step | Command | Where | Time | Produces | Success check |
|---|---|---|---|---|---|
| 0 | `bash slurm_jobs/00_setup_env.sh` | interactive on 10.4.64.27/28 (**not** panther-login) | ~15 min | conda env `iris_d75_repro`; code snapshots `repro_d75_work/code/{iris-bench_ce61c63,dev_eae47d9}` | ends with "Setup done" |
| 1 | `sbatch slurm_jobs/01_download_data_cpu.sh` (or `bash …` on 10.4.64.27/28 if compute nodes have no internet) | CPU | < 30 min | Kaggle v11 (916 MB, MIT) in `repro_d75_work/data/raw/` + `layout.txt` | script checks 90 `video.mp4` + `parameters.json`; token read from `~/.kaggle/kaggle_token.txt` |
| 2 | `sbatch slurm_jobs/02_preprocess_verify_cpu.sh` | CPU, 16 cores | < 1 h | three `.npy` datasets (~35 GB: `delfys75_garcia`, `_s6`, `_s3`), SHA-256 manifests; `Results/repro_d75/preprocessing/` | `verify.log` says "All files OK." 3×; garcia report: 90/90 ok; s6 report: 45 `too_short` (expected); `stride_evidence.txt`: 45 clips match stride 6; `gt_check.txt`: only 2 Torricelli rounding warnings |
| 3 | `sbatch slurm_jobs/03_validate_eval_cpu.sh` | CPU | 1 min | `Results/repro_d75/validation_old_csvs/` | `checks.txt`: **18/18 checks passed** (can run any time after step 0) |
| 4 | `sbatch slurm_jobs/04_smoke_a100.sh` | 1× A100 | < 1 h | `Results/repro_d75/smoke_<job>_*` | both statuses `ok`; prints a runtime estimate per job |
| 5 | `sbatch` each of `05a`–`05d` | 4× A100, in parallel | see step 4 | one folder per config (below) | job log ends "finished"; see "Reading a run" |
| 6 | `sbatch` each of `06a`–`06d` | 4× H200, in parallel with step 5 | see step 4 | one folder per config | same |
| 7 | `sbatch slurm_jobs/07_evaluate_cpu.sh` | CPU | 1 min | `Results/repro_d75/evaluation/` | start with `new_evaluator/summary.txt` |

## Data protocols

| Dataset | Stride / frames per sample / Δt | Used by | Why |
|---|---|---|---|
| `delfys75_garcia` (main) | pendulum, Torricelli 6 / 20 / 0.1 s; LED 1 / 20 / 1/60 s; sliding block 2 / 10 / 1/30 s; dropped ball 2 / 4 / 1/30 s; free fall 1 / 10 / 1/60 s | 05a–06b | Garcia et al. (CVPR 2025, arXiv:2410.01376v2) Table 5; every clip yields windows |
| `delfys75_s6` | 6 / 10 / — for all | 06c | the data behind the published runs; dropped ball (27–33 frames), free fall (16–23) and sliding block (39–57) are shorter than the 60 frames needed, which is why those 45 clips failed in Table 4 |
| `delfys75_s3` | 3 / 10 / 0.05 s for all | 06d | the supplement's stated Δt, used consistently |

Evaluation subsets: Kaggle's `free_fall` folder holds bouncing-ball clips (`parameters.json`: elasticity),
which are not among Garcia et al.'s 75 videos and have no g ground truth; they are run, but reported in a
separate block and marked * in the LaTeX tables. Sliding block is scored on total acceleration
a = g(sin θ − μ cos θ) (Garcia et al. estimate only that); μ is not estimable with the baseline block.

## The eight GPU jobs

All path-based (no VLM), seed 42, 500 epochs, one GPU each.

| Script | GPU | Config folder | Code | Data / dt | Model, loss | Purpose |
|---|---|---|---|---|---|---|
| 05a | A100 | `g_base_1step` | public `ce61c63` | garcia / per system | baseline, 1-step | corrected Table 4 "Base." and Table 5 "1-step" |
| 05b | A100 | `g_base_multi` | public | garcia / per system | baseline, multi-step | path-based Table 5 "Multi" (published one was VLM-routed) |
| 05c | A100 | `g_unified_1step` | public | garcia / per system | unified, 1-step | Table 4 "Corr." |
| 05d | A100 | `g_unified_multi` | public | garcia / per system | unified, multi-step | completes the 2×2 |
| 06a | H200 | `g_base_1step_init5` | public | garcia / per system | baseline, init 5 | is α learned or does it stay at its init? |
| 06b | H200 | `g_base_1step_init20` | public | garcia / per system | baseline, init 20 | same |
| 06c | H200 | `s6_legacy_eae47d9_base_1step_dt0.05` | dev `eae47d9` | s6 / **0.05** | baseline, 1-step | the published Table 4 "Base." setting (45 clips; the rest have no data at stride 6) |
| 06d | H200 | `s3_base_1step`, `s3_unified_1step` | public | s3 / 0.05 | baseline + unified | dt sensitivity |

Walltime: 2 days for baseline jobs (2.5 for 06c, 06d), 12 h for unified jobs. If a job times out,
resubmit the same script with `sbatch --export=ALL,RESUME=1 slurm_jobs/<script>`: finished clips are skipped.
Account/QOS lines are copied from earlier projects (`a100_hbku`, `h200_hbku`); confirm them with
`sacctmgr show assoc user=$USER format=account,qos` before submitting.

## Reading a run

Each config folder has `clips.csv` (one row per clip), `run.log`, `provenance.txt` (commits, GPU,
torch/CUDA, data-manifest hash, tool hashes), `pip_freeze.txt` and, for the baseline, `param_logs/`
(α, β and losses per epoch for every clip).

`status` in `clips.csv`: `ok`; `failed` (exception; message in `error`); `not_trained` (training
returned before epoch 1, estimate = init); `nan_during_training`; `nonfinite`. Only `ok` clips enter
the MAE; summaries show `n_ok/n_total`. Some failures are expected and are results, not bugs to hide.
A job exits with code 3 when it finished but some clips are not `ok`.

## What the wrappers change relative to the released code (and why)

`repro_d75/run_baseline.py` and `run_unified.py` call the released functions unchanged
(`main.execute_experiment`, `run_unified_delfys75.train_one_video`, …) from a pinned snapshot. They only:

- record exceptions as `failed` instead of writing zeros;
- delete `best_model.pt` before each clip (otherwise a clip that hits NaN early loads the previous clip's model);
- process clips in sorted order;
- seed the unified model per clip (the released script sets no seed);
- override `init_phys` for 06a/06b only.

Kept as released and recorded, not fixed: the unified model fits only the first window of
each clip (`frames_used` column; 4 frames for dropped ball under the garcia protocol); batch size is
128 for every system (Garcia et al. used 64/32/all); `train.py`'s early stopping never triggers (the counter resets each
epoch), so every clip runs all 500 epochs; the public code subsamples clips to 1500 windows (eae47d9 does not).

`repro_d75/video2npy_fixed.py` reproduces `src/utils/video2npy.py` bit for bit at a fixed stride
(checked on test videos), saves float32 instead of float64, lists clips too short for one window, and
writes `protocol.json` (stride, frames, Δt per system) that the runners read when `dt=protocol`.

`scripts/evaluate_delfys75.py` uses model-specific mappings (baseline: L = |α|, decay = α, g = α,
k = α, sliding-block acceleration = 10|α|; unified: L = g/γ₀, other systems not physically mapped),
excludes failed clips, and never reads a parameter from a folder name. Step 3 checks it against
the released CSVs. Pendulum damping is reported with the old sign convention and is unverified.

## Round 2 (after the first evaluation): what the reply to the researcher still needs

| Script | GPU | Config folder(s) | Purpose | Time |
|---|---|---|---|---|
| 08a | A100 | `s6_legacy_eae47d9_unified_1step_dt0.05`, `g_unified_1step_seed1`, `_seed2` | re-run Table 4 "Corr." in the published setting (with 06c this reproduces both Table 4 columns); unified seeds | < 1 h |
| 08b, 08c | A100 | `g_base_1step_seed1`, `_seed2` | error bars for the corrected baseline (Table 4 "Base." / Table 5 "1-step") | ~4 h each |
| 08d, 08e | H200 | `g_base_multi_seed1`, `_seed2` | error bars for multi-step (Table 5 "Multi") | ~4 h each |

Then a second evaluation into a new folder (the first one is kept):
`sbatch --export=ALL,EVAL_NAME=evaluation_v2 slurm_jobs/07_evaluate_cpu.sh`.
It adds `new_evaluator/seed_summary.{csv,txt}` (MAE mean ± std over seeds 42, 1, 2) and
`old_script_table4_published_setting_legacy_base_vs_legacy_unified/` (the released script on both
re-run Table 4 columns; compare with the paper's Table 4).

Seeds: for the baseline, `--seed` replaces `main.py`'s per-clip `torch.manual_seed(42)` (weight init, batch
order); the 1500-window subsample stays fixed by `main.py`'s `default_rng(42)`.
