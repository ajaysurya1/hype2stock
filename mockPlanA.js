const http = require('http');
const { scoreStudio } = require('./signalEngine');

const MOCK_DATA = [
  {
    studio: 'Disney',
    ticker: 'DIS',
    movies: [
      { title: "Deadpool & Wolverine", popularity: 2500, vote_average: 8.2, release_date: new Date().toISOString() },
      { title: "Inside Out 2", popularity: 1800, vote_average: 7.9, release_date: new Date(Date.now() - 40 * 24 * 60 * 60 * 1000).toISOString() }
    ],
    stock: { momentum: 5.2 }
  },
  {
    studio: 'Netflix',
    ticker: 'NFLX',
    movies: [
      { title: "Atlas", popularity: 500, vote_average: 5.5, release_date: new Date().toISOString() }
    ],
    stock: { momentum: -1.2 }
  }
];

const server = http.createServer((req, res) => {
  if (req.url === '/api/signals/all') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    
    // Simulate Plan A scoring the studios
    const scored = MOCK_DATA.map(item => ({
      ...item,
      signal: scoreStudio(item.movies, item.stock)
    }));
    
    res.end(JSON.stringify(scored));
  } else {
    res.writeHead(404);
    res.end();
  }
});

server.listen(3001, () => console.log('Mock Plan A running on port 3001'));
