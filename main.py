import argparse
import json
import os
import sys
import time
import logging
from datetime import datetime, timezone
 
import requests
from bs4 import BeautifulSoup
 
# setup
 
API_BASE = "https://public.api.bsky.app/xrpc"
SEARCH_ENDPOINT = f"{API_BASE}/app.bsky.feed.searchPosts"
 
DEFAULT_QUERIES = [
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "neural network",
    "LLM",
    "ChatGPT",
    "GPT-5",
    "natural language processing",
    "computer vision",
    "generative AI",
    "transformer model",
    "large language model",
    "Claude AI",
    "OpenAI",
]

# logging 

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
