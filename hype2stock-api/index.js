require('dotenv').config();
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const { STUDIO_MAP, TMDB_STUDIO_IDS } = require('./studioMap');
const { scoreStudio } = require('../signalEngine');

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

const TMDB_API_KEY = process.env.TMDB_API_KEY;
const TMDB_BASE_URL = 'https://api.themoviedb.org/3';

// Cache configuration
const CACHE_TTL_MS = 10 * 60 * 1000; // 10 minutes for movies
const STOCK_CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes for stocks
const cache = {}; // { [cacheKey]: { data: any, timestamp: number } }

// Helper to format movie object
const formatMovie = (movie) => ({
  title: movie.title,
  release_date: movie.release_date,
  vote_average: movie.vote_average,
  vote_count: movie.vote_count,
  popularity: movie.popularity,
  poster_path: movie.poster_path
});

// Helper for caching logic
const getCachedData = (key, ttlMs = CACHE_TTL_MS) => {
  const cached = cache[key];
  if (cached && (Date.now() - cached.timestamp < ttlMs)) {
    return cached.data;
  }
  return null;
};

const setCachedData = (key, data) => {
  cache[key] = {
    data,
    timestamp: Date.now()
  };
};

// --- Internal Data Fetchers ---

async function getMoviesForStudio(studioParam) {
  const studioParamLower = studioParam.toLowerCase();
  const studioKey = Object.keys(TMDB_STUDIO_IDS).find(k => k.includes(studioParamLower) || studioParamLower.includes(k));
  
  if (!studioKey) {
    throw new Error(`Studio '${studioParam}' not found or not supported.`);
  }

  const companyId = TMDB_STUDIO_IDS[studioKey];
  const cacheKey = `studio_${companyId}`;
  
  const cachedData = getCachedData(cacheKey);
  if (cachedData) return cachedData;

  const today = new Date().toISOString().split('T')[0];
  
  const response = await axios.get(`${TMDB_BASE_URL}/discover/movie`, {
    params: {
      api_key: TMDB_API_KEY,
      with_companies: companyId,
      sort_by: 'primary_release_date.desc',
      'primary_release_date.lte': today,
      include_adult: false,
      page: 1
    }
  });

  const movies = response.data.results
    .sort((a, b) => new Date(b.release_date) - new Date(a.release_date))
    .slice(0, 3)
    .map(formatMovie);

  setCachedData(cacheKey, movies);
  return movies;
}

async function getStockForTicker(tickerParam) {
  const ticker = tickerParam.toUpperCase();
  const cacheKey = `stock_${ticker}`;

  const cachedData = getCachedData(cacheKey, STOCK_CACHE_TTL_MS);
  if (cachedData) return cachedData;

  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${ticker}?interval=1d&range=1mo`;
  
  // Provide User-Agent to avoid blocks
  const response = await axios.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' } });
  
  const result = response.data.chart.result[0];
  const meta = result.meta;
  const timestamps = result.timestamp || [];
  const closePrices = result.indicators?.quote[0]?.close || [];
  
  let priceHistory = [];
  for (let i = 0; i < timestamps.length; i++) {
    if (closePrices[i] !== null && closePrices[i] !== undefined) {
      priceHistory.push({
        date: new Date(timestamps[i] * 1000).toISOString().split('T')[0],
        close: closePrices[i]
      });
    }
  }

  const currentPrice = meta.regularMarketPrice;
  const previousClose = meta.chartPreviousClose;
  const changePercent = previousClose ? ((currentPrice - previousClose) / previousClose) * 100 : 0;
  
  let changePercent5d = 0;
  if (priceHistory.length >= 6) {
    const close5DaysAgo = priceHistory[priceHistory.length - 6].close;
    changePercent5d = ((currentPrice - close5DaysAgo) / close5DaysAgo) * 100;
  } else if (priceHistory.length > 1) {
    const earliestClose = priceHistory[0].close;
    changePercent5d = ((currentPrice - earliestClose) / earliestClose) * 100;
  }

  const stockData = {
    currentPrice,
    previousClose,
    changePercent,
    changePercent5d,
    volume: meta.regularMarketVolume,
    marketCap: null, // Usually omitted in v8 chart endpoint
    fiftyTwoWeekHigh: meta.fiftyTwoWeekHigh || null,
    fiftyTwoWeekLow: meta.fiftyTwoWeekLow || null,
    priceHistory
  };

  setCachedData(cacheKey, stockData);
  return stockData;
}

// --- Routes ---

app.get('/api/health', (req, res) => {
  res.json({ status: "ok", timestamp: Date.now() });
});

app.get('/api/movies/search', async (req, res) => {
  const query = req.query.query;
  if (!query) {
    return res.status(400).json({ error: "Missing query parameter" });
  }

  const cacheKey = `search_${query.toLowerCase()}`;
  const cachedData = getCachedData(cacheKey);
  
  if (cachedData) return res.json(cachedData);

  try {
    const response = await axios.get(`${TMDB_BASE_URL}/search/movie`, {
      params: {
        api_key: TMDB_API_KEY,
        query: query,
        include_adult: false
      }
    });

    const movies = response.data.results.map(formatMovie);
    setCachedData(cacheKey, movies);
    res.json(movies);
  } catch (error) {
    console.error("TMDB Search Error:", error?.response?.data || error.message);
    res.status(500).json({ error: "Failed to search movies from TMDB" });
  }
});

app.get('/api/movies/:studio', async (req, res) => {
  try {
    const movies = await getMoviesForStudio(req.params.studio);
    res.json(movies);
  } catch (error) {
    if (error.message.includes('not found')) {
      return res.status(404).json({ error: error.message });
    }
    console.error("Movie Error:", error.message);
    res.status(500).json({ error: "Failed to fetch studio movies from TMDB" });
  }
});

app.get('/api/stock/all', async (req, res) => {
  try {
    const tickers = Object.values(STUDIO_MAP);
    const promises = tickers.map(ticker => getStockForTicker(ticker).then(data => ({ ticker, data })));
    const results = await Promise.all(promises);
    
    const responseObj = {};
    results.forEach(r => {
      responseObj[r.ticker] = r.data;
    });
    
    res.json(responseObj);
  } catch (error) {
    console.error("Stock All Error:", error.message);
    res.status(500).json({ error: "Failed to fetch all stock data" });
  }
});

app.get('/api/signals/all', async (req, res) => {
  try {
    const studios = Object.keys(STUDIO_MAP);
    const results = await Promise.all(studios.map(async (studioName) => {
      const ticker = STUDIO_MAP[studioName];
      const [movies, stock] = await Promise.all([
        getMoviesForStudio(studioName),
        getStockForTicker(ticker)
      ]);
      
      // Map changePercent to momentum for the signal engine
      const stockWithMomentum = { ...stock, momentum: stock.changePercent };
      const signal = scoreStudio(movies, stockWithMomentum);
      
      return {
        studio: studioName,
        ticker,
        movies,
        stock: stockWithMomentum,
        signal
      };
    }));
    
    res.json(results);
  } catch (error) {
    console.error("Signals All Error:", error.message);
    res.status(500).json({ error: "Failed to generate all signals" });
  }
});

app.get('/api/stock/:ticker', async (req, res) => {
  try {
    const stock = await getStockForTicker(req.params.ticker);
    res.json(stock);
  } catch (error) {
    console.error("Stock Fetch Error:", error.message);
    res.status(500).json({ error: "Failed to fetch stock data from Yahoo Finance" });
  }
});

app.get('/api/combined/:studio', async (req, res) => {
  const studioParam = req.params.studio;
  
  // Strict matching based on STUDIO_MAP keys
  const studioName = Object.keys(STUDIO_MAP).find(k => k.toLowerCase() === studioParam.toLowerCase());
  
  if (!studioName) {
    return res.status(404).json({ error: `Studio '${studioParam}' not found in map.` });
  }

  const ticker = STUDIO_MAP[studioName];

  try {
    const [movies, stock] = await Promise.all([
      getMoviesForStudio(studioName),
      getStockForTicker(ticker)
    ]);

    res.json({
      studio: studioName,
      ticker,
      movies,
      stock
    });
  } catch (error) {
    console.error("Combined API Error:", error.message);
    res.status(500).json({ error: "Failed to fetch combined data" });
  }
});

app.listen(PORT, () => {
  console.log(`hype2stock-api running on port ${PORT}`);
});
