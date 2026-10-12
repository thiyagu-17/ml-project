"""Fetch live CricAPI cricket match data, clean it, and reproduce clustering/PCA analysis."""

import json
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage
from scipy.spatial.distance import pdist
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, silhouette_score

API_URL = "https://api.cricapi.com/v1/currentMatches"
PUBLIC_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PUBLIC_DIR / "analysis"
RAW_PATH = PUBLIC_DIR / "raw-cricket-data.csv"
CLEAN_PATH = PUBLIC_DIR / "cleaned-cricket-data.csv"
K_VALUES = [2, 3, 4]

plt.rcParams.update({"figure.facecolor": "#f4f1e8", "axes.facecolor": "#f4f1e8", "savefig.facecolor": "#f4f1e8", "font.family": "DejaVu Sans"})


def fetch_live_matches():
    api_key = os.environ.get("CRICAPI_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Set CRICAPI_KEY in your environment before running the analysis.")
    response = requests.get(API_URL, params={"apikey": api_key, "offset": 0}, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Unexpected response format from CricAPI.")
    records = payload.get("data") or []
    if not records:
        raise ValueError("No live matches returned by CricAPI.")
    return records


def parse_score_summary(match_record):
    total_runs = 0
    total_wickets = 0
    total_overs = 0.0
    score_entries = match_record.get("score") or []
    for entry in score_entries:
        if not isinstance(entry, dict):
            continue
        try:
            total_runs += int(entry.get("r", 0) or 0)
        except (TypeError, ValueError):
            pass
        try:
            total_wickets += int(entry.get("w", 0) or 0)
        except (TypeError, ValueError):
            pass
        try:
            total_overs += parse_cricket_overs(entry.get("o", 0))
        except (TypeError, ValueError):
            pass
    return {
        "innings_runs": total_runs,
        "innings_wickets": total_wickets,
        "innings_overs": total_overs,
        "runs_per_over": (total_runs / total_overs) if total_overs else 0.0,
    }


def parse_cricket_overs(value):
    text = str(value or "0").strip()
    whole_overs, separator, balls_text = text.partition(".")
    whole_overs = int(whole_overs or 0)
    if not separator:
        return float(whole_overs)
    balls = int(balls_text or 0)
    if not 0 <= balls < 6:
        raise ValueError("Cricket overs must contain between zero and five balls after the decimal point.")
    return whole_overs + balls / 6


def clean_status(value):
    text = str(value or "").strip()
    low = text.lower()
    if any(token in low for token in ["stumps", "lead", "trail", "day", "innings", "in progress", "live"]):
        return "Live/In Progress"
    if any(token in low for token in ["won", "completed", "finished", "abandoned", "result"]):
        return "Completed"
    if "scheduled" in low:
        return "Scheduled"
    if "tie" in low:
        return "Completed"
    if text:
        return text
    return "Unknown"


def normalize_match(match_record):
    teams = match_record.get("teams") or []
    team_1 = str(teams[0]).strip() if len(teams) > 0 else "Unknown"
    team_2 = str(teams[1]).strip() if len(teams) > 1 else "Unknown"
    status = clean_status(match_record.get("status"))
    venue = str(match_record.get("venue") or "Unknown").strip()
    date_value = str(match_record.get("date") or "Unknown").strip()
    match_type = str(match_record.get("matchType") or "Unknown").strip().title()
    score_summary = parse_score_summary(match_record)
    match_name = str(match_record.get("name") or f"{team_1} vs {team_2}").strip()
    row = {
        "match_name": match_name,
        "status": status,
        "venue": venue,
        "team_1": team_1,
        "team_2": team_2,
        "date": date_value,
        "match_type": match_type,
        **score_summary,
    }
    return row


def fetch_and_save_raw_data():
    matches = fetch_live_matches()
    rows = [normalize_match(match) for match in matches]
    frame = pd.DataFrame(rows)
    frame = frame.dropna(subset=["match_name", "team_1", "team_2"]).copy()
    frame = frame.drop_duplicates(subset=["match_name"], keep="first")
    for column in ["match_name", "status", "venue", "team_1", "team_2", "match_type", "date"]:
        if column in frame.columns:
            frame[column] = frame[column].astype(str).str.strip()
    frame.to_csv(RAW_PATH, index=False)
    return frame


def clean_fixture(frame):
    cleaned = frame.copy()
    cleaned["status"] = cleaned["status"].apply(clean_status)
    cleaned["match_type"] = cleaned["match_type"].replace({"": "Unknown"})
    cleaned["venue"] = cleaned["venue"].fillna("Unknown")
    cleaned["team_1"] = cleaned["team_1"].fillna("Unknown")
    cleaned["team_2"] = cleaned["team_2"].fillna("Unknown")
    cleaned["match_name"] = cleaned["match_name"].fillna(cleaned["team_1"] + " vs " + cleaned["team_2"])
    cleaned = cleaned.drop_duplicates(subset=["match_name"], keep="first")
    cleaned["innings_runs"] = pd.to_numeric(cleaned["innings_runs"], errors="coerce").fillna(0)
    cleaned["innings_wickets"] = pd.to_numeric(cleaned["innings_wickets"], errors="coerce").fillna(0)
    cleaned["innings_overs"] = pd.to_numeric(cleaned["innings_overs"], errors="coerce").fillna(0)
    cleaned["runs_per_over"] = pd.to_numeric(cleaned["runs_per_over"], errors="coerce").fillna(0)
    cleaned = cleaned[["match_name", "status", "venue", "team_1", "team_2", "date", "match_type", "innings_runs", "innings_wickets", "innings_overs", "runs_per_over"]]
    cleaned.to_csv(CLEAN_PATH, index=False)
    return cleaned


def save_bar_chart(series, filename, title, color):
    fig, axis = plt.subplots(figsize=(8, 4.4))
    series.value_counts().sort_values().plot.barh(ax=axis, color=color, width=0.68)
    axis.set(title=title, xlabel="Number of records", ylabel="")
    axis.grid(axis="x", alpha=0.18)
    axis.spines[["top", "right", "left"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / filename, dpi=160)
    plt.close(fig)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_frame = fetch_and_save_raw_data()
    frame = clean_fixture(raw_frame)
    if frame.empty:
        raise ValueError("No valid match records remained after cleaning.")

    feature_columns = ["status", "venue", "team_1", "team_2", "match_type", "innings_runs", "innings_wickets", "innings_overs", "runs_per_over"]
    encoded = pd.get_dummies(frame[feature_columns], columns=["status", "venue", "team_1", "team_2", "match_type"], dtype=int)
    matrix = encoded.to_numpy(dtype=float)
    n_rows, n_features = matrix.shape
    unique_rows = np.unique(matrix, axis=0).shape[0]
    candidate_k_values = [k for k in K_VALUES if k < n_rows and k <= unique_rows]
    if not candidate_k_values:
        raise ValueError("At least three distinct match feature rows are required for clustering.")

    kmeans_results, kmeans_labels = [], {}
    for k in candidate_k_values:
        labels = KMeans(n_clusters=k, n_init=30, random_state=42).fit_predict(matrix)
        if not 2 <= len(np.unique(labels)) < n_rows:
            continue
        kmeans_labels[k] = labels
        kmeans_results.append({"k": k, "silhouette": float(silhouette_score(matrix, labels))})
    if not kmeans_results:
        raise ValueError("K-means could not form valid clusters from the current match data.")
    best_kmeans = max(kmeans_results, key=lambda result: result["silhouette"])

    cosine_distances = pdist(matrix, metric="cosine")
    hierarchy = linkage(cosine_distances, method="average")
    hclust_results, hclust_labels = [], {}
    for k in candidate_k_values:
        labels = fcluster(hierarchy, t=k, criterion="maxclust")
        if not 2 <= len(np.unique(labels)) < n_rows:
            continue
        hclust_labels[k] = labels
        hclust_results.append({"k": k, "silhouette": float(silhouette_score(matrix, labels, metric="cosine"))})
    if not hclust_results:
        raise ValueError("Hierarchical clustering could not form valid clusters from the current match data.")
    best_hclust = max(hclust_results, key=lambda result: result["silhouette"])
    hclust_count = len(set(hclust_labels[best_hclust["k"]]))
    ari = adjusted_rand_score(kmeans_labels[best_kmeans["k"]], hclust_labels[best_hclust["k"]])

    pca = PCA().fit(matrix)
    coordinates = pca.transform(matrix)
    left_vectors, singular_values, _ = np.linalg.svd(matrix, full_matrices=False)
    svd_coordinates = left_vectors[:, :2] * singular_values[:2]

    save_bar_chart(frame["status"], "status-counts.png", "Current matches by status", "#26736d")
    save_bar_chart(frame["venue"], "venue-counts.png", "Current matches by venue", "#d17b39")

    fig, axis = plt.subplots(figsize=(11, 4.7))
    sample = encoded.head(min(6, len(encoded)))
    axis.axis("off")
    table = axis.table(cellText=sample.values, colLabels=sample.columns, rowLabels=[f"Match {i + 1}" for i in sample.index], loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(7)
    table.scale(1, 1.45)
    axis.set_title("One-hot encoded API match matrix (sample)", loc="left", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "encoded-feature-sample.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(7.7, 4.7))
    axis.bar([str(x["k"]) for x in kmeans_results], [x["silhouette"] for x in kmeans_results], color="#26736d", label="K-means / Euclidean")
    axis.plot([str(x["k"]) for x in hclust_results], [x["silhouette"] for x in hclust_results], color="#d17b39", marker="o", label="Average linkage / cosine")
    axis.set(title="Silhouette comparison across candidate k", xlabel="Number of clusters (k)", ylabel="Mean silhouette score")
    axis.axhline(0, color="#48565a", linewidth=0.8)
    axis.legend(frameon=False)
    axis.grid(axis="y", alpha=0.18)
    axis.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "silhouette-comparison.png", dpi=170)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(8.5, 5.3))
    axis.scatter(coordinates[:, 0], coordinates[:, 1], c=kmeans_labels[best_kmeans["k"]], cmap="Set2", s=95, edgecolor="#202a2e", linewidth=0.7)
    for i, name in enumerate(frame["match_name"]):
        axis.annotate(f"{i + 1}. {name}", coordinates[i, :2], xytext=(5, 4), textcoords="offset points", fontsize=7)
    axis.set(title=f"K-means groups projected onto first two PCs (k={best_kmeans['k']})", xlabel=f"PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)", ylabel=f"PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)")
    axis.grid(alpha=0.18)
    axis.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "cluster-map.png", dpi=170)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(10, 5.5))
    dendrogram(hierarchy, labels=[f"{i + 1}. {name}" for i, name in enumerate(frame["match_name"])], leaf_rotation=55, leaf_font_size=7, ax=axis, color_threshold=0)
    axis.set(title="Average-linkage hierarchical clustering (cosine distance)", ylabel="Cosine distance")
    axis.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "dendrogram.png", dpi=170)
    plt.close(fig)

    variance = pca.explained_variance_ratio_
    fig, axis = plt.subplots(figsize=(7.7, 4.7))
    components = np.arange(1, min(9, len(variance)) + 1)
    axis.bar(components, variance[:len(components)], color="#26736d", label="Individual")
    axis.plot(components, np.cumsum(variance[:len(components)]), color="#d17b39", marker="o", label="Cumulative")
    axis.set(title="PCA explained-variance spectrum", xlabel="Principal component", ylabel="Share of total variance")
    axis.set_xticks(components)
    axis.set_ylim(bottom=0)
    axis.legend(frameon=False)
    axis.grid(axis="y", alpha=0.18)
    axis.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "pca-scree.png", dpi=170)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(8.5, 5.4))
    axis.scatter(coordinates[:, 0], coordinates[:, 1], color="#26736d", s=75, edgecolor="white", linewidth=0.8)
    for i in range(n_rows):
        axis.annotate(str(i + 1), coordinates[i, :2], xytext=(5, 4), textcoords="offset points", fontsize=8)
    loadings = pca.components_.T[:, :2]
    scale = max(np.ptp(coordinates[:, 0]), np.ptp(coordinates[:, 1])) * 0.33
    for index in np.argsort(np.linalg.norm(loadings, axis=1))[-7:]:
        x, y = loadings[index] * scale
        axis.annotate("", xy=(x, y), xytext=(0, 0), arrowprops={"arrowstyle": "->", "color": "#d17b39", "lw": 1.3})
        axis.text(x * 1.08, y * 1.08, encoded.columns[index].replace("team_", "").replace("status_", ""), fontsize=7, color="#8b4a1d")
    axis.axhline(0, color="#aeb7b1", linewidth=0.7)
    axis.axvline(0, color="#aeb7b1", linewidth=0.7)
    axis.set(title="PCA scores and selected feature loadings", xlabel="PC1", ylabel="PC2")
    axis.grid(alpha=0.15)
    axis.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "pca-biplot.png", dpi=170)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(7.7, 4.7))
    axis.plot(np.arange(1, len(singular_values) + 1), singular_values, marker="o", color="#26736d")
    axis.set(title="Singular values of the one-hot feature matrix", xlabel="Singular-value rank", ylabel="Singular value")
    axis.grid(alpha=0.18)
    axis.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "svd-spectrum.png", dpi=170)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(8.5, 5.3))
    axis.scatter(svd_coordinates[:, 0], svd_coordinates[:, 1], color="#d17b39", s=75, edgecolor="white", linewidth=0.8)
    for i, name in enumerate(frame["match_name"]):
        axis.annotate(f"{i + 1}. {name}", svd_coordinates[i], xytext=(5, 4), textcoords="offset points", fontsize=7)
    axis.set(title="Rank-2 SVD projection of the uncentered feature matrix", xlabel="Left singular score 1", ylabel="Left singular score 2")
    axis.grid(alpha=0.18)
    axis.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "svd-projection.png", dpi=170)
    plt.close(fig)

    report = {
        "dataset": {
            "records": n_rows,
            "numeric_features": n_features,
            "feature_names": encoded.columns.tolist(),
            "preview_rows": frame.head(6).to_dict(orient="records"),
            "status_counts": frame["status"].value_counts().to_dict(),
            "venue_counts": frame["venue"].value_counts().to_dict(),
        },
        "clustering": {
            "kmeans": kmeans_results,
            "kmeans_best_k": best_kmeans["k"],
            "hierarchical": hclust_results,
            "hierarchical_best_k": best_hclust["k"],
            "hierarchical_cluster_count": hclust_count,
            "best_solution_adjusted_rand_index": float(ari),
        },
        "pca": {
            "explained_variance_ratio": variance.tolist(),
            "cumulative_variance_ratio": np.cumsum(variance).tolist(),
            "svd_singular_values": singular_values.tolist(),
            "top_pc1_loadings": sorted(zip(encoded.columns.tolist(), pca.components_[0].tolist()), key=lambda item: abs(item[1]), reverse=True)[:5],
        },
        "source": {"name": "CricAPI", "url": API_URL},
    }
    (OUTPUT_DIR / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Fetched {n_rows} current-match records from CricAPI.")
    print(f"K-means best k={best_kmeans['k']}; hierarchical cosine best k={hclust_count}; ARI={ari:.3f}.")
    print(f"PC1 explains {variance[0]:.1%}; first 2 PCs explain {variance[:2].sum():.1%}.")


if __name__ == "__main__":
    main()