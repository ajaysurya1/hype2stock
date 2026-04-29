const { generateInsight } = require('./signalEngine');

function generateBadge(signal) {
  if (signal === "BULLISH") return { color: "#22c55e", label: "BULLISH" };
  if (signal === "WARNING") return { color: "#ef4444", label: "WARNING" };
  return { color: "#f59e0b", label: "NEUTRAL" };
}

function createStudio(studio, ticker, contentScore, hypeScore, signal, currentPrice, changePercent, movies) {
  const signalObj = {
    contentScore,
    hypeScore,
    stockMomentum: changePercent,
    signalStrength: Math.round((contentScore + hypeScore) / 2),
    overallSignal: signal,
    confidence: "HIGH",
    topMovie: { title: movies[0].title, contentScore: Math.round(movies[0].vote_average * 10) },
    reasoning: `Based on 3 recent release(s), the weighted content score is ${contentScore}/100 and hype levels sit at ${hypeScore}/100.`,
    badge: generateBadge(signal)
  };

  return {
    studio,
    ticker,
    signal: signalObj,
    insight: generateInsight(studio, signalObj),
    movies,
    stock: { 
      currentPrice, 
      changePercent,
      momentum: changePercent 
    }
  };
}

const MOCK_DASHBOARD = {
  lastUpdated: new Date().toISOString(),
  degraded: false,
  isDemo: true,
  studios: [
    createStudio("Disney", "DIS", 78, 72, "BULLISH", 112.45, 1.8, [
      { title: "Inside Out 2", popularity: 2500, vote_average: 8.2, release_date: new Date(Date.now() - 30 * 86400000).toISOString() },
      { title: "Deadpool & Wolverine", popularity: 3100, vote_average: 8.4, release_date: new Date(Date.now() - 15 * 86400000).toISOString() },
      { title: "Moana 2", popularity: 1800, vote_average: 7.5, release_date: new Date(Date.now() - 60 * 86400000).toISOString() }
    ]),
    createStudio("Netflix", "NFLX", 84, 81, "BULLISH", 685.20, 3.2, [
      { title: "Hit Man", popularity: 1900, vote_average: 7.8, release_date: new Date(Date.now() - 25 * 86400000).toISOString() },
      { title: "Beverly Hills Cop: Axel F", popularity: 2200, vote_average: 7.2, release_date: new Date(Date.now() - 10 * 86400000).toISOString() },
      { title: "Atlas", popularity: 1500, vote_average: 5.6, release_date: new Date(Date.now() - 40 * 86400000).toISOString() }
    ]),
    createStudio("Warner Bros", "WBD", 51, 38, "NEUTRAL", 8.34, -0.5, [
      { title: "Furiosa: A Mad Max Saga", popularity: 1200, vote_average: 7.9, release_date: new Date(Date.now() - 45 * 86400000).toISOString() },
      { title: "The Watchers", popularity: 800, vote_average: 5.8, release_date: new Date(Date.now() - 20 * 86400000).toISOString() },
      { title: "Godzilla x Kong", popularity: 950, vote_average: 7.1, release_date: new Date(Date.now() - 90 * 86400000).toISOString() }
    ]),
    createStudio("Sony", "SONY", 63, 55, "NEUTRAL", 19.67, 0.9, [
      { title: "Bad Boys: Ride or Die", popularity: 1600, vote_average: 7.3, release_date: new Date(Date.now() - 12 * 86400000).toISOString() },
      { title: "The Garfield Movie", popularity: 1100, vote_average: 6.8, release_date: new Date(Date.now() - 35 * 86400000).toISOString() },
      { title: "Madame Web", popularity: 500, vote_average: 3.8, release_date: new Date(Date.now() - 120 * 86400000).toISOString() }
    ]),
    createStudio("Universal", "CMCSA", 44, 29, "WARNING", 37.12, -1.4, [
      { title: "Despicable Me 4", popularity: 2100, vote_average: 7.5, release_date: new Date(Date.now() - 5 * 86400000).toISOString() },
      { title: "The Fall Guy", popularity: 900, vote_average: 7.0, release_date: new Date(Date.now() - 55 * 86400000).toISOString() },
      { title: "Abigail", popularity: 400, vote_average: 6.5, release_date: new Date(Date.now() - 80 * 86400000).toISOString() }
    ])
  ]
};

// Sort studios by signalStrength descending
MOCK_DASHBOARD.studios.sort((a, b) => b.signal.signalStrength - a.signal.signalStrength);

module.exports = { MOCK_DASHBOARD };
