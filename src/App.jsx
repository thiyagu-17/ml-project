import { useEffect, useState } from 'react'
import './App.css'
import cricketPlayer from './assets/334647.jpg'
import cricketCelebration from './assets/Screenshot 2026-09-20 214218.png'
import { aboutMe, conclusionParagraphs, introParagraphs, questions } from './content'

const tabs = [
  'Introduction', 'DataPrep_EDA', 'Clustering', 'PCA', 'NaiveBayes', 'DecTrees',
  'Regression', 'AdaBoost', 'GradientBoosting', 'XGBoost', 'SVM', 'NN',
  'Conclusions', 'About Me',
]

const assetUrl = (path) => `${import.meta.env.BASE_URL}${path}`
const figureUrl = (name) => assetUrl(`analysis/${name}`)
const dataUrl = (name) => assetUrl(`data/${name}`)
const codeUrl = (name) => assetUrl(`analysis/${name}`)

const percent = (value, digits = 1) =>
  value === undefined || value === null ? '—' : `${(value * 100).toFixed(digits)}%`

function Figure({ name, alt, caption, wide = false }) {
  return (
    <figure className={wide ? 'figure-card wide-figure' : 'figure-card'}>
      <a href={figureUrl(name)} target="_blank" rel="noreferrer">
        <img src={figureUrl(name)} alt={alt} loading="lazy" />
      </a>
      <figcaption>{caption}</figcaption>
    </figure>
  )
}

function CodeLinks({ items }) {
  return (
    <div className="data-action-row">
      {items.map((item) => (
        <a key={item.file} className="code-download" href={codeUrl(item.file)} download>
          {item.label}
        </a>
      ))}
    </div>
  )
}

function DataLinks({ items }) {
  return (
    <div className="data-action-row">
      {items.map((item) => (
        <a key={item.href} href={item.href} target="_blank" rel="noreferrer"
           download={item.download ? '' : undefined}>
          {item.label}
        </a>
      ))}
    </div>
  )
}

// --------------------------------------------------------------------------

const edaFigures = [
  {
    name: 'missing-values.png',
    alt: 'Bar chart comparing empty cells per column in the raw and cleaned files',
    caption: 'Figure 1: The eight columns that carried the most empty cells in the raw file, with the cleaned file marked at zero. Every gap was either filled from another field or removed with the row, so the cleaned file contains no missing values at all.',
  },
  {
    name: 'runs-distribution.png',
    alt: 'Overlaid histograms of first-innings totals for the fifty-over and twenty-over game',
    caption: 'Figure 2: First-innings totals form two clearly separated peaks, one for each format. The fifty-over median sits at 250 runs against 151 for the twenty-over game, which is close to the ratio of overs available.',
  },
  {
    name: 'run-rate-by-format.png',
    alt: 'Box plots of first-innings run rate split by format and by gender',
    caption: 'Figure 3: Scoring rate rises sharply as the format shortens, from about 5.1 runs per over to about 7.6. The spread within each group is wide, which shows that format sets the general level but conditions and opposition still move individual matches a long way.',
  },
  {
    name: 'runs-vs-overs.png',
    alt: 'Scatter plot of first-innings runs against overs faced with constant run-rate reference lines',
    caption: 'Figure 4: Plotting runs against overs faced separates the two formats into distinct bands, with diagonal guides marking constant scoring rates. The vertical stacks at twenty and fifty overs are innings that used the full allocation without being bowled out.',
  },
  {
    name: 'wickets-distribution.png',
    alt: 'Grouped bar chart of wickets lost in the first innings by format',
    caption: 'Figure 5: Twenty-over innings far more often close with wickets still in hand, because the clock rather than the bowling usually ends them. Fifty-over innings cluster toward the right of the chart, where sides are bowled out or nearly so.',
  },
  {
    name: 'correlation-heatmap.png',
    alt: 'Correlation matrix of the eleven numeric match features',
    caption: 'Figure 6: Run rate moves strongly with boundary share and strongly against dot-ball share, which is expected because those three describe the same scoring behaviour from different angles. The near absence of correlation between powerplay runs and run rate is more surprising and is examined in Figure 10.',
  },
  {
    name: 'matches-per-year.png',
    alt: 'Stacked bar chart of matches per year by format',
    caption: 'Figure 7: The volume of recorded international cricket grows steadily, and the twenty-over game overtakes the fifty-over game after about 2015. The final year is partial because the archive was downloaded mid-season.',
  },
  {
    name: 'scoring-trend.png',
    alt: 'Line chart of mean first-innings run rate per year for both formats with error bands',
    caption: 'Figure 8: Average scoring rates have drifted upward in both formats across two decades, with shaded bands showing the uncertainty in each yearly average. The twenty-over line is far more volatile because fewer matches and shorter innings make each year’s mean less stable.',
  },
  {
    name: 'boundary-and-dots.png',
    alt: 'Two histograms comparing boundary share and dot-ball share across formats',
    caption: 'Figure 9: Roughly half of a twenty-over total arrives in fours and sixes against about 42 percent in the fifty-over game. The dot-ball panel mirrors this, with the longer format accepting far more deliveries that yield nothing.',
  },
  {
    name: 'powerplay-vs-total.png',
    alt: 'Scatter plot of powerplay runs against the final first-innings total with fitted lines',
    caption: 'Figure 10: A strong powerplay is only loosely connected to the eventual total, with a correlation of about 0.48 across all matches. The wide vertical scatter at every powerplay score shows that many fast starts were not converted and many slow starts recovered.',
  },
  {
    name: 'toss-and-result.png',
    alt: 'Two bar charts showing toss outcomes and the balance of defended and chased totals',
    caption: 'Figure 11: Captains who won the toss went on to win the match almost exactly half the time, whichever decision they made. The right-hand panel shows that totals are defended and chased at close to even rates in both formats.',
  },
  {
    name: 'top-venues.png',
    alt: 'Horizontal bar chart of the fifteen most used venues',
    caption: 'Figure 12: A small group of grounds hosts a disproportionate share of the fixtures, led by neutral and tournament venues. Name variants such as the two spellings of one Dhaka ground were merged during cleaning before this chart was drawn.',
  },
  {
    name: 'top-teams.png',
    alt: 'Horizontal bar chart of the fifteen teams appearing most often',
    caption: 'Figure 13: The established full-member nations dominate the fixture list by a wide margin. The long tail of associate nations beyond these fifteen is the main reason the dataset contains 111 distinct teams.',
  },
  {
    name: 'weather-vs-scoring.png',
    alt: 'Line chart of mean run rate against bands of match-day maximum temperature',
    caption: 'Figure 14: Match-day temperature collected from the weather API moves the scoring rate very little within either format. The lines stay close to flat across a thirty-degree range, which argues against heat being a major driver of scoring.',
  },
  {
    name: 'clean-sample-table.png',
    alt: 'Table image showing seven rows of the cleaned match dataset',
    caption: 'Figure 15: Seven rows of the finished analysis table, showing the derived scoring measures and the result label beside the original match details. Every column in this file is populated for all 6,066 rows.',
  },
]

// --------------------------------------------------------------------------

function App() {
  const [activeTab, setActiveTab] = useState('Introduction')
  const [eda, setEda] = useState(null)
  const [unsupervised, setUnsupervised] = useState(null)
  const [supervised, setSupervised] = useState(null)
  const [reportError, setReportError] = useState('')

  useEffect(() => {
    let cancelled = false
    const load = (file) =>
      fetch(figureUrl(file)).then((response) => {
        if (!response.ok) throw new Error(`${file} returned ${response.status}`)
        return response.json()
      })

    Promise.all([
      load('eda-summary.json'),
      load('clustering-pca-results.json'),
      load('supervised-results.json'),
    ])
      .then(([edaData, unsupervisedData, supervisedData]) => {
        if (cancelled) return
        setEda(edaData)
        setUnsupervised(unsupervisedData)
        setSupervised(supervisedData)
      })
      .catch(() => {
        if (!cancelled) setReportError('The computed results could not be loaded.')
      })

    return () => { cancelled = true }
  }, [])

  const pending = (label) => <p role="status">{reportError || `Loading ${label}.`}</p>

  // ------------------------------------------------------------------ intro

  const renderIntroduction = () => (
    <section className="content-panel">
      <header className="assignment-heading">
        <span className="eyebrow">The topic</span>
        <h2>Setting a target and chasing it down</h2>
        <p>What decides a cricket match, and how much of it is settled before play begins.</p>
      </header>

      <div className="text-block">
        {introParagraphs.slice(0, 2).map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
      </div>

      <div className="intro-gallery">
        <figure className="intro-figure">
          <img src={cricketPlayer} alt="A batter waiting at the crease for the next delivery" />
          <figcaption>
            A batter faces every delivery alone, judging length and line in under half a second.
            The accumulation of those individual judgements across an innings is what produces a total.
          </figcaption>
        </figure>
        <figure className="intro-figure">
          <img src={cricketCelebration} alt="Cricket players celebrating a wicket together" />
          <figcaption>
            Wickets shift a match more sharply than runs do, because they remove a side&apos;s ability to accelerate later.
            A team that keeps wickets in hand retains options that a team rebuilding does not have.
          </figcaption>
        </figure>
      </div>

      <div className="text-block">
        {introParagraphs.slice(2).map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
      </div>

      <div className="questions-box">
        <h3>Ten questions this project sets out to answer</h3>
        <ol>{questions.map((question) => <li key={question}>{question}</li>)}</ol>
      </div>
    </section>
  )

  // -------------------------------------------------------------- data prep

  const renderDataPrep = () => (
    <section className="content-panel assignment-panel">
      <header className="assignment-heading">
        <span className="eyebrow">Gathering, cleaning, exploring</span>
        <h2>Data Preparation and Exploratory Analysis</h2>
        <p>Where the data came from, what was wrong with it, and what it looks like once repaired.</p>
      </header>

      <section className="assignment-section">
        <h3>Why this data, and where it came from</h3>
        <p>
          The questions on the Introduction tab are about what actually happens across many
          completed matches, so a handful of memorable games would not answer them. Three sources
          were combined: a bulk archive of ball-by-ball scorecards that supplies the match record
          itself, a live REST API that supplies currently running fixtures, and a second REST API
          that supplies the weather at each host city on the day of the match. The first provides
          the volume and the outcome labels, the second shows the same measurements being taken on
          live matches, and the third tests whether conditions explain any of the scoring.
        </p>

        {eda ? (
          <div className="summary-grid">
            <div className="summary-card"><span>Matches after cleaning</span><strong>{eda.clean_rows.toLocaleString()}</strong></div>
            <div className="summary-card"><span>Seasons covered</span><strong>{eda.date_range[0].slice(0, 4)}{'–'}{eda.date_range[1].slice(0, 4)}</strong></div>
            <div className="summary-card"><span>Venues / teams</span><strong>{eda.venues} / {eda.teams}</strong></div>
          </div>
        ) : pending('the dataset summary')}

        <div className="source-grid">
          <div className="source-card">
            <span className="source-type">Bulk download</span>
            <h3>Cricsheet ball-by-ball archives</h3>
            <p>
              Every delivery of 6,872 one-day and twenty-over internationals, published as one
              scorecard file and one metadata file per match. These archives are the raw source
              behind every number on this site.
            </p>
            <DataLinks items={[
              { href: 'https://cricsheet.org/downloads/', label: 'Cricsheet downloads page' },
              { href: 'https://cricsheet.org/downloads/odis_male_csv2.zip', label: 'Raw: ODI (men)' },
              { href: 'https://cricsheet.org/downloads/odis_female_csv2.zip', label: 'Raw: ODI (women)' },
              { href: 'https://cricsheet.org/downloads/t20s_male_csv2.zip', label: 'Raw: T20 (men)' },
            ]} />
          </div>

          <div className="source-card">
            <span className="source-type">REST API</span>
            <h3>CricAPI current matches</h3>
            <p>
              Returns the fixtures in progress at the moment of the request, with live scores and
              venue details. Access requires a free key, which is read from an environment
              variable and never stored in the repository.
            </p>
            <div className="api-box">
              <h3>Endpoint and example request</h3>
              <p><code>GET https://api.cricapi.com/v1/currentMatches?apikey=&lt;KEY&gt;&amp;offset=0</code></p>
              <p className="api-note">
                Returns JSON with a <em>data</em> array, in which each element carries
                {' '}<em>name</em>, <em>venue</em>, <em>teams</em>, <em>matchType</em> and a
                {' '}<em>score</em> array holding one entry per innings.
              </p>
            </div>
            <DataLinks items={[
              { href: dataUrl('cricapi-current-snapshot.csv'), label: 'Snapshot returned by this endpoint', download: true },
            ]} />
          </div>

          <div className="source-card">
            <span className="source-type">REST API</span>
            <h3>Open-Meteo archive and geocoding</h3>
            <p>
              Supplies the maximum temperature, minimum temperature and rainfall recorded at each
              host city on each match date. No key is required, so this part of the pipeline can
              be reproduced by anyone.
            </p>
            <div className="api-box">
              <h3>Endpoints and example requests</h3>
              <p><code>GET https://geocoding-api.open-meteo.com/v1/search?name=Mumbai&amp;count=1</code></p>
              <p><code>GET https://archive-api.open-meteo.com/v1/archive?latitude=19.07&amp;longitude=72.87&amp;start_date=2015-01-01&amp;end_date=2015-12-31&amp;daily=temperature_2m_max,precipitation_sum&amp;timezone=UTC</code></p>
              <p className="api-note">
                The city name is resolved to coordinates first, then one archive request covers
                that city&apos;s full date range and only match days are kept.
              </p>
            </div>
            <DataLinks items={[
              { href: dataUrl('venue-weather.csv'), label: 'Weather joined to match days', download: true },
            ]} />
          </div>
        </div>
      </section>

      <section className="assignment-section">
        <h3>What the raw data looked like, and what cleaning changed</h3>
        <p>
          The archives arrive as two files per match rather than as a table, so the first step
          flattens them into one row per fixture by summing each innings from its deliveries. That
          flattened file is the raw data shown below, and it is genuinely untidy: it carries
          {eda ? ` ${eda.raw_missing_cells.toLocaleString()} ` : ' '}
          empty cells, abandoned fixtures with no winner, rain-shortened innings, matches decided
          by a revised target, and the same ground recorded under two different names.
        </p>

        <div className="raw-clean-grid">
          <Figure
            name="raw-sample-table.png"
            alt="Table image of seven raw rows with missing values marked"
            caption="Figure A: Seven rows of the flattened raw file, with empty cells marked. The gaps in winner, city and second-innings columns are what the cleaning rules below had to resolve."
          />
          <Figure
            name="clean-sample-table.png"
            alt="Table image of seven cleaned rows with no missing values"
            caption="Figure B: The same table after cleaning, with derived scoring measures and the result label added. No cell in this file is empty."
          />
        </div>

        <div className="model-section-block">
          <h4>Cleaning rules applied, in order</h4>
          <ol>
            <li>Text columns trimmed; known team-name aliases such as <em>USA</em> and <em>UAE</em> resolved to one spelling each.</li>
            <li>Venue names collapsed where one spelling is a prefix of another, which merged 133 duplicate venues and reduced the venue count from 508 to {eda ? eda.venues : '375'}.</li>
            <li>Dates parsed to a single format; any row with an unrecoverable date removed.</li>
            <li>All score columns coerced to numbers, with non-numeric entries treated as missing rather than silently set to zero.</li>
            <li>Abandoned matches, ties and matches decided by a revised rain target removed, because a first-innings total cannot be compared against a target that was later changed.</li>
            <li>Structurally impossible rows removed: negative runs, more than ten wickets, or a missing batting side.</li>
            <li>Innings cut to under 60 percent of their scheduled overs removed as rain-affected fragments rather than contests.</li>
            <li>Duplicate fixtures removed, both by match identifier and by the combination of date, teams and first-innings score.</li>
            <li>Remaining optional text fields filled from a defensible source: city taken from the venue string, absent awards recorded as <em>Not awarded</em>.</li>
            <li>Derived measures added: run rate, powerplay run rate, boundary share, dot-ball share, extras share, and the result label.</li>
            <li>Division artefacts from step 10 removed, and all share columns constrained to lie between 0 and 1.</li>
          </ol>
        </div>

        {eda ? (
          <div className="metric-strip">
            <div><span>Raw rows</span><strong>{eda.raw_rows.toLocaleString()}</strong></div>
            <div><span>Rows removed</span><strong>{eda.rows_removed.toLocaleString()} ({percent(eda.rows_removed / eda.raw_rows)})</strong></div>
            <div><span>Empty cells remaining</span><strong>{eda.clean_missing_cells}</strong></div>
          </div>
        ) : null}

        <h3>All data files</h3>
        <DataLinks items={[
          { href: dataUrl('cricsheet-matches-raw.csv'), label: 'Raw flattened matches (CSV)', download: true },
          { href: dataUrl('cricsheet-matches-clean.csv'), label: 'Cleaned matches (CSV)', download: true },
          { href: dataUrl('cricapi-current-snapshot.csv'), label: 'CricAPI snapshot (CSV)', download: true },
          { href: dataUrl('venue-weather.csv'), label: 'Venue weather (CSV)', download: true },
          { href: dataUrl('dataset-summary.json'), label: 'Dataset summary (JSON)', download: true },
        ]} />
      </section>

      <section className="assignment-section">
        <h3>Code</h3>
        <p>
          Written in Python. The pipeline uses <em>requests</em> for both APIs and the archive
          download, <em>pandas</em> and <em>NumPy</em> for flattening and cleaning, and
          <em> Matplotlib</em> for every figure. The first script below gathers and cleans; the
          second produces the fifteen exploratory figures on this tab.
        </p>
        <CodeLinks items={[
          { file: 'build_dataset.py', label: 'build_dataset.py — gather and clean' },
          { file: 'eda_cricket.py', label: 'eda_cricket.py — exploratory figures' },
          { file: 'plot_style.py', label: 'plot_style.py — shared figure styling' },
        ]} />
      </section>

      <section className="assignment-section">
        <h3>Exploring the data</h3>
        <p>
          Fifteen figures follow. They move from the condition of the data itself, through the
          distributions of the main measurements, to the relationships that later tabs model
          directly. Each thumbnail opens at full size.
        </p>
        <div className="analysis-figure-grid">
          {edaFigures.map((figure) => <Figure key={figure.name} {...figure} />)}
        </div>
      </section>

      <section className="assignment-section">
        <h3>What exploration already shows</h3>
        <p>
          Three results are visible before any model is fitted. The toss appears to be worth
          almost nothing: the captain who won it went on to win the match
          {eda ? ` ${percent(eda.toss_winner_win_rate)} ` : ' '}
          of the time, and the two possible decisions performed within two points of each other.
          Format is the dominant structure in the data, separating totals, scoring rates,
          boundary shares and dot-ball shares into two distinct populations. The powerplay is
          weaker evidence than commentary implies, correlating with the final total at only
          {eda ? ` ${eda.powerplay_correlation}` : ''}. These observations set up the grouping
          work on the Clustering tab and the prediction work on the supervised tabs.
        </p>
      </section>
    </section>
  )

  // ------------------------------------------------------------- clustering

  const renderClustering = () => {
    const results = unsupervised
    return (
      <section className="content-panel assignment-panel">
        <header className="assignment-heading">
          <span className="eyebrow">Unsupervised learning</span>
          <h2>Clustering</h2>
          <p>Letting the matches group themselves, without being told what a format is.</p>
        </header>

        <section className="assignment-section">
          <h3>Overview</h3>
          <p>
            Clustering sorts observations into groups by similarity alone, with no answer key
            supplied. It answers a different kind of question from prediction: not
            <em> what will happen</em>, but <em>are these things alike</em>. Two families of
            method are used here. <strong>Partitional</strong> clustering, of which k-means is the
            standard example, requires the number of groups to be fixed in advance; it places k
            centres, assigns every match to its nearest centre, moves each centre to the mean of
            what it captured, and repeats until nothing moves. <strong>Hierarchical</strong>
            clustering instead builds a whole tree: it begins with every match in a group of its
            own, repeatedly merges the two closest groups, and continues until one group remains.
            The number of clusters is then chosen afterwards by cutting the tree at a height.
          </p>
          <p>
            The choice of distance decides what <em>close</em> means. k-means here uses
            <strong> squared Euclidean distance</strong>, the ordinary straight-line distance,
            which asks whether two matches had similar magnitudes. The hierarchical model uses
            <strong> cosine distance</strong>, which measures the angle between two matches
            treated as vectors and ignores their overall size; two innings with the same balance
            of boundaries, dots and wickets are close under cosine even if one scored far more
            runs. Average linkage is used when merging, meaning the distance between two groups is
            the mean distance across all pairs spanning them. Because the raw columns mix run
            totals in the hundreds with ratios between zero and one, every feature is
            standardised to zero mean and unit variance first. Without that step both distance
            measures would effectively rank matches by whichever column happened to have the
            widest range.
          </p>
          <div className="analysis-figure-grid">
            <Figure
              name="cluster-map.png"
              alt="Scatter plot of matches on two principal components coloured by k-means cluster"
              caption="Figure 1: Every match placed on the first two principal components and coloured by its k-means group, with crosses marking the cluster centres. The two groups occupy clearly separate regions with only a narrow band of overlap."
            />
            <Figure
              name="dendrogram.png"
              alt="Average-linkage dendrogram built on cosine distance"
              caption="Figure 2: The hierarchical merge tree, read from the individual matches at the bottom upward to a single group at the top. The dashed line marks the height at which the tree was cut to produce two clusters."
            />
          </div>
        </section>

        <section className="assignment-section">
          <h3>Data Prep</h3>
          <p>
            Clustering requires <strong>unlabelled numeric data only</strong>. It cannot accept
            text, and it must not be shown the answer, because the entire point is to discover
            structure rather than to reproduce a category that was handed over. Every text column
            was therefore dropped rather than encoded, and so were the result label, the winning
            team, the format and the gender. Format in particular is withheld deliberately: if the
            clusters rediscover it on their own, that is evidence the measurements capture
            something real, and that test is only valid if the model never sees it.
          </p>
          <p>
            What remains is {results ? results.n_features : 11} numeric measurements describing how
            the runs were accumulated. All {results ? results.n_matches.toLocaleString() : ''} matches
            are used. Each column is then standardised, so a one-unit difference means one standard
            deviation in every direction rather than one run in one column and one percentage point
            in another.
          </p>
          <Figure
            name="clustering-input-sample.png"
            alt="Table image of six rows of the unlabelled numeric clustering input"
            caption="Figure 3: Six rows of the clustering input. There is no label column and no text column anywhere in this table, which is the requirement for an unsupervised method."
            wide
          />
          <DataLinks items={[
            { href: dataUrl('clustering-input-sample.csv'), label: 'Clustering input (CSV)', download: true },
            { href: dataUrl('cricsheet-matches-clean.csv'), label: 'Cleaned source data (CSV)', download: true },
            { href: dataUrl('cricsheet-matches-raw.csv'), label: 'Raw source data (CSV)', download: true },
            { href: 'https://cricsheet.org/downloads/', label: 'Original raw archives' },
          ]} />
        </section>

        <section className="assignment-section">
          <h3>Code</h3>
          <p>
            Written in Python, using <em>scikit-learn</em> for k-means, the silhouette scores and
            the standardiser, and <em>SciPy</em> for the cosine distance matrix and the
            average-linkage tree.
          </p>
          <CodeLinks items={[
            { file: 'clustering_pca.py', label: 'clustering_pca.py — clustering, PCA and SVD' },
            { file: 'build_dataset.py', label: 'build_dataset.py — upstream data pipeline' },
          ]} />
        </section>

        <section className="assignment-section">
          <h3>Results</h3>
          {results ? (
            <>
              <p>
                k-means was run for every k from 2 to 8. The three headline values requested were
                k = 2, k = 3 and k = 4, scoring{' '}
                {Object.entries(results.headline_k).map(([k, score], index, all) => (
                  <span key={k}>{index > 0 ? (index === all.length - 1 ? ' and ' : ', ') : ''}
                    <strong>{score.toFixed(3)}</strong> at k = {k}</span>
                ))}
                {' '}on the silhouette measure. The silhouette compares how close each match sits
                to its own group against how close it sits to the nearest rival group, on a scale
                from -1 to 1, so higher is better. It falls away steadily as k grows, which says
                that splitting the data more finely produces groups that are no longer
                well separated.
              </p>
              <div className="metric-strip">
                <div><span>Best k (k-means)</span><strong>{results.kmeans_best_k}</strong></div>
                <div><span>Best k (hierarchical)</span><strong>{results.hierarchical_best_k}</strong></div>
                <div><span>Agreement between them</span><strong>{results.adjusted_rand_index.toFixed(3)}</strong></div>
              </div>
              <p>
                The hierarchical model, using cosine distance on a format-balanced sample of{' '}
                {results.hierarchical_sample_size.toLocaleString()} matches, independently reached
                the same answer: its silhouette also peaks at k = {results.hierarchical_best_k},
                at {results.hierarchical_best_silhouette.toFixed(3)}. The dendrogram shows the
                same conclusion visually, splitting into two long branches that join only at the
                very top of the tree. Agreement between the two solutions was measured with the
                adjusted Rand index, which scores 1 for identical groupings and 0 for the
                agreement expected by chance; the two methods scored{' '}
                <strong>{results.adjusted_rand_index.toFixed(3)}</strong>. Two methods using
                different distance measures and different algorithms almost never agree that
                closely unless the structure they are describing is genuinely present.
              </p>
              <div className="analysis-figure-grid">
                <Figure
                  name="silhouette-comparison.png"
                  alt="Line chart of silhouette score against number of clusters for both methods"
                  caption="Figure 4: Silhouette scores for both methods across k = 2 to 8, with the chosen k marked. Both curves fall monotonically after k = 2, so no larger number of clusters is supported."
                />
                <Figure
                  name="silhouette-profile.png"
                  alt="Silhouette width of individual matches grouped by cluster"
                  caption="Figure 5: The silhouette width of individual matches, sorted within each cluster. Almost all values are positive, meaning very few matches sit closer to the other group than to their own."
                />
                <Figure
                  name="cluster-profiles.png"
                  alt="Heatmap of mean standardised feature values within each cluster"
                  caption="Figure 6: What actually separates the two clusters, measured in standard deviations from the overall mean. Cluster 0 is long, slow and dot-heavy; cluster 1 is short, fast and boundary-heavy."
                  wide
                />
                <Figure
                  name="cluster-composition.png"
                  alt="Stacked bars showing the format mix and result mix inside each cluster"
                  caption="Figure 7: The format and result composition of each cluster, neither of which was available when fitting. The format split is almost perfect, while the result split sits near even in both clusters."
                  wide
                />
              </div>
              <p>
                Comparing the clusters against the withheld information makes their meaning plain.
                Cluster 0 holds {results.cluster_sizes['0'].toLocaleString()} matches averaging{' '}
                {results.cluster_mean_runs['0']} runs, and cluster 1 holds{' '}
                {results.cluster_sizes['1'].toLocaleString()} averaging{' '}
                {results.cluster_mean_runs['1']}. Checked against the format column the model never
                received, the groups correspond almost exactly to the fifty-over and twenty-over
                games. Checked against the result label, both clusters are close to an even split
                between totals defended and totals chased, at{' '}
                {percent(results.cluster_defended_rate['0'])} and{' '}
                {percent(results.cluster_defended_rate['1'])}.
              </p>
            </>
          ) : pending('the clustering results')}
        </section>

        <section className="assignment-section">
          <h3>Conclusions</h3>
          <p>
            The strongest natural division in international cricket is the format itself, and it
            is strong enough that two different methods recover it without ever being told it
            exists. This is a meaningful result rather than a trivial one: it says the fifty-over
            and twenty-over games are not simply long and short versions of one activity but
            genuinely distinct competitions, separable purely from the shape of an innings. The
            separation is driven by how runs were accumulated rather than by how many were scored,
            since the measurements that carry it are scoring rate, boundary share and dot-ball
            share. The near-perfect agreement between a magnitude-based distance and an
            angle-based distance makes it unlikely that this is an artefact of one modelling choice.
          </p>
          <p>
            Just as informative is what clustering did <em>not</em> find. No grouping emerged that
            corresponds to winning or losing: both clusters split almost evenly between totals
            defended and totals chased. In other words, the natural structure of the data is about
            the <em>kind</em> of cricket being played, not about who won it. That is a useful
            negative result, because it says the match outcome is not simply a by-product of an
            obvious scoring pattern and will need a method that is actually given the answer to
            learn from. That is exactly what the Naive Bayes and Decision Tree tabs do.
          </p>
        </section>
      </section>
    )
  }

  // -------------------------------------------------------------------- PCA

  const renderPca = () => {
    const results = unsupervised
    return (
      <section className="content-panel assignment-panel">
        <header className="assignment-heading">
          <span className="eyebrow">Dimensionality reduction</span>
          <h2>PCA and SVD</h2>
          <p>Replacing eleven overlapping measurements with a handful of independent ones.</p>
        </header>

        <section className="assignment-section">
          <h3>Overview</h3>
          <p>
            Principal Component Analysis replaces the original variables with a new set of
            directions called principal components. The components are built so that the first
            captures as much of the variation in the data as any single direction can, the second
            captures as much of what remains as possible while sitting at right angles to the
            first, and so on. Because they are mutually perpendicular, the components do not
            repeat each other&apos;s information, which is the central advantage over the original
            columns.
          </p>
          <p>
            Underneath this sits an <strong>eigenvalue</strong> and <strong>eigenvector</strong>
            problem. The relationships among the standardised columns are summarised in a
            correlation matrix. An eigenvector of that matrix is a direction that the matrix
            stretches without rotating, and its eigenvalue is the factor by which it stretches.
            In this setting the eigenvectors <em>are</em> the principal components, giving the
            direction, and each eigenvalue <em>is</em> the variance captured along that direction.
            Ordering the eigenvalues from largest to smallest therefore orders the components from
            most to least informative, and dividing each eigenvalue by their total gives the share
            of variance that component explains. Because the data was standardised, the
            eigenvalues sum to the number of variables, and an eigenvalue above 1 marks a
            component carrying more information than any single original column.
          </p>
          <p>
            <strong>Dimensionality reduction</strong> means keeping only the leading components and
            discarding the rest. High-dimensional data causes real difficulties. Distances become
            less discriminating as dimensions multiply, so neighbours and strangers start to look
            equally far apart and methods that rely on distance quietly degrade. The number of
            observations needed to cover a space grows explosively with its dimension, so models
            overfit. Correlated columns duplicate the same underlying signal and give it undue
            weight. Nothing can be plotted beyond three dimensions, so the data cannot be
            inspected directly. Reducing the dimensions addresses all four at once, at the cost of
            discarding some information, and the scree plot is how that trade is judged.
          </p>
          <div className="analysis-figure-grid">
            <Figure
              name="pca-scree.png"
              alt="Scree plot of variance explained per component with a cumulative line"
              caption="Figure 1: The share of variance captured by each component, with the running total on the right axis. The first two components carry two thirds of the variation and five are needed to pass ninety percent."
            />
            <Figure
              name="pca-biplot.png"
              alt="PCA biplot showing matches as points and original features as arrows"
              caption="Figure 2: Matches drawn on the first two components, with arrows showing the direction each original measurement points. Arrows close together describe measurements that tend to rise and fall together."
            />
          </div>
        </section>

        <section className="assignment-section">
          <h3>Data Prep</h3>
          <p>
            PCA requires a complete numeric matrix with no missing values and no text, and it is
            unsupervised, so no label is supplied. It is also highly sensitive to scale: because it
            maximises variance, any column measured in large units would dominate the leading
            component simply by being large. The same{' '}
            {results ? results.n_features : 11}-column standardised matrix used for clustering is
            therefore used here, which is equivalent to analysing the correlation matrix rather
            than the covariance matrix.
          </p>
          <Figure
            name="clustering-input-sample.png"
            alt="Table image of six rows of the numeric PCA input"
            caption="Figure 3: The same unlabelled numeric matrix used for clustering, which is the required input form for PCA. Standardising before decomposition is what stops the run-total columns from absorbing the first component."
            wide
          />
          <DataLinks items={[
            { href: dataUrl('clustering-input-sample.csv'), label: 'PCA input (CSV)', download: true },
            { href: dataUrl('cricsheet-matches-clean.csv'), label: 'Cleaned source data (CSV)', download: true },
            { href: dataUrl('cricsheet-matches-raw.csv'), label: 'Raw source data (CSV)', download: true },
            { href: 'https://cricsheet.org/downloads/', label: 'Original raw archives' },
          ]} />
        </section>

        <section className="assignment-section">
          <h3>Code</h3>
          <p>
            Written in Python. <em>scikit-learn</em> provides the PCA implementation and the
            standardiser, and <em>NumPy</em> provides the singular value decomposition used to
            confirm the relationship between singular values and eigenvalues.
          </p>
          <CodeLinks items={[
            { file: 'clustering_pca.py', label: 'clustering_pca.py — clustering, PCA and SVD' },
          ]} />
        </section>

        <section className="assignment-section">
          <h3>Results</h3>
          {results ? (
            <>
              <div className="metric-strip">
                <div><span>PC1 + PC2 variance</span><strong>{percent(results.pc1_pc2_variance)}</strong></div>
                <div><span>Components for 90%</span><strong>{results.components_for_90_percent} of {results.n_features}</strong></div>
                <div><span>Eigenvalues above 1</span><strong>{results.eigenvalues_above_one}</strong></div>
              </div>
              <p>
                The first component explains{' '}
                {percent(results.explained_variance_ratio[0])} of the variation and the second{' '}
                {percent(results.explained_variance_ratio[1])}, so a two-dimensional picture
                retains {percent(results.pc1_pc2_variance)} of everything in the original eleven
                columns. Reaching ninety percent takes{' '}
                {results.components_for_90_percent} components, which is a genuine reduction from{' '}
                {results.n_features} while discarding only a tenth of the information.{' '}
                {results.eigenvalues_above_one} eigenvalues exceed 1, and by the common rule of
                thumb those are the components worth keeping. That no single component dominates is
                itself the sign of a well-scaled problem; a first component near 99 percent would
                indicate one unstandardised column swamping the rest.
              </p>
              <p>
                Reading the biplot is a matter of reading the arrows. Each arrow points in the
                direction in which that original measurement increases, its length shows how
                strongly it loads on the two components displayed, and the angle between two
                arrows reflects their correlation: a small angle means they rise together, a
                straight angle means one rises as the other falls, and a right angle means they
                are unrelated. Here the run-rate arrows and the boundary-share arrow point one
                way while the dot-ball arrow points almost directly opposite, which is the visual
                form of the correlations seen in the exploratory heatmap. The innings-length and
                total-runs arrows point upward, nearly perpendicular to the scoring-rate arrows,
                showing that how long an innings lasted and how fast it was scored are close to
                independent.
              </p>
              <p>
                The two components therefore have readable meanings. PC1 is a
                <strong> tempo</strong> axis, loading positively on run rate and boundaries and
                negatively on dot balls. PC2 is a <strong>volume</strong> axis, loading on overs
                faced and runs scored in both innings. That matches the cluster structure exactly:
                the format split that both clustering methods found is a split along these two
                axes, which is why the cluster scatter on the previous tab separates so cleanly.
              </p>
              <div className="analysis-figure-grid">
                <Figure
                  name="pca-loadings.png"
                  alt="Heatmap of feature loadings on the first four principal components"
                  caption="Figure 4: How strongly each original measurement contributes to the first four components. The alternating signs on PC1 confirm it contrasts fast, boundary-driven innings against slow, dot-heavy ones."
                  wide
                />
                <Figure
                  name="svd-spectrum.png"
                  alt="Singular values of the centred matrix beside the eigenvalues of the correlation matrix"
                  caption="Figure 5: The singular values from the decomposition beside the eigenvalues they produce. Each eigenvalue is the square of its singular value divided by one less than the number of matches, which is the algebraic link between SVD and PCA."
                  wide
                />
              </div>
              <p>
                Singular value decomposition factorises the centred data matrix directly into
                three parts, and it is how PCA is computed in practice because it is numerically
                more stable than forming the correlation matrix first. The connection is exact:
                squaring each singular value and dividing by one less than the number of matches
                reproduces the eigenvalues plotted beside them. The spectrum falls away smoothly
                rather than collapsing after the first value, which is the same conclusion the
                scree plot reaches by a different route.
              </p>
            </>
          ) : pending('the PCA results')}
        </section>

        <section className="assignment-section">
          <h3>Conclusions</h3>
          <p>
            The eleven measurements describing an innings are not eleven independent facts; they
            are closer to five, and largely to two. Almost all of what distinguishes one match
            from another can be expressed as a combination of how fast the runs came and how many
            of them there were in total. For the topic, this says that the vocabulary cricket uses
            to describe an innings is highly redundant, and that run rate, boundary share and
            dot-ball percentage are three ways of describing a single underlying quantity, the
            tempo of the innings.
          </p>
          <p>
            Practically, this justifies the small feature set used by the later models and
            explains why they do not need dozens of inputs. It also confirms the clustering result
            from an entirely independent direction: the format separation found there appears here
            as the dominant pair of components, which means the same structure is visible whether
            one asks how matches group or how they vary. One limitation is worth stating plainly.
            PCA finds only directions that are straight lines through the data, so any relationship
            that bends is invisible to it, and the roughly ten percent of variation discarded here
            is not guaranteed to be noise.
          </p>
        </section>
      </section>
    )
  }

  // ----------------------------------------------------------- naive bayes

  const renderNaiveBayes = () => {
    const results = supervised
    const nb = results?.naive_bayes
    return (
      <section className="content-panel assignment-panel">
        <header className="assignment-heading">
          <span className="eyebrow">Supervised learning</span>
          <h2>Naive Bayes</h2>
          <p>Predicting the result of a match from the first innings alone.</p>
        </header>

        <section className="assignment-section">
          <h3>Overview</h3>
          <p>
            Naive Bayes is a probabilistic classifier built on Bayes&apos; theorem. For a match it
            asks a simple question: given everything observed in the first innings, which outcome
            is more probable? It answers by combining how common each outcome is in general with
            how typical the observed measurements are of each outcome. Formally it computes the
            probability of each class given the evidence as proportional to the probability of the
            class multiplied by the probability of the evidence given that class, and assigns
            whichever class scores higher.
          </p>
          <p>
            The <strong>naive</strong> part is an assumption: that every feature is independent of
            every other once the class is known. That assumption is plainly false here, since run
            rate and boundary share are strongly related, and PCA on the previous tab quantified
            exactly how related. The method is nonetheless used widely because it is fast, needs
            very little training data, handles many features comfortably, and is often accurate
            even when its assumption is violated, because it only needs to rank the classes
            correctly rather than to estimate their probabilities precisely. It is a standard
            baseline for text classification, spam filtering, document categorisation and medical
            triage.
          </p>
          <p>
            The variants differ in what they assume about the features themselves.
            <strong> Multinomial Naive Bayes</strong>, the standard form used here, models each
            feature as a count drawn from a multinomial distribution, which is why it is the usual
            choice for word frequencies in a document and why it requires every input to be
            non-negative. <strong>Bernoulli Naive Bayes</strong> instead treats every feature as a
            binary on/off indicator and models the probability that each is switched on for each
            class. The key difference is that Bernoulli explicitly uses the <em>absence</em> of a
            feature as evidence, whereas multinomial simply records a count of zero and moves on;
            for text, Bernoulli asks whether a word appears at all while multinomial asks how
            often. <strong>Gaussian Naive Bayes</strong> is included as a third comparison and
            assumes each feature follows a normal distribution within each class, which suits
            continuous measurements such as run rate.
          </p>
          <div className="analysis-figure-grid">
            <Figure
              name="class-separation.png"
              alt="Four histograms comparing the two outcomes across key measurements"
              caption="Figure 1: The distribution of four key measurements within each outcome, which is precisely what Naive Bayes estimates during training. Run rate separates the two outcomes well while wickets lost separates them hardly at all."
              wide
            />
            <Figure
              name="nb-roc-curves.png"
              alt="ROC curves for the three Naive Bayes variants"
              caption="Figure 2: Each variant's trade-off between catching true results and raising false alarms, against the diagonal that random guessing would produce. All three sit well above the diagonal, so all three carry genuine signal."
            />
          </div>
        </section>

        <section className="assignment-section">
          <h3>Data Prep</h3>
          <p>
            Supervised learning requires <strong>labelled</strong> data: every row must carry the
            answer the model is meant to learn. The label here is whether the first-innings total
            was <em>Defended</em> or <em>Chased</em>, derived by comparing the winning team against
            the team that batted first. Unlabelled rows cannot be used at all, which is why
            abandoned matches and ties were removed during cleaning.
          </p>
          <p>
            Choosing the features matters as much as choosing the label. Every second-innings
            column was deliberately excluded, because those columns describe the chase itself and
            a model given them would be reading the answer off its own input rather than
            predicting it. What remains is {results ? results.n_features : 14} measurements
            available at the innings break: seven counts, four rates, and three context
            indicators for format, gender and whether the toss winner chose to bat.
            scikit-learn&apos;s Multinomial Naive Bayes also requires numeric, non-negative input,
            so the rate columns were rescaled onto the range 0 to 1 using limits learned from the
            training data only. The Bernoulli model required a different preparation again: each
            column was split at its training-set median into above-typical and at-or-below-typical.
          </p>
          <p>
            The data was then split into a <strong>training set</strong> used to build the model
            and a <strong>testing set</strong> used only to measure it, in a 70/30 stratified
            split. The two must be <strong>disjoint</strong>, sharing no row, for a simple reason:
            a model can memorise rows it has seen, so measuring it on training data reports how
            well it remembers rather than how well it generalises. A model tested on its own
            training data can look excellent and still fail completely on a new match. Stratifying
            keeps the same proportion of each outcome in both halves, so the test set is a fair
            sample rather than an accidentally lopsided one. The split was verified to share zero
            rows.
          </p>
          <div className="raw-clean-grid">
            <Figure
              name="supervised-data-sample.png"
              alt="Table image showing labelled rows with the label column first"
              caption="Figure 3: Labelled rows as supplied to the model, with the answer in the leading column. Every row carries its outcome, which is what separates supervised from unsupervised data."
              wide
            />
            <Figure
              name="train-test-split.png"
              alt="Bar charts showing the sizes of the training and testing sets and their class balance"
              caption="Figure 4: The 70/30 split and the class balance within each half. The two sets share no match, and both preserve the same near-even division between the outcomes."
              wide
            />
          </div>
          {results ? (
            <div className="metric-strip">
              <div><span>Training rows</span><strong>{results.train_rows.toLocaleString()}</strong></div>
              <div><span>Testing rows</span><strong>{results.test_rows.toLocaleString()}</strong></div>
              <div><span>Rows in both</span><strong>{results.overlapping_rows}</strong></div>
            </div>
          ) : null}
          <DataLinks items={[
            { href: dataUrl('supervised-train.csv'), label: 'Training set (CSV)', download: true },
            { href: dataUrl('supervised-test.csv'), label: 'Testing set (CSV)', download: true },
            { href: dataUrl('cricsheet-matches-clean.csv'), label: 'Cleaned source data (CSV)', download: true },
            { href: dataUrl('cricsheet-matches-raw.csv'), label: 'Raw source data (CSV)', download: true },
            { href: 'https://cricsheet.org/downloads/', label: 'Original raw archives' },
          ]} />
        </section>

        <section className="assignment-section">
          <h3>Code</h3>
          <p>
            Written in Python, using <em>scikit-learn</em> for all three Naive Bayes variants, the
            train/test split, the rescaling and the evaluation measures.
          </p>
          <CodeLinks items={[
            { file: 'supervised_models.py', label: 'supervised_models.py — Naive Bayes and Decision Trees' },
            { file: 'build_dataset.py', label: 'build_dataset.py — upstream data pipeline' },
          ]} />
        </section>

        <section className="assignment-section">
          <h3>Results</h3>
          {nb ? (
            <>
              <div className="metric-strip">
                <div><span>Multinomial NB</span><strong>{percent(nb['Multinomial NB'].accuracy)}</strong></div>
                <div><span>Bernoulli NB</span><strong>{percent(nb['Bernoulli NB'].accuracy)}</strong></div>
                <div><span>Gaussian NB</span><strong>{percent(nb['Gaussian NB'].accuracy)}</strong></div>
              </div>
              <p>
                The required multinomial model reached{' '}
                <strong>{percent(nb['Multinomial NB'].accuracy)}</strong> accuracy on the held-out
                testing set. The right comparison is not zero but the majority-class baseline of{' '}
                {percent(results.majority_class_baseline)}, which is what guessing the more common
                outcome every time would achieve, so the model adds roughly{' '}
                {((nb['Multinomial NB'].accuracy - results.majority_class_baseline) * 100).toFixed(0)}{' '}
                points of genuine predictive power. Bernoulli reached{' '}
                {percent(nb['Bernoulli NB'].accuracy)} and Gaussian{' '}
                {percent(nb['Gaussian NB'].accuracy)}. That Gaussian edges ahead is unsurprising,
                since most of these features are continuous measurements rather than counts, and
                that Bernoulli trails slightly is also expected, since reducing each measurement to
                above or below its median throws away the magnitude.
              </p>
              <Figure
                name="nb-confusion-matrices.png"
                alt="Three confusion matrices, one per Naive Bayes variant"
                caption="Figure 5: Confusion matrices for all three variants, with counts and row percentages. The diagonal holds correct predictions and the off-diagonal the mistakes, broken down by which outcome was missed."
                wide
              />
              <p>
                The confusion matrices show where the errors fall. For the multinomial model,
                of {(nb['Multinomial NB'].confusion_matrix[0][0] + nb['Multinomial NB'].confusion_matrix[0][1]).toLocaleString()}{' '}
                matches that were actually chased down,{' '}
                {nb['Multinomial NB'].confusion_matrix[0][0].toLocaleString()} were identified
                correctly, while of{' '}
                {(nb['Multinomial NB'].confusion_matrix[1][0] + nb['Multinomial NB'].confusion_matrix[1][1]).toLocaleString()}{' '}
                totals that were actually defended,{' '}
                {nb['Multinomial NB'].confusion_matrix[1][1].toLocaleString()} were identified
                correctly. The model is noticeably better at recognising a total that will be
                chased than one that will be defended, which makes sense: a low or slowly scored
                total is a clear signal, whereas a strong total can still be overhauled by a good
                chase and nothing in the first innings reveals that. Area under the ROC curve was{' '}
                {nb['Multinomial NB'].roc_auc.toFixed(3)} for the multinomial model, and five-fold
                cross-validation on the training data gave{' '}
                {percent(nb['Multinomial NB'].cv_mean)} with a standard deviation of only{' '}
                {(nb['Multinomial NB'].cv_std * 100).toFixed(1)} points, so the headline figure is
                stable rather than a lucky split.
              </p>
            </>
          ) : pending('the Naive Bayes results')}
        </section>

        <section className="assignment-section">
          <h3>Conclusions</h3>
          <p>
            The outcome of an international cricket match can be anticipated at better than seven
            in ten from the first innings alone, before the chase has begun. For the topic this is
            a substantial finding, because it means a first-innings total is not merely a number
            but a reasonably strong statement about what is likely to follow. It also sets a
            sensible limit: three matches in ten still went the other way, and that residue is the
            genuine uncertainty that makes the sport worth watching. Anyone claiming a cricket
            result can be called reliably at the innings break is overstating the case.
          </p>
          <p>
            The pattern of errors is as informative as the accuracy. Totals that were going to be
            chased down were easier to spot than totals that would be defended, which says that a
            weak first innings is more diagnostic than a strong one. A side that bats poorly has
            usually settled its own fate; a side that bats well has only made its opponent&apos;s
            task harder. The three variants landing within two points of each other, despite
            assuming quite different things about the data, suggests the signal is spread across
            several measurements rather than concentrated in one. That the independence assumption
            is violated and the model works anyway is a reminder that a classifier only has to
            rank the outcomes correctly, not describe the sport accurately.
          </p>
        </section>
      </section>
    )
  }

  // --------------------------------------------------------- decision trees

  const renderDecisionTrees = () => {
    const results = supervised
    const trees = results?.decision_trees
    const impurity = results?.impurity_example
    const depthStudy = results?.decision_tree_depth_study
    const treeNames = trees ? Object.keys(trees) : []
    const bestTreeName = trees
      ? treeNames.reduce((best, name) => (trees[name].accuracy > trees[best].accuracy ? name : best))
      : null
    const bestTree = bestTreeName ? trees[bestTreeName] : null
    return (
      <section className="content-panel assignment-panel">
        <header className="assignment-heading">
          <span className="eyebrow">Supervised learning</span>
          <h2>Decision Trees</h2>
          <p>A sequence of yes-or-no questions that sorts a match toward its likely result.</p>
        </header>

        <section className="assignment-section">
          <h3>Overview</h3>
          <p>
            A decision tree classifies by asking a chain of yes-or-no questions. Each internal node
            tests one feature against one threshold, each branch follows one answer, and each leaf
            carries a prediction. To classify a new match the tree is walked from the root to a
            leaf. Its great advantage over most classifiers is that the finished model is directly
            readable: the path to any prediction can be written out as a sentence, which matters in
            any setting where a decision has to be justified rather than merely made. Trees also
            accept features on different scales without standardisation and capture interactions
            between features automatically.
          </p>
          <p>
            Building a tree means choosing, at every node, which feature and which threshold to
            split on, and that choice is made by measuring <strong>impurity</strong>: how mixed
            the outcomes are within a group. A group where every match has the same outcome is
            pure; a 50/50 group is maximally impure. <strong>Gini impurity</strong> is the
            probability that two items drawn at random from the group would have different labels,
            computed as one minus the sum of the squared class proportions, and runs from 0 when
            pure to 0.5 for a balanced two-class group. <strong>Entropy</strong> measures the same
            idea in bits of information, computed as the negative sum of each proportion times its
            own base-two logarithm, running from 0 when pure to 1 for a balanced two-class group.
            The two almost always choose the same splits; Gini is marginally cheaper to compute
            because it avoids logarithms, while entropy penalises mixed nodes slightly more
            sharply.
          </p>
          <p>
            <strong>Information gain</strong> turns impurity into a decision rule. It is the
            impurity of the parent node minus the weighted average impurity of the children it
            produces, where each child is weighted by the share of rows it received. A split that
            separates the outcomes well leaves children that are purer than the parent, so the gain
            is large; a split that leaves both children as mixed as the parent gains nothing. At
            every node the algorithm evaluates every feature at every candidate threshold and keeps
            whichever produces the greatest gain, then repeats on each child. The figure below
            works one real split through the arithmetic.
          </p>
          {impurity ? (
            <p>
              Taking a concrete case from the training data: the parent node holds all{' '}
              {(impurity.left_count + impurity.right_count).toLocaleString()} training matches and
              is almost perfectly balanced between the two outcomes, so its Gini is{' '}
              {impurity.parent_gini.toFixed(4)} and its entropy is{' '}
              {impurity.parent_entropy.toFixed(4)}, both at their maximum for two classes.
              Splitting on {impurity.feature.toLowerCase()} at {impurity.threshold} sends{' '}
              {impurity.left_count.toLocaleString()} matches left, where entropy falls to{' '}
              {impurity.left_entropy.toFixed(4)}, and {impurity.right_count.toLocaleString()}{' '}
              right, where it falls to {impurity.right_entropy.toFixed(4)}. Weighting those two
              children by their size gives {impurity.weighted_child_entropy.toFixed(4)}, so the
              information gain is {impurity.parent_entropy.toFixed(4)} minus{' '}
              {impurity.weighted_child_entropy.toFixed(4)}, or{' '}
              <strong>{impurity.information_gain.toFixed(4)}</strong> bits. Measured with Gini
              instead, the weighted child impurity is{' '}
              {impurity.weighted_child_gini.toFixed(4)}, a drop of{' '}
              {(impurity.parent_gini - impurity.weighted_child_gini).toFixed(4)}. Both measures
              agree that the split is worth making, which is the usual outcome.
            </p>
          ) : null}
          <Figure
            name="impurity-example.png"
            alt="Worked example of Gini, entropy and information gain for a single split"
            caption="Figure 1: A real split from the training data worked through in full, splitting on first-innings run rate at the median. The parent node is almost perfectly balanced, so its entropy starts at its two-class maximum. The split lifts information gain to 0.0735 bits and drops the weighted Gini by 0.0501."
            wide
          />
          <p>
            It is in principle possible to build an <strong>infinite number of different trees</strong>
            {' '}from the same data, and the reason is worth stating carefully. Each continuous
            feature offers infinitely many thresholds, since run rate could be split at 6.15, at
            6.151, or at any value between; even restricting thresholds to midpoints between
            observed values leaves a number of splits that grows with the data, and those choices
            compound at every node. Features may also be reused at different depths, trees may be
            grown to any depth, and the same set of rules can be ordered in many different ways to
            produce structurally different trees that classify identically. Finding the smallest
            tree that fits a dataset is a computationally hard problem, so practical algorithms
            such as the one used here are <em>greedy</em>: they take the best split available at
            each node without reconsidering earlier choices. This is fast and usually good, but it
            gives no guarantee of the best tree overall, and it is why the three trees below differ
            despite being built from identical data.
          </p>
          <div className="analysis-figure-grid">
            <Figure
              name="dt-feature-importance.png"
              alt="Horizontal bar chart of feature importance in the best tree"
              caption="Figure 2: How much each measurement contributed to the best-performing tree's total impurity reduction. Run rate dominates, which is why it appears at the root of every tree built here."
            />
            <Figure
              name="dt-depth-curve.png"
              alt="Line chart of training and testing accuracy against maximum tree depth"
              caption="Figure 3: Training and testing accuracy as the depth limit is raised from 1 to 20. The training line climbs toward perfection while the testing line peaks early and then declines, which is overfitting made visible."
            />
          </div>
        </section>

        <section className="assignment-section">
          <h3>Data Prep</h3>
          <p>
            Decision trees are a supervised method, so they need <strong>labelled</strong> data in
            exactly the same sense as Naive Bayes: every row carries the <em>Defended</em> or
            <em> Chased</em> answer the tree is meant to learn. Unlabelled rows are unusable. The
            identical {results ? results.n_features : 14}-feature design matrix is used, with all
            second-innings columns excluded for the same reason as before, so that the comparison
            between the two methods is fair.
          </p>
          <p>
            Trees need less preparation than Naive Bayes because they are insensitive to scale: a
            threshold test does not care whether a column runs from 0 to 1 or from 0 to 500, so no
            rescaling or binarisation was applied. scikit-learn&apos;s implementation does require
            numeric input, so the format and gender columns were encoded as 0/1 indicators. The
            same 70/30 stratified split into a <strong>training set</strong> and a
            <strong> testing set</strong> is reused, with the same random seed, so both methods see
            exactly the same rows. The two sets must be <strong>disjoint</strong> because a tree
            grown deep enough can memorise its training data perfectly, reaching
            {depthStudy ? ` ${percent(depthStudy.deep_train_accuracy)} ` : ' '}
            training accuracy while performing far worse on unseen matches. Figure 3 above shows
            precisely that gap opening, and it is only visible because the test rows were held back.
          </p>
          <div className="raw-clean-grid">
            <Figure
              name="supervised-data-sample.png"
              alt="Table image showing labelled rows with the label column first"
              caption="Figure 4: The labelled input, identical to the table used for Naive Bayes. Keeping the two methods on the same rows is what makes their accuracies directly comparable."
              wide
            />
            <Figure
              name="train-test-split.png"
              alt="Bar charts showing training and testing set sizes and class balance"
              caption="Figure 5: The same disjoint, stratified 70/30 split reused here. No match appears in both halves, which is what makes the reported accuracy an honest estimate."
              wide
            />
          </div>
          <DataLinks items={[
            { href: dataUrl('supervised-train.csv'), label: 'Training set (CSV)', download: true },
            { href: dataUrl('supervised-test.csv'), label: 'Testing set (CSV)', download: true },
            { href: dataUrl('cricsheet-matches-clean.csv'), label: 'Cleaned source data (CSV)', download: true },
            { href: dataUrl('cricsheet-matches-raw.csv'), label: 'Raw source data (CSV)', download: true },
            { href: 'https://cricsheet.org/downloads/', label: 'Original raw archives' },
          ]} />
        </section>

        <section className="assignment-section">
          <h3>Code</h3>
          <p>
            Written in Python, using <em>scikit-learn</em> for the tree implementation, the
            impurity criteria, the plotting of each tree and the evaluation measures. The worked
            Gini and entropy example in Figure 1 is computed directly with <em>NumPy</em> rather
            than read out of the library, so the arithmetic can be checked.
          </p>
          <CodeLinks items={[
            { file: 'supervised_models.py', label: 'supervised_models.py — Naive Bayes and Decision Trees' },
            { file: 'build_dataset.py', label: 'build_dataset.py — upstream data pipeline' },
          ]} />
        </section>

        <section className="assignment-section">
          <h3>Results</h3>
          {trees ? (
            <>
              <p>
                Three trees were built from the same training data, differing in their impurity
                criterion and in how far they were allowed to grow. Tree A uses Gini and stops at
                depth 3. Tree B uses entropy and stops at depth 4. Tree C uses Gini, is allowed to
                reach depth 6, and requires at least 40 matches in every leaf.
              </p>
              <div className="metric-strip">
                {treeNames.map((name) => (
                  <div key={name}>
                    <span>{name.split(' - ')[0]}</span>
                    <strong>{percent(trees[name].accuracy)}</strong>
                  </div>
                ))}
              </div>
              <div className="analysis-figure-grid">
                <Figure
                  name="dt-tree-a-gini-depth3.png"
                  alt="Decision tree diagram using Gini impurity limited to depth three"
                  caption="Figure 6: Tree A, the shallowest and most readable of the three, with eight leaves. It splits first on run rate, then on runs scored, which is the pattern every tree here repeats."
                  wide
                />
                <Figure
                  name="dt-tree-b-entropy-depth4.png"
                  alt="Decision tree diagram using entropy limited to depth four"
                  caption="Figure 7: Tree B, grown one level deeper using entropy rather than Gini. The extra depth nearly doubles the number of leaves without improving accuracy on unseen matches."
                  wide
                />
                <Figure
                  name="dt-tree-c-gini-depth6.png"
                  alt="Decision tree diagram using Gini to depth six with a minimum leaf size"
                  caption="Figure 8: Tree C, allowed to reach depth 6 but required to keep at least 40 matches in every leaf. The minimum leaf size is what stops it from fragmenting into tiny unreliable groups."
                  wide
                />
              </div>
              <Figure
                name="dt-confusion-matrices.png"
                alt="Three confusion matrices, one for each decision tree"
                caption="Figure 9: Confusion matrices for the three trees on the held-out testing set. All three share the same tendency to identify totals that will be chased slightly more reliably than totals that will be defended."
                wide
              />
              <p>
                The best of the three was <strong>{bestTreeName.split(' - ')[0]}</strong>{' '}
                at <strong>{percent(bestTree.accuracy)}</strong>, against the
                majority-class baseline of {percent(results.majority_class_baseline)}. The striking
                result is that the <em>shallowest</em> tree performed best. Tree A, with just{' '}
                {bestTree.leaves} leaves, beat the deeper trees on unseen matches while
                scoring lowest on its own training data, and the gap between its training and
                testing accuracy is only{' '}
                {((bestTree.train_accuracy - bestTree.accuracy) * 100).toFixed(1)}{' '}
                points. Figure 3 extends this across every depth from 1 to 20: training accuracy
                rises toward {depthStudy ? percent(depthStudy.deep_train_accuracy) : ''} while
                testing accuracy peaks at depth {depthStudy ? depthStudy.best_depth : ''} and then
                falls to {depthStudy ? percent(depthStudy.deep_test_accuracy) : ''}. The deepest
                trees are memorising individual matches.
              </p>
              <p>
                All three trees place <em>first-innings run rate</em> at the root, and all three
                choose a threshold close to five runs per over, which is effectively the dividing
                line between the two formats that clustering found independently. The second level
                then tests the raw run total. This is a cricketing result stated in the tree&apos;s
                own vocabulary: the tempo of the innings is the first thing worth knowing, and the
                size of the total is interpreted in that context rather than on its own. Comparing
                the two methods, the trees edge out Naive Bayes by about{' '}
                {((bestTree.accuracy - results.naive_bayes['Multinomial NB'].accuracy) * 100).toFixed(1)}{' '}
                points, which is consistent with the trees being able to capture interactions that
                the independence assumption forbids.
              </p>
            </>
          ) : pending('the decision tree results')}
        </section>

        <section className="assignment-section">
          <h3>Conclusions</h3>
          <p>
            The clearest lesson for the topic is that <em>how fast</em> a side scored matters more
            than <em>how much</em> it scored. Every tree asks about run rate before it asks about
            runs, which inverts the way totals are usually discussed. A score of 160 means one
            thing in twenty overs and something entirely different in fifty, and the tree discovers
            that distinction on its own rather than being told it. For anyone assessing a total at
            the innings break, the practical advice the model offers is to establish the tempo
            first and only then judge the number.
          </p>
          <p>
            The second lesson is about the limits of complexity. The simplest tree, small enough to
            read in full on a single screen, predicted unseen matches better than either of its
            more elaborate rivals. The deeper trees learned the particular matches they were shown
            rather than the game those matches came from, and the depth curve makes that failure
            easy to see. This matters beyond the modelling, because it suggests that the handful of
            rules that genuinely govern whether a total is defended are few and fairly blunt. The
            remaining three matches in ten that the tree gets wrong are not waiting for a more
            complicated model; they are the part of cricket that the first innings genuinely does
            not determine.
          </p>
        </section>
      </section>
    )
  }

  // ------------------------------------------------------------ conclusions

  const renderConclusions = () => (
    <section className="content-panel">
      <header className="assignment-heading">
        <span className="eyebrow">What it all means</span>
        <h2>Conclusions</h2>
        <p>What more than six thousand completed matches say about how cricket is decided.</p>
      </header>

      <div className="text-block">
        {conclusionParagraphs.slice(0, 2).map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
      </div>

      <div className="intro-gallery">
        <figure className="intro-figure">
          <img src={cricketCelebration} alt="Cricket players celebrating together after a wicket" />
          <figcaption>
            Matches turn on accumulated work rather than single moments, and the record bears that out.
            Sides that sustained an innings fared better than sides that merely started one well.
          </figcaption>
        </figure>
        <figure className="intro-figure">
          <img src={cricketPlayer} alt="A batter at the crease preparing to face a delivery" />
          <figcaption>
            Roughly three matches in ten still finished against what the first innings suggested.
            That stubborn remainder is the part of the sport no amount of evidence removes.
          </figcaption>
        </figure>
      </div>

      <div className="text-block">
        {conclusionParagraphs.slice(2).map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
      </div>
    </section>
  )

  // --------------------------------------------------------------- about me

  const renderAboutMe = () => (
    <section className="content-panel">
      <header className="assignment-heading">
        <span className="eyebrow">About</span>
        <h2>About Me</h2>
        <p>Who built this, and how it was put together.</p>
      </header>
      <div className="text-block">
        {aboutMe.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
      </div>
      <div className="model-section-block">
        <h4>How to reproduce everything on this site</h4>
        <ol>
          <li>Install the Python packages listed in <code>requirements.txt</code>.</li>
          <li>Run <code>build_dataset.py</code> to download the archives, call both APIs and write the raw and cleaned files.</li>
          <li>Run <code>eda_cricket.py</code> for the exploratory figures.</li>
          <li>Run <code>clustering_pca.py</code> for the clustering, PCA and SVD results.</li>
          <li>Run <code>supervised_models.py</code> for the Naive Bayes and Decision Tree results.</li>
        </ol>
      </div>
      <CodeLinks items={[
        { file: 'build_dataset.py', label: 'build_dataset.py' },
        { file: 'eda_cricket.py', label: 'eda_cricket.py' },
        { file: 'clustering_pca.py', label: 'clustering_pca.py' },
        { file: 'supervised_models.py', label: 'supervised_models.py' },
        { file: 'plot_style.py', label: 'plot_style.py' },
      ]} />
    </section>
  )

  // ------------------------------------------------------------ placeholder

  const renderPlaceholderTab = (tabLabel, note) => (
    <section className="content-panel assignment-panel">
      <header className="assignment-heading">
        <span className="eyebrow">Planned for a later module</span>
        <h2>{tabLabel}</h2>
        <p>{note}</p>
      </header>
      <div className="section-summary">
        <p>
          This tab is part of the required project structure and will be completed in a later
          module. The cleaned dataset, the labelled training and testing sets and the data
          pipeline that feed it are already in place on the Data Prep and Naive Bayes tabs, so
          the work here will reuse exactly the same rows and the same disjoint split.
        </p>
      </div>
      <DataLinks items={[
        { href: dataUrl('cricsheet-matches-clean.csv'), label: 'Cleaned data (CSV)', download: true },
        { href: dataUrl('supervised-train.csv'), label: 'Training set (CSV)', download: true },
        { href: dataUrl('supervised-test.csv'), label: 'Testing set (CSV)', download: true },
      ]} />
    </section>
  )

  const placeholders = {
    Regression: ['Regression', 'Modelling a first-innings total as a continuous quantity rather than a category.'],
    AdaBoost: ['AdaBoost', 'Combining many shallow trees, each one focused on the matches its predecessors got wrong.'],
    GradientBoosting: ['Gradient Boosting', 'Building an additive model that fits the residual error left by the previous stage.'],
    XGBoost: ['XGBoost', 'A regularised, optimised implementation of gradient boosting applied to the same split.'],
    SVM: ['Support Vector Machines', 'Separating the two outcomes with the widest possible margin, including non-linear kernels.'],
    NN: ['Neural Networks', 'A fully connected network trained on the same labelled first-innings features.'],
  }

  const renderTab = () => {
    switch (activeTab) {
      case 'Introduction': return renderIntroduction()
      case 'DataPrep_EDA': return renderDataPrep()
      case 'Clustering': return renderClustering()
      case 'PCA': return renderPca()
      case 'NaiveBayes': return renderNaiveBayes()
      case 'DecTrees': return renderDecisionTrees()
      case 'Conclusions': return renderConclusions()
      case 'About Me': return renderAboutMe()
      default: return renderPlaceholderTab(...placeholders[activeTab])
    }
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
            <button
              key={tab}
              type="button"
              className={activeTab === tab ? 'tab-button active' : 'tab-button'}
              onClick={() => setActiveTab(tab)}
            >
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
