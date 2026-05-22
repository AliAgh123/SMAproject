# SMA Chess

<p align="center">
  <img src="img/01%20_%20Wire%20mesh%20(2).png" alt="SMA Chess Logo" width="220"/>
</p>

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

<p align="center">
  <img src="img/SMA%20Diagram%20(2).png" alt="Project Architecture" width="600"/>
</p>

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
- Local Stockfish engine binary for the Stockfish comparison command.

## Platform

The project was developed and tested on **macOS**. It should also work on Windows and Linux:

- On macOS/Linux use `run_chess_defaults.sh` / `run_all.sh`
- On Windows use `run_chess_defaults.ps1` / `run_all.ps1` (PowerShell equivalents are included)
- The Python package itself (`uv run sma-chess ...`) is fully cross-platform

Install/sync dependencies:

```bash
uv sync
```

## Dataset

The project uses rated standard chess games from the [Lichess open database](https://database.lichess.org/).
Lichess publishes a free, complete monthly dump of all rated games in compressed PGN format (`.pgn.zst`).

The default run uses the **May 2015** dump:

```
https://database.lichess.org/standard/lichess_db_standard_rated_2015-05.pgn.zst
```

Any other monthly dump from the same database works as a drop-in replacement — just point
`RAW_PGN` at the downloaded file. Larger or more recent dumps will produce bigger graphs and
may take longer to parse.

```bash
# Example: use the January 2017 dump instead
MODE=raw \
RAW_PGN=data/raw/lichess_db_standard_rated_2017-01.pgn.zst \
CHECKPOINT=data/interim/chess_2017_01_pass1.pkl \
GRAPH=data/processed/chess_graph_2017_01.json \
./run_chess_defaults.sh
```

## Quick Start

### Step 1 — Install dependencies

```bash
cd /path/to/SMAproject
uv sync
```

### Step 2 — Install Stockfish

The project requires a local [Stockfish](https://stockfishchess.org/download/) engine binary.
The runner auto-detects it at the common install locations (`/opt/homebrew/bin/stockfish`,
`/usr/local/bin/stockfish`, `/usr/games/stockfish`).

| Platform         | Command                                                                                        |
| ---------------- | ---------------------------------------------------------------------------------------------- |
| macOS (Homebrew) | `brew install stockfish`                                                                       |
| Ubuntu / Debian  | `sudo apt install stockfish`                                                                   |
| Windows          | Download from [stockfish.org](https://stockfishchess.org/download/) and set `STOCKFISH_ENGINE` |

### Step 3 - Ensure needed LiChess Database is downloaded

You need to verify that you have a LiChess DB installed from [Lichess open database](https://database.lichess.org/)

### Step 4 — Run the full pipeline

This is the **recommended first run**. It parses the raw chess data, builds the graph, and runs
all analyses and visualizations using the same parameters as `notebooks/chess.ipynb`:

```bash
MODE=raw \
RAW_PGN=data/raw/lichess_db_standard_rated_2015-05.pgn.zst \
CHECKPOINT=data/interim/chess_2015_05_pass1.pkl \
./run_chess_defaults.sh
```

> **Note:** Parsing the raw `.pgn.zst` file takes several minutes.
> Subsequent runs can skip it using `MODE=checkpoint` (see below).

On Windows PowerShell:

```powershell
$env:STOCKFISH_ENGINE = "C:\path\to\stockfish.exe"
.\run_all.ps1 -Mode raw -RawPgn data\raw\lichess_db_standard_rated_2015-05.pgn.zst -Checkpoint data\interim\chess_2015_05_pass1.pkl
```

The runner produces:

```text
data/processed/chess_graph_2015_05_6k.json   ← built graph
data/processed/benchmark.csv
reports/summary.json
reports/analysis.json
reports/regression_metrics.json
reports/stockfish_metrics.json
reports/figures/graph_overview.png
reports/figures/chess_superstructure.png
reports/figures/expected_value_heatmap.png
reports/figures/centrality_overlap.png
reports/figures/macro_structure_top_paths.png
reports/figures/interactive_graph.html
reports/figures/interactive_path.html
reports/figures/benchmark.png
reports/figures/ablation_depth_comparison.png
reports/figures/regression_performance.png
reports/figures/stockfish_comparison.png
```

---

> **Note:** Everything below this line is supplementary. If you have already completed Step 3 above, there is nothing else you need to run — all outputs have been generated.

---

### Subsequent Runs (skip PGN parsing)

Once the checkpoint exists, use `MODE=checkpoint` to rebuild the graph without re-parsing:

```bash
MODE=checkpoint \
CHECKPOINT=data/interim/chess_2015_05_pass1.pkl \
./run_chess_defaults.sh
```

Or skip graph building entirely if the graph JSON already exists:

```bash
./run_chess_defaults.sh
```

## Run Modes

| `MODE`               | What it does                                                                 |
| -------------------- | ---------------------------------------------------------------------------- |
| `existing` (default) | Expects the graph JSON to already exist, jumps straight to analysis          |
| `checkpoint`         | Rebuilds the graph JSON from a saved `.pkl` checkpoint, then runs analysis   |
| `raw`                | Full pipeline: parse PGN → save checkpoint → build graph JSON → run analysis |

## Custom Runs

For targeted analysis or to explore individual commands, use the CLI directly.
Every command supports `--help`:

```bash
uv run sma-chess --help
uv run sma-chess analyze --help
uv run sma-chess visualize --help
uv run sma-chess benchmark --help
uv run sma-chess stockfish --help
```

Example: run only the analysis step on an existing graph:

```bash
uv run sma-chess analyze \
  --graph data/processed/chess_graph_2015_05_6k.json \
  --top-k 5 \
  --paths \
  --communities
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
  --notebook-static \
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
  --figure reports/figures/benchmark.png \
  --ablation-figure reports/figures/ablation_depth_comparison.png
```

Run regression:

```bash
uv run sma-chess regression \
  --graph data/processed/chess_graph_2015_05_6k.json \
  --output reports/regression_metrics.json \
  --figure reports/figures/regression_performance.png
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

Stockfish comparison is a required part of the project and requires a local Stockfish engine binary:

```bash
uv run sma-chess stockfish \
  --graph data/processed/chess_graph_2015_05_6k.json \
  --engine /path/to/stockfish \
  --figure reports/figures/stockfish_comparison.png \
  --output reports/stockfish_metrics.json
```

## Development Checks

Run lint checks for the project package code:

```bash
uv run ruff check src/sma_chess
```

## Notes

- The canonical project is the chess network analytics package.
- The package source of truth is under `src/sma_chess/`.
- `run_all.sh` is for macOS/Linux/Git Bash/WSL.
- `run_all.ps1` is for native Windows PowerShell.
- The original analysis was conducted in the chess.ipynb (in the notebooks folder)
