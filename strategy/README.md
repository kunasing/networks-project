# Network Strategy Experiments

This folder contains additional analysis and experimental trading strategies built on top of the stock correlation network from the main project.

The goal is to explore whether **network topology (clusters and centrality)** can generate useful trading signals.

## Directory Structure

```shell

strategy/
│
├── prepare_stock_data.py
├── analysis.ipynb
├── README.md
│
├── data/
│   └── Yearly/
│       ├── 2021/
│       ├── 2022/
│       ├── 2023/
│       └── 2024/
│
└── prepared_output/
├── df_ready.csv
├── ret_mat.csv
├── meta.csv
├── selected_tickers.txt
└── summary.txt

```

## Setup

Install dependencies:

```shell

pip install pandas numpy networkx scipy scikit-learn matplotlib jupyter

```

## Execution

### 1. Prepare the dataset

```shell

python prepare_stock_data.py --data_root data --output_dir prepared_output

```

This script:

- loads daily stock CSV files
- extracts dates from filenames
- filters liquid stocks
- builds a return matrix for network analysis

Outputs are saved in `prepared_output/`.

### 2. Run the analysis notebook

```shell

jupyter notebook analysis.ipynb

```

The notebook performs:

- network construction
- community detection
- centrality analysis
- visualization of the stock network
- backtesting of network-based strategies

## Strategies Tested

### Cluster Mean Reversion

Long stocks that underperform their network cluster and short those that outperform.

### Central-to-Peripheral Propagation

Use returns of highly central "hub" stocks as signals for peripheral stocks.

## Output

The notebook produces:

- network visualizations
- cluster analysis
- centrality rankings
- cumulative strategy returns
- benchmark comparison
