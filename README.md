# Cricket Machine Learning Project

A React and Vite website documenting a term-long machine learning project on
international cricket: data gathering and cleaning, exploratory analysis,
clustering, PCA and SVD, and supervised classification with Naive Bayes and
Decision Trees.

**Topic question:** at the innings break, knowing only what the team batting
first did, will that total be defended or chased down?

## Run the website

```sh
npm install
npm run dev     # development server
npm run build   # production build into dist/
npm run preview # serve the production build
```

## Reproduce the analysis

Install the Python packages in `requirements.txt`, then run the four scripts in
order from the project root:

```sh
python public/analysis/build_dataset.py      # gather + clean  (slow: downloads ~29 MB)
python public/analysis/eda_cricket.py        # 15 exploratory figures
python public/analysis/clustering_pca.py     # clustering, PCA, SVD
python public/analysis/supervised_models.py  # Naive Bayes, Decision Trees
```

`build_dataset.py` accepts `--skip-weather` to skip the Open-Meteo enrichment.

### Data sources

| Source | Type | Key required |
| --- | --- | --- |
| [Cricsheet](https://cricsheet.org/downloads/) ball-by-ball archives | Bulk download | No |
| [CricAPI](https://api.cricapi.com/v1/currentMatches) current matches | REST API | Yes, `CRICAPI_KEY` |
| [Open-Meteo](https://open-meteo.com/) geocoding + historical archive | REST API | No |

Set `CRICAPI_KEY` in the local environment before running. Do not put the key in
source files, in `public/`, or in a `VITE_` variable, because everything under
`public/` is published with the site. When the key is absent the script keeps the
committed snapshot and continues; the other two sources need no credentials, so
the pipeline is reproducible without it.

The downloaded archives are cached in `data_cache/`, which is git-ignored and
regenerated on demand.

## Layout

```
public/analysis/     Python pipeline, generated figures, results JSON
public/data/         raw and cleaned CSVs, train/test splits, API outputs
src/App.jsx          tab layout and page structure
src/content.js       Introduction, Conclusions and About Me prose
src/App.css          styling (unchanged by the analysis pipeline)
```

### Scripts

- `build_dataset.py` — downloads the archives, flattens 6,872 matches from
  ball-by-ball data, calls both APIs, applies eleven documented cleaning rules,
  and writes the raw and cleaned CSVs.
- `eda_cricket.py` — the raw/clean comparison tables and 15 exploratory figures.
- `clustering_pca.py` — k-means and average-linkage hierarchical clustering on
  cosine distance, plus PCA and SVD. All features are standardised first.
- `supervised_models.py` — Multinomial, Bernoulli and Gaussian Naive Bayes plus
  three Decision Trees, on a disjoint stratified 70/30 split.
- `plot_style.py` — shared figure styling used by all three figure scripts.

### Generated outputs consumed by the website

- `public/analysis/eda-summary.json`
- `public/analysis/clustering-pca-results.json`
- `public/analysis/supervised-results.json`

Every number shown on the site is read from these files at runtime rather than
typed into the page, so re-running the pipeline updates the site.

## Headline results

| | |
| --- | --- |
| Matches after cleaning | 6,066 (2002–2026) |
| Rows removed in cleaning | 806, leaving zero empty cells |
| Best clustering | k = 2, recovering the ODI/T20 split; ARI 0.976 between methods |
| PCA | 5 of 11 components reach 90% of variance |
| Best classifier | Decision tree, 72.4% vs a 50.9% majority-class baseline |
