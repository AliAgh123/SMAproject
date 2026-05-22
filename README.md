# SMA Chess

Chess opening network analysis built as a reusable Python package.

This project turns chess games into a directed graph of positions and transitions, then analyzes the graph with structural metrics, expected-value scoring, centrality, community detection, path search, benchmarking, and interactive visualizations.

## What The Project Does

- Parses compressed `.pgn.zst` chess game files.
- Builds a pruned graph JSON where:
  - nodes are chess positions, stored with FEN, outcomes, and visit counts
  - edges are moves/transitions, stored with probability and count
- Loads processed graph JSON into `networkx.DiGraph`.
- Computes summary statistics, expected value, PageRank, in/out degree rankings, communities, and top weighted paths.
- Generates static charts and interactive PyVis HTML graph views.
- Benchmarks custom DFS-style path scoring against NetworkX DFS, BFS, Dijkstra, and random walk baselines.

## Project Layout

```text
data/
  raw/          # compressed PGN files
  interim/      # parsing checkpoints
  processed/    # graph JSON and benchmark outputs
reports/
  figures/      # static PNG and interactive HTML outputs
src/sma_chess/
  loading/      # PGN and graph loading
  management/   # pruning and persistence helpers
  exploration/  # graph structure and centrality helpers
  analytics/    # EV, path scoring, communities, benchmarks, Stockfish tools
  visualization/# static/interactive visualization helpers
  cli.py        # command-line interface
```

## Requirements

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/)

Install/sync dependencies:

```bash
uv sync
```

## Quick Start

From the project root:

```bash
cd /path/to/SMAproject
./run_all.sh
```

On Windows PowerShell:

```powershell
cd path\to\SMAproject
.\run_all.ps1
```

The runner creates:

```text
reports/summary.json
reports/analysis.json
reports/figures/graph_overview.png
reports/figures/interactive_graph.html
reports/figures/interactive_path.html
data/processed/benchmark.csv
reports/figures/benchmark.png
```

## Run Modes

Use the existing processed graph JSON:

```bash
./run_all.sh
```

Build graph JSON from an existing checkpoint first:

```bash
MODE=checkpoint \
CHECKPOINT=data/interim/test_2013_02_pass1.pkl \
GRAPH=data/processed/rebuilt_graph.json \
./run_all.sh
```

Parse raw PGN, build graph JSON, then run all analysis:

```bash
MODE=raw \
RAW_PGN=data/raw/lichess_db_standard_rated_2013-02.pgn.zst \
CHECKPOINT=data/interim/pass1.pkl \
GRAPH=data/processed/chess_graph_from_raw.json \
./run_all.sh
```

PowerShell equivalents:

```powershell
.\run_all.ps1 -Mode checkpoint -Checkpoint data/interim/test_2013_02_pass1.pkl -Graph data/processed/rebuilt_graph.json
```

```powershell
.\run_all.ps1 -Mode raw -RawPgn data/raw/lichess_db_standard_rated_2013-02.pgn.zst -Checkpoint data/interim/pass1.pkl -Graph data/processed/chess_graph_from_raw.json
```

## CLI Usage

Show all commands:

```bash
uv run sma-chess --help
```

Summarize a graph:

```bash
uv run sma-chess summarize \
  --graph data/processed/chess_graph_2015_05_6k.json
```

Run analysis:

```bash
uv run sma-chess analyze \
  --graph data/processed/chess_graph_2015_05_6k.json \
  --top-k 5 \
  --paths \
  --communities
```

Generate static and interactive visualizations:

```bash
uv run sma-chess visualize \
  --graph data/processed/chess_graph_2015_05_6k.json \
  --output-dir reports/figures \
  --interactive \
  --max-nodes 500 \
  --color-by ev \
  --path-view
```

Run benchmark:

```bash
uv run sma-chess benchmark \
  --graph data/processed/chess_graph_2015_05_6k.json \
  --node-sizes 100 300 500 1000 \
  --output data/processed/benchmark.csv \
  --figure reports/figures/benchmark.png
```

Parse PGN into a checkpoint:

```bash
uv run sma-chess parse-pgn \
  --pgn data/raw/lichess_db_standard_rated_2013-02.pgn.zst \
  --output data/interim/pass1.pkl \
  --max-depth 20 \
  --min-elo 1000 \
  --min-main-time 300
```

Build graph JSON from a checkpoint:

```bash
uv run sma-chess build-graph \
  --checkpoint data/interim/pass1.pkl \
  --output data/processed/chess_graph_from_raw.json \
  --max-nodes 10000 \
  --min-prob 0.02 \
  --min-count 100
```

## Interactive Visualizations

Interactive visualizations are exported as standalone HTML files using PyVis.

Open these in a browser after running the project:

```text
reports/figures/interactive_graph.html
reports/figures/interactive_path.html
```

Color modes:

```bash
--color-by ev
--color-by pagerank
--color-by visits
--color-by community
```

Large graphs can be heavy in the browser, so interactive output samples the highest-visit nodes by default:

```bash
--max-nodes 500
--min-edge-prob 0.03
```

## Stockfish Comparison

Stockfish comparison is optional and requires a local Stockfish engine binary:

```bash
uv run sma-chess stockfish \
  --graph data/processed/chess_graph_2015_05_6k.json \
  --engine /path/to/stockfish \
  --figure reports/figures/stockfish_comparison.png
```

## Development Checks

Run lint checks for the currently refactored package code:

```bash
uv run ruff check src/sma_chess/cli.py src/sma_chess/visualization
```

Run tests:

```bash
uv run pytest
```

At the moment, the project still needs a proper test suite. `pytest` may report that no tests were collected until tests are added under `tests/`.

## Notes

- The canonical project is the chess network analytics package.
- Older notebooks are retained as reference/report artifacts.
- The package source of truth is under `src/sma_chess/`.
- `run_all.sh` is for macOS/Linux/Git Bash/WSL.
- `run_all.ps1` is for native Windows PowerShell.
