#!/bin/bash -l
#SBATCH -J d75_s6_legacy_eae47d9_dt005
#SBATCH -o d75_s6_legacy_eae47d9_dt005_%j.out
#SBATCH -e d75_s6_legacy_eae47d9_dt005_%j.err
#SBATCH -p gpu-H200
#SBATCH --gres=gpu:1
#SBATCH -c 8
#SBATCH --mem 60000MB
#SBATCH -A h200_hbku
#SBATCH -q h200_hbku_qos
#SBATCH -t 2-12:00:00
#
# LEGACY: dev commit eae47d9 code on stride-6 / 10-frame data with --dt 0.05: the setting that
# produced Table 4 'Base.' (audit). Dropped ball, free fall and sliding block have no .npy at
# stride 6 (too short), so only 45 clips run -- as in the published run. No 1500-sample cap in
# this code version, so it is the slowest job.
#
# Output: Results/repro_d75/<config>/ (clips.csv with a status per clip, run.log,
# provenance.txt, param_logs/). Never overwrites: if the folder exists the job stops.
# Timed out? Resubmit with RESUME=1 (sbatch --export=ALL,RESUME=1 ...): finished clips are skipped.
_SJ="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"; _SJ="${_SJ%/slurm_jobs}/slurm_jobs"
export REPO="${_SJ%/slurm_jobs}"; source "$_SJ/common.sh"  # works under sbatch (submit from repo root or slurm_jobs/) and with plain bash
activate_env
python -c 'import torch; assert torch.cuda.is_available(), "no GPU visible"; print(torch.cuda.get_device_name(0))'

run_config s6_legacy_eae47d9_base_1step_dt0.05
