
# Custom Algorithm: Outcome-Weighted Path Scoring (From Scratch)
def get_top_weighted_paths(graph, start_node, depth_limit=4, top_k=5):
    """
    Custom Depth-Limited DFS to find the highest-scoring tactical paths.
    Does not use external pathfinding libraries.
    """
    valid_paths = []

    def custom_dfs(current_node, current_path, current_score, current_depth):
        # Base case: reached depth limit or a leaf node (checkmate/draw/end of data)
        if current_depth == depth_limit or graph.out_degree(current_node) == 0:
            valid_paths.append((current_path, current_score))
            return

        # Recursive case: explore successors
        for next_node in graph.successors(current_node):
            edge_prob = graph[current_node][next_node].get('weight', 0.0) #current edge probability
            child_ev = graph.nodes[next_node].get('expected_value', 0.0) #success of move given the future step/child

            # Heuristic calculation: Edge Probability * Expected Value of the outcome
            step_score = edge_prob * child_ev

            # Continue search deeper
            custom_dfs(next_node,
                       current_path + [next_node],
                       current_score + step_score,
                       current_depth + 1)

    # Initialize DFS from the starting node
    custom_dfs(start_node, [start_node], 0.0, 0)

    # Sort paths by score descending (from scratch sorting logic via lambda)
    valid_paths.sort(key=lambda x: x[1], reverse=True)

    return valid_paths[:top_k]