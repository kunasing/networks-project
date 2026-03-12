from pathlib import Path

import networkx as nx
import pandas as pd


# SIC code division mapping
DIVISIONS = {
    range(100, 1000): "Agriculture, Forestry and Fishing",
    range(1000, 1500): "Mining",
    range(1500, 1800): "Construction",
    range(1800, 2000): "Not Used",
    range(2000, 4000): "Manufacturing",
    range(4000, 5000): "Transportation & Communications",
    range(5000, 5200): "Wholesale Trade",
    range(5200, 6000): "Retail Trade",
    range(6000, 6800): "Finance, Insurance & Real Estate",
    range(7000, 9000): "Services",
    range(9100, 9730): "Public Administration",
    range(9900, 10000): "Nonclassifiable",
}


def get_division(sic_code):
    """Map a numeric SIC code to its broad industry division name."""
    try:
        code = int(sic_code)
        for code_range, name in DIVISIONS.items():
            if code in code_range:
                return name
    except (ValueError, TypeError):
        pass
    return None


def load_similarity(output_dir: Path = Path("output")) -> pd.DataFrame:
    """Load the cosine similarity matrix from disk."""
    path = output_dir / "ticker_similarities.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Similarity matrix not found at {path}. Run data_processor.py first."
        )
    return pd.read_csv(path, index_col=0)


def build_network(dist_df: pd.DataFrame) -> nx.Graph:
    """Build a weighted graph from a cosine-distance DataFrame, removing self-loops."""
    G = nx.from_pandas_adjacency(dist_df)
    G.remove_edges_from(nx.selfloop_edges(G))
    print(f"Graph built with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    return G
