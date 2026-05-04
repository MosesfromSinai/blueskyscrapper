import argparse
import json
import os
import time

import requests
from atproto import Client
from bs4 import BeautifulSoup
from dotenv import load_dotenv

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def get_html_title(url):
    try:
        response = requests.get(url, timeout=5, headers={"User-Agent": "CS172-Bluesky-Collector"})
        soup = BeautifulSoup(response.text, "html.parser")

        if soup.title and soup.title.string:
            return soup.title.string.strip()

    except Exception:
        return None

    return None


def create_client():
    load_dotenv()

    handle = os.getenv("BSKY_HANDLE")
    app_password = os.getenv("BSKY_APP_PASSWORD")

    if not handle or not app_password:
        raise ValueError("Missing BSKY_HANDLE or BSKY_APP_PASSWORD in .env")

    client = Client()
    client.login(handle, app_password)

    return client


def fetch_posts(client, query, limit=100):
    try:
        response = client.app.bsky.feed.search_posts({
            "q": query,
            "limit": limit,
            "sort": "latest"
        })

        return response.posts

    except Exception as error:
        print(f"Search failed for '{query}': {error}")
        return []


def save_posts(queries, target_mb, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    client = create_client()

#uses the data structure set to hold the URL 
    seen_uris = set()
    file_index = 1
    current_file_size = 0
    total_bytes = 0

    file_path = os.path.join(output_dir, f"posts_{file_index}.jsonl")

    while total_bytes < target_mb * 1024 * 1024:
        for query in queries:
            posts = fetch_posts(client, query)

            for post_data in posts:
                uri = post_data.uri

                if uri in seen_uris:
                    continue

                seen_uris.add(uri)

                external_url = None
                external_title = None

                if getattr(post_data, "embed", None):
                    embed = post_data.embed

                    if getattr(embed, "external", None):
                        external_url = embed.external.uri
                        external_title = get_html_title(external_url)
                #holds the dictionary data structure (METADATA)
                post = {
                    "uri": post_data.uri,
                    "cid": post_data.cid,
                    "author_handle": post_data.author.handle,
                    "author_display_name": post_data.author.display_name,
                    "text": post_data.record.text,
                    "created_at": post_data.record.created_at,
                    "like_count": post_data.like_count,
                    "reply_count": post_data.reply_count,
                    "repost_count": post_data.repost_count,
                    "quote_count": post_data.quote_count,
                    "indexed_at": post_data.indexed_at,
                    "external_url": external_url,
                    "external_title": external_title
                }

                line = json.dumps(post, ensure_ascii=False) + "\n"
                line_size = len(line.encode("utf-8"))

                if current_file_size + line_size > MAX_FILE_SIZE:
                    file_index += 1
                    current_file_size = 0
                    file_path = os.path.join(output_dir, f"posts_{file_index}.jsonl")

                with open(file_path, "a", encoding="utf-8") as file:
                    file.write(line)

                current_file_size += line_size
                total_bytes += line_size

                print(f"{total_bytes / (1024 * 1024):.2f} MB collected")

                if total_bytes >= target_mb * 1024 * 1024:
                    break

            if total_bytes >= target_mb * 1024 * 1024:
                break

        time.sleep(1)

    print("Done collecting data.")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--queries", required=True)
    parser.add_argument("--target_mb", type=int, required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()
    #follows the queries and implements strip and split
    queries = [query.strip() for query in args.queries.split(",")]

    save_posts(queries, args.target_mb, args.output)


if __name__ == "__main__":
    main()