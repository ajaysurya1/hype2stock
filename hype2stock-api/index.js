require('dotenv').config();
const express = require('express');
const cors = require('cors');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

const TMDB_API_KEY = process.env.TMDB_API_KEY;
const TMDB_BASE_URL = 'https://api.themoviedb.org/3';

// Cache configuration
const CACHE_TTL_MS = 10 * 60 * 1000; // 10 minutes
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
const getCachedData = (key) => {
  const cached = cache[key];
  if (cached && (Date.now() - cached.timestamp < CACHE_TTL_MS)) {
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

// Studio IDs mapping
const STUDIO_IDS = {
  "disney": 2,
  "warner bros": 174,
  "netflix": 213,
  "sony pictures": 34,
  "universal": 33
};

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
  
  if (cachedData) {
    return res.json(cachedData);
  }

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
    console.error("TMDB API Error:", error?.response?.data || error.message);
    res.status(500).json({ error: "Failed to fetch movies from TMDB" });
  }
});

app.get('/api/movies/:studio', async (req, res) => {
  const studioParam = req.params.studio.toLowerCase();
  
  // Find matching studio key (handle potential exact match issues)
  const studioKey = Object.keys(STUDIO_IDS).find(k => k.includes(studioParam) || studioParam.includes(k));
  
  if (!studioKey) {
    return res.status(404).json({ error: `Studio '${req.params.studio}' not found or not supported.` });
  }

  const companyId = STUDIO_IDS[studioKey];
  const cacheKey = `studio_${companyId}`;
  
  const cachedData = getCachedData(cacheKey);
  if (cachedData) {
    return res.json(cachedData);
  }

  try {
    // We only want released movies, so we filter by release date <= today
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

    // Ensure they are sorted properly and take top 3
    const movies = response.data.results
      .sort((a, b) => new Date(b.release_date) - new Date(a.release_date))
      .slice(0, 3)
      .map(formatMovie);

    setCachedData(cacheKey, movies);
    res.json(movies);

  } catch (error) {
    console.error("TMDB API Error:", error?.response?.data || error.message);
    res.status(500).json({ error: "Failed to fetch studio movies from TMDB" });
  }
});

app.listen(PORT, () => {
  console.log(`hype2stock-api running on port ${PORT}`);
});
