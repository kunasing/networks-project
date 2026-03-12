import os
import glob
import argparse
import numpy as np
import pandas as pd


def load_all_files(data_root: str, date_col: str = "date") -> pd.DataFrame:
    files = sorted(glob.glob(os.path.join(data_root, "**", "*.csv.gz"), recursive=True))
    if not files:
        raise FileNotFoundError(f"No .csv.gz files found under: {data_root}")

    dfs = []
    for i, f in enumerate(files, 1):
        if i % 50 == 0 or i == len(files):
            print(f"Loading file {i}/{len(files)}: {f}")

        base = os.path.basename(f)              # e.g. 20210104.csv.gz
        date_str = base.replace(".csv.gz", "") # e.g. 20210104

        try:
            file_date = pd.to_datetime(date_str, format="%Y%m%d")
        except Exception as e:
            raise ValueError(f"Could not parse date from filename: {f}") from e

        tmp = pd.read_csv(f, compression="gzip")
        tmp[date_col] = file_date
        dfs.append(tmp)

    df = pd.concat(dfs, ignore_index=True)
    return df


def clean_and_prepare(
    df: pd.DataFrame,
    ret_col: str = "fret_RR_CLCL",
    ticker_col: str = "ticker",
    date_col: str = "date",
    liq_col: str = "volume",
    top_n_stocks: int = 100,
    min_history_ratio: float = 0.80,
):
    required_cols = [ticker_col, ret_col, date_col]
    for c in required_cols:
        if c not in df.columns:
            raise KeyError(f"Required column not found: {c}")

    if liq_col not in df.columns:
        raise KeyError(f"Liquidity column not found: {liq_col}")

    meta_candidates = [
        "PERMNO", "name", "SICCD", "HSICMG", "HSICIG",
        "PRIMEXCH", "HEXCD", "sharesOut", "volume", "NUMTRD"
    ]

    keep_cols = [date_col, ticker_col, ret_col, liq_col]
    keep_cols += [c for c in meta_candidates if c in df.columns and c not in keep_cols]
    df = df[keep_cols].copy()

    df[ticker_col] = df[ticker_col].astype(str)
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    numeric_cols = [ret_col, liq_col, "sharesOut", "NUMTRD"]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=[ticker_col, date_col, ret_col])
    df = df[np.isfinite(df[ret_col])]
    df = df[(df[ret_col] > -1.0) & (df[ret_col] < 1.0)]

    if liq_col in df.columns:
        df = df[df[liq_col].fillna(0) >= 0]

    df = df.sort_values([date_col, ticker_col]).reset_index(drop=True)

    num_dates = df[date_col].nunique()
    obs_count = df.groupby(ticker_col)[date_col].nunique().sort_values(ascending=False)
    min_required_days = int(min_history_ratio * num_dates)
    eligible_tickers = obs_count[obs_count >= min_required_days].index.tolist()

    if not eligible_tickers:
        raise ValueError("No stocks passed the minimum history requirement.")

    df_eligible = df[df[ticker_col].isin(eligible_tickers)].copy()

    liq_rank = (
        df_eligible.groupby(ticker_col)[liq_col]
        .median()
        .sort_values(ascending=False)
    )

    selected_tickers = liq_rank.head(top_n_stocks).index.tolist()

    if not selected_tickers:
        raise ValueError("No stocks selected after liquidity ranking.")

    df_ready = df[df[ticker_col].isin(selected_tickers)].copy()
    df_ready = df_ready.sort_values([date_col, ticker_col]).reset_index(drop=True)

    ret_mat = df_ready.pivot_table(
        index=date_col,
        columns=ticker_col,
        values=ret_col
    ).sort_index()

    min_non_na = int(min_history_ratio * len(ret_mat))
    valid_cols = ret_mat.columns[ret_mat.notna().sum() >= min_non_na]
    ret_mat = ret_mat[valid_cols].copy()
    ret_mat = ret_mat.fillna(0.0)

    meta_keep = [c for c in [
        "PERMNO", "name", "SICCD", "HSICMG", "HSICIG",
        "PRIMEXCH", "HEXCD", "sharesOut", "volume", "NUMTRD"
    ] if c in df_ready.columns]

    agg_map = {}
    for c in meta_keep:
        if c in ["volume", "NUMTRD", "sharesOut"]:
            agg_map[c] = "median"
        else:
            agg_map[c] = "last"

    meta = (
        df_ready.sort_values(date_col)
        .groupby(ticker_col)
        .agg(agg_map)
    )

    meta = meta.reindex(ret_mat.columns)

    summary = {
        "raw_rows": len(df),
        "prepared_rows": len(df_ready),
        "num_dates": int(df_ready[date_col].nunique()),
        "selected_stocks": int(len(ret_mat.columns)),
        "date_start": str(df_ready[date_col].min().date()) if len(df_ready) else None,
        "date_end": str(df_ready[date_col].max().date()) if len(df_ready) else None,
        "min_required_days": int(min_required_days),
    }

    return df_ready, ret_mat, meta, selected_tickers, summary


def save_outputs(
    output_dir: str,
    df_ready: pd.DataFrame,
    ret_mat: pd.DataFrame,
    meta: pd.DataFrame,
    selected_tickers: list,
    summary: dict,
):
    os.makedirs(output_dir, exist_ok=True)

    df_ready_csv = os.path.join(output_dir, "df_ready.csv")
    ret_mat_csv = os.path.join(output_dir, "ret_mat.csv")
    meta_csv = os.path.join(output_dir, "meta.csv")
    tickers_txt = os.path.join(output_dir, "selected_tickers.txt")
    summary_txt = os.path.join(output_dir, "summary.txt")

    df_ready.to_csv(df_ready_csv, index=False)
    ret_mat.to_csv(ret_mat_csv)
    meta.to_csv(meta_csv)

    with open(tickers_txt, "w", encoding="utf-8") as f:
        for t in selected_tickers:
            f.write(f"{t}\n")

    with open(summary_txt, "w", encoding="utf-8") as f:
        for k, v in summary.items():
            f.write(f"{k}: {v}\n")

    print("\nSaved files:")
    print(df_ready_csv)
    print(ret_mat_csv)
    print(meta_csv)
    print(tickers_txt)
    print(summary_txt)


def main():
    parser = argparse.ArgumentParser(description="Prepare stock network data from daily csv.gz files.")
    parser.add_argument("--data_root", type=str, required=True, help="Root folder containing daily .csv.gz files")
    parser.add_argument("--output_dir", type=str, default="prepared_output", help="Folder to save outputs")
    parser.add_argument("--ret_col", type=str, default="fret_RR_CLCL", help="Return column to use")
    parser.add_argument("--ticker_col", type=str, default="ticker", help="Ticker column")
    parser.add_argument("--date_col", type=str, default="date", help="Date column to create")
    parser.add_argument("--liq_col", type=str, default="volume", help="Liquidity column for ranking")
    parser.add_argument("--top_n_stocks", type=int, default=100, help="Number of stocks to keep")
    parser.add_argument("--min_history_ratio", type=float, default=0.80, help="Minimum fraction of dates a stock must appear")
    args = parser.parse_args()

    print("Loading raw files...")
    df = load_all_files(data_root=args.data_root, date_col=args.date_col)

    print("\nPreparing cleaned dataset...")
    df_ready, ret_mat, meta, selected_tickers, summary = clean_and_prepare(
        df=df,
        ret_col=args.ret_col,
        ticker_col=args.ticker_col,
        date_col=args.date_col,
        liq_col=args.liq_col,
        top_n_stocks=args.top_n_stocks,
        min_history_ratio=args.min_history_ratio,
    )

    print("\nSummary:")
    for k, v in summary.items():
        print(f"{k}: {v}")

    save_outputs(
        output_dir=args.output_dir,
        df_ready=df_ready,
        ret_mat=ret_mat,
        meta=meta,
        selected_tickers=selected_tickers,
        summary=summary,
    )


if __name__ == "__main__":
    main()