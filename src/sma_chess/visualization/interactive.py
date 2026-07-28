from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Literal

import chess
import chess.svg
import networkx as nx
from pyvis.network import Network


ColorMode = Literal["ev", "pagerank", "visits", "community"]


EV_COLORS = {
    "positive": "#16a34a",
    "neutral": "#64748b",
    "negative": "#dc2626",
}
COMMUNITY_COLORS = [
    "#2563eb",
    "#16a34a",
    "#dc2626",
    "#9333ea",
    "#ea580c",
    "#0891b2",
    "#be123c",
    "#4f46e5",
    "#65a30d",
    "#ca8a04",
]


def _scaled(value: float, low: float, high: float, out_low: float, out_high: float) -> float:
    if high <= low:
        return (out_low + out_high) / 2
    ratio = (value - low) / (high - low)
    return out_low + ratio * (out_high - out_low)


def _sample_graph(graph: nx.DiGraph, max_nodes: int) -> nx.DiGraph:
    if graph.number_of_nodes() <= max_nodes:
        return graph.copy()

    ranked_nodes = sorted(
        graph.nodes(data=True),
        key=lambda item: item[1].get("visits", 0) or 0,
        reverse=True,
    )
    selected = [node for node, _ in ranked_nodes[:max_nodes]]
    return graph.subgraph(selected).copy()


def _node_color(
    node: str,
    data: dict,
    color_by: ColorMode,
    pagerank: dict[str, float],
    communities: dict[str, int],
) -> str:
    if color_by == "pagerank":
        score = pagerank.get(node, 0.0)
        scores = list(pagerank.values())
        return _blue_scale(score, min(scores), max(scores))

    if color_by == "visits":
        return "#0f766e"

    if color_by == "community":
        index = communities.get(node, 0)
        return COMMUNITY_COLORS[index % len(COMMUNITY_COLORS)]

    ev = data.get("expected_value", 0.0) or 0.0
    if ev > 0.05:
        return EV_COLORS["positive"]
    if ev < -0.05:
        return EV_COLORS["negative"]
    return EV_COLORS["neutral"]


def _blue_scale(value: float, low: float, high: float) -> str:
    intensity = int(_scaled(value, low, high, 90, 220))
    return f"rgb(37, 99, {intensity})"


def _board_svg(fen: str | None) -> str:
    if not fen:
        return ""

    try:
        board = chess.Board(fen)
    except ValueError:
        return ""

    svg = chess.svg.board(board, size=220)
    return f'<div style="margin: 0 0 8px 0;">{svg}</div>'


def _node_title(node: str, data: dict, *, show_board: bool = True) -> str:
    outcomes = data.get("outcomes") or [0, 0, 0]
    wins, losses, draws = outcomes
    ev = data.get("expected_value", 0.0) or 0.0
    fen = data.get("fen", "N/A")
    board = _board_svg(fen) if show_board else ""
    return (
        f"{board}"
        f"<b>{escape(str(node))}</b><br>"
        f"FEN: {escape(str(fen))}<br>"
        f"Visits: {data.get('visits', 0):,}<br>"
        f"Outcomes: W {wins:,} / L {losses:,} / D {draws:,}<br>"
        f"Expected value: {ev:+.4f}"
    )


def _edge_title(data: dict) -> str:
    return (
        f"Probability: {data.get('weight', 0.0):.4f}<br>"
        f"Count: {data.get('count', 0):,}"
    )


def _community_index(graph: nx.DiGraph) -> dict[str, int]:
    communities = nx.community.greedy_modularity_communities(graph.to_undirected())
    result: dict[str, int] = {}
    for index, community in enumerate(communities):
        for node in community:
            result[node] = index
    return result


def create_interactive_graph(
    graph: nx.DiGraph,
    output_path: str | Path,
    *,
    max_nodes: int = 500,
    color_by: ColorMode = "community",
    min_edge_prob: float = 0.0,
    show_boards: bool = True,
    height: str = "850px",
    width: str = "100%",
) -> Path:
    sampled = _sample_graph(graph, max_nodes)
    if min_edge_prob > 0:
        low_probability_edges = [
            (u, v)
            for u, v, data in sampled.edges(data=True)
            if data.get("weight", 0.0) < min_edge_prob
        ]
        sampled.remove_edges_from(low_probability_edges)

    pagerank = nx.pagerank(sampled, weight="weight") if color_by == "pagerank" else {}
    communities = _community_index(sampled) if color_by == "community" else {}
    visits = [data.get("visits", 0) or 0 for _, data in sampled.nodes(data=True)]
    visit_min = min(visits) if visits else 0
    visit_max = max(visits) if visits else 0

    network = Network(
        height=height,
        width=width,
        directed=True,
        bgcolor="#ffffff",
        font_color="#111827",
        cdn_resources="in_line",
    )
    network.toggle_physics(True)
    network.set_options(
        """
        {
          "interaction": {
            "hover": true,
            "navigationButtons": true,
            "keyboard": true
          },
          "physics": {
            "barnesHut": {
              "gravitationalConstant": -23000,
              "centralGravity": 0.2,
              "springLength": 110,
              "springConstant": 0.035,
              "damping": 0.18
            },
            "minVelocity": 0.75,
            "stabilization": {
              "iterations": 180
            }
          },
          "edges": {
            "arrows": {
              "to": {
                "enabled": true,
                "scaleFactor": 0.45
              }
            },
            "smooth": {
              "type": "dynamic"
            },
            "color": {
              "color": "#94a3b8",
              "highlight": "#0f172a"
            }
          }
        }
        """
    )

    for node, data in sampled.nodes(data=True):
        visits_count = data.get("visits", 0) or 0
        size = _scaled(visits_count, visit_min, visit_max, 8, 32)
        network.add_node(
            node,
            label="",
            title=_node_title(node, data, show_board=show_boards),
            color=_node_color(node, data, color_by, pagerank, communities),
            size=size,
            value=visits_count,
        )

    for source, target, data in sampled.edges(data=True):
        probability = data.get("weight", 0.0) or 0.0
        network.add_edge(
            source,
            target,
            title=_edge_title(data),
            value=max(probability * 10, 0.1),
            width=_scaled(probability, 0, 1, 0.4, 4.0),
        )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    network.write_html(str(output), notebook=False, open_browser=False)
    return output


def create_interactive_path_graph(
    graph: nx.DiGraph,
    path: list[str],
    output_path: str | Path,
    *,
    neighborhood_hops: int = 1,
    show_boards: bool = True,
    height: str = "760px",
    width: str = "100%",
) -> Path:
    nodes = set(path)
    for node in path:
        nodes.update(nx.single_source_shortest_path_length(graph, node, cutoff=neighborhood_hops).keys())
    subgraph = graph.subgraph(nodes).copy()
    path_edges = set(zip(path, path[1:], strict=False))

    network = Network(
        height=height,
        width=width,
        directed=True,
        bgcolor="#ffffff",
        font_color="#111827",
        cdn_resources="in_line",
    )
    network.toggle_physics(True)

    for node, data in subgraph.nodes(data=True):
        on_path = node in nodes and node in path
        network.add_node(
            node,
            label=str(path.index(node) + 1) if on_path else "",
            title=_node_title(node, data, show_board=show_boards),
            color="#f59e0b" if on_path else "#64748b",
            size=26 if on_path else 10,
        )

    for source, target, data in subgraph.edges(data=True):
        on_path = (source, target) in path_edges
        network.add_edge(
            source,
            target,
            title=_edge_title(data),
            color="#f59e0b" if on_path else "#cbd5e1",
            width=4 if on_path else 1,
        )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    network.write_html(str(output), notebook=False, open_browser=False)
    return output
