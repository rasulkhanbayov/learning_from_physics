"""
Load baseline and unified CSVs (main.py format), map alpha/beta to physical
params (L, k, g, decay, damping, etc.), compute errors vs Delfys75/parameters.json,
and write parameter_errors_baseline.csv, parameter_errors_unified.csv, and
parameter_errors_comparison.txt.

Usage:
  python scripts/compare_baseline_unified.py --baseline Results/delfys75/delfys75.csv --unified Results/delfys75_unified/delfys75_unified.csv --params Delfys75/parameters.json --out Results/delfys75
  python scripts/compare_baseline_unified.py --baseline Results/delfys75/delfys75.csv --unified Results/delfys75_unified/delfys75_unified.csv --out Results/delfys75
"""

import argparse
import csv
import json
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_csv(path: str):
    """Load main.py-style CSV. Returns list of dicts with dynamics, setting, video_id, alpha, beta, ..."""
    rows = []
    with open(path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if len(row) < 9:
                continue
            # run = first 3 cols (dynamics, setting, video_id), then alpha, beta, max_z, min_z, z0, z1
            dynamics = row[0].strip()
            setting = row[1].strip()
            video_id = row[2].strip()
            try:
                alpha = float(row[3])
                beta = float(row[4])
            except (ValueError, IndexError):
                continue
            rows.append({
                "dynamics": dynamics,
                "setting": setting,
                "video_id": video_id,
                "alpha": alpha,
                "beta": beta,
            })
    return rows


def get_gt_params(params_json: dict, dynamics: str, setting: str):
    """Get ground-truth param means for (dynamics, setting) from parameters.json."""
    out = {}
    # Standard g for dropped_ball and free_fall (not in JSON)
    if dynamics in ("dropped_ball", "free_fall"):
        out["g"] = 9.80665
    d = params_json.get(dynamics)
    if not d:
        return out
    s = d.get(setting)
    if not s:
        return out
    for param_name, v in s.items():
        if isinstance(v, dict) and "mean" in v:
            out[param_name] = v["mean"]
    return out


def alpha_beta_to_physical(dynamics: str, setting: str, alpha: float, beta: float, params_json: dict):
    """
    Map (alpha, beta) to physical params per dynamics (paper conventions).
    Returns dict param_name -> estimated value.
    """
    est = {}
    if dynamics in ("dropped_ball", "free_fall"):
        # ODE z'' + beta*z' + alpha*z = 0; in free fall / dropped ball, alpha ~ g
        est["g"] = alpha if alpha > 0 else 0.0
    elif dynamics == "led":
        # Decay: beta often used as decay rate
        est["decay"] = beta if beta > 0 else 0.0
    elif dynamics == "pendulum":
        # alpha = omega^2 = g/L -> L = g/alpha; damping ~ -beta
        g = 9.80665
        est["damping"] = -beta
        est["length"] = g / alpha if alpha > 0 else 0.0
    elif dynamics == "sliding_block":
        # Angle from setting name; friction from beta
        angle_map = {"low": 20.0, "mid": 25.0, "high": 30.0}
        est["angle"] = angle_map.get(setting, 25.0)
        est["friction"] = beta if beta >= 0 else 0.0
    elif dynamics == "torricelli":
        est["k"] = alpha if alpha > 0 else 0.0
    return est


def param_name_for_output(dynamics: str, param: str) -> str:
    """Match parameter_errors column names (length_m, angle_deg, etc.)."""
    if param == "length":
        return "length_m"
    if param == "angle":
        return "angle_deg"
    return param


def compute_errors(rows: list, params_json: dict) -> list:
    """Aggregate rows by (dynamics, setting), map to physical params, compute errors vs GT."""
    # Group by (dynamics, setting)
    groups = defaultdict(list)
    for r in rows:
        key = (r["dynamics"], r["setting"])
        groups[key].append(r)

    results = []
    for (dynamics, setting), group in sorted(groups.items()):
        gt_all = get_gt_params(params_json, dynamics, setting)
        if not gt_all:
            continue
        for param, gt_mean in gt_all.items():
            estimates = []
            for r in group:
                est_dict = alpha_beta_to_physical(dynamics, setting, r["alpha"], r["beta"], params_json)
                p_out = param_name_for_output(dynamics, param)
                if p_out in est_dict:
                    estimates.append(est_dict[p_out])
                elif param in est_dict:
                    estimates.append(est_dict[param])
            if not estimates:
                continue
            est_mean = sum(estimates) / len(estimates)
            abs_errors = [abs(e - gt_mean) for e in estimates]
            abs_err_mean = sum(abs_errors) / len(abs_errors)
            abs_err_std = (sum((x - abs_err_mean) ** 2 for x in abs_errors) / len(abs_errors)) ** 0.5
            rel_err = abs_err_mean / (abs(gt_mean) + 1e-10)
            p_out = param_name_for_output(dynamics, param)
            results.append({
                "dynamics": dynamics,
                "setting": setting,
                "param": p_out,
                "gt_mean": gt_mean,
                "est_mean": est_mean,
                "abs_err_mean": abs_err_mean,
                "abs_err_std": abs_err_std,
                "rel_err_mean": rel_err,
                "n": len(estimates),
            })
    return results


def load_params(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def write_errors_csv(results: list, path: str):
    headers = ["dynamics", "setting", "param", "gt_mean", "est_mean", "abs_err_mean", "abs_err_std", "rel_err_mean", "n"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        w.writerows(results)


def write_comparison(baseline_results: list, unified_results: list, path: str):
    by_key = {}
    for r in baseline_results:
        key = (r["dynamics"], r["setting"], r["param"])
        by_key[key] = {"gt": r["gt_mean"], "baseline_est": r["est_mean"], "baseline_err": r["abs_err_mean"], "unified_est": None, "unified_err": None}
    for r in unified_results:
        key = (r["dynamics"], r["setting"], r["param"])
        if key not in by_key:
            by_key[key] = {"gt": r["gt_mean"], "baseline_est": None, "baseline_err": None, "unified_est": r["est_mean"], "unified_err": r["abs_err_mean"]}
        else:
            by_key[key]["unified_est"] = r["est_mean"]
            by_key[key]["unified_err"] = r["abs_err_mean"]
    lines = [
        "Comparison: Baseline (main.py) vs Unified (run_unified_delfys75.py)",
        "Negative diff_err = unified has lower error (better).",
        "=" * 80,
        f"{'Dynamics':<16} {'Setting':<14} {'Param':<12} {'GT':<10} {'Unif_est':<10} {'Unif_|Err|':<10} {'Base_est':<10} {'Base_|Err|':<10} {'Diff_err':<10}",
        "-" * 80,
    ]
    for key in sorted(by_key.keys()):
        d, s, p = key
        v = by_key[key]
        gt = v["gt"]
        u_est = v["unified_est"] if v["unified_est"] is not None else float("nan")
        u_err = v["unified_err"] if v["unified_err"] is not None else float("nan")
        b_est = v["baseline_est"] if v["baseline_est"] is not None else float("nan")
        b_err = v["baseline_err"] if v["baseline_err"] is not None else float("nan")
        diff = float("nan")
        if v["baseline_err"] is not None and v["unified_err"] is not None:
            diff = v["unified_err"] - v["baseline_err"]
        lines.append(f"{d:<16} {s:<14} {p:<12} {gt:<10.4f} {u_est:<10.4f} {u_err:<10.4f} {b_est:<10.4f} {b_err:<10.4f} {diff:<10.4f}")
    with open(path, "w") as f:
        f.write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", type=str, required=True, help="Baseline CSV (e.g. Results/delfys75/delfys75.csv)")
    ap.add_argument("--unified", type=str, required=True, help="Unified CSV (e.g. Results/delfys75_unified/delfys75_unified.csv)")
    ap.add_argument("--params", type=str, default=None, help="parameters.json path (default: Delfys75/parameters.json)")
    ap.add_argument("--out", type=str, default="Results/delfys75", help="Output directory for error CSVs and comparison")
    args = ap.parse_args()

    params_path = args.params or os.path.join(ROOT, "Delfys75", "parameters.json")
    params_json = load_params(params_path)

    baseline_rows = load_csv(args.baseline)
    unified_rows = load_csv(args.unified)

    baseline_results = compute_errors(baseline_rows, params_json)
    unified_results = compute_errors(unified_rows, params_json)

    os.makedirs(args.out, exist_ok=True)
    write_errors_csv(baseline_results, os.path.join(args.out, "parameter_errors_baseline.csv"))
    write_errors_csv(unified_results, os.path.join(args.out, "parameter_errors_unified.csv"))
    write_comparison(baseline_results, unified_results, os.path.join(args.out, "parameter_errors_comparison.txt"))

    print(f"Wrote {args.out}/parameter_errors_baseline.csv")
    print(f"Wrote {args.out}/parameter_errors_unified.csv")
    print(f"Wrote {args.out}/parameter_errors_comparison.txt")


if __name__ == "__main__":
    main()
