import { useEffect, useState } from 'react'
import './App.css'
import cricketPlayer from './assets/334647.jpg'
import cricketCelebration from './assets/Screenshot 2026-09-20 214218.png'

const tabs = ['Introduction', 'Data Prep & EDA', 'Clustering', 'PCA', 'NaiveBayes', 'DecTrees', 'Regression', 'AdaBoost', 'GradientBoosting', 'XGBoost', 'SVM', 'NN', 'Conclusions']
const assetUrl = (path) => `${import.meta.env.BASE_URL}${path}`

const introParagraphs = [
  'I chose cricket because a match is shaped by more than the final score. Teams make decisions about batting, bowling, and field placement as conditions change, and those choices give the sport a useful connection to data analysis. Cricket also has a large following across different countries, so the game matters to players, supporters, and communities beyond the field.',
  'For this project, I am interested in how live match records can be organized and explored with machine learning. I gathered current-match data from CricAPI, which provides team names, venues, dates, statuses, and score entries. The project uses those real match details to explore how similar matches cluster and how the key features can be reduced into a smaller set of components.',
  'The current dataset is built from live cricket match records, cleaned and prepared for analysis. I extracted innings runs, wickets, overs, and run rate, then combined these values with match status, venue, teams, and match type for clustering, PCA, and SVD.'
]

const questions = [
  'Which batting statistics are most closely related to match results?',
  'How do strike rate and run rate vary across an innings?',
  'Which bowling statistics best describe wicket-taking performance?',
  'How do venues relate to scoring patterns?',
  'Are strong powerplay scores associated with match wins?',
  'Which player statistics are most useful for comparing performance?',
  'How is the toss related to match outcomes?',
  'Can recent results help describe a team\'s form?',
  'Which match features best separate wins from losses?',
  'Do these patterns differ across cricket formats?'
]

function App() {
  const [activeTab, setActiveTab] = useState('Introduction')
  const [report, setReport] = useState(null)
  const [reportError, setReportError] = useState('')

  useEffect(() => {
    let cancelled = false

    fetch(assetUrl('analysis/results.json'))
      .then((response) => {
        if (!response.ok) throw new Error(`Analysis report returned ${response.status}`)
        return response.json()
      })
      .then((data) => {
        if (!cancelled) setReport(data)
      })
      .catch(() => {
        if (!cancelled) setReportError('The analysis results could not be loaded.')
      })

    return () => {
      cancelled = true
    }
  }, [])

  const renderIntroduction = () => (
    <section className="content-panel">
      <div className="text-block">
        {introParagraphs.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
      </div>
      <div className="intro-gallery">
        <figure className="intro-figure">
          <img src={cricketPlayer} alt="Cricket player preparing to bat" />
          <figcaption>Batting depends on timing, judgment, and adapting to each delivery.</figcaption>
        </figure>
        <figure className="intro-figure">
          <img src={cricketCelebration} alt="Cricket players celebrating together" />
          <figcaption>Players rely on coordination as a match changes around them.</figcaption>
        </figure>
      </div>
      <div className="questions-box">
        <h3>Questions for further study</h3>
        <ol>{questions.map((question) => <li key={question}>{question}</li>)}</ol>
      </div>
    </section>
  )

  const renderDataPrep = () => {
    const data = report?.dataset

    return (
      <section className="content-panel">
        <div className="section-summary">
          <p>I used live current-match cricket data from CricAPI, which includes match status, team names, venue, date, and innings score details. The data was cleaned, standardized, and reduced to meaningful fields for clustering and PCA. The charts below show the cleaned API-derived sample and the feature matrix used for later unsupervised learning.</p>
        </div>

        <div className="summary-grid">
          <div className="summary-card"><span>Records</span><strong>{data?.records ?? '—'}</strong></div>
          <div className="summary-card"><span>Match statuses</span><strong>{data ? Object.keys(data.status_counts).length : '—'}</strong></div>
          <div className="summary-card"><span>Venues</span><strong>{data ? Object.keys(data.venue_counts).length : '—'}</strong></div>
        </div>

        <div className="data-links-row">
          <div className="data-download-card">
            <h3>Raw data</h3>
            <a href={assetUrl('raw-cricket-data.csv')} download>Open raw CSV</a>
          </div>
          <div className="data-download-card">
            <h3>Cleaned data</h3>
            <a href={assetUrl('cleaned-cricket-data.csv')} download>Open cleaned CSV</a>
          </div>
          <div className="data-download-card">
            <h3>API source</h3>
            <a href="https://api.cricapi.com/v1/currentMatches" target="_blank" rel="noreferrer">CricAPI current matches</a>
          </div>
          <div className="data-download-card">
            <h3>Analysis code</h3>
            <a href={assetUrl('analysis/analyze_cricket.py')} download>Python script</a>
          </div>
        </div>

        <div className="analysis-figure-grid">
          <figure className="figure-card">
            <img src={assetUrl('analysis/status-counts.png')} alt="Bar chart of sample match counts by status" />
            <figcaption>Figure 1: Match status counts from the cleaned sample.</figcaption>
          </figure>
          <figure className="figure-card">
            <img src={assetUrl('analysis/venue-counts.png')} alt="Bar chart of sample match counts by venue" />
            <figcaption>Figure 2: Venue distribution across the current API records.</figcaption>
          </figure>
          <figure className="figure-card">
            <img src={assetUrl('analysis/encoded-feature-sample.png')} alt="Encoded feature matrix built from API match records" />
            <figcaption>Figure 3: Encoded numeric feature sample used in clustering and PCA.</figcaption>
          </figure>
          <figure className="figure-card">
            <img src={assetUrl('analysis/silhouette-comparison.png')} alt="Silhouette comparison by cluster count" />
            <figcaption>Figure 4: Silhouette comparison across the tested cluster counts.</figcaption>
          </figure>
          <figure className="figure-card">
            <img src={assetUrl('analysis/cluster-map.png')} alt="Cluster assignments projected in PC space" />
            <figcaption>Figure 5: K-means assignments projected onto the first two principal components.</figcaption>
          </figure>
          <figure className="figure-card">
            <img src={assetUrl('analysis/dendrogram.png')} alt="Dendrogram for hierarchical clustering" />
            <figcaption>Figure 6: Average-linkage dendrogram using cosine distance.</figcaption>
          </figure>
          <figure className="figure-card">
            <img src={assetUrl('analysis/pca-scree.png')} alt="PCA explained variance scree plot" />
            <figcaption>Figure 7: PCA explained-variance chart showing variance by component.</figcaption>
          </figure>
          <figure className="figure-card">
            <img src={assetUrl('analysis/pca-biplot.png')} alt="PCA biplot with score points and loading directions" />
            <figcaption>Figure 8: PCA biplot summarizing the match positions and feature loadings.</figcaption>
          </figure>
          <figure className="figure-card">
            <img src={assetUrl('analysis/svd-spectrum.png')} alt="Singular value spectrum" />
            <figcaption>Figure 9: SVD singular-value spectrum for the uncentered feature matrix.</figcaption>
          </figure>
          <figure className="figure-card">
            <img src={assetUrl('analysis/svd-projection.png')} alt="Rank-two SVD projection" />
            <figcaption>Figure 10: Two-dimensional SVD projection of the sample records.</figcaption>
          </figure>
        </div>

        <div className="data-preview">
          <h3>Cleaned API records</h3>
          <div className="table-scroll">
            <table>
              <thead><tr><th>Match</th><th>Status</th><th>Venue</th><th>Date</th></tr></thead>
              <tbody>
                {(data?.preview_rows ?? []).map((row) => (
                  <tr key={row.match_name}><td>{row.match_name}</td><td>{row.status}</td><td>{row.venue}</td><td>{row.date}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    )
  }

  const renderClustering = () => {
    const results = report?.clustering
    const data = report?.dataset
    const bestKMeans = results?.kmeans.find((item) => item.k === results.kmeans_best_k)
    const bestHierarchical = results?.hierarchical.find((item) => item.k === results.hierarchical_best_k)

    return (
      <section className="content-panel assignment-panel">
        <header className="assignment-heading">
          <span className="eyebrow">Unsupervised learning</span>
          <h2>Clustering</h2>
          <p>Grouping match records without an outcome label.</p>
        </header>

        <section className="assignment-section">
          <h3>Overview</h3>
          <p>Clustering groups observations by similarity without using a known class label. Partitional methods such as k-means assign each row to one of k groups, minimizing within-group squared Euclidean distance. Hierarchical clustering builds a tree of merges. I used average linkage with cosine distance, which measures the angle between feature vectors rather than their magnitude.</p>
          <p>I compared match status, venue, teams, match type, and innings score summaries. The silhouette score compares how close each record is to its own group and to other groups. These are match-level records, so the results describe this API snapshot rather than individual player performance.</p>
          <div className="analysis-figure-grid">
            <figure className="figure-card"><img src={assetUrl('analysis/cluster-map.png')} alt="K-means groups projected onto the first two principal components" /><figcaption>K-means assignments shown in the first two principal components.</figcaption></figure>
            <figure className="figure-card"><img src={assetUrl('analysis/dendrogram.png')} alt="Average-linkage hierarchical dendrogram using cosine distance" /><figcaption>Hierarchical merges using cosine distance.</figcaption></figure>
          </div>
        </section>

        <section className="assignment-section">
          <h3>Data Prep</h3>
          <p>Clustering uses unlabeled numeric data. I combined innings runs, wickets, overs, and run rate with one-hot encoded status, venue, team, and match-type fields, producing {data?.numeric_features ?? '—'} input columns. Match name and date are shown in the table but are not model inputs. The numeric values are not scaled, so larger score values can have more influence on distances.</p>
          <div className="data-action-row"><a href={assetUrl('raw-cricket-data.csv')} download>Raw CSV</a><a href={assetUrl('cleaned-cricket-data.csv')} download>Cleaned CSV</a><a href={assetUrl('analysis/encoded-feature-sample.png')} target="_blank" rel="noreferrer">Feature matrix image</a></div>
          <figure className="figure-card sample-figure"><img src={assetUrl('analysis/encoded-feature-sample.png')} alt="Preview of one-hot encoded numeric clustering features" /><figcaption>Encoded model input: {data?.records ?? '—'} records and {data?.numeric_features ?? '—'} numeric features.</figcaption></figure>
        </section>

        <section className="assignment-section">
          <h3>Code</h3>
          <p>The Python script fetches the current CricAPI records, cleans the fields, creates the feature matrix, and compares k-means with average-linkage hierarchical clustering using cosine distance.</p>
          <a className="code-download" href={assetUrl('analysis/analyze_cricket.py')} download>Python analysis script</a>
        </section>

        <section className="assignment-section">
          <h3>Results</h3>
          {results ? <>
            <div className="metric-strip"><div><span>K-means best k</span><strong>{results.kmeans_best_k}</strong></div><div><span>Hierarchical best k</span><strong>{results.hierarchical_best_k}</strong></div><div><span>Hierarchical groups</span><strong>{results.hierarchical_cluster_count ?? results.hierarchical_best_k}</strong></div><div><span>Adjusted Rand index</span><strong>{results.best_solution_adjusted_rand_index.toFixed(2)}</strong></div></div>
            <p>The highest k-means silhouette was {bestKMeans.silhouette.toFixed(3)} at k={bestKMeans.k}. The highest hierarchical silhouette was {bestHierarchical.silhouette.toFixed(3)} at k={bestHierarchical.k}. The adjusted Rand index was {results.best_solution_adjusted_rand_index.toFixed(2)}, which summarizes how closely the two selected groupings agree. These results describe the current API records, not stable categories across cricket matches.</p>
            <div className="analysis-figure-grid">
              <figure className="figure-card"><img src={assetUrl('analysis/silhouette-comparison.png')} alt="Silhouette scores at k equals 2, 3, and 4 for both clustering methods" /><figcaption>Silhouette scores for k=2, 3, and 4.</figcaption></figure>
              <figure className="figure-card"><img src={assetUrl('analysis/cluster-map.png')} alt="Scatter plot of matches colored by k-means cluster" /><figcaption>Cluster assignments projected onto two principal components.</figcaption></figure>
              <figure className="figure-card wide-figure"><img src={assetUrl('analysis/dendrogram.png')} alt="Cosine-distance hierarchical clustering dendrogram" /><figcaption>The dendrogram shows how the current API records merge under average linkage.</figcaption></figure>
            </div>
          </> : <p role="status">{reportError || 'Loading clustering results.'}</p>}
        </section>

        <section className="assignment-section">
          <h3>Conclusions</h3>
          <p>The cluster assignments summarize similarities among the current API records. Because the sample changes with the live endpoint and combines team, venue, status, and score-summary fields, the groups should be interpreted only as patterns in this snapshot.</p>
        </section>
      </section>
    )
  }

  const renderPca = () => {
    const results = report?.pca
    const data = report?.dataset
    const firstTwoVariance = results?.cumulative_variance_ratio[1]
    const firstFiveVariance = results?.cumulative_variance_ratio[4]

    return (
      <section className="content-panel assignment-panel">
        <header className="assignment-heading">
          <span className="eyebrow">Dimensionality reduction</span>
          <h2>PCA and SVD</h2>
          <p>Reducing the feature matrix and inspecting its main directions.</p>
        </header>

        <section className="assignment-section">
          <h3>Overview</h3>
          <p>Principal Component Analysis (PCA) replaces the original variables with ordered, perpendicular directions called principal components. An eigenvector gives a component's direction in the feature space, and its eigenvalue measures the variance along that direction. The first component captures the most variance; each following component captures as much as possible without repeating the earlier directions.</p>
          <p>Dimensionality reduction represents many variables with fewer components, which can make analysis and visualization easier, but it also discards information. The current sample has many one-hot columns relative to its number of records. PCA centers the columns but does not standardize their scales, so the larger-range score values can dominate the components. In the biplot, points are match scores on the first two components and arrows show selected variable loadings.</p>
          <div className="analysis-figure-grid">
            <figure className="figure-card"><img src={assetUrl('analysis/pca-scree.png')} alt="PCA individual and cumulative explained variance by component" /><figcaption>Variance explained by each component and cumulatively.</figcaption></figure>
            <figure className="figure-card"><img src={assetUrl('analysis/pca-biplot.png')} alt="PCA scores and selected one-hot feature loading vectors" /><figcaption>Match scores and selected variable loading directions.</figcaption></figure>
          </div>
        </section>

        <section className="assignment-section">
          <h3>Data Prep</h3>
          <p>PCA requires numeric observations with the same set of columns. I used the one-hot encoded matrix of {data?.numeric_features ?? '—'} features, with no labels. PCA centers the columns before decomposition. The sample is small relative to its number of features.</p>
          <div className="data-action-row"><a href={assetUrl('raw-cricket-data.csv')} download>Raw CSV</a><a href={assetUrl('cleaned-cricket-data.csv')} download>Cleaned CSV</a><a href={assetUrl('analysis/encoded-feature-sample.png')} target="_blank" rel="noreferrer">Feature matrix image</a></div>
          <figure className="figure-card sample-figure"><img src={assetUrl('analysis/encoded-feature-sample.png')} alt="Preview of the numeric matrix used for PCA and SVD" /><figcaption>Input matrix: {data?.records ?? '—'} matches by {data?.numeric_features ?? '—'} features.</figcaption></figure>
        </section>

        <section className="assignment-section">
          <h3>Code</h3>
          <p>The script applies scikit-learn PCA to the centered feature matrix and NumPy singular value decomposition to the uncentered matrix. The SVD spectrum is not the PCA variance spectrum because the input is not centered first.</p>
          <a className="code-download" href={assetUrl('analysis/analyze_cricket.py')} download>Python analysis script</a>
        </section>

        <section className="assignment-section">
          <h3>Results</h3>
          {results ? <>
            <p>PC1 explains {(results.explained_variance_ratio[0] * 100).toFixed(1)}% of the variance, and the first two components explain {(firstTwoVariance * 100).toFixed(1)}%. The first five explain {(firstFiveVariance * 100).toFixed(1)}%. The biplot places each match by its first two component scores; loading arrows show which variables contribute to those directions. The largest absolute PC1 loadings are {results.top_pc1_loadings.map(([name]) => name.replace('status_', 'status: ').replace('venue_', 'venue: ').replace('team_1_', 'team 1: ').replace('team_2_', 'team 2: ')).join(', ')}.</p>
            <div className="analysis-figure-grid">
              <figure className="figure-card"><img src={assetUrl('analysis/pca-scree.png')} alt="Scree plot with individual and cumulative PCA variance" /><figcaption>The scree plot shows individual and cumulative explained variance.</figcaption></figure>
              <figure className="figure-card"><img src={assetUrl('analysis/pca-biplot.png')} alt="PCA biplot of match scores and variable loadings" /><figcaption>The biplot relates match positions to selected feature directions.</figcaption></figure>
              <figure className="figure-card"><img src={assetUrl('analysis/svd-spectrum.png')} alt="Singular values of the one-hot feature matrix" /><figcaption>Singular values from SVD of the uncentered matrix.</figcaption></figure>
              <figure className="figure-card"><img src={assetUrl('analysis/svd-projection.png')} alt="Rank-two SVD projection of the match sample" /><figcaption>Rank-two SVD projection using the two largest singular directions.</figcaption></figure>
            </div>
          </> : <p role="status">{reportError || 'Loading PCA and SVD results.'}</p>}
        </section>

        <section className="assignment-section">
          <h3>Conclusions</h3>
          <p>The first two components retain {(firstTwoVariance * 100).toFixed(1)}% of the variance in this dataset. The loadings show which input features contribute to the component directions; they do not establish player or team performance. These results describe the current API snapshot, and the unscaled numeric features should be considered when interpreting the projection.</p>
        </section>
      </section>
    )
  }

  const renderConclusions = () => (
    <section className="content-panel">
      <div className="text-block">
        <p>I used live CricAPI match records and analyzed their teams, venues, statuses, match types, and innings score summaries. The clustering and dimensionality-reduction results describe the records returned at the time of analysis.</p>
        <p>The dataset contains match-level summaries, not ball-by-ball or player-level performance. The sample can also change as current matches change, so the results should not be generalized beyond this snapshot.</p>
      </div>
      <div className="image-grid single-image">
        <figure className="figure-card">
          <img src={cricketCelebration} alt="Cricket players celebrating together" />
          <figcaption>The analysis is limited to the match-level fields returned by the current API.</figcaption>
        </figure>
      </div>
    </section>
  )

  const renderPlaceholderTab = (tabLabel) => (
    <section className="content-panel assignment-panel">
      <header className="assignment-heading">
        <span className="eyebrow">Work in progress</span>
        <h2>{tabLabel}</h2>
        <p>This tab is included in the project structure, and the method will be developed in a later phase of the assignment.</p>
      </header>
      <div className="section-summary">
        <p>Work in progress for the next phases of the project. This placeholder keeps the required navigation complete without adding unrelated models or datasets.</p>
      </div>
    </section>
  )

  const renderTab = () => {
    if (activeTab === 'Introduction') return renderIntroduction()
    if (activeTab === 'Data Prep & EDA') return renderDataPrep()
    if (activeTab === 'Clustering') return renderClustering()
    if (activeTab === 'PCA') return renderPca()
    if (activeTab === 'NaiveBayes') return renderPlaceholderTab('Naive Bayes')
    if (activeTab === 'DecTrees') return renderPlaceholderTab('Decision Trees')
    if (activeTab === 'Regression') return renderPlaceholderTab('Regression')
    if (activeTab === 'AdaBoost') return renderPlaceholderTab('AdaBoost')
    if (activeTab === 'GradientBoosting') return renderPlaceholderTab('Gradient Boosting')
    if (activeTab === 'XGBoost') return renderPlaceholderTab('XGBoost')
    if (activeTab === 'SVM') return renderPlaceholderTab('SVM')
    if (activeTab === 'NN') return renderPlaceholderTab('Neural Networks')
    return renderConclusions()
  }

  return (
    <div className="page-shell sidebar-layout">
      <aside className="sidebar">
        <div className="brand-wrap">
          <div className="brand-mark">CR</div>
          <span>Cricket Analytics Project</span>
        </div>
        <nav className="tab-nav" aria-label="Project navigation">
          {tabs.map((tab) => (
            <button key={tab} type="button" className={activeTab === tab ? 'tab-button active' : 'tab-button'} onClick={() => setActiveTab(tab)}>
              {tab}
            </button>
          ))}
        </nav>
      </aside>
      <main className="content-wrap">{renderTab()}</main>
    </div>
  )
}

export default App