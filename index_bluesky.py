import json
from pathlib import Path


DATA_DIRS = (Path("sample_data"), Path("data"))


def iter_jsonl_files():
    for data_dir in DATA_DIRS:
        if data_dir.exists():
            yield from sorted(data_dir.glob("*.jsonl"))


def iter_posts(jsonl_files):
    for jsonl_file in jsonl_files:
        with jsonl_file.open("r", encoding="utf-8") as posts_file:
            for line_number, line in enumerate(posts_file, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    yield jsonl_file, line_number, json.loads(line)
                except json.JSONDecodeError as error:
                    print(f"Skipping invalid JSON in {jsonl_file}:{line_number}: {error}")
