"""Model fitting for the web app.

Each function reproduces the filtering + statsmodels formula from the
matching chapter of the book's Python code, fit once at startup and reused
for every prediction request.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.stats import poisson

from data_cache import load_pbp


class Models:
    def __init__(self):
        pbp_py = load_pbp()

        self.ryoe_simple = self._fit_ryoe_simple(pbp_py)
        self.ryoe_multi = self._fit_ryoe_multi(pbp_py)
        self.completion_simple = self._fit_completion_simple(pbp_py)
        self.completion_multi = self._fit_completion_multi(pbp_py)
        self.pass_td = self._fit_pass_td(pbp_py)

    # Chapter 3: rushing_yards ~ 1 + ydstogo
    def _fit_ryoe_simple(self, pbp_py):
        run = pbp_py.query('play_type == "run" & rusher_id.notnull()').reset_index()
        run.loc[run.rushing_yards.isnull(), "rushing_yards"] = 0
        return smf.ols(formula="rushing_yards ~ 1 + ydstogo", data=run).fit()

    # Chapter 4: rushing_yards ~ 1 + down + ydstogo + down:ydstogo + yardline_100 + run_location + score_differential
    def _fit_ryoe_multi(self, pbp_py):
        run = pbp_py.query(
            'play_type == "run" & rusher_id.notnull() & down.notnull() & run_location.notnull()'
        ).reset_index()
        run.loc[run.rushing_yards.isnull(), "rushing_yards"] = 0
        run["down"] = run["down"].astype(str)
        return smf.ols(
            data=run,
            formula="rushing_yards ~ 1 + down + ydstogo + "
            + "down:ydstogo + yardline_100 + "
            + "run_location + score_differential",
        ).fit()

    # Chapter 5 (simple): complete_pass ~ air_yards
    def _fit_completion_simple(self, pbp_py):
        passes = pbp_py.query(
            'play_type == "pass" & passer_id.notnull() & air_yards.notnull()'
        ).reset_index()
        return smf.glm(
            formula="complete_pass ~ air_yards", data=passes, family=sm.families.Binomial()
        ).fit()

    # Chapter 5 (multiple): complete_pass ~ down * ydstogo + yardline_100 + air_yards + pass_location + qb_hit
    def _fit_completion_multi(self, pbp_py):
        passes = pbp_py.query(
            'play_type == "pass" & passer_id.notnull() & air_yards.notnull()'
        ).reset_index()
        passes["down"] = passes["down"].astype(str)
        passes["qb_hit"] = passes["qb_hit"].astype(str)
        passes_no_miss = passes[
            [
                "passer",
                "passer_id",
                "season",
                "down",
                "qb_hit",
                "complete_pass",
                "ydstogo",
                "yardline_100",
                "air_yards",
                "pass_location",
            ]
        ].dropna(axis=0)
        return smf.glm(
            formula="complete_pass ~ down * ydstogo + "
            + "yardline_100 + air_yards + "
            + "pass_location + qb_hit",
            data=passes_no_miss,
            family=sm.families.Binomial(),
        ).fit()

    # Chapter 6: pass_td_y ~ pass_td_rate + total_line (Poisson)
    def _fit_pass_td(self, pbp_py):
        passes = pbp_py.query("passer_id.notnull()").reset_index()
        passes.loc[passes.pass_touchdown.isnull(), "pass_touchdown"] = 0
        passes.loc[passes.passer.isnull(), "passer"] = "none"
        passes.loc[passes.passer_id.isnull(), "passer_id"] = "none"

        pass_td_y = passes.groupby(["season", "week", "passer_id", "passer"]).agg(
            {"pass_touchdown": ["sum"], "total_line": ["count", "mean"]}
        )
        pass_td_y.columns = list(map("_".join, pass_td_y.columns))
        pass_td_y.reset_index(inplace=True)
        pass_td_y.rename(
            columns={
                "pass_touchdown_sum": "pass_td_y",
                "total_line_mean": "total_line",
                "total_line_count": "n_passes",
            },
            inplace=True,
        )
        pass_td_y_geq10 = pass_td_y.query("n_passes >= 10")

        x_py = pd.DataFrame()
        for season_idx in range(2017, 2022 + 1):
            for week_idx in range(1, 22 + 1):
                week_calc = (
                    pass_td_y_geq10.query(
                        "(season == "
                        + str(season_idx - 1)
                        + ") |"
                        + "(season == "
                        + str(season_idx)
                        + "&"
                        + "week < "
                        + str(week_idx)
                        + ")"
                    )
                    .groupby(["passer_id", "passer"])
                    .agg({"pass_td_y": ["count", "mean"]})
                )
                week_calc.columns = list(map("_".join, week_calc.columns))
                week_calc.reset_index(inplace=True)
                week_calc.rename(
                    columns={"pass_td_y_count": "n_games", "pass_td_y_mean": "pass_td_rate"},
                    inplace=True,
                )
                week_calc["season"] = season_idx
                week_calc["week"] = week_idx
                x_py = pd.concat([x_py, week_calc])

        pass_td_y_geq10 = pass_td_y_geq10.query("season != 2016").merge(
            x_py, on=["season", "week", "passer_id", "passer"], how="inner"
        )

        return smf.glm(
            formula="pass_td_y ~ pass_td_rate + total_line",
            data=pass_td_y_geq10,
            family=sm.families.Poisson(),
        ).fit()


def poisson_probs(mu):
    return {
        "p0": float(poisson.pmf(k=0, mu=mu)),
        "p1": float(poisson.pmf(k=1, mu=mu)),
        "p2": float(poisson.pmf(k=2, mu=mu)),
        "p_ge3": float(1 - poisson.cdf(k=2, mu=mu)),
    }
