import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp, Wallet, DollarSign, Activity, PlusCircle, MinusCircle, X } from 'lucide-react';
import { API_BASE_URL } from '../config';

const StatCard = ({ title, value, subtext, icon: Icon, trend, onAction }) => (
    <div className="card relative overflow-hidden group">
        <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <Icon className="w-16 h-16 text-primary" />
        </div>
        <div className="relative z-10">
            <div className="flex justify-between items-start">
                <h3 className="text-text-secondary text-sm font-medium uppercase tracking-wider">{title}</h3>
                {onAction && (
                    <button onClick={onAction} className="text-primary hover:text-white transition-colors">
                        <PlusCircle className="w-5 h-5" />
                    </button>
                )}
            </div>
            <p className="text-3xl font-bold mt-2 text-white">{value}</p>
            <p className={`text-sm mt-1 ${trend === 'up' ? 'text-secondary' : 'text-danger'}`}>
                {subtext}
            </p>
        </div>
    </div>
);

const CashModal = ({ isOpen, onClose, onUpdate }) => {
    const [amount, setAmount] = useState('');
    const [type, setType] = useState('DEPOSIT');

    if (!isOpen) return null;

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await axios.post(`${API_BASE_URL}/portfolio/cash`, { amount: parseFloat(amount), type });
            onUpdate();
            onClose();
        } catch (error) {
            alert("Error updating cash");
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="card w-96 relative animate-fade-in">
                <button onClick={onClose} className="absolute top-4 right-4 text-text-secondary hover:text-white">
                    <X className="w-5 h-5" />
                </button>
                <h2 className="text-xl font-bold text-white mb-4">Manage Cash</h2>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm text-text-secondary mb-1">Action</label>
                        <div className="flex gap-2">
                            <button
                                type="button"
                                onClick={() => setType('DEPOSIT')}
                                className={`flex-1 py-2 rounded-lg font-medium transition-colors ${type === 'DEPOSIT' ? 'bg-secondary text-white' : 'bg-slate-800 text-text-secondary'}`}
                            >
                                Deposit
                            </button>
                            <button
                                type="button"
                                onClick={() => setType('WITHDRAW')}
                                className={`flex-1 py-2 rounded-lg font-medium transition-colors ${type === 'WITHDRAW' ? 'bg-danger text-white' : 'bg-slate-800 text-text-secondary'}`}
                            >
                                Withdraw
                            </button>
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm text-text-secondary mb-1">Amount (PKR)</label>
                        <input
                            type="number"
                            value={amount}
                            onChange={(e) => setAmount(e.target.value)}
                            className="input w-full"
                            placeholder="5000"
                            required
                        />
                    </div>
                    <button type="submit" className="btn btn-primary w-full">
                        Confirm {type === 'DEPOSIT' ? 'Deposit' : 'Withdrawal'}
                    </button>
                </form>
            </div>
        </div>
    );
};

const Dashboard = () => {
    const [portfolio, setPortfolio] = useState(null);
    const [plan, setPlan] = useState(null);
    const [history, setHistory] = useState([]);
    const [isCashModalOpen, setIsCashModalOpen] = useState(false);

    const fetchData = async () => {
        try {
            const portRes = await axios.get(`${API_BASE_URL}/portfolio`);
            setPortfolio(portRes.data);
            const planRes = await axios.get(`${API_BASE_URL}/autonomous/plan`);
            setPlan(planRes.data);
            const histRes = await axios.get(`${API_BASE_URL}/portfolio/history`);
            setHistory(histRes.data);
        } catch (error) {
            console.error("Error fetching data", error);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    if (!portfolio) return <div className="flex items-center justify-center h-full text-primary animate-pulse">Loading Dashboard...</div>;

    const pieData = portfolio.holdings.map(h => ({ name: h.symbol, value: h.market_value }));
    const COLORS = ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ef4444'];

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="text-3xl font-bold text-white">Dashboard</h2>
                    <p className="text-text-secondary mt-1">Welcome back, Investor.</p>
                </div>
                <div className="flex gap-2">
                    <span className="px-3 py-1 bg-secondary/20 text-secondary rounded-full text-sm font-medium border border-secondary/20 flex items-center gap-2">
                        <div className="w-2 h-2 bg-secondary rounded-full animate-pulse"></div>
                        Market Open
                    </span>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <StatCard
                    title="Total Net Worth"
                    value={`PKR ${portfolio.total_value.toLocaleString()}`}
                    subtext="+2.4% from yesterday"
                    icon={Wallet}
                    trend="up"
                />
                <StatCard
                    title="Cash Balance"
                    value={`PKR ${portfolio.cash_balance.toLocaleString()}`}
                    subtext="Available for trade"
                    icon={DollarSign}
                    trend="up"
                    onAction={() => setIsCashModalOpen(true)}
                />
                <StatCard
                    title="Holdings Value"
                    value={`PKR ${portfolio.holdings_value.toLocaleString()}`}
                    subtext={`${portfolio.holdings.length} Active Positions`}
                    icon={Activity}
                    trend="up"
                />
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="card lg:col-span-2 min-h-[400px]">
                    <h3 className="text-lg font-bold text-white mb-6">Portfolio Performance</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={history}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis dataKey="date" stroke="#94a3b8" tick={{ fontSize: 12 }} />
                            <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                                itemStyle={{ color: '#f8fafc' }}
                            />
                            <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={3} dot={false} activeDot={{ r: 8 }} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>

                <div className="card min-h-[400px]">
                    <h3 className="text-lg font-bold text-white mb-6">Allocation</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie
                                data={pieData}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={80}
                                paddingAngle={5}
                                dataKey="value"
                            >
                                {pieData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                            />
                        </PieChart>
                    </ResponsiveContainer>
                    <div className="mt-4 space-y-2">
                        {pieData.map((entry, index) => (
                            <div key={index} className="flex items-center justify-between text-sm">
                                <div className="flex items-center gap-2">
                                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }}></div>
                                    <span className="text-text-secondary">{entry.name}</span>
                                </div>
                                <span className="font-medium text-white">{((entry.value / portfolio.holdings_value) * 100).toFixed(1)}%</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Daily Plan */}
            {plan && plan.plan && (
                <div className="card border-l-4 border-l-warning">
                    <div className="flex items-center gap-3 mb-4">
                        <TrendingUp className="text-warning w-6 h-6" />
                        <h2 className="text-xl font-bold text-white">Daily Autonomous Plan</h2>
                    </div>

                    <div className="space-y-3">
                        {plan.plan.length === 0 ? (
                            <p className="text-text-muted italic">No trades scheduled for today.</p>
                        ) : (
                            plan.plan.map((trade, idx) => (
                                <div key={idx} className="flex items-center justify-between bg-slate-900/50 p-4 rounded-lg border border-slate-700/50 hover:border-slate-600 transition-colors">
                                    <div className="flex items-center gap-4">
                                        <span className={`px-3 py-1 rounded text-xs font-bold uppercase ${trade.action === 'BUY' ? 'bg-secondary/20 text-secondary' : 'bg-danger/20 text-danger'}`}>
                                            {trade.action}
                                        </span>
                                        <div>
                                            <span className="font-bold text-white text-lg">{trade.symbol}</span>
                                            <span className="text-text-muted text-sm ml-2">x {trade.quantity} shares</span>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-white font-medium">Target: {trade.price_range}</div>
                                        <div className="text-xs text-text-muted">{trade.reason}</div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                    <div className="mt-4 pt-4 border-t border-slate-700 flex justify-between text-sm text-text-secondary">
                        <span>Budget Used: <span className="text-white">PKR {(plan.todays_budget - plan.remaining_cash).toLocaleString()}</span></span>
                        <span>Remaining: <span className="text-secondary font-bold">PKR {plan.remaining_cash?.toLocaleString()}</span></span>
                    </div>
                </div>
            )}

            <CashModal
                isOpen={isCashModalOpen}
                onClose={() => setIsCashModalOpen(false)}
                onUpdate={fetchData}
            />
        </div>
    );
};

export default Dashboard;
