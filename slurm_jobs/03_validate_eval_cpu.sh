#!/bin/bash -l
#SBATCH -J d75_validate_eval
#SBATCH -o d75_validate_eval_%j.out
#SBATCH -e d75_validate_eval_%j.err
#SBATCH -p cpu-all
#SBATCH -c 2
#SBATCH --mem 4000MB
#SBATCH -t 00:20:00
#
# Validates the new evaluator (scripts/evaluate_delfys75.py) on the OLD released
# CSVs before trusting it on new runs. Needs no data or GPU; can run any time after 00.
#   1. New evaluator on the Table 4 and Table 5 source CSVs must reproduce:
#      - delfys75_audit/reproducibility.md 3.3 "model-consistent" baseline: pendulum 0.347/0.708/1.187, LED 7.449
#      - every printed Table 5 value (both columns), which shows the lost Table 5
#        script used the same mappings (L=|alpha|, g=alpha, decay=alpha, k=alpha, failed excluded)
#   2. Old compare_baseline_unified.py (public snapshot) on the same CSVs must regenerate
#      Results/delfys75_comparison/parameter_errors_comparison.txt (4th-decimal GT rounding aside).
_SJ="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"; _SJ="${_SJ%/slurm_jobs}/slurm_jobs"
export REPO="${_SJ%/slurm_jobs}"; source "$_SJ/common.sh"  # works under sbatch (submit from repo root or slurm_jobs/) and with plain bash
activate_env

V=$(new_run_dir validation_old_csvs)
write_provenance "$V" "evaluator validation on released CSVs"
R="$REPO/Results"

python "$REPO/scripts/evaluate_delfys75.py" \
    --run t4_base="$R/delfys75_baseline/delfys75_baseline.csv:baseline" \
    --run t4_corr="$R/delfys75_improved/delfys75_improved.csv:unified" \
    --run t5_1step="$R/delfys75_original/delfys75.csv:baseline" \
    --run t5_multi="$R/delfys75/delfys75.csv:baseline" \
    --write_gt_json "$V/gt_builtin.json" --out "$V/new_evaluator" | tee "$V/new_evaluator.txt"

python - "$V/new_evaluator/summary.csv" <<'EOF' | tee "$V/checks.txt"
import csv, sys
S = {(r["run_name"], r["dynamics"], r["setting"], r["param"]): r for r in csv.DictReader(open(sys.argv[1]))}
checks = [  # (run, dynamics, setting, param, expected MAE, tolerance)
    ("t4_base", "pendulum", "pendulum_45", "length", 0.347, 0.001),
    ("t4_base", "pendulum", "pendulum_90", "length", 0.708, 0.001),
    ("t4_base", "pendulum", "pendulum_150", "length", 1.187, 0.001),
    ("t4_base", "led", "led_2s", "decay", 7.449, 0.001),
] + [("t5_1step", d, s, p, v, 0.0051) for d, s, p, v in [
    ("dropped_ball", "large", "g", 0.25), ("free_fall", "mousepad", "g", 2.12), ("free_fall", "table", "g", 1.06),
    ("free_fall", "tennis", "g", 1.06), ("led", "led_10s", "decay", 2.09), ("pendulum", "pendulum_45", "length", 0.35),
    ("torricelli", "large", "k", 6.27)]] + [("t5_multi", d, s, p, v, 0.0051) for d, s, p, v in [
    ("dropped_ball", "large", "g", 0.18), ("free_fall", "mousepad", "g", 1.65), ("free_fall", "table", "g", 0.15),
    ("free_fall", "tennis", "g", 0.53), ("led", "led_10s", "decay", 7.46), ("pendulum", "pendulum_45", "length", 0.50),
    ("torricelli", "large", "k", 6.54)]]
bad = 0
for run, d, s, p, exp, tol in checks:
    got = float(S[(run, d, s, p)]["mae"])
    ok = abs(got - exp) <= tol
    bad += not ok
    print(f"{'OK  ' if ok else 'FAIL'} {run:<9}{d}/{s}/{p}: got {got:.4f}, expected {exp}")
print(f"{len(checks) - bad}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
EOF

python "$CODE_PUBLIC/scripts/compare_baseline_unified.py" \
    --baseline "$R/delfys75_baseline/delfys75_baseline.csv" --unified "$R/delfys75_improved/delfys75_improved.csv" \
    --params "$V/gt_builtin.json" --out "$V/old_script_on_old_csvs" > /dev/null
echo "=== diff: committed Table 4 comparison vs regenerated (only 4th-decimal rounding expected)"
diff <(tr -d '\r' < "$R/delfys75_comparison/parameter_errors_comparison.txt") \
     "$V/old_script_on_old_csvs/parameter_errors_comparison.txt" | tee "$V/old_script_diff.txt" || true

echo
echo "Validation done: $V/checks.txt must say all checks passed."
