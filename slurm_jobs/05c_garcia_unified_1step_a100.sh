#!/bin/bash -l
#SBATCH -J d75_garcia_unified_1step
#SBATCH -o d75_garcia_unified_1step_%j.out
#SBATCH -e d75_garcia_unified_1step_%j.err
#SBATCH -p gpu-A100
#SBATCH --gres=gpu:1
#SBATCH -c 8
#SBATCH --mem 60000MB
#SBATCH -A a100_hbku
#SBATCH -q a100_hbku_qos
#SBATCH -t 12:00:00
#
# Unified model (run_unified_delfys75.py, Table 4 'Corr.'), one-step.
# Garcia-protocol data (per-system stride / frames / dt, Garcia et al. CVPR 2025 Table 5), public code.
# As released it fits only the FIRST window of each clip (frames_used column).
#
# Output: Results/repro_d75/<config>/ (clips.csv with a status per clip, run.log,
# provenance.txt, param_logs/). Never overwrites: if the folder exists the job stops.
# Timed out? Resubmit with RESUME=1 (sbatch --export=ALL,RESUME=1 ...): finished clips are skipped.
_SJ="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"; _SJ="${_SJ%/slurm_jobs}/slurm_jobs"
export REPO="${_SJ%/slurm_jobs}"; source "$_SJ/common.sh"  # works under sbatch (submit from repo root or slurm_jobs/) and with plain bash
activate_env
python -c 'import torch; assert torch.cuda.is_available(), "no GPU visible"; print(torch.cuda.get_device_name(0))'

run_config g_unified_1step
