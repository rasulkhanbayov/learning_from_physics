#!/bin/bash -l
#SBATCH -J d75_preprocess
#SBATCH -o d75_preprocess_%j.out
#SBATCH -e d75_preprocess_%j.err
#SBATCH -p cpu-all
#SBATCH -c 16
#SBATCH --mem 64000MB
#SBATCH -t 08:00:00
#
# Videos -> .npy, then verification and SHA-256 manifests, for three datasets:
#   delfys75_garcia  MAIN: Garcia et al. (CVPR 2025) Table 5 per-system stride / frames per
#                    sample (pendulum, torricelli 6/20; LED 1/20; sliding block 2/10;
#                    dropped ball 2/4; free_fall bouncing-ball clips 1/10)
#   delfys75_s6      stride 6, 10 frames for all: the published runs' data. Dropped ball,
#                    free fall and sliding block clips are too short (< 60 frames) and are
#                    listed as too_short -- the cause of the 45 failed clips in Table 4.
#   delfys75_s3      stride 3, 10 frames, dt 0.05 s: the supplement's stated dt
# Also tests which stride produced the archived run's .npy files
# (Results/delfys75_1/delfys75.log), using the true frame counts.
#
# Fails without writing anything if a video path cannot be mapped to
# dynamics/setting/run; the error lists the paths. Clips too short for one
# 10-frame window are listed as "too_short" in the reports, never silently dropped.
_SJ="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"; _SJ="${_SJ%/slurm_jobs}/slurm_jobs"
export REPO="${_SJ%/slurm_jobs}"; source "$_SJ/common.sh"  # works under sbatch (submit from repo root or slurm_jobs/) and with plain bash
activate_env

[ -d "$DATA_RAW/extracted" ] || { echo "Run 01_download_data_cpu.sh first." >&2; exit 1; }
P=$(new_run_dir preprocessing)
write_provenance "$P" "preprocessing: garcia preset, stride 6, stride 3 from $DATA_RAW/extracted"
NW="${SLURM_CPUS_PER_TASK:-8}"

for SPEC in "garcia:--preset garcia" "s6:--stride 6" "s3:--stride 3"; do
    TAG="${SPEC%%:*}"; OPT=(${SPEC#*:})
    DST="$WORK/data/delfys75_$TAG"
    echo "=== $TAG (${OPT[*]}) -> $DST"
    python -I "$REPO/repro_d75/video2npy_fixed.py" --input_dir "$DATA_RAW/extracted" --output_dir "$DST" \
        "${OPT[@]}" --report "$P/preprocess_${TAG}_report.csv" --workers "$NW" 2>&1 | tee -a "$P/preprocess.log"
    python -I "$REPO/repro_d75/verify_npy.py" --root "$DST" --manifest "$DST.sha256.tsv" \
        --report "$P/preprocess_${TAG}_report.csv" 2>&1 | tee -a "$P/verify.log"
    cp "$DST.sha256.tsv" "$P/"
    cp "$DST/protocol.json" "$P/protocol_${TAG}.json"
done

echo "=== Which stride produced the archived run's .npy files?"
python -I "$REPO/repro_d75/stride_evidence.py" --log "$REPO/Results/delfys75_1/delfys75.log" \
    --report "$P/preprocess_s6_report.csv" --out "$P/stride_evidence.csv" | tee "$P/stride_evidence.txt"

echo "=== Ground truth"
mapfile -t GT_FILES < <(find "$DATA_RAW/extracted" -type f -iname 'parameters*.json')
if [ "${#GT_FILES[@]}" -eq 1 ]; then
    cp "${GT_FILES[0]}" "$P/parameters.json"
    # Prints a WARNING for every value that differs from the GT used in the released comparison files.
    python "$REPO/scripts/evaluate_delfys75.py" --params "$P/parameters.json" --write_gt_json "$P/gt_used.json" | tee "$P/gt_check.txt"
else
    echo "Found ${#GT_FILES[@]} parameters*.json files: ${GT_FILES[*]:-none}. Using the built-in GT (delfys75_audit/reproducibility.md 5.1)." | tee "$P/gt_check.txt"
    python "$REPO/scripts/evaluate_delfys75.py" --write_gt_json "$P/gt_used.json"
fi

echo
echo "Preprocessing done. Before any GPU job, check in $P:"
echo "  verify.log says 'All files OK.' three times"
echo "  preprocess_garcia_report.csv: all 90 clips ok; s6 report: 45 too_short (expected)"
echo "  stride_evidence.txt: which stride matches the archived run"
echo "  gt_check.txt: only the two expected Torricelli k rounding WARNINGs (medium, small)"
