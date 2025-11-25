import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import PortfolioView from './components/PortfolioView';
import ChatInterface from './components/ChatInterface';
import MarketView from './components/MarketView';
import SettingsView from './components/SettingsView';
import NewsView from './components/NewsView';
import AIStockDashboard from './components/AIStockDashboard';

function App() {
  React.useEffect(() => {
    const runPolling = async () => {
      try {
        // 1. Get Settings for Polling Rate
        const settingsRes = await fetch('http://localhost:8000/settings');
        const settings = await settingsRes.json();
        const intervalMinutes = settings.polling_interval || 5;

        console.log(`Starting AI Polling Service (Interval: ${intervalMinutes}m)`);

        const poll = async () => {
          try {
            console.log("Running Scheduled AI Scan...");
            // Trigger News Analysis
            await fetch('http://localhost:8000/autonomous/analyze-news', { method: 'POST' });
            // Trigger Trading Cycle (includes intraday checks)
            await fetch('http://localhost:8000/autonomous/trade', { method: 'POST' });
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
          <Route path="/" element={<Dashboard />} />
          <Route path="/portfolio" element={<PortfolioView />} />
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
