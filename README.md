# Boogle - Simple Search Engine

Boogle is a Python-based search engine built from scratch. It demonstrates the core components of a search engine: crawling, processing, indexing, ranking, and retrieval.

## Architecture

Boogle is modularized into the following components:

-   **Crawler** (`boogle/crawler/`): Fetches pages starting from seed URLs, respecting `robots.txt` (stubbed) and depth limits. Stores raw HTML and builds a link graph.
-   **Processor** (`boogle/processor/`): Cleans HTML, extracts text, tokenizes, removes stop words, and stems tokens.
-   **Indexer** (`boogle/indexer/`): Builds an inverted index (`term -> [doc_id, ...]`) and stores document metadata.
-   **Ranker** (`boogle/ranker/`): Computes PageRank scores from the link graph.
-   **Query Engine** (`boogle/query_engine/`): Retrievers documents matching a query and scores them using a combination of BM25 (text relevance) and PageRank (authority).
-   **Frontend** (`boogle/frontend/`): A lightweight Flask web application for searching.

## Setup & Running

### Prerequisites
-   Python 3.8+
-   virtualenv (recommended)

### Installation

1.  Clone the repository.
2.  Create a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # on Linux/Mac
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: minimal requirements: `requests`, `beautifulsoup4`, `flask`, `python-dotenv`, `nltk`, `numpy`, `networkx`, `scipy`)*

### Usage

1.  **Configure**: Check `.env` to set seed URLs and crawl limits.
2.  **Crawl**: Run the crawler to fetch pages.
    ```bash
    python -m boogle.crawler.crawler
    ```
3.  **Index**: Build the inverted index from crawled pages.
    ```bash
    python -m boogle.indexer.inverted_index
    ```
4.  **Rank**: Compute PageRank scores.
    ```bash
    python -m boogle.ranker.pagerank
    ```
5.  **Serve**: Start the web server.
    ```bash
    python -m boogle.frontend.app
    ```
    Open `http://localhost:5000` in your browser.

## Configuration (.env)

-   `SEED_URLS`: Comma-separated list of starting URLs.
-   `MAX_DEPTH`: Crawl depth limit.
-   `MAX_PAGES`: Maximum pages to crawl.
-   `RANKING_ALPHA`: Weight for text relevance (0.0 - 1.0).
-   `RANKING_BETA`: Weight for PageRank (0.0 - 1.0).

## Implementation Details

-   **Text Processing**: Uses NLTK for stemming and stop-stop removal.
-   **Storage**: Uses local filesystem (JSON/HTML files) for simplicity.
-   **Ranking**: Uses a linear combination of BM25 score and PageRank score.
