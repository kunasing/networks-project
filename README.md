# MATH 168 - Networks Group Project

Our project is to analyze stock data using networks. We want to find which industries and stocks are correlated and central to the market.

To initialize and run the project, we use uv. This manages packages and dependencies and also sets the virtual environment.

Installation docs: https://docs.astral.sh/uv/getting-started/installation/#standalone-installer.

## Setup

Retrieve the data from ... ?

We store the tickers at ticker_metadata/tickers.txt, so this is not necessary, but shows how the list is generated.
Create .env file in root, with API key for polygon (now massive), so you can run the stocks list if it needs updated:

```text
POLYGON_API_KEY=your_api_key_here
```

## Running the Project

Then, you can:
`uv run stocks_list.py` -> generates `ticker_metadata/tickers.txt`, which is a list of stocks in the exchange. used later to filter out ETFs, Funds, and Trusts.
`uv run data_processor.py` -> use rolling window for stock return to generate a similarity rating for performance between different stocks.
`uv run main.py` -> network anaylsis... to be updated
