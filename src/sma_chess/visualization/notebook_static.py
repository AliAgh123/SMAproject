from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.lines import Line2D
from networkx.algorithms.community import greedy_modularity_communities


def _save_and_show(save_path=None, show=True):
    fig = plt.gcf()
    if save_path is not None:
        output = Path(save_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, bbox_inches="tight")
    if show:
        plt.show()
    return fig


def plot_chess_superstructure(G, save_path=None, show=True, top_n=6000):
    #Let's look at your cool supergraph guys.

    # We Filter the graph (Top 300 most visited nodes)
    TOP_N = top_n
    sorted_nodes = sorted(G.nodes(data=True), key=lambda x: x[1].get('visits', 0), reverse=True)
    core_nodes = [n[0] for n in sorted_nodes[:TOP_N]]
    core_G = G.subgraph(core_nodes)

    # We know the first node is the one with the most visits. I want to color it in red for explainability
    first_node_hash = core_nodes[0]

    plt.figure(figsize=(14, 12))

    # layout
    pos = nx.spring_layout(core_G, k=0.3, iterations=50)

    # All the other nodes and edges

    # Separate nodes and edges
    other_nodes = [node for node in core_G.nodes() if node != first_node_hash]
    other_edges = [(u, v) for u, v in core_G.edges() if u != first_node_hash]

    # Draw standard nodes
    nx.draw_networkx_nodes(core_G, pos,
                           nodelist=other_nodes,
                           node_size=40,
                           node_color='#bdc3c7',
                           alpha=0.7)

    # Draw standard edges (probability colormap)
    other_edge_probs = [core_G[u][v].get('weight', 0.0) for u, v in other_edges]
    nx.draw_networkx_edges(
        core_G, pos,
        edgelist=other_edges,
        edge_color=other_edge_probs,
        edge_cmap=plt.cm.plasma,
        width=1.0,
        alpha=0.5, # Slightly transparent to let the root edges pop
        arrowsize=10,
        connectionstyle="arc3,rad=0.1"
    )

    # Now I want to draw the first node and it's connections (second moves)

    # Draw the starting node (larger, red, with a border)
    nx.draw_networkx_nodes(core_G, pos,
                           nodelist=[first_node_hash],
                           node_size=250, # Significantly larger
                           node_color='#e74c3c', # A clean, professional red
                           edgecolors='black',
                           linewidths=2,
                           alpha=1.0)

    # Draw direct connections from the start node (thicker, solid blue)
    direct_edges = [(u, v) for u, v in core_G.edges() if u == first_node_hash]
    nx.draw_networkx_edges(
        core_G, pos,
        edgelist=direct_edges,
        edge_color='#2980b9', # A sharp, structural blue
        width=3.0, # Thicker lines to show primary pathways
        alpha=1.0,
        arrowsize=15,
        connectionstyle="arc3,rad=0.1"
    )

    # A little makeup so it looks nice
    sm = plt.cm.ScalarMappable(cmap=plt.cm.plasma, norm=plt.Normalize(vmin=0, vmax=1))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=plt.gca(), fraction=0.046, pad=0.04)
    cbar.set_label('Transition Probability (Later Moves)', fontsize=12)

    plt.title('Chess Superstructure: Opening Transitions\n(Red: Starting Position | Blue: First Legal Moves)', fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    return _save_and_show(save_path=save_path, show=show)


def plot_expected_value_heatmap(G, save_path=None, show=True, top_n=6000):
    # expected value heatmap
    # 1. Extract the Core Network
    TOP_N = top_n
    sorted_nodes = sorted(G.nodes(data=True), key=lambda x: x[1].get('visits', 0), reverse=True)
    core_nodes = [n[0] for n in sorted_nodes[:TOP_N]]
    core_G = G.subgraph(core_nodes)

    pos = nx.spring_layout(core_G, k=0.3, iterations=50)

    # 3. Extract EVs for color mapping
    node_evs = [core_G.nodes[n].get('expected_value', 0.0) for n in core_G.nodes()]

    plt.figure(figsize=(14, 12))

    nx.draw_networkx_edges(core_G, pos,
                           edge_color='#ecf0f1',
                           alpha=0.4,
                           width=1.0,
                           arrows=False)

    nodes_plot = nx.draw_networkx_nodes(
        core_G, pos,
        node_size=120,
        node_color=node_evs,
        cmap=plt.cm.RdYlGn, # Red (Loss) -> Yellow (Draw/Eq) -> Green (Win)
        vmin=-1.0, # Minimum possible EV
        vmax=1.0,  # Maximum possible EV
        edgecolors='black',
        linewidths=0.5
    )

    # 6. Highlight the Starting Node (Thick blue border)
    first_node_hash = core_nodes[0]
    nx.draw_networkx_nodes(
        core_G, pos,
        nodelist=[first_node_hash],
        node_size=350,
        node_color=[core_G.nodes[first_node_hash].get('expected_value', 0.0)],
        cmap=plt.cm.RdYlGn,
        vmin=-1.0,
        vmax=1.0,
        edgecolors='#0000ff', # Blue highlight for the root
        linewidths=3
    )

    # 7. Add Colorbar & Polish
    cbar = plt.colorbar(nodes_plot, ax=plt.gca(), fraction=0.046, pad=0.04)
    cbar.set_label('Expected Value (Red = Trap/Loss, Green = Highly Favorable)', fontsize=12)

    plt.title('Network Heatmap: Positional Favorability (Expected Value)', fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    return _save_and_show(save_path=save_path, show=show)


def plot_centrality_overlap(G, save_path=None, show=True, top_n=6000):
    # Centrality overlap visualization
    # 1. Filter Graph
    TOP_N = top_n
    amount_2_draw = 15
    sorted_nodes = sorted(G.nodes(data=True), key=lambda x: x[1].get('visits', 0), reverse=True)
    core_nodes = [n[0] for n in sorted_nodes[:TOP_N]]
    core_G = G.subgraph(core_nodes)
    alpha = False
    # 2. Compute the Metrics strictly on our visual Core Graph
    print("Calculating Centrality Metrics...")

    # PageRank (Blue)
    pagerank = nx.pagerank(core_G, weight='weight')
    top_pr = set(sorted(pagerank, key=pagerank.get, reverse=True)[:amount_2_draw])

    # Betweenness (Yellow)
    betweenness = nx.betweenness_centrality(core_G)
    top_bet = set(sorted(betweenness, key=betweenness.get, reverse=True)[:amount_2_draw])

    # Out-Degree (Red)
    out_degree = dict(core_G.out_degree())
    top_out = set(sorted(out_degree, key=out_degree.get, reverse=True)[:amount_2_draw])

    # 3. Apply the Color Mixing Logic
    node_colors = []
    node_sizes = []

    for node in core_G.nodes():
        in_pr = node in top_pr
        in_bet = node in top_bet
        in_out = node in top_out

        # Check overlaps first (The Venn Diagram logic)
        if in_pr and in_bet and in_out:
            color = '#0031e2' # White (All three)
            size = 500
        elif in_pr and in_bet:
            color = '#2ecc71' # Green (Blue + Yellow)
            size = 350
        elif in_pr and in_out:
            color = '#9b59b6' # Purple (Blue + Red)
            size = 350
        elif in_bet and in_out:
            color = '#e67e22' # Orange (Yellow + Red)
            size = 350
        elif in_pr:
            color = '#3498db' # Blue
            size = 200
        elif in_bet:
            color = '#f1c40f' # Yellow
            size = 200
        elif in_out:
            color = '#e74c3c' # Red
            size = 200
        else:
            color = '#bdc3c7' # Light Gray
            size = 60
            alpha = True

        node_colors.append(color)
        node_sizes.append(size)

    plt.figure(figsize=(15, 13))
    pos = nx.spring_layout(core_G, k=0.35, iterations=50)

    nx.draw_networkx_edges(core_G, pos, edge_color='#ecf0f1', alpha=0.4, width=1.0, arrows=False)

    if alpha:
      nx.draw_networkx_nodes(core_G, pos,
                           node_size=node_sizes,
                           node_color=node_colors,
                           edgecolors='#2c3e50', # Dark border to make white/yellow pop
                           linewidths=1.5, alpha=0.3)
      alpha = False
    else:
      nx.draw_networkx_nodes(core_G, pos,
                           node_size=node_sizes,
                           node_color=node_colors,
                           edgecolors='#2c3e50', # Dark border to make white/yellow pop
                           linewidths=1.5)

    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='PageRank (Hub) - Blue', markerfacecolor='#3498db', markersize=12),
        Line2D([0], [0], marker='o', color='w', label='Betweenness (Bridge) - Yellow', markerfacecolor='#f1c40f', markersize=12),
        Line2D([0], [0], marker='o', color='w', label='Out-Degree (Complex) - Red', markerfacecolor='#e74c3c', markersize=12),
        Line2D([0], [0], marker='o', color='w', label='PR + Betweenness - Green', markerfacecolor='#2ecc71', markersize=14),
        Line2D([0], [0], marker='o', color='w', label='PR + Out-Degree - Purple', markerfacecolor='#9b59b6', markersize=14),
        Line2D([0], [0], marker='o', color='w', label='Betweenness + Out - Orange', markerfacecolor='#e67e22', markersize=14),
        Line2D([0], [0], marker='o', color='w', label='All Three Metrics - White', markerfacecolor='#ffffff', markeredgecolor='black', markersize=16),
    ]

    plt.legend(handles=legend_elements, loc='upper left', title="Top 10 Centrality Metrics",
               fontsize=11, title_fontsize=13, framealpha=0.9)

    plt.title('Network Centrality Overlap: Structural Importance vs Tactical Complexity', fontsize=18, pad=20)
    plt.axis('off')
    plt.tight_layout()
    return _save_and_show(save_path=save_path, show=show)


def plot_macro_structure_top_paths(G, first_node_hash, top_paths, save_path=None, show=True, top_n=6000):
    TOP_N = top_n
    sorted_nodes = sorted(G.nodes(data=True), key=lambda x: x[1].get('visits', 0), reverse=True)
    core_nodes = [n[0] for n in sorted_nodes[:TOP_N]]
    core_G = G.subgraph(core_nodes)

    # 2. Community Detection
    undirected_core = core_G.to_undirected()
    communities = list(greedy_modularity_communities(undirected_core))

    community_colors = ['#2c3e50', '#18bc9c', '#3498db', '#8e44ad', '#d35400', '#16a085', '#27ae60']
    node_color_map = {}

    for i, comm in enumerate(communities):
        color = community_colors[i] if i < len(community_colors) else '#bdc3c7'
        for node in comm:
            if node in core_G:
                node_color_map[node] = color

    node_colors = [node_color_map.get(n, '#bdc3c7') for n in core_G.nodes()]
    node_sizes = [200 if n == first_node_hash else 60 for n in core_G.nodes()]

    plt.figure(figsize=(18, 14)) # Slightly larger canvas
    pos = nx.spring_layout(core_G, k=0.15, iterations=60, seed=42) # k=0.25 spreads the expanded clusters out nicely

    # Draw standard edges and nodes
    nx.draw_networkx_edges(core_G, pos, edge_color='#ecf0f1', alpha=0.3, width=0.8, arrows=False)
    nx.draw_networkx_nodes(core_G, pos, node_size=node_sizes, node_color=node_colors, edgecolors='#ffffff', linewidths=0.5, alpha=0.3)

    # We create a gradient style for the paths: Gold (Rank 1) -> Purple (Rank 5)
    path_colors = ['#f1c40f', '#e67e22', '#e74c3c', '#c0392b', '#9b59b6']
    path_widths = [5.0, 3.5, 2.5, 2.0, 1.5]
    path_alphas = [1.0, 0.9, 0.8, 0.7, 0.6]

    for rank in range(min(5, len(top_paths))):
        path_nodes = top_paths[rank][0]
        path_edges = [(path_nodes[i], path_nodes[i+1]) for i in range(len(path_nodes)-1)]

        drawable_edges = [(u, v) for u, v in path_edges if u in core_G and v in core_G]
        drawable_nodes = [n for n in path_nodes if n in core_G]

        # Highlight Path Nodes
        nx.draw_networkx_nodes(core_G, pos, nodelist=drawable_nodes, node_size=100,
                               node_color=[node_color_map.get(n) for n in drawable_nodes],
                               edgecolors=path_colors[rank], linewidths=path_widths[rank]/1.5, alpha=0.5)

        # Highlight Path Edges
        nx.draw_networkx_edges(core_G, pos, edgelist=drawable_edges, edge_color=path_colors[rank],
                               width=path_widths[rank], alpha=path_alphas[rank],
                               arrowsize=15, connectionstyle="arc3,rad=0.15")

    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='Cluster 1 (Primary)', markerfacecolor=community_colors[0], markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Cluster 2', markerfacecolor=community_colors[1], markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Cluster 3', markerfacecolor=community_colors[2], markersize=10),
        Line2D([0], [0], color='w', label='-------------------'),
        Line2D([0], [0], color=path_colors[0], lw=5, label='Rank 1 Path (Optimal)'),
        Line2D([0], [0], color=path_colors[1], lw=3.5, label='Rank 2 Path'),
        Line2D([0], [0], color=path_colors[2], lw=2.5, label='Rank 3 Path'),
        Line2D([0], [0], color=path_colors[3], lw=2, label='Rank 4 Path'),
        Line2D([0], [0], color=path_colors[4], lw=1.5, label='Rank 5 Path'),
    ]

    plt.legend(handles=legend_elements, loc='upper right', title="Network Structure & Top Paths",
               fontsize=10, title_fontsize=12, framealpha=0.9)

    plt.title('Macro-Structure & Top 5 Algorithmic Paths', fontsize=18, pad=20)
    plt.axis('off')
    plt.tight_layout()
    return _save_and_show(save_path=save_path, show=show)


def plot_algorithm_performance(y_test, y_pred, r2, rmse, save_path=None, show=True):
    plt.figure(figsize=(10, 8))

    # Scatter plot of True vs Predicted scores
    plt.scatter(y_test, y_pred, color='#18bc9c', alpha=0.6, edgecolor='white', s=60, label='Predicted Paths')

    min_val = min(y_test.min(), y_pred.min())
    max_val = max(y_test.max(), y_pred.max())
    plt.plot([min_val, max_val], [min_val, max_val], color='#f1c40f', linestyle='--', linewidth=2, label='Perfect Prediction')

    plt.title('Algorithm Performance: Actual vs. Predicted Path Scores', fontsize=16, pad=15)
    plt.xlabel('Actual Outcome-Weighted Score (Calculated by DFS)', fontsize=13)
    plt.ylabel('Machine Learning Predicted Score (Random Forest)', fontsize=13)

    plt.text(min_val + 0.02, max_val - 0.05, f'R² Score: {r2:.3f}\nRMSE: {rmse:.3f}',
             fontsize=14, color='white', bbox=dict(facecolor='#2c3e50', alpha=0.8, edgecolor='none', pad=10))

    plt.legend(loc='lower right', fontsize=12)
    plt.grid(color='#34495e', linestyle='-', linewidth=0.5, alpha=0.5)
    plt.tight_layout()
    fig = _save_and_show(save_path=save_path, show=show)

    plt.style.use('default')
    return fig


def plot_ablation_depth_comparison(df_limited, df_unconstrained, save_path='ablation_depth_comparison.pdf', show=True):
    # ──────────────────────────────────────────────────────────────
    # Plotting — 2 rows × 2 cols
    #   Row 1: depth-limited    (time | score)
    #   Row 2: unconstrained    (time | score)
    # ──────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(2, 2, figsize=(18, 12))
    fig.suptitle('Ablation Study: Depth-Limited vs. Unconstrained Search',
                 fontsize=16, fontweight='bold', y=1.01)

    bar_width = 0.25

    for row, (df, title_tag) in enumerate([(df_limited,       'Depth-Limited  (d = 4)'),
                                            (df_unconstrained, 'Unconstrained')]):

        ax_time, ax_score = axes[row]
        x = np.arange(len(df['Nodes']))

        # ── Time plot ────────────────────────────────────────────
        ax_time.plot(df['Nodes'], df['Time_Custom_DFS'],
                     marker='o', color='#f1c40f', linewidth=2.5, label='Custom DFS (ours)')
        ax_time.plot(df['Nodes'], df['Time_NX_DFS'],
                     marker='s', color='#3498db', linewidth=2, linestyle='--', label='NetworkX DFS')
        ax_time.plot(df['Nodes'], df['Time_NX_BFS'],
                     marker='^', color='#1abc9c', linewidth=2, linestyle='--', label='NetworkX BFS')
        ax_time.plot(df['Nodes'], df['Time_Dijkstra'],
                     marker='D', color='#e74c3c', linewidth=2, label='Dijkstra (optimal)')
        ax_time.set_yscale('log')
        ax_time.set_title(f'{title_tag} — Execution Time', fontsize=13)
        ax_time.set_xlabel('Number of Nodes')
        ax_time.set_ylabel('Time (seconds, log scale)')
        ax_time.grid(color='#34495e', linestyle=':', alpha=0.5)
        ax_time.legend(fontsize=9)

        # ── Score plot ───────────────────────────────────────────
        ax_score.bar(x - bar_width, df['Score_Optimal'],
                     width=bar_width, color='#e74c3c', label='Optimal ceiling (Dijkstra)')
        ax_score.bar(x,             df['Score_Custom'],
                     width=bar_width, color='#f1c40f', label='Custom DFS (ours)')
        ax_score.bar(x + bar_width, df['Score_Random'],
                     width=bar_width, color='#95a5a6', label='Naïve baseline (random)')
        ax_score.set_title(f'{title_tag} — Path Quality', fontsize=13)
        ax_score.set_xlabel('Number of Nodes')
        ax_score.set_ylabel('Outcome-Weighted Path Score')
        ax_score.set_xticks(x)
        ax_score.set_xticklabels(df['Nodes'], rotation=45)
        ax_score.grid(axis='y', color='#34495e', linestyle=':', alpha=0.5)
        ax_score.legend(fontsize=9)

    plt.tight_layout()
    if save_path is not None:
        output = Path(save_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output, bbox_inches='tight')
    if show:
        plt.show()

    print("\n=== Depth-Limited Results ===")
    print(df_limited[['Nodes','Time_Custom_DFS','Time_Dijkstra',
                       'Score_Custom','Score_Optimal','Score_Random']].to_string(index=False))

    print("\n=== Unconstrained Results ===")
    print(df_unconstrained[['Nodes','Time_Custom_DFS','Time_Dijkstra',
                             'Score_Custom','Score_Optimal','Score_Random']].to_string(index=False))

    return fig
