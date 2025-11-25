import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, LineChart, Settings, Bell, TrendingUp, PieChart, MessageSquare } from 'lucide-react';
import clsx from 'clsx';

const Sidebar = () => {
    const location = useLocation();

    const navItems = [
        { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
        { path: '/portfolio', icon: PieChart, label: 'Portfolio' },
        { path: '/market', icon: LineChart, label: 'Market' },
        { path: '/news', icon: Bell, label: 'News' },
        { path: '/ai-stocks', icon: TrendingUp, label: 'AI Stocks' },
        { path: '/chat', icon: MessageSquare, label: 'AI Chat' },
        { path: '/settings', icon: Settings, label: 'Settings' },
    ];

    return (
        <div className="w-64 bg-surface border-r border-slate-700 flex flex-col h-full">
            <div className="p-6 border-b border-slate-700">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-gradient-to-br from-primary to-accent rounded-lg flex items-center justify-center">
                        <TrendingUp className="text-white w-5 h-5" />
                    </div>
                    <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
                        PSX Co-Pilot
                    </h1>
                </div>
            </div>

            <nav className="flex-1 p-4 space-y-2">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = location.pathname === item.path;
                    return (
                        <Link
                            key={item.path}
                            to={item.path}
                            className={clsx(
                                'flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 group',
                                isActive
                                    ? 'bg-primary/10 text-primary border border-primary/20'
                                    : 'text-text-secondary hover:bg-slate-800 hover:text-white'
                            )}
                        >
                            <Icon className={clsx('w-5 h-5', isActive ? 'text-primary' : 'text-slate-500 group-hover:text-white')} />
                            <span className="font-medium">{item.label}</span>
                        </Link>
                    );
                })}
            </nav>


        </div>
    );
};

export default Sidebar;
