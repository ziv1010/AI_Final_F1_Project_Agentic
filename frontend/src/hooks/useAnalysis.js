import { useState, useEffect, useRef, useCallback } from 'react';
import { io } from 'socket.io-client';

const BACKEND_URL = 'http://localhost:5010';

export const useAnalysis = () => {
    const [socket, setSocket] = useState(null);
    const [status, setStatus] = useState('disconnected'); // disconnected, connecting, connected
    const [currentSession, setCurrentSession] = useState(null);
    const [sessionStatus, setSessionStatus] = useState(null);
    const [progress, setProgress] = useState([]);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);

    // Keep track of polling interval to clear it
    const pollIntervalRef = useRef(null);

    // Initial Socket Connection
    useEffect(() => {
        const newSocket = io(BACKEND_URL, {
            transports: ['websocket', 'polling'],
            reconnectionAttempts: 5,
        });

        setStatus('connecting');

        newSocket.on('connect', () => {
            console.log('Connected to server');
            setStatus('connected');
        });

        newSocket.on('connect_error', (err) => {
            console.error('Connection error:', err);
            setStatus('disconnected');
        });

        newSocket.on('disconnect', () => {
            console.log('Disconnected from server');
            setStatus('disconnected');
        });

        newSocket.on('progress', (data) => {
            if (data.session_id === currentSession) {
                // Add new progress item
                setProgress(prev => {
                    // Check if we already have this specific timestamp/message combo to avoid dupes if any
                    const exists = prev.some(p => p.timestamp === data.timestamp && p.message === data.message);
                    if (exists) return prev;
                    return [...prev, {
                        timestamp: data.timestamp,
                        status: data.status,
                        message: data.message,
                        node: data.node,
                    }];
                });

                if (data.status === 'completed') {
                    fetchSessionStatus(data.session_id);
                }
            }
        });

        setSocket(newSocket);

        return () => {
            newSocket.close();
            if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
        };
    }, [currentSession]); // Re-subscribe if session changes? No, just the check inside 'progress' needs currentSession access or ref

    // Fix for accessing currentSession inside socket callback without re-running effect
    // We actually want the socket effect to run ONCE, so we should use a ref for currentSession
    const currentSessionRef = useRef(currentSession);
    useEffect(() => {
        currentSessionRef.current = currentSession;
    }, [currentSession]);

    // Re-bind progress event if we really need to, but better to use Ref inside the closure if logic allows.
    // However, simplest way with the existing structure:
    useEffect(() => {
        if (!socket) return;

        const handleProgress = (data) => {
            if (data.session_id === currentSessionRef.current) {
                setProgress(prev => [...prev, {
                    timestamp: data.timestamp,
                    status: data.status,
                    message: data.message,
                    node: data.node,
                }]);

                if (data.status === 'completed') {
                    fetchSessionStatus(data.session_id);
                }
            }
        };

        socket.off('progress'); // Remove old listener
        socket.on('progress', handleProgress);

    }, [socket, currentSession]); // This is safe enough

    const fetchSessionStatus = useCallback(async (sessionId) => {
        try {
            const response = await fetch(`/api/session/${sessionId}`);
            const data = await response.json();
            setSessionStatus(data);

            if (data.status === 'completed' && data.result) {
                setResult(data.result);
                setIsAnalyzing(false);
                if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
            }
        } catch (err) {
            console.error('Error fetching session status:', err);
        }
    }, []);

    const submitQuery = async (query, depth) => {
        setIsAnalyzing(true);
        setProgress([]);
        setResult(null);
        setSessionStatus(null);
        setError(null);

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, depth }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }

            if (data.session_id) {
                setCurrentSession(data.session_id);

                if (socket) {
                    socket.emit('subscribe', { session_id: data.session_id });
                }

                // Poll every 2 seconds
                if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
                pollIntervalRef.current = setInterval(() => {
                    fetchSessionStatus(data.session_id);
                }, 2000);

                // Timeout after 5 mins
                setTimeout(() => {
                    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
                }, 300000);
            }
        } catch (err) {
            console.error('Error submitting query:', err);
            setError(err.message);
            setIsAnalyzing(false);
        }
    };

    return {
        status,
        sessionStatus,
        progress,
        result,
        error,
        isAnalyzing,
        submitQuery,
    };
};
