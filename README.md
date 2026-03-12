# MATH 168 - Networks Group Project

This project analyzes financial market correlations by building networks from stock return similarities. We identify industry clusters and central market influencers using 5-day log returns and cosine distance metrics.

## Setup & Running

### 1. Download Dataset

Before running the project, download the raw stock data and place it in the `data/` directory:

- [Download Dataset (Google Drive)](https://drive.google.com/file/d/1cEzKmWXDQkTdpLI9VeJsPMcXdQXswDwo/view?usp=sharing)
- Extract the zip file directly into the `data/` directory (this will create `data/Yearly/`).
- Ensure your structure looks like: `data/Yearly/2021/`, `data/Yearly/2022/`, etc.

### 2. Environment Setup (Standard Pip)

Create a virtual environment and install the required dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
pip install pandas numpy networkx scikit-learn matplotlib jupyter
```

### 3. Data Processing

Calculate 5-day log returns and generate similarity matrices:

```bash
python data_processor.py
```

_This will clean the data and output results to the `output/` directory._

### 4. Network Analysis

Run the main analysis script to build the network and view top correlations:

```bash
python main.py
```

### 5. Interactive Exploration

For deep-dive analysis (MST, centrality, etc.), use the Jupyter Notebook:

```bash
jupyter notebook analyze_network.ipynb
```

---

## Alternative Methodology: `uv`

If you have `uv` installed, you can skip the manual environment setup:

1. **Initialize**: `uv sync`
2. **Run Scripts**:
   - `uv run data_processor.py`
   - `uv run main.py`
   - `uv run jupyter notebook analyze_network.ipynb`

[Install uv](https://docs.astral.sh/uv/getting-started/installation/)

---

## Utilities

The `utils/` folder contains scripts for project maintenance and metadata gathering:

- `utils/stocks_list.py`: Fetches a fresh list of active stock tickers and company names from the Polygon API (requires `POLYGON_API_KEY` in `.env`). Saved to `ticker_metadata/tickers.txt`.
- `utils/extract_siccd.py`: Scans the daily stock data files to extract unique SICCD (Standard Industrial Classification) codes for each ticker. Saved to `ticker_metadata/ticker_siccd.txt`.

Example usage:

```bash
# Update ticker names
python utils/stocks_list.py

# Extract industry codes from local data
python utils/extract_siccd.py
```
