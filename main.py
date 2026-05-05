import argparse
import json
import os
import time

import requests
from atproto import Client
from bs4 import BeautifulSoup
from dotenv import load_dotenv

MAX_FILE_SIZE = 10 * 1024 * 1024 #finalizes the max MB whcih is 10MB

#gets the HTML titla by checking the parsing and the given URL 
def get_html_title(url):
    try:
    #prgram sends a request to the URL with a timeout of 5
        response = requests.get(url, timeout=5, headers={"User-Agent": "CS172-Bluesky-Collector"})
        soup = BeautifulSoup(response.text, "html.parser")
    #parses whatever is in the HTML (follows the Beautiful soup library)
        if soup.title and soup.title.string:
            return soup.title.string.strip()

    except Exception:
        return None

    return None

#log in credentials for bluesky
def create_client():
    load_dotenv()
    #
    handle = os.getenv("BSKY_HANDLE") #username
    app_password = os.getenv("BSKY_APP_PASSWORD") #password 

    if not handle or not app_password: #log in authentication
        raise ValueError("Missing BSKY_HANDLE or BSKY_APP_PASSWORD in .env")

    client = Client()
    client.login(handle, app_password)

    return client

#function that fetches the posts from bluesky 
def fetch_posts(client, query, limit=100):
    try:
        response = client.app.bsky.feed.search_posts({
            "q": query,
            "limit": limit,
            "sort": "latest"
        })
        #queries throught the Bluesky api and the fetches posts from bluesky 
        return response.posts

    except Exception as error:
        print(f"Search failed for '{query}': {error}")
        return []


def save_posts(queries, target_mb, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    client = create_client()

    # uses the data structure set to hold the post URIs
    seen_post_uris = set()
    current_file_number = 1
    current_file_size = 0
    total_data_size = 0

    file_path = os.path.join(output_dir, f"posts_{current_file_number}.jsonl")
####collects data until hits the max target size 
    while total_data_size < target_mb * 1024 * 1024:
        for query in queries:
            posts = fetch_posts(client, query)

            for bluesky_post in posts:
                uri = bluesky_post.uri
##### initialize API client

                if uri in seen_post_uris:
                    continue

                seen_post_uris.add(uri)
### external data
                external_url = None
                external_title = None

                if getattr(bluesky_post, "embed", None):
                    embed = bluesky_post.embed

                    if getattr(embed, "external", None):
                        external_url = embed.external.uri
                        external_title = get_html_title(external_url)

                # holds the dictionary data structure for each post
                post = {
                    "uri": bluesky_post.uri,
                    "cid": bluesky_post.cid,
                    "author_handle": bluesky_post.author.handle,
                    "author_display_name": bluesky_post.author.display_name,
                    "text": bluesky_post.record.text,
                    "created_at": bluesky_post.record.created_at,
                    "like_count": bluesky_post.like_count,
                    "reply_count": bluesky_post.reply_count,
                    "repost_count": bluesky_post.repost_count,
                    "quote_count": bluesky_post.quote_count,
                    "indexed_at": bluesky_post.indexed_at,
                    "external_url": external_url,
                    "external_title": external_title
                }

                line = json.dumps(post, ensure_ascii=False) + "\n"
                line_size = len(line.encode("utf-8"))

                if current_file_size + line_size > MAX_FILE_SIZE:
                    current_file_number += 1
                    current_file_size = 0
                    file_path = os.path.join(output_dir, f"posts_{current_file_number}.jsonl")

                with open(file_path, "a", encoding="utf-8") as file:
                    file.write(line)

                current_file_size += line_size
                total_data_size += line_size

                print(f"{total_data_size / (1024 * 1024):.2f} MB collected")

                if total_data_size >= target_mb * 1024 * 1024:
                    break

            if total_data_size >= target_mb * 1024 * 1024:
                break

        time.sleep(1)

    print("Done collecting data.")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--queries", required=True)
    parser.add_argument("--target_mb", type=int, required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    # follows the queries and implements strip and split
    queries = [query.strip() for query in args.queries.split(",")]

    save_posts(queries, args.target_mb, args.output)


if __name__ == "__main__":
    main()