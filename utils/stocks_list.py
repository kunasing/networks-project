import os
import time

import requests
from dotenv import load_dotenv


def main():
    # Load environment variables from .env file
    load_dotenv()
    api_key = os.getenv("POLYGON_API_KEY")

    if not api_key:
        print("Error: POLYGON_API_KEY not found in environment or .env file.")
        return

    stock_types = ["CS", "OS", "ADRC"]

    # Map ticker -> company name
    ticker_metadata = {}

    for stock_type in stock_types:
        get_tickers_by_type(stock_type, ticker_metadata, api_key)

    save_tickers_to_file(ticker_metadata)

    print(f"Found {len(ticker_metadata)} stock tickers")
    return len(ticker_metadata)


def save_tickers_to_file(ticker_metadata, filepath=None):
    """Writes all unique tickers and stock names to a tab-separated file."""
    if filepath is None:
        # Move up one level from utils/ to project root
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(base_dir, "ticker_metadata", "tickers.txt")

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        f.write("ticker\tname\n")
        for ticker in sorted(ticker_metadata):
            name = ticker_metadata.get(ticker, "")
            f.write(f"{ticker}\t{name}\n")


def get_tickers_by_type(stock_type, ticker_metadata: dict, api_key: str):
    params = {
        "type": stock_type,
        "market": "stocks",
        "active": "true",
        "order": "asc",
        "limit": "1000",
        "sort": "ticker",
        "apiKey": api_key,
    }

    url = "https://api.massive.com/v3/reference/tickers"

    while url:
        response = requests.get(url, params=params)

        if response.status_code == 429 or (
            response.status_code != 200
            and "exceeded the maximum requests per minute" in response.text
        ):
            print("Rate limit exceeded, continuing in 1 minute.")
            time.sleep(30)
            print("...in 30 seconds.")
            time.sleep(15)
            print("...in 15 seconds.")
            time.sleep(15)
            continue

        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text}")
            break

        data = response.json()
        print(f"Tickers retrieved: {data.get('count')}")

        for item in data.get("results", []):
            ticker = item.get("ticker")
            if not ticker:
                continue
            ticker_metadata[ticker] = item.get("name", "")

        url = data.get("next_url")

        if not url:
            print(f"Finished fetching all tickers of type {stock_type}.")
            break


if __name__ == "__main__":
    main()
