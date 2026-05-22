import networkx as nx


def compute_expected_value(outcomes: list[int] | None) -> float:
    # Outcomes: [White Win, Black Win, Draw]
    # Important: the graph-building pipeline stores outcomes in this order.
    if outcomes is None:
        outcomes = [0, 0, 0]

    W, L, D = outcomes[0], outcomes[1], outcomes[2]
    total = W + D + L

    if total > 0:
        return (W - L) / total
    else:
        return 0.0


def add_expected_values(graph: nx.DiGraph) -> nx.DiGraph:
    # Calculate and store Expected Value (E[v]) for every node
    for node in graph.nodes():
        # Outcomes: [White Win, Black Win, Draw]
        outcomes = graph.nodes[node].get('outcomes', [0, 0, 0])
        graph.nodes[node]['expected_value'] = compute_expected_value(outcomes)

    return graph
