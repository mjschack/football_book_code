import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from flask import Flask, jsonify, request, send_from_directory

from models import Models, poisson_probs

app = Flask(__name__, static_folder="static", static_url_path="")

print("Loading data and fitting models (first run downloads 2016-2022 play-by-play data)...")
fitted = Models()
print("Models ready.")


def model_meta(fit):
    return {
        "r_squared": getattr(fit, "rsquared", None),
        "n_obs": int(fit.nobs),
        "params": {k: round(float(v), 5) for k, v in fit.params.items()},
    }


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/model-info")
def model_info():
    return jsonify(
        {
            "ryoe_simple": model_meta(fitted.ryoe_simple),
            "ryoe_multi": model_meta(fitted.ryoe_multi),
            "completion_simple": model_meta(fitted.completion_simple),
            "completion_multi": model_meta(fitted.completion_multi),
            "pass_td": model_meta(fitted.pass_td),
        }
    )


@app.post("/api/ryoe-simple")
def ryoe_simple():
    body = request.get_json(force=True)
    ydstogo = float(body["ydstogo"])
    row = pd.DataFrame({"ydstogo": [ydstogo]})
    pred = float(fitted.ryoe_simple.predict(row)[0])
    return jsonify({"expected_rushing_yards": round(pred, 3)})


@app.post("/api/ryoe-multi")
def ryoe_multi():
    body = request.get_json(force=True)
    row = pd.DataFrame(
        {
            "down": [str(float(body["down"]))],
            "ydstogo": [float(body["ydstogo"])],
            "yardline_100": [float(body["yardline_100"])],
            "run_location": [body["run_location"]],
            "score_differential": [float(body["score_differential"])],
        }
    )
    pred = float(fitted.ryoe_multi.predict(row)[0])
    result = {"expected_rushing_yards": round(pred, 3)}
    if body.get("actual_yards") not in (None, ""):
        actual = float(body["actual_yards"])
        result["ryoe"] = round(actual - pred, 3)
    return jsonify(result)


@app.post("/api/completion-simple")
def completion_simple():
    body = request.get_json(force=True)
    row = pd.DataFrame({"air_yards": [float(body["air_yards"])]})
    pred = float(fitted.completion_simple.predict(row)[0])
    return jsonify({"completion_probability": round(pred, 4)})


@app.post("/api/completion-multi")
def completion_multi():
    body = request.get_json(force=True)
    row = pd.DataFrame(
        {
            "down": [str(float(body["down"]))],
            "ydstogo": [float(body["ydstogo"])],
            "yardline_100": [float(body["yardline_100"])],
            "air_yards": [float(body["air_yards"])],
            "pass_location": [body["pass_location"]],
            "qb_hit": [str(float(body["qb_hit"]))],
        }
    )
    pred = float(fitted.completion_multi.predict(row)[0])
    result = {"completion_probability": round(pred, 4)}
    if body.get("completed") not in (None, ""):
        actual = float(body["completed"])
        result["cpoe"] = round(actual - pred, 4)
    return jsonify(result)


@app.post("/api/pass-td")
def pass_td():
    body = request.get_json(force=True)
    row = pd.DataFrame(
        {
            "pass_td_rate": [float(body["pass_td_rate"])],
            "total_line": [float(body["total_line"])],
        }
    )
    mu = float(fitted.pass_td.predict(row)[0])
    result = {"expected_pass_td": round(mu, 4)}
    result.update({k: round(v, 4) for k, v in poisson_probs(mu).items()})
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
