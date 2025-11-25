import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, TrendingUp, TrendingDown, Activity, BarChart2, X } from 'lucide-react';
import { API_BASE_URL } from '../config';

const StockDetailModal = ({ symbol, onClose }) => {
    const [details, setDetails] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDetails = async () => {
            try {
                const response = await axios.get(`${API_BASE_URL}/market/quote/${symbol}`);
                setDetails(response.data);
            } catch (error) {
                console.error("Error fetching stock details:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchDetails();
    }, [symbol]);

    if (!symbol) return null;

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="card w-96 relative animate-fade-in">
                <button onClick={onClose} className="absolute top-4 right-4 text-text-secondary hover:text-white">
                    <X className="w-5 h-5" />
                </button>
                <h2 className="text-xl font-bold text-white mb-4">{symbol} Details</h2>
                {loading ? (
                    <div className="text-center p-4 text-primary animate-pulse">Loading...</div>
                ) : details ? (
                    <div className="space-y-4">
                        <div className="flex justify-between items-center">
                            <span className="text-text-secondary">Price</span>
                            <span className="text-2xl font-bold text-white">{details.price}</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-text-secondary">Change</span>
                            <span className={`font-bold ${details.changePercent >= 0 ? 'text-secondary' : 'text-danger'}`}>
                                {details.changePercent}%
                            </span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-text-secondary">Volume</span>
                            <span className="text-white">{details.volume?.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-text-secondary">High</span>
                            <span className="text-white">{details.high}</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-text-secondary">Low</span>
                            <span className="text-white">{details.low}</span>
                        </div>
                    </div>
                ) : (
                    <div className="text-center text-danger">Failed to load details</div>
                )}
            </div>
        </div>
    );
};

const MarketView = () => {
    const [marketData, setMarketData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [isSearching, setIsSearching] = useState(false);
    const [selectedSymbol, setSelectedSymbol] = useState(null);

    useEffect(() => {
        const fetchMarketData = async () => {
            try {
                const response = await axios.get(`${API_BASE_URL}/market/summary`);
                setMarketData(response.data);
            } catch (error) {
                console.error("Error fetching market data:", error);
                setMarketData({ error: "Failed to load market data" });
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
                    const response = await axios.get(`${API_BASE_URL}/market/search?q=${searchTerm}`);
                    setSearchResults(response.data);
                } catch (error) {
                    console.error("Error searching:", error);
                    setSearchResults([]);
                } finally {
                    setIsSearching(false);
                }
            } else {
                setSearchResults([]);
            }
        }, 500);

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
        <div className="space-y-8 animate-fade-in">
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
