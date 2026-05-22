from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import networkx as nx

from sma_chess.analytics.communities import detect_communities
from sma_chess.analytics.expected_value import add_expected_values
from sma_chess.analytics.path_scoring import get_top_weighted_paths
from sma_chess.config import FIGURES_DIR, PROCESSED_DATA_DIR
from sma_chess.exploration.structure import get_structural_properties
from sma_chess.loading.graph_loader import get_start_node, load_graph_json, summarize_graph
from sma_chess.loading.pgn_parser import run_pass1
from sma_chess.management.persistence import load_pickle, save_json, save_pickle
from sma_chess.management.pruning import run_pass2


def _path(value: str) -> Path:
    return Path(value).expanduser()


def _print_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def _load_analyzed_graph(path: Path) -> nx.DiGraph:
    graph = load_graph_json(path)
    add_expected_values(graph)
    return graph


def cmd_parse_pgn(args: argparse.Namespace) -> int:
    pass1_data = run_pass1(
        str(args.pgn),
        max_depth=args.max_depth,
        min_elo=args.min_elo,
        min_main_time=args.min_main_time,
    )
    save_pickle(pass1_data, args.output)
    print(f"Saved pass-1 checkpoint: {args.output}")
    return 0


def cmd_build_graph(args: argparse.Namespace) -> int:
    if args.checkpoint:
        pass1_data = load_pickle(args.checkpoint)
    elif args.pgn:
        pass1_data = run_pass1(
            str(args.pgn),
            max_depth=args.max_depth,
            min_elo=args.min_elo,
            min_main_time=args.min_main_time,
        )
        if args.save_checkpoint:
            save_pickle(pass1_data, args.save_checkpoint)
            print(f"Saved pass-1 checkpoint: {args.save_checkpoint}")
    else:
        raise SystemExit("build-graph requires either --checkpoint or --pgn")

    graph_data = run_pass2(
        pass1_data["node_occurrence"],
        pass1_data["transitions"],
        pass1_data["outcomes"],
        pass1_data["hash_to_fen"],
        max_nodes=args.max_nodes,
        min_prob=args.min_prob,
        min_count=args.min_count,
    )
    save_json(graph_data, args.output)
    print(f"Saved graph JSON: {args.output}")
    return 0


def cmd_summarize(args: argparse.Namespace) -> int:
    graph = load_graph_json(args.graph)
    summary = summarize_graph(graph)
    summary.update(get_structural_properties(graph))
    _print_json(summary)
    return 0


def _top_items(scores: dict[Any, float], top_k: int) -> list[dict[str, Any]]:
    return [
        {"node": node, "score": score}
        for node, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_k]
    ]


def cmd_analyze(args: argparse.Namespace) -> int:
    graph = _load_analyzed_graph(args.graph)
    start_node, start_data = get_start_node(graph)

    pagerank = nx.pagerank(graph, weight="weight")
    in_degree = dict(graph.in_degree())
    out_degree = dict(graph.out_degree())
    ev_scores = {
        node: data.get("expected_value", 0.0)
        for node, data in graph.nodes(data=True)
    }

    result: dict[str, Any] = {
        "summary": summarize_graph(graph),
        "start": {
            "node": start_node,
            "fen": start_data.get("fen"),
            "visits": start_data.get("visits"),
        },
        "top_pagerank": _top_items(pagerank, args.top_k),
        "top_in_degree": _top_items(in_degree, args.top_k),
        "top_out_degree": _top_items(out_degree, args.top_k),
        "top_expected_value": _top_items(ev_scores, args.top_k),
    }

    if args.communities:
        communities = detect_communities(graph)
        result["communities"] = {
            "count": len(communities),
            "largest_sizes": sorted((len(c) for c in communities), reverse=True)[: args.top_k],
        }

    if args.paths:
        paths = get_top_weighted_paths(
            graph,
            start_node,
            depth_limit=args.depth,
            top_k=args.top_k,
            beam_width=args.beam_width,
            perspective=args.path_perspective,
        )
        result["top_paths"] = [
            {"score": score, "path": path}
            for path, score in paths
        ]

    _print_json(result)
    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from sma_chess.analytics.benchmarking import plot_benchmark_results, run_benchmark
    from sma_chess.visualization import plot_ablation_depth_comparison

    graph = _load_analyzed_graph(args.graph)
    df = run_benchmark(
        graph,
        node_sizes=args.node_sizes,
        depth_limit=args.depth,
        beam_width=args.beam_width,
        perspective=args.path_perspective,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    print(f"Saved benchmark CSV: {args.output}")

    if args.figure:
        fig = plot_benchmark_results(df, show=False)
        args.figure.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.figure, dpi=180, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved benchmark figure: {args.figure}")

    if args.ablation_figure:
        df_unconstrained = run_benchmark(
            graph,
            node_sizes=args.node_sizes,
            depth_limit=None,
            beam_width=args.beam_width,
            perspective=args.path_perspective,
        )
        fig = plot_ablation_depth_comparison(
            df,
            df_unconstrained,
            save_path=args.ablation_figure,
            show=False,
        )
        plt.close(fig)
        print(f"Saved ablation figure: {args.ablation_figure}")
    return 0


def cmd_visualize(args: argparse.Namespace) -> int:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sma_chess.visualization import (
        create_interactive_graph,
        create_interactive_path_graph,
        plot_centrality_overlap,
        plot_chess_superstructure,
        plot_expected_value_heatmap,
        plot_macro_structure_top_paths,
    )

    graph = _load_analyzed_graph(args.graph)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if not args.interactive_only:
        visits = [data.get("visits", 0) or 0 for _, data in graph.nodes(data=True)]
        evs = [data.get("expected_value", 0.0) for _, data in graph.nodes(data=True)]
        out_degrees = [degree for _, degree in graph.out_degree()]

        fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
        axes[0].hist(visits, bins=args.bins, color="#3b82f6")
        axes[0].set_title("Node Visits")
        axes[0].set_xlabel("Visits")
        axes[0].set_ylabel("Nodes")

        axes[1].hist(evs, bins=args.bins, color="#10b981")
        axes[1].set_title("Expected Value")
        axes[1].set_xlabel("EV")

        axes[2].hist(out_degrees, bins=args.bins, color="#f59e0b")
        axes[2].set_title("Out Degree")
        axes[2].set_xlabel("Outgoing edges")

        fig.suptitle(args.graph.name)
        fig.tight_layout()
        overview_path = output_dir / "graph_overview.png"
        fig.savefig(overview_path, dpi=180, bbox_inches="tight")
        plt.close(fig)

        print(f"Saved graph overview figure: {overview_path}")

    if args.interactive or args.interactive_only:
        interactive_path = args.interactive_output or output_dir / "interactive_graph.html"
        output_path = create_interactive_graph(
            graph,
            interactive_path,
            max_nodes=args.max_nodes,
            color_by=args.color_by,
            min_edge_prob=args.min_edge_prob,
            show_boards=not args.no_boards,
        )
        print(f"Saved interactive graph: {output_path}")

    if args.path_view:
        if args.path_rank < 1:
            raise SystemExit("--path-rank must be 1 or greater")

        start_node, _ = get_start_node(graph)
        paths = get_top_weighted_paths(
            graph,
            start_node,
            depth_limit=args.path_depth,
            top_k=args.path_rank,
            beam_width=args.beam_width,
            perspective=args.path_perspective,
        )
        if not paths:
            print("No path view saved: no weighted paths were found.")
            return 0

        path, score = paths[args.path_rank - 1]
        path_output = args.path_output or output_dir / "interactive_path.html"
        output_path = create_interactive_path_graph(
            graph,
            path,
            path_output,
            show_boards=not args.no_boards,
        )
        print(f"Saved interactive path view: {output_path} (score={score:.4f})")

    if args.notebook_static:
        start_node, _ = get_start_node(graph)
        paths = get_top_weighted_paths(
            graph,
            start_node,
            depth_limit=args.path_depth,
            top_k=5,
            beam_width=args.beam_width,
            perspective=args.path_perspective,
        )

        notebook_figures = [
            (
                "chess_superstructure.png",
                plot_chess_superstructure(
                    graph,
                    save_path=output_dir / "chess_superstructure.png",
                    show=False,
                    top_n=args.notebook_static_max_nodes,
                ),
            ),
            (
                "expected_value_heatmap.png",
                plot_expected_value_heatmap(
                    graph,
                    save_path=output_dir / "expected_value_heatmap.png",
                    show=False,
                    top_n=args.notebook_static_max_nodes,
                ),
            ),
            (
                "centrality_overlap.png",
                plot_centrality_overlap(
                    graph,
                    save_path=output_dir / "centrality_overlap.png",
                    show=False,
                    top_n=args.notebook_static_max_nodes,
                ),
            ),
            (
                "macro_structure_top_paths.png",
                plot_macro_structure_top_paths(
                    graph,
                    start_node,
                    paths,
                    save_path=output_dir / "macro_structure_top_paths.png",
                    show=False,
                    top_n=args.notebook_static_max_nodes,
                ),
            ),
        ]
        for filename, fig in notebook_figures:
            plt.close(fig)
            print(f"Saved notebook static figure: {output_dir / filename}")
    return 0


def cmd_regression(args: argparse.Namespace) -> int:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from sma_chess.analytics.regression import train_random_forest_regressor
    from sma_chess.visualization import plot_algorithm_performance

    graph = _load_analyzed_graph(args.graph)
    model, df, X_test, y_test, y_pred, r2, rmse = train_random_forest_regressor(
        graph,
        test_size=args.test_size,
        random_state=args.random_state,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    metrics = {
        "training_paths": len(df),
        "test_size": args.test_size,
        "random_state": args.random_state,
        "r2": float(r2),
        "rmse": float(rmse),
        "features": list(X_test.columns),
        "feature_importances": {
            name: float(importance)
            for name, importance in zip(X_test.columns, model.feature_importances_, strict=False)
        },
    }
    args.output.write_text(json.dumps(metrics, indent=2, sort_keys=True))
    print(f"Saved regression metrics: {args.output}")

    if args.figure:
        fig = plot_algorithm_performance(y_test, y_pred, r2, rmse, save_path=args.figure, show=False)
        plt.close(fig)
        print(f"Saved regression figure: {args.figure}")

    return 0


def cmd_stockfish(args: argparse.Namespace) -> int:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from sma_chess.analytics.stockfish_eval import evaluate_paths_stockfish, plot_scatter_comp

    graph = _load_analyzed_graph(args.graph)
    start_node, _ = get_start_node(graph)
    top_paths = get_top_weighted_paths(
        graph,
        start_node,
        depth_limit=args.depth,
        top_k=args.top_k,
        beam_width=args.beam_width,
        perspective=args.path_perspective,
    )
    scores = evaluate_paths_stockfish(
        graph,
        top_paths,
        stockfish_path=str(args.engine),
        stockfish_depth=args.stockfish_depth,
    )
    fig, rho, pval, ndcg = plot_scatter_comp(graph, top_paths, scores, label=args.graph.name)

    if args.figure:
        args.figure.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.figure, dpi=180, bbox_inches="tight")
        print(f"Saved Stockfish comparison figure: {args.figure}")
    plt.close(fig)

    metrics = {"spearman_rho": rho, "p_value": pval, "ndcg": ndcg}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(metrics, indent=2, sort_keys=True))
        print(f"Saved Stockfish metrics: {args.output}")
    else:
        _print_json(metrics)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sma-chess",
        description="Chess network parsing, analysis, benchmarking, and visualization tools.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse_pgn = subparsers.add_parser("parse-pgn", help="Parse a compressed PGN into a pass-1 checkpoint.")
    parse_pgn.add_argument("--pgn", type=_path, required=True, help="Path to a .pgn.zst file.")
    parse_pgn.add_argument("--output", type=_path, required=True, help="Checkpoint pickle output path.")
    parse_pgn.add_argument("--max-depth", type=int, default=20)
    parse_pgn.add_argument("--min-elo", type=int, default=1000)
    parse_pgn.add_argument("--min-main-time", type=int, default=300)
    parse_pgn.set_defaults(func=cmd_parse_pgn)

    build_graph = subparsers.add_parser("build-graph", help="Build a pruned graph JSON from PGN or checkpoint data.")
    build_graph.add_argument("--checkpoint", type=_path, help="Pass-1 checkpoint pickle path.")
    build_graph.add_argument("--pgn", type=_path, help="Path to a .pgn.zst file.")
    build_graph.add_argument("--save-checkpoint", type=_path, help="Optional checkpoint path when building from PGN.")
    build_graph.add_argument("--output", type=_path, required=True, help="Graph JSON output path.")
    build_graph.add_argument("--max-depth", type=int, default=20)
    build_graph.add_argument("--min-elo", type=int, default=1000)
    build_graph.add_argument("--min-main-time", type=int, default=300)
    build_graph.add_argument("--max-nodes", type=int, default=10000)
    build_graph.add_argument("--min-prob", type=float, default=0.02)
    build_graph.add_argument("--min-count", type=int, default=100)
    build_graph.set_defaults(func=cmd_build_graph)

    summarize = subparsers.add_parser("summarize", help="Print graph summary statistics.")
    summarize.add_argument("--graph", type=_path, required=True, help="Processed graph JSON path.")
    summarize.set_defaults(func=cmd_summarize)

    analyze = subparsers.add_parser("analyze", help="Run centrality, EV, community, and path analyses.")
    analyze.add_argument("--graph", type=_path, required=True, help="Processed graph JSON path.")
    analyze.add_argument("--top-k", type=int, default=5)
    analyze.add_argument("--depth", type=int, default=4)
    analyze.add_argument("--beam-width", type=int, default=2, help="Candidate moves kept per ply for path search.")
    analyze.add_argument(
        "--path-perspective",
        choices=["optimal", "white", "black"],
        default="optimal",
        help="How to rank returned weighted paths.",
    )
    analyze.add_argument("--communities", action="store_true", help="Include greedy modularity community summary.")
    analyze.add_argument("--paths", action="store_true", help="Include top weighted paths from the start node.")
    analyze.set_defaults(func=cmd_analyze)

    benchmark = subparsers.add_parser("benchmark", help="Benchmark path algorithms on the graph.")
    benchmark.add_argument("--graph", type=_path, required=True, help="Processed graph JSON path.")
    benchmark.add_argument("--output", type=_path, default=PROCESSED_DATA_DIR / "benchmark.csv")
    benchmark.add_argument("--figure", type=_path, help="Optional figure output path.")
    benchmark.add_argument("--node-sizes", type=int, nargs="+", help="Node sizes to benchmark.")
    benchmark.add_argument("--depth", type=int, default=4, help="Depth for custom path search and traversal baselines.")
    benchmark.add_argument("--beam-width", type=int, default=2, help="Candidate moves kept per ply for path search.")
    benchmark.add_argument("--ablation-figure", type=_path, help="Optional depth-limited vs unconstrained ablation figure path.")
    benchmark.add_argument(
        "--path-perspective",
        choices=["optimal", "white", "black"],
        default="optimal",
        help="How to rank custom weighted paths.",
    )
    benchmark.set_defaults(func=cmd_benchmark)

    visualize = subparsers.add_parser("visualize", help="Save basic graph overview figures.")
    visualize.add_argument("--graph", type=_path, required=True, help="Processed graph JSON path.")
    visualize.add_argument("--output-dir", type=_path, default=FIGURES_DIR)
    visualize.add_argument("--bins", type=int, default=40)
    visualize.add_argument("--interactive", action="store_true", help="Also save a PyVis interactive HTML graph.")
    visualize.add_argument("--interactive-only", action="store_true", help="Only save the interactive HTML graph.")
    visualize.add_argument("--notebook-static", action="store_true", help="Also save static Matplotlib figures migrated from chess.ipynb.")
    visualize.add_argument("--notebook-static-max-nodes", type=int, default=6000, help="Max high-visit nodes for notebook-static plots.")
    visualize.add_argument("--interactive-output", type=_path, help="Interactive HTML output path.")
    visualize.add_argument("--max-nodes", type=int, default=500, help="Max nodes in the interactive graph.")
    visualize.add_argument("--min-edge-prob", type=float, default=0.0, help="Hide lower-probability edges.")
    visualize.add_argument("--no-boards", action="store_true", help="Do not render chess boards in node hover cards.")
    visualize.add_argument("--path-view", action="store_true", help="Save an interactive highlighted top-path HTML graph.")
    visualize.add_argument("--path-depth", type=int, default=4, help="Depth for the highlighted weighted path.")
    visualize.add_argument("--path-rank", type=int, default=1, help="Which ranked path to highlight, starting at 1.")
    visualize.add_argument("--path-output", type=_path, help="Interactive path HTML output path.")
    visualize.add_argument("--beam-width", type=int, default=2, help="Candidate moves kept per ply for path search.")
    visualize.add_argument(
        "--path-perspective",
        choices=["optimal", "white", "black"],
        default="optimal",
        help="How to rank highlighted weighted paths.",
    )
    visualize.add_argument(
        "--color-by",
        choices=["ev", "pagerank", "visits", "community"],
        default="ev",
        help="Interactive node coloring mode.",
    )
    visualize.set_defaults(func=cmd_visualize)

    regression = subparsers.add_parser("regression", help="Train random-forest path score approximation and save metrics/figure.")
    regression.add_argument("--graph", type=_path, required=True, help="Processed graph JSON path.")
    regression.add_argument("--output", type=_path, default=PROCESSED_DATA_DIR / "regression_metrics.json")
    regression.add_argument("--figure", type=_path, help="Optional actual-vs-predicted figure output path.")
    regression.add_argument("--test-size", type=float, default=0.2)
    regression.add_argument("--random-state", type=int, default=42)
    regression.set_defaults(func=cmd_regression)

    stockfish = subparsers.add_parser("stockfish", help="Compare top model paths with a Stockfish engine.")
    stockfish.add_argument("--graph", type=_path, required=True, help="Processed graph JSON path.")
    stockfish.add_argument("--engine", type=_path, default=Path("/usr/games/stockfish"))
    stockfish.add_argument("--stockfish-depth", type=int, default=15)
    stockfish.add_argument("--depth", type=int, default=4)
    stockfish.add_argument("--top-k", type=int, default=5)
    stockfish.add_argument("--beam-width", type=int, default=2, help="Candidate moves kept per ply for path search.")
    stockfish.add_argument(
        "--path-perspective",
        choices=["optimal", "white", "black"],
        default="optimal",
        help="How to rank paths before Stockfish comparison.",
    )
    stockfish.add_argument("--figure", type=_path, help="Optional figure output path.")
    stockfish.add_argument("--output", type=_path, help="Optional metrics JSON output path.")
    stockfish.set_defaults(func=cmd_stockfish)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
