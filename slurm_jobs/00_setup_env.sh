#!/bin/bash
# Run INTERACTIVELY, once, from the repo root on a shared server (10.4.64.27 or
# 10.4.64.28), NOT on panther-login (which kills stray long-running processes, e.g.
# conda) and NOT via sbatch. Creates the conda env and the two read-only code snapshots.
#   ssh 10.4.64.27; cd ~/learning_from_physics; bash slurm_jobs/00_setup_env.sh
#
# Code snapshots (the local working tree is never modified):
#   $WORK/code/iris-bench_ce61c63  public release, KurbanIntelligenceLab/iris-bench @ ce61c63
#   $WORK/code/dev_eae47d9         dev commit that added the Table 4 CSVs (git archive of the local repo)
_SJ="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"; _SJ="${_SJ%/slurm_jobs}/slurm_jobs"
export REPO="${_SJ%/slurm_jobs}"; source "$_SJ/common.sh"  # works under sbatch (submit from repo root or slurm_jobs/) and with plain bash

if [[ "$(hostname)" == *login* ]]; then
    echo "This is $(hostname): login nodes kill long-running processes (conda was killed here before)." >&2
    echo "Run it on a shared server instead: ssh 10.4.64.27 (or .28), then bash slurm_jobs/00_setup_env.sh" >&2
    exit 1
fi
if [ ! -d "$HOME/miniconda3" ] && [ -z "${CONDA_SH:-}" ]; then
    echo "miniconda3 not found at \$HOME/miniconda3 -- install it or export CONDA_SH." >&2
    exit 1
fi
source "${CONDA_SH:-$HOME/miniconda3/etc/profile.d/conda.sh}"
if conda env list | grep -q "^${ENV_NAME} "; then
    echo "Environment ${ENV_NAME} exists; updating packages only."
else
    conda create -y -n "${ENV_NAME}" python=3.12
fi
conda activate "${ENV_NAME}"
pip install -r "$REPO/repro_d75/requirements_repro.txt"

mkdir -p "$WORK/code"
if [ ! -d "$CODE_PUBLIC" ]; then
    git clone --quiet https://github.com/KurbanIntelligenceLab/iris-bench "$CODE_PUBLIC"
    git -C "$CODE_PUBLIC" -c advice.detachedHead=false checkout --quiet "$PUBLIC_COMMIT"
    git -C "$CODE_PUBLIC" rev-parse HEAD > "$CODE_PUBLIC/SNAPSHOT_COMMIT"
fi
if [ "$(git -C "$CODE_PUBLIC" rev-parse HEAD)" != "$PUBLIC_COMMIT" ]; then
    echo "ERROR: $CODE_PUBLIC is not at $PUBLIC_COMMIT" >&2
    exit 1
fi
if [ ! -d "$CODE_LEGACY" ]; then
    mkdir -p "$CODE_LEGACY"
    git -C "$REPO" archive "$LEGACY_COMMIT" | tar -x -C "$CODE_LEGACY"
    git -C "$REPO" rev-parse "$LEGACY_COMMIT" > "$CODE_LEGACY/SNAPSHOT_COMMIT"
fi

python - <<'EOF'
import torch, cv2, numpy, sklearn, omegaconf, wandb, yaml
print("torch", torch.__version__, "cuda build", torch.version.cuda, "| cuda available here:", torch.cuda.is_available())
print("cv2", cv2.__version__, "| numpy", numpy.__version__)
EOF
pip freeze > "$WORK/env_freeze.txt"

echo
echo "Setup done. Env: ${ENV_NAME}. Snapshots: $CODE_PUBLIC, $CODE_LEGACY"
echo "Next: put your Kaggle token at ~/.kaggle/kaggle.json (chmod 600), then run 01_download_data_cpu.sh."
echo "Check that the account/QOS lines in slurm_jobs/0[4-6]*.sh match this project:"
echo "  module load shared slurm && sacctmgr show assoc user=\$USER format=account,qos"
