#!/bin/bash -l
#SBATCH -J d75_legacy_unified_and_unified_seeds
#SBATCH -o d75_legacy_unified_and_unified_seeds_%j.out
#SBATCH -e d75_legacy_unified_and_unified_seeds_%j.err
#SBATCH -p gpu-A100
#SBATCH --gres=gpu:1
#SBATCH -c 8
#SBATCH --mem 60000MB
#SBATCH -A a100_hbku
#SBATCH -q a100_hbku_qos
#SBATCH -t 06:00:00
#
# (1) The published Table 4 'Corr.' setting: unified model, eae47d9 code, stride-6 data,
# --dt 0.05. With 06c this reproduces BOTH Table 4 columns. (2) Unified 1-step, seeds 1, 2.
# All three are fast (minutes each).
#
# Output: Results/repro_d75/<config>/. Never overwrites; timed out -> resubmit with RESUME=1.
_SJ="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"; _SJ="${_SJ%/slurm_jobs}/slurm_jobs"
export REPO="${_SJ%/slurm_jobs}"; source "$_SJ/common.sh"  # works under sbatch (submit from repo root or slurm_jobs/) and with plain bash
activate_env
python -c 'import torch; assert torch.cuda.is_available(), "no GPU visible"; print(torch.cuda.get_device_name(0))'

run_config s6_legacy_eae47d9_unified_1step_dt0.05
run_config g_unified_1step_seed1
run_config g_unified_1step_seed2
