import time
from tqdm import tqdm
from sma_chess.loading.pgn_parser import _fmt_duration


def run_pass2(
    node_occurrence,
    transitions,
    outcomes,
    hash_to_fen,
    max_nodes: int = 10000,
    min_prob: float = 0.02,
    min_count: int = 100,
) -> dict:
    t_start   = time.perf_counter()
    top_nodes = {h for h, _ in node_occurrence.most_common(max_nodes)}
    final_adj = {}

    with tqdm(
        top_nodes,
        desc="Pass 2 — pruning",
        unit=" nodes",
        bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}]",
    ) as pbar:
        for curr_hash in pbar:
            node_trans  = transitions.get(curr_hash, {})
            total_exits = sum(node_trans.values())
            if total_exits < min_count:
                continue

            valid_edges = {
                str(nh): {"prob": round(cnt / total_exits, 4), "count": cnt}
                for nh, cnt in node_trans.items()
                if cnt / total_exits >= min_prob and nh in top_nodes
            }

            if valid_edges:
                final_adj[str(curr_hash)] = {
                    "edges":        valid_edges,
                    "outcomes":     outcomes.get(curr_hash, [0, 0, 0]),
                    "total_visits": total_exits,
                    "fen":          hash_to_fen.get(curr_hash),
                }

    t_done = time.perf_counter() - t_start
    print(f"\n✓ Pass 2 done in {_fmt_duration(t_done)}")
    print(f"  Final graph: {len(final_adj):,} nodes\n")
    return final_adj