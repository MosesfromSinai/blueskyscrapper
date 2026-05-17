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
