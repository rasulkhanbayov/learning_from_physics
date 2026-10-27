#!/bin/bash -l
#SBATCH -J d75_evaluate
#SBATCH -o d75_evaluate_%j.out
#SBATCH -e d75_evaluate_%j.err
#SBATCH -p cpu-all
#SBATCH -c 2
#SBATCH --mem 8000MB
#SBATCH -t 00:30:00
#
# After 05a-05d and 06a-06d: evaluate every new run.
#   evaluation/new_evaluator/      model-specific mappings, failed runs excluded, n_ok/n_total
#                                  (summary.txt, summary.csv, per_clip_errors.csv, table4_rows.tex,
#                                  table5_rows.tex, all_rows.tex, init_sensitivity_*.{csv,txt})
#   evaluation/old_script_*/       released compare_baseline_unified.py on the same runs
#                                  (successful clips only), for side-by-side comparison with the paper
# Stops if a run is missing; set ALLOW_PARTIAL=1 to evaluate whatever exists.
# Second evaluation after the 08* jobs (seeds, legacy unified), into a new folder:
#   sbatch --export=ALL,EVAL_NAME=evaluation_v2 slurm_jobs/07_evaluate_cpu.sh
_SJ="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"; _SJ="${_SJ%/slurm_jobs}/slurm_jobs"
export REPO="${_SJ%/slurm_jobs}"; source "$_SJ/common.sh"  # works under sbatch (submit from repo root or slurm_jobs/) and with plain bash
activate_env

RUNS=(  # evaluator name : config folder : model
    "base1:g_base_1step:baseline"
    "basem:g_base_multi:baseline"
    "unif1:g_unified_1step:unified"
    "unifm:g_unified_multi:unified"
    "base1_init5:g_base_1step_init5:baseline"
    "base1_init20:g_base_1step_init20:baseline"
    "legacy_dt005:s6_legacy_eae47d9_base_1step_dt0.05:baseline"
    "s3_base1:s3_base_1step:baseline"
    "s3_unif1:s3_unified_1step:unified"
)
OPTIONAL=(  # added after the first evaluation (08* jobs); used when present
    "base1_s1:g_base_1step_seed1:baseline"
    "base1_s2:g_base_1step_seed2:baseline"
    "basem_s1:g_base_multi_seed1:baseline"
    "basem_s2:g_base_multi_seed2:baseline"
    "unif1_s1:g_unified_1step_seed1:unified"
    "unif1_s2:g_unified_1step_seed2:unified"
    "legacy_unif_dt005:s6_legacy_eae47d9_unified_1step_dt0.05:unified"
)
ARGS=(); MISSING=(); PRESENT=" "
for r in "${OPTIONAL[@]}"; do
    IFS=: read -r name cfg model <<< "$r"
    if [ -f "$OUT/$cfg/clips.csv" ]; then ARGS+=(--run "$name=$OUT/$cfg/clips.csv:$model"); PRESENT+="$name "; fi
done
for r in "${RUNS[@]}"; do
    IFS=: read -r name cfg model <<< "$r"
    if [ -f "$OUT/$cfg/clips.csv" ]; then
        ARGS+=(--run "$name=$OUT/$cfg/clips.csv:$model")
    else
        MISSING+=("$cfg")
    fi
done
if [ "${#MISSING[@]}" -gt 0 ]; then
    echo "Missing runs: ${MISSING[*]}" >&2
    [ "${ALLOW_PARTIAL:-0}" = "1" ] || { echo "Set ALLOW_PARTIAL=1 to evaluate the others." >&2; exit 1; }
fi

E=$(new_run_dir "${EVAL_NAME:-evaluation}")
write_provenance "$E" "evaluation of: ${ARGS[*]}"
GT="$OUT/preprocessing/gt_used.json"
[ -f "$GT" ] || { echo "No $GT: run 02 first." >&2; exit 1; }
PARAMS=()
if [ -f "$OUT/preprocessing/parameters.json" ]; then PARAMS=(--params "$OUT/preprocessing/parameters.json"); fi

INIT=()
if [ -f "$OUT/g_base_1step_init5/clips.csv" ] && [ -f "$OUT/g_base_1step_init20/clips.csv" ] && [ -f "$OUT/g_base_1step/clips.csv" ]; then
    INIT=(--init_runs base1_init5,base1,base1_init20)
fi

SEEDS=()
for g in base1 basem unif1; do
    if [[ "$PRESENT" == *" ${g}_s1 "* && "$PRESENT" == *" ${g}_s2 "* ]]; then SEEDS+=(--seed_group "$g=$g,${g}_s1,${g}_s2"); fi
done

python "$REPO/scripts/evaluate_delfys75.py" "${ARGS[@]}" "${PARAMS[@]}" "${INIT[@]}" "${SEEDS[@]}" --out "$E/new_evaluator" | tee "$E/new_evaluator.txt"

old_script() {  # NAME BASELINE_CFG SECOND_CFG: the released script, as used for the paper tables
    local n="$1" b="$OUT/$2/mainpy_format_ok_only.csv" u="$OUT/$3/mainpy_format_ok_only.csv"
    if [ -f "$b" ] && [ -f "$u" ]; then
        python "$CODE_PUBLIC/scripts/compare_baseline_unified.py" --baseline "$b" --unified "$u" \
            --params "$GT" --out "$E/old_script_$n" > /dev/null
        echo "old script ($n): $E/old_script_$n/parameter_errors_comparison.txt"
    fi
}
old_script table4_like_base1_vs_unif1 g_base_1step g_unified_1step
old_script table4_like_legacy_vs_unif1 s6_legacy_eae47d9_base_1step_dt0.05 g_unified_1step
old_script table5_like_base1_vs_basem g_base_1step g_base_multi
# Both published Table 4 columns re-run in the published setting, scored by the released script:
old_script table4_published_setting_legacy_base_vs_legacy_unified s6_legacy_eae47d9_base_1step_dt0.05 s6_legacy_eae47d9_unified_1step_dt0.05

echo
echo "Status counts per run (clips not ok are excluded from the MAE and listed in clips.csv):"
for r in "${RUNS[@]}" "${OPTIONAL[@]}"; do
    IFS=: read -r name cfg model <<< "$r"
    if [ -f "$OUT/$cfg/clips.csv" ]; then
        python - "$OUT/$cfg/clips.csv" "$cfg" <<'EOF'
import csv, sys, collections
c = collections.Counter(r["status"] for r in csv.DictReader(open(sys.argv[1])))
print(f"  {sys.argv[2]:<42}{dict(c)}")
EOF
    fi
done | tee "$E/status_counts.txt"
echo "Evaluation done: start with $E/new_evaluator/summary.txt"
