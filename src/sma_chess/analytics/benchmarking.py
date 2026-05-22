import time
import random
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

from sma_chess.analytics.path_scoring import get_top_weighted_paths


NODE_SIZES = [100, 300, 500, 1000, 1500, 3000, 5000, 6000]


def run_benchmark(
    G,
    node_sizes=None,
    depth_limit=4,
    beam_width=2,
    perspective="optimal",
):
    print("Benchmarking")

    if node_sizes is None:
        node_sizes = NODE_SIZES

    results = []

    # Ensure Djistra inversion of the metric (cost becomes max value)
    for u, v, data in G.edges(data=True):
        prob = data.get('weight', 0.0)
        ev = G.nodes[v].get('expected_value', 0.0)
        # We add 1e-6 to avoid zero division, and max to avoid negative costs
        G[u][v]['cost'] = 1.0 / max(prob * ev + 1e-6, 1e-6)

    # The Benchmarking Loop
    for size in tqdm(node_sizes):

        # Extract Subgraph
        sorted_nodes = sorted(G.nodes(data=True), key=lambda x: x[1].get('visits', 0), reverse=True)
        subgraph_nodes = [n[0] for n in sorted_nodes[:size]]
        subG = G.subgraph(subgraph_nodes).copy()
        start_node = subgraph_nodes[0]

        # 1. Custom DFS (Ours)
        start_time = time.perf_counter()
        # (Assuming your get_top_weighted_paths function is loaded in the script)
        effective_depth = depth_limit if depth_limit is not None else len(subG)

        custom_paths = get_top_weighted_paths(
            subG,
            start_node,
            depth_limit=effective_depth,
            top_k=1,
            beam_width=beam_width,
            perspective=perspective,
        )
        time_custom = time.perf_counter() - start_time
        score_custom = custom_paths[0][1] if custom_paths else 0

        # 2. NetworkX DFS (Blind Traversal)
        start_time = time.perf_counter()
        if depth_limit is None:
            list(nx.dfs_edges(subG, source=start_node))
        else:
            list(nx.dfs_edges(subG, source=start_node, depth_limit=depth_limit))
        time_nx_dfs = time.perf_counter() - start_time

        # 3. NetworkX BFS (Blind Traversal)
        start_time = time.perf_counter()
        if depth_limit is None:
            list(nx.bfs_edges(subG, source=start_node))
        else:
            list(nx.bfs_edges(subG, source=start_node, depth_limit=depth_limit))
        time_nx_bfs = time.perf_counter() - start_time

        # 4. Dijkstra's Algorithm (Optimal Score)
        start_time = time.perf_counter()
        try:
            # Find all nodes that are exactly depth_limit away.
            if depth_limit is None:
                depth_map = nx.single_source_shortest_path_length(subG, start_node)
            else:
                depth_map = nx.single_source_shortest_path_length(subG, start_node, cutoff=depth_limit)
            max_depth = max(depth_map.values()) if depth_map else 0
            target_nodes = [n for n, depth in depth_map.items() if depth == max_depth and n != start_node]

            optimal_path = []
            if target_nodes:
                lowest_cost = float('inf')

                # Ask Dijkstra for the lowest cost path to ANY of those boundary nodes
                for target in target_nodes:
                    try:
                        path = nx.shortest_path(subG, start_node, target, weight='cost')
                        # Calculate total path cost
                        cost = sum(subG[path[i]][path[i+1]]['cost'] for i in range(len(path)-1))
                        if cost < lowest_cost:
                            lowest_cost = cost
                            optimal_path = path
                    except nx.NetworkXNoPath:
                        continue
            else:
                optimal_path = [start_node]

            time_dijkstra = time.perf_counter() - start_time

            # Calculate our custom score for Dijkstra's chosen path
            score_dijkstra = 0
            if len(optimal_path) > 1:
                for i in range(len(optimal_path)-1):
                    u, v = optimal_path[i], optimal_path[i+1]
                    score_dijkstra += subG[u][v].get('weight', 0.0) * subG.nodes[v].get('expected_value', 0.0)

        except Exception as e:
            print(f"Dijkstra Error: {e}")
            time_dijkstra = 0
            score_dijkstra = 0

        # 5. Random Walk to compare for random path selections
        score_random = 0
        curr = start_node
        for _ in range(effective_depth):
            successors = list(subG.successors(curr))
            if not successors:
                break
            nxt = random.choice(successors)
            score_random += subG[curr][nxt].get('weight', 0.0) * subG.nodes[nxt].get('expected_value', 0.0)
            curr = nxt

        # Log results
        results.append({
            'Nodes': size,
            'Time_Custom_DFS': time_custom,
            'Time_NX_DFS': time_nx_dfs,
            'Time_NX_BFS': time_nx_bfs,
            'Time_Dijkstra': time_dijkstra,
            'Score_Custom': score_custom,
            'Score_Optimal': score_dijkstra,
            'Score_Random': score_random
        })

    return pd.DataFrame(results)


def plot_benchmark_results(df_bench, show=True):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # Plot 1: Execution Time (Log Scale)
    ax1.plot(df_bench['Nodes'], df_bench['Time_Custom_DFS'], marker='o', color='#f1c40f', linewidth=2.5, label='Custom DFS (Yours)')
    ax1.plot(df_bench['Nodes'], df_bench['Time_NX_DFS'], marker='s', color='#3498db', linewidth=2, linestyle='--', label='NetworkX DFS')
    ax1.plot(df_bench['Nodes'], df_bench['Time_NX_BFS'], marker='^', color='#1abc9c', linewidth=2, linestyle='--', label='NetworkX BFS')
    ax1.plot(df_bench['Nodes'], df_bench['Time_Dijkstra'], marker='D', color='#e74c3c', linewidth=2, label='Dijkstra (Optimal)')

    ax1.set_yscale('log') # Log scale because time grows exponentially
    ax1.set_title('Algorithm Scalability: Execution Time vs. Graph Size', fontsize=14, pad=10)
    ax1.set_xlabel('Number of Nodes in Graph', fontsize=12)
    ax1.set_ylabel('Execution Time (Seconds) - Log Scale', fontsize=12)
    ax1.grid(color='#34495e', linestyle=':', alpha=0.6)
    ax1.legend(loc='upper left', fontsize=10)

    # Plot 2: Path Quality (Accuracy)
    bar_width = 0.25
    x = np.arange(len(df_bench['Nodes']))

    ax2.bar(x - bar_width, df_bench['Score_Optimal'], width=bar_width, color='#e74c3c', label='Optimal Ceiling (Dijkstra)')
    ax2.bar(x, df_bench['Score_Custom'], width=bar_width, color='#f1c40f', label='Custom DFS (Ours)')
    ax2.bar(x + bar_width, df_bench['Score_Random'], width=bar_width, color='#95a5a6', label='Naive Baseline (Random)')

    ax2.set_title('Algorithm Accuracy: Path Quality Optimization', fontsize=14, pad=10)
    ax2.set_xlabel('Number of Nodes in Graph', fontsize=12)
    ax2.set_ylabel('Outcome-Weighted Path Score', fontsize=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels(df_bench['Nodes'])
    ax2.grid(axis='y', color='#34495e', linestyle=':', alpha=0.6)
    ax2.legend(loc='upper right', fontsize=10)

    plt.tight_layout()
    if show:
        plt.show()
    plt.style.use('default')

    return fig
