import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { TrendingUp, TrendingDown, Activity, BarChart2, Search, X, Info } from 'lucide-react';
import { ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const StockDetailModal = ({ symbol, onClose }) => {
    const [klines, setKlines] = useState([]);
    const [info, setInfo] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [klineRes, infoRes] = await Promise.all([
                    axios.get(`http://localhost:8000/market/klines/${symbol}?timeframe=1d`),
                    axios.get(`http://localhost:8000/market/company/${symbol}`)
                ]);

                // Process K-Lines for Recharts
                const processedData = klineRes.data.map(k => ({
                    date: new Date(k.timestamp).toLocaleDateString(),
                    price: k.close,
                    volume: k.volume
                })); // Removed .reverse() to fix chronological order

                setKlines(processedData);
                setInfo(infoRes.data);
            } catch (error) {
                console.error("Error fetching details", error);
            } finally {
                setLoading(false);
            }
        };
        if (symbol) fetchData();
    }, [symbol]);

    if (!symbol) return null;

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="card w-full max-w-4xl max-h-[90vh] overflow-y-auto relative animate-fade-in">
                <button onClick={onClose} className="absolute top-4 right-4 text-text-secondary hover:text-white">
                    <X className="w-6 h-6" />
                </button>

                {loading ? (
                    <div className="h-64 flex items-center justify-center text-primary animate-pulse">Loading Details...</div>
                ) : (
                    <div className="space-y-6">
                        {/* Header */}
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

                        {/* Chart */}
                        <div className="h-[400px] w-full bg-slate-900/50 rounded-lg p-4 border border-slate-700">
                            <ResponsiveContainer width="100%" height="100%">
                                <ComposedChart data={klines}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                    <XAxis dataKey="date" stroke="#94a3b8" tick={{ fontSize: 12 }} />
                                    <YAxis yAxisId="left" stroke="#94a3b8" domain={['auto', 'auto']} tick={{ fontSize: 12 }} />
                                    <YAxis yAxisId="right" orientation="right" stroke="#64748b" tick={{ fontSize: 12 }} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                                    />
                                    <Bar yAxisId="right" dataKey="volume" fill="#3b82f6" opacity={0.3} />
                                    <Line yAxisId="left" type="monotone" dataKey="price" stroke="#10b981" strokeWidth={2} dot={false} />
                                </ComposedChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Key People */}
                        {info?.keyPeople && (
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                {info.keyPeople.slice(0, 3).map((p, idx) => (
                                    <div key={idx} className="bg-slate-800/50 p-3 rounded border border-slate-700">
                                        <div className="text-xs text-text-muted uppercase">{p.position}</div>
                                        <div className="font-medium text-white">{p.name}</div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

const MarketView = () => {
    const [marketData, setMarketData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedSymbol, setSelectedSymbol] = useState(null);

    // Search Logic - Moved up to fix Hook Rule violation
    const [searchResults, setSearchResults] = useState([]);
    const [isSearching, setIsSearching] = useState(false);

    useEffect(() => {
        const fetchMarketData = async () => {
            try {
                const res = await axios.get('http://localhost:8000/market/summary');
                setMarketData(res.data);
            } catch (error) {
                console.error("Error fetching market data", error);
            } finally {
                setLoading(false);
            }
        };
        fetchMarketData();
    }, []);

    useEffect(() => {
        const delayDebounceFn = setTimeout(async () => {
            if (searchTerm) {
                setIsSearching(true);
                try {
                    const res = await axios.get(`http://localhost:8000/market/search?q=${searchTerm}`);
                    setSearchResults(res.data);
                } catch (error) {
                    console.error("Search error", error);
                } finally {
                    setIsSearching(false);
                }
            } else {
                setSearchResults([]);
            }
        }, 500); // Debounce 500ms

        return () => clearTimeout(delayDebounceFn);
    }, [searchTerm]);

    if (loading) return <div className="text-center p-10 text-primary animate-pulse">Loading Market Data...</div>;
    if (!marketData || marketData.error) return (
        <div className="text-center p-10 text-danger">
            <h3 className="text-xl font-bold">Failed to load market data</h3>
            <p className="text-text-secondary">{marketData?.error || "Unknown error"}</p>
        </div>
    );

    return (
        <div className="space-y-8">
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold text-white">Market Overview</h1>
                    <p className="text-text-secondary mt-1">Real-time data from PSX Terminal</p>
                </div>
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary w-4 h-4" />
                    <input
                        type="text"
                        placeholder="Search Symbol..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="input pl-10 w-64"
                    />
                </div>
            </div>

            {/* Key Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="card">
                    <div className="flex items-center gap-3 mb-2">
                        <Activity className="text-primary w-5 h-5" />
                        <h3 className="text-text-secondary text-sm font-medium uppercase">Index</h3>
                    </div>
                    <p className="text-2xl font-bold text-white">{marketData?.index || "N/A"}</p>
                </div>
                <div className="card">
                    <div className="flex items-center gap-3 mb-2">
                        <BarChart2 className="text-accent w-5 h-5" />
                        <h3 className="text-text-secondary text-sm font-medium uppercase">Volume</h3>
                    </div>
                    <p className="text-2xl font-bold text-white">{(marketData?.volume || 0).toLocaleString()}</p>
                </div>
                <div className="card">
                    <div className="flex items-center gap-3 mb-2">
                        <TrendingUp className="text-secondary w-5 h-5" />
                        <h3 className="text-text-secondary text-sm font-medium uppercase">Gainers</h3>
                    </div>
                    <p className="text-2xl font-bold text-secondary">{marketData?.gainers || 0}</p>
                </div>
                <div className="card">
                    <div className="flex items-center gap-3 mb-2">
                        <TrendingDown className="text-danger w-5 h-5" />
                        <h3 className="text-text-secondary text-sm font-medium uppercase">Losers</h3>
                    </div>
                    <p className="text-2xl font-bold text-danger">{marketData?.losers || 0}</p>
                </div>
            </div>

            {/* Search Results or Top Movers */}
            {searchTerm ? (
                <div className="card p-0 overflow-hidden">
                    <div className="p-4 border-b border-slate-700 bg-surface/50">
                        <h3 className="font-bold text-white flex items-center gap-2">
                            <Search className="w-5 h-5" /> Search Results
                        </h3>
                    </div>
                    <table className="w-full text-left">
                        <thead className="bg-slate-900/50 text-text-secondary text-xs uppercase">
                            <tr>
                                <th className="p-3">Symbol</th>
                                <th className="p-3 text-right">Price</th>
                                <th className="p-3 text-right">Change</th>
                                <th className="p-3 text-right">Vol</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700">
                            {isSearching ? (
                                <tr><td colSpan="4" className="p-4 text-center text-text-secondary">Searching...</td></tr>
                            ) : Array.isArray(searchResults) && searchResults.length > 0 ? (
                                searchResults.map((stock, idx) => (
                                    <tr
                                        key={idx}
                                        className="hover:bg-slate-800/50 cursor-pointer transition-colors"
                                        onClick={() => setSelectedSymbol(stock.symbol)}
                                    >
                                        <td className="p-3 font-bold text-white">{stock?.symbol || "N/A"}</td>
                                        <td className="p-3 text-right text-text-primary">{stock?.price || 0}</td>
                                        <td className={`p-3 text-right ${stock?.changePercent >= 0 ? 'text-secondary' : 'text-danger'}`}>
                                            {stock?.changePercent > 0 ? '+' : ''}{stock?.changePercent || 0}%
                                        </td>
                                        <td className="p-3 text-right text-text-muted text-sm">{(stock?.volume || 0).toLocaleString()}</td>
                                    </tr>
                                ))
                            ) : (
                                <tr><td colSpan="4" className="p-4 text-center text-text-secondary">No results found via API.</td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Top Gainers */}
                    <div className="card p-0 overflow-hidden">
                        <div className="p-4 border-b border-slate-700 bg-surface/50">
                            <h3 className="font-bold text-secondary flex items-center gap-2">
                                <TrendingUp className="w-5 h-5" /> Top Gainers
                            </h3>
                        </div>
                        <table className="w-full text-left">
                            <thead className="bg-slate-900/50 text-text-secondary text-xs uppercase">
                                <tr>
                                    <th className="p-3">Symbol</th>
                                    <th className="p-3 text-right">Price</th>
                                    <th className="p-3 text-right">Change</th>
                                    <th className="p-3 text-right">Vol</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700">
                                {(Array.isArray(marketData?.top_gainers) ? marketData.top_gainers : []).map((stock, idx) => (
                                    <tr
                                        key={idx}
                                        className="hover:bg-slate-800/50 cursor-pointer transition-colors"
                                        onClick={() => setSelectedSymbol(stock.symbol)}
                                    >
                                        <td className="p-3 font-bold text-white">{stock?.symbol || "N/A"}</td>
                                        <td className="p-3 text-right text-text-primary">{stock?.price || 0}</td>
                                        <td className="p-3 text-right text-secondary">+{stock?.changePercent || 0}%</td>
                                        <td className="p-3 text-right text-text-muted text-sm">{(stock?.volume || 0).toLocaleString()}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Top Losers */}
                    <div className="card p-0 overflow-hidden">
                        <div className="p-4 border-b border-slate-700 bg-surface/50">
                            <h3 className="font-bold text-danger flex items-center gap-2">
                                <TrendingDown className="w-5 h-5" /> Top Losers
                            </h3>
                        </div>
                        <table className="w-full text-left">
                            <thead className="bg-slate-900/50 text-text-secondary text-xs uppercase">
                                <tr>
                                    <th className="p-3">Symbol</th>
                                    <th className="p-3 text-right">Price</th>
                                    <th className="p-3 text-right">Change</th>
                                    <th className="p-3 text-right">Vol</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700">
                                {(Array.isArray(marketData?.top_losers) ? marketData.top_losers : []).map((stock, idx) => (
                                    <tr
                                        key={idx}
                                        className="hover:bg-slate-800/50 cursor-pointer transition-colors"
                                        onClick={() => setSelectedSymbol(stock.symbol)}
                                    >
                                        <td className="p-3 font-bold text-white">{stock?.symbol || "N/A"}</td>
                                        <td className="p-3 text-right text-text-primary">{stock?.price || 0}</td>
                                        <td className="p-3 text-right text-danger">{stock?.changePercent || 0}%</td>
                                        <td className="p-3 text-right text-text-muted text-sm">{(stock?.volume || 0).toLocaleString()}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {selectedSymbol && (
                <StockDetailModal symbol={selectedSymbol} onClose={() => setSelectedSymbol(null)} />
            )}
        </div>
    );
};

export default MarketView;
