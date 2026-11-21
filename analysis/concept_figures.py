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

Run:  python public/analysis/concept_figures.py
"""

from __future__ import annotations

import numpy as np
from scipy.cluster.hierarchy import dendrogram, linkage, set_link_color_palette

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


def main() -> None:
    figure_kmeans_steps()
    figure_hierarchical_and_distance()
    figure_pca_eigenvectors()
    figure_dimensionality()
    figure_impurity_curves()


if __name__ == "__main__":
    main()
