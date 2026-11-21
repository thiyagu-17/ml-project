"""Explanatory diagrams for the Overview sections of the method tabs.

These figures explain how each method works, so they use small synthetic
examples rather than the cricket data. The cricket results live in the
Results sections and are produced by clustering_pca.py and supervised_models.py.

Writes into public/analysis/:
    concept-kmeans-steps.png             how k-means moves its centres
    concept-hierarchical-distance.png    a dendrogram, and Euclidean vs cosine distance
    concept-pca-eigenvectors.png         eigenvectors of a 2-D cloud and projection onto PC1
    concept-dimensionality.png           why distances lose meaning in high dimensions
    concept-impurity-curves.png          Gini and entropy against class proportion
    concept-linear-regression.png        a fitted line and its residuals
    concept-sigmoid.png                  score -> probability -> class, and why not a line
    concept-adaboost-rounds.png          AdaBoost reweighting, round by round
    concept-bagging-boosting.png         bagging against boosting
    concept-adaboost-alpha.png           a stump's alpha against its error

Run:  python public/analysis/concept_figures.py
"""

from __future__ import annotations

import numpy as np
from scipy.cluster.hierarchy import dendrogram, linkage, set_link_color_palette
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier

import plot_style as ps

RNG = np.random.default_rng(7)


def style(axis) -> None:
    axis.grid(alpha=0.16, linewidth=0.8)
    axis.set_axisbelow(True)
    axis.spines[["top", "right"]].set_visible(False)


# --------------------------------------------------------------------------
# Clustering
# --------------------------------------------------------------------------


def figure_kmeans_steps() -> None:
    centres_true = np.array([[1.5, 1.5], [5.0, 2.0], [3.2, 5.0]])
    points = np.vstack([c + RNG.normal(scale=0.65, size=(40, 2)) for c in centres_true])
    centres = np.array([[0.5, 4.8], [1.2, 4.0], [5.8, 5.5]])

    def assign(current):
        distances = ((points[:, None, :] - current[None, :, :]) ** 2).sum(axis=2)
        return distances.argmin(axis=1)

    snapshots = [("1. Choose k = 3 starting centres", centres.copy(), None)]
    labels = assign(centres)
    snapshots.append(("2. Assign each point to its nearest centre", centres.copy(), labels))
    for _ in range(20):
        centres = np.array([points[labels == k].mean(axis=0) for k in range(3)])
        labels = assign(centres)
    snapshots.append(("3. Move centres to the mean and repeat", centres.copy(), labels))

    figure, axes = ps.plt.subplots(1, 3, figsize=(13.2, 4.6), sharex=True, sharey=True)
    for axis, (title, current, current_labels) in zip(axes, snapshots):
        style(axis)
        if current_labels is None:
            axis.scatter(points[:, 0], points[:, 1], s=26, color=ps.SAND, edgecolor="none")
        else:
            for k in range(3):
                mask = current_labels == k
                axis.scatter(points[mask, 0], points[mask, 1], s=26,
                             color=ps.SEQUENCE[k], alpha=0.75, edgecolor="none")
        for k, centre in enumerate(current):
            axis.scatter(*centre, s=330, marker="X", color=ps.SEQUENCE[k],
                         edgecolor=ps.INK, linewidth=1.6, zorder=5)
        axis.set_title(title, fontsize=12, fontweight="bold", loc="left")
        axis.set_xlabel("Feature 1")
    axes[0].set_ylabel("Feature 2")
    figure.suptitle("How k-means clustering works (partitional)", fontsize=14,
                    fontweight="bold", x=0.01, ha="left")
    ps.save(figure, "concept-kmeans-steps.png")


def figure_hierarchical_and_distance() -> None:
    figure, axes = ps.plt.subplots(1, 2, figsize=(13.0, 5.0),
                                   gridspec_kw={"width_ratios": [1.25, 1]})

    # Left: a dendrogram for ten labelled points.
    points = np.vstack([RNG.normal(loc, 0.45, size=(n, 2))
                        for loc, n in [((0, 0), 4), ((4, 0.5), 3), ((2, 4), 3)]])
    tree = linkage(points, method="average")
    axis = axes[0]
    style(axis)
    set_link_color_palette([ps.TEAL, ps.ORANGE, ps.PLUM])
    cut = (tree[-2, 2] + tree[-3, 2]) / 2
    dendrogram(tree, ax=axis, labels=[f"P{i + 1}" for i in range(len(points))],
               color_threshold=cut, above_threshold_color=ps.SLATE)
    set_link_color_palette(None)
    axis.axhline(cut, color=ps.INK, linestyle="--", linewidth=1.3)
    axis.text(axis.get_xlim()[1] * 0.98, cut * 1.05, "cut here: 3 clusters",
              ha="right", fontsize=10)
    axis.set_title("Hierarchical: merge the closest groups, then cut the tree",
                   fontsize=12, fontweight="bold", loc="left")
    axis.set_ylabel("Distance at which groups merge")
    axis.tick_params(axis="x", labelsize=10)

    # Right: Euclidean distance against cosine distance for two vectors.
    axis = axes[1]
    style(axis)
    a, b = np.array([1.2, 3.6]), np.array([4.6, 2.2])
    for vector, name, colour in [(a, "A", ps.TEAL), (b, "B", ps.ORANGE)]:
        axis.annotate("", xy=vector, xytext=(0, 0),
                      arrowprops={"arrowstyle": "-|>", "color": colour, "linewidth": 2.6})
        axis.text(*(vector * 1.06), name, fontsize=13, fontweight="bold", color=colour)
    axis.plot([a[0], b[0]], [a[1], b[1]], ":", color=ps.INK, linewidth=2)
    euclid = np.linalg.norm(a - b)
    axis.text((a[0] + b[0]) / 2 + 0.15, (a[1] + b[1]) / 2 + 0.25,
              f"Euclidean distance\n= straight line = {euclid:.2f}", fontsize=10)
    angle_a, angle_b = np.arctan2(a[1], a[0]), np.arctan2(b[1], b[0])
    arc = np.linspace(angle_b, angle_a, 40)
    axis.plot(1.3 * np.cos(arc), 1.3 * np.sin(arc), color=ps.PLUM, linewidth=2)
    cosine = 1 - a @ b / (np.linalg.norm(a) * np.linalg.norm(b))
    axis.text(1.45, 0.55, f"angle θ\ncosine distance\n= 1 − cos θ = {cosine:.2f}",
              fontsize=10, color=ps.PLUM)
    axis.set_xlim(-0.2, 5.6)
    axis.set_ylim(-0.2, 4.4)
    axis.set_aspect("equal")
    axis.set_title("Two ways to measure 'close'", fontsize=12, fontweight="bold", loc="left")
    axis.set_xlabel("Feature 1")
    axis.set_ylabel("Feature 2")
    ps.save(figure, "concept-hierarchical-distance.png")


# --------------------------------------------------------------------------
# PCA
# --------------------------------------------------------------------------


def figure_pca_eigenvectors() -> None:
    covariance = np.array([[3.0, 2.2], [2.2, 2.4]])
    data = RNG.multivariate_normal([0, 0], covariance, size=260)
    # Standardise, exactly as the cricket features are before PCA, so the
    # eigenvalues sum to the number of columns (2 here).
    data = (data - data.mean(axis=0)) / data.std(axis=0, ddof=1)
    values, vectors = np.linalg.eigh(np.cov(data.T))
    order = np.argsort(values)[::-1]
    values, vectors = values[order], vectors[:, order]
    # Point PC1 up and to the right and PC2 up and to the left, for readability.
    vectors[:, 0] *= np.sign(vectors[0, 0]) or 1
    vectors[:, 1] *= np.sign(vectors[1, 1]) or 1

    figure, axes = ps.plt.subplots(1, 2, figsize=(13.0, 5.3), sharex=True, sharey=True)
    axis = axes[0]
    style(axis)
    axis.scatter(data[:, 0], data[:, 1], s=14, color=ps.SAND, alpha=0.8, edgecolor="none")
    for index, colour in enumerate([ps.TEAL, ps.ORANGE]):
        tip = vectors[:, index] * 2 * np.sqrt(values[index])
        axis.annotate("", xy=tip, xytext=(0, 0),
                      arrowprops={"arrowstyle": "-|>", "color": colour, "linewidth": 3})
        label_at = tip + vectors[:, index] * 0.75
        axis.text(*label_at, f"PC{index + 1}\nλ = {values[index]:.2f}",
                  color=colour, fontsize=11, fontweight="bold", ha="center", va="center",
                  bbox={"facecolor": ps.PAGE_BG, "edgecolor": "none", "alpha": 0.85, "pad": 1.5})
    axis.set_title("Eigenvectors give the directions, eigenvalues the spread",
                   fontsize=12, fontweight="bold", loc="left")
    axis.set_xlabel("Feature 1 (standardised)")
    axis.set_ylabel("Feature 2 (standardised)")

    axis = axes[1]
    style(axis)
    pc1 = vectors[:, 0]
    projected = np.outer(data @ pc1, pc1)
    for point, image in zip(data[::4], projected[::4]):
        axis.plot([point[0], image[0]], [point[1], image[1]], color=ps.SLATE,
                  linewidth=0.6, alpha=0.5)
    axis.scatter(data[:, 0], data[:, 1], s=12, color=ps.SAND, alpha=0.55, edgecolor="none")
    axis.scatter(projected[:, 0], projected[:, 1], s=12, color=ps.TEAL, edgecolor="none")
    share = values[0] / values.sum()
    axis.set_title(f"Keeping only PC1: 2 columns become 1, {share:.0%} of variance kept",
                   fontsize=12, fontweight="bold", loc="left")
    axis.set_xlabel("Feature 1 (standardised)")
    for axis in axes:
        axis.set_aspect("equal")
    ps.save(figure, "concept-pca-eigenvectors.png")


def figure_dimensionality() -> None:
    dimensions = [1, 2, 3, 5, 10, 20, 50, 100, 200, 500, 1000]
    contrast = []
    for dimension in dimensions:
        ratios = []
        for _ in range(20):
            points = RNG.uniform(size=(300, dimension))
            distances = np.linalg.norm(points[1:] - points[0], axis=1)
            ratios.append((distances.max() - distances.min()) / distances.min())
        contrast.append(np.median(ratios))

    figure, axis = ps.new_axes(9.4, 5.0)
    axis.plot(dimensions, contrast, marker="o", markersize=7, linewidth=2.4, color=ps.TEAL)
    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.annotate("in 2-D the farthest point is many\ntimes farther away than the nearest",
                  xy=(2, contrast[1]), xytext=(4, contrast[1] * 1.2), fontsize=10,
                  arrowprops={"arrowstyle": "-|>", "color": ps.SLATE})
    axis.annotate("in 1,000-D nearest and farthest\nare almost the same distance",
                  xy=(1000, contrast[-1]), xytext=(60, contrast[-1] * 12), fontsize=10,
                  arrowprops={"arrowstyle": "-|>", "color": ps.SLATE})
    ps.finish(figure, axis, "concept-dimensionality.png",
              "Why high-dimensional data is hard: distances stop discriminating",
              "Number of dimensions (log scale)",
              "(farthest − nearest) / nearest distance")


# --------------------------------------------------------------------------
# Decision trees
# --------------------------------------------------------------------------


def figure_impurity_curves() -> None:
    p = np.linspace(0.001, 0.999, 400)
    gini = 1 - p ** 2 - (1 - p) ** 2
    entropy = -(p * np.log2(p) + (1 - p) * np.log2(1 - p))

    figure, axis = ps.new_axes(9.2, 5.0)
    axis.plot(p, entropy, linewidth=2.6, color=ps.ORANGE, label="Entropy (max 1.0)")
    axis.plot(p, gini, linewidth=2.6, color=ps.TEAL, label="Gini impurity (max 0.5)")
    axis.axvline(0.5, color=ps.SLATE, linestyle="--", linewidth=1.2)
    axis.text(0.51, 0.06, "50/50 node:\nmost impure", fontsize=10, color=ps.SLATE)
    axis.text(0.02, 0.06, "pure node", fontsize=10, color=ps.SLATE)
    axis.text(0.98, 0.06, "pure node", fontsize=10, color=ps.SLATE, ha="right")
    axis.set_ylim(0, 1.08)
    axis.legend(loc="upper right")
    ps.finish(figure, axis, "concept-impurity-curves.png",
              "Both impurity measures peak when a node is evenly mixed",
              "Share of the node in one class (p)", "Impurity")


# --------------------------------------------------------------------------
# Regression
# --------------------------------------------------------------------------


def figure_linear_regression() -> None:
    x = RNG.uniform(20, 70, 60)
    y = 60 + 2.0 * x + RNG.normal(0, 18, 60)
    slope, intercept = np.polyfit(x, y, 1)
    fitted = intercept + slope * x

    figure, axis = ps.new_axes(9.2, 5.4)
    for xi, yi, fi in zip(x, y, fitted):
        axis.plot([xi, xi], [yi, fi], color=ps.ORANGE, linewidth=1, alpha=0.7)
    axis.scatter(x, y, s=30, color=ps.SLATE, zorder=3, label="Observed values")
    grid = np.linspace(15, 75, 2)
    axis.plot(grid, intercept + slope * grid, color=ps.TEAL, linewidth=3,
              label=f"Fitted line: y = {intercept:.0f} + {slope:.2f} x")
    axis.plot([], [], color=ps.ORANGE, linewidth=1.5, label="Residuals (errors) the line minimises")
    axis.annotate(f"slope = {slope:.2f}:\neach extra unit of x adds\n{slope:.2f} units of y",
                  xy=(60, intercept + slope * 60), xytext=(28, intercept + slope * 72),
                  fontsize=10, arrowprops={"arrowstyle": "-|>", "color": ps.SLATE})
    axis.legend(loc="lower right")
    ps.finish(figure, axis, "concept-linear-regression.png",
              "Linear regression: the straight line with the smallest squared errors",
              "Input x (for example, powerplay runs)", "Numeric target y (for example, final total)")


def figure_sigmoid() -> None:
    figure, axes = ps.plt.subplots(1, 2, figsize=(13.0, 5.0))
    for axis in axes:
        style(axis)

    # Left: score -> probability -> class.
    axis = axes[0]
    z = np.linspace(-7, 7, 300)
    probability = 1 / (1 + np.exp(-z))
    axis.axvspan(-7, 0, color=ps.ORANGE, alpha=0.10)
    axis.axvspan(0, 7, color=ps.TEAL, alpha=0.10)
    axis.plot(z, probability, color=ps.INK, linewidth=2.8)
    axis.axhline(0.5, color=ps.SLATE, linestyle="--", linewidth=1.2)
    axis.text(-6.7, 0.53, "threshold 0.5", fontsize=10, color=ps.SLATE)
    axis.text(-3.6, 0.88, "predict class 0", fontsize=11, color=ps.ORANGE, fontweight="bold")
    axis.text(1.0, 0.1, "predict class 1", fontsize=11, color=ps.TEAL, fontweight="bold")
    axis.annotate("score z = 2  →  p = 0.88", xy=(2, 1 / (1 + np.exp(-2))), xytext=(2.4, 0.62),
                  fontsize=10, arrowprops={"arrowstyle": "-|>", "color": ps.SLATE})
    axis.set_title("Sigmoid: p = 1 / (1 + e^(−z)) squeezes any score into 0–1",
                   fontsize=12, fontweight="bold", loc="left")
    axis.set_xlabel("Linear score z = b0 + b1·x1 + b2·x2 + …")
    axis.set_ylabel("Probability of class 1")

    # Right: a straight line against the S-curve on yes/no data.
    axis = axes[1]
    x = np.sort(RNG.uniform(3, 9, 120))
    truth = 1 / (1 + np.exp(-(x - 6) * 1.6))
    y = (RNG.uniform(size=x.size) < truth).astype(int)
    jitter = y + RNG.uniform(-0.03, 0.03, y.size)
    axis.scatter(x, jitter, s=18, color=ps.SAND, edgecolor="none", label="Observed outcome (0 or 1)")
    slope, intercept = np.polyfit(x, y, 1)
    grid = np.linspace(2.5, 9.5, 200)
    axis.plot(grid, intercept + slope * grid, color=ps.ORANGE, linewidth=2.4,
              label="Linear regression: escapes 0–1")
    logistic = LogisticRegression().fit(x.reshape(-1, 1), y)
    axis.plot(grid, logistic.predict_proba(grid.reshape(-1, 1))[:, 1], color=ps.TEAL, linewidth=2.8,
              label="Logistic regression: stays a probability")
    axis.axhline(0, color=ps.SLATE, linewidth=0.8)
    axis.axhline(1, color=ps.SLATE, linewidth=0.8)
    axis.legend(loc="upper left", fontsize=9.5)
    axis.set_title("Why a yes/no target needs the S-curve", fontsize=12, fontweight="bold", loc="left")
    axis.set_xlabel("Input x (for example, run rate)")
    axis.set_ylabel("Outcome / predicted probability")
    ps.save(figure, "concept-sigmoid.png")


# --------------------------------------------------------------------------
# AdaBoost
# --------------------------------------------------------------------------


def figure_adaboost_rounds() -> None:
    """Textbook AdaBoost with stumps, drawn round by round on a toy dataset."""
    n = 60
    points = RNG.uniform(0, 10, size=(n, 2))
    labels = np.where((points[:, 0] > 4) & (points[:, 1] > 3) | (points[:, 1] > 8), 1, -1)
    flip = RNG.choice(n, 4, replace=False)
    labels[flip] *= -1

    weights = np.full(n, 1 / n)
    stumps, alphas = [], []
    figure, axes = ps.plt.subplots(1, 4, figsize=(16.5, 4.6), sharex=True, sharey=True)
    for round_index in range(3):
        stump = DecisionTreeClassifier(max_depth=1).fit(points, labels, sample_weight=weights)
        wrong = stump.predict(points) != labels
        error = weights[wrong].sum()
        alpha = 0.5 * np.log((1 - error) / error)
        axis = axes[round_index]
        style(axis)
        sizes = 2400 * weights
        for value, colour in [(1, ps.TEAL), (-1, ps.ORANGE)]:
            mask = labels == value
            axis.scatter(points[mask, 0], points[mask, 1], s=sizes[mask], color=colour,
                         edgecolor=ps.INK, linewidth=0.5, alpha=0.85)
        axis.scatter(points[wrong, 0], points[wrong, 1], s=sizes[wrong] * 1.9, facecolor="none",
                     edgecolor=ps.INK, linewidth=1.4)
        feature, threshold = stump.tree_.feature[0], stump.tree_.threshold[0]
        if feature == 0:
            axis.axvline(threshold, color=ps.INK, linewidth=2.4)
        else:
            axis.axhline(threshold, color=ps.INK, linewidth=2.4)
        axis.set_title(f"Round {round_index + 1}: error {error:.2f}, alpha {alpha:.2f}",
                       fontsize=11.5, fontweight="bold", loc="left")
        stumps.append(stump)
        alphas.append(alpha)
        weights = weights * np.exp(np.where(wrong, alpha, -alpha))
        weights /= weights.sum()

    # Final weighted vote of many rounds, shown as a decision surface.
    weights = np.full(n, 1 / n)
    ensemble = []
    for _ in range(25):
        stump = DecisionTreeClassifier(max_depth=1).fit(points, labels, sample_weight=weights)
        wrong = stump.predict(points) != labels
        error = max(weights[wrong].sum(), 1e-6)
        alpha = 0.5 * np.log((1 - error) / error)
        ensemble.append((alpha, stump))
        weights = weights * np.exp(np.where(wrong, alpha, -alpha))
        weights /= weights.sum()
    grid_x, grid_y = np.meshgrid(np.linspace(0, 10, 200), np.linspace(0, 10, 200))
    grid = np.column_stack([grid_x.ravel(), grid_y.ravel()])
    vote = sum(alpha * stump.predict(grid) for alpha, stump in ensemble).reshape(grid_x.shape)
    axis = axes[3]
    style(axis)
    axis.contourf(grid_x, grid_y, np.sign(vote), levels=[-2, 0, 2],
                  colors=[ps.ORANGE, ps.TEAL], alpha=0.18)
    for value, colour in [(1, ps.TEAL), (-1, ps.ORANGE)]:
        mask = labels == value
        axis.scatter(points[mask, 0], points[mask, 1], s=40, color=colour,
                     edgecolor=ps.INK, linewidth=0.5)
    axis.set_title("Final: weighted vote of 25 stumps", fontsize=11.5, fontweight="bold", loc="left")
    for axis in axes:
        axis.set_xlabel("Feature 1")
    axes[0].set_ylabel("Feature 2")
    figure.suptitle("AdaBoost round by round: point size = weight, ringed points = misclassified",
                    fontsize=14, fontweight="bold", x=0.01, ha="left")
    ps.save(figure, "concept-adaboost-rounds.png")


def _box(axis, x, y, text, colour, width=1.9, height=0.8):
    axis.add_patch(ps.plt.Rectangle((x - width / 2, y - height / 2), width, height,
                                    facecolor=colour, edgecolor="none", alpha=0.9))
    axis.text(x, y, text, ha="center", va="center", fontsize=10, color="white", fontweight="bold")


def _arrow(axis, start, end, text=""):
    axis.annotate("", xy=end, xytext=start,
                  arrowprops={"arrowstyle": "-|>", "color": ps.SLATE, "linewidth": 1.6})
    if text:
        axis.text((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 + 0.28, text,
                  ha="center", fontsize=9, color=ps.SLATE)


def figure_bagging_vs_boosting() -> None:
    figure, axes = ps.plt.subplots(1, 2, figsize=(14.0, 5.0))
    for axis in axes:
        axis.axis("off")
        axis.set_xlim(0, 10)
        axis.set_ylim(0, 7)

    axis = axes[0]
    axis.set_title("Bagging: independent trees, built side by side", fontsize=12.5,
                   fontweight="bold", loc="left")
    _box(axis, 5, 6.2, "Training data", ps.SLATE, width=3)
    for i, x in enumerate([1.6, 5, 8.4]):
        _arrow(axis, (5, 5.75), (x, 4.75))
        _box(axis, x, 4.3, f"Random sample {i + 1}", ps.SAND, width=2.6)
        _arrow(axis, (x, 3.85), (x, 2.95))
        _box(axis, x, 2.5, f"Full tree {i + 1}", ps.TEAL, width=2.6)
        _arrow(axis, (x, 2.05), (5, 1.05))
    _box(axis, 5, 0.6, "Equal vote", ps.INK, width=3)

    axis = axes[1]
    axis.set_title("Boosting: each stump fixes the last one's mistakes", fontsize=12.5,
                   fontweight="bold", loc="left")
    xs = [1.3, 3.8, 6.3, 8.8]
    for i, x in enumerate(xs):
        label = "…" if i == 3 else f"Stump {i + 1}"
        _box(axis, x, 4.3, label, ps.TEAL if i < 3 else ps.SLATE, width=1.9)
        _box(axis, x, 6.0, "Equal weights" if i == 0 else "Reweighted data", ps.SAND, width=2.2)
        _arrow(axis, (x, 5.6), (x, 4.75))
        if i < 3:
            _arrow(axis, (x + 0.95, 4.3), (xs[i + 1] - 0.95, 5.8), "up-weight errors")
            _arrow(axis, (x, 3.85), (5.0, 1.05))
        axis.text(x, 3.45, f"alpha {i + 1}" if i < 3 else "", ha="center", fontsize=9.5,
                  color=ps.INK)
    _box(axis, 5, 0.6, "Vote weighted by alpha", ps.INK, width=3.6)
    ps.save(figure, "concept-bagging-boosting.png")


def figure_alpha() -> None:
    error = np.linspace(0.01, 0.99, 400)
    alpha = 0.5 * np.log((1 - error) / error)
    figure, axis = ps.new_axes(9.2, 5.0)
    axis.plot(error, alpha, color=ps.TEAL, linewidth=2.8)
    axis.axhline(0, color=ps.SLATE, linewidth=1)
    axis.axvline(0.5, color=ps.SLATE, linestyle="--", linewidth=1.2)
    axis.text(0.52, 1.6, "error 0.5 = coin flip:\nalpha 0, the stump gets no say",
              fontsize=10, color=ps.SLATE)
    axis.annotate("accurate stump:\nlarge say in the vote", xy=(0.1, 0.5 * np.log(9)),
                  xytext=(0.17, 1.9), fontsize=10,
                  arrowprops={"arrowstyle": "-|>", "color": ps.SLATE})
    axis.set_ylim(-2.4, 2.4)
    ps.finish(figure, axis, "concept-adaboost-alpha.png",
              "A stump's weight in the vote: alpha = ½ · ln((1 − error) / error)",
              "Weighted error of the stump", "alpha")


def main() -> None:
    figure_kmeans_steps()
    figure_hierarchical_and_distance()
    figure_pca_eigenvectors()
    figure_dimensionality()
    figure_impurity_curves()
    figure_linear_regression()
    figure_sigmoid()
    figure_adaboost_rounds()
    figure_bagging_vs_boosting()
    figure_alpha()


if __name__ == "__main__":
    main()
