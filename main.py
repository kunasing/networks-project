import sys
from pathlib import Path

import networkx as nx
import pandas as pd


def main():
    output_dir = Path("output")
    similarity_file = output_dir / "ticker_similarities.csv"

    # Check if a checkpoint exists
    if not similarity_file.exists():
        print(f"Error: Similarity matrix checkpoint {similarity_file} does not exist.")
        print("Please run data_processor.py first.")
        sys.exit(1)

    print(f"Loading similarity matrix from checkpoint: {similarity_file}...")
    # Load the CSV. index_col=0 assumes ticker names are in the first column
    sim_df = pd.read_csv(similarity_file, index_col=0)

    G = build_network(sim_df)
    display(G)


def build_network(sim_df):
    print("Building a dense graph from similarity matrix...")
    # Create a graph from the similarity matrix
    # We use the index/columns as nodes and row values as edge weights
    G = nx.from_pandas_adjacency(sim_df)

    # Remove self-loops (diagonal of the matrix is 1.0)
    G.remove_edges_from(nx.selfloop_edges(G))

    print(
        f"Graph built with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges."
    )
    return G


def display(G):
    # Because the graph is dense (N^2 edges), we might want to filter or summarize
    print("\n--- Network Summary ---")
    print(f"Nodes: {G.number_of_nodes()}")
    print(f"Edges: {G.number_of_edges()}")

    # For very large dense graphs, drawing is often uninformative or slow.
    # However, we can show the top connected pairs.
    print("\nTop 5 Most Similar Ticker Pairs:")
    edges = sorted(
        G.edges(data=True), key=lambda x: x[2].get("weight", 0), reverse=True
    )
    for u, v, d in edges:
        if d["weight"] == 1:
            pass
        if d["weight"] <= 0.9:
            break
        print(f"{u} <-> {v}: {d['weight']:.4f}")


if __name__ == "__main__":
    main()
