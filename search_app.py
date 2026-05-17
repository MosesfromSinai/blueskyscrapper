from datetime import datetime, timezone
from math import log
from pathlib import Path

import lucene
from flask import Flask
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import MultiFieldQueryParser, QueryParser
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.store import FSDirectory


INDEX_DIR = Path("indexdir")
SEARCH_FIELDS = ("text", "author_handle", "author_display_name", "external_title")
CANDIDATE_LIMIT = 50
ENGAGEMENT_FIELDS = ("likes", "replies", "reposts", "quotes")

app = Flask(__name__)


def initialize_lucene():
    env = lucene.getVMEnv()
    if env is None:
        lucene.initVM(vmargs=["-Djava.awt.headless=true"])
    else:
        env.attachCurrentThread()


def open_searcher(index_dir=INDEX_DIR):
    initialize_lucene()
    directory = FSDirectory.open(Paths.get(str(Path(index_dir).resolve())))
    reader = DirectoryReader.open(directory)
    searcher = IndexSearcher(reader)
    return searcher, reader


def parse_query(query_text):
    analyzer = StandardAnalyzer()
    escaped_query = QueryParser.escape(query_text.strip())
    parser = MultiFieldQueryParser(SEARCH_FIELDS, analyzer)
    return parser.parse(escaped_query)


def search_candidates(query_text, limit=CANDIDATE_LIMIT):
    if not query_text.strip():
        return []

    searcher, reader = open_searcher()
    try:
        query = parse_query(query_text)
        hits = searcher.search(query, limit).scoreDocs
        return [(searcher.doc(hit.doc), float(hit.score)) for hit in hits]
    finally:
        reader.close()


# PyLucene gives top-k inverted-index relevance; we rerank with recency
# and engagement, following the lecture idea of combining ranking signals.
def parse_created_at(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError: return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def stored_int(doc, field_name):
    try:
        field = doc.getField(field_name)
        value = field.numericValue() if field else doc.get(field_name)
        return int(value or 0)
    except (AttributeError, TypeError, ValueError): return 0


def compute_final_score(doc, relevance_score, now=None):
    now = now or datetime.now(timezone.utc)
    created_at = parse_created_at(doc.get("created_at"))
    age_seconds = 0 if created_at is None else max((now - created_at).total_seconds(), 0)
    recency_boost = 1 / (1 + age_seconds / 86400)
    engagement_boost = log(1 + sum(stored_int(doc, field) for field in ENGAGEMENT_FIELDS)) * 0.1
    return float(relevance_score) + recency_boost + engagement_boost


def rerank_candidates(candidates):
    ranked = [{"doc": doc, "relevance_score": float(score), "final_score": compute_final_score(doc, score)}
              for doc, score in candidates]
    return sorted(ranked, key=lambda result: result["final_score"], reverse=True)
