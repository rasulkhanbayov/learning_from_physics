"""
Evaluate trained video dynamics classifier on Delfys75 (same format as VLM evaluation).

Usage:
  python scripts/evaluate_video_classifier.py --path ./delfys75 --checkpoint Results/video_classifier/best.pt --out Results/video_classifier_eval
"""

import argparse
import os
import sys
import csv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.video_classifier import (
    get_gt_dynamics_from_path,
    load_classifier,
    predict_dynamics_from_npy,
    DYNAMICS_CLASSES,
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", type=str, default="./delfys75")
    ap.add_argument("--checkpoint", type=str, required=True, help="Path to best.pt")
    ap.add_argument("--out", type=str, default="Results/video_classifier_eval")
    args = ap.parse_args()

    model = load_classifier(args.checkpoint)
    rows = []
    for root, _, files in os.walk(args.path):
        for f in files:
            if not f.endswith(".npy"):
                continue
            file_path = os.path.join(root, f)
            gt = get_gt_dynamics_from_path(file_path)
            if gt is None:
                continue
            pred = predict_dynamics_from_npy(file_path, model=model)
            if pred is None:
                pred = ""
            correct = pred == gt
            rows.append({"path": file_path, "gt": gt, "pred": pred, "correct": correct})

    if not rows:
        print("No .npy files with known dynamics found.")
        return

    correct_count = sum(r["correct"] for r in rows)
    accuracy = correct_count / len(rows)
    gt_all = [r["gt"] for r in rows]
    pred_all = [r["pred"] for r in rows]
    classes = sorted(set(gt_all))

    print("\n--- Video classifier dynamics evaluation ---")
    print(f"Checkpoint: {args.checkpoint}")
    print(f"Total videos: {len(rows)}")
    print(f"Correct: {correct_count}")
    print(f"Accuracy: {accuracy:.2%}")
    print("Per-class accuracy (GT class -> accuracy):")
    per_class = {}
    for c in classes:
        indices = [i for i, g in enumerate(gt_all) if g == c]
        correct_c = sum(1 for i in indices if pred_all[i] == c)
        acc_c = correct_c / len(indices) if indices else 0
        per_class[c] = acc_c
        print(f"  {c}: {correct_c}/{len(indices)} = {acc_c:.2%}")

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "video_classifier_eval_summary.txt"), "w") as f:
        f.write("Video classifier dynamics evaluation\n")
        f.write(f"Checkpoint: {args.checkpoint}\n")
        f.write(f"Data path: {args.path}\n")
        f.write(f"Total videos: {len(rows)}\n")
        f.write(f"Accuracy: {accuracy:.2%}\n")
        f.write(f"Per-class accuracy: {per_class}\n")
    with open(os.path.join(args.out, "video_classifier_results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["path", "gt", "pred", "correct"])
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {args.out}/video_classifier_eval_summary.txt and video_classifier_results.csv")


if __name__ == "__main__":
    main()
