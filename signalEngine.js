/**
 * signalEngine.js
 * The core brain of Hype2Stock, calculating content, hype, and market signals.
 */

/**
 * Configuration thresholds for generating signals.
 */
const SIGNAL_THRESHOLDS = {
  BULLISH_CONTENT: 65,
  BULLISH_HYPE: 50,
  WARNING_CONTENT: 40,
  WARNING_HYPE: 25
};

/**
 * Maps TMDB's raw popularity score to a 0-100 scale using logarithmic scaling.
 * 
 * @param {number} rawPopularity - The raw popularity score from TMDB (can be 1000+).
 * @returns {number} A normalized score between 0 and 100.
 */
function normalizePopularity(rawPopularity) {
  return Math.min((Math.log10(rawPopularity + 1) / 3) * 100, 100);
}

/**
 * Determines the recency weight based on release date.
 * 
 * @param {string} releaseDateStr - The release date string (YYYY-MM-DD).
 * @returns {number} A weight between 0.2 and 1.0.
 */
function getRecencyWeight(releaseDateStr) {
  if (!releaseDateStr) return 0.2;
  
  const releaseDate = new Date(releaseDateStr);
  const now = new Date();
  const diffDays = Math.floor((now - releaseDate) / (1000 * 60 * 60 * 24));
  
  if (diffDays <= 30) return 1.0;
  if (diffDays <= 90) return 0.7;
  if (diffDays <= 180) return 0.4;
  return 0.2;
}

/**
 * Calculates scores for a single movie.
 * 
 * @param {Object} movie - The movie object.
 * @param {string} movie.title - The movie title.
 * @param {number} movie.popularity - TMDB popularity.
 * @param {number} movie.vote_average - TMDB vote average (0-10).
 * @param {string} movie.release_date - Release date string.
 * @returns {Object} The scored movie data.
 */
function scoreMovie(movie) {
  const contentScore = (movie.vote_average || 0) * 10;
  const hypeScore = normalizePopularity(movie.popularity || 0);
  const recencyWeight = getRecencyWeight(movie.release_date);
  
  return {
    title: movie.title,
    contentScore,
    hypeScore,
    recencyWeight,
    rating: movie.vote_average
  };
}

/**
 * Aggregates movie scores and stock data into a final signal.
 * 
 * @param {Array<Object>} movies - Array of up to 3 recent movie objects.
 * @param {Object} stock - Stock data object.
 * @param {number} [stock.momentum] - Stock momentum value.
 * @returns {Object} The final aggregated signal.
 */
function scoreStudio(movies, stock) {
  if (!movies || movies.length === 0) {
    return {
      contentScore: 0, hypeScore: 0, stockMomentum: stock?.momentum || 0,
      signalStrength: 0, overallSignal: "NEUTRAL", confidence: "LOW",
      topMovie: { title: "N/A", contentScore: 0 },
      reasoning: "Insufficient data to generate a signal.",
      badge: { color: "#f59e0b", label: "NEUTRAL" }
    };
  }

  const scoredMovies = movies.map(scoreMovie);
  
  let totalContent = 0;
  let totalHype = 0;
  let totalWeight = 0;
  
  let topMovie = scoredMovies[0];

  scoredMovies.forEach(m => {
    totalContent += m.contentScore * m.recencyWeight;
    totalHype += m.hypeScore * m.recencyWeight;
    totalWeight += m.recencyWeight;
    
    if (m.contentScore > topMovie.contentScore) {
      topMovie = m;
    }
  });
  
  const contentScore = Math.round(totalContent / (totalWeight || 1));
  const hypeScore = Math.round(totalHype / (totalWeight || 1));
  const stockMomentum = stock?.momentum || 0;
  const signalStrength = Math.round((contentScore + hypeScore) / 2);
  
  let overallSignal = "NEUTRAL";
  let badgeColor = "#f59e0b"; // amber
  
  if (contentScore >= SIGNAL_THRESHOLDS.BULLISH_CONTENT && hypeScore >= SIGNAL_THRESHOLDS.BULLISH_HYPE) {
    overallSignal = "BULLISH";
    badgeColor = "#22c55e"; // green
  } else if (contentScore <= SIGNAL_THRESHOLDS.WARNING_CONTENT || hypeScore <= SIGNAL_THRESHOLDS.WARNING_HYPE) {
    overallSignal = "WARNING";
    badgeColor = "#ef4444"; // red
  }
  
  let confidence = "LOW";
  if (movies.length >= 3) confidence = "HIGH";
  else if (movies.length === 2) confidence = "MEDIUM";
  
  const reasoning = `Based on ${movies.length} recent release(s), the weighted content score is ${contentScore}/100 and hype levels sit at ${hypeScore}/100.`;

  return {
    contentScore,
    hypeScore,
    stockMomentum,
    signalStrength,
    overallSignal,
    confidence,
    topMovie: { title: topMovie.title, contentScore: Math.round(topMovie.contentScore) },
    reasoning,
    badge: { color: badgeColor, label: overallSignal }
  };
}

/**
 * Generates an investor insight based on the studio's signal.
 * 
 * @param {string} studioName - The name of the studio/company (e.g., "Disney", "Netflix").
 * @param {Object} signal - The signal object returned by scoreStudio.
 * @returns {string} A two-sentence investor insight.
 */
function generateInsight(studioName, signal) {
  if (signal.overallSignal === "BULLISH") {
    return `${studioName}'s content momentum is strong with an ${signal.contentScore}/100 score. Upcoming releases show elevated hype — watch ${studioName} into the next earnings window.`;
  } else if (signal.overallSignal === "WARNING") {
    return `${studioName}'s content is struggling to gain traction, reflected in a low ${signal.contentScore}/100 score. Muted hype levels suggest caution before increasing exposure to ${studioName}.`;
  } else {
    return `${studioName} is showing steady performance with a ${signal.contentScore}/100 content score. Hype metrics are stable, indicating a holding pattern for the near term.`;
  }
}

module.exports = {
  SIGNAL_THRESHOLDS,
  normalizePopularity,
  getRecencyWeight,
  scoreMovie,
  scoreStudio,
  generateInsight
};

// --- Simple Test ---
if (require.main === module) {
  console.log("--- Running Signal Engine Tests ---\n");
  
  const mockMovies = [
    { title: "Deadpool & Wolverine", popularity: 2500, vote_average: 8.2, release_date: new Date().toISOString() },
    { title: "Inside Out 2", popularity: 1800, vote_average: 7.9, release_date: new Date(Date.now() - 40 * 24 * 60 * 60 * 1000).toISOString() },
    { title: "The Marvels", popularity: 400, vote_average: 5.5, release_date: new Date(Date.now() - 120 * 24 * 60 * 60 * 1000).toISOString() }
  ];
  
  const mockStock = { momentum: +5.2 };
  
  const movieScore = scoreMovie(mockMovies[0]);
  console.log("1. Single Movie Score (Deadpool & Wolverine):");
  console.log(movieScore);
  console.log("\n-------------------------\n");
  
  const signal = scoreStudio(mockMovies, mockStock);
  console.log("2. Studio Signal (Disney):");
  console.log(signal);
  console.log("\n-------------------------\n");
  
  const insight = generateInsight("DIS", signal);
  console.log("3. Generated Insight:");
  console.log(insight);
}
