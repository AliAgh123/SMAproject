param(
    [string]$Mode = $(if ($env:MODE) { $env:MODE } else { "existing" }),
    [string]$Graph = $(if ($env:GRAPH) { $env:GRAPH } else { "data/processed/chess_graph_2015_05_6k.json" }),
    [string]$RawPgn = $(if ($env:RAW_PGN) { $env:RAW_PGN } else { "data/raw/lichess_db_standard_rated_2013-02.pgn.zst" }),
    [string]$Checkpoint = $(if ($env:CHECKPOINT) { $env:CHECKPOINT } else { "data/interim/pass1.pkl" }),
    [string]$ReportDir = $(if ($env:REPORT_DIR) { $env:REPORT_DIR } else { "reports" }),
    [string]$FigureDir = $(if ($env:FIGURE_DIR) { $env:FIGURE_DIR } else { "reports/figures" }),
    [int[]]$BenchmarkNodes = $(if ($env:BENCHMARK_NODES) { $env:BENCHMARK_NODES -split " " } else { 100, 300, 500, 1000 }),
    [int]$MaxDepth = $(if ($env:MAX_DEPTH) { $env:MAX_DEPTH } else { 20 }),
    [int]$MinElo = $(if ($env:MIN_ELO) { $env:MIN_ELO } else { 1000 }),
    [int]$MinMainTime = $(if ($env:MIN_MAIN_TIME) { $env:MIN_MAIN_TIME } else { 300 }),
    [int]$MaxNodes = $(if ($env:MAX_NODES) { $env:MAX_NODES } else { 10000 }),
    [double]$MinProb = $(if ($env:MIN_PROB) { $env:MIN_PROB } else { 0.02 }),
    [int]$MinCount = $(if ($env:MIN_COUNT) { $env:MIN_COUNT } else { 100 })
)

$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path $ReportDir, $FigureDir, "data/interim", "data/processed" | Out-Null

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
    --figure "$FigureDir/benchmark.png"

Write-Host ""
Write-Host "Done."
Write-Host "Summary:              $ReportDir/summary.json"
Write-Host "Analysis:             $ReportDir/analysis.json"
Write-Host "Static overview:      $FigureDir/graph_overview.png"
Write-Host "Interactive graph:    $FigureDir/interactive_graph.html"
Write-Host "Interactive path:     $FigureDir/interactive_path.html"
Write-Host "Benchmark CSV:        data/processed/benchmark.csv"
Write-Host "Benchmark figure:     $FigureDir/benchmark.png"
