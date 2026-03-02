import argparse
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


def main():
  build_network()


def build_network():
  pass


def read():
  data_dir = "data"
  # Find both standard CSVs and gzipped CSVs
  csv_files = []
  for ext in ["*.csv", "*.csv.gz"]:
    csv_files.extend(glob.glob(f"{data_dir}/**/{ext}", recursive=True))

  # Deduplicate in case a file exists as both .csv and .csv.gz (prefer .csv)
  file_stems = {}
  for f in csv_files:
    stem = f.replace(".gz", "")
    # If we already have the uncompressed version, skip adding the compressed one
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

  # Pivot to get a time series matrix: index=date, columns=ticker, values=close price
  print("Pivoting data to chronological order...")
  # Use pivot_table with 'last' to avoid crashes if there are duplicated date-ticker rows
  # Convert 'close' to numeric, replacing any non-numeric strings with NaN
  full_df["close"] = pd.to_numeric(full_df["close"], errors="coerce")

  prices_df = full_df.pivot_table(
    index="date", columns="ticker", values="close", aggfunc="last"
  )

  # 1. Calculate log return values for a 50-day window
  # Formula: ln(P_t / P_{t-50})
  print("Calculating 50-day rolling log returns...")

  # Ensure float type for safety
  prices_df = prices_df.astype(float)

  # Note: .shift(50) moves prices down by 50 rows, aligning previous prices with current day.
  # Therefore, np.log(prices / prices.shift(50)) provides the 50-day return for any given point t
  log_returns_50d = np.log(prices_df / prices_df.shift(50))

  # 2. Extract step size 10 to form the sliding window vectors
  # We take every 10th row, starting from day 50 where the first 50-day window fully matures
  print("Applying step size 10 to extract periodic returns for each ticker...")
  vector_df = log_returns_50d.iloc[50::10]

  # Transposing means: each row is a stock ticker, and columns represent the log return values iteratively
  ticker_vectors = vector_df.T

  # Remove infs and NaNs resulting from missing data, zero division, or log(0)
  ticker_vectors = ticker_vectors.replace([np.inf, -np.inf], np.nan)
  ticker_vectors = ticker_vectors.fillna(0)

  print(
    f"Constructed vectors for {len(ticker_vectors)} tickers. Vector length: {ticker_vectors.shape[1]}"
  )

  # 3. Generate Similarity Metric between vectors (every combination)
  print("Computing cosine similarity between all combinations of ticker vectors...")

  sim_matrix = cosine_similarity(ticker_vectors.values)

  # Cast to DataFrame for easy indexing and lookups
  sim_df = pd.DataFrame(
    sim_matrix, index=ticker_vectors.index, columns=ticker_vectors.index
  )

  print("Similarity calculations complete! Matrix shape:", sim_df.shape)
  print("\nSample top-left corner:")
  print(sim_df.iloc[:5, :5])

  # Save output to a CSV
  out_file = "ticker_similarities.csv"
  sim_df.to_csv(out_file)
  print(f"\nSimilarity matrix saved to {out_file}")


if __name__ == "__main__":
  main()
