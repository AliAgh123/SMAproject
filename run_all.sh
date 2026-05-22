#!/usr/bin/env bash
set -euo pipefail

MODE="${MODE:-existing}"
GRAPH="${GRAPH:-data/processed/chess_graph_2015_05_6k.json}"
RAW_PGN="${RAW_PGN:-data/raw/lichess_db_standard_rated_2013-02.pgn.zst}"
CHECKPOINT="${CHECKPOINT:-data/interim/pass1.pkl}"
REPORT_DIR="${REPORT_DIR:-reports}"
FIGURE_DIR="${FIGURE_DIR:-reports/figures}"
BENCHMARK_NODES="${BENCHMARK_NODES:-100 300 500 1000}"
NOTEBOOK_STATIC_MAX_NODES="${NOTEBOOK_STATIC_MAX_NODES:-500}"
STOCKFISH_ENGINE="${STOCKFISH_ENGINE:-/usr/games/stockfish}"
STOCKFISH_DEPTH="${STOCKFISH_DEPTH:-15}"
STOCKFISH_PATH_DEPTH="${STOCKFISH_PATH_DEPTH:-6}"
STOCKFISH_TOP_K="${STOCKFISH_TOP_K:-20}"
MAX_DEPTH="${MAX_DEPTH:-20}"
MIN_ELO="${MIN_ELO:-1000}"
MIN_MAIN_TIME="${MIN_MAIN_TIME:-300}"
MAX_NODES="${MAX_NODES:-10000}"
MIN_PROB="${MIN_PROB:-0.02}"
MIN_COUNT="${MIN_COUNT:-100}"

mkdir -p "$REPORT_DIR" "$FIGURE_DIR" data/interim data/processed

echo "==> Syncing dependencies"
uv sync

case "$MODE" in
  existing)
    echo "==> Using existing graph JSON: $GRAPH"
    ;;

  checkpoint)
    echo "==> Building graph JSON from checkpoint: $CHECKPOINT"
    uv run sma-chess build-graph \
      --checkpoint "$CHECKPOINT" \
      --output "$GRAPH" \
      --max-nodes "$MAX_NODES" \
      --min-prob "$MIN_PROB" \
      --min-count "$MIN_COUNT"
    ;;

  raw)
    echo "==> Parsing raw PGN into checkpoint: $CHECKPOINT"
    uv run sma-chess parse-pgn \
      --pgn "$RAW_PGN" \
      --output "$CHECKPOINT" \
      --max-depth "$MAX_DEPTH" \
      --min-elo "$MIN_ELO" \
      --min-main-time "$MIN_MAIN_TIME"

    echo "==> Building graph JSON from checkpoint: $GRAPH"
    uv run sma-chess build-graph \
      --checkpoint "$CHECKPOINT" \
      --output "$GRAPH" \
      --max-nodes "$MAX_NODES" \
      --min-prob "$MIN_PROB" \
      --min-count "$MIN_COUNT"
    ;;

  *)
    echo "Unknown MODE: $MODE" >&2
    echo "Use MODE=existing, MODE=checkpoint, or MODE=raw." >&2
    exit 2
    ;;
esac

echo "==> Writing graph summary"
uv run sma-chess summarize \
  --graph "$GRAPH" \
  > "$REPORT_DIR/summary.json"

echo "==> Writing analysis report"
uv run sma-chess analyze \
  --graph "$GRAPH" \
  --top-k 5 \
  --paths \
  --communities \
  > "$REPORT_DIR/analysis.json"

echo "==> Generating static and interactive visualizations"
uv run sma-chess visualize \
  --graph "$GRAPH" \
  --output-dir "$FIGURE_DIR" \
  --interactive \
  --notebook-static \
  --notebook-static-max-nodes "$NOTEBOOK_STATIC_MAX_NODES" \
  --max-nodes 500 \
  --color-by ev \
  --path-view \
  --path-depth 4 \
  --path-rank 1 \
  --interactive-output "$FIGURE_DIR/interactive_graph.html" \
  --path-output "$FIGURE_DIR/interactive_path.html"

echo "==> Running benchmark"
uv run sma-chess benchmark \
  --graph "$GRAPH" \
  --node-sizes $BENCHMARK_NODES \
  --output data/processed/benchmark.csv \
  --figure "$FIGURE_DIR/benchmark.png" \
  --ablation-figure "$FIGURE_DIR/ablation_depth_comparison.png"

echo "==> Running regression analysis"
uv run sma-chess regression \
  --graph "$GRAPH" \
  --output "$REPORT_DIR/regression_metrics.json" \
  --figure "$FIGURE_DIR/regression_performance.png"

echo "==> Running Stockfish comparison"
if [[ ! -x "$STOCKFISH_ENGINE" ]]; then
  echo "Stockfish engine not found or not executable: $STOCKFISH_ENGINE" >&2
  echo "Set STOCKFISH_ENGINE=/path/to/stockfish and rerun." >&2
  exit 2
fi
uv run sma-chess stockfish \
  --graph "$GRAPH" \
  --engine "$STOCKFISH_ENGINE" \
  --stockfish-depth "$STOCKFISH_DEPTH" \
  --depth "$STOCKFISH_PATH_DEPTH" \
  --top-k "$STOCKFISH_TOP_K" \
  --figure "$FIGURE_DIR/stockfish_comparison.png" \
  --output "$REPORT_DIR/stockfish_metrics.json"

echo
echo "Done."
echo "Summary:              $REPORT_DIR/summary.json"
echo "Analysis:             $REPORT_DIR/analysis.json"
echo "Static overview:      $FIGURE_DIR/graph_overview.png"
echo "Interactive graph:    $FIGURE_DIR/interactive_graph.html"
echo "Interactive path:     $FIGURE_DIR/interactive_path.html"
echo "Benchmark CSV:        data/processed/benchmark.csv"
echo "Benchmark figure:     $FIGURE_DIR/benchmark.png"
echo "Ablation figure:      $FIGURE_DIR/ablation_depth_comparison.png"
echo "Regression metrics:   $REPORT_DIR/regression_metrics.json"
echo "Regression figure:    $FIGURE_DIR/regression_performance.png"
echo "Stockfish metrics:    $REPORT_DIR/stockfish_metrics.json"
echo "Stockfish figure:     $FIGURE_DIR/stockfish_comparison.png"
