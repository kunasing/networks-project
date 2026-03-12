import glob
import os
from pathlib import Path

import pandas as pd


def extract_siccd_mapping(
    data_dir="data/Yearly", output_file="ticker_metadata/ticker_siccd.txt"
):
    """
    Scans daily CSV files in data_dir to build a unique mapping of ticker -> SICCD.
    Saves the results as a tab-separated file.
    """
    print(f"Scanning files in {data_dir} for SICCD data...")

    # Get all csv files
    csv_files = glob.glob(f"{data_dir}/**/*.csv*", recursive=True)
    if not csv_files:
        print(f"No data files found in {data_dir}")
        return

    # Map ticker -> siccd
    ticker_siccd = {}

    # We process files to find unique SICCDs. Since they are theoretically constant,
    # we can stop looking for a ticker once we find it once.
    for file_path in csv_files:
        try:
            # Detect if gzipped
            compression = "gzip" if str(file_path).endswith(".gz") else None

            # Read only the columns we need
            df = pd.read_csv(
                file_path, usecols=["ticker", "SICCD"], compression=compression
            )
            df = df.dropna(subset=["ticker", "SICCD"])

            # Drop duplicates in this file to speed up iteration
            df = df.drop_duplicates(subset=["ticker"])

            for _, row in df.iterrows():
                ticker = str(row["ticker"]).strip()
                # Clean up SICCD (remove .0 if it's a float-string)
                siccd = str(row["SICCD"]).strip().split(".")[0]

                if ticker not in ticker_siccd:
                    ticker_siccd[ticker] = siccd

        except Exception as e:
            # Some files might be missing the column or be corrupted, just skip
            continue

    if not ticker_siccd:
        print("No SICCD data could be extracted.")
        return

    # Save to file
    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w") as f:
        f.write("ticker\tsiccd\n")
        for ticker in sorted(ticker_siccd):
            f.write(f"{ticker}\t{ticker_siccd[ticker]}\n")

    print(f"Successfully saved {len(ticker_siccd)} mappings to {output_file}")


if __name__ == "__main__":
    extract_siccd_mapping()
