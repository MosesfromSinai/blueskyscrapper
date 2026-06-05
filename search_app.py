from datetime import datetime, timezone
from math import log
from pathlib import Path

import lucene
from flask import Flask, render_template, request
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.search import BooleanClause, BooleanQuery, IndexSearcher
from org.apache.lucene.store import FSDirectory

INDEX_DIR = Path("indexdir")
SEARCH_FIELDS = ("text", "author_handle", "author_display_name", "external_title")
CANDIDATE_LIMIT = 50
RESULT_LIMIT = 10
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
    return searcher, reader, directory


def parse_query(query_text):
    analyzer = StandardAnalyzer()
    escaped_query = QueryParser.escape(query_text.strip())
    builder = BooleanQuery.Builder()
    for field_name in SEARCH_FIELDS:
        parser = QueryParser(field_name, analyzer)
        builder.add(parser.parse(escaped_query), BooleanClause.Occur.SHOULD)
    return builder.build()


def search_candidates(query_text, limit=CANDIDATE_LIMIT):
    if not query_text.strip():
        return []

    searcher, reader, directory = open_searcher()
    try:
        query = parse_query(query_text)
        hits = searcher.search(query, limit).scoreDocs
        return [(searcher.doc(hit.doc), float(hit.score)) for hit in hits]
    finally:
        reader.close()
        directory.close()


# PyLucene gives top-k inverted-index relevance; we rerank with recency
# and engagement, following the lecture idea of combining ranking signals.
def parse_created_at(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def stored_int(doc, field_name):
    try:
        field = doc.getField(field_name)
        value = field.numericValue() if field else doc.get(field_name)
        return int(value or 0)
    except (AttributeError, TypeError, ValueError):
        return 0


def compute_final_score(doc, relevance_score, now=None):
    now = now or datetime.now(timezone.utc)
    created_at = parse_created_at(doc.get("created_at"))

    if created_at is None:
        age_in_days = 0
    else:
        age_seconds = max((now - created_at).total_seconds(), 0)
        age_in_days = age_seconds / 86400

    engagement = sum(stored_int(doc, field) for field in ENGAGEMENT_FIELDS)
    recency_boost = 1 / (1 + age_in_days)
    engagement_boost = log(1 + engagement) * 0.1

    return float(relevance_score) + recency_boost + engagement_boost

def compute_engagement(doc):
    return sum(stored_int(doc, field) for field in ENGAGEMENT_FIELDS)

# Sort candidates based on the selected extra credit ranking mode.
def rerank_candidates(candidates, rank_by="combined"):
    ranked = []
    for doc, score in candidates:
        created_at = parse_created_at(doc.get("created_at"))
        engagement = compute_engagement(doc)

        ranked.append(
            {
                "doc": doc,
                "relevance_score": float(score),
                "final_score": compute_final_score(doc, score),
                "created_at": created_at,
                "engagement": engagement,
            }
        )

    if rank_by == "relevance":
        return sorted(ranked, key=lambda result: result["relevance_score"], reverse=True)

    if rank_by == "newest":
        return sorted(
            ranked,
            key=lambda result: result["created_at"] or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )

    if rank_by == "engagement":
        return sorted(ranked, key=lambda result: result["engagement"], reverse=True)

    return sorted(ranked, key=lambda result: result["final_score"], reverse=True)

##def rerank_candidates(candidates):
##    ranked = []
##    for doc, score in candidates:
##        ranked.append(
##           {
##                "doc": doc,
##                "relevance_score": float(score),
##                "final_score": compute_final_score(doc, score),
##            }
##       )
##    return sorted(ranked, key=lambda result: result["final_score"], reverse=True)


def custom_snippet(text, query_text, width=180):
    text = text or ""
    lower_text = text.lower()
    terms = [term.lower() for term in query_text.split() if term]
    match_positions = [lower_text.find(term) for term in terms if term in lower_text]
    start = max((min(match_positions) if match_positions else 0) - width // 3, 0)
    end = min(start + width, len(text))
    snippet = text[start:end].strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet += "..."
    return snippet

## def build_results(query_text, limit=RESULT_LIMIT):
##    ranked = rerank_candidates(search_candidates(query_text))[:limit]


def build_results(query_text, rank_by="combined", limit=RESULT_LIMIT):
    ranked = rerank_candidates(search_candidates(query_text), rank_by)[:limit]
    results = []
    for result in ranked:
        doc = result["doc"]
        text = doc.get("text") or ""
        author = doc.get("author_display_name") or doc.get("author_handle") or "Unknown"
        results.append(
            {
                "author": author,
                "created_at": doc.get("created_at") or "",
                "text": text,
                "snippet": custom_snippet(text, query_text),
                "external_url": doc.get("external_url") or "",
                "relevance_score": result["relevance_score"],
                "final_score": result["final_score"],
                "engagement": result["engagement"],
            }
        )
    return results


@app.route("/", methods=["GET"])
def search_page():
    query = request.args.get("q", "").strip()
    rank_by = request.args.get("rank_by", "combined")
    results = []
    error = None

    if query:
        try:
            results = build_results(query, rank_by)
        except Exception as exc:
            error = f"Search failed. Make sure the PyLucene index exists in {INDEX_DIR}/. ({exc})"

    return render_template(
        "search.html",
        query=query,
        rank_by=rank_by,
        results=results,
        error=error,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
