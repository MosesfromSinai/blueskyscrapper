from pathlib import Path

import lucene
from flask import Flask
from java.nio.file import Paths
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.store import FSDirectory


INDEX_DIR = Path("indexdir")

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
