import React from 'react';
import Sidebar from './Sidebar';

const Layout = ({ children }) => {
    return (
        <div className="flex h-screen bg-background text-text-primary overflow-hidden font-sans">
            <Sidebar />
            <main className="flex-1 overflow-auto relative">
                {/* Header / Top bar could go here */}
                <div className="p-8 max-w-7xl mx-auto">
                    {children}
                </div>
            </main>
        </div>
    );
};

export default Layout;
