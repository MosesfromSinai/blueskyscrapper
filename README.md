# Bluesky Data Collector

This project is a CS172 data collection crawler that uses the Bluesky API to collect posts based on search queries.

## Features

- Collects Bluesky posts using the `atproto` Python library
- Accepts multiple search queries as input
- Avoids duplicate posts using post URIs

## Project Structure

```bash
blueskyscrapper/
├── main.py              # main Python crawler program
├── crawler.sh           # Unix/Linux executable script for running the crawler
├── collector.sh         # optional shell script/helper
├── requirements.txt     # Python dependencies
├── sample_data/         # sample output data
├── README.md            # project documentation
└── .gitignore
```

## Requirements

This project uses Python 3.

Install the required packages with:

```bash
pip install -r requirements.txt
```

If `requirements.txt` is not available, install the dependencies manually:

```bash
pip install atproto python-dotenv requests beautifulsoup4
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