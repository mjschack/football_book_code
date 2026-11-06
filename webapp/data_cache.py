"""Shared play-by-play data loading, cached once for every model in the app.

Mirrors the per-chapter download pattern already used in the book's scripts
(check for a local cache file, else pull with nfl_data_py) but keeps a single
shared cache so the web app doesn't re-download the same seasons five times.
"""
import os

import nfl_data_py as nfl
import pandas as pd

SEASONS = range(2016, 2022 + 1)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CACHE_FILE = os.path.join(DATA_DIR, "pbp_py_webapp_cache.parquet")

_pbp_cache = None


def load_pbp():
    """Load cached play-by-play data, downloading it on first run."""
    global _pbp_cache
    if _pbp_cache is not None:
        return _pbp_cache

    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.isfile(CACHE_FILE):
        pbp_py = pd.read_parquet(CACHE_FILE)
    else:
        pbp_py = nfl.import_pbp_data(list(SEASONS), downcast=True, cache=False)
        pbp_py.to_parquet(CACHE_FILE)

    _pbp_cache = pbp_py
    return pbp_py
