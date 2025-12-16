import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { TrendingUp, TrendingDown, DollarSign, Activity, History, RefreshCw, X, ChevronDown, Check, ThumbsUp, ThumbsDown, PlusCircle, Calendar, Edit2 } from 'lucide-react';
import { ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { API_BASE_URL } from '../config';

// Manual Add Stock Modal
const AddStockModal = ({ onClose, onAdd }) => {
    const [formData, setFormData] = useState({
        symbol: '',
        quantity: 1,
        price: 0,
        date: new Date().toISOString().split('T')[0],
        reasoning: ''
    });

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await axios.post(`${API_BASE_URL}/autonomous/holdings/add`, {
                symbol: formData.symbol.toUpperCase(),
                quantity: parseInt(formData.quantity),
                price: parseFloat(formData.price),
                date: new Date(formData.date).toISOString(),
                reasoning: formData.reasoning
            });
            onAdd();
            onClose();
        } catch (error) {
            console.error("Error adding stock manually", error);
            alert("Failed to add stock");
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="card w-full max-w-lg bg-surface border border-slate-700 animate-fade-in relative">
                <button onClick={onClose} className="absolute top-4 right-4 text-text-secondary hover:text-white">
                    <X className="w-6 h-6" />
                </button>
                <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
                    <PlusCircle className="text-accent" /> Add Stock Manually
                </h2>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm text-text-secondary mb-1">Symbol</label>
                            <input
                                type="text"
                                required
                                value={formData.symbol}
                                onChange={e => setFormData({ ...formData, symbol: e.target.value })}
                                className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white uppercase focus:border-accent outline-none"
                                placeholder="e.g. TRG"
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-text-secondary mb-1">Quantity</label>
                            <input
                                type="number"
                                required
                                min="1"
                                step="1"
                                value={formData.quantity}
                                onChange={e => setFormData({ ...formData, quantity: Math.floor(e.target.value) })}
                                className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white focus:border-accent outline-none"
                            />
                        </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm text-text-secondary mb-1">Buy Price (Rs)</label>
                            <input
                                type="number"
                                required
                                step="0.01"
                                value={formData.price}
                                onChange={e => setFormData({ ...formData, price: e.target.value })}
                                className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white focus:border-accent outline-none"
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-text-secondary mb-1">Date Purchased</label>
                            <input
                                type="date"
                                required
                                value={formData.date}
                                onChange={e => setFormData({ ...formData, date: e.target.value })}
                                className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white focus:border-accent outline-none"
                            />
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm text-text-secondary mb-1">Reasoning / Notes</label>
                        <textarea
                            required
                            value={formData.reasoning}
                            onChange={e => setFormData({ ...formData, reasoning: e.target.value })}
                            className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white focus:border-accent outline-none h-24 resize-none"
                            placeholder="Why did you buy this? e.g. 'Strong earnings report expected'"
                        />
                    </div>
                    <button type="submit" className="btn btn-accent w-full py-3 font-bold mt-4">
                        Add to Portfolio
                    </button>
                </form>
            </div>
        </div>
    );
};

const EditBudgetModal = ({ currentBudget, onClose, onUpdate }) => {
    const [budget, setBudget] = useState(currentBudget);

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await axios.post(`${API_BASE_URL}/settings`, {
                ai_cash_balance: parseFloat(budget)
            });
            onUpdate();
            onClose();
        } catch (error) {
            console.error("Error updating budget", error);
            alert("Failed to update budget");
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="card w-full max-w-sm bg-surface border border-slate-700 animate-fade-in relative">
                <button onClick={onClose} className="absolute top-4 right-4 text-text-secondary hover:text-white">
                    <X className="w-6 h-6" />
                </button>
                <h2 className="text-xl font-bold text-white mb-4">Edit Available Budget</h2>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm text-text-secondary mb-1">New Balance (Rs)</label>
                        <input
                            type="number"
                            step="0.01"
                            required
                            value={budget}
                            onChange={(e) => setBudget(e.target.value)}
                            className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white focus:border-accent outline-none"
                        />
                    </div>
                    <button type="submit" className="btn btn-primary w-full py-2">Update Balance</button>
                </form>
            </div>
        </div>
    );
};

// Stock Detail Modal Component (reused from MarketView)
const StockDetailModal = ({ symbol, onClose, portfolioItem, onUpdate }) => {
    const [klines, setKlines] = useState([]);
    const [info, setInfo] = useState(null);
    const [loading, setLoading] = useState(true);
    const [notes, setNotes] = useState(portfolioItem?.user_reasoning || '');
    const [savingNotes, setSavingNotes] = useState(false);
    const [sellMode, setSellMode] = useState(false);
    const [sellQty, setSellQty] = useState(portfolioItem?.quantity || 0);
    const [sellPrice, setSellPrice] = useState(portfolioItem?.current_price || 0);
    const [sellReason, setSellReason] = useState('');

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [klineRes, infoRes] = await Promise.all([
                    axios.get(`${API_BASE_URL}/market/klines/${symbol}?timeframe=1d`),
                    axios.get(`${API_BASE_URL}/market/company/${symbol}`)
                ]);

                const processedData = klineRes.data.map(k => ({
                    date: new Date(k.timestamp).toLocaleDateString(),
                    price: k.close,
                    volume: k.volume
                }));

                setKlines(processedData);
                setInfo(infoRes.data);
                if (portfolioItem && portfolioItem.current_price > 0) {
                    setSellPrice(portfolioItem.current_price);
                } else if (processedData.length > 0) {
                    setSellPrice(processedData[processedData.length - 1].price);
                }
            } catch (error) {
                console.error("Error fetching details", error);
            } finally {
                setLoading(false);
            }
        };
        if (symbol) fetchData();
    }, [symbol, portfolioItem]);

    const handleSaveNotes = async () => {
        setSavingNotes(true);
        try {
            await axios.post(`${API_BASE_URL}/autonomous/holdings/update-notes`, {
                symbol: symbol,
                notes: notes
            });
            if (onUpdate) onUpdate();
            alert("Notes updated!");
        } catch (e) {
            console.error(e);
            alert("Failed to save notes");
        } finally {
            setSavingNotes(false);
        }
    };

    const handleSell = async (e) => {
        e.preventDefault();
        try {
            await axios.post(`${API_BASE_URL}/autonomous/holdings/sell`, {
                symbol: symbol,
                quantity: parseInt(sellQty),
                price: parseFloat(sellPrice),
                reason: sellReason
            });
            onClose();
            if (onUpdate) onUpdate();
        } catch (e) {
            console.error(e);
            alert("Failed to sell stock: " + (e.response?.data?.detail || e.message));
        }
    };

    if (!symbol) return null;

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="card w-full max-w-4xl max-h-[90vh] overflow-y-auto relative animate-fade-in flex flex-col md:flex-row gap-6">
                <button onClick={onClose} className="absolute top-4 right-4 text-text-secondary hover:text-white z-10">
                    <X className="w-6 h-6" />
                </button>

                {/* Left Side: Chart & Info */}
                <div className="flex-1 space-y-6">
                    {loading ? (
                        <div className="h-64 flex items-center justify-center text-primary animate-pulse">Loading Details...</div>
                    ) : (
                        <div className="space-y-6">
                            <div>
                                <h2 className="text-3xl font-bold text-white flex items-center gap-3">
                                    {symbol}
                                    {info?.financialStats?.marketCap && (
                                        <span className="text-sm font-normal px-2 py-1 bg-slate-800 rounded text-text-secondary">
                                            Cap: {info.financialStats.marketCap.raw}
                                        </span>
                                    )}
                                </h2>
                                <p className="text-text-secondary mt-2">{info?.businessDescription?.substring(0, 150)}...</p>
                            </div>

                            <div className="h-[300px] w-full bg-slate-900/50 rounded-lg p-4 border border-slate-700">
                                <ResponsiveContainer width="100%" height="100%">
                                    <ComposedChart data={klines}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                        <XAxis dataKey="date" stroke="#94a3b8" tick={{ fontSize: 12 }} />
                                        <YAxis yAxisId="left" stroke="#94a3b8" domain={['auto', 'auto']} tick={{ fontSize: 12 }} />
                                        <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }} />
                                        <Line yAxisId="left" type="monotone" dataKey="price" stroke="#10b981" strokeWidth={2} dot={false} />
                                    </ComposedChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    )}
                </div>

                {/* Right Side: Management */}
                {portfolioItem && (
                    <div className="w-full md:w-1/3 space-y-6 border-l border-slate-700 pl-6">
                        <h3 className="text-xl font-bold text-white flex items-center gap-2">
                            <Activity className="w-5 h-5 text-accent" /> Management
                        </h3>

                        {/* Notes Section */}
                        <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700">
                            <label className="block text-sm font-bold text-white mb-2">Strategy Notes</label>
                            <p className="text-xs text-text-secondary mb-2">The AI considers these notes when making decisions.</p>
                            <textarea
                                className="w-full bg-slate-900 border border-slate-600 rounded p-2 text-white h-32 text-sm focus:border-accent outline-none"
                                value={notes}
                                onChange={(e) => setNotes(e.target.value)}
                                placeholder="E.g. Hold until 30% profit, Sell if drops below 100..."
                            ></textarea>
                            <button
                                onClick={handleSaveNotes}
                                disabled={savingNotes}
                                className="mt-2 w-full btn btn-secondary py-1 text-sm"
                            >
                                {savingNotes ? 'Saving...' : 'Update Notes'}
                            </button>
                        </div>

                        {/* Sell Section */}
                        <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700">
                            {!sellMode ? (
                                <button
                                    onClick={() => setSellMode(true)}
                                    className="w-full btn btn-danger py-2"
                                >
                                    Sell Stock
                                </button>
                            ) : (
                                <form onSubmit={handleSell} className="space-y-3">
                                    <h4 className="font-bold text-white border-b border-slate-600 pb-2">Manual Sell</h4>
                                    <div>
                                        <label className="text-xs text-text-secondary">Quantity (Max: {portfolioItem.quantity})</label>
                                        <input
                                            type="number"
                                            max={portfolioItem.quantity}
                                            min="1"
                                            step="1"
                                            value={sellQty}
                                            onChange={(e) => setSellQty(Math.floor(e.target.value))}
                                            className="w-full bg-slate-900 border border-slate-600 rounded p-1 text-white"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-xs text-text-secondary">Price</label>
                                        <input
                                            type="number"
                                            step="0.01"
                                            value={sellPrice}
                                            onChange={(e) => setSellPrice(e.target.value)}
                                            className="w-full bg-slate-900 border border-slate-600 rounded p-1 text-white"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-xs text-text-secondary">Reason</label>
                                        <input
                                            type="text"
                                            required
                                            value={sellReason}
                                            onChange={(e) => setSellReason(e.target.value)}
                                            className="w-full bg-slate-900 border border-slate-600 rounded p-1 text-white"
                                            placeholder="Why sell?"
                                        />
                                    </div>
                                    <div className="flex gap-2">
                                        <button type="button" onClick={() => setSellMode(false)} className="flex-1 btn bg-slate-600 text-white py-1">Cancel</button>
                                        <button type="submit" className="flex-1 btn btn-danger py-1">Confirm Sell</button>
                                    </div>
                                </form>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

const AIStockDashboard = () => {
    const [portfolio, setPortfolio] = useState({ holdings: [], summary: { total_value: 0, total_pnl: 0 } });
    const [notifications, setNotifications] = useState([]);
    const [tradeHistory, setTradeHistory] = useState([]);
    const [recommendations, setRecommendations] = useState([]);
    const [loading, setLoading] = useState(false);
    const [trading, setTrading] = useState(false);
    const [selectedSymbol, setSelectedSymbol] = useState(null);
    const [showTradeHistory, setShowTradeHistory] = useState(false);
    const [showAddModal, setShowAddModal] = useState(false);
    const [showBudgetModal, setShowBudgetModal] = useState(false);

    const [activeTab, setActiveTab] = useState('dashboard'); // 'dashboard' or 'actions'
    const [activityFilter, setActivityFilter] = useState('all'); // 'today', 'week', 'month', 'custom', 'all'
    const [customDays, setCustomDays] = useState(3);

    const fetchData = async (forceRefreshPrice = false) => {
        // Only show loading spinner on very first load if data is empty, or manage it via initial state.
        // We removed setLoading(true) here to prevent flash on every interval.
        try {
            // If it's the initial load or a specific refresh, we can try a 2-step load:
            // 1. Get cached data (Fast)
            // 2. Get live data (Slower) if needed

            // For periodic updates (interval), we usually want live prices (refresh_prices=true),
            // but for first load, we want speed.

            // Strategy:
            // ALWAYS fetch standard (cached) first if we aren't specifically forcing a price refresh.
            // THEN, if it was a fast fetch, trigger a background refresh.

            const portfolioRes = await axios.get(`${API_BASE_URL}/autonomous/portfolio?refresh_prices=${forceRefreshPrice}`);
            setPortfolio(portfolioRes.data);

            // Parallel fetch for logs
            const [notifRes, tradeRes, recRes] = await Promise.all([
                axios.get(`${API_BASE_URL}/autonomous/notifications`),
                axios.get(`${API_BASE_URL}/autonomous/trade-history`),
                axios.get(`${API_BASE_URL}/autonomous/recommendations`)
            ]);

            setNotifications(notifRes.data);
            setTradeHistory(tradeRes.data);
            setRecommendations(recRes.data);

            // If we did a fast load (forceRefreshPrice=false), trigger a background refresh
            if (!forceRefreshPrice) {
                // Quietly update prices in background
                axios.get(`${API_BASE_URL}/autonomous/portfolio?refresh_prices=true`)
                    .then(res => {
                        console.log("Background price update complete");
                        setPortfolio(res.data);
                    })
                    .catch(err => console.error("Background refresh failed", err));
            }

        } catch (error) {
            console.error("Error fetching AI data", error);
        } finally {
            setLoading(false);
        }
    };

    const triggerTrade = async () => {
        setTrading(true);
        try {
            await axios.post(`${API_BASE_URL}/autonomous/trade`);
            fetchData();
        } catch (error) {
            console.error("Error triggering trade", error);
        } finally {
            setTrading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, []);

    // Filter trades to only show those with P&L (sells)
    const pnlTrades = tradeHistory.filter(t => t.pnl != null);

    // Filter Notifications
    const filteredNotifications = notifications.filter(n => {
        if (activityFilter === 'all') return true;
        const noteDate = new Date(n.timestamp);
        const now = new Date();

        if (activityFilter === 'today') {
            return noteDate.toDateString() === now.toDateString();
        }
        if (activityFilter === 'week') {
            const weekAgo = new Date();
            weekAgo.setDate(now.getDate() - 7);
            return noteDate >= weekAgo;
        }
        if (activityFilter === 'month') {
            const monthAgo = new Date();
            monthAgo.setDate(now.getDate() - 30);
            return noteDate >= monthAgo;
        }
        if (activityFilter === 'custom') {
            const customAgo = new Date();
            customAgo.setDate(now.getDate() - customDays);
            return noteDate >= customAgo;
        }
        return true;
    });

    const handleRecommendation = async (id, action) => {
        try {
            await axios.post(`${API_BASE_URL}/autonomous/recommendations/${id}/${action}`);
            fetchData();
        } catch (error) {
            console.error(`Error ${action} recommendation`, error);
        }
    };

    return (
        <div className="space-y-6 animate-slide-up">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                        <Activity className="w-8 h-8 text-accent" /> AI Bot Dashboard
                    </h1>
                    <p className="text-text-secondary mt-1">Autonomous trading performance and activity log.</p>
                </div>
                <div className="flex gap-2 items-center">
                    {/* Tabs */}
                    <div className="bg-slate-800 p-1 rounded-lg flex mr-4">
                        <button
                            onClick={() => setActiveTab('dashboard')}
                            className={`px-4 py-2 rounded-md transition-colors ${activeTab === 'dashboard' ? 'bg-primary text-white font-bold' : 'text-text-secondary hover:text-white'}`}
                        >
                            Dashboard
                        </button>
                        <button
                            onClick={() => setActiveTab('actions')}
                            className={`px-4 py-2 rounded-md transition-colors flex items-center gap-2 ${activeTab === 'actions' ? 'bg-primary text-white font-bold' : 'text-text-secondary hover:text-white'}`}
                        >
                            Actions
                            {recommendations.length > 0 && (
                                <span className="bg-danger text-white text-xs px-1.5 rounded-full animate-pulse">{recommendations.length}</span>
                            )}
                        </button>
                    </div>

                    <button
                        onClick={() => setShowAddModal(true)}
                        className="btn btn-secondary flex items-center gap-2"
                    >
                        <PlusCircle className="w-4 h-4" />
                        Add Stock
                    </button>
                    <button
                        onClick={triggerTrade}
                        disabled={trading}
                        className="btn btn-accent flex items-center gap-2"
                    >
                        <RefreshCw className={`w-4 h-4 ${trading ? 'animate-spin' : ''}`} />
                        {trading ? 'Running...' : 'Run Analysis'}
                    </button>
                </div>
            </div>

            {activeTab === 'actions' && (
                <div className="space-y-6 animate-fade-in">
                    <div className="card border-l-4 border-l-accent">
                        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                            <Activity className="w-5 h-5 text-accent" /> Pending Recommendations
                        </h2>
                        {recommendations.length === 0 ? (
                            <div className="text-center py-12 text-text-secondary bg-slate-800/30 rounded-lg">
                                <Check className="w-12 h-12 mx-auto mb-3 opacity-20" />
                                <p>No pending actions. The AI is monitoring the market.</p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {recommendations.map(rec => (
                                    <div key={rec.id} className="bg-slate-800 p-4 rounded-lg border border-slate-700 flex flex-col justify-between">
                                        <div>
                                            <div className="flex justify-between items-start mb-2">
                                                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                                                    {rec.symbol}
                                                    <span className={`text-xs px-2 py-0.5 rounded ${rec.action === 'BUY' ? 'bg-emerald-500/20 text-emerald-500' : 'bg-rose-500/20 text-rose-500'}`}>
                                                        {rec.action}
                                                    </span>
                                                </h3>
                                                <span className="text-xs text-text-secondary">{new Date(rec.timestamp).toLocaleString()}</span>
                                            </div>
                                            <div className="text-sm text-text-secondary mb-3">
                                                <p>Size: <span className="text-white font-medium">{rec.quantity} shares</span> @ ~Rs. {rec.price.toFixed(2)}</p>
                                                <p className="mt-2 text-text-muted italic">"{rec.reason}"</p>
                                            </div>
                                        </div>
                                        <div className="flex gap-3 mt-4">
                                            <button
                                                onClick={() => handleRecommendation(rec.id, 'approve')}
                                                className="flex-1 btn bg-emerald-600 hover:bg-emerald-500 text-white py-2 rounded flex items-center justify-center gap-2"
                                            >
                                                <ThumbsUp className="w-4 h-4" /> Approve
                                            </button>
                                            <button
                                                onClick={() => handleRecommendation(rec.id, 'deny')}
                                                className="flex-1 btn bg-slate-700 hover:bg-slate-600 text-white py-2 rounded flex items-center justify-center gap-2"
                                            >
                                                <ThumbsDown className="w-4 h-4" /> Deny
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {activeTab === 'dashboard' && (
                <>
                    {/* Summary Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                        <div className="card bg-gradient-to-br from-surface to-surface/50">
                            <div className="flex items-center gap-4">
                                <div className="p-3 bg-primary/10 rounded-lg text-primary">
                                    <DollarSign className="w-6 h-6" />
                                </div>
                                <div>
                                    <p className="text-text-secondary text-sm">Net Worth</p>
                                    <p className="text-2xl font-bold text-white">
                                        Rs. {portfolio.summary.total_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className="card bg-gradient-to-br from-surface to-surface/50 relative group">
                            <button
                                onClick={() => setShowBudgetModal(true)}
                                className="absolute top-2 right-2 text-text-secondary hover:text-accent opacity-0 group-hover:opacity-100 transition-opacity"
                                title="Edit Budget"
                            >
                                <Edit2 className="w-4 h-4" />
                            </button>
                            <div className="flex items-center gap-4">
                                <div className="p-3 bg-emerald-500/10 rounded-lg text-emerald-500">
                                    <DollarSign className="w-6 h-6" />
                                </div>
                                <div>
                                    <p className="text-text-secondary text-sm">Available Budget</p>
                                    <p className="text-2xl font-bold text-white">
                                        Rs. {portfolio.summary.cash_balance?.toLocaleString(undefined, { minimumFractionDigits: 2 }) || '0.00'}
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className="card bg-gradient-to-br from-surface to-surface/50">
                            <div className="flex items-center gap-4">
                                <div className={`p-3 rounded-lg ${portfolio.summary.total_pnl >= 0 ? 'bg-secondary/10 text-secondary' : 'bg-danger/10 text-danger'}`}>
                                    {portfolio.summary.total_pnl >= 0 ? <TrendingUp className="w-6 h-6" /> : <TrendingDown className="w-6 h-6" />}
                                </div>
                                <div>
                                    <p className="text-text-secondary text-sm">Unrealized PnL</p>
                                    <p className={`text-2xl font-bold ${portfolio.summary.total_pnl >= 0 ? 'text-secondary' : 'text-danger'}`}>
                                        {portfolio.summary.total_pnl >= 0 ? '+' : ''}Rs. {portfolio.summary.total_pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className="card bg-gradient-to-br from-surface to-surface/50">
                            <div className="flex items-center gap-4">
                                <div className="p-3 bg-accent/10 rounded-lg text-accent">
                                    <Activity className="w-6 h-6" />
                                </div>
                                <div>
                                    <p className="text-text-secondary text-sm">Active Positions</p>
                                    <p className="text-2xl font-bold text-white">
                                        {portfolio.holdings.length}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Overall Performance Card */}
                    <div className="card bg-gradient-to-br from-primary/5 to-secondary/5 border border-primary/20">
                        <h2 className="text-xl font-bold text-white mb-4">Overall Performance</h2>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                            <div>
                                <p className="text-text-secondary text-sm mb-1">Initial Capital</p>
                                <p className="text-2xl font-bold text-white">
                                    Rs. {(portfolio.summary.initial_capital || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                </p>
                            </div>
                            <div>
                                <p className="text-text-secondary text-sm mb-1">Current Net Worth</p>
                                <p className="text-2xl font-bold text-white">
                                    Rs. {portfolio.summary.total_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                </p>
                            </div>
                            <div>
                                <p className="text-text-secondary text-sm mb-1">Realized PnL</p>
                                <p className={`text-2xl font-bold ${(portfolio.summary.realized_pnl || 0) >= 0 ? 'text-secondary' : 'text-danger'}`}>
                                    {(portfolio.summary.realized_pnl || 0) >= 0 ? '+' : ''}Rs. {(portfolio.summary.realized_pnl || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                </p>
                            </div>
                            <div>
                                <p className="text-text-secondary text-sm mb-1">Return %</p>
                                <p className={`text-2xl font-bold ${(portfolio.summary.overall_pnl_percent || 0) >= 0 ? 'text-secondary' : 'text-danger'}`}>
                                    {(portfolio.summary.overall_pnl_percent || 0) >= 0 ? '+' : ''}{(portfolio.summary.overall_pnl_percent || 0).toFixed(2)}%
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* Portfolio Table */}
                        <div className="lg:col-span-2 card space-y-4">
                            <h2 className="text-xl font-bold text-white mb-4">Current Holdings</h2>
                            <div className="overflow-x-auto">
                                <table className="w-full text-left">
                                    <thead className="text-text-secondary border-b border-slate-700">
                                        <tr>
                                            <th className="pb-3">Symbol</th>
                                            <th className="pb-3">Qty</th>
                                            <th className="pb-3">Avg Cost</th>
                                            <th className="pb-3">Current</th>
                                            <th className="pb-3">PnL</th>
                                            <th className="pb-3">Decision</th>
                                            <th className="pb-3">Date</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-700">
                                        {portfolio.holdings.length === 0 ? (
                                            <tr>
                                                <td colSpan="7" className="py-4 text-center text-text-secondary">No active positions.</td>
                                            </tr>
                                        ) : (
                                            portfolio.holdings.map((item) => (
                                                <tr
                                                    key={item.symbol}
                                                    className="group hover:bg-slate-800/50 transition-colors cursor-pointer"
                                                    onClick={() => setSelectedSymbol(item.symbol)}
                                                >
                                                    <td className="py-4 font-bold text-white">{item.symbol}</td>
                                                    <td className="py-4 text-text-primary">{item.quantity}</td>
                                                    <td className="py-4 text-text-secondary">Rs. {item.avg_cost.toFixed(2)}</td>
                                                    <td className="py-4 text-text-primary">Rs. {item.current_price.toFixed(2)}</td>
                                                    <td className={`py-4 font-bold ${item.pnl >= 0 ? 'text-secondary' : 'text-danger'}`}>
                                                        {item.pnl >= 0 ? '+' : ''}{item.pnl.toFixed(2)} ({item.pnl_percent.toFixed(1)}%)
                                                    </td>
                                                    <td className="py-4 text-xs">
                                                        {item.last_decision ? (
                                                            <div className="flex flex-col">
                                                                <span className={`font-bold ${item.last_decision === 'SELL' ? 'text-danger' :
                                                                    item.last_decision === 'BUY_MORE' ? 'text-secondary' : 'text-text-secondary'
                                                                    }`}>
                                                                    {item.last_decision}
                                                                </span>
                                                                {item.last_reason && (
                                                                    <span className="text-[10px] text-text-muted truncate max-w-[120px]" title={item.last_reason}>
                                                                        {item.last_reason.substring(0, 30)}...
                                                                    </span>
                                                                )}
                                                            </div>
                                                        ) : (
                                                            <span className="text-text-secondary">-</span>
                                                        )}
                                                    </td>
                                                    <td className="py-4 text-text-secondary text-sm">
                                                        <div className="flex flex-col">
                                                            <span>{new Date(item.purchased_at).toLocaleDateString()}</span>
                                                            {item.user_reasoning && (
                                                                <span className="text-[10px] text-accent truncate max-w-[100px]" title={item.user_reasoning}>Has Notes</span>
                                                            )}
                                                        </div>
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        {/* Notifications Log */}
                        <div className="card space-y-4 h-[500px] flex flex-col">
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                    <History className="w-5 h-5 text-text-secondary" /> Activity Log
                                </h2>
                                <div className="flex items-center gap-2">
                                    {activityFilter === 'custom' && (
                                        <div className="flex items-center gap-1 bg-slate-900 border border-slate-700 rounded px-2">
                                            <span className="text-xs text-text-secondary">Days:</span>
                                            <input
                                                type="number"
                                                min="1"
                                                max="365"
                                                value={customDays}
                                                onChange={(e) => setCustomDays(parseInt(e.target.value) || 1)}
                                                className="w-12 bg-transparent text-xs text-white outline-none py-1 text-right"
                                            />
                                        </div>
                                    )}
                                    <select
                                        className="bg-slate-900 border border-slate-700 text-xs rounded px-2 py-1 text-text-secondary outline-none focus:border-accent"
                                        value={activityFilter}
                                        onChange={(e) => setActivityFilter(e.target.value)}
                                    >
                                        <option value="today">Today</option>
                                        <option value="week">Last 7 Days</option>
                                        <option value="month">Last 30 Days</option>
                                        <option value="custom">Custom</option>
                                        <option value="all">All Time</option>
                                    </select>
                                </div>
                            </div>
                            <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
                                {filteredNotifications.length === 0 ? (
                                    <p className="text-text-secondary text-center py-4">No recent activity.</p>
                                ) : (
                                    filteredNotifications.map((note) => (
                                        <div key={note.id} className="p-3 rounded-lg bg-slate-800/50 border border-slate-700 hover:border-slate-600 transition-colors">
                                            <div className="flex justify-between items-start mb-1">
                                                <span className={`text-xs font-bold px-2 py-0.5 rounded ${note.type === 'TRADE' ? 'bg-accent/20 text-accent' : 'bg-primary/20 text-primary'}`}>
                                                    {note.type}
                                                </span>
                                                <span className="text-xs text-text-secondary">
                                                    {new Date(note.timestamp + "Z").toLocaleString('en-US', {
                                                        timeZone: 'Asia/Karachi',
                                                        month: 'short',
                                                        day: 'numeric',
                                                        hour: '2-digit',
                                                        minute: '2-digit'
                                                    })}
                                                </span>
                                            </div>
                                            <h4 className="font-medium text-white text-sm">{note.title}</h4>
                                            <p className="text-xs text-text-secondary mt-1">{note.message}</p>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                    {/* P&L History - Collapsible, at end */}
                    <div className="card">
                        <button
                            onClick={() => setShowTradeHistory(!showTradeHistory)}
                            className="w-full flex items-center justify-between text-left"
                        >
                            <h2 className="text-xl font-bold text-white">P&L History ({pnlTrades.length} transactions)</h2>
                            <ChevronDown className={`w-5 h-5 text-text-secondary transition-transform ${showTradeHistory ? 'rotate-180' : ''}`} />
                        </button>

                        {showTradeHistory && (
                            <div className="overflow-x-auto mt-4">
                                <table className="w-full text-left text-sm">
                                    <thead className="text-text-secondary border-b border-slate-700">
                                        <tr>
                                            <th className="pb-3">Date/Time</th>
                                            <th className="pb-3">Symbol</th>
                                            <th className="pb-3 text-right">Quantity</th>
                                            <th className="pb-3 text-right">Sell Price</th>
                                            <th className="pb-3 text-right">P&L</th>
                                            <th className="pb-3">Reason</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-700">
                                        {pnlTrades.length === 0 ? (
                                            <tr>
                                                <td colSpan="6" className="py-4 text-center text-text-secondary">No P&L transactions yet.</td>
                                            </tr>
                                        ) : (
                                            pnlTrades.map((trade, idx) => (
                                                <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                                                    <td className="py-3 text-text-muted">
                                                        {new Date(trade.timestamp + "Z").toLocaleString('en-US', {
                                                            timeZone: 'Asia/Karachi',
                                                            month: 'short',
                                                            day: 'numeric',
                                                            hour: '2-digit',
                                                            minute: '2-digit'
                                                        })}
                                                    </td>
                                                    <td className="py-3 font-medium text-white">{trade.symbol}</td>
                                                    <td className="py-3 text-right text-text-primary">{trade.quantity}</td>
                                                    <td className="py-3 text-right text-text-secondary">Rs. {trade.price.toFixed(2)}</td>
                                                    <td className={`py-3 text-right font-bold ${trade.pnl >= 0 ? 'text-secondary' : 'text-danger'}`}>
                                                        {trade.pnl >= 0 ? '+' : ''}Rs. {trade.pnl.toFixed(2)}
                                                    </td>
                                                    <td className="py-3 text-text-muted text-xs max-w-xs truncate" title={trade.reason}>
                                                        {trade.reason || 'N/A'}
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>

                    {/* Stock Detail Modal */}
                    {selectedSymbol && (
                        <StockDetailModal
                            symbol={selectedSymbol}
                            onClose={() => setSelectedSymbol(null)}
                            portfolioItem={portfolio.holdings.find(h => h.symbol === selectedSymbol)}
                            onUpdate={fetchData}
                        />
                    )}

                    {/* Add Stock Modal */}
                    {showAddModal && (
                        <AddStockModal onClose={() => setShowAddModal(false)} onAdd={fetchData} />
                    )}

                    {/* Edit Budget Modal */}
                    {showBudgetModal && (
                        <EditBudgetModal
                            currentBudget={portfolio.summary.cash_balance || 0}
                            onClose={() => setShowBudgetModal(false)}
                            onUpdate={fetchData}
                        />
                    )}

                    {/* Edit Budget Modal */}
                    {showBudgetModal && (
                        <EditBudgetModal
                            currentBudget={portfolio.summary.cash_balance || 0}
                            onClose={() => setShowBudgetModal(false)}
                            onUpdate={fetchData}
                        />
                    )}
                </>
            )}
        </div>
    );
};

export default AIStockDashboard;
