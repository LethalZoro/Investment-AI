import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import PortfolioView from './components/PortfolioView';
import ChatInterface from './components/ChatInterface';
import MarketView from './components/MarketView';
import SettingsView from './components/SettingsView';
import NewsView from './components/NewsView';
import AIStockDashboard from './components/AIStockDashboard';
import { API_BASE_URL } from './config';

function App() {
  // Polling for AI updates (Background Process)
  useEffect(() => {
    const runPolling = async () => {
      try {
        // 1. Get Settings for Polling Rate
        const settingsRes = await fetch(`${API_BASE_URL}/settings`);
        const settings = await settingsRes.json();
        const intervalMinutes = settings.polling_interval || 5;

        console.log(`Starting AI Polling Service (Interval: ${intervalMinutes}m)`);

        const poll = async () => {
          try {
            if (settings.autonomous_mode) {
              console.log("Running Scheduled AI Scan...");
              // Trigger News Analysis
              await fetch(`${API_BASE_URL}/autonomous/analyze-news`, { method: 'POST' });
              // Trigger Trading Cycle (includes intraday checks)
              await fetch(`${API_BASE_URL}/autonomous/trade`, { method: 'POST' });
            }
          } catch (e) {
            console.error("Polling Error:", e);
          }
        };

        // Run immediately on load
        poll();

        // Set interval
        const intervalId = setInterval(poll, intervalMinutes * 60 * 1000);
        return () => clearInterval(intervalId);

      } catch (e) {
        console.error("Failed to initialize polling:", e);
      }
    };

    runPolling();
  }, []);

  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<AIStockDashboard />} />
          {/* <Route path="/portfolio" element={<PortfolioView />} /> */}
          <Route path="/chat" element={<ChatInterface />} />
          <Route path="/market" element={<MarketView />} />
          <Route path="/news" element={<NewsView />} />
          <Route path="/ai-stocks" element={<AIStockDashboard />} />
          <Route path="/settings" element={<SettingsView />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
