import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Briefcase, TrendingUp, TrendingDown, Plus, Trash2, X } from 'lucide-react';
import { API_BASE_URL } from '../config';

const SellModal = ({ isOpen, onClose, item, onSuccess }) => {
    const [quantity, setQuantity] = useState(item.quantity);
    const [price, setPrice] = useState(item.current_price);

    if (!isOpen) return null;

    const handleSell = async (e) => {
        e.preventDefault();
        try {
            await axios.post(`${API_BASE_URL}/portfolio/sell`, {
                symbol: item.symbol,
                quantity: parseInt(quantity),
                price: parseFloat(price)
            });
            onSuccess();
            onClose();
        } catch (error) {
            alert("Error selling item: " + (error.response?.data?.detail || error.message));
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="card w-96 relative animate-fade-in">
                <button onClick={onClose} className="absolute top-4 right-4 text-text-secondary hover:text-white">
                    <X className="w-5 h-5" />
                </button>
                <h2 className="text-xl font-bold text-white mb-4">Sell {item.symbol}</h2>
                <form onSubmit={handleSell} className="space-y-4">
                    <div>
                        <label className="block text-sm text-text-secondary mb-1">Quantity (Max: {item.quantity})</label>
                        <input
                            type="number"
                            value={quantity}
                            onChange={(e) => setQuantity(e.target.value)}
                            max={item.quantity}
                            min="1"
                            className="input w-full"
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm text-text-secondary mb-1">Sell Price</label>
                        <input
                            type="number"
                            value={price}
                            onChange={(e) => setPrice(e.target.value)}
                            className="input w-full"
                            required
                        />
                    </div>
                    <div className="p-3 bg-slate-800 rounded-lg">
                        <div className="flex justify-between text-sm mb-1">
                            <span className="text-text-secondary">Total Value:</span>
                            <span className="text-white font-bold">PKR {(quantity * price).toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-text-secondary">Est. PnL:</span>
                            <span className={`${(price - item.avg_cost) >= 0 ? 'text-secondary' : 'text-danger'} font-bold`}>
                                {((price - item.avg_cost) * quantity).toLocaleString()}
                            </span>
                        </div>
                    </div>
                    <button type="submit" className="btn btn-primary w-full bg-danger hover:bg-red-600 border-none">
                        Confirm Sell
                    </button>
                </form>
            </div>
        </div>
    );
};

const PortfolioView = () => {
    const [portfolio, setPortfolio] = useState({ holdings: [], summary: {} });
    const [loading, setLoading] = useState(true);
    const [newItem, setNewItem] = useState({ symbol: '', quantity: '', avg_cost: '', strategy_tag: 'UNASSIGNED' });
    const [isSellModalOpen, setIsSellModalOpen] = useState(false);
    const [selectedItem, setSelectedItem] = useState(null);
    const [transactions, setTransactions] = useState([]);
    const [activeTab, setActiveTab] = useState('holdings');

    const fetchPortfolio = async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/portfolio`);
            setPortfolio(response.data);
            const txResponse = await axios.get(`${API_BASE_URL}/portfolio/transactions`);
            setTransactions(txResponse.data);
        } catch (error) {
            console.error("Error fetching portfolio:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchPortfolio();
    }, []);

    const handleAdd = async (e) => {
        e.preventDefault();
        try {
            await axios.post(`${API_BASE_URL}/portfolio/add`, newItem);
            setNewItem({ symbol: '', quantity: '', avg_cost: '', strategy_tag: 'UNASSIGNED' });
            fetchPortfolio();
        } catch (error) {
            alert("Error adding position");
        }
    };

    const openSellModal = (item) => {
        setSelectedItem(item);
        setIsSellModalOpen(true);
    };

    if (loading) return <div className="text-center p-10 text-primary animate-pulse">Loading Portfolio...</div>;

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                        <Briefcase className="w-8 h-8 text-primary" /> Portfolio Management
                    </h1>
                    <p className="text-text-secondary mt-1">Track your holdings and performance.</p>
                </div>
                <div className="text-right">
                    <p className="text-sm text-text-secondary">Total PnL</p>
                    <p className={`text-2xl font-bold ${portfolio?.summary?.total_pnl >= 0 ? 'text-secondary' : 'text-danger'}`}>
                        {portfolio?.summary?.total_pnl >= 0 ? '+' : ''}PKR {portfolio?.summary?.total_pnl?.toLocaleString() || '0'}
                    </p>
                </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex border-b border-slate-700 mb-6">
                <button
                    className={`px-6 py-3 font-medium text-sm transition-colors border-b-2 ${activeTab === 'holdings' ? 'border-primary text-primary' : 'border-transparent text-text-secondary hover:text-white'}`}
                    onClick={() => setActiveTab('holdings')}
                >
                    Current Holdings
                </button>
                <button
                    className={`px-6 py-3 font-medium text-sm transition-colors border-b-2 ${activeTab === 'history' ? 'border-primary text-primary' : 'border-transparent text-text-secondary hover:text-white'}`}
                    onClick={() => setActiveTab('history')}
                >
                    Transaction History
                </button>
            </div>

            {activeTab === 'holdings' ? (
                <>
                    {/* Add New Position */}
                    <div className="card">
                        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                            <Plus className="w-5 h-5 text-primary" /> Add New Position
                        </h3>
                        <form onSubmit={handleAdd} className="grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
                            <div>
                                <label className="block text-sm text-text-secondary mb-1">Symbol</label>
                                <input
                                    type="text"
                                    value={newItem.symbol}
                                    onChange={e => setNewItem({ ...newItem, symbol: e.target.value.toUpperCase() })}
                                    className="input w-full"
                                    placeholder="e.g. OGDC"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-text-secondary mb-1">Quantity</label>
                                <input
                                    type="number"
                                    value={newItem.quantity}
                                    onChange={e => setNewItem({ ...newItem, quantity: parseInt(e.target.value) })}
                                    className="input w-full"
                                    placeholder="0"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-text-secondary mb-1">Avg Cost</label>
                                <input
                                    type="number"
                                    value={newItem.avg_cost}
                                    onChange={e => setNewItem({ ...newItem, avg_cost: parseFloat(e.target.value) })}
                                    className="input w-full"
                                    placeholder="0.00"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-text-secondary mb-1">Strategy</label>
                                <select
                                    value={newItem.strategy_tag}
                                    onChange={e => setNewItem({ ...newItem, strategy_tag: e.target.value })}
                                    className="input w-full appearance-none"
                                >
                                    <option value="UNASSIGNED">Unassigned</option>
                                    <option value="DCA">DCA</option>
                                    <option value="FOREVER">Forever</option>
                                    <option value="TRADING">Trading</option>
                                </select>
                            </div>
                            <button type="submit" className="btn btn-primary w-full">
                                Add Position
                            </button>
                        </form>
                    </div>

                    {/* Holdings Table */}
                    <div className="card overflow-hidden p-0">
                        <table className="w-full text-left border-collapse">
                            <thead className="bg-surface/50 text-text-secondary uppercase text-xs font-semibold tracking-wider">
                                <tr>
                                    <th className="p-4 border-b border-slate-700">Symbol</th>
                                    <th className="p-4 border-b border-slate-700">Qty</th>
                                    <th className="p-4 border-b border-slate-700">Avg Cost</th>
                                    <th className="p-4 border-b border-slate-700">Current</th>
                                    <th className="p-4 border-b border-slate-700">Market Value</th>
                                    <th className="p-4 border-b border-slate-700">PnL</th>
                                    <th className="p-4 border-b border-slate-700">Strategy</th>
                                    <th className="p-4 border-b border-slate-700">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700">
                                {portfolio.holdings.map((item, idx) => (
                                    <tr key={idx} className="hover:bg-slate-800/50 transition-colors">
                                        <td className="p-4 font-bold text-white">{item.symbol}</td>
                                        <td className="p-4 text-text-primary">{item.quantity}</td>
                                        <td className="p-4 text-text-secondary">{item.avg_cost.toLocaleString()}</td>
                                        <td className="p-4 text-text-primary">{item.current_price.toLocaleString()}</td>
                                        <td className="p-4 font-medium text-white">{item.market_value.toLocaleString()}</td>
                                        <td className={`p-4 font-medium flex items-center gap-1 ${item.pnl >= 0 ? 'text-secondary' : 'text-danger'}`}>
                                            {item.pnl >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                                            {Math.abs(item.pnl).toLocaleString()}
                                        </td>
                                        <td className="p-4">
                                            <span className={`px-2 py-1 rounded text-xs font-bold border ${item.strategy === 'FOREVER' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                                                item.strategy === 'TRADING' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                                                    'bg-slate-700 text-slate-300 border-slate-600'
                                                }`}>
                                                {item.strategy}
                                            </span>
                                        </td>
                                        <td className="p-4">
                                            <button
                                                onClick={() => openSellModal(item)}
                                                className="text-danger hover:bg-danger/10 p-2 rounded transition-colors"
                                                title="Sell Position"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </>
            ) : (
                /* History Table */
                <div className="card overflow-hidden p-0 animate-fade-in">
                    <table className="w-full text-left border-collapse">
                        <thead className="bg-surface/50 text-text-secondary uppercase text-xs font-semibold tracking-wider">
                            <tr>
                                <th className="p-4 border-b border-slate-700">Date/Time</th>
                                <th className="p-4 border-b border-slate-700">Symbol</th>
                                <th className="p-4 border-b border-slate-700">Action</th>
                                <th className="p-4 border-b border-slate-700">Quantity</th>
                                <th className="p-4 border-b border-slate-700">Price</th>
                                <th className="p-4 border-b border-slate-700">Total Value</th>
                                <th className="p-4 border-b border-slate-700">Notes</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700">
                            {transactions.map((tx, idx) => (
                                <tr key={idx} className="hover:bg-slate-800/50 transition-colors">
                                    <td className="p-4 text-text-secondary text-sm">
                                        {new Date(tx.timestamp).toLocaleString()}
                                    </td>
                                    <td className="p-4 font-bold text-white">{tx.symbol}</td>
                                    <td className="p-4">
                                        <span className={`px-2 py-1 rounded text-xs font-bold uppercase ${tx.action === 'BUY' ? 'bg-secondary/20 text-secondary' : 'bg-danger/20 text-danger'}`}>
                                            {tx.action}
                                        </span>
                                    </td>
                                    <td className="p-4 text-text-primary">{tx.quantity}</td>
                                    <td className="p-4 text-text-secondary">{tx.price.toLocaleString()}</td>
                                    <td className="p-4 font-medium text-white">{(tx.quantity * tx.price).toLocaleString()}</td>
                                    <td className="p-4 text-text-muted text-sm">{tx.notes}</td>
                                </tr>
                            ))}
                            {transactions.length === 0 && (
                                <tr>
                                    <td colSpan="7" className="p-8 text-center text-text-muted">
                                        No transaction history found.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Sell Modal */}
            {isSellModalOpen && selectedItem && (
                <SellModal
                    isOpen={isSellModalOpen}
                    onClose={() => setIsSellModalOpen(false)}
                    item={selectedItem}
                    onSuccess={fetchPortfolio}
                />
            )}
        </div>
    );
};

export default PortfolioView;
