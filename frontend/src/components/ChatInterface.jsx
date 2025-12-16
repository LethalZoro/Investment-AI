import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, Bot, User, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import clsx from 'clsx';
import { API_BASE_URL } from '../config';

const ChatInterface = () => {
    const [messages, setMessages] = useState([
        { role: 'bot', content: "Hello! I'm your AI Investment Co-Pilot. I can analyze your portfolio, suggest trades based on news, or answer market questions. How can I help?" }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [dataSource, setDataSource] = useState('ai'); // 'ai' or 'personal'
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMsg = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            // Prepare history (map 'bot' to 'assistant' for OpenAI)
            const history = messages.map(msg => ({
                role: msg.role === 'bot' ? 'assistant' : 'user',
                content: msg.content
            }));

            const response = await axios.post(`${API_BASE_URL}/chat`, {
                message: input,
                history: history
            });

            const botMsg = { role: 'bot', content: response.data.answer };
            setMessages(prev => [...prev, botMsg]);
        } catch (error) {
            console.error("Chat error:", error);
            setMessages(prev => [...prev, { role: 'bot', content: "Sorry, I encountered an error processing your request." }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-8rem)] card p-0 overflow-hidden">
            {/* Chat Header */}
            <div className="p-4 border-b border-slate-700 bg-surface/50 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-primary to-accent rounded-full flex items-center justify-center">
                        <Bot className="text-white w-6 h-6" />
                    </div>
                    <div>
                        <h2 className="font-bold text-white">AI Co-Pilot</h2>
                        <p className="text-xs text-text-secondary flex items-center gap-1">
                            <span className="w-2 h-2 bg-secondary rounded-full animate-pulse"></span> Online
                        </p>
                    </div>
                </div>

                {/* Data Source Toggle */}
                <div className="flex bg-slate-800 rounded-lg p-1 border border-slate-700 hidden">
                    {/* Toggle Removed - Always AI */}
                </div>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-900/50">
                {messages.map((msg, idx) => (
                    <div key={idx} className={clsx('flex gap-4', msg.role === 'user' ? 'justify-end' : 'justify-start')}>
                        {msg.role === 'bot' && (
                            <div className="w-8 h-8 bg-surface rounded-full flex items-center justify-center border border-slate-700 flex-shrink-0">
                                <Bot className="w-5 h-5 text-primary" />
                            </div>
                        )}
                        <div className={clsx(
                            'max-w-[80%] p-4 rounded-2xl shadow-md',
                            msg.role === 'user'
                                ? 'bg-primary text-white rounded-br-none'
                                : 'bg-surface border border-slate-700 text-text-primary rounded-bl-none'
                        )}>
                            <div className="prose prose-invert prose-sm max-w-none">
                                <ReactMarkdown>{msg.content}</ReactMarkdown>
                            </div>
                        </div>
                        {msg.role === 'user' && (
                            <div className="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center border border-slate-600 flex-shrink-0">
                                <User className="w-5 h-5 text-slate-300" />
                            </div>
                        )}
                    </div>
                ))}
                {loading && (
                    <div className="flex gap-4 justify-start">
                        <div className="w-8 h-8 bg-surface rounded-full flex items-center justify-center border border-slate-700">
                            <Sparkles className="w-4 h-4 text-accent animate-spin" />
                        </div>
                        <div className="bg-surface border border-slate-700 text-text-secondary p-4 rounded-2xl rounded-bl-none animate-pulse">
                            Thinking...
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <form onSubmit={handleSend} className="p-4 bg-surface border-t border-slate-700 flex gap-3">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask about stocks, strategies, or your portfolio..."
                    className="flex-1 input bg-slate-900 border-slate-700 focus:ring-primary"
                />
                <button
                    type="submit"
                    disabled={loading}
                    className="btn btn-primary px-6 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <Send className="w-5 h-5" />
                </button>
            </form>

            {/* Suggestion Chips */}
            <div className="px-4 pb-4 flex gap-2 overflow-x-auto">
                {['What is my P&L history?', 'Why did you buy TRG?', 'Summarize my portfolio', 'Any new alerts?'].map((suggestion, idx) => (
                    <button
                        key={idx}
                        onClick={() => {
                            setInput(suggestion);
                            // Optional: auto-send
                            // handleSend({ preventDefault: () => {} }); 
                        }}
                        className="whitespace-nowrap px-3 py-1 bg-slate-800 hover:bg-slate-700 text-xs text-text-secondary rounded-full border border-slate-700 transition-colors"
                    >
                        {suggestion}
                    </button>
                ))}
            </div>
        </div>
    );
};

export default ChatInterface;
