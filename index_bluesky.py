import json
from pathlib import Path

from org.apache.lucene.document import Document, Field, StoredField, StringField, TextField


DATA_DIRS = (Path("sample_data"), Path("data"))
COUNT_FIELDS = {
    "likes": "like_count",
    "replies": "reply_count",
    "reposts": "repost_count",
    "quotes": "quote_count",
}


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


def safe_text(value):
    return "" if value is None else str(value)


def safe_int(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def build_document(post):
    doc = Document()
    for field_name in ("uri", "created_at", "indexed_at", "external_url"):
        doc.add(StringField(field_name, safe_text(post.get(field_name)), Field.Store.YES))
    for field_name in ("author_handle", "author_display_name", "text", "external_title"):
        doc.add(TextField(field_name, safe_text(post.get(field_name)), Field.Store.YES))
    for index_field, post_field in COUNT_FIELDS.items():
        doc.add(StoredField(index_field, safe_int(post.get(post_field))))
    return doc
