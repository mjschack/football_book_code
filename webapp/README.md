# Football Analytics Calculators (SPA)

A small single-page web app that lets you plug in game-situation values and
get predictions back from the Python models in this book (Chapters 3-6),
fit on real play-by-play data pulled with `nfl_data_py`. It reuses the same
filtering, formulas, and `statsmodels` calls as the chapter scripts — it
doesn't reimplement the stats.

Covers:
- Ch. 3: Rushing Yards Over Expected (simple linear regression)
- Ch. 4: Rushing Yards Over Expected (multiple regression)
- Ch. 5: Completion probability / CPOE (simple and multiple logistic GLM)
- Ch. 6: Expected passing touchdowns + Poisson probabilities

Chapters 1, 2, 7, and 8 are EDA, web scraping, and clustering — there's no
single "input values, get a prediction" calculator to build from those, so
they're not part of this app.

## Running it

```
cd webapp
python3 -m venv ../.venv   # optional but recommended
source ../.venv/bin/activate
pip install -r requirements.txt
python3 server.py
```

Then open http://localhost:5000/.

On first run the server downloads 2016-2022 play-by-play data (~1 minute)
and caches it to `../data/pbp_py_webapp_cache.parquet`; later restarts load
from that cache and fit the models in a few seconds. The cache file isn't
committed to the repo (same reasoning as the book's own per-chapter CSV
caches — it's large and easy to regenerate).

## Structure

- `data_cache.py` — shared data download/cache, used by all five models
- `models.py` — fits the five models, same formulas as the book's chapter scripts
- `server.py` — Flask app: serves the static frontend and a small JSON API
- `static/` — the SPA itself (`index.html`, `app.js`, `style.css`), no build step
