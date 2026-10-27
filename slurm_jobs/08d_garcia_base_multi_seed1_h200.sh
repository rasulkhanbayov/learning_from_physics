#!/bin/bash -l
#SBATCH -J d75_garcia_base_multi_seed1
#SBATCH -o d75_garcia_base_multi_seed1_%j.out
#SBATCH -e d75_garcia_base_multi_seed1_%j.err
#SBATCH -p gpu-H200
#SBATCH --gres=gpu:1
#SBATCH -c 8
#SBATCH --mem 60000MB
#SBATCH -A h200_hbku
#SBATCH -q h200_hbku_qos
#SBATCH -t 2-00:00:00
#
# As 05b with seed 1.
#
# Output: Results/repro_d75/<config>/. Never overwrites; timed out -> resubmit with RESUME=1.
_SJ="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"; _SJ="${_SJ%/slurm_jobs}/slurm_jobs"
export REPO="${_SJ%/slurm_jobs}"; source "$_SJ/common.sh"  # works under sbatch (submit from repo root or slurm_jobs/) and with plain bash
activate_env
python -c 'import torch; assert torch.cuda.is_available(), "no GPU visible"; print(torch.cuda.get_device_name(0))'

run_config g_base_multi_seed1
