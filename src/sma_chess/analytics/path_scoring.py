from __future__ import annotations

from typing import Literal

import networkx as nx


PathPerspective = Literal["optimal", "white", "black"]


def _active_player(graph: nx.DiGraph, node: str) -> str:
    fen = graph.nodes[node].get("fen", "")
    parts = fen.split()
    if len(parts) >= 2 and parts[1] in {"w", "b"}:
        return parts[1]
    return "w"


def _terminal_expected_value(graph: nx.DiGraph, path: list[str]) -> float:
    return graph.nodes[path[-1]].get("expected_value", 0.0) or 0.0


def get_top_weighted_paths(
    graph: nx.DiGraph,
    start_node: str,
    depth_limit: int = 4,
    top_k: int = 5,
    beam_width: int | None = 2,
    perspective: PathPerspective = "optimal",
) -> list[tuple[list[str], float]]:
    """
    Find high-scoring paths with a depth-limited, beam-pruned search.

    The step score is interpreted from the active player's perspective:
    white prefers positive expected value, while black prefers negative expected
    value. Final ranking can then be filtered by `perspective`.
    """
    if depth_limit < 0:
        raise ValueError("depth_limit must be non-negative")
    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    if beam_width is not None and beam_width < 1:
        raise ValueError("beam_width must be at least 1 when provided")
    if perspective not in {"optimal", "white", "black"}:
        raise ValueError("perspective must be one of: optimal, white, black")
    if start_node not in graph:
        raise ValueError(f"start_node is not in graph: {start_node}")

    valid_paths: list[tuple[list[str], float]] = []

    def custom_dfs(
        current_node: str,
        current_path: list[str],
        current_score: float,
        current_depth: int,
    ) -> None:
        if current_depth == depth_limit or graph.out_degree(current_node) == 0:
            valid_paths.append((current_path, current_score))
            return

        player_multiplier = 1 if _active_player(graph, current_node) == "w" else -1
        candidates = []

        for next_node in graph.successors(current_node):
            edge_prob = graph[current_node][next_node].get("weight", 0.0)
            child_ev = graph.nodes[next_node].get("expected_value", 0.0) or 0.0
            step_score = edge_prob * child_ev * player_multiplier
            candidates.append((next_node, step_score))

        candidates.sort(key=lambda item: item[1], reverse=True)
        if beam_width is not None:
            candidates = candidates[:beam_width]

        for next_node, step_score in candidates:
            custom_dfs(
                next_node,
                current_path + [next_node],
                current_score + step_score,
                current_depth + 1,
            )

    custom_dfs(start_node, [start_node], 0.0, 0)

    if perspective == "white":
        valid_paths.sort(key=lambda item: _terminal_expected_value(graph, item[0]), reverse=True)
    elif perspective == "black":
        valid_paths.sort(key=lambda item: _terminal_expected_value(graph, item[0]))
    else:
        valid_paths.sort(key=lambda item: item[1], reverse=True)

    return valid_paths[:top_k]
