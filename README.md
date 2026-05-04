# Bluesky Data Collector

## Setup

Install dependencies:
pip install atproto python-dotenv requests beautifulsoup4

Create a .env file:
BSKY_HANDLE=your_handle
BSKY_APP_PASSWORD=your_app_password

## Run

python main.py --queries "ai,technology,programming,science,news" --target_mb 500 --output data

## Output

Data is stored in JSONL format in the data folder. Each file is about 10MB.