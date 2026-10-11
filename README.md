# Cricket Machine Learning Project

A React and Vite project website documenting cricket data preparation, exploratory analysis, clustering, PCA, and SVD.

## Run the website

```sh
npm install
npm run dev
npm run build
```

## Reproduce the analysis

Install the Python packages listed in `requirements.txt` and set `CRICAPI_KEY` in your local environment. Do not put the key in source files, public assets, or a `VITE_` variable. Then run:

```sh
python public/analysis/analyze_cricket.py
```

The script fetches current-match data from CricAPI, writes the raw and cleaned CSV files under `public/`, and regenerates the metrics JSON and plots under `public/analysis/`. GitHub Pages serves these generated files as static assets and does not run the Python script or refresh API data. Run the script and deploy a new build to update the published data.

## Main files

- `src/App.jsx`: tabs, assignment text, data links, and analysis figures
- `src/App.css`: project and responsive figure styling
- `public/analysis/analyze_cricket.py`: cleaning, clustering, PCA/SVD, metrics, and plot generation
- `public/analysis/results.json`: computed report consumed by the website
- `public/raw-cricket-data.csv` and `public/cleaned-cricket-data.csv`: accessible input and cleaned sample
