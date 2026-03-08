import glob
import os
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


def load_tickers_from_file(filepath="ticker_metadata/tickers.txt"):
    """Reads tickers from a file back into a set."""
    if not os.path.exists(filepath):
        print(f"Ticker file {filepath} not found.")
        return set()
    with open(filepath, "r") as f:
        return {line.strip() for line in f if line.strip()}


def read_and_process(output_dir: Path, ticker_set: set):
    data_dir = "data"
    # Find both standard CSVs and gzipped CSVs
    csv_files = []
    for ext in ["*.csv", "*.csv.gz"]:
        csv_files.extend(glob.glob(f"{data_dir}/**/{ext}", recursive=True))

    # Deduplicate in case a file exists as both .csv and .csv.gz (prefer .csv)
    file_stems = {}
    for f in csv_files:
        stem = f.replace(".gz", "")
        if stem in file_stems and not f.endswith(".gz"):
            file_stems[stem] = f
        elif stem not in file_stems:
            file_stems[stem] = f

    final_files = list(file_stems.values())

    if not final_files:
        print(f"No CSV files found in {data_dir}")
        return

    print(f"Found {len(final_files)} daily stock data files. Reading data...")

    df_list = []
    for file in final_files:
        try:
            # We only need ticker, date, and close price
            df = pd.read_csv(file, usecols=["ticker", "date", "close"])

            # Filter by the provided ticker set
            if ticker_set:
                df = df[df["ticker"].isin(ticker_set)]

            df_list.append(df)
        except Exception as e:
            print(f"Error reading {file}: {e}")

    if not df_list:
        print("Failed to load any data.")
        return

    full_df = pd.concat(df_list, ignore_index=True)

    # Sort chronologically
    print("Sorting chronological data...")
    full_df = full_df.sort_values(by=["date", "ticker"])

    # Pivot to get a time series matrix
    print("Pivoting data to chronological order...")
    full_df["close"] = pd.to_numeric(full_df["close"], errors="coerce")
    prices_df = full_df.pivot_table(
        index="date", columns="ticker", values="close", aggfunc="last"
    )

    print(full_df.shape)
    print(prices_df.shape)

    # Calculate weekly returns (every 5 days)
    print("Calculating weekly (5-day) log returns...")
    prices_df = prices_df.astype(float)
    # Get prices every 5 days
    weekly_prices = prices_df.iloc[::5]
    # Calculate log returns between these 5-day intervals
    # log(P_t / P_{t-5})
    vector_df = np.log(weekly_prices / weekly_prices.shift(1))
    # Drop the first row as it will be NaN
    vector_df = vector_df.dropna(how="all")

    # Identify tickers with missing data
    missing_data_mask = vector_df.isna().any()
    missing_tickers = missing_data_mask[missing_data_mask].index.tolist()
    if missing_tickers:
        print(f"Tickers with missing data (being removed): {', '.join(missing_tickers)}")
    
    # Remove tickers with missing data
    vector_df = vector_df.dropna(axis=1)

    # Transposing means: each row is a stock ticker
    ticker_vectors = vector_df.T
    ticker_vectors = ticker_vectors.replace([np.inf, -np.inf], np.nan)
    ticker_vectors = ticker_vectors.fillna(0)

    print(f"Constructed vectors for {len(ticker_vectors)} tickers.")

    # Save ticker vectors to CSV
    vectors_file = output_dir / "ticker_vectors.csv"
    ticker_vectors.to_csv(vectors_file)
    print(f"Ticker vectors saved to {vectors_file}")

    # 3. Generate Similarity Metric
    print("Computing cosine similarity...")
    sim_matrix = cosine_similarity(ticker_vectors.values)
    sim_df = pd.DataFrame(
        sim_matrix, index=ticker_vectors.index, columns=ticker_vectors.index
    )

    # Save to CSV (replacing pickle)
    out_file = output_dir / "ticker_similarities.csv"
    sim_df.to_csv(out_file)
    print(f"Similarity matrix saved to {out_file}")


if __name__ == "__main__":
    output_path = Path("output")
    output_path.mkdir(parents=True, exist_ok=True)

    # Optional: Load a specific subset of tickers if the file exists
    tickers = load_tickers_from_file()
    if tickers:
        print(f"Filtering for {len(tickers)} tickers from file.")
    else:
        print("No ticker file found or empty. Processing all tickers in data folder.")

    read_and_process(output_path, tickers)
