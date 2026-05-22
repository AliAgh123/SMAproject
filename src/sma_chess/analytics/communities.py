from networkx.algorithms.community import greedy_modularity_communities


def detect_communities(G):
    """
    Network analysis
    """
    # Community Detection (Using built-in library)
    # Convert to undirected temporarily for community detection
    undirected_G = G.to_undirected()
    # Using greedy modularity to find clusters of game states
    communities = list(greedy_modularity_communities(undirected_G))
    print(f"\nDetected {len(communities)} distinct communities (clusters of game states).")

    return communities