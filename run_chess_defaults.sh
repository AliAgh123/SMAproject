#!/usr/bin/env bash
set -euo pipefail

# Default full-project run using the analysis parameters from notebooks/chess.ipynb.
# By default this mirrors the notebook's starting point: the processed 6k graph JSON.
# Set MODE=raw if you want to rebuild a graph from the raw PGN/ZST first.
# Set CLEAN_OUTPUTS=0 to keep existing generated outputs.

if [[ -z "${STOCKFISH_ENGINE:-}" ]]; then
  for candidate in \
    "$(command -v stockfish 2>/dev/null || true)" \
    /opt/homebrew/bin/stockfish \
    /usr/local/bin/stockfish \
    /usr/games/stockfish
  do
    if [[ -n "$candidate" && -x "$candidate" ]]; then
      export STOCKFISH_ENGINE="$candidate"
      break
    fi
  done
fi

if [[ -z "${STOCKFISH_ENGINE:-}" || ! -x "$STOCKFISH_ENGINE" ]]; then
  echo "Stockfish engine not found." >&2
  echo "Set STOCKFISH_ENGINE=/path/to/stockfish and rerun." >&2
  exit 2
fi

export MODE="${MODE:-raw}"
export RAW_PGN="${RAW_PGN:-data/raw/lichess_db_standard_rated_2015-05.pgn.zst}"
export CHECKPOINT="${CHECKPOINT:-data/interim/chess_pass1.pkl}"
export GRAPH="${GRAPH:-data/processed/chess_graph_2015_05_6k.json}"

# Raw-build defaults used by the package when MODE=raw.
export MAX_DEPTH="${MAX_DEPTH:-20}"
export MIN_ELO="${MIN_ELO:-1000}"
export MIN_MAIN_TIME="${MIN_MAIN_TIME:-300}"
export MAX_NODES="${MAX_NODES:-10000}"
export MIN_PROB="${MIN_PROB:-0.02}"
export MIN_COUNT="${MIN_COUNT:-100}"

# chess.ipynb benchmark and visualization defaults.
export BENCHMARK_NODES="${BENCHMARK_NODES:-100 300 500 1000 1500 3000 5000 6000}"
export NOTEBOOK_STATIC_MAX_NODES="${NOTEBOOK_STATIC_MAX_NODES:-6000}"

# chess.ipynb Stockfish defaults. run_all.sh uses the small comparison first.
export STOCKFISH_DEPTH="${STOCKFISH_DEPTH:-15}"
export STOCKFISH_PATH_DEPTH="${STOCKFISH_PATH_DEPTH:-6}"
export STOCKFISH_TOP_K="${STOCKFISH_TOP_K:-20}"

if [[ "${CLEAN_OUTPUTS:-1}" == "1" ]]; then
  echo "==> Cleaning generated outputs"
  rm -f data/processed/benchmark.csv
  rm -f data/processed/regression_metrics.json
  rm -f reports/*.json
  rm -f reports/figures/*.png reports/figures/*.html
  if [[ "$MODE" == "raw" ]]; then
    rm -f "$CHECKPOINT" "$GRAPH"
  fi
fi

./run_all.sh

# echo "==> Running additional chess.ipynb Stockfish comparisons"
# uv run sma-chess stockfish \
#   --graph "$GRAPH" \
#   --engine "$STOCKFISH_ENGINE" \
#   --stockfish-depth "$STOCKFISH_DEPTH" \
#   --depth 8 \
#   --top-k 50 \
#   --figure reports/figures/stockfish_depth8_top50.png \
#   --output reports/stockfish_depth8_top50.json

# uv run sma-chess stockfish \
#   --graph "$GRAPH" \
#   --engine "$STOCKFISH_ENGINE" \
#   --stockfish-depth "$STOCKFISH_DEPTH" \
#   --depth 10 \
#   --top-k 100 \
#   --beam-width 3 \
#   --figure reports/figures/stockfish_depth10_top100.png \
#   --output reports/stockfish_depth10_top100.json

# uv run sma-chess stockfish \
#   --graph "$GRAPH" \
#   --engine "$STOCKFISH_ENGINE" \
#   --stockfish-depth "$STOCKFISH_DEPTH" \
#   --depth 6 \
#   --top-k 20 \
#   --path-perspective white \
#   --figure reports/figures/stockfish_depth6_top20_white.png \
#   --output reports/stockfish_depth6_top20_white.json

# uv run sma-chess stockfish \
#   --graph "$GRAPH" \
#   --engine "$STOCKFISH_ENGINE" \
#   --stockfish-depth "$STOCKFISH_DEPTH" \
#   --depth 8 \
#   --top-k 50 \
#   --path-perspective white \
#   --figure reports/figures/stockfish_depth8_top50_white.png \
#   --output reports/stockfish_depth8_top50_white.json

# uv run sma-chess stockfish \
#   --graph "$GRAPH" \
#   --engine "$STOCKFISH_ENGINE" \
#   --stockfish-depth "$STOCKFISH_DEPTH" \
#   --depth 10 \
#   --top-k 100 \
#   --beam-width 3 \
#   --path-perspective white \
#   --figure reports/figures/stockfish_depth10_top100_white.png \
#   --output reports/stockfish_depth10_top100_white.json

echo
echo "Chess notebook default run complete."
