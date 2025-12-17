import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Save, Shield, Cpu, DollarSign } from 'lucide-react';
import { API_BASE_URL } from '../config';

const SettingsView = () => {
    const [settings, setSettings] = useState({
        daily_trade_budget: 5000,
        ai_cash_balance: 10000,
        autonomous_mode: false,
        rollover_percent: 0.5,
        polling_interval: 5,
        trading_start_time: "09:30",
        trading_end_time: "15:30"
    });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const response = await axios.get(`${API_BASE_URL}/settings`);
                if (response.data) {
                    setSettings(response.data);
                }
            } catch (error) {
                console.error("Error fetching settings:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchSettings();
    }, []);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setSettings(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked :
                (name === 'trading_start_time' || name === 'trading_end_time') ? value :
                    parseFloat(value)
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        try {
            await axios.post(`${API_BASE_URL}/settings`, settings);
            alert("Settings saved successfully!");
        } catch (error) {
            console.error("Error saving settings:", error);
            alert("Failed to save settings.");
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div className="text-center p-10 text-primary animate-pulse">Loading Settings...</div>;

    return (
        <div className="max-w-2xl mx-auto animate-fade-in">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-white">Settings</h1>
                <p className="text-text-secondary mt-1">Configure your Autonomous Agent and Risk Controls.</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
                {/* Autonomous Mode Toggle */}
                <div className="card flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className={`p-3 rounded-full ${settings.autonomous_mode ? 'bg-secondary/20 text-secondary' : 'bg-slate-800 text-text-secondary'}`}>
                            <Cpu className="w-6 h-6" />
                        </div>
                        <div>
                            <h3 className="text-lg font-bold text-white">Autonomous Mode</h3>
                            <p className="text-sm text-text-secondary">Allow the agent to generate daily trading plans.</p>
                        </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                        <input
                            type="checkbox"
                            name="autonomous_mode"
                            checked={settings.autonomous_mode}
                            onChange={handleChange}
                            className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-secondary/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-secondary"></div>
                    </label>
                </div>

                {/* Budget Settings */}
                <div className="card space-y-6">
                    <div className="flex items-center gap-2 mb-4 border-b border-slate-700 pb-4">
                        <DollarSign className="text-accent w-5 h-5" />
                        <h3 className="text-lg font-bold text-white">Budget Configuration</h3>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-2">Daily Trade Budget (PKR)</label>
                            <input
                                type="number"
                                name="daily_trade_budget"
                                value={settings.daily_trade_budget}
                                onChange={handleChange}
                                className="input w-full"
                                min="0"
                            />
                            <p className="text-xs text-text-muted mt-1">Max amount to allocate per day.</p>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-2">AI Cash Balance (Initial Capital)</label>
                            <input
                                type="number"
                                name="ai_cash_balance"
                                value={settings.ai_cash_balance}
                                onChange={handleChange}
                                className="input w-full"
                                min="0"
                            />
                            <p className="text-xs text-text-muted mt-1">Total funds available for AI trading.</p>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-2">Rollover Percentage (0-1.0)</label>
                            <input
                                type="number"
                                name="rollover_percent"
                                value={settings.rollover_percent}
                                onChange={handleChange}
                                className="input w-full"
                                min="0"
                                max="1"
                                step="0.05"
                            />
                            <p className="text-xs text-text-muted mt-1">Unused budget carried to next day.</p>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-2">AI Polling Rate (Minutes)</label>
                            <select
                                name="polling_interval"
                                value={settings.polling_interval || 5}
                                onChange={handleChange}
                                className="input w-full"
                            >
                                <option value="1">Every 1 Minute (High CPU)</option>
                                <option value="5">Every 5 Minutes (Recommended)</option>
                                <option value="15">Every 15 Minutes</option>
                                <option value="60">Every Hour</option>
                            </select>
                            <p className="text-xs text-text-muted mt-1">How often AI scans for news & alerts.</p>
                        </div>
                    </div>
                </div>

                {/* Trading Hours Settings */}
                <div className="card space-y-6">
                    <div className="flex items-center gap-2 mb-4 border-b border-slate-700 pb-4">
                        <Cpu className="text-secondary w-5 h-5" />
                        <h3 className="text-lg font-bold text-white">Trading Hours (PKT)</h3>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-2">Start Time (24h)</label>
                            <input
                                type="time"
                                name="trading_start_time"
                                value={settings.trading_start_time || "09:30"}
                                onChange={handleChange}
                                className="input w-full"
                            />
                            <p className="text-xs text-text-muted mt-1">AI will start trading after this time.</p>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-2">End Time (24h)</label>
                            <input
                                type="time"
                                name="trading_end_time"
                                value={settings.trading_end_time || "15:30"}
                                onChange={handleChange}
                                className="input w-full"
                            />
                            <p className="text-xs text-text-muted mt-1">AI will stop trading after this time.</p>
                        </div>
                    </div>
                </div>

                {/* Risk Profile (Read Only for now) */}
                <div className="card opacity-75">
                    <div className="flex items-center gap-2 mb-4 border-b border-slate-700 pb-4">
                        <Shield className="text-danger w-5 h-5" />
                        <h3 className="text-lg font-bold text-white">Risk Controls (Hard Coded)</h3>
                    </div>
                    <ul className="space-y-2 text-sm text-text-secondary">
                        <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 bg-danger rounded-full"></span> Max 15% Allocation per Stock</li>
                        <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 bg-danger rounded-full"></span> Max 40% Allocation per Sector</li>
                        <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 bg-danger rounded-full"></span> No Leverage / Margin Trading</li>
                    </ul>
                </div>

                <button
                    type="submit"
                    disabled={saving}
                    className="btn btn-primary w-full flex items-center justify-center gap-2"
                >
                    <Save className="w-5 h-5" />
                    {saving ? 'Saving...' : 'Save Configuration'}
                </button>
            </form>
        </div>
    );
};

export default SettingsView;
