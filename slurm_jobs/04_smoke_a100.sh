#!/bin/bash -l
#SBATCH -J d75_smoke
#SBATCH -o d75_smoke_%j.out
#SBATCH -e d75_smoke_%j.err
#SBATCH -p gpu-A100
#SBATCH --gres=gpu:1
#SBATCH -c 8
#SBATCH --mem 60000MB
#SBATCH -A a100_hbku
#SBATCH -q a100_hbku_qos
#SBATCH -t 03:00:00
#
# End-to-end check on 2 real clips at full length (500 epochs) before the 8 big jobs:
# the largest clip and the first dropped_ball/large clip of the main (Garcia-protocol)
# data, through the baseline and the unified model (public code, per-system dt). Prints seconds per clip and
# a rough wall-clock estimate for 05*/06*. Results go to Results/repro_d75/smoke_*.
_SJ="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"; _SJ="${_SJ%/slurm_jobs}/slurm_jobs"
export REPO="${_SJ%/slurm_jobs}"; source "$_SJ/common.sh"  # works under sbatch (submit from repo root or slurm_jobs/) and with plain bash
activate_env
nvidia-smi -L
python -c 'import torch; assert torch.cuda.is_available(), "no GPU visible"; print(torch.cuda.get_device_name(0))'

M="$DATA_G.sha256.tsv"
[ -f "$M" ] || { echo "Run 02_preprocess_verify_cpu.sh first." >&2; exit 1; }
BIG=$(awk -F'\t' 'NR>1 {split($2,s,"x"); print s[1]"\t"$1}' "$M" | sort -k1,1nr | head -1 | cut -f2 | cut -d/ -f1-3)
DROP=$(awk -F'\t' 'NR>1 && $1 ~ /^dropped_ball\/large\// {print $1}' "$M" | head -1 | cut -d/ -f1-3)
ONLY=(--only "$BIG")
if [ -n "$DROP" ]; then ONLY+=(--only "$DROP"); else echo "WARNING: no dropped_ball/large clip in the main data" >&2; fi
echo "Smoke clips: ${ONLY[*]}"
TAG="${SLURM_JOB_ID:-manual$(date +%s)}"

SMOKE_KIND=baseline run_config "smoke_${TAG}_baseline" "${ONLY[@]}"
SMOKE_KIND=unified  run_config "smoke_${TAG}_unified"  "${ONLY[@]}"

python - "$M" "$OUT/smoke_${TAG}_baseline/clips.csv" "$OUT/smoke_${TAG}_unified/clips.csv" <<'EOF'
import csv, sys
man = [l.rstrip("\n").split("\t") for l in open(sys.argv[1])][1:]
n_all = [int(r[1].split("x")[0]) for r in man]
b = list(csv.DictReader(open(sys.argv[2])))
u = list(csv.DictReader(open(sys.argv[3])))
for r in b + u:
    print(f"{r['dynamics']}/{r['setting']}/{r['run']}: status={r['status']} {r['seconds']} s {r['error']}")
# Baseline cost ~ samples per clip (capped at 1500 in the public code, uncapped in eae47d9).
ok = [r for r in b if r["status"] == "ok"]
if not ok:
    sys.exit("No baseline smoke clip finished ok: read the error column above before submitting anything.")
rate = max(float(r["seconds"]) / min(int(r["n_samples"]), 1500) for r in ok)
pub = sum(min(n, 1500) for n in n_all) * rate / 3600
leg = sum(n for n in n_all) * rate / 3600
uni = max(float(r["seconds"]) for r in u) * len(n_all) / 3600
print(f"Rough estimate per job on this GPU: baseline (public) {pub:.1f} h, legacy eae47d9 {leg:.1f} h, unified {uni:.2f} h")
print("Walltime requested in 05*/06*: 2 days (baseline), 12 h (unified). Raise -t if the estimate is close.")
EOF
echo "Smoke test done. If both statuses are ok, submit 05a-05d and 06a-06d."
