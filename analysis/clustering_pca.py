"""Clustering, PCA and SVD for the Clustering and PCA tabs.

Clustering and PCA are unsupervised, so the result label is removed before
anything is fitted. Every feature is standardised first: the raw columns mix
run totals in the hundreds with ratios between zero and one, and without
scaling the distance and variance calculations would simply measure whichever
column happens to have the widest range.

Reads  public/data/cricsheet-matches-clean.csv
Writes the clustering and PCA figures plus clustering-pca-results.json

Run:  python public/analysis/clustering_pca.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage, set_link_color_palette
from scipy.spatial.distance import pdist
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, silhouette_samples, silhouette_score
from sklearn.preprocessing import StandardScaler

import plot_style as ps

PUBLIC_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PUBLIC_DIR / "data"
OUTPUT_DIR = PUBLIC_DIR / "analysis"

RANDOM_STATE = 42
K_VALUES = [2, 3, 4, 5, 6, 7, 8]
HEADLINE_K = [2, 3, 4]
HIERARCHICAL_SAMPLE = 1000
DENDROGRAM_SAMPLE = 250

FEATURES = [
    "first_innings_runs", "first_innings_wickets", "first_innings_overs",
    "first_innings_run_rate", "powerplay_runs", "powerplay_run_rate",
    "boundary_share", "dot_ball_share", "extras_share",
    "second_innings_runs", "second_innings_run_rate",
]

SHORT = {
    "first_innings_runs": "1st runs",
    "first_innings_wickets": "1st wickets",
    "first_innings_overs": "1st overs",
    "first_innings_run_rate": "1st run rate",
    "powerplay_runs": "PP runs",
    "powerplay_run_rate": "PP run rate",
    "boundary_share": "Boundary %",
    "dot_ball_share": "Dot ball %",
    "extras_share": "Extras %",
    "second_innings_runs": "2nd runs",
    "second_innings_run_rate": "2nd run rate",
}


# --------------------------------------------------------------------------


def build_matrix(clean: pd.DataFrame) -> tuple[np.ndarray, pd.DataFrame]:
    """Return the standardised, unlabelled feature matrix."""
    features = clean[FEATURES].copy()
    scaled = StandardScaler().fit_transform(features.to_numpy(dtype=float))
    return scaled, features


def stratified_sample(clean: pd.DataFrame, size: int) -> np.ndarray:
    """Row positions of a format-balanced sample, for the costly O(n^2) steps."""
    rng = np.random.default_rng(RANDOM_STATE)
    positions = []
    for fmt in clean["match_type"].unique():
        pool = np.flatnonzero((clean["match_type"] == fmt).to_numpy())
        share = max(1, round(size * len(pool) / len(clean)))
        positions.append(rng.choice(pool, size=min(share, len(pool)), replace=False))
    return np.sort(np.concatenate(positions))


# --------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------


def figure_silhouette_curve(kmeans_scores, hierarchical_scores, best_k) -> None:
    figure, axis = ps.new_axes(9.3, 5.1)
    ks = [row["k"] for row in kmeans_scores]
    axis.plot(ks, [row["silhouette"] for row in kmeans_scores], marker="o", markersize=8,
              linewidth=2.4, color=ps.TEAL, label="k-means (Euclidean, all matches)")
    axis.plot([row["k"] for row in hierarchical_scores],
              [row["silhouette"] for row in hierarchical_scores], marker="s", markersize=7,
              linewidth=2.4, color=ps.ORANGE,
              label=f"Average linkage (cosine, {HIERARCHICAL_SAMPLE:,}-match sample)")
    axis.axvline(best_k, color=ps.SLATE, linestyle="--", linewidth=1.3)
    axis.text(best_k + 0.1, axis.get_ylim()[1] * 0.96, f"best k = {best_k}",
              fontsize=10, color=ps.SLATE, va="top")
    axis.set_xticks(ks)
    axis.legend(loc="upper right")
    ps.finish(figure, axis, "silhouette-comparison.png",
              "Both methods score highest at the same number of clusters",
              "Number of clusters (k)", "Mean silhouette score")


def figure_silhouette_profile(scaled, labels, k, score) -> None:
    """Per-match silhouette widths, grouped by cluster."""
    sample = stratified_sample_positions = np.random.default_rng(RANDOM_STATE).choice(
        len(scaled), size=min(2500, len(scaled)), replace=False)
    values = silhouette_samples(scaled[sample], labels[sample])
    sampled_labels = labels[sample]

    figure, axis = ps.new_axes(9.0, 5.4)
    axis.grid(alpha=0.16, axis="x")
    lower = 5
    for cluster in range(k):
        cluster_values = np.sort(values[sampled_labels == cluster])
        upper = lower + len(cluster_values)
        axis.fill_betweenx(np.arange(lower, upper), 0, cluster_values,
                           color=ps.SEQUENCE[cluster % len(ps.SEQUENCE)], alpha=0.85)
        axis.text(-0.055, lower + len(cluster_values) / 2, f"Cluster {cluster}",
                  va="center", ha="right", fontsize=10)
        lower = upper + 12
    axis.axvline(score, color=ps.INK, linestyle="--", linewidth=1.4)
    axis.text(score + 0.012, lower * 0.97, f"mean = {score:.3f}", fontsize=10, color=ps.INK)
    axis.set_yticks([])
    axis.set_xlim(-0.16, 1.0)
    ps.finish(figure, axis, "silhouette-profile.png",
              f"Silhouette width of individual matches at k = {k}",
              "Silhouette width", "")


def figure_cluster_scatter(coordinates, labels, variance, k) -> None:
    figure, axis = ps.new_axes(9.3, 5.6)
    for cluster in range(k):
        mask = labels == cluster
        axis.scatter(coordinates[mask, 0], coordinates[mask, 1], s=11, alpha=0.4,
                     color=ps.SEQUENCE[cluster % len(ps.SEQUENCE)], edgecolor="none",
                     label=f"Cluster {cluster} (n={int(mask.sum()):,})")
        centre = coordinates[mask, :2].mean(axis=0)
        axis.scatter(*centre, s=320, marker="X", edgecolor=ps.INK, linewidth=1.5,
                     color=ps.SEQUENCE[cluster % len(ps.SEQUENCE)], zorder=5)
    legend = axis.legend(loc="upper right", markerscale=2.4)
    for handle in legend.legend_handles:
        handle.set_alpha(1)
    ps.finish(figure, axis, "cluster-map.png",
              f"k-means groups shown on the first two principal components (k = {k})",
              f"PC1 ({variance[0]:.1%} of variance)", f"PC2 ({variance[1]:.1%} of variance)")


def figure_cluster_profiles(features, labels, k) -> None:
    """Mean standardised value of every feature within each cluster."""
    frame = features.copy()
    frame["cluster"] = labels
    standardised = (frame[FEATURES] - frame[FEATURES].mean()) / frame[FEATURES].std()
    standardised["cluster"] = labels
    profile = standardised.groupby("cluster")[FEATURES].mean()

    figure, axis = ps.new_axes(10.2, 1.5 + 0.62 * k)
    axis.grid(False)
    limit = float(np.abs(profile.values).max())
    image = axis.imshow(profile.values, cmap="BrBG", vmin=-limit, vmax=limit, aspect="auto")
    axis.set_xticks(range(len(FEATURES)), [SHORT[f] for f in FEATURES],
                    rotation=35, ha="right", fontsize=9.5)
    axis.set_yticks(range(k), [f"Cluster {c}\n(n={int((labels == c).sum()):,})" for c in range(k)],
                    fontsize=9.5)
    for row in range(k):
        for column in range(len(FEATURES)):
            value = profile.values[row, column]
            axis.text(column, row, f"{value:+.1f}", ha="center", va="center", fontsize=8.5,
                      color="white" if abs(value) > limit * 0.55 else ps.INK)
    bar = figure.colorbar(image, ax=axis, shrink=0.85, pad=0.02)
    bar.set_label("Standard deviations from the overall mean", fontsize=9.5)
    axis.spines[["left", "bottom"]].set_visible(False)
    ps.finish(figure, axis, "cluster-profiles.png",
              "What separates the clusters, feature by feature", "", "")


def figure_cluster_composition(clean, labels, k) -> None:
    frame = clean.assign(cluster=labels)
    figure, axes = ps.plt.subplots(1, 2, figsize=(11.5, 4.7))
    for axis in axes:
        axis.grid(alpha=0.16, axis="y")
        axis.set_axisbelow(True)
        axis.spines[["top", "right"]].set_visible(False)

    formats = frame.groupby("cluster")["match_type"].value_counts(normalize=True).unstack().fillna(0)
    bottom = np.zeros(k)
    for fmt in ["ODI", "T20"]:
        if fmt not in formats:
            continue
        axes[0].bar(formats.index, 100 * formats[fmt], bottom=bottom,
                    color=ps.FORMAT_COLOURS[fmt], label=fmt, width=0.62)
        bottom += 100 * formats[fmt].values
    axes[0].set(title="Format mix inside each cluster", xlabel="Cluster",
                ylabel="Share of cluster (%)")
    axes[0].set_xticks(range(k))
    axes[0].legend(ncols=2, loc="lower center", bbox_to_anchor=(0.5, -0.3))

    results = frame.groupby("cluster")["result_label"].value_counts(normalize=True).unstack().fillna(0)
    bottom = np.zeros(k)
    for label in ["Defended", "Chased"]:
        if label not in results:
            continue
        axes[1].bar(results.index, 100 * results[label], bottom=bottom,
                    color=ps.RESULT_COLOURS[label], label=label, width=0.62)
        bottom += 100 * results[label].values
    axes[1].axhline(50, color=ps.INK, linestyle="--", linewidth=1.2)
    axes[1].set(title="Match outcome inside each cluster (not used when fitting)",
                xlabel="Cluster", ylabel="Share of cluster (%)")
    axes[1].set_xticks(range(k))
    axes[1].legend(ncols=2, loc="lower center", bbox_to_anchor=(0.5, -0.3))

    for axis in axes:
        axis.title.set_fontweight("bold")
        axis.title.set_fontsize(12.5)
    ps.save(figure, "cluster-composition.png")


def figure_dendrogram(sample_matrix, sample_frame, cut_k) -> None:
    distances = pdist(sample_matrix, metric="cosine")
    tree = linkage(distances, method="average")
    threshold = tree[-(cut_k - 1), 2]

    figure, axis = ps.new_axes(11.0, 5.6)
    axis.grid(alpha=0.16, axis="y")
    set_link_color_palette(list(ps.SEQUENCE))
    dendrogram(
        tree, ax=axis, color_threshold=threshold, above_threshold_color=ps.SLATE,
        no_labels=True, truncate_mode=None,
    )
    set_link_color_palette(None)
    axis.axhline(threshold, color=ps.INK, linestyle="--", linewidth=1.4)
    axis.text(axis.get_xlim()[1] * 0.99, threshold * 1.06,
              f"cut for k = {cut_k}", ha="right", fontsize=10, color=ps.INK)
    axis.set_xticks([])
    ps.finish(figure, axis, "dendrogram.png",
              f"Average-linkage dendrogram on cosine distance ({len(sample_frame):,} matches)",
              "Individual matches, ordered by the merge sequence", "Cosine distance")
    return tree


def figure_scree(explained, cumulative) -> None:
    shown = min(len(explained), 11)
    figure, axis = ps.new_axes(9.4, 5.2)
    components = np.arange(1, shown + 1)
    axis.bar(components, 100 * explained[:shown], color=ps.TEAL, width=0.62,
             label="Variance explained by this component")
    twin = axis.twinx()
    twin.plot(components, 100 * cumulative[:shown], color=ps.ORANGE, marker="o",
              markersize=7, linewidth=2.4, label="Running total")
    twin.axhline(90, color=ps.SLATE, linestyle=":", linewidth=1.3)
    twin.text(shown - 0.1, 91.8, "90% of total variance (right axis)", ha="right",
              fontsize=9.5, color=ps.SLATE,
              bbox={"facecolor": ps.PAGE_BG, "edgecolor": "none", "pad": 1.6})
    twin.set_ylim(0, 105)
    twin.set_ylabel("Cumulative variance explained (%)")
    twin.spines[["top"]].set_visible(False)
    twin.grid(False)
    for component, value in zip(components, 100 * explained[:shown]):
        axis.text(component, value + 0.7, f"{value:.1f}", ha="center", fontsize=8.5,
                  color=ps.SLATE)
    axis.set_xticks(components)
    handles = axis.get_legend_handles_labels()[0] + twin.get_legend_handles_labels()[0]
    labels = axis.get_legend_handles_labels()[1] + twin.get_legend_handles_labels()[1]
    axis.legend(handles, labels, loc="center right")
    ps.finish(figure, axis, "pca-scree.png",
              "No single component dominates once the features are standardised",
              "Principal component", "Variance explained (%)")


def figure_biplot(coordinates, loadings, explained, labels, k) -> None:
    figure, axis = ps.new_axes(9.6, 6.2)
    for cluster in range(k):
        mask = labels == cluster
        axis.scatter(coordinates[mask, 0], coordinates[mask, 1], s=8, alpha=0.2,
                     color=ps.SEQUENCE[cluster % len(ps.SEQUENCE)], edgecolor="none")

    scale = 0.86 * np.abs(coordinates[:, :2]).max()
    # Label positions are nudged outward along each arrow so the text never
    # sits on top of the arrow head or on another label.
    for index, feature in enumerate(FEATURES):
        x, y = loadings[0, index] * scale, loadings[1, index] * scale
        axis.annotate("", xy=(x, y), xytext=(0, 0),
                      arrowprops={"arrowstyle": "-|>", "color": ps.INK,
                                  "linewidth": 1.5, "alpha": 0.85})
        axis.text(x * 1.13, y * 1.13, SHORT[feature], fontsize=9.5, color=ps.INK,
                  ha="center", va="center", fontweight="bold",
                  bbox={"facecolor": ps.PAGE_BG, "edgecolor": "none", "alpha": 0.8, "pad": 1.4})
    axis.axhline(0, color=ps.SLATE, linewidth=0.9, alpha=0.6)
    axis.axvline(0, color=ps.SLATE, linewidth=0.9, alpha=0.6)
    ps.finish(figure, axis, "pca-biplot.png",
              "Biplot: matches as points, original features as arrows",
              f"PC1 ({explained[0]:.1%} of variance)", f"PC2 ({explained[1]:.1%} of variance)")


def figure_loadings(loadings) -> None:
    shown = 4
    figure, axis = ps.new_axes(10.0, 4.4)
    axis.grid(False)
    limit = float(np.abs(loadings[:shown]).max())
    image = axis.imshow(loadings[:shown], cmap="PuOr", vmin=-limit, vmax=limit, aspect="auto")
    axis.set_xticks(range(len(FEATURES)), [SHORT[f] for f in FEATURES],
                    rotation=35, ha="right", fontsize=9.5)
    axis.set_yticks(range(shown), [f"PC{i + 1}" for i in range(shown)], fontsize=10.5)
    for row in range(shown):
        for column in range(len(FEATURES)):
            value = loadings[row, column]
            axis.text(column, row, f"{value:+.2f}", ha="center", va="center", fontsize=8.5,
                      color="white" if abs(value) > limit * 0.6 else ps.INK)
    bar = figure.colorbar(image, ax=axis, shrink=0.85, pad=0.02)
    bar.set_label("Loading", fontsize=9.5)
    axis.spines[["left", "bottom"]].set_visible(False)
    ps.finish(figure, axis, "pca-loadings.png",
              "How each original feature contributes to the first four components", "", "")


def figure_svd(singular_values, eigenvalues) -> None:
    shown = min(len(singular_values), 11)
    figure, axes = ps.plt.subplots(1, 2, figsize=(11.5, 4.7))
    for axis in axes:
        axis.grid(alpha=0.16, axis="y")
        axis.set_axisbelow(True)
        axis.spines[["top", "right"]].set_visible(False)

    components = np.arange(1, shown + 1)
    axes[0].bar(components, singular_values[:shown], color=ps.PLUM, width=0.62)
    axes[0].set(title="Singular values of the centred matrix",
                xlabel="Component", ylabel="Singular value")
    axes[0].set_xticks(components)

    axes[1].plot(components, eigenvalues[:shown], marker="o", markersize=7,
                 linewidth=2.3, color=ps.TEAL)
    axes[1].axhline(1.0, color=ps.ORANGE, linestyle="--", linewidth=1.4)
    axes[1].text(shown - 0.1, 1.08, "Kaiser rule: eigenvalue = 1", ha="right",
                 fontsize=9.5, color=ps.ORANGE)
    axes[1].set(title="Eigenvalues of the correlation matrix",
                xlabel="Component", ylabel="Eigenvalue")
    axes[1].set_xticks(components)

    for axis in axes:
        axis.title.set_fontweight("bold")
        axis.title.set_fontsize(12.5)
    ps.save(figure, "svd-spectrum.png")


def figure_model_sample(features: pd.DataFrame) -> None:
    sample = features.head(6).round(3)
    sample.columns = [SHORT[c] for c in sample.columns]
    ps.table_figure(
        sample, "clustering-input-sample.png",
        "Unlabelled numeric input for clustering and PCA",
        f"{len(features):,} matches x {len(FEATURES)} features, standardised before fitting",
        max_columns=11, width=13.5,
    )


# --------------------------------------------------------------------------


def main() -> None:
    clean = pd.read_csv(DATA_DIR / "cricsheet-matches-clean.csv")
    scaled, features = build_matrix(clean)
    print(f"  matrix {scaled.shape}", flush=True)

    features.round(4).to_csv(DATA_DIR / "clustering-input-sample.csv", index=False)
    figure_model_sample(features)

    # --- k-means -----------------------------------------------------------
    kmeans_scores, kmeans_labels = [], {}
    for k in K_VALUES:
        model = KMeans(n_clusters=k, n_init=10, random_state=RANDOM_STATE)
        labels = model.fit_predict(scaled)
        score = float(silhouette_score(scaled, labels, sample_size=3000,
                                       random_state=RANDOM_STATE))
        kmeans_scores.append({"k": k, "silhouette": round(score, 4),
                              "inertia": round(float(model.inertia_), 1)})
        kmeans_labels[k] = labels
        print(f"    k-means k={k} silhouette={score:.4f}", flush=True)

    best_kmeans = max(kmeans_scores, key=lambda row: row["silhouette"])
    best_k = best_kmeans["k"]

    # --- hierarchical ------------------------------------------------------
    positions = stratified_sample(clean, HIERARCHICAL_SAMPLE)
    sample_matrix = scaled[positions]
    sample_frame = clean.iloc[positions]
    distances = pdist(sample_matrix, metric="cosine")
    tree = linkage(distances, method="average")

    hierarchical_scores, hierarchical_labels = [], {}
    for k in K_VALUES:
        labels = fcluster(tree, t=k, criterion="maxclust")
        if len(np.unique(labels)) < 2:
            continue
        score = float(silhouette_score(sample_matrix, labels, metric="cosine"))
        hierarchical_scores.append({"k": k, "silhouette": round(score, 4)})
        hierarchical_labels[k] = labels
        print(f"    hclust  k={k} silhouette={score:.4f}", flush=True)

    best_hierarchical = max(hierarchical_scores, key=lambda row: row["silhouette"])
    agreement = adjusted_rand_score(
        kmeans_labels[best_hierarchical["k"]][positions],
        hierarchical_labels[best_hierarchical["k"]],
    )

    # --- PCA and SVD -------------------------------------------------------
    pca = PCA().fit(scaled)
    coordinates = pca.transform(scaled)
    explained = pca.explained_variance_ratio_
    cumulative = np.cumsum(explained)
    loadings = pca.components_

    centred = scaled - scaled.mean(axis=0)
    singular_values = np.linalg.svd(centred, full_matrices=False)[1]
    eigenvalues = pca.explained_variance_

    # --- figures -----------------------------------------------------------
    figure_silhouette_curve(kmeans_scores, hierarchical_scores, best_k)
    figure_silhouette_profile(scaled, kmeans_labels[best_k], best_k, best_kmeans["silhouette"])
    figure_cluster_scatter(coordinates, kmeans_labels[best_k], explained, best_k)
    figure_cluster_profiles(features, kmeans_labels[best_k], best_k)
    figure_cluster_composition(clean, kmeans_labels[best_k], best_k)
    figure_dendrogram(sample_matrix, sample_frame, best_hierarchical["k"])
    figure_scree(explained, cumulative)
    figure_biplot(coordinates, loadings, explained, kmeans_labels[best_k], best_k)
    figure_loadings(loadings)
    figure_svd(singular_values, eigenvalues)

    components_for_90 = int(np.searchsorted(cumulative, 0.90) + 1)
    cluster_frame = clean.assign(cluster=kmeans_labels[best_k])
    results = {
        "n_matches": int(len(clean)),
        "n_features": len(FEATURES),
        "feature_names": FEATURES,
        "scaled": True,
        "kmeans": kmeans_scores,
        "kmeans_best_k": best_k,
        "kmeans_best_silhouette": best_kmeans["silhouette"],
        "headline_k": {str(row["k"]): row["silhouette"]
                       for row in kmeans_scores if row["k"] in HEADLINE_K},
        "hierarchical": hierarchical_scores,
        "hierarchical_best_k": best_hierarchical["k"],
        "hierarchical_best_silhouette": best_hierarchical["silhouette"],
        "hierarchical_sample_size": int(len(positions)),
        "adjusted_rand_index": round(float(agreement), 4),
        "cluster_sizes": {str(c): int((kmeans_labels[best_k] == c).sum()) for c in range(best_k)},
        "cluster_format_mix": {
            str(c): cluster_frame[cluster_frame["cluster"] == c]["match_type"]
            .value_counts(normalize=True).round(3).to_dict()
            for c in range(best_k)
        },
        "cluster_mean_runs": {
            str(c): round(float(cluster_frame[cluster_frame["cluster"] == c]["first_innings_runs"].mean()), 1)
            for c in range(best_k)
        },
        "cluster_defended_rate": {
            str(c): round(float(cluster_frame[cluster_frame["cluster"] == c]["bat_first_won"].mean()), 3)
            for c in range(best_k)
        },
        "explained_variance_ratio": [round(float(v), 5) for v in explained],
        "cumulative_variance_ratio": [round(float(v), 5) for v in cumulative],
        "eigenvalues": [round(float(v), 4) for v in eigenvalues],
        "singular_values": [round(float(v), 3) for v in singular_values],
        "components_for_90_percent": components_for_90,
        "pc1_pc2_variance": round(float(cumulative[1]), 4),
        "pc1_loadings": {SHORT[f]: round(float(loadings[0, i]), 3)
                         for i, f in enumerate(FEATURES)},
        "pc2_loadings": {SHORT[f]: round(float(loadings[1, i]), 3)
                         for i, f in enumerate(FEATURES)},
        "eigenvalues_above_one": int((eigenvalues > 1).sum()),
    }
    with open(OUTPUT_DIR / "clustering-pca-results.json", "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)

    print(f"\n  best k-means k={best_k} silhouette={best_kmeans['silhouette']}")
    print(f"  best hclust  k={best_hierarchical['k']} silhouette={best_hierarchical['silhouette']}")
    print(f"  ARI between the two at k={best_hierarchical['k']}: {agreement:.3f}")
    print(f"  components for 90% variance: {components_for_90}")
    print(f"  PC1+PC2 variance: {cumulative[1]:.1%}")


if __name__ == "__main__":
    main()
