/**
 * Resilient WebSocket client for live telemetry streaming with auto-reconnection and heartbeat.
 */
import { useEffect, useRef, useState, useCallback } from 'react';

export function useMetricsWebSocket() {
  const [data, setData] = useState(null);
  const [status, setStatus] = useState('disconnected'); // 'connecting' | 'connected' | 'disconnected' | 'error'
  const [error, setError] = useState(null);
  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const pingIntervalRef = useRef(null);
  const isUnmountedRef = useRef(false);

  const getWsUrl = useCallback(() => {
    if (import.meta.env.VITE_WS_URL) {
      return import.meta.env.VITE_WS_URL;
    }
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // If running in Vite dev mode (port 5173), proxy or direct connect to backend port 8000
    const host = window.location.port === '5173' ? `${window.location.hostname}:8000` : window.location.host;
    return `${protocol}//${host}/ws/metrics`;
  }, []);

  const connect = useCallback(() => {
    if (socketRef.current && (socketRef.current.readyState === WebSocket.CONNECTING || socketRef.current.readyState === WebSocket.OPEN)) {
      return; // Already connecting or open
    }

    const wsUrl = getWsUrl();
    setStatus('connecting');
    setError(null);

    try {
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        if (isUnmountedRef.current) {
          ws.close();
          return;
        }
        setStatus('connected');
        setError(null);

        // Setup ping interval to keep connection alive
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 15000);
      };

      ws.onmessage = (event) => {
        if (event.data === 'pong') return;
        try {
          const snapshot = JSON.parse(event.data);
          setData(snapshot);
        } catch (err) {
          console.debug('Received non-JSON websocket message:', event.data);
        }
      };

      ws.onerror = (evt) => {
        if (!isUnmountedRef.current) {
          setError('WebSocket communication error');
          setStatus('error');
        }
      };

      ws.onclose = () => {
        clearInterval(pingIntervalRef.current);
        if (!isUnmountedRef.current) {
          setStatus('disconnected');
          // Auto reconnect after 2.5 seconds
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, 2500);
        }
      };
    } catch (err) {
      setError(err.message || 'Failed to establish WebSocket connection');
      setStatus('error');
    }
  }, [getWsUrl]);

  useEffect(() => {
    isUnmountedRef.current = false;
    connect();

    return () => {
      isUnmountedRef.current = true;
      clearInterval(pingIntervalRef.current);
      clearTimeout(reconnectTimeoutRef.current);
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [connect]);

  return {
    latestSnapshot: data,
    connectionStatus: status,
    connectionError: error,
    reconnect: connect,
  };
}
