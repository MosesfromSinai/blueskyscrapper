#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 3 ]; then
    echo "Usage: ./crawler.sh \"<queries>\" <target_mb> <output_dir>"
    echo "Example: ./crawler.sh \"ai,technology,programming,science,news\" 500 data"
    exit 1
fi

python main.py --queries "$1" --target_mb "$2" --output "$3"
