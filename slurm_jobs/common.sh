#!/bin/bash
# Sourced by every slurm_jobs/*.sh; not run on its own. Paths, environment,
# provenance logging, and the table of run configurations.
set -euo pipefail

REPO="${REPO:-${SLURM_SUBMIT_DIR:-$PWD}}"; REPO="${REPO%/slurm_jobs}"  # submit from the repo root (or slurm_jobs/); or export REPO
cd "$REPO"
if [ ! -f "$REPO/repro_d75/run_baseline.py" ]; then
    echo "REPO=$REPO does not look like the learning_from_physics repo root." >&2
    exit 1
fi

ENV_NAME="iris_d75_repro"
WORK="${D75_WORK:-$REPO/repro_d75_work}"   # code snapshots + data; large, keep out of git
OUT="$REPO/Results/repro_d75"              # every new result goes here; existing Results/ folders are never touched
CODE_PUBLIC="$WORK/code/iris-bench_ce61c63"
CODE_LEGACY="$WORK/code/dev_eae47d9"
PUBLIC_COMMIT="ce61c635db1ac90d770421cc97ba02f8626b6d16"  # iris-bench main, 2026-09-24
LEGACY_COMMIT="eae47d9"                                    # dev commit that added the Table 4 CSVs
DATA_RAW="$WORK/data/raw"
DATA_G="$WORK/data/delfys75_garcia"  # MAIN: Garcia et al. per-system stride/frames (protocol.json)
DATA_S6="$WORK/data/delfys75_s6"     # stride 6, 10 frames, all systems: what the published runs used
DATA_S3="$WORK/data/delfys75_s3"     # stride 3, 10 frames, dt 0.05 s: the supplement's stated dt

export WANDB_MODE=disabled
export MPLBACKEND=Agg
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
export PYTHONHASHSEED=42

activate_env() {
    source "${CONDA_SH:-$HOME/miniconda3/etc/profile.d/conda.sh}"
    conda activate "$ENV_NAME"
    # Deliberately no `module load cuda` -- the pip torch wheel bundles its own CUDA runtime.
}

# new_run_dir NAME -> creates $OUT/NAME and prints it. Fails if it exists (RESUME=1 to continue).
new_run_dir() {
    local d="$OUT/$1"
    if [ -e "$d" ] && [ "${RESUME:-0}" != "1" ]; then
        echo "ERROR: $d already exists. Results are never overwritten: move it away," >&2
        echo "or set RESUME=1 to continue an interrupted run (finished clips are skipped)." >&2
        exit 1
    fi
    mkdir -p "$d"
    echo "$d"
}

# write_provenance DIR DESCRIPTION...
write_provenance() {
    local d="$1" c m; shift
    {
        echo "description: $*"
        echo "date: $(date -Is)"
        echo "host: $(hostname)  slurm_job: ${SLURM_JOB_ID:-none}  partition: ${SLURM_JOB_PARTITION:-none}"
        echo "repo_commit: $(git -C "$REPO" rev-parse HEAD)  uncommitted_files: $(git -C "$REPO" status --porcelain | wc -l)"
        for c in "$CODE_PUBLIC" "$CODE_LEGACY"; do
            if [ -f "$c/SNAPSHOT_COMMIT" ]; then echo "code_snapshot $(basename "$c"): $(cat "$c/SNAPSHOT_COMMIT")"; fi
        done
        echo "gpu: $(nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>/dev/null | head -1 || true)"
        python -c 'import sys,torch,numpy,cv2;print("python",sys.version.split()[0],"| torch",torch.__version__,"| cuda",torch.version.cuda,"| cudnn",torch.backends.cudnn.version(),"| numpy",numpy.__version__,"| cv2",cv2.__version__,"| cuda_available",torch.cuda.is_available())'
        for m in "$DATA_G.sha256.tsv" "$DATA_S6.sha256.tsv" "$DATA_S3.sha256.tsv"; do
            if [ -f "$m" ]; then echo "data_manifest $(basename "$m"): sha256 $(sha256sum "$m" | cut -c1-16)"; fi
        done
        echo "tool_hashes:"
        (cd "$REPO" && sha256sum repro_d75/*.py scripts/evaluate_delfys75.py slurm_jobs/*.sh)
    } > "$d/provenance.txt"
    pip freeze > "$d/pip_freeze.txt"
}

# run_config NAME [--only dyn/setting/run ...]: one training configuration, one GPU.
run_config() {
    local name="$1"; shift
    local kind code data dt loss="" extra=()
    case "$name" in
        # dt=protocol: per-system dt (stride/60) from $DATA_G/protocol.json
        g_base_1step)           kind=baseline; code=$CODE_PUBLIC; data=$DATA_G;  dt=protocol; loss=latent_loss ;;
        g_base_multi)           kind=baseline; code=$CODE_PUBLIC; data=$DATA_G;  dt=protocol; loss=latent_loss_multistep ;;
        g_base_1step_init5)     kind=baseline; code=$CODE_PUBLIC; data=$DATA_G;  dt=protocol; loss=latent_loss; extra=(--init_phys 5) ;;
        g_base_1step_init20)    kind=baseline; code=$CODE_PUBLIC; data=$DATA_G;  dt=protocol; loss=latent_loss; extra=(--init_phys 20) ;;
        g_unified_1step)        kind=unified;  code=$CODE_PUBLIC; data=$DATA_G;  dt=protocol ;;
        g_unified_multi)        kind=unified;  code=$CODE_PUBLIC; data=$DATA_G;  dt=protocol; extra=(--multistep) ;;
        s6_legacy_eae47d9_base_1step_dt0.05)
                                kind=baseline; code=$CODE_LEGACY; data=$DATA_S6; dt=0.05; loss=latent_loss ;;
        s3_base_1step)          kind=baseline; code=$CODE_PUBLIC; data=$DATA_S3; dt=0.05; loss=latent_loss ;;
        s3_unified_1step)       kind=unified;  code=$CODE_PUBLIC; data=$DATA_S3; dt=0.05 ;;
        # Added after the first evaluation: seeds 1 and 2 for the main runs, and the published
        # "Corr." setting (unified model, eae47d9, stride-6 data, dt 0.05).
        g_base_1step_seed1)     kind=baseline; code=$CODE_PUBLIC; data=$DATA_G;  dt=protocol; loss=latent_loss; extra=(--seed 1) ;;
        g_base_1step_seed2)     kind=baseline; code=$CODE_PUBLIC; data=$DATA_G;  dt=protocol; loss=latent_loss; extra=(--seed 2) ;;
        g_base_multi_seed1)     kind=baseline; code=$CODE_PUBLIC; data=$DATA_G;  dt=protocol; loss=latent_loss_multistep; extra=(--seed 1) ;;
        g_base_multi_seed2)     kind=baseline; code=$CODE_PUBLIC; data=$DATA_G;  dt=protocol; loss=latent_loss_multistep; extra=(--seed 2) ;;
        g_unified_1step_seed1)  kind=unified;  code=$CODE_PUBLIC; data=$DATA_G;  dt=protocol; extra=(--seed 1) ;;
        g_unified_1step_seed2)  kind=unified;  code=$CODE_PUBLIC; data=$DATA_G;  dt=protocol; extra=(--seed 2) ;;
        s6_legacy_eae47d9_unified_1step_dt0.05)
                                kind=unified;  code=$CODE_LEGACY; data=$DATA_S6; dt=0.05 ;;
        smoke_*)                kind="${SMOKE_KIND:?}"; code=$CODE_PUBLIC; data=$DATA_G; dt=protocol; loss=latent_loss ;;
        *) echo "unknown configuration: $name" >&2; exit 1 ;;
    esac
    [ -f "$code/SNAPSHOT_COMMIT" ] || { echo "Code snapshot $code missing: run 00_setup_env.sh first." >&2; exit 1; }
    [ -f "$data.sha256.tsv" ] || { echo "No verified data at $data: run 02_preprocess_verify_cpu.sh first." >&2; exit 1; }

    local d; d=$(new_run_dir "$name")
    write_provenance "$d" "$name: kind=$kind code=$(basename "$code") data=$(basename "$data") dt=$dt loss=${loss:-n/a} extra=${extra[*]:-none} seed=42 unless --seed in extra; args=$*"
    local resume=()
    if [ "${RESUME:-0}" = "1" ]; then resume=(--resume); fi

    echo "=== $name -> $d"
    set +e
    if [ "$kind" = baseline ]; then
        python -u "$REPO/repro_d75/run_baseline.py" --code_dir "$code" --data_root "$data" --dt "$dt" \
            --loss "$loss" --out_dir "$d" "${extra[@]}" "${resume[@]}" "$@" 2>&1 | tee -a "$d/run.log"
    else
        python -u "$REPO/repro_d75/run_unified.py" --code_dir "$code" --data_root "$data" --dt "$dt" \
            --seed 42 --out_dir "$d" "${extra[@]}" "${resume[@]}" "$@" 2>&1 | tee -a "$d/run.log"
    fi
    local rc=${PIPESTATUS[0]}
    set -e
    case $rc in
        0) echo "[$name] finished: all clips ok -> $d/clips.csv" ;;
        3) echo "[$name] finished, but some clips are NOT ok (expected for some systems)." >&2
           echo "       Read the status and error columns of $d/clips.csv." >&2 ;;
        *) echo "[$name] CRASHED (exit $rc); see $d/run.log. Fix, then rerun with RESUME=1." >&2
           exit "$rc" ;;
    esac
}
