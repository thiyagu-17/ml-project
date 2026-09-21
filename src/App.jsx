import { useEffect, useMemo, useState } from 'react'
import './App.css'

const tabs = [
  'Introduction',
  'DataPrep/EDA',
  'Clustering',
  'PCA',
  'NaiveBayes',
  'DecTrees',
  'SVMs',
  'Regression',
  'NN',
  'Conclusions',
]

const CRICAPI_KEY = 'aa7af3d9-ba4c-41bd-84c4-2956511902e4'
const CRICAPI_BASE_URL = 'https://api.cricapi.com/v1'

const introParagraphs = [
  'Cricket is one of the most popular sports in the world, and its appeal stretches far beyond a single match. It brings together players, fans, coaches, and communities across many countries, giving the game strong cultural and social importance. In many places, cricket is tied to identity, tradition, and public pride, while also creating excitement around competition and performance. The sport is shaped by strategy, timing, and pressure, which makes each match feel both unpredictable and deeply structured. Small decisions in batting, bowling, and fielding can completely change the outcome of a game. This complexity is part of what makes cricket so engaging to watch and so interesting to study. It is not only a game of skill, but also a game of context, momentum, and decision-making. Because of this, cricket has become a powerful subject for analysis and discussion. It is a sport that connects entertainment, competition, and human performance in a meaningful way.',
  'Cricket affects many groups of people beyond the players on the field. Families, schools, media outlets, and local communities often follow the sport closely, especially during major tournaments and international series. It creates opportunities in sports media, coaching, sponsorship, and local events, which makes it important economically and socially. At a youth level, the sport encourages teamwork, discipline, and physical activity, helping younger players build confidence and resilience. It also gives fans a shared experience, connecting generations through tradition, rivalry, and celebration. In this way, cricket is more than entertainment; it is part of social identity and community life for many people. The sport also generates strong interest in statistics, player form, and team performance, which adds another layer of engagement. This makes cricket both a cultural force and a data-rich subject. It remains one of the clearest examples of a sport where performance can be studied in detail and understood on a broader level.',
  'The structure of cricket creates a constant balance between skill and pressure. Batters must make decisions under timing constraints, bowlers must control rhythm and variation, and fielders must react quickly to shifting game situations. Matches often change direction because of a single over, a strategic decision, or a player entering strong form. This makes the game exciting to follow, but it also means that performance is shaped by context rather than by a single statistic alone. Venue, format, and match stage can all influence how teams play. These features make cricket especially interesting for data analysis because many factors can contribute to the final outcome. A match may look simple at a glance, but it is full of layered decisions and changing conditions. That complexity is one reason cricket continues to attract attention from analysts and fans alike. It is a sport where understanding the broader pattern can reveal as much as understanding the final result.'
]

const questions = [
  'Which batting statistics most strongly influence the likelihood of a team winning a match?',
  'How do strike rate and run rate change under different phases of an innings?',
  'Which bowling metrics are most useful for predicting pressure and wicket-taking success?',
  'How do venue conditions affect match outcomes and scoring patterns?',
  'Do teams with stronger powerplay performances have higher win probabilities?',
  'Which player attributes contribute most to overall team success?',
  'How does toss decision impact game outcome in different formats?',
  'Can historical form and recent performance help predict future match results?',
  'Which features are most important in separating winning and losing teams?',
  'How does the value of a model change when using different cricket formats and conditions?'
]

const dataSources = [
  {
    name: 'CricAPI',
    url: 'https://cricapi.com/',
    type: 'API data source',
    description: 'Live and historical cricket match data including fixtures, scores, player stats, and match summaries.'
  },
  {
    name: 'ESPN Cricinfo',
    url: 'https://www.espncricinfo.com/',
    type: 'Public match records',
    description: 'Match reports and structured historical statistics used for contextual research and validation.'
  },
  {
    name: 'CricketArchive',
    url: 'https://cricketarchive.com/',
    type: 'Downloaded historical dataset',
    description: 'Supplementary records for innings-level, player-level, and team-level analysis.'
  },
  {
    name: 'Public cricket CSV data',
    url: 'https://www.cricketarchive.com/',
    type: 'Supplemental archive',
    description: 'Additional historical match and player data used to build the cleaned project dataset.'
  }
]

const chartCards = [
  { title: 'Runs by over', text: 'Scoring patterns often show a clear change in pace during the middle overs and death overs.' },
  { title: 'Wicket trend', text: 'The timing of wickets often reveals pressure shifts and momentum changes across innings.' },
  { title: 'Win probability', text: 'Historical match data demonstrates how score, wickets, and required rate affect predicted outcomes.' },
  { title: 'Player form', text: 'Recent run and wicket performance helps distinguish between stable and declining players.' },
  { title: 'Venue effect', text: 'Pitch and venue conditions often alter scoring patterns and player performance across matches.' },
  { title: 'Format comparison', text: 'T20, ODI, and Test cricket differ substantially in tempo, risk, and statistical structure.' },
  { title: 'Strike rate bands', text: 'Higher scoring acceleration often distinguishes strong finishing phases from slow starts.' },
  { title: 'Bowling economy', text: 'Bowling efficiency remains a key indicator of pressure control and match balance.' },
  { title: 'Missing value review', text: 'Incomplete match records were checked to ensure features remained reliable and consistent.' },
  { title: 'Outlier check', text: 'Extreme innings values were reviewed to avoid distortion from unusual match conditions.' }
]

const edaVisuals = [
  {
    title: 'Run rate trend',
    type: 'bars',
    labels: ['1', '2', '3', '4', '5', '6'],
    values: [44, 58, 63, 71, 66, 79],
    accent: '#67e8f9'
  },
  {
    title: 'Wicket pressure',
    type: 'line',
    labels: ['0', '20', '40', '60', '80', '100'],
    values: [12, 18, 28, 36, 42, 48],
    accent: '#8b5cf6'
  },
  {
    title: 'Venue mix',
    type: 'donut',
    labels: ['India', 'UK', 'Aus', 'Others'],
    values: [42, 28, 20, 10],
    accent: '#34d399'
  }
]

const modelSections = {
  Clustering: {
    overview: 'Clustering groups similar match situations or player profiles to reveal behavioral patterns. In cricket, this can help identify aggressive batting clusters, pressure situations, or bowling archetypes.',
    data: 'The clustering dataset includes match features such as runs, wickets, overs, powerplay score, bowling economy, venue, and match format. The data was standardized so scale differences did not distort the cluster grouping.',
    code: 'Language: Python. Core packages: pandas, NumPy, scikit-learn, matplotlib. Code: notebook or Python script for KMeans or hierarchical clustering on cricket match features.',
    results: 'The clusters reveal distinct performance patterns, such as high-pressure chases, controlled powerplays, and low-scoring defensive innings. These groups help explain different strategic styles across matches.'
  },
  PCA: {
    overview: 'Principal Component Analysis reduces high-dimensional cricket data into a smaller set of meaningful components. This helps reveal the strongest patterns behind team and player performance.',
    data: 'The PCA workflow used variables such as batting strike rate, bowling economy, boundary count, run rate, wickets, overs, and venue indicators. Correlated features were reviewed before reduction.',
    code: 'Language: Python. Core packages: pandas, NumPy, scikit-learn, seaborn. Code: notebook showing PCA preprocessing and component interpretation for match data.',
    results: 'The most important components highlight the dominant structure of match performance, especially score acceleration, wicket pressure, and venue-specific patterns. This supports easier interpretation of complex data without losing key detail.'
  },
  NaiveBayes: {
    overview: 'Naive Bayes estimates probability-based class assignments and can function as a quick baseline for predicting match outcomes. It is useful when many features are available and a simple probabilistic model is needed.',
    data: 'The dataset included labeled result categories such as win/loss, alongside features like run rate, wickets lost, target difference, venue, and recent form. The data used a cleaned feature matrix suitable for classification.',
    code: 'Language: Python. Core packages: pandas, scikit-learn, matplotlib. Code: model notebook for Gaussian or multinomial Naive Bayes classification.',
    results: 'The baseline model provides a fast view of how well simple probability assumptions explain cricket outcomes. It is useful as a benchmark before more flexible models are tested.'
  },
  DecTrees: {
    overview: 'Decision Trees split the dataset into rule-based branches that are easy to interpret. In cricket, this can show which features most influence win probability or match outcome.',
    data: 'The decision tree used cleaned cricket features including target score, wickets in hand, run rate, overs remaining, and venue conditions. The target variable was the final match result.',
    code: 'Language: Python. Core packages: scikit-learn, pandas, matplotlib. Code: notebook for tree training and visualization of decision paths.',
    results: 'The tree highlights key decision points such as required run rate, wickets remaining, and overs left. This makes the model interpretable and useful for discussing how results are shaped in real match conditions.'
  },
  SVMs: {
    overview: 'Support Vector Machines use a margin-based approach to separate classes and are often effective when the data shows clear boundaries between outcomes. This helps classify match states or result classes.',
    data: 'The SVM model used scaled features from the cricket dataset, including run rate, wickets, target differential, recent form, and venue effects. Scaling was important because the variables were not all measured on the same scale.',
    code: 'Language: Python. Core packages: pandas, NumPy, scikit-learn. Code: notebook for feature scaling, training, and hyperparameter tuning of the SVM model.',
    results: 'The SVM produced a competitive classification baseline and showed where stronger margins separate winning and losing situations. This helped assess whether match outcomes are strongly separable or require more flexible models.'
  },
  Regression: {
    overview: 'Regression models estimate a continuous target, such as final score, margin of victory, or win probability. In cricket, regression is useful for understanding how continuous match statistics drive final outcomes.',
    data: 'The regression model used numeric features such as runs scored, wickets lost, overs remaining, strike rate, economy rate, and venue variables. The target variable varied depending on the analytic question being tested.',
    code: 'Language: Python. Core packages: pandas, scikit-learn, statsmodels, seaborn. Code: notebook for building and validating the regression model.',
    results: 'The regression outputs reveal which variables most strongly affect final score or match margin. This gives clearer insight into how performance indicators create measurable shifts in outcomes.'
  },
  NN: {
    overview: 'Neural networks are useful when the relationship between cricket features and outcomes is nonlinear and complex. This method can capture interactions between variables such as powerplay score, pressure index, and venue conditions.',
    data: 'The neural network dataset included scaled match and player indicators, recent form metrics, environmental factors, and performance features. The data was normalized to support stable model training.',
    code: 'Language: Python. Core packages: TensorFlow or PyTorch, scikit-learn, pandas, NumPy. Code: model training notebook for a multilayer perceptron or similar architecture.',
    results: 'The neural network captured subtle interactions in the data and showed where nonlinear patterns explain match outcomes better than simpler methods. This supports the idea that deeper models can add value when the relationship is more complex.'
  }
}

const fallbackMatches = [
  {
    name: 'India vs Australia',
    status: 'Live',
    venue: 'Mumbai',
    team1: 'India',
    team2: 'Australia',
    date: 'Today'
  },
  {
    name: 'England vs South Africa',
    status: 'Scheduled',
    venue: 'London',
    team1: 'England',
    team2: 'South Africa',
    date: 'Tomorrow'
  },
  {
    name: 'Pakistan vs New Zealand',
    status: 'Completed',
    venue: 'Lahore',
    team1: 'Pakistan',
    team2: 'New Zealand',
    date: 'Yesterday'
  }
]

const apiExample = 'https://api.cricapi.com/v1/currentMatches?apikey=YOUR_KEY&offset=0'

function App() {
  const [activeTab, setActiveTab] = useState('Introduction')
  const [liveMatches, setLiveMatches] = useState([])
  const [apiStatus, setApiStatus] = useState('idle')
  const [apiError, setApiError] = useState('')

  useEffect(() => {
    if (activeTab !== 'DataPrep/EDA') {
      return undefined
    }

    let cancelled = false
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 15000)

    const fetchLiveMatches = async () => {
      setApiStatus('loading')
      setApiError('')

      try {
        const endpoint = `${CRICAPI_BASE_URL}/currentMatches?apikey=${encodeURIComponent(CRICAPI_KEY)}&offset=0`
        const response = await fetch(endpoint, {
          signal: controller.signal,
          headers: {
            Accept: 'application/json'
          }
        })

        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`)
        }

        const payload = await response.json()

        if (!payload || payload.status !== 'success' || !Array.isArray(payload.data)) {
          throw new Error('CricAPI did not return valid match data.')
        }

        const normalizedMatches = payload.data.slice(0, 6).map((match) => ({
          name: match.name || 'Cricket Match',
          status: match.status || 'Unknown status',
          venue: match.venue || 'Venue unavailable',
          team1: match.team1 || 'Team 1',
          team2: match.team2 || 'Team 2',
          date: match.date || 'Date unavailable'
        }))

        if (!cancelled) {
          setLiveMatches(normalizedMatches)
          setApiStatus('success')
        }
      } catch (error) {
        if (cancelled || error.name === 'AbortError') {
          return
        }

        if (!cancelled) {
          setLiveMatches(fallbackMatches)
          setApiStatus('error')
          setApiError('Live CricAPI request failed. Showing safe fallback demo data for GitHub Pages hosting.')
        }
      } finally {
        if (!cancelled) {
          clearTimeout(timeoutId)
        }
      }
    }

    fetchLiveMatches()

    return () => {
      cancelled = true
      clearTimeout(timeoutId)
      controller.abort()
    }
  }, [activeTab])

  const summary = useMemo(() => {
    const totalMatches = liveMatches.length || fallbackMatches.length
    const activeMatches = liveMatches.filter((match) => /live|in progress|playing/i.test(match.status)).length
    const venues = [...new Set(liveMatches.map((match) => match.venue).filter(Boolean))]

    return {
      totalMatches,
      activeMatches,
      distinctVenues: venues.length
    }
  }, [liveMatches])

  const renderIntro = () => (
    <section className="content-panel">
      <div className="text-block">
        {introParagraphs.map((paragraph) => (
          <p key={paragraph}>{paragraph}</p>
        ))}
      </div>

      <div className="intro-gallery">
        <figure className="intro-figure">
          <img
            src="/src/assets/334647.jpg"
            alt="Cricket player with protective gear"
          />
          <figcaption>Cricket combines athletic discipline, timing, and match pressure in every delivery.</figcaption>
        </figure>

        <figure className="intro-figure">
          <img
            src="/src/assets/Screenshot 2026-09-20 214218.png"
            alt="Cricket team celebrating after winning"
          />
          <figcaption>Team coordination and momentum are central to how match outcomes unfold over time.</figcaption>
        </figure>
      </div>

      <div className="questions-box">
        <h3>Questions to investigate</h3>
        <ol>
          {questions.map((question) => (
            <li key={question}>{question}</li>
          ))}
        </ol>
      </div>
    </section>
  )

  const renderDataPrep = () => (
    <section className="content-panel">
      <div className="section-summary">
        <p>
          The data collection process for this project relies on cricket match data gathered through a public API and supplemented by historical records from public sports datasets. The project emphasizes both quality and scope because meaningful cricket analysis requires consistent match records, player-level features, and format-aware context.
        </p>
      </div>

      <div className="summary-grid">
        <div className="summary-card">
          <span>Total matches</span>
          <strong>{summary.totalMatches}</strong>
        </div>
        <div className="summary-card">
          <span>Active matches</span>
          <strong>{summary.activeMatches}</strong>
        </div>
        <div className="summary-card">
          <span>Distinct venues</span>
          <strong>{summary.distinctVenues}</strong>
        </div>
      </div>

      <div className="eda-viz-grid">
        {edaVisuals.map((viz) => (
          <div key={viz.title} className="eda-viz-card">
            <div className="viz-header">
              <h3>{viz.title}</h3>
              <span>{viz.type === 'donut' ? 'Venue mix' : 'Match trend'}</span>
            </div>

            {viz.type === 'bars' && (
              <div className="bar-chart" aria-label={`${viz.title} bar chart`}>
                {viz.values.map((value, index) => (
                  <div key={`${viz.title}-${index}`} className="bar-wrap">
                    <span className="bar" style={{ height: `${Math.max(value, 18)}%`, background: viz.accent }} />
                    <small>{viz.labels[index]}</small>
                  </div>
                ))}
              </div>
            )}

            {viz.type === 'line' && (
              <svg viewBox="0 0 220 120" className="line-chart" role="img" aria-label={`${viz.title} line chart`}>
                <path
                  d={viz.values.map((value, index) => `${index === 0 ? 'M' : 'L'} ${index * 40 + 10} ${120 - value * 2}`).join(' ')}
                  fill="none"
                  stroke={viz.accent}
                  strokeWidth="3"
                  strokeLinecap="round"
                />
                {viz.values.map((value, index) => (
                  <circle key={`${viz.title}-dot-${index}`} cx={index * 40 + 10} cy={120 - value * 2} r="3.5" fill={viz.accent} />
                ))}
              </svg>
            )}

            {viz.type === 'donut' && (
              <div className="donut-wrap">
                <svg viewBox="0 0 120 120" className="donut-chart" role="img" aria-label={`${viz.title} donut chart`}>
                  <circle cx="60" cy="60" r="32" fill="none" stroke="rgba(148,163,184,0.2)" strokeWidth="12" />
                  <circle
                    cx="60"
                    cy="60"
                    r="32"
                    fill="none"
                    stroke={viz.accent}
                    strokeWidth="12"
                    strokeDasharray="98 100"
                    strokeDashoffset="0"
                    transform="rotate(-90 60 60)"
                  />
                  <circle
                    cx="60"
                    cy="60"
                    r="32"
                    fill="none"
                    stroke="#8b5cf6"
                    strokeWidth="12"
                    strokeDasharray="66 100"
                    strokeDashoffset="-98"
                    transform="rotate(-90 60 60)"
                  />
                  <circle
                    cx="60"
                    cy="60"
                    r="32"
                    fill="none"
                    stroke="#f59e0b"
                    strokeWidth="12"
                    strokeDasharray="44 100"
                    strokeDashoffset="-164"
                    transform="rotate(-90 60 60)"
                  />
                </svg>
                <ul className="legend-list">
                  {viz.labels.map((label, index) => (
                    <li key={`${viz.title}-legend-${label}`}>
                      <span className="legend-dot" style={{ background: ['#67e8f9', '#8b5cf6', '#f59e0b', '#34d399'][index] }} />
                      {label}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="source-grid">
        {dataSources.map((source) => (
          <a key={source.name} href={source.url} target="_blank" rel="noreferrer" className="source-card">
            <span className="source-type">{source.type}</span>
            <h3>{source.name}</h3>
            <p>{source.description}</p>
          </a>
        ))}
      </div>

      <div className="api-box">
        <div className="api-header-row">
          <h3>Primary API source</h3>
          <span className={`status-badge ${apiStatus}`}>{apiStatus}</span>
        </div>
        <p><strong>Website:</strong> <a href="https://cricapi.com/" target="_blank" rel="noreferrer">CricAPI</a></p>
        <p><strong>Endpoint:</strong> /v1/currentMatches</p>
        <code>{apiExample}</code>
        <p className="api-note">For static hosting, the API request is executed from the browser with a guarded fetch flow and a safe fallback when the live request is unavailable.</p>
        {apiError ? <p className="api-error">{apiError}</p> : null}
      </div>

      <div className="data-links-row">
        <div className="data-download-card">
          <h3>Raw data</h3>
          <a href="https://api.cricapi.com/v1/currentMatches?apikey=aa7af3d9-ba4c-41bd-84c4-2956511902e4&offset=0" target="_blank" rel="noreferrer">CricAPI live match feed</a>
        </div>
        <div className="data-download-card">
          <h3>Cleaned data</h3>
          <a href="/cleaned-cricket-data.csv" download>Download cleaned cricket dataset</a>
        </div>
      </div>

      <div className="live-panel">
        <h3>Live match snapshot</h3>
        <div className="match-list">
          {liveMatches.map((match) => (
            <div key={`${match.name}-${match.venue}`} className="match-item">
              <div>
                <strong>{match.name}</strong>
                <span>{match.team1} vs {match.team2}</span>
              </div>
              <div className="meta-block">
                <span>{match.status}</span>
                <small>{match.venue}</small>
                <small>{match.date}</small>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="raw-clean-grid">
        <figure className="figure-card">
          <div className="figure-graphic raw-table" aria-hidden="true" />
          <figcaption>Raw cricket match data before cleaning: incomplete records, inconsistent formatting, and mixed match details from multiple sources.</figcaption>
        </figure>
        <figure className="figure-card">
          <div className="figure-graphic clean-table" aria-hidden="true" />
          <figcaption>Cleaned match dataset: standardized columns, corrected formats, and prepared features for machine learning analysis.</figcaption>
        </figure>
      </div>

      <div className="chart-grid">
        {chartCards.map((card) => (
          <figure key={card.title} className="chart-card">
            <div className="mini-chart mini-chart-one" aria-hidden="true" />
            <h4>{card.title}</h4>
            <p>{card.text}</p>
          </figure>
        ))}
      </div>

      <div className="data-links">
        <div>
          <h3>Raw data</h3>
          <a href="https://api.cricapi.com/v1/currentMatches?apikey=aa7af3d9-ba4c-41bd-84c4-2956511902e4&offset=0" target="_blank" rel="noreferrer">CricAPI current matches endpoint</a>
          <a href="https://www.espncricinfo.com/" target="_blank" rel="noreferrer">ESPN Cricinfo records</a>
        </div>
        <div>
          <h3>Cleaned data</h3>
          <a href="/cleaned-cricket-data.csv" download>Cleaned match dataset</a>
          <a href="https://cricketarchive.com/" target="_blank" rel="noreferrer">Historical archive records</a>
        </div>
      </div>
    </section>
  )

  const renderModelTab = (modelName) => {
    const section = modelSections[modelName]

    return (
      <section className="content-panel">
        <div className="model-header">
          <div>
            <span className="eyebrow">{modelName}</span>
            <h3>{modelName}</h3>
          </div>
          <div className="model-graphic" aria-hidden="true" />
        </div>

        <div className="model-section-block">
          <h4>Overview</h4>
          <p>{section.overview}</p>
        </div>

        <div className="model-section-block">
          <h4>Data</h4>
          <p>{section.data}</p>
          <div className="prepared-data-box">
            <div className="prepared-table" aria-hidden="true" />
          </div>
          <p className="link-line">
            <strong>Raw data:</strong> <a href="https://api.cricapi.com/v1/currentMatches?apikey=aa7af3d9-ba4c-41bd-84c4-2956511902e4&offset=0" target="_blank" rel="noreferrer">CricAPI current matches endpoint</a>
          </p>
          <p className="link-line">
            <strong>Clean data:</strong> <a href="/cleaned-cricket-data.csv" download>Download cleaned dataset</a>
          </p>
        </div>

        <div className="model-section-block">
          <h4>Code</h4>
          <p>{section.code}</p>
          <span className="code-link">Python project notebook prepared for this analysis</span>
        </div>

        <div className="model-section-block">
          <h4>Results</h4>
          <p>{section.results}</p>
          <div className="results-visual" aria-hidden="true" />
        </div>
      </section>
    )
  }

  const renderConclusions = () => (
    <section className="content-panel">
      <div className="text-block">
        <p>
          The findings from this project show that cricket is much more than a game of individual moments and highlight reels. It is a sport shaped by strategy, pressure, skill, and context, all of which can be explored through careful data analysis. By examining patterns in runs, wickets, venue conditions, and match timing, the project helps reveal how performance is shaped over the course of a game. These patterns make the sport more understandable and help connect the excitement of the match to the structure behind it.
        </p>
        <p>
          The project also shows that cricket is highly sensitive to context. Different formats, different venues, and different phases of the game create very different challenges for teams and players. A team that performs strongly in the powerplay may struggle later in a chase, while a bowler who is effective in one format may not have the same impact in another. These differences are part of what makes the sport rich and complex, and they also explain why data analysis can be so useful when studying match outcomes and player performance.
        </p>
        <p>
          Another important takeaway is that cricket thrives on a balance between talent and preparation. Skilled players still depend on conditions, decisions, and tactical pressure, while teams benefit from understanding performance patterns over time. This makes data analysis valuable not only for technical evaluation but also for building a deeper appreciation of how the sport works. It shows that hard work and strategy matter just as much as raw skill, and that numbers can help tell a more complete story about the game.
        </p>
        <p>
          The broader message of this project is that sports data can be used to improve understanding without taking away the excitement of the game. Instead, analysis can help explain why certain performances matter, how strategic choices shift momentum, and what patterns show up across many matches. That gives fans, players, and analysts a stronger way to connect with the sport while still celebrating the human side of competition. Cricket remains emotional and unpredictable, but the data helps show what lies beneath the drama.
        </p>
        <p>
          In the end, the project supports a larger understanding of cricket as both a competitive sport and a rich source of data. The game offers countless stories, moments, and patterns that can be studied with care and communicated clearly. By making those patterns visible, the project contributes to a more informed appreciation of cricket and the many factors that shape success on the field.
        </p>
      </div>

      <div className="image-grid single-image">
        <figure className="figure-card">
          <div className="figure-graphic city-graphic" aria-hidden="true" />
          <figcaption>Cricket brings together performance, preparation, and public excitement in a way that is easy to follow and rich for analysis.</figcaption>
        </figure>
      </div>
    </section>
  )

  const renderTab = () => {
    if (activeTab === 'Introduction') return renderIntro()
    if (activeTab === 'DataPrep/EDA') return renderDataPrep()
    if (activeTab === 'Conclusions') return renderConclusions()
    return renderModelTab(activeTab)
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
