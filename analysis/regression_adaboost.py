"""Linear regression, logistic regression and AdaBoost for the Part 4 tabs.

Every model here uses the same disjoint 70/30 split as the Naive Bayes and
Decision Tree models (supervised-train.csv and supervised-test.csv, matched by
match_id), so all accuracies on the site are measured on the same test rows.

Rule followed throughout: the test set is never used to choose anything.
Settings are chosen with cross-validation or a validation set carved out of
the training set; each chosen model is then scored once on the test set.

Questions answered
------------------
Linear regression:   how many runs will the first innings finish with, given
                     only what happened in the powerplay and the match context?
Logistic regression: at the innings break, will the total be defended or
                     chased down? (the same question as Naive Bayes)
AdaBoost:            the same Defended/Chased question, with boosted stumps.

Reads  public/data/cricsheet-matches-clean.csv
       public/data/supervised-train.csv, public/data/supervised-test.csv
       public/analysis/supervised-results.json (Part 3 results, for comparison)
Writes figures, regression/adaboost CSVs and regression-adaboost-results.json

Run:  python public/analysis/regression_adaboost.py
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import AdaBoostClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, mean_absolute_error,
                             mean_squared_error, r2_score, roc_auc_score)
from sklearn.model_selection import (GridSearchCV, KFold, StratifiedKFold,
                                     cross_val_score, cross_validate, train_test_split)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

import plot_style as ps
from supervised_models import CLASS_NAMES, SHORT, plot_confusion

PUBLIC_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PUBLIC_DIR / "data"
OUTPUT_DIR = PUBLIC_DIR / "analysis"
RANDOM_STATE = 42

# AdaBoost's staged_predict passes plain arrays to the fitted stumps internally,
# which makes scikit-learn 1.3 warn about missing column names. The values are
# in the same column order, so the warning is noise.
warnings.filterwarnings("ignore", message="X does not have valid feature names")

# --------------------------------------------------------------------------
# Shared inputs
# --------------------------------------------------------------------------


def load_inputs():
    clean = pd.read_csv(DATA_DIR / "cricsheet-matches-clean.csv").set_index("match_id")
    train = pd.read_csv(DATA_DIR / "supervised-train.csv")
    test = pd.read_csv(DATA_DIR / "supervised-test.csv")
    overlap = set(train["match_id"]) & set(test["match_id"])
    assert not overlap, "training and testing sets must be disjoint"
    return clean, train, test


def table(frame, filename, title, subtitle, wrap=9, width=13.5):
    ps.table_figure(frame, filename, title, subtitle, width=width,
                    wrap_columns=wrap, fontsize=9.5)


# --------------------------------------------------------------------------
# Linear regression
# --------------------------------------------------------------------------

LINEAR_TARGET = "first_innings_runs"
LINEAR_BASE = ["powerplay_runs", "powerplay_wickets"]
LINEAR_CONTEXT = ["is_t20", "is_womens", "toss_winner_batted"]
LINEAR_NAMES = {
    "powerplay_runs": "PP runs",
    "powerplay_wickets": "PP wickets",
    "is_t20": "Is T20",
    "is_womens": "Is women's",
    "toss_winner_batted": "Toss winner batted",
    "pp_runs_x_t20": "PP runs x T20",
    "pp_wickets_x_t20": "PP wickets x T20",
    "first_innings_runs": "TOTAL (target)",
}


def linear_frame(clean, ids):
    rows = clean.loc[ids]
    frame = pd.DataFrame({
        "powerplay_runs": rows["powerplay_runs"].to_numpy(),
        "powerplay_wickets": rows["powerplay_wickets"].to_numpy(),
        "is_t20": (rows["match_type"] == "T20").astype(int).to_numpy(),
        "is_womens": (rows["gender"] == "female").astype(int).to_numpy(),
        "toss_winner_batted": rows["toss_winner_batted"].to_numpy(),
    }, index=ids)
    # Interaction terms let each format have its own slope: one powerplay run
    # is a bigger share of a twenty-over innings than of a fifty-over one.
    frame["pp_runs_x_t20"] = frame["powerplay_runs"] * frame["is_t20"]
    frame["pp_wickets_x_t20"] = frame["powerplay_wickets"] * frame["is_t20"]
    return frame, rows[LINEAR_TARGET].astype(float)


LINEAR_CANDIDATES = {
    "A: powerplay only": LINEAR_BASE,
    "B: + format, gender, toss": LINEAR_BASE + LINEAR_CONTEXT,
    "C: + separate slopes per format": LINEAR_BASE + LINEAR_CONTEXT
    + ["pp_runs_x_t20", "pp_wickets_x_t20"],
}


def run_linear(clean, train, test):
    X_train_all, y_train = linear_frame(clean, train["match_id"].to_numpy())
    X_test_all, y_test = linear_frame(clean, test["match_id"].to_numpy())

    # Choose the feature set by 5-fold cross-validation on the training set.
    folds = KFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    candidates = []
    for name, columns in LINEAR_CANDIDATES.items():
        scores = cross_validate(LinearRegression(), X_train_all[columns], y_train, cv=folds,
                                scoring=("neg_root_mean_squared_error", "r2"))
        candidates.append({"name": name, "features": len(columns),
                           "cv_rmse": round(float(-scores["test_neg_root_mean_squared_error"].mean()), 2),
                           "cv_r2": round(float(scores["test_r2"].mean()), 4)})
    chosen = min(candidates, key=lambda row: row["cv_rmse"])
    columns = LINEAR_CANDIDATES[chosen["name"]]

    model = LinearRegression().fit(X_train_all[columns], y_train)
    predicted = model.predict(X_test_all[columns])
    is_t20 = X_test_all["is_t20"].to_numpy() == 1

    # A reference point: predicting each format's average total from training.
    format_means = y_train.groupby(X_train_all["is_t20"].to_numpy()).mean()
    baseline = np.where(is_t20, format_means[1], format_means[0])

    coefficients = dict(zip(columns, model.coef_))
    slopes = {
        "odi_run": coefficients.get("powerplay_runs", 0.0),
        "t20_run": coefficients.get("powerplay_runs", 0.0) + coefficients.get("pp_runs_x_t20", 0.0),
        "odi_wicket": coefficients.get("powerplay_wickets", 0.0),
        "t20_wicket": coefficients.get("powerplay_wickets", 0.0) + coefficients.get("pp_wickets_x_t20", 0.0),
    }
    results = {
        "target": "First-innings total (runs)",
        "candidates": candidates,
        "chosen": chosen["name"],
        "features": [LINEAR_NAMES[c] for c in columns],
        "intercept": round(float(model.intercept_), 2),
        "coefficients": {LINEAR_NAMES[c]: round(float(v), 3) for c, v in coefficients.items()},
        "slopes": {k: round(float(v), 2) for k, v in slopes.items()},
        "test_rmse": round(float(mean_squared_error(y_test, predicted) ** 0.5), 2),
        "test_mae": round(float(mean_absolute_error(y_test, predicted)), 2),
        "test_r2": round(float(r2_score(y_test, predicted)), 4),
        "test_r2_odi": round(float(r2_score(y_test[~is_t20], predicted[~is_t20])), 4),
        "test_r2_t20": round(float(r2_score(y_test[is_t20], predicted[is_t20])), 4),
        "test_mae_odi": round(float(mean_absolute_error(y_test[~is_t20], predicted[~is_t20])), 2),
        "test_mae_t20": round(float(mean_absolute_error(y_test[is_t20], predicted[is_t20])), 2),
        "baseline_rmse": round(float(mean_squared_error(y_test, baseline) ** 0.5), 2),
        "baseline_mae": round(float(mean_absolute_error(y_test, baseline)), 2),
        "train_rows": int(len(y_train)),
        "test_rows": int(len(y_test)),
    }

    # Data files and table images.
    for name, X, y, ids in [("train", X_train_all, y_train, train["match_id"]),
                            ("test", X_test_all, y_test, test["match_id"])]:
        export = X[columns].copy()
        export.insert(0, "match_id", ids.to_numpy())
        export[LINEAR_TARGET] = y.to_numpy()
        export.to_csv(DATA_DIR / f"regression-{name}.csv", index=False)

    def sample(X, y, ids):
        frame = X[columns].head(6).copy()
        frame.insert(0, LINEAR_TARGET, y.head(6).astype(int).to_numpy())
        frame.insert(0, "Match ID", ids.head(6).astype(str).to_numpy())
        frame.columns = ["Match ID"] + [LINEAR_NAMES[c] for c in frame.columns[1:]]
        return frame

    table(sample(X_train_all, y_train, train["match_id"]), "regression-data-sample.png",
          "Linear regression data: a numeric target and numeric inputs",
          "TOTAL is the number being predicted; every other column is known by the end of the powerplay")
    table(sample(X_train_all, y_train, train["match_id"]), "regression-train-sample.png",
          f"Linear regression training set: first 6 of {len(y_train):,} rows",
          "Same matches as the classification training set; no match ID appears in the testing set")
    table(sample(X_test_all, y_test, test["match_id"]), "regression-test-sample.png",
          f"Linear regression testing set: first 6 of {len(y_test):,} rows",
          "Held back until the feature set was chosen, then used once")

    # Predicted against actual.
    figure, axis = ps.new_axes(8.6, 6.4)
    for fmt, mask, colour in [("ODI", ~is_t20, ps.FORMAT_COLOURS["ODI"]),
                              ("T20", is_t20, ps.FORMAT_COLOURS["T20"])]:
        axis.scatter(y_test[mask], predicted[mask], s=12, alpha=0.4, color=colour,
                     edgecolor="none", label=f"{fmt} (n={int(mask.sum()):,})")
    limit = [0, max(float(y_test.max()), float(predicted.max())) * 1.04]
    axis.plot(limit, limit, "--", color=ps.INK, linewidth=1.3, label="Perfect prediction")
    axis.set_xlim(limit)
    axis.set_ylim(limit)
    legend = axis.legend(loc="upper left", markerscale=2.2)
    for handle in legend.legend_handles:
        handle.set_alpha(1)
    axis.text(0.98, 0.04, f"Test R² = {results['test_r2']:.2f}\nTest MAE = {results['test_mae']:.0f} runs",
              transform=axis.transAxes, ha="right", va="bottom", fontsize=10.5,
              bbox={"facecolor": ps.PAGE_BG, "edgecolor": ps.SAND, "pad": 5})
    ps.finish(figure, axis, "regression-predicted-actual.png",
              "Predicted against actual first-innings totals (testing set)",
              "Actual total (runs)", "Predicted total (runs)")

    # Cross-validation comparison of the candidate feature sets.
    figure, axis = ps.new_axes(9.2, 4.4)
    names = [row["name"] for row in candidates]
    values = [row["cv_rmse"] for row in candidates]
    colours = [ps.TEAL if name == chosen["name"] else ps.SAND for name in names]
    axis.barh(names, values, color=colours, height=0.55)
    for position, value in enumerate(values):
        axis.text(value + 0.4, position, f"{value:.1f} runs", va="center", fontsize=10)
    axis.invert_yaxis()
    axis.set_xlim(0, max(values) * 1.18)
    ps.finish(figure, axis, "regression-feature-selection.png",
              "Choosing the inputs by 5-fold cross-validation (training set only)",
              "Cross-validated RMSE (lower is better)", "")

    # Residuals by format.
    figure, axis = ps.new_axes(9.0, 4.8)
    residual = y_test.to_numpy() - predicted
    for fmt, mask, colour in [("ODI", ~is_t20, ps.FORMAT_COLOURS["ODI"]),
                              ("T20", is_t20, ps.FORMAT_COLOURS["T20"])]:
        axis.hist(residual[mask], bins=40, alpha=0.55, color=colour, label=fmt)
    axis.axvline(0, color=ps.INK, linestyle="--", linewidth=1.2)
    axis.legend()
    ps.finish(figure, axis, "regression-residuals.png",
              "Prediction errors on the testing set, by format",
              "Actual minus predicted total (runs)", "Matches")
    return results


# --------------------------------------------------------------------------
# Logistic regression
# --------------------------------------------------------------------------

C_GRID = np.logspace(-3, 2, 11)


def run_logistic(train, test, part3):
    X_train = train.drop(columns=["match_id", "LABEL"])
    X_test = test.drop(columns=["match_id", "LABEL"])
    y_train = (train["LABEL"] == "Defended").astype(int)
    y_test = (test["LABEL"] == "Defended").astype(int)

    pipeline = make_pipeline(StandardScaler(), LogisticRegression(max_iter=5000))
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    search = GridSearchCV(pipeline, {"logisticregression__C": C_GRID}, cv=folds,
                          scoring="accuracy", return_train_score=False).fit(X_train, y_train)
    cv_scores = search.cv_results_["mean_test_score"]
    best_c = float(search.best_params_["logisticregression__C"])
    model = search.best_estimator_

    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]
    matrix = confusion_matrix(y_test, predictions)
    scaler = model.named_steps["standardscaler"]
    logistic = model.named_steps["logisticregression"]
    per_sd = dict(zip(X_train.columns, logistic.coef_[0]))
    per_unit = {c: v / s for (c, v), s in zip(per_sd.items(), scaler.scale_)}

    results = {
        "c_grid": [round(float(c), 5) for c in C_GRID],
        "cv_accuracy": [round(float(s), 4) for s in cv_scores],
        "best_c": round(best_c, 5),
        "best_cv_accuracy": round(float(search.best_score_), 4),
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
        "confusion_matrix": matrix.tolist(),
        "intercept": round(float(logistic.intercept_[0]), 4),
        "odds_ratio_per_sd": {SHORT[c]: round(float(np.exp(v)), 3) for c, v in per_sd.items()},
        "coef_per_unit": {SHORT[c]: round(float(v), 5) for c, v in per_unit.items()},
        "feature_sd": {SHORT[c]: round(float(s), 4) for c, s in zip(X_train.columns, scaler.scale_)},
        "odds_per_10_runs": round(float(np.exp(10 * per_unit["first_innings_runs"])), 3),
        "odds_per_wicket": round(float(np.exp(per_unit["first_innings_wickets"])), 3),
        "odds_per_run_rate": round(float(np.exp(per_unit["first_innings_run_rate"])), 3),
        "odds_toss_batted": round(float(np.exp(per_unit["toss_winner_batted"])), 3),
    }

    # Validation curve for C.
    figure, axis = ps.new_axes(9.2, 4.8)
    axis.plot(C_GRID, 100 * cv_scores, marker="o", markersize=7, linewidth=2.3, color=ps.TEAL)
    axis.set_xscale("log")
    axis.axvline(best_c, color=ps.SLATE, linestyle="--", linewidth=1.2)
    axis.text(best_c * 1.15, 100 * cv_scores.min() + 0.15, f"chosen C = {best_c:g}",
              fontsize=10, color=ps.SLATE)
    ps.finish(figure, axis, "logistic-tuning.png",
              "Choosing the regularisation strength by 5-fold cross-validation",
              "C (smaller = stronger regularisation, log scale)", "Cross-validated accuracy (%)")

    # Confusion matrix.
    figure, axis = ps.plt.subplots(figsize=(5.4, 4.6))
    plot_confusion(axis, matrix, "Logistic regression", results["accuracy"])
    ps.save(figure, "logistic-confusion-matrix.png")

    # Odds ratios per standard deviation.
    odds = pd.Series(results["odds_ratio_per_sd"]).sort_values()
    figure, axis = ps.new_axes(9.4, 5.8)
    colours = [ps.TEAL if v >= 1 else ps.ORANGE for v in odds.values]
    axis.barh(odds.index, odds.values - 1, left=1, color=colours, height=0.65)
    axis.axvline(1, color=ps.INK, linewidth=1.2)
    for position, value in enumerate(odds.values):
        axis.text(value + (0.03 if value >= 1 else -0.03), position, f"x{value:.2f}",
                  va="center", ha="left" if value >= 1 else "right", fontsize=9.5)
    axis.set_xscale("log")
    low, high = odds.min(), odds.max()
    axis.set_xlim(low / 1.5, high * 1.5)
    ticks = [t for t in [0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4, 6] if low / 1.5 <= t <= high * 1.5]
    axis.set_xticks(ticks, [f"x{t:g}" for t in ticks])
    axis.xaxis.set_minor_locator(ps.plt.NullLocator())
    ps.finish(figure, axis, "logistic-odds-ratios.png",
              "How each input changes the odds of the total being defended",
              "Odds multiplier for a one-standard-deviation increase (log scale)", "")

    # Comparison with Naive Bayes on the same test set.
    rows = [(name, part3["naive_bayes"][name]["accuracy"]) for name in part3["naive_bayes"]]
    rows.append(("Logistic regression", results["accuracy"]))
    figure, axis = ps.new_axes(9.2, 4.4)
    names = [r[0] for r in rows]
    values = [100 * r[1] for r in rows]
    colours = [ps.TEAL if n == "Logistic regression" else ps.SAND for n in names]
    axis.barh(names, values, color=colours, height=0.55)
    axis.axvline(100 * part3["majority_class_baseline"], color=ps.INK, linestyle="--", linewidth=1.2)
    for position, value in enumerate(values):
        axis.text(value + 0.3, position, f"{value:.1f}%", va="center", fontsize=10)
    axis.set_ylim(len(rows) - 0.5, -1.1)
    axis.text(100 * part3["majority_class_baseline"] + 0.3, -0.85,
              "baseline: always guess the commoner outcome", fontsize=9, color=ps.INK, va="center")
    axis.set_xlim(45, max(values) + 5)
    ps.finish(figure, axis, "logistic-vs-naive-bayes.png",
              "Logistic regression against the Part 3 Naive Bayes models (same testing set)",
              "Test accuracy (%)", "")
    return results


# --------------------------------------------------------------------------
# AdaBoost
# --------------------------------------------------------------------------

NUMERIC_FOR_BOOSTING = [
    "first_innings_runs", "first_innings_wickets", "first_innings_fours",
    "first_innings_sixes", "first_innings_extras", "powerplay_runs", "powerplay_wickets",
    "first_innings_run_rate", "powerplay_run_rate", "boundary_share", "dot_ball_share",
]
CATEGORICAL = ["match_type", "gender", "toss_decision"]
LEARNING_RATES = [0.05, 0.1, 0.25, 0.5, 1.0]
MAX_ROUNDS = 600


def boosting_frame(clean, ids):
    """Numeric columns as they are, categorical columns one-hot encoded."""
    rows = clean.loc[ids]
    raw = rows[NUMERIC_FOR_BOOSTING + CATEGORICAL].copy()
    encoded = pd.get_dummies(raw, columns=CATEGORICAL, dtype=int)
    return raw, encoded


def stump_model(rounds, rate):
    return AdaBoostClassifier(estimator=DecisionTreeClassifier(max_depth=1),
                              n_estimators=rounds, learning_rate=rate,
                              algorithm="SAMME", random_state=RANDOM_STATE)


def run_adaboost(clean, train, test, part3):
    raw_train, X_train = boosting_frame(clean, train["match_id"].to_numpy())
    _, X_test = boosting_frame(clean, test["match_id"].to_numpy())
    X_test = X_test.reindex(columns=X_train.columns, fill_value=0)
    y_train = (train["LABEL"] == "Defended").astype(int).to_numpy()
    y_test = (test["LABEL"] == "Defended").astype(int).to_numpy()

    # Data files and the one-hot encoding step.
    for name, X, y, ids in [("train", X_train, y_train, train["match_id"]),
                            ("test", X_test, y_test, test["match_id"])]:
        export = X.copy()
        export.insert(0, "match_id", ids.to_numpy())
        export["LABEL"] = np.where(y == 1, "Defended", "Chased")
        export.to_csv(DATA_DIR / f"adaboost-{name}.csv", index=False)

    before = raw_train[CATEGORICAL].head(6).reset_index()
    before.columns = ["Match ID", "match_type", "gender", "toss_decision"]
    onehot_columns = [c for c in X_train.columns if c.startswith(tuple(f"{c}_" for c in CATEGORICAL))]
    after = X_train[onehot_columns].head(6).reset_index()
    after = after.rename(columns={after.columns[0]: "Match ID"})
    table(before, "adaboost-onehot-before.png",
          "Before one-hot encoding: three text columns",
          "AdaBoost in scikit-learn cannot split on text such as 'ODI' or 'field'")
    table(after, "adaboost-onehot-after.png",
          "After one-hot encoding: one 0/1 column per category",
          "pd.get_dummies turns each category into its own yes/no column", wrap=9)

    def labelled(X, y, ids):
        frame = X.head(6).copy()
        frame.insert(0, "Match ID", ids.head(6).astype(str).to_numpy())
        frame.insert(0, "LABEL", np.where(y[:6] == 1, "Defended", "Chased"))
        frame.columns = [SHORT.get(c, c) for c in frame.columns]
        return frame.round(3)

    table(labelled(X_train, y_train, train["match_id"]), "adaboost-train-sample.png",
          f"AdaBoost training set: first 6 of {len(y_train):,} rows",
          "Numeric columns plus the one-hot columns; same matches as every other model", wrap=10, width=16)
    table(labelled(X_test, y_test, test["match_id"]), "adaboost-test-sample.png",
          f"AdaBoost testing set: first 6 of {len(y_test):,} rows",
          "Untouched until the number of rounds and the learning rate were fixed", wrap=10, width=16)

    # Tuning: a validation set carved out of the training set only.
    X_fit, X_val, y_fit, y_val = train_test_split(
        X_train, y_train, test_size=0.25, random_state=RANDOM_STATE, stratify=y_train)
    curves, best = {}, None
    for rate in LEARNING_RATES:
        model = stump_model(MAX_ROUNDS, rate).fit(X_fit, y_fit)
        staged = np.array([accuracy_score(y_val, p) for p in model.staged_predict(X_val)])
        curves[rate] = staged
        rounds = int(np.argmax(staged)) + 1
        if best is None or staged.max() > best["val_accuracy"]:
            best = {"learning_rate": rate, "n_estimators": rounds,
                    "val_accuracy": float(staged.max())}

    # Confirm the chosen settings are stable with 5-fold CV (still training data only).
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    cv = cross_val_score(stump_model(best["n_estimators"], best["learning_rate"]),
                         X_train, y_train, cv=folds, scoring="accuracy")

    final = stump_model(best["n_estimators"], best["learning_rate"]).fit(X_train, y_train)
    predictions = final.predict(X_test)
    probabilities = final.predict_proba(X_test)[:, 1]
    matrix = confusion_matrix(y_test, predictions)

    stumps = []
    for tree, weight, error in zip(final.estimators_[:6], final.estimator_weights_[:6],
                                   final.estimator_errors_[:6]):
        feature = X_train.columns[tree.tree_.feature[0]]
        stumps.append({"feature": SHORT.get(feature, feature),
                       "threshold": round(float(tree.tree_.threshold[0]), 3),
                       "weighted_error": round(float(error), 4),
                       "alpha": round(float(weight), 4)})

    tree_a = part3["decision_trees"]["Tree A - Gini, depth 3"]
    results = {
        "features": [SHORT.get(c, c) for c in X_train.columns],
        "n_features": int(X_train.shape[1]),
        "learning_rates": LEARNING_RATES,
        "max_rounds": MAX_ROUNDS,
        "fit_rows": int(len(y_fit)),
        "validation_rows": int(len(y_val)),
        "best_by_rate": {str(rate): {"rounds": int(np.argmax(c)) + 1,
                                     "val_accuracy": round(float(c.max()), 4)}
                         for rate, c in curves.items()},
        "chosen": {"learning_rate": best["learning_rate"], "n_estimators": best["n_estimators"],
                   "val_accuracy": round(best["val_accuracy"], 4)},
        "cv_accuracy": round(float(cv.mean()), 4),
        "cv_std": round(float(cv.std()), 4),
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "train_accuracy": round(float(final.score(X_train, y_train)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
        "confusion_matrix": matrix.tolist(),
        "first_stumps": stumps,
        "tree_a_accuracy": tree_a["accuracy"],
        "gain_over_tree_a_points": round(100 * (accuracy_score(y_test, predictions) - tree_a["accuracy"]), 2),
    }

    # Validation accuracy as rounds are added.
    figure, axis = ps.new_axes(10.0, 5.4)
    palette = [ps.SAND, ps.PLUM, ps.ORANGE, ps.TEAL, ps.SLATE]
    rounds_axis = np.arange(1, MAX_ROUNDS + 1)
    for colour, (rate, curve) in zip(palette, curves.items()):
        axis.plot(rounds_axis, 100 * curve, linewidth=1.9, color=colour,
                  label=f"learning rate {rate}")
    axis.scatter([best["n_estimators"]], [100 * best["val_accuracy"]], s=140, marker="*",
                 color=ps.INK, zorder=5, label=f"chosen: {best['n_estimators']} rounds, "
                                               f"rate {best['learning_rate']}")
    axis.set_xscale("log")
    axis.legend(loc="lower right", fontsize=9.5)
    ps.finish(figure, axis, "adaboost-validation-curve.png",
              "Validation accuracy as boosting rounds are added",
              "Number of rounds (log scale)", "Validation accuracy (%)")

    # Best validation accuracy per learning rate.
    figure, axis = ps.new_axes(8.8, 4.4)
    rates = [str(r) for r in LEARNING_RATES]
    values = [100 * curves[r].max() for r in LEARNING_RATES]
    colours = [ps.TEAL if r == best["learning_rate"] else ps.SAND for r in LEARNING_RATES]
    axis.bar(rates, values, color=colours, width=0.55)
    for position, (r, value) in enumerate(zip(LEARNING_RATES, values)):
        axis.text(position, value + 0.1, f"{value:.1f}%\n({int(np.argmax(curves[r])) + 1} rounds)",
                  ha="center", fontsize=9.5)
    axis.set_ylim(min(values) - 2, max(values) + 1.6)
    ps.finish(figure, axis, "adaboost-learning-rates.png",
              "Best validation accuracy reached at each learning rate",
              "Learning rate", "Best validation accuracy (%)")

    # Confusion matrix.
    figure, axis = ps.plt.subplots(figsize=(5.4, 4.6))
    plot_confusion(axis, matrix, "AdaBoost", results["accuracy"])
    ps.save(figure, "adaboost-confusion-matrix.png")

    # Which features the stumps used, weighted by alpha.
    importance = pd.Series(final.feature_importances_,
                           index=[SHORT.get(c, c) for c in X_train.columns]).sort_values()
    importance = importance[importance > 0.002]
    figure, axis = ps.new_axes(9.2, 5.4)
    axis.barh(importance.index, 100 * importance.values, color=ps.TEAL, height=0.65)
    for position, value in enumerate(100 * importance.values):
        axis.text(value + 0.4, position, f"{value:.1f}%", va="center", fontsize=9.5)
    axis.set_xlim(0, 100 * importance.max() * 1.18)
    ps.finish(figure, axis, "adaboost-feature-importance.png",
              "Which measurements the boosted stumps rely on",
              "Share of total importance (%)", "")
    return results


# --------------------------------------------------------------------------
# All models on the same testing set
# --------------------------------------------------------------------------


def figure_model_comparison(part3, logistic, adaboost):
    rows = [(name, r["accuracy"]) for name, r in part3["naive_bayes"].items()]
    rows += [(name.split(" - ")[0], r["accuracy"]) for name, r in part3["decision_trees"].items()]
    rows += [("Logistic regression", logistic["accuracy"]), ("AdaBoost", adaboost["accuracy"])]
    rows.sort(key=lambda r: r[1])
    figure, axis = ps.new_axes(9.6, 5.4)
    names = [r[0] for r in rows]
    values = [100 * r[1] for r in rows]
    new = {"Logistic regression", "AdaBoost"}
    colours = [ps.TEAL if n in new else ps.SAND for n in names]
    axis.barh(names, values, color=colours, height=0.6)
    for position, value in enumerate(values):
        axis.text(value + 0.2, position, f"{value:.1f}%", va="center", fontsize=10)
    axis.axvline(100 * part3["majority_class_baseline"], color=ps.INK, linestyle="--", linewidth=1.2)
    axis.set_xlim(45, max(values) + 4)
    handles = [ps.plt.Rectangle((0, 0), 1, 1, color=ps.TEAL), ps.plt.Rectangle((0, 0), 1, 1, color=ps.SAND),
               ps.plt.Line2D([0], [0], color=ps.INK, linestyle="--")]
    axis.legend(handles, ["Part 4 models", "Part 3 models", "Majority-class baseline"],
                loc="upper center", bbox_to_anchor=(0.45, -0.14), ncols=3, fontsize=9.5)
    ps.finish(figure, axis, "model-comparison.png",
              "Every classifier so far, scored on the same untouched testing set",
              "Test accuracy (%)", "")
    return [{"model": n, "accuracy": round(float(v) / 100, 4)} for n, v in zip(names, values)]


def main() -> None:
    clean, train, test = load_inputs()
    part3 = json.loads((OUTPUT_DIR / "supervised-results.json").read_text(encoding="utf-8"))
    print(f"  train {len(train)}  test {len(test)}  overlap 0", flush=True)

    print("  Linear regression", flush=True)
    linear = run_linear(clean, train, test)
    print(f"    chosen {linear['chosen']}  test R2={linear['test_r2']}  MAE={linear['test_mae']}", flush=True)

    print("  Logistic regression", flush=True)
    logistic = run_logistic(train, test, part3)
    print(f"    C={logistic['best_c']}  test accuracy={logistic['accuracy']}", flush=True)

    print("  AdaBoost", flush=True)
    adaboost = run_adaboost(clean, train, test, part3)
    print(f"    chosen {adaboost['chosen']}  test accuracy={adaboost['accuracy']}", flush=True)

    comparison = figure_model_comparison(part3, logistic, adaboost)
    results = {
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "overlapping_rows": 0,
        "majority_class_baseline": part3["majority_class_baseline"],
        "linear": linear,
        "logistic": logistic,
        "adaboost": adaboost,
        "comparison": comparison,
    }
    with open(OUTPUT_DIR / "regression-adaboost-results.json", "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)


if __name__ == "__main__":
    main()
