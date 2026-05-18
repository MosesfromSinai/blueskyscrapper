import argparse
import json
from pathlib import Path

import lucene
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import (
    Document,
    Field,
    StoredField,
    StringField,
    TextField,
)
from org.apache.lucene.index import IndexWriter, IndexWriterConfig
from org.apache.lucene.store import FSDirectory

DATA_DIRS = (Path("sample_data"), Path("data"))
DEFAULT_INDEX_DIR = Path("indexdir")
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
                    print(
                        f"Skipping invalid JSON in {jsonl_file}:{line_number}: {error}"
                    )


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
        doc.add(
            StringField(field_name, safe_text(post.get(field_name)), Field.Store.YES)
        )
    for field_name in (
        "author_handle",
        "author_display_name",
        "text",
        "external_title",
    ):
        doc.add(TextField(field_name, safe_text(post.get(field_name)), Field.Store.YES))
    for index_field, post_field in COUNT_FIELDS.items():
        doc.add(StoredField(index_field, safe_int(post.get(post_field))))
    return doc


def initialize_lucene():
    env = lucene.getVMEnv()
    if env is None:
        lucene.initVM(vmargs=["-Djava.awt.headless=true"])
    else:
        env.attachCurrentThread()


def open_index_writer(index_dir):
    index_dir = Path(index_dir)
    index_dir.mkdir(parents=True, exist_ok=True)
    directory = FSDirectory.open(Paths.get(str(index_dir.resolve())))
    analyzer = StandardAnalyzer()
    config = IndexWriterConfig(analyzer)
    config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)
    return IndexWriter(directory, config), directory


def build_index(index_dir=DEFAULT_INDEX_DIR):
    jsonl_files = list(iter_jsonl_files())
    if not jsonl_files:
        raise FileNotFoundError("No .jsonl files found in sample_data/ or data/")

    initialize_lucene()
    writer, directory = open_index_writer(index_dir)
    count = 0
    try:
        for _, _, post in iter_posts(jsonl_files):
            writer.addDocument(build_document(post))
            count += 1
            if count % 1000 == 0:
                print(f"Indexed {count} posts...")
        writer.commit()
    finally:
        writer.close()
        directory.close()
    print(f"Indexed {count} posts into {index_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Build a PyLucene index for Bluesky posts."
    )
    parser.add_argument("--index-dir", default=str(DEFAULT_INDEX_DIR))
    args = parser.parse_args()
    build_index(args.index_dir)


if __name__ == "__main__":
    main()
