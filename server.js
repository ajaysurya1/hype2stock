/**
 * server.js
 * Lightweight Express middleware layer for Hype2Stock.
 */

const express = require('express');
const cors = require('cors');
const http = require('http');
const { WebSocketServer } = require('ws');
const { generateInsight } = require('./signalEngine');
const { MOCK_DASHBOARD } = require('./mockData');

const app = express();
const server = http.createServer(app);
const wss = new WebSocketServer({ server, path: '/ws' });

const PORT = 3002;
const UPSTREAM_URL = 'http://localhost:3001/api/signals/all';

// --- Cache & State ---
let dashboardCache = null;
let lastUpdated = null;

// Mock data fallback
const MOCK_STUDIOS = [
  { studio: 'Disney', ticker: 'DIS' },
  { studio: 'Netflix', ticker: 'NFLX' },
  { studio: 'Warner Bros', ticker: 'WBD' },
  { studio: 'Universal', ticker: 'CMCSA' },
  { studio: 'Paramount', ticker: 'PARA' }
];

function getMockDashboard() {
  const timestamp = new Date().toISOString();
  const studios = MOCK_STUDIOS.map(s => {
    const mockSignal = {
      contentScore: 50,
      hypeScore: 50,
      stockMomentum: 0,
      signalStrength: 50,
      overallSignal: 'NEUTRAL',
      confidence: 'LOW',
      topMovie: { title: 'N/A', contentScore: 0 },
      reasoning: 'Fallback mock data generated due to upstream connection failure.',
      badge: { color: '#f59e0b', label: 'NEUTRAL' }
    };
    return {
      studio: s.studio,
      ticker: s.ticker,
      signal: mockSignal,
      insight: generateInsight(s.studio, mockSignal),
      movies: [],
      stock: { momentum: 0 }
    };
  });
  
  return {
    lastUpdated: timestamp,
    degraded: true,
    studios
  };
}

// --- Middleware ---
app.use(cors({
  origin: ['http://localhost:5173', 'http://localhost:3000']
}));

// Request logging middleware
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.originalUrl} -> ${res.statusCode} in ${duration}ms`);
  });
  next();
});

// --- Data Fetching Logic ---
async function fetchUpstreamData() {
  if (process.env.DEMO_MODE === 'true') {
    MOCK_DASHBOARD.lastUpdated = new Date().toISOString();
    return MOCK_DASHBOARD;
  }

  try {
    const response = await fetch(UPSTREAM_URL);
    if (!response.ok) {
      throw new Error(`Upstream returned status ${response.status}`);
    }
    
    const rawData = await response.json();
    
    // Enrich with insights
    const enrichedStudios = rawData.map(item => {
      const signal = item.signal || {};
      const insight = generateInsight(item.studio || 'Unknown', signal);
      
      return {
        ...item,
        insight
      };
    });
    
    // Sort by signalStrength descending
    enrichedStudios.sort((a, b) => {
      const strengthA = a.signal?.signalStrength || 0;
      const strengthB = b.signal?.signalStrength || 0;
      return strengthB - strengthA;
    });

    const timestamp = new Date().toISOString();
    
    dashboardCache = {
      lastUpdated: timestamp,
      studios: enrichedStudios
    };
    lastUpdated = timestamp;
    
    return dashboardCache;
    
  } catch (error) {
    console.error(`[Error] Fetching upstream data failed: ${error.message}`);
    if (dashboardCache) {
      console.log('Returning cached data.');
      return dashboardCache;
    }
    console.log('Returning mock data.');
    return getMockDashboard();
  }
}

// --- Endpoints ---

app.get('/api/ping', (req, res) => {
  res.json({
    ok: true,
    mode: process.env.DEMO_MODE === 'true' ? "demo" : "live",
    uptime: process.uptime()
  });
});

app.get('/api/dashboard', async (req, res) => {
  const data = await fetchUpstreamData();
  res.json(data);
});

app.get('/api/studio/:studio', async (req, res) => {
  const data = await fetchUpstreamData();
  const requestedStudio = req.params.studio.toLowerCase();
  
  const studioData = data.studios.find(s => 
    s.studio.toLowerCase() === requestedStudio || 
    s.ticker.toLowerCase() === requestedStudio
  );
  
  if (studioData) {
    res.json({
      lastUpdated: data.lastUpdated,
      degraded: data.degraded,
      ...studioData
    });
  } else {
    res.status(404).json({ error: 'Studio not found' });
  }
});

app.get('/api/refresh', async (req, res) => {
  dashboardCache = null; // Clear cache
  const data = await fetchUpstreamData();
  res.json({ refreshed: true, timestamp: data.lastUpdated });
});

// --- WebSocket ---
wss.on('connection', async (ws) => {
  console.log('New WebSocket connection');
  // Send current data immediately
  const data = dashboardCache || await fetchUpstreamData();
  ws.send(JSON.stringify(data));
});

// Broadcast every 60 seconds
setInterval(async () => {
  const data = await fetchUpstreamData();
  const payload = JSON.stringify(data);
  wss.clients.forEach(client => {
    if (client.readyState === 1) { // WebSocket.OPEN is 1
      client.send(payload);
    }
  });
}, 60000);

// Ensure cache is populated on startup
fetchUpstreamData().then(() => {
  // Start server after initial fetch attempt
  server.listen(PORT, () => {
    console.log(`Middleware server running on port ${PORT}`);
  });
});
