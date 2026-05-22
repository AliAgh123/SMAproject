import chess
import networkx as nx


def compute_centrality_metrics(G, core_G):
    # Centrality: PageRank identifies 'hub' chess states that games frequently funnel through
    pagerank = nx.pagerank(G, weight='weight')
    top_pagerank_node = max(pagerank, key=pagerank.get)
    betweenness = nx.betweenness_centrality(core_G)
    top_bc = max(betweenness, key=betweenness.get)

    print("\n--- Network Centrality Metrics ---")
    print(f"Node with highest PageRank (Most Central State): {top_pagerank_node}")
    print(f"Highest PageRank Score: {pagerank[top_pagerank_node]:.5f}")
    print(f"Betweenesss centrality score: {top_bc}")

    return pagerank, top_pagerank_node, betweenness, top_bc


def node_info(node, G):
    data = G.nodes[node]
    outcomes = data.get('outcomes', [0, 0, 0]) or [0, 0, 0]
    W, L, D = outcomes[0], outcomes[1], outcomes[2]
    total = W + D + L
    return {
        'node':           node,
        'fen':            data.get('fen', 'N/A'),
        'visits':         total,
        'wins':           W,
        'draws':          D,
        'losses':         L,
        'expected_value': data.get('expected_value', 0.0),
    }


def print_top3(metric_name, scores, G):
    top3 = sorted(scores, key=scores.get, reverse=True)[:3]
    print(f"\n{'='*60}")
    print(f"  TOP 3 — {metric_name}")
    print(f"{'='*60}")
    for rank, node in enumerate(top3, 1):
        info = node_info(node, G)
        print(f"\n  #{rank}  Score: {scores[node]:.6f}")
        print(f"  FEN:    {info['fen']}")
        print(f"  Visits: {info['visits']:,}  (W:{info['wins']} D:{info['draws']} L:{info['losses']})")
        print(f"  E[v]:   {info['expected_value']:+.4f}")
        print(chess.Board(info['fen']))


def print_network_measures(G, core_G):
    # Compute metrics
    pagerank    = nx.pagerank(G, weight='weight')
    betweenness = nx.betweenness_centrality(core_G)
    in_degree   = dict(G.in_degree())
    out_degree  = dict(G.out_degree())

    # Top 3
    print_top3("PageRank (most central states)",     pagerank,    G)
    print_top3("Betweenness Centrality (bottlenecks)", betweenness, core_G)
    print_top3("In-Degree (most arrived at)",        in_degree,   G)
    print_top3("Out-Degree (most branching)",        out_degree,  G)

    return pagerank, betweenness, in_degree, out_degree
