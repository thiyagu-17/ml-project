"""Naive Bayes and Decision Tree models for the supervised-learning tabs.

The question put to both models is a real forecasting problem: at the innings
break, knowing only what the team batting first did, will that total be
defended or chased down?

Every second-innings column is therefore excluded. Those columns describe the
chase itself, so including them would let the model read the answer off its own
input instead of predicting it.

Reads  public/data/cricsheet-matches-clean.csv
Writes the model figures, the train/test samples and supervised-results.json

Run:  python public/analysis/supervised_models.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, roc_auc_score, roc_curve
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.naive_bayes import BernoulliNB, GaussianNB, MultinomialNB
from sklearn.preprocessing import MinMaxScaler
from sklearn.tree import DecisionTreeClassifier, plot_tree

import plot_style as ps

PUBLIC_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PUBLIC_DIR / "data"
OUTPUT_DIR = PUBLIC_DIR / "analysis"

RANDOM_STATE = 42
TEST_SIZE = 0.30
CLASS_NAMES = ["Chased", "Defended"]

# Count-style features: every value is a non-negative whole number, which is
# what MultinomialNB expects.
COUNT_FEATURES = [
    "first_innings_runs", "first_innings_wickets", "first_innings_fours",
    "first_innings_sixes", "first_innings_extras", "powerplay_runs",
    "powerplay_wickets",
]

# Rate-style features, kept separate because they are proportions, not counts.
RATE_FEATURES = [
    "first_innings_run_rate", "powerplay_run_rate", "boundary_share", "dot_ball_share",
]

CONTEXT_FEATURES = ["is_t20", "is_womens", "toss_winner_batted"]

ALL_FEATURES = COUNT_FEATURES + RATE_FEATURES + CONTEXT_FEATURES

SHORT = {
    "first_innings_runs": "Runs",
    "first_innings_wickets": "Wickets",
    "first_innings_fours": "Fours",
    "first_innings_sixes": "Sixes",
    "first_innings_extras": "Extras",
    "powerplay_runs": "PP runs",
    "powerplay_wickets": "PP wickets",
    "first_innings_run_rate": "Run rate",
    "powerplay_run_rate": "PP run rate",
    "boundary_share": "Boundary %",
    "dot_ball_share": "Dot ball %",
    "is_t20": "Is T20",
    "is_womens": "Is women's",
    "toss_winner_batted": "Toss winner batted",
}


# --------------------------------------------------------------------------


def build_design_matrix(clean: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Assemble the labelled feature table and the target vector."""
    frame = clean.copy()
    frame["is_t20"] = (frame["match_type"] == "T20").astype(int)
    frame["is_womens"] = (frame["gender"] == "female").astype(int)

    features = frame[ALL_FEATURES].astype(float)
    # bat_first_won == 1 means the total was defended.
    target = frame["bat_first_won"].astype(int)
    return features, target


def plot_confusion(axis, matrix, title, accuracy) -> None:
    """Draw one labelled confusion matrix with counts and row percentages."""
    axis.grid(False)
    normalised = matrix / matrix.sum(axis=1, keepdims=True)
    axis.imshow(normalised, cmap="BuGn", vmin=0, vmax=1)
    for row in range(2):
        for column in range(2):
            axis.text(column, row,
                      f"{matrix[row, column]:,}\n{100 * normalised[row, column]:.1f}%",
                      ha="center", va="center", fontsize=11.5,
                      color="white" if normalised[row, column] > 0.55 else ps.INK,
                      fontweight="bold")
    axis.set_xticks([0, 1], [f"Predicted\n{name}" for name in CLASS_NAMES], fontsize=9.5)
    axis.set_yticks([0, 1], [f"Actual\n{name}" for name in CLASS_NAMES], fontsize=9.5)
    axis.set_title(f"{title}\naccuracy {accuracy:.1%}", fontsize=12, fontweight="bold", pad=10)
    for spine in axis.spines.values():
        spine.set_visible(False)


# --------------------------------------------------------------------------
# Data-preparation figures
# --------------------------------------------------------------------------


def figure_labelled_sample(features: pd.DataFrame, target: pd.Series) -> None:
    sample = features.head(6).copy().round(3)
    sample.insert(0, "LABEL", target.head(6).map({1: "Defended", 0: "Chased"}).values)
    sample.columns = ["LABEL"] + [SHORT[c] for c in features.columns]
    ps.table_figure(
        sample, "supervised-data-sample.png",
        "Labelled data: every row carries the answer the model must learn",
        f"{len(features):,} matches x {len(ALL_FEATURES)} features, plus one label column",
        max_columns=9, width=13.5,
    )


def figure_train_test(y_train, y_test) -> None:
    """Show that the split is disjoint, stratified and complete."""
    figure, axes = ps.plt.subplots(1, 2, figsize=(11.5, 4.6))
    for axis in axes:
        axis.grid(alpha=0.16, axis="y")
        axis.set_axisbelow(True)
        axis.spines[["top", "right"]].set_visible(False)

    total = len(y_train) + len(y_test)
    axes[0].bar(["Training set", "Testing set"], [len(y_train), len(y_test)],
                color=[ps.TEAL, ps.ORANGE], width=0.5)
    for position, value in enumerate([len(y_train), len(y_test)]):
        axes[0].text(position, value + total * 0.015,
                     f"{value:,}\n({value / total:.0%})", ha="center", fontsize=11)
    axes[0].set(title=f"Disjoint split of all {total:,} matches",
                ylabel="Number of matches", ylim=(0, total * 0.85))

    width = 0.36
    for offset, (name, series, colour) in zip(
        [-width / 2, width / 2],
        [("Training", y_train, ps.TEAL), ("Testing", y_test, ps.ORANGE)],
    ):
        shares = series.value_counts(normalize=True).sort_index()
        axes[1].bar(np.arange(2) + offset, 100 * shares.values, width=width,
                    color=colour, label=name)
        for position, value in zip(np.arange(2) + offset, 100 * shares.values):
            axes[1].text(position, value + 1.1, f"{value:.1f}%", ha="center", fontsize=10)
    axes[1].set_xticks(range(2), CLASS_NAMES)
    axes[1].set(title="Stratified: both sets keep the same class balance",
                ylabel="Share of the set (%)", ylim=(0, 68))
    axes[1].legend()

    for axis in axes:
        axis.title.set_fontweight("bold")
        axis.title.set_fontsize(12.5)
    ps.save(figure, "train-test-split.png")


def figure_class_separation(features: pd.DataFrame, target: pd.Series) -> None:
    """Class-conditional distributions, which are what Naive Bayes models."""
    chosen = ["first_innings_runs", "first_innings_run_rate",
              "dot_ball_share", "first_innings_wickets"]
    figure, axes = ps.plt.subplots(2, 2, figsize=(11.0, 6.6))
    for axis, column in zip(axes.ravel(), chosen):
        axis.grid(alpha=0.16)
        axis.set_axisbelow(True)
        axis.spines[["top", "right"]].set_visible(False)
        for value, name in enumerate(CLASS_NAMES):
            series = features.loc[target == value, column]
            axis.hist(series, bins=34, color=ps.RESULT_COLOURS[name], alpha=0.28)
            axis.hist(series, bins=34, histtype="step", linewidth=2.0,
                      color=ps.RESULT_COLOURS[name],
                      label=f"{name} (mean {series.mean():.2f})")
        axis.set_title(SHORT[column], fontsize=12, fontweight="bold")
        axis.set_ylabel("Matches")
        axis.legend(fontsize=9)
    figure.suptitle("Where the two outcomes differ, and where they overlap",
                    fontsize=14, fontweight="bold", x=0.01, ha="left")
    ps.save(figure, "class-separation.png")


# --------------------------------------------------------------------------
# Naive Bayes
# --------------------------------------------------------------------------


def run_naive_bayes(X_train, X_test, y_train, y_test) -> dict:
    """Fit the three Naive Bayes variants, each on the input form it assumes."""
    # MultinomialNB needs non-negative values, so the rate columns are mapped
    # onto [0, 1] using limits learned from the training set only.
    scaler = MinMaxScaler().fit(X_train)
    train_multinomial = scaler.transform(X_train)
    test_multinomial = np.clip(scaler.transform(X_test), 0, 1)

    # BernoulliNB expects on/off features, so each column is split at its
    # training-set median into "above typical" and "at or below typical".
    thresholds = X_train.median()
    train_bernoulli = (X_train > thresholds).astype(int)
    test_bernoulli = (X_test > thresholds).astype(int)

    models = {
        "Multinomial NB": (MultinomialNB(), train_multinomial, test_multinomial),
        "Bernoulli NB": (BernoulliNB(), train_bernoulli, test_bernoulli),
        "Gaussian NB": (GaussianNB(), X_train, X_test),
    }

    results, matrices = {}, {}
    for name, (model, train_data, test_data) in models.items():
        model.fit(train_data, y_train)
        predictions = model.predict(test_data)
        probabilities = model.predict_proba(test_data)[:, 1]
        accuracy = accuracy_score(y_test, predictions)
        matrices[name] = confusion_matrix(y_test, predictions)
        cv = cross_val_score(model, train_data, y_train, cv=5, scoring="accuracy")
        results[name] = {
            "accuracy": round(float(accuracy), 4),
            "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
            "cv_mean": round(float(cv.mean()), 4),
            "cv_std": round(float(cv.std()), 4),
            "confusion_matrix": matrices[name].tolist(),
            "probabilities": probabilities,
        }
        print(f"    {name:<16} accuracy={accuracy:.4f}  auc={results[name]['roc_auc']:.4f}",
              flush=True)

    figure, axes = ps.plt.subplots(1, 3, figsize=(12.6, 4.4))
    for axis, (name, result) in zip(axes, results.items()):
        plot_confusion(axis, np.array(result["confusion_matrix"]), name, result["accuracy"])
    figure.suptitle("Naive Bayes confusion matrices on the held-out testing set",
                    fontsize=14, fontweight="bold", x=0.01, ha="left")
    ps.save(figure, "nb-confusion-matrices.png")

    figure, axis = ps.new_axes(9.2, 5.0)
    for name, result in results.items():
        false_positive, true_positive, _ = roc_curve(y_test, result["probabilities"])
        axis.plot(false_positive, true_positive, linewidth=2.3,
                  label=f"{name} (AUC {result['roc_auc']:.3f})")
    axis.plot([0, 1], [0, 1], "--", color=ps.SLATE, linewidth=1.3, label="Random guessing")
    axis.legend(loc="lower right")
    ps.finish(figure, axis, "nb-roc-curves.png",
              "All three variants separate the two outcomes well above chance",
              "False positive rate", "True positive rate")

    for result in results.values():
        result.pop("probabilities")
    return results


# --------------------------------------------------------------------------
# Decision Trees
# --------------------------------------------------------------------------


def impurity_statistics(labels: np.ndarray) -> tuple[float, float]:
    """Return (gini, entropy) for a vector of binary labels."""
    if len(labels) == 0:
        return 0.0, 0.0
    proportions = np.array([np.mean(labels == value) for value in (0, 1)])
    gini = float(1 - np.sum(proportions ** 2))
    non_zero = proportions[proportions > 0]
    entropy = float(-np.sum(non_zero * np.log2(non_zero)))
    return gini, entropy


def figure_impurity_example(X_train: pd.DataFrame, y_train: pd.Series) -> dict:
    """Work one real split through Gini, entropy and information gain."""
    column = "first_innings_run_rate"
    threshold = round(float(X_train[column].median()), 2)
    labels = y_train.to_numpy()
    left = labels[X_train[column].to_numpy() <= threshold]
    right = labels[X_train[column].to_numpy() > threshold]

    parent_gini, parent_entropy = impurity_statistics(labels)
    left_gini, left_entropy = impurity_statistics(left)
    right_gini, right_entropy = impurity_statistics(right)
    weight_left, weight_right = len(left) / len(labels), len(right) / len(labels)
    child_entropy = weight_left * left_entropy + weight_right * right_entropy
    child_gini = weight_left * left_gini + weight_right * right_gini
    information_gain = parent_entropy - child_entropy

    def describe(name, values, gini, entropy):
        defended = int(np.sum(values == 1))
        chased = int(np.sum(values == 0))
        return (f"{name}\n{len(values):,} matches\n"
                f"Defended {defended:,}  |  Chased {chased:,}\n"
                f"Gini = {gini:.4f}\nEntropy = {entropy:.4f}")

    figure, axis = ps.plt.subplots(figsize=(10.6, 6.2))
    axis.axis("off")
    axis.set_xlim(0, 10)
    axis.set_ylim(0, 10)

    boxes = [
        (5.0, 8.5, describe("PARENT NODE (all training matches)", labels,
                            parent_gini, parent_entropy), ps.TEAL),
        (2.3, 4.2, describe(f"LEFT: run rate ≤ {threshold}", left,
                            left_gini, left_entropy), ps.ORANGE),
        (7.7, 4.2, describe(f"RIGHT: run rate > {threshold}", right,
                            right_gini, right_entropy), ps.PLUM),
    ]
    for x, y, text, colour in boxes:
        axis.text(x, y, text, ha="center", va="center", fontsize=10.2, color="white",
                  bbox={"boxstyle": "round,pad=0.62", "facecolor": colour,
                        "edgecolor": "none"})
    for x_end in (2.3, 7.7):
        axis.annotate("", xy=(x_end, 5.3), xytext=(5.0, 7.5),
                      arrowprops={"arrowstyle": "-|>", "color": ps.SLATE, "linewidth": 2})
    # Offset to the outside of each arrow so the text sits on clear background.
    axis.text(2.5, 6.75, f"{weight_left:.0%}\nof rows", fontsize=9.5, color=ps.SLATE,
              ha="right", va="center")
    axis.text(7.5, 6.75, f"{weight_right:.0%}\nof rows", fontsize=9.5, color=ps.SLATE,
              ha="left", va="center")

    # Four decimals throughout: the information gain here falls almost exactly
    # on a three-decimal rounding boundary, and showing three would make this
    # figure disagree with the same numbers quoted on the page.
    summary = (
        f"Weighted child entropy  =  {weight_left:.4f} x {left_entropy:.4f}  +  "
        f"{weight_right:.4f} x {right_entropy:.4f}  =  {child_entropy:.4f}\n"
        f"Information gain  =  parent entropy  -  weighted child entropy  =  "
        f"{parent_entropy:.4f}  -  {child_entropy:.4f}  =  {information_gain:.4f}\n"
        f"Weighted child Gini  =  {child_gini:.4f}   "
        f"(a drop of {parent_gini - child_gini:.4f} from the parent)"
    )
    axis.text(5.0, 0.95, summary, ha="center", va="center", fontsize=10.4, color=ps.INK,
              bbox={"boxstyle": "round,pad=0.6", "facecolor": "#ebe6d7",
                    "edgecolor": ps.SAND, "linewidth": 1.2})
    axis.set_title("Measuring the goodness of one split", loc="left",
                   fontsize=14, fontweight="bold", pad=6)
    ps.save(figure, "impurity-example.png")

    return {
        "feature": SHORT[column],
        "threshold": threshold,
        "parent_gini": round(parent_gini, 4),
        "parent_entropy": round(parent_entropy, 4),
        "left_count": int(len(left)),
        "right_count": int(len(right)),
        "left_entropy": round(left_entropy, 4),
        "right_entropy": round(right_entropy, 4),
        "weighted_child_entropy": round(child_entropy, 4),
        "information_gain": round(information_gain, 4),
        "weighted_child_gini": round(child_gini, 4),
    }


TREE_SETTINGS = [
    ("Tree A - Gini, depth 3",
     {"criterion": "gini", "max_depth": 3},
     "dt-tree-a-gini-depth3.png"),
    ("Tree B - Entropy, depth 4",
     {"criterion": "entropy", "max_depth": 4},
     "dt-tree-b-entropy-depth4.png"),
    ("Tree C - Gini, depth 6, leaves of 40+",
     {"criterion": "gini", "max_depth": 6, "min_samples_leaf": 40},
     "dt-tree-c-gini-depth6.png"),
]


def run_decision_trees(X_train, X_test, y_train, y_test) -> dict:
    feature_labels = [SHORT[c] for c in X_train.columns]
    results, matrices, models = {}, {}, {}

    for name, settings, filename in TREE_SETTINGS:
        model = DecisionTreeClassifier(random_state=RANDOM_STATE, **settings)
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)
        matrices[name] = confusion_matrix(y_test, predictions)
        models[name] = model
        cv = cross_val_score(model, X_train, y_train, cv=5, scoring="accuracy")
        results[name] = {
            "settings": settings,
            "accuracy": round(float(accuracy), 4),
            "train_accuracy": round(float(model.score(X_train, y_train)), 4),
            "roc_auc": round(float(roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])), 4),
            "cv_mean": round(float(cv.mean()), 4),
            "leaves": int(model.get_n_leaves()),
            "depth": int(model.get_depth()),
            "confusion_matrix": matrices[name].tolist(),
        }
        print(f"    {name:<36} test={accuracy:.4f} train={results[name]['train_accuracy']:.4f} "
              f"leaves={results[name]['leaves']}", flush=True)

        # Size the canvas from the leaf count rather than the depth limit, so a
        # wide tree gets the horizontal room its deepest row actually needs and
        # the node boxes never overlap.
        leaves = results[name]["leaves"]
        width = max(14.0, 0.95 * leaves)
        height = 2.1 * results[name]["depth"] + 2.0
        figure, axis = ps.plt.subplots(figsize=(width, height))
        axis.set_facecolor(ps.PAGE_BG)
        plot_tree(
            model, ax=axis, feature_names=feature_labels, class_names=CLASS_NAMES,
            filled=True, rounded=True, impurity=True, proportion=True,
            fontsize=9 if leaves <= 20 else 8,
        )
        axis.set_title(
            f"{name}  -  test accuracy {accuracy:.1%}, {results[name]['leaves']} leaves",
            loc="left", fontsize=14, fontweight="bold", pad=10,
        )
        ps.save(figure, filename)

    figure, axes = ps.plt.subplots(1, 3, figsize=(12.6, 4.4))
    for axis, (name, result) in zip(axes, results.items()):
        plot_confusion(axis, np.array(result["confusion_matrix"]),
                       name.split(" - ")[0], result["accuracy"])
    figure.suptitle("Decision tree confusion matrices on the held-out testing set",
                    fontsize=14, fontweight="bold", x=0.01, ha="left")
    ps.save(figure, "dt-confusion-matrices.png")

    best_name = max(results, key=lambda key: results[key]["accuracy"])
    importances = pd.Series(models[best_name].feature_importances_,
                            index=feature_labels).sort_values()
    importances = importances[importances > 0.001]
    figure, axis = ps.new_axes(9.4, 5.4)
    axis.barh(importances.index, 100 * importances.values, color=ps.TEAL, height=0.68)
    for position, value in enumerate(100 * importances.values):
        axis.text(value + 0.6, position, f"{value:.1f}%", va="center", fontsize=9.5,
                  color=ps.SLATE)
    axis.set_xlim(0, 100 * importances.max() * 1.16)
    ps.finish(figure, axis, "dt-feature-importance.png",
              f"Which features {best_name.split(' - ')[0]} actually splits on",
              "Share of the tree's total impurity reduction (%)", "")

    depths = list(range(1, 21))
    train_curve, test_curve = [], []
    for depth in depths:
        model = DecisionTreeClassifier(criterion="gini", max_depth=depth,
                                       random_state=RANDOM_STATE).fit(X_train, y_train)
        train_curve.append(model.score(X_train, y_train))
        test_curve.append(model.score(X_test, y_test))

    figure, axis = ps.new_axes(9.4, 5.1)
    axis.plot(depths, 100 * np.array(train_curve), marker="o", markersize=5,
              linewidth=2.3, color=ps.ORANGE, label="Training set")
    axis.plot(depths, 100 * np.array(test_curve), marker="s", markersize=5,
              linewidth=2.3, color=ps.TEAL, label="Testing set")
    best_depth = depths[int(np.argmax(test_curve))]
    axis.axvline(best_depth, color=ps.SLATE, linestyle="--", linewidth=1.3)
    axis.text(best_depth + 0.3, 52, f"best test depth = {best_depth}",
              fontsize=10, color=ps.SLATE)
    axis.set_xticks(depths[::2])
    axis.legend(loc="center right")
    ps.finish(figure, axis, "dt-depth-curve.png",
              "Deeper trees memorise the training set without predicting better",
              "Maximum tree depth", "Accuracy (%)")

    return results, {"best_depth": int(best_depth),
                     "deep_train_accuracy": round(float(train_curve[-1]), 4),
                     "deep_test_accuracy": round(float(test_curve[-1]), 4)}


# --------------------------------------------------------------------------


def main() -> None:
    clean = pd.read_csv(DATA_DIR / "cricsheet-matches-clean.csv")
    features, target = build_design_matrix(clean)
    print(f"  labelled matrix {features.shape}", flush=True)

    X_train, X_test, y_train, y_test = train_test_split(
        features, target, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=target
    )
    overlap = len(set(X_train.index) & set(X_test.index))
    assert overlap == 0, "training and testing sets must be disjoint"
    print(f"  train {X_train.shape}  test {X_test.shape}  overlapping rows: {overlap}",
          flush=True)

    train_export = X_train.copy()
    train_export["LABEL"] = y_train.map({1: "Defended", 0: "Chased"})
    train_export.to_csv(DATA_DIR / "supervised-train.csv", index=False)
    test_export = X_test.copy()
    test_export["LABEL"] = y_test.map({1: "Defended", 0: "Chased"})
    test_export.to_csv(DATA_DIR / "supervised-test.csv", index=False)

    figure_labelled_sample(features, target)
    figure_train_test(y_train, y_test)
    figure_class_separation(features, target)

    print("  Naive Bayes", flush=True)
    nb_results = run_naive_bayes(X_train, X_test, y_train, y_test)

    print("  Decision Trees", flush=True)
    impurity = figure_impurity_example(X_train, y_train)
    dt_results, dt_extra = run_decision_trees(X_train, X_test, y_train, y_test)

    majority = float(max(y_test.mean(), 1 - y_test.mean()))
    results = {
        "task": "Predict whether a first-innings total is Defended or Chased",
        "n_matches": int(len(features)),
        "n_features": len(ALL_FEATURES),
        "feature_names": [SHORT[c] for c in ALL_FEATURES],
        "excluded_for_leakage": ["second innings runs, wickets, overs and run rate"],
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "test_size": TEST_SIZE,
        "overlapping_rows": overlap,
        "class_balance": {"Defended": int(target.sum()), "Chased": int((1 - target).sum())},
        "majority_class_baseline": round(majority, 4),
        "naive_bayes": nb_results,
        "decision_trees": dt_results,
        "decision_tree_depth_study": dt_extra,
        "impurity_example": impurity,
        "best_overall": max(
            [(name, result["accuracy"]) for name, result in {**nb_results, **dt_results}.items()],
            key=lambda pair: pair[1],
        ),
    }
    with open(OUTPUT_DIR / "supervised-results.json", "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)

    print(f"\n  majority-class baseline: {majority:.1%}")
    print(f"  best model: {results['best_overall'][0]} at {results['best_overall'][1]:.1%}")


if __name__ == "__main__":
    main()
