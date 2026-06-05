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
├── indexer.sh           # helper script for rebuilding the PyLucene index
├── run_app.sh           # helper script for running the Flask search app
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
The official CS172 server already has Java, Lucene, and PyLucene installed.

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

## Part B: CS172 Server Deployment

The Part B collection is the Bluesky JSONL data. The indexer reads every
`.jsonl` file in `sample_data/` and also reads `data/*.jsonl` if the `data/`
folder exists.

On the official CS172 server, use:

```bash
ssh class-047
cd blueskyscrapper
```

Build the PyLucene index:

```bash
python3 index_bluesky.py
```

This rebuilds the generated Lucene index in:

```bash
indexdir/
```

The `indexdir/` folder is generated and ignored by Git, but it must exist on
the deployed server for search to work.

You can also use the helper script:

```bash
./indexer.sh
```

Run the Flask search app:

```bash
python3 search_app.py
```

You can also use the helper script:

```bash
./run_app.sh
```

The app listens on `0.0.0.0:8080`. On the CS172 server, open:

```bash
http://class-047.cs.ucr.edu:8080
```

For local testing on the same machine, open:

```bash
http://127.0.0.1:8080
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

### Extra Credit: Ranking Modes

For the extra credit part of Phase B, the Flask search interface supports multiple ranking modes for Bluesky posts. Users can choose how results are ordered using the ranking dropdown on the search page.

The supported ranking modes are:
- **Combined**: sorts by the final score, which combines PyLucene relevance, recency, and engagement.
- **Relevance**: sorts only by the raw PyLucene relevance score.
- **Newest**: sorts posts by their `created_at` timestamp, showing the newest posts first.
- **Engagement**: sorts by total interaction count, using likes, replies, reposts, and quotes.

The engagement value is calculated as:

```text
engagement = likes + replies + reposts + quotes
```

This allows users to compare different ways of ranking social media search results including relevance-based, time-based, engagement-based, and combined ranking.

## Phase B Final Submission Checklist

Before submitting, make sure the final report PDF includes:

- Collaboration details describing each team member's contributions
- System overview covering architecture, index structures, and search algorithm
- Known limitations of the system
- Deployment instructions for rebuilding the index and running the Flask app
- Screenshots showing the search page and search results
- A real link to the short video demo, up to 5 minutes

Video demo link: TODO - add the real video URL before submitting.
