from pathlib import Path
import json
import networkx as nx


def load_graph_json(
    path: str | Path,
    *,
    sort_by_visits: bool = True,
    keep_only_known_targets: bool = True,
) -> nx.DiGraph:
    """
    Load a chess graph from a JSON file and construct a directed graph.

    Parameters:
        path (str | Path): The path to the JSON file.
        sort_by_visits (bool): Whether to sort nodes by visit count.
        keep_only_known_targets (bool): Whether to keep only nodes with known targets.

    Returns:
        nx.DiGraph: The constructed directed graph.
    """
    with open(path, "r") as f:
        data = json.load(f)
    ordered_data = data
    if sort_by_visits: # 2. Sort the data by 'total_visits' descending
        # This ensures the starting position (most visits) is at index 0
        sorted_items = sorted(
            data.items(), 
            key=lambda x: x[1].get("total_visits", 0), 
            reverse=True
        )

        # Convert back to an ordered dictionary
        ordered_data = dict(sorted_items)
        
    # 3. Construct the Directed Graph
    graph = nx.DiGraph()

    # Add nodes first to preserve the 'topological' visit-based order
    for node_hash, node_info in ordered_data.items():
        graph.add_node(node_hash, 
                fen=node_info.get('fen'),
                visits=node_info.get('total_visits'),
                outcomes=node_info.get('outcomes'))

    # Now add the edges
    for node_hash, node_info in ordered_data.items():
        edges = node_info.get('edges', {})
        for next_hash, edge_data in edges.items():
            # We only add edges if the destination exists in our node list
            if keep_only_known_targets and not graph.has_node(next_hash):
                continue
            graph.add_edge(node_hash, next_hash, 
                    weight=edge_data['prob'], 
                    count=edge_data['count'])


    
    return graph


def get_start_node(graph: nx.DiGraph) -> str:
    # 4. Verify the "First" Node
    first_node_hash = max(
        graph.nodes,
        key=lambda node_hash: graph.nodes[node_hash].get("visits", 0) or 0,
    )
    first_node_data = graph.nodes[first_node_hash]
    return first_node_hash, first_node_data

def summarize_graph(graph: nx.DiGraph) -> dict:
    first_node_hash, first_node_data = get_start_node(graph)
    return {
        "total_nodes": graph.number_of_nodes(),
        "total_edges": graph.number_of_edges(),
        "first_node_hash": first_node_hash,
        "first_node_visits": first_node_data['visits'],
        "first_node_fen": first_node_data['fen']
    }


def print_graph_summary(graph: nx.DiGraph) -> None:
    summary = summarize_graph(graph)
    print(f"Total Nodes: {summary['total_nodes']}")
    print(f"Total Edges: {summary['total_edges']}")
    print(f"First Node Hash: {summary['first_node_hash']}")
    print(f"First Node Visits: {summary['first_node_visits']}")
    print(f"First Node FEN: {summary['first_node_fen']}")
