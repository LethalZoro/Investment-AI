import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Bell, ExternalLink, RefreshCw, TrendingUp, TrendingDown, AlertTriangle, Newspaper } from 'lucide-react';

const NewsView = () => {
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(false);
    const [analyzing, setAnalyzing] = useState(false);

    const fetchAlerts = async () => {
        setLoading(true);
        try {
            const res = await axios.get('http://localhost:8000/autonomous/alerts');
            setAlerts(res.data);
        } catch (error) {
            console.error("Error fetching alerts", error);
        } finally {
            setLoading(false);
        }
    };

    const triggerAnalysis = async () => {
        setAnalyzing(true);
        try {
            await axios.post('http://localhost:8000/autonomous/analyze-news');
            fetchAlerts();
        } catch (error) {
            console.error("Error triggering analysis", error);
        } finally {
            setAnalyzing(false);
        }
    };

    useEffect(() => {
        fetchAlerts();
    }, []);

    return (
        <div className="space-y-6 animate-slide-up">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                        <Newspaper className="w-8 h-8 text-primary" /> Market News & Signals
                    </h1>
                    <p className="text-text-secondary mt-1">Real-time news analysis and AI-generated trade signals.</p>
                </div>
                <button
                    onClick={triggerAnalysis}
                    disabled={analyzing}
                    className="btn btn-primary flex items-center gap-2"
                >
                    <RefreshCw className={`w-4 h-4 ${analyzing ? 'animate-spin' : ''}`} />
                    {analyzing ? 'Scanning Market...' : 'Scan Now'}
                </button>
            </div>

            {/* Alerts Grid */}
            <div className="grid grid-cols-1 gap-4">
                {alerts.length === 0 && !loading ? (
                    <div className="text-center p-10 text-text-secondary bg-surface rounded-xl border border-slate-700">
                        <Newspaper className="w-12 h-12 mx-auto mb-3 opacity-50" />
                        <p>No news analyzed yet. Click "Scan Now" to analyze the market.</p>
                    </div>
                ) : (
                    alerts.map((alert) => (
                        <div key={alert.id} className="card hover:border-primary/50 transition-colors group">
                            <div className="flex justify-between items-start">
                                <div className="flex items-start gap-4">
                                    <div className={`p-3 rounded-lg ${alert.signal === 'BUY' ? 'bg-secondary/10 text-secondary' :
                                        alert.signal === 'SELL' ? 'bg-danger/10 text-danger' :
                                            'bg-slate-700 text-slate-300'
                                        }`}>
                                        {alert.signal === 'BUY' ? <TrendingUp className="w-6 h-6" /> :
                                            alert.signal === 'SELL' ? <TrendingDown className="w-6 h-6" /> :
                                                <AlertTriangle className="w-6 h-6" />}
                                    </div>
                                    <div>
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="font-bold text-xl text-white">{alert.symbol}</span>
                                            <span className={`text-xs font-bold px-2 py-0.5 rounded ${alert.signal === 'BUY' ? 'bg-secondary/20 text-secondary' :
                                                alert.signal === 'SELL' ? 'bg-danger/20 text-danger' :
                                                    'bg-slate-700 text-slate-300'
                                                }`}>
                                                {alert.signal}
                                            </span>
                                            <span className="text-xs text-text-secondary">
                                                {new Date(alert.timestamp).toLocaleString()}
                                            </span>
                                        </div>
                                        <p className="text-text-primary leading-relaxed">{alert.reason}</p>
                                    </div>
                                </div>
                                {alert.url && (
                                    <a
                                        href={alert.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-text-secondary hover:text-primary transition-colors p-2"
                                        title="Read Source"
                                    >
                                        <ExternalLink className="w-5 h-5" />
                                    </a>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default NewsView;
