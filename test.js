
const WebSocket = require('ws');

async function runTests() {
  console.log("--- Testing HTTP GET /api/dashboard ---");
  try {
    const res = await fetch('http://localhost:3002/api/dashboard');
    const data = await res.json();
    console.log("HTTP Response Status:", res.status);
    console.log("Data (summary):");
    console.log("Last Updated:", data.lastUpdated);
    console.log("Studios count:", data.studios?.length);
    if (data.studios && data.studios.length > 0) {
      console.log("Top Studio:", data.studios[0].studio);
      console.log("Insight:", data.studios[0].insight);
    }
  } catch (e) {
    console.error("HTTP fetch failed:", e.message);
  }

  console.log("\n--- Testing WebSocket /ws ---");
  const ws = new WebSocket('ws://localhost:3002/ws');
  
  ws.on('open', () => {
    console.log("WebSocket connection opened.");
  });

  ws.on('message', (data) => {
    const parsed = JSON.parse(data.toString());
    console.log("WebSocket Message Received:");
    console.log("Last Updated:", parsed.lastUpdated);
    console.log("Studios count:", parsed.studios?.length);
    ws.close();
  });

  ws.on('error', (err) => {
    console.error("WebSocket error:", err);
  });

  ws.on('close', () => {
    console.log("WebSocket connection closed.");
  });
}

runTests();
