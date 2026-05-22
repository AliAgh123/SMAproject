import re
import chess
import chess.polyglot
from collections import defaultdict, Counter
import io
import time
import zstandard as zstd
from tqdm import tqdm

HEADER_RE     = re.compile(r'\[(\w+)\s+"([^"]*)"\]')
MOVE_NUM_RE   = re.compile(r'\d+\.+')
RESULT_TOKENS = frozenset({'1-0', '0-1', '1/2-1/2', '*'})


def _strip_comments_and_variations(text: str) -> str:
    out   = []
    brace = 0
    paren = 0
    for ch in text:
        if   ch == '{':
            brace += 1
        elif ch == '}':
            brace = max(brace - 1, 0)
        elif brace == 0:
            if   ch == '(':
                paren += 1
            elif ch == ')':
                paren = max(paren - 1, 0)
            elif paren == 0:
                out.append(ch)
    return ''.join(out)


def _extract_san_moves(movetext: str) -> list:
    clean = _strip_comments_and_variations(movetext)
    clean = MOVE_NUM_RE.sub(' ', clean)
    return [t for t in clean.split() if t not in RESULT_TOKENS]


def _iter_raw_games(text_stream):
    headers    = []
    move_parts = []
    for raw in text_stream:
        line = raw.rstrip()
        if not line:
            continue
        if line[0] == '[':
            if move_parts:
                yield headers, ' '.join(move_parts)
                headers    = []
                move_parts = []
            headers.append(line)
        else:
            move_parts.append(line)
    if move_parts:
        yield headers, ' '.join(move_parts)


def _parse_headers(header_lines: list) -> dict:
    out = {}
    for line in header_lines:
        m = HEADER_RE.match(line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def _fmt_duration(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    if h > 0:
        return f"{h}h {m}m {s:.1f}s"
    elif m > 0:
        return f"{m}m {s:.1f}s"
    else:
        return f"{s:.2f}s"



def run_pass1(
    pgn_zst_path: str,
    max_depth: int = 20,
    min_elo: int = 1000,
    min_main_time: int = 300,
) -> dict:
    hash_to_fen     = {}
    transitions     = defaultdict(Counter)
    outcomes        = defaultdict(lambda: [0, 0, 0])
    node_occurrence = Counter()

    dctx = zstd.ZstdDecompressor()
    game_count = processed_count = error_count = 0
    t_start    = time.perf_counter()

    print(f"Opening: {pgn_zst_path}\n")

    with open(pgn_zst_path, "rb") as fh, \
         dctx.stream_reader(fh) as reader:

        text_stream = io.TextIOWrapper(reader, encoding='utf-8', errors='replace')

        with tqdm(
            _iter_raw_games(text_stream),
            desc="Pass 1 — parsing",
            unit=" games",
            miniters=500,
            bar_format="{desc}: {n_fmt} games [{elapsed}, {rate_fmt}]{postfix}",
        ) as pbar:

            for header_lines, movetext in pbar:
                game_count += 1

                headers = _parse_headers(header_lines)
                try:
                    w_elo     = int(headers.get("WhiteElo",    "0") or "0")
                    b_elo     = int(headers.get("BlackElo",    "0") or "0")
                    tc        = headers.get("TimeControl", "0+0")
                    main_time = int(tc.split('+')[0]) if '+' in tc else 0
                except (ValueError, IndexError):
                    continue

                if w_elo < min_elo or b_elo < min_elo or main_time < min_main_time:
                    continue

                processed_count += 1
                res     = headers.get("Result", "*")
                # Outcome order throughout the project:
                # [white_wins, black_wins, draws]
                res_idx = 0 if res == "1-0" else 1 if res == "0-1" else 2

                san_moves = _extract_san_moves(movetext)
                board     = chess.Board()

                try:
                    for depth, san in enumerate(san_moves):
                        if depth >= max_depth:
                            break

                        curr_hash = chess.polyglot.zobrist_hash(board)

                        if curr_hash not in hash_to_fen:
                            hash_to_fen[curr_hash] = board.fen()

                        move = board.parse_san(san)
                        board.push(move)
                        next_hash = chess.polyglot.zobrist_hash(board)

                        transitions[curr_hash][next_hash] += 1
                        node_occurrence[curr_hash]         += 1
                        outcomes[curr_hash][res_idx]       += 1

                except (chess.InvalidMoveError, chess.IllegalMoveError,
                        chess.AmbiguousMoveError, ValueError):
                    error_count += 1
                    continue

                if game_count % 2000 == 0:
                    pbar.set_postfix(
                        kept   = f"{processed_count:,}",
                        errors = f"{error_count:,}",
                        nodes  = f"{len(node_occurrence):,}",
                    )

    t_pass1 = time.perf_counter() - t_start
    print(f"\n✓ Pass 1 done in {_fmt_duration(t_pass1)}")
    print(f"  Scanned: {game_count:,} | Kept: {processed_count:,} | "
          f"Errors: {error_count:,} | Unique nodes: {len(node_occurrence):,}\n")

    return {
        "hash_to_fen":     hash_to_fen,
        "transitions":     dict(transitions),
        "outcomes":        dict(outcomes),
        "node_occurrence": node_occurrence,
    }

