#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "Usage: ./indexer.sh <index_dir>"
    exit 1
fi

python index_bluesky.py --index-dir "$1"