# Cricket Machine Learning Project

A React and Vite website documenting a term-long machine learning project on
international cricket: data gathering and cleaning, exploratory analysis,
clustering, PCA and SVD, and supervised classification with Naive Bayes,
Decision Trees, logistic regression and AdaBoost, plus linear regression.

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

Install the Python packages in `requirements.txt`, then run the six scripts in
order from the project root:

```sh
python public/analysis/build_dataset.py      # gather + clean  (slow: downloads ~29 MB)
python public/analysis/eda_cricket.py        # 15 exploratory figures
python public/analysis/concept_figures.py    # explanatory diagrams for the Overview sections
python public/analysis/clustering_pca.py     # clustering, PCA, SVD
python public/analysis/supervised_models.py  # Naive Bayes, Decision Trees
python public/analysis/regression_adaboost.py # linear + logistic regression, AdaBoost
```

`build_dataset.py` options:

- `--from-raw` re-cleans the committed `cricsheet-matches-raw.csv` instead of
  downloading. Cricsheet keeps adding matches, so a fresh download produces a
  larger raw file than the one published with the site.
- `--skip-weather` keeps the committed `venue-weather.csv` instead of calling
  Open-Meteo. Without it, only cities and dates missing from that file are
  requested.

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
  ball-by-ball data, applies eleven documented cleaning rules, calls CricAPI
  (raw snapshot plus a cleaned ODI/T20 version) and Open-Meteo (match-day
  weather for every host city with 38+ matches), and writes all the CSVs.
- `eda_cricket.py` — the raw/clean comparison tables and 15 exploratory figures.
- `concept_figures.py` — small synthetic diagrams that explain k-means,
  hierarchical clustering, distance measures, eigenvectors, dimensionality and
  impurity. They use made-up data on purpose; the cricket results come from the
  other scripts.
- `clustering_pca.py` — k-means and average-linkage hierarchical clustering on
  cosine distance, plus PCA and SVD. All features are standardised first;
  silhouettes are scored on every match, not a subsample.
- `supervised_models.py` — Multinomial, Bernoulli and Gaussian Naive Bayes plus
  three Decision Trees, on a disjoint stratified 70/30 split.
- `regression_adaboost.py` — linear regression (first-innings total from the
  powerplay), logistic regression and AdaBoost (defended or chased). Reuses the
  Part 3 train/test files so every model is scored on the same test matches;
  all settings are chosen by cross-validation or a validation split inside the
  training set, and the test set is used once per final model.
- `plot_style.py` — shared figure styling used by every figure script.

### Generated outputs consumed by the website

- `public/analysis/eda-summary.json`
- `public/analysis/clustering-pca-results.json`
- `public/analysis/supervised-results.json`
- `public/analysis/regression-adaboost-results.json`

The numbers in the page text and figure captions are read from these files at
runtime rather than typed into the page, so re-running the pipeline updates the
site.

## Headline results

| | |
| --- | --- |
| Matches after cleaning | 6,066 (2002–2026) |
| Rows removed in cleaning | 806, leaving zero empty cells |
| Best clustering | k = 2, recovering the ODI/T20 split; ARI 0.976 between methods |
| PCA | 5 of 11 components reach 90% of variance |
| Best classifier | Decision tree, 72.4% vs a 50.9% majority-class baseline |
