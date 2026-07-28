param(
    [string]$Mode = $(if ($env:MODE) { $env:MODE } else { "existing" }),
    [string]$Graph = $(if ($env:GRAPH) { $env:GRAPH } else { "data/processed/chess_graph_2015_05_6k.json" }),
    [string]$RawPgn = $(if ($env:RAW_PGN) { $env:RAW_PGN } else { "data/raw/lichess_db_standard_rated_2013-02.pgn.zst" }),
    [string]$Checkpoint = $(if ($env:CHECKPOINT) { $env:CHECKPOINT } else { "data/interim/pass1.pkl" }),
    [string]$ReportDir = $(if ($env:REPORT_DIR) { $env:REPORT_DIR } else { "reports" }),
    [string]$FigureDir = $(if ($env:FIGURE_DIR) { $env:FIGURE_DIR } else { "reports/figures" }),
    [int[]]$BenchmarkNodes = $(if ($env:BENCHMARK_NODES) { $env:BENCHMARK_NODES -split " " } else { 100, 300, 500, 1000 }),
    [int]$NotebookStaticMaxNodes = $(if ($env:NOTEBOOK_STATIC_MAX_NODES) { $env:NOTEBOOK_STATIC_MAX_NODES } else { 500 }),
    [string]$StockfishEngine = $(if ($env:STOCKFISH_ENGINE) { $env:STOCKFISH_ENGINE } else { "/usr/games/stockfish" }),
    [int]$StockfishDepth = $(if ($env:STOCKFISH_DEPTH) { $env:STOCKFISH_DEPTH } else { 15 }),
    [int]$StockfishPathDepth = $(if ($env:STOCKFISH_PATH_DEPTH) { $env:STOCKFISH_PATH_DEPTH } else { 6 }),
    [int]$StockfishTopK = $(if ($env:STOCKFISH_TOP_K) { $env:STOCKFISH_TOP_K } else { 20 }),
    [int]$MaxDepth = $(if ($env:MAX_DEPTH) { $env:MAX_DEPTH } else { 20 }),
    [int]$MinElo = $(if ($env:MIN_ELO) { $env:MIN_ELO } else { 1000 }),
    [int]$MinMainTime = $(if ($env:MIN_MAIN_TIME) { $env:MIN_MAIN_TIME } else { 300 }),
    [int]$MaxNodes = $(if ($env:MAX_NODES) { $env:MAX_NODES } else { 10000 }),
    [double]$MinProb = $(if ($env:MIN_PROB) { $env:MIN_PROB } else { 0.02 }),
    [int]$MinCount = $(if ($env:MIN_COUNT) { $env:MIN_COUNT } else { 100 })
)

$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path $ReportDir, $FigureDir, "data/raw", "data/interim", "data/processed" | Out-Null

Write-Host "==> Syncing dependencies"
uv sync

switch ($Mode) {
    "existing" {
        Write-Host "==> Using existing graph JSON: $Graph"
    }

    "checkpoint" {
        Write-Host "==> Building graph JSON from checkpoint: $Checkpoint"
        uv run sma-chess build-graph `
            --checkpoint $Checkpoint `
            --output $Graph `
            --max-nodes $MaxNodes `
            --min-prob $MinProb `
            --min-count $MinCount
    }

    "raw" {
        Write-Host "==> Parsing raw PGN into checkpoint: $Checkpoint"
        uv run sma-chess parse-pgn `
            --pgn $RawPgn `
            --output $Checkpoint `
            --max-depth $MaxDepth `
            --min-elo $MinElo `
            --min-main-time $MinMainTime

        Write-Host "==> Building graph JSON from checkpoint: $Graph"
        uv run sma-chess build-graph `
            --checkpoint $Checkpoint `
            --output $Graph `
            --max-nodes $MaxNodes `
            --min-prob $MinProb `
            --min-count $MinCount
    }

    default {
        throw "Unknown Mode: $Mode. Use existing, checkpoint, or raw."
    }
}

Write-Host "==> Writing graph summary"
uv run sma-chess summarize --graph $Graph | Out-File -Encoding utf8 "$ReportDir/summary.json"

Write-Host "==> Writing analysis report"
uv run sma-chess analyze `
    --graph $Graph `
    --top-k 5 `
    --paths `
    --communities |
    Out-File -Encoding utf8 "$ReportDir/analysis.json"

Write-Host "==> Generating static and interactive visualizations"
uv run sma-chess visualize `
    --graph $Graph `
    --output-dir $FigureDir `
    --interactive `
    --notebook-static `
    --notebook-static-max-nodes $NotebookStaticMaxNodes `
    --max-nodes 500 `
    --color-by ev `
    --path-view `
    --path-depth 4 `
    --path-rank 1 `
    --interactive-output "$FigureDir/interactive_graph.html" `
    --path-output "$FigureDir/interactive_path.html"

Write-Host "==> Running benchmark"
uv run sma-chess benchmark `
    --graph $Graph `
    --node-sizes $BenchmarkNodes `
    --output data/processed/benchmark.csv `
    --figure "$FigureDir/benchmark.png" `
    --ablation-figure "$FigureDir/ablation_depth_comparison.png"

Write-Host "==> Running regression analysis"
uv run sma-chess regression `
    --graph $Graph `
    --output "$ReportDir/regression_metrics.json" `
    --figure "$FigureDir/regression_performance.png"

Write-Host "==> Running Stockfish comparison"
if (-not (Test-Path $StockfishEngine)) {
    throw "Stockfish engine not found: $StockfishEngine. Set STOCKFISH_ENGINE=/path/to/stockfish and rerun."
}
uv run sma-chess stockfish `
    --graph $Graph `
    --engine $StockfishEngine `
    --stockfish-depth $StockfishDepth `
    --depth $StockfishPathDepth `
    --top-k $StockfishTopK `
    --figure "$FigureDir/stockfish_comparison.png" `
    --output "$ReportDir/stockfish_metrics.json"

Write-Host ""
Write-Host "Done."
Write-Host "Summary:              $ReportDir/summary.json"
Write-Host "Analysis:             $ReportDir/analysis.json"
Write-Host "Static overview:      $FigureDir/graph_overview.png"
Write-Host "Interactive graph:    $FigureDir/interactive_graph.html"
Write-Host "Interactive path:     $FigureDir/interactive_path.html"
Write-Host "Benchmark CSV:        data/processed/benchmark.csv"
Write-Host "Benchmark figure:     $FigureDir/benchmark.png"
Write-Host "Ablation figure:      $FigureDir/ablation_depth_comparison.png"
Write-Host "Regression metrics:   $ReportDir/regression_metrics.json"
Write-Host "Regression figure:    $FigureDir/regression_performance.png"
Write-Host "Stockfish metrics:    $ReportDir/stockfish_metrics.json"
Write-Host "Stockfish figure:     $FigureDir/stockfish_comparison.png"
