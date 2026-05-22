import networkx as nx


"""
NETWORK EXPLORATION
"""


def get_network_density(graph: nx.DiGraph) -> float:
    # Structural properties
    return nx.density(graph)


def print_network_density(graph: nx.DiGraph) -> None:
    # Structural properties
    print(f"Network Density: {nx.density(graph):.5f}")


def get_structural_properties(graph: nx.DiGraph) -> dict:
    # Structural properties
    return {
        "total_nodes": graph.number_of_nodes(),
        "total_edges": graph.number_of_edges(),
        "density": nx.density(graph),
        "is_directed": graph.is_directed(),
    }
