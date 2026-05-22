# save_pickle(data, path)
# load_pickle(path)
# save_json(data, path)
# load_json(path)


from pathlib import Path
import json
import pickle


def save_pickle(data, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("wb") as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)


def load_pickle(path: str | Path):
    path = Path(path)

    with path.open("rb") as f:
        return pickle.load(f)


def save_json(data, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w") as f:
        json.dump(data, f)


def load_json(path: str | Path):
    path = Path(path)

    with path.open("r") as f:
        return json.load(f)