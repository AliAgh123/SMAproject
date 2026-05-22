from stockfish import Stockfish
from scipy.stats import spearmanr
from sklearn.metrics import ndcg_score
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler


STOCKFISH_PATH  = "/usr/games/stockfish"
STOCKFISH_DEPTH = 15


def get_player(fen):
    return fen.split(" ")[1]


def outcome_for_player(outcomes, fen):
    total = sum(outcomes)
    if total == 0:
        return 0.5
    w, b, d = outcomes
    return w / total if get_player(fen) == "w" else b / total


def get_node_fen(G, h):
    return G.nodes[str(h)].get("fen", None)


def get_node_outcomes(G, h):
    o = G.nodes[str(h)].get("outcomes", {})
    if isinstance(o, dict):
        return [o.get("W", 0), o.get("D", 0), o.get("L", 0)]
    return o


def compute_danger(G, path):
    dangers = []
    for i in range(len(path) - 1):
        current = str(path[i])
        chosen  = str(path[i + 1])
        fen     = get_node_fen(G, current)
        if not fen:
            dangers.append(0.0)
            continue
        children = list(G.successors(current))
        if len(children) <= 1:
            dangers.append(0.0)
            continue
        chosen_ev = outcome_for_player(get_node_outcomes(G, chosen), fen)
        other_evs = [outcome_for_player(get_node_outcomes(G, c), fen)
                     for c in children if c != chosen]
        dangers.append(chosen_ev - np.mean(other_evs))
    return dangers


def eval_path_stockfish(G, sf_instance, path):
    scores = []
    for h in path:
        fen = get_node_fen(G, h)
        if not fen:
            continue
        sf_instance.set_fen_position(fen)
        ev = sf_instance.get_evaluation()
        cp = (1000 if ev["value"] > 0 else -1000) if ev["type"] == "mate" else ev["value"]
        scores.append(cp)
    return scores


def evaluate_paths_stockfish(G, top_paths_input, stockfish_path=STOCKFISH_PATH, stockfish_depth=STOCKFISH_DEPTH):
    sf_instance = Stockfish(path=stockfish_path, depth=stockfish_depth)
    path_sf_scores = {}
    for path, score in top_paths_input:
        key = tuple(path)
        path_sf_scores[key] = eval_path_stockfish(G, sf_instance, path)
    print("Done:", len(path_sf_scores), "paths")
    return path_sf_scores


def plot_scatter_comp(G, top_paths_input, path_sf_scores, label=""):

    dfs_scores = [score for _, score in top_paths_input]
    sf_avgs    = [np.mean(path_sf_scores[tuple(p)]) for p, _ in top_paths_input]
    labels     = [f"P{i+1}" for i in range(len(top_paths_input))]
    dangers    = [np.mean(compute_danger(G, p)) for p, _ in top_paths_input]

    dfs_norm   = MinMaxScaler().fit_transform(np.array(dfs_scores).reshape(-1,1)).flatten()
    sf_norm    = MinMaxScaler().fit_transform(np.array(sf_avgs).reshape(-1,1)).flatten()

    rho, pval  = spearmanr(dfs_norm, sf_norm)
    sf_shifted = np.array(sf_norm) - min(sf_norm)
    ndcg       = ndcg_score(np.array([sf_shifted]), np.array([dfs_norm]))

    fig, ax = plt.subplots(figsize=(9, 6))

    scatter = ax.scatter(dfs_norm, sf_norm,
                         c=dangers, cmap="RdYlGn_r",
                         vmin=0, vmax=max(dangers),
                         s=120, edgecolors="black", linewidths=0.5, zorder=3)

    m, b   = np.polyfit(dfs_norm, sf_norm, 1)
    x_line = np.linspace(min(dfs_norm), max(dfs_norm), 100)
    ax.plot(x_line, m * x_line + b, color="steelblue", linewidth=1.5,
            linestyle="--", label="Regression line")

    for i in range(len(top_paths_input)):
        ax.annotate(labels[i], (dfs_norm[i], sf_norm[i]),
                    fontsize=8, ha="left", va="bottom",
                    xytext=(5, 4), textcoords="offset points")

    x_pad = (max(dfs_norm) - min(dfs_norm)) * 0.15
    y_pad = (max(sf_norm)  - min(sf_norm))  * 0.15
    ax.set_xlim(min(dfs_norm) - x_pad, max(dfs_norm) + x_pad)
    ax.set_ylim(min(sf_norm)  - y_pad, max(sf_norm)  + y_pad)

    ax.axhline(0, color="black", linewidth=0.8, zorder=1)
    ax.axvline(0, color="black", linewidth=0.8, zorder=1)

    plt.colorbar(scatter, ax=ax, label="Avg danger score (red = harder for humans)")
    ax.set_xlabel("Model Score (normalized)",             fontsize=12)
    ax.set_ylabel("Stockfish Avg Centipawn (normalized)", fontsize=12)
    ax.set_title(f"{label}  |  Spearman ρ = {rho:.3f}  |  NDCG = {ndcg:.3f}",
                 fontsize=13)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

    print(f"Spearman ρ = {rho:.3f}  (p={pval:.4f})")
    print(f"NDCG       = {ndcg:.3f}")

    return fig, rho, pval, ndcg
