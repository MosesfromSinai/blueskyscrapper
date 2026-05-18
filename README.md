# Bluesky Data Collector

This project is a CS172 data collection crawler that uses the Bluesky API to collect posts based on search queries.

## Features

- Collects Bluesky posts using the `atproto` Python library
- Accepts multiple search queries as input
- Avoids duplicate posts using post URIs
- Builds a PyLucene index over collected Bluesky JSONL files
- Provides a Flask search interface for Part B

## Project Structure

```bash
blueskyscrapper/
├── main.py              # main Python crawler program
├── index_bluesky.py     # builds the PyLucene search index
├── search_app.py        # Flask search interface
├── crawler.sh           # Unix/Linux executable script for running the crawler
├── collector.sh         # optional shell script/helper
├── requirements.txt     # Python dependencies
├── sample_data/         # sample output data
├── templates/           # Flask HTML templates
├── README.md            # project documentation
└── .gitignore
```

## Requirements

This project uses Python 3.

Install the required packages with:

```bash
pip install -r requirements.txt
```

Part B also requires PyLucene. PyLucene is not listed as a normal pip dependency
because it usually needs a separate local installation with Java/Lucene support.
Install PyLucene in the Python environment before running the indexer or search app.

If `requirements.txt` is not available, install the dependencies manually:

```bash
pip install atproto python-dotenv requests beautifulsoup4 Flask
```

## Bluesky Authentication

Before running the crawler, create a `.env` file in the main project folder.

Inside `.env`, add your Bluesky handle and app password:

```env
BSKY_HANDLE=your_bluesky_handle
BSKY_APP_PASSWORD=your_bluesky_app_password
```

Use a Bluesky app password instead of your normal account password.

## How to Run

You can run the crawler directly with Python:

```bash
python main.py --queries "ai,technology,programming,science,news" --target_mb 500 --output data
```

You can also run it using the included shell script.

First, make the script executable:

```bash
chmod +x crawler.sh
```

Then run:

```bash
./crawler.sh "ai,technology,programming,science,news" 500 data
```

## Command Format

The shell script takes three parameters:

```bash
./crawler.sh "<queries>" <target_mb> <output_dir>
```

Example:

```bash
./crawler.sh "ai,technology,programming,science,news" 500 data
```

This command collects around 500 MB of Bluesky posts using the given search terms and stores the output in a folder named `data`.

## Parameters

| Parameter | Description | Example |
|---|---|---|
| `queries` | Comma-separated search terms used to collect Bluesky posts | `"ai,technology,programming"` |
| `target_mb` | Target amount of raw data to collect in megabytes | `500` |
| `output_dir` | Folder where the JSONL output files will be saved | `data` |

## Output Format

The crawler stores posts in JSONL format. Each line is one JSON object representing one Bluesky post.

Example output files:

```bash
data/posts_1.jsonl
data/posts_2.jsonl
data/posts_3.jsonl
```

## Part B: PyLucene Search

The Part B collection is the Bluesky JSONL data. The indexer reads every
`.jsonl` file in `sample_data/` and also reads `data/*.jsonl` if the `data/`
folder exists.

Build the PyLucene index:

```bash
python index_bluesky.py
```

This creates a local Lucene index in:

```bash
indexdir/
```

Run the Flask search app:

```bash
python search_app.py
```

Then open:

```bash
http://127.0.0.1:5000
```

The search page shows the top 10 results. Each result displays the raw
PyLucene relevance score and the final combined score.

Ranking function:

```text
final_score = relevance_score + recency_boost + engagement_boost
recency_boost = 1 / (1 + age_in_days)
engagement_boost = log(1 + likes + replies + reposts + quotes) * 0.1
```

The Flask app first retrieves a top-k candidate set from PyLucene, then reranks those candidates
using recency and engagement.
