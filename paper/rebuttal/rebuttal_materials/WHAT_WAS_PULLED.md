# Rebuttal materials pulled from rasulkhanbayov/learning_from_physics

Source: https://github.com/rasulkhanbayov/learning_from_physics (public, main branch)
Pulled: 2026-06-27

## Files in that repo NOT present in your local folders

These exist in the public repo but are **missing** from both
`Desktop\learning_from_physics` (raw) and `Desktop\KIL\learning_from_physics` (clean):

| File | What it is | Status |
|---|---|---|
| `run_hitting_cones_kappa_experiment.py` | **κ=0 vs κ=learned experiment** → backs **Rebuttal Tab. 3 right** (MSE reduces 6–19%) | ✅ PULLED (full, verbatim) |
| `reviews.txt` | Raw reviewer comments (MCJw=5 WA, PXn6=3 BR, bRfX=3 BR) | ⚠️ summary only — pull manually |
| `rebuttal.tex` | Rebuttal LaTeX source | ⚠️ pull manually (too long for fetch) |
| `new_rebuttal.tex` | Newer rebuttal LaTeX | ⚠️ pull manually |
| `new_rebt_rasul.tex` | Your rebuttal edit | ⚠️ pull manually |

## Why `run_hitting_cones_kappa_experiment.py` matters

This is one of the THREE missing rebuttal experiments I flagged earlier. It is the
**κ ablation** promised to reviewers (Rebuttal Tab. 3, right: "κ reduces MSE 6.0–19.0%").
It generates synthetic hitting-cones data from the free_fall ODE with known κ, trains
κ=0 vs κ=learned, and writes `Results/hitting_cones_reconstruction/` (CSV + LaTeX table +
κ-consistency stats).

⚠️ **Edit needed before reuse:** line ~30 hardcodes `REPO = "/home/ubuntu/learning_from_physics"`
(a cloud path). Change it to your repo root, or make it `os.path.dirname(__file__)`-relative,
before running.

## UPDATE — all rebuttal assets traced to commit 1f96b06

The commit **`1f96b06` "Add ECCV 2026 rebuttal files and experiment results" (2026-05-21)**
added everything. Status of the THREE rebuttal experiments:

| Rebuttal table | Script | Result files | Where |
|---|---|---|---|
| **Tab. 3 right** (κ=0 vs learned) | `run_hitting_cones_kappa_experiment.py` | `Results/hitting_cones_reconstruction/{reconstruction_comparison.csv, kappa_consistency.csv, table_reconstruction.tex}` | ✅ script PULLED here; CSVs must be copied from repo |
| **Tab. 3 left** (multi-clip vs per-clip) | `scripts/run_multi_clip_iris.py` | `Results/iris_multi_clip/{iris_multi_clip.csv, per_clip_on_test_split.csv, table_iris_multi_clip.tex}` + `Results/iris_multi_clip_run.log` | ⚠️ in repo, NOT pulled (too long for fetch) — clone it |
| **Tab. 2** (4K vs 1080p resolution) | **NONE** | **NONE** | ❌ does not exist anywhere — must locate or REGENERATE |

### ⚠️ Tab. 2 (resolution) is the real gap
The 4K-vs-1080p MAE numbers in Rebuttal Tab. 2 (Dropping ball +5.2%, Pendulum +12.1%,
Two Moving Pend(1S) +7.1%) were produced by a script that was **never committed**.
No `*resolution*` / `*1080*` / `*downsample*` file exists in the public repo or your
local folders. Before camera-ready, either find that script on whatever machine ran it,
or regenerate it (downsample IRIS 4K → 1080p, rerun parameter estimation, compute MAE delta).

### Get the multi-clip script + all result CSVs (clone is easiest)
```
git clone https://github.com/rasulkhanbayov/learning_from_physics _tmp_pull
# rebuttal experiment scripts + results
cp _tmp_pull/scripts/run_multi_clip_iris.py        ./rebuttal_materials/
cp -r _tmp_pull/Results/iris_multi_clip            ./rebuttal_materials/
cp -r _tmp_pull/Results/hitting_cones_reconstruction ./rebuttal_materials/
# rebuttal docs
cp _tmp_pull/rebuttal.tex _tmp_pull/new_rebuttal.tex _tmp_pull/new_rebt_rasul.tex \
   _tmp_pull/reviews.txt   ./rebuttal_materials/
rm -rf _tmp_pull
```

Note: `run_multi_clip_iris.py` covers 5 phenomena (Dropping_ball, Pendulum, Rotation,
Sliding_cone, Falling_ball), 80/20 split, trains one shared encoder+physics on all train
clips vs per-clip baseline. Like the kappa script, check it for any hardcoded cloud paths
before running.

## IMPORTANT — CNN accuracy discrepancy is RESOLVED by the rebuttal

Earlier I flagged: repo eval says CNN = 100%, but paper says 98.40 / 99.30.
`new_rebuttal.tex` clarifies: **held-out CNN accuracy is actually 100% (48/48)**,
and the "≈99%" in the submitted paper was a conservative figure.
→ For camera-ready, align the paper to **100%** (matching the committed eval), OR keep
99.30% and note it — but the rebuttal already committed to 100% to reviewers, so use 100%.

## Manual pull instructions (for the .tex + reviews.txt)

WebFetch can't return long files verbatim. Get them directly:

```
# clone just to grab the files, then copy what you want
git clone https://github.com/rasulkhanbayov/learning_from_physics _tmp_pull
cp _tmp_pull/rebuttal.tex _tmp_pull/new_rebuttal.tex _tmp_pull/new_rebt_rasul.tex \
   _tmp_pull/reviews.txt  ./rebuttal_materials/
rm -rf _tmp_pull
```

(or download each via the GitHub "Raw" button)
