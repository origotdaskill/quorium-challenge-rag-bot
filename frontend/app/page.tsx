'use client';

import { useState, useRef, useEffect } from 'react';
import {
    Send,
    Bot,
    User,
    FileText,
    Loader2,
    Sparkles,
    MessageCircle,
    AlertCircle
} from 'lucide-react';
import styles from './page.module.css';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    sources?: string[];
    timestamp: Date;
}

interface ApiResponse {
    answer: string;
    sources: string[];
}

export default function Home() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9754';

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        inputRef.current?.focus();
    }, []);

    const generateId = () => {
        return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!input.trim() || isLoading) return;

        const userMessage: Message = {
            id: generateId(),
            role: 'user',
            content: input.trim(),
            timestamp: new Date(),
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(`${API_URL}/ask`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: userMessage.content }),
            });

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            const data: ApiResponse = await response.json();

            const assistantMessage: Message = {
                id: generateId(),
                role: 'assistant',
                content: data.answer,
                sources: data.sources,
                timestamp: new Date(),
            };

            setMessages(prev => [...prev, assistantMessage]);
        } catch (err) {
            console.error('Error:', err);
            setError('Failed to get response. Please check if the backend is running.');

            const errorMessage: Message = {
                id: generateId(),
                role: 'assistant',
                content: 'Sorry, I encountered an error while processing your question. Please make sure the backend service is running and try again.',
                timestamp: new Date(),
            };

            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    return (
        <main className={styles.main}>
            {/* Background Effects */}
            <div className={styles.bgGradient} />
            <div className={styles.bgGrid} />

            <div className={styles.container}>
                {/* Header */}
                <header className={styles.header}>
                    <div className={styles.logo}>
                        <div className={styles.logoIcon}>
                            <Sparkles size={28} />
                        </div>
                        <div className={styles.logoText}>
                            <h1>RAG Q&A</h1>
                            <span>AI-Powered Document Assistant</span>
                        </div>
                    </div>
                </header>

                {/* Chat Area */}
                <div className={styles.chatArea}>
                    {messages.length === 0 ? (
                        <div className={styles.emptyState}>
                            <div className={styles.emptyIcon}>
                                <MessageCircle size={64} />
                            </div>
                            <h2>Ask anything about your documents</h2>
                            <p>I can help you find information, answer questions, and provide insights from your ingested documents.</p>
                            <div className={styles.suggestions}>
                                <button
                                    className={styles.suggestion}
                                    onClick={() => setInput('What are the main topics covered in the documents?')}
                                >
                                    <FileText size={16} />
                                    What are the main topics?
                                </button>
                                <button
                                    className={styles.suggestion}
                                    onClick={() => setInput('Can you summarize the key points?')}
                                >
                                    <FileText size={16} />
                                    Summarize key points
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className={styles.messages}>
                            {messages.map((message) => (
                                <div
                                    key={message.id}
                                    className={`${styles.message} ${styles[message.role]}`}
                                >
                                    <div className={styles.messageAvatar}>
                                        {message.role === 'user' ? (
                                            <User size={20} />
                                        ) : (
                                            <Bot size={20} />
                                        )}
                                    </div>
                                    <div className={styles.messageContent}>
                                        <div className={styles.messageText}>
                                            {message.content}
                                        </div>
                                        {message.sources && message.sources.length > 0 && (
                                            <div className={styles.sources}>
                                                <span className={styles.sourcesLabel}>
                                                    <FileText size={14} />
                                                    Sources:
                                                </span>
                                                <div className={styles.sourcesList}>
                                                    {message.sources.map((source, idx) => (
                                                        <span key={idx} className={styles.sourceTag}>
                                                            {source}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}

                            {isLoading && (
                                <div className={`${styles.message} ${styles.assistant}`}>
                                    <div className={styles.messageAvatar}>
                                        <Bot size={20} />
                                    </div>
                                    <div className={styles.messageContent}>
                                        <div className={styles.loadingDots}>
                                            <span></span>
                                            <span></span>
                                            <span></span>
                                        </div>
                                    </div>
                                </div>
                            )}

                            <div ref={messagesEndRef} />
                        </div>
                    )}
                </div>

                {/* Error Banner */}
                {error && (
                    <div className={styles.errorBanner}>
                        <AlertCircle size={18} />
                        {error}
                    </div>
                )}

                {/* Input Area */}
                <form onSubmit={handleSubmit} className={styles.inputArea}>
                    <div className={styles.inputWrapper}>
                        <input
                            ref={inputRef}
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Ask a question about your documents..."
                            className={styles.input}
                            disabled={isLoading}
                        />
                        <button
                            type="submit"
                            className={styles.sendButton}
                            disabled={!input.trim() || isLoading}
                        >
                            {isLoading ? (
                                <Loader2 size={20} className={styles.spinning} />
                            ) : (
                                <Send size={20} />
                            )}
                        </button>
                    </div>
                    <p className={styles.inputHint}>
                        Press Enter to send • Powered by RAG technology
                    </p>
                </form>
            </div>
        </main>
    );
}
