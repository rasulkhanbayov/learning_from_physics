# Delfys75 audit and reproduction (IRIS paper, Tables 4 and 5), October 2026

Private working record of the audit and re-run of the Delfys75 results. The public, reduced
version is in [KurbanIntelligenceLab/iris-bench](https://github.com/KurbanIntelligenceLab/iris-bench)
(`REPRODUCE_DELFYS75.md`, `repro_d75/`, `Results/repro_d75/`).

## Where things are

| Path | Content |
|---|---|
| `delfys75_audit/reproducibility.md` | audit notes written before the re-runs (hypotheses and plan; the re-runs below settle them) |
| `slurm_jobs/` | all cluster jobs, run in the order given in `slurm_jobs/RUN_ORDER.md` (00–08); `common.sh` holds paths and run configurations |
| `repro_d75/` | tools: fixed-stride preprocessing (`video2npy_fixed.py`), checks (`verify_npy.py`, `stride_evidence.py`), clip-by-clip runners (`run_baseline.py`, `run_unified.py`), pinned `requirements_repro.txt` |
| `scripts/evaluate_delfys75.py` | evaluator (model-specific mappings, failed clips excluded, init and seed summaries) |
| `Results/repro_d75/<run>/` | one folder per run: `clips.csv` (per-clip status and estimates), `run.log`, `provenance.txt`, `pip_freeze.txt` |
| `Results/repro_d75/preprocessing/` | per-clip frame and sample reports, SHA-256 manifests, `stride_evidence.txt`, ground truth (`parameters.json`, `gt_used.json`) |
| `Results/repro_d75/validation_old_csvs/` | evaluator checked against the released CSVs (18/18) |
| `Results/repro_d75/evaluation/`, `evaluation_v2/` | evaluations of all runs (v2 adds seeds and the published-setting re-run of both Table 4 columns) |
| `Results/repro_d75/job_logs/` | SLURM stdout/stderr of every job |
| `paper/` | paper and supplement PDFs and sources, drafts, rebuttal, slides |

## Run names

| Prefix | Meaning |
|---|---|
| `g_` | Garcia et al. per-system protocol (stride / frames / Δt per system) |
| `s6_legacy_eae47d9_*_dt0.05` | published Table 4 setting: code at `eae47d9`, stride 6, `--dt 0.05` |
| `s3_` | stride 3, Δt 0.05 for all systems |
| `_init5` / `_init20` | physics parameters initialised at 5 / 20 instead of 10 |
| `_seed1` / `_seed2` | seeds 1 / 2 instead of 42 |

## Main results

- **Stride.** All 45 clips with a logged shape in the archived run match stride 6, while training used `--dt 0.05` (`preprocessing/stride_evidence.txt`).
- **Table 4 "Base."** reproduces with the released scoring script: 95.54 / 50.87 / 29.65 vs 95.07 / 50.15 / 29.83 (`evaluation_v2/old_script_table4_published_setting_*`).
- **Table 4 "Corr."** does not reproduce. The unified runs were unseeded, and the results vary strongly between seeds.
- **Table 5** regenerates exactly from the released CSVs (`validation_old_csvs/checks.txt`).
- **Seed and init dependence** are in `evaluation_v2/new_evaluator/seed_summary.txt` and `init_sensitivity_summary.txt`.

## Not in git

`repro_d75_work/` (~39 GB) holds the Kaggle download, the `.npy` datasets and the code snapshots. To regenerate it:

1. `bash slurm_jobs/00_setup_env.sh` (code snapshots and conda env);
2. `01_download_data_cpu.sh` (Kaggle v11; zip SHA-256 in `Results/repro_d75/preprocessing/`);
3. `02_preprocess_verify_cpu.sh` (rebuilds the `.npy` files and checks them against the committed manifests).

The per-run `work/` folders (checkpoints, plots) and `param_logs/` (per-epoch JSON) are also excluded.

The tool hashes in `provenance.txt` are of the versions at run time, so later edits make them differ from the current files. Some tools gained options after the early runs (`--seed` in `run_baseline.py`, `--seed_group` in the evaluator), with defaults unchanged; other edits changed comments only, for example the path to `reproducibility.md`.
