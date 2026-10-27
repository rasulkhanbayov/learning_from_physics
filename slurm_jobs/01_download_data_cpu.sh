#!/bin/bash -l
#SBATCH -J d75_download
#SBATCH -o d75_download_%j.out
#SBATCH -e d75_download_%j.err
#SBATCH -p cpu-all
#SBATCH -c 2
#SBATCH --mem 8000MB
#SBATCH -t 03:00:00
#
# Downloads Delfys75 (Kaggle jaswar/physical-parameter-prediction, version 11, MIT license,
# 916 MB zip: output_selected/<dynamics>/<setting>/<run>/{video,masks}.mp4 + parameters.json)
# into $WORK/data/raw, checks it, and writes layout.txt. Needs internet: if compute nodes
# have none, run it on a shared server instead:  bash slurm_jobs/01_download_data_cpu.sh
#
# Token: KAGGLE_API_TOKEN from the environment, or the line
#   export KAGGLE_API_TOKEN=KGAT_...   in ~/.kaggle/kaggle_token.txt (chmod 600).
# Downloads with curl (the new KGAT_ tokens are not supported by older kaggle CLIs); the
# token goes in a private header file, so it never appears on the command line or in logs.
#
# READ $WORK/data/raw/layout.txt before 02.
_SJ="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"; _SJ="${_SJ%/slurm_jobs}/slurm_jobs"
export REPO="${_SJ%/slurm_jobs}"; source "$_SJ/common.sh"  # works under sbatch (submit from repo root or slurm_jobs/) and with plain bash
if [ -z "${SLURM_JOB_ID:-}" ] && [[ "$(hostname)" == *login* ]]; then
    echo "Do not run this on $(hostname) (login nodes kill long processes). Use sbatch, or bash on 10.4.64.27/28." >&2
    exit 1
fi
activate_env

DATASET="jaswar/physical-parameter-prediction"
VERSION=11                      # pin: the version inspected on 2026-10-14
EXPECTED_VIDEOS=90              # 18 settings x 5 clips (masks.mp4 not counted)

TOKEN="${KAGGLE_API_TOKEN:-}"
if [ -z "$TOKEN" ] && [ -f "$HOME/.kaggle/kaggle_token.txt" ]; then
    TOKEN=$(sed -n 's/^[[:space:]]*\(export[[:space:]]\+\)\?KAGGLE_API_TOKEN=//p' "$HOME/.kaggle/kaggle_token.txt" | head -1 | tr -d "\"' \r")
fi
if [ -z "$TOKEN" ]; then
    echo "No Kaggle token: export KAGGLE_API_TOKEN=... or put 'export KAGGLE_API_TOKEN=KGAT_...'" >&2
    echo "in ~/.kaggle/kaggle_token.txt (chmod 600)." >&2
    exit 1
fi
if [ -e "$DATA_RAW" ]; then
    echo "ERROR: $DATA_RAW already exists; not downloading over it." >&2
    exit 1
fi
mkdir -p "$DATA_RAW/zip" "$DATA_RAW/extracted"
HDR=$(mktemp); chmod 600 "$HDR"; trap 'rm -f "$HDR"' EXIT
printf 'Authorization: Bearer %s\n' "$TOKEN" > "$HDR"
unset TOKEN KAGGLE_API_TOKEN

API="https://www.kaggle.com/api/v1"
curl -fsS -H @"$HDR" "$API/datasets/view/$DATASET" -o "$DATA_RAW/dataset-metadata.json"
curl -fsS -H @"$HDR" "$API/datasets/list/$DATASET?datasetVersionNumber=$VERSION&pageSize=500" -o "$DATA_RAW/file-list.json"
curl -fSL --retry 3 -H @"$HDR" "$API/datasets/download/$DATASET?datasetVersionNumber=$VERSION" -o "$DATA_RAW/zip/delfys75_v$VERSION.zip"
(cd "$DATA_RAW/zip" && sha256sum ./*.zip) | tee "$DATA_RAW/zip_sha256.txt"

# Python's zipfile checks every CRC and strips absolute / ".." paths when extracting.
python -I - "$DATA_RAW/zip/delfys75_v$VERSION.zip" "$DATA_RAW/extracted" <<'EOF'
import sys, zipfile
with zipfile.ZipFile(sys.argv[1]) as z:
    bad = z.testzip()
    if bad:
        sys.exit(f"corrupt member in zip: {bad}")
    z.extractall(sys.argv[2])
    print(f"extracted {len(z.namelist())} members")
EOF

N_VID=$(find "$DATA_RAW/extracted" -type f -name 'video.mp4' | wc -l)
N_GT=$(find "$DATA_RAW/extracted" -type f -name 'parameters.json' | wc -l)
if [ "$N_VID" -ne "$EXPECTED_VIDEOS" ] || [ "$N_GT" -ne 1 ]; then
    echo "ERROR: expected $EXPECTED_VIDEOS video.mp4 and 1 parameters.json; found $N_VID and $N_GT." >&2
    exit 1
fi

{
    echo "# Kaggle metadata (license, version, size)"
    python -c 'import json,sys; d=json.load(open(sys.argv[1])); print({k: d.get(k) for k in ("ref","title","licenseName","currentVersionNumber","totalBytes","lastUpdated")})' "$DATA_RAW/dataset-metadata.json"
    echo
    echo "# file counts by extension"
    find "$DATA_RAW/extracted" -type f | sed 's/.*\.//' | sort | uniq -c
    echo
    echo "# directories (depth <= 5)"
    find "$DATA_RAW/extracted" -maxdepth 5 -type d | sed "s#^$DATA_RAW/extracted##" | sort
    echo
    echo "# json / csv / txt files (possible ground truth)"
    find "$DATA_RAW/extracted" -type f \( -iname '*.json' -o -iname '*.csv' -o -iname '*.txt' \)
} | tee "$DATA_RAW/layout.txt"

echo
echo "Download done. READ $DATA_RAW/layout.txt, then run 02_preprocess_verify_cpu.sh."
echo "Expected: 90 video.mp4 + 90 masks.mp4 under output_selected/, one parameters.json, license MIT."
