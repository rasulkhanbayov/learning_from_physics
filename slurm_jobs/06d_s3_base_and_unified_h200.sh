#!/bin/bash -l
#SBATCH -J d75_s3_base_and_unified
#SBATCH -o d75_s3_base_and_unified_%j.out
#SBATCH -e d75_s3_base_and_unified_%j.err
#SBATCH -p gpu-H200
#SBATCH --gres=gpu:1
#SBATCH -c 8
#SBATCH --mem 60000MB
#SBATCH -A h200_hbku
#SBATCH -q h200_hbku_qos
#SBATCH -t 2-12:00:00
#
# Sensitivity: stride 3 / 10 frames / dt 0.05 (the supplement's stated dt, used consistently),
# baseline then unified (one-step), sequentially on one GPU. Free fall and most dropped-ball
# clips are too short at stride 3 (listed in the preprocessing report).
#
# Output: Results/repro_d75/<config>/ (clips.csv with a status per clip, run.log,
# provenance.txt, param_logs/). Never overwrites: if the folder exists the job stops.
# Timed out? Resubmit with RESUME=1 (sbatch --export=ALL,RESUME=1 ...): finished clips are skipped.
_SJ="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"; _SJ="${_SJ%/slurm_jobs}/slurm_jobs"
export REPO="${_SJ%/slurm_jobs}"; source "$_SJ/common.sh"  # works under sbatch (submit from repo root or slurm_jobs/) and with plain bash
activate_env
python -c 'import torch; assert torch.cuda.is_available(), "no GPU visible"; print(torch.cuda.get_device_name(0))'

run_config s3_base_1step
run_config s3_unified_1step
