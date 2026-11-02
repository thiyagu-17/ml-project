"""Exploratory data analysis figures for the Data Prep and EDA tab.

Reads  public/data/cricsheet-matches-raw.csv and cricsheet-matches-clean.csv
Writes the EDA figures and eda-summary.json into public/analysis/

Run:  python public/analysis/eda_cricket.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import plot_style as ps

PUBLIC_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PUBLIC_DIR / "data"
OUTPUT_DIR = PUBLIC_DIR / "analysis"

NUMERIC_FOR_CORRELATION = [
    "first_innings_runs", "first_innings_wickets", "first_innings_overs",
    "first_innings_run_rate", "powerplay_runs", "powerplay_run_rate",
    "boundary_share", "dot_ball_share", "extras_share",
    "second_innings_runs", "second_innings_run_rate",
]

PRETTY = {
    "first_innings_runs": "1st inns runs",
    "first_innings_wickets": "1st inns wickets",
    "first_innings_overs": "1st inns overs",
    "first_innings_run_rate": "1st inns run rate",
    "powerplay_runs": "Powerplay runs",
    "powerplay_run_rate": "Powerplay run rate",
    "boundary_share": "Boundary share",
    "dot_ball_share": "Dot-ball share",
    "extras_share": "Extras share",
    "second_innings_runs": "2nd inns runs",
    "second_innings_run_rate": "2nd inns run rate",
}


# --------------------------------------------------------------------------
# Raw and clean comparison
# --------------------------------------------------------------------------


def figure_raw_and_clean_tables(raw: pd.DataFrame, clean: pd.DataFrame) -> None:
    """Show a readable slice of the data before and after cleaning."""
    raw_slice = raw[[
        "match_id", "date", "match_type", "city", "winner",
        "winner_runs", "method", "second_innings_runs",
    ]].head(7).fillna("(missing)")
    ps.table_figure(
        raw_slice, "raw-sample-table.png",
        "Raw match table, straight from the Cricsheet archives",
        f"{len(raw):,} rows x {raw.shape[1]} columns, {int(raw.isna().sum().sum()):,} empty cells",
    )

    clean_slice = clean[[
        "match_id", "date", "match_type", "city", "winner",
        "first_innings_runs", "first_innings_run_rate", "result_label",
    ]].head(7)
    ps.table_figure(
        clean_slice, "clean-sample-table.png",
        "Cleaned match table used for every model on this site",
        f"{len(clean):,} rows x {clean.shape[1]} columns, 0 empty cells",
    )


def figure_missing_values(raw: pd.DataFrame, clean: pd.DataFrame) -> None:
    """Compare empty cells per column before and after cleaning."""
    shared = [c for c in raw.columns if c in clean.columns]
    missing = raw[shared].isna().sum().sort_values(ascending=False).head(10)
    missing = missing[missing > 0]

    figure, axis = ps.new_axes(9.5, 5.4)
    positions = np.arange(len(missing))
    axis.barh(positions, missing.values, height=0.6, color=ps.ORANGE, label="Raw file")
    for position, value in zip(positions, missing.values):
        axis.text(value + 12, position, f"{value:,}", va="center", fontsize=9.5, color=ps.SLATE)
        # The cleaned file has no empty cells, so mark the zero explicitly
        # rather than drawing a bar of zero width that cannot be seen.
        axis.plot(0, position, marker="|", markersize=13, markeredgewidth=3, color=ps.TEAL)

    axis.set_yticks(positions, [c.replace("_", " ").capitalize() for c in missing.index])
    axis.invert_yaxis()
    axis.set_xlim(-14, missing.max() * 1.16)
    handles = [
        ps.plt.Rectangle((0, 0), 1, 1, color=ps.ORANGE),
        ps.plt.Line2D([0], [0], marker="|", markersize=13, markeredgewidth=3,
                      color=ps.TEAL, linestyle="none"),
    ]
    axis.legend(handles, ["Raw file", "Cleaned file (zero in every column)"],
                loc="lower right")
    ps.finish(figure, axis, "missing-values.png",
              "Every empty cell is resolved between the raw and cleaned files",
              "Number of empty cells", "")


# --------------------------------------------------------------------------
# Distribution and relationship figures
# --------------------------------------------------------------------------


def figure_runs_distribution(clean: pd.DataFrame) -> None:
    figure, axis = ps.new_axes(9.5, 5.2)
    for fmt, colour in ps.FORMAT_COLOURS.items():
        subset = clean.loc[clean["match_type"] == fmt, "first_innings_runs"]
        axis.hist(subset, bins=45, alpha=0.62, color=colour,
                  label=f"{fmt} (n={len(subset):,}, median {subset.median():.0f})")
    axis.legend(loc="upper right")
    ps.finish(figure, axis, "runs-distribution.png",
              "First-innings totals separate cleanly by format",
              "Runs scored in the first innings", "Number of matches")


def figure_run_rate_by_format(clean: pd.DataFrame) -> None:
    figure, axis = ps.new_axes(9.0, 5.2)
    groups, labels, colours = [], [], []
    for fmt in ["ODI", "T20"]:
        for gender in ["male", "female"]:
            subset = clean[(clean["match_type"] == fmt) & (clean["gender"] == gender)]
            if len(subset) < 25:
                continue
            groups.append(subset["first_innings_run_rate"].values)
            labels.append(f"{fmt}\n{gender}")
            colours.append(ps.FORMAT_COLOURS[fmt])

    box = axis.boxplot(groups, patch_artist=True, widths=0.55,
                       medianprops={"color": ps.INK, "linewidth": 1.8},
                       flierprops={"marker": ".", "markersize": 3,
                                   "markerfacecolor": ps.SLATE,
                                   "markeredgecolor": "none", "alpha": 0.35})
    for patch, colour in zip(box["boxes"], colours):
        patch.set_facecolor(colour)
        patch.set_alpha(0.65)
        patch.set_edgecolor(ps.SLATE)
    axis.set_xticks(range(1, len(labels) + 1), labels)
    ps.finish(figure, axis, "run-rate-by-format.png",
              "Scoring speed rises with the shorter format",
              "", "First-innings runs per over")


def figure_runs_vs_overs(clean: pd.DataFrame) -> None:
    figure, axis = ps.new_axes(9.3, 5.4)
    for fmt, colour in ps.FORMAT_COLOURS.items():
        subset = clean[clean["match_type"] == fmt]
        axis.scatter(subset["first_innings_overs"], subset["first_innings_runs"],
                     s=9, alpha=0.3, color=colour, edgecolor="none", label=fmt)
    # Reference lines sit in the empty band between the two formats so that
    # their labels never land on top of the data.
    for rate, style in [(4, ":"), (6, "--"), (9, "-.")]:
        overs = np.array([0, 50])
        axis.plot(overs, overs * rate, style, color=ps.SLATE, linewidth=1.1, alpha=0.75)
        axis.text(25.5, 25.5 * rate, f"{rate} runs/over", fontsize=8.5, color=ps.SLATE,
                  va="center", ha="center", rotation=0,
                  bbox={"facecolor": ps.PAGE_BG, "edgecolor": "none", "pad": 1.6})
    axis.set_xlim(0, 52)
    axis.set_ylim(0, clean["first_innings_runs"].max() * 1.05)
    legend = axis.legend(loc="upper left", markerscale=2.6)
    for handle in legend.legend_handles:
        handle.set_alpha(1)
    ps.finish(figure, axis, "runs-vs-overs.png",
              "Innings length and total runs trace two distinct formats",
              "Overs faced in the first innings", "Runs scored")


def figure_wickets_distribution(clean: pd.DataFrame) -> None:
    figure, axis = ps.new_axes(9.0, 5.0)
    width = 0.38
    for offset, (fmt, colour) in zip([-width / 2, width / 2], ps.FORMAT_COLOURS.items()):
        counts = clean.loc[clean["match_type"] == fmt, "first_innings_wickets"].value_counts()
        counts = counts.reindex(range(11), fill_value=0).sort_index()
        share = 100 * counts / counts.sum()
        axis.bar(np.arange(11) + offset, share.values, width=width, color=colour, label=fmt)
    axis.set_xticks(range(11))
    axis.legend()
    ps.finish(figure, axis, "wickets-distribution.png",
              "Twenty-over innings far more often end with wickets in hand",
              "Wickets lost in the first innings", "Share of that format's matches (%)")


def figure_correlation_heatmap(clean: pd.DataFrame) -> None:
    matrix = clean[NUMERIC_FOR_CORRELATION].corr()
    labels = [PRETTY[c] for c in matrix.columns]

    figure, axis = ps.new_axes(8.6, 7.2)
    axis.grid(False)
    image = axis.imshow(matrix.values, cmap="BrBG", vmin=-1, vmax=1)
    axis.set_xticks(range(len(labels)), labels, rotation=45, ha="right", fontsize=9)
    axis.set_yticks(range(len(labels)), labels, fontsize=9)
    for row in range(len(labels)):
        for column in range(len(labels)):
            value = matrix.values[row, column]
            axis.text(column, row, f"{value:.2f}", ha="center", va="center",
                      fontsize=7.6, color="white" if abs(value) > 0.55 else ps.INK)
    bar = figure.colorbar(image, ax=axis, shrink=0.78)
    bar.set_label("Pearson correlation", fontsize=10)
    axis.spines[["left", "bottom"]].set_visible(False)
    ps.finish(figure, axis, "correlation-heatmap.png",
              "Run rate, boundaries and dot balls move together", "", "")


def figure_matches_per_year(clean: pd.DataFrame) -> None:
    counts = clean.pivot_table(index="year", columns="match_type",
                               values="match_id", aggfunc="count").fillna(0)
    counts = counts.loc[counts.index < counts.index.max()]

    figure, axis = ps.new_axes(9.5, 5.0)
    bottom = np.zeros(len(counts))
    for fmt in ["ODI", "T20"]:
        if fmt not in counts.columns:
            continue
        axis.bar(counts.index, counts[fmt], bottom=bottom,
                 color=ps.FORMAT_COLOURS[fmt], label=fmt, width=0.78)
        bottom += counts[fmt].values
    axis.legend(loc="upper left")
    ps.finish(figure, axis, "matches-per-year.png",
              "Twenty-over cricket overtakes the fifty-over game after 2015",
              "Year", "Matches in the cleaned dataset")


def figure_scoring_trend(clean: pd.DataFrame) -> None:
    figure, axis = ps.new_axes(9.5, 5.0)
    for fmt, colour in ps.FORMAT_COLOURS.items():
        subset = clean[clean["match_type"] == fmt]
        yearly = subset.groupby("year")["first_innings_run_rate"].agg(["mean", "count", "std"])
        yearly = yearly[yearly["count"] >= 15]
        error = yearly["std"] / np.sqrt(yearly["count"])
        axis.plot(yearly.index, yearly["mean"], color=colour, linewidth=2.2, marker="o",
                  markersize=4, label=fmt)
        axis.fill_between(yearly.index, yearly["mean"] - error, yearly["mean"] + error,
                          color=colour, alpha=0.2)
    axis.legend(loc="center left")
    ps.finish(figure, axis, "scoring-trend.png",
              "Average scoring rate has drifted upward in both formats",
              "Year", "Mean first-innings runs per over")


def figure_powerplay_vs_total(clean: pd.DataFrame) -> None:
    figure, axis = ps.new_axes(9.3, 5.3)
    for fmt, colour in ps.FORMAT_COLOURS.items():
        subset = clean[clean["match_type"] == fmt]
        axis.scatter(subset["powerplay_runs"], subset["first_innings_runs"],
                     s=9, alpha=0.26, color=colour, edgecolor="none")
        slope, intercept = np.polyfit(subset["powerplay_runs"], subset["first_innings_runs"], 1)
        grid = np.linspace(subset["powerplay_runs"].min(), subset["powerplay_runs"].max(), 50)
        correlation = subset["powerplay_runs"].corr(subset["first_innings_runs"])
        axis.plot(grid, slope * grid + intercept, color=colour, linewidth=2.4,
                  label=f"{fmt}: r = {correlation:.2f}")
    axis.legend(loc="upper left")
    ps.finish(figure, axis, "powerplay-vs-total.png",
              "A strong powerplay only loosely predicts the final total",
              "Runs scored during the powerplay", "First-innings total")


def figure_boundary_and_dots(clean: pd.DataFrame) -> None:
    figure, axes = ps.plt.subplots(1, 2, figsize=(11.5, 4.8))
    for axis in axes:
        axis.grid(alpha=0.16, linewidth=0.8)
        axis.set_axisbelow(True)
        axis.spines[["top", "right"]].set_visible(False)

    # Outlined histograms with a light fill keep both formats legible where
    # the two distributions overlap.
    for fmt, colour in ps.FORMAT_COLOURS.items():
        subset = clean[clean["match_type"] == fmt]
        for axis, column in [(axes[0], "boundary_share"), (axes[1], "dot_ball_share")]:
            values = 100 * subset[column]
            axis.hist(values, bins=36, color=colour, alpha=0.26)
            axis.hist(values, bins=36, histtype="step", color=colour,
                      linewidth=2.0, label=f"{fmt} (median {values.median():.0f}%)")

    axes[0].set(title="Runs that came from boundaries",
                xlabel="Share of the total from fours and sixes (%)", ylabel="Matches")
    axes[1].set(title="Deliveries that produced no run",
                xlabel="Share of legal deliveries that were dots (%)", ylabel="Matches")
    for axis in axes:
        axis.title.set_fontweight("bold")
        axis.legend()
    ps.save(figure, "boundary-and-dots.png")


def figure_top_venues(clean: pd.DataFrame) -> None:
    counts = clean["venue"].value_counts().head(15).sort_values()
    figure, axis = ps.new_axes(9.5, 5.6)
    axis.barh([ps.shorten(v, 34) for v in counts.index], counts.values,
              color=ps.TEAL, height=0.72)
    for position, value in enumerate(counts.values):
        axis.text(value + 1.5, position, str(value), va="center", fontsize=9, color=ps.SLATE)
    axis.set_xlim(0, counts.max() * 1.12)
    ps.finish(figure, axis, "top-venues.png",
              "Fifteen grounds host a disproportionate share of the fixtures",
              "Matches hosted", "")


def figure_top_teams(clean: pd.DataFrame) -> None:
    counts = pd.concat([clean["team_a"], clean["team_b"]]).value_counts().head(15).sort_values()
    figure, axis = ps.new_axes(9.5, 5.6)
    axis.barh([ps.shorten(t, 30) for t in counts.index], counts.values,
              color=ps.PLUM, height=0.72)
    for position, value in enumerate(counts.values):
        axis.text(value + 6, position, str(value), va="center", fontsize=9, color=ps.SLATE)
    axis.set_xlim(0, counts.max() * 1.12)
    ps.finish(figure, axis, "top-teams.png",
              "The full-member nations dominate the fixture list",
              "Matches played", "")


def figure_toss_and_result(clean: pd.DataFrame) -> None:
    figure, axes = ps.plt.subplots(1, 2, figsize=(11.5, 4.9))
    for axis in axes:
        axis.grid(alpha=0.16, linewidth=0.8, axis="y")
        axis.set_axisbelow(True)
        axis.spines[["top", "right"]].set_visible(False)

    decisions = clean.groupby("toss_decision")["toss_winner_won_match"].agg(["mean", "count"])
    axes[0].bar([f"Chose to {d}\n(n={int(decisions.loc[d, 'count']):,})" for d in decisions.index],
                100 * decisions["mean"], color=[ps.TEAL, ps.ORANGE], width=0.55)
    axes[0].axhline(50, color=ps.INK, linestyle="--", linewidth=1.2)
    axes[0].text(-0.46, 53, "even odds", fontsize=9.5, color=ps.INK, ha="left", style="italic")
    axes[0].set(title="Does winning the toss help?", ylabel="Toss winner went on to win (%)",
                ylim=(0, 72))
    for position, value in enumerate(100 * decisions["mean"]):
        axes[0].text(position, value + 1.5, f"{value:.1f}%", ha="center", fontsize=10)

    shares = clean.groupby("match_type")["result_label"].value_counts(normalize=True).unstack()
    bottom = np.zeros(len(shares))
    for label in ["Defended", "Chased"]:
        axes[1].bar(shares.index, 100 * shares[label], bottom=bottom,
                    color=ps.RESULT_COLOURS[label], label=label, width=0.52)
        for position, (base, value) in enumerate(zip(bottom, 100 * shares[label])):
            axes[1].text(position, base + value / 2, f"{value:.1f}%", ha="center",
                         color="white", fontweight="bold", fontsize=10)
        bottom += 100 * shares[label].values
    axes[1].set(title="How first-innings totals are decided", ylabel="Share of matches (%)")
    axes[1].legend(loc="lower center", ncols=2, bbox_to_anchor=(0.5, -0.22))

    for axis in axes:
        axis.title.set_fontweight("bold")
    ps.save(figure, "toss-and-result.png")


def figure_weather(clean: pd.DataFrame) -> bool:
    """Plot scoring against match-day temperature when the API data exists."""
    weather_path = DATA_DIR / "venue-weather.csv"
    if not weather_path.exists():
        return False
    weather = pd.read_csv(weather_path)
    merged = clean.merge(weather, on=["city", "date"], how="inner")
    if len(merged) < 150:
        return False

    merged["temp_band"] = pd.cut(merged["temp_max_c"], [0, 20, 25, 30, 35, 60],
                                 labels=["<20", "20-25", "25-30", "30-35", "35+"])
    figure, axis = ps.new_axes(9.3, 5.2)
    for fmt, colour in ps.FORMAT_COLOURS.items():
        subset = merged[merged["match_type"] == fmt]
        banded = subset.groupby("temp_band", observed=True)["first_innings_run_rate"].agg(["mean", "count"])
        banded = banded[banded["count"] >= 12]
        axis.plot(banded.index.astype(str), banded["mean"], marker="o", markersize=7,
                  linewidth=2.2, color=colour, label=f"{fmt} (n={int(subset.shape[0]):,})")
    axis.legend()
    ps.finish(figure, axis, "weather-vs-scoring.png",
              "Match-day temperature barely moves the scoring rate",
              "Daytime maximum temperature (°C)", "Mean first-innings run rate")
    return True


# --------------------------------------------------------------------------


def main() -> None:
    raw = pd.read_csv(DATA_DIR / "cricsheet-matches-raw.csv", low_memory=False)
    clean = pd.read_csv(DATA_DIR / "cricsheet-matches-clean.csv")
    print(f"  raw {raw.shape}  clean {clean.shape}", flush=True)

    figure_raw_and_clean_tables(raw, clean)
    figure_missing_values(raw, clean)
    figure_runs_distribution(clean)
    figure_run_rate_by_format(clean)
    figure_runs_vs_overs(clean)
    figure_wickets_distribution(clean)
    figure_correlation_heatmap(clean)
    figure_matches_per_year(clean)
    figure_scoring_trend(clean)
    figure_powerplay_vs_total(clean)
    figure_boundary_and_dots(clean)
    figure_top_venues(clean)
    figure_top_teams(clean)
    figure_toss_and_result(clean)
    has_weather = figure_weather(clean)

    correlations = clean[NUMERIC_FOR_CORRELATION].corr()["first_innings_runs"].drop("first_innings_runs")
    summary = {
        "raw_rows": int(len(raw)),
        "raw_columns": int(raw.shape[1]),
        "raw_missing_cells": int(raw.isna().sum().sum()),
        "clean_rows": int(len(clean)),
        "clean_columns": int(clean.shape[1]),
        "clean_missing_cells": int(clean.isna().sum().sum()),
        "rows_removed": int(len(raw) - len(clean)),
        "date_range": [clean["date"].min(), clean["date"].max()],
        "venues": int(clean["venue"].nunique()),
        "cities": int(clean["city"].nunique()),
        "teams": int(pd.concat([clean["team_a"], clean["team_b"]]).nunique()),
        "formats": clean["match_type"].value_counts().to_dict(),
        "genders": clean["gender"].value_counts().to_dict(),
        "label_balance": clean["result_label"].value_counts().to_dict(),
        "toss_winner_win_rate": round(float(clean["toss_winner_won_match"].mean()), 4),
        "toss_chose_to_bat_rate": round(float(clean["toss_winner_batted"].mean()), 4),
        "median_runs": clean.groupby("match_type")["first_innings_runs"].median().to_dict(),
        "mean_run_rate": clean.groupby("match_type")["first_innings_run_rate"].mean().round(2).to_dict(),
        "powerplay_correlation": round(
            float(clean["powerplay_runs"].corr(clean["first_innings_runs"])), 3),
        "strongest_correlations": correlations.abs().sort_values(ascending=False).head(4).round(3).to_dict(),
        "has_weather": has_weather,
        "figure_count": 14 + int(has_weather),
    }
    with open(OUTPUT_DIR / "eda-summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
