/**
 * React Integration Example for Claude SDK Server Streaming
 * 
 * This file demonstrates how to integrate Claude SDK Server's streaming
 * capabilities into a React application using hooks and components.
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { EventSourcePolyfill } from 'event-source-polyfill';

// ============================================================================
// Type Definitions
// ============================================================================

interface StreamEvent {
  id: string;
  type: string;
  timestamp: string;
  session_id?: string;
  severity: 'info' | 'success' | 'warning' | 'error' | 'critical';
  message: string;
  data?: Record<string, any>;
}

interface QueryResponse {
  response: string;
  session_id: string;
}

interface StreamStatus {
  active_connections: number;
  events_queued: number;
  total_events_sent: number;
  uptime_seconds: number;
}

// ============================================================================
// Custom Hooks
// ============================================================================

/**
 * Hook for Server-Sent Events streaming
 */
export function useSSEStream(
  url: string,
  options?: {
    eventTypes?: string[];
    sessionId?: string;
    includePerformance?: boolean;
    includeSystem?: boolean;
  }
) {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    // Build query parameters
    const params = new URLSearchParams();
    if (options?.eventTypes) {
      params.append('event_types', options.eventTypes.join(','));
    }
    if (options?.sessionId) {
      params.append('session_id', options.sessionId);
    }
    if (options?.includePerformance !== undefined) {
      params.append('include_performance', String(options.includePerformance));
    }
    if (options?.includeSystem !== undefined) {
      params.append('include_system', String(options.includeSystem));
    }

    const fullUrl = `${url}?${params.toString()}`;

    // Create EventSource connection
    const eventSource = new EventSource(fullUrl);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
      setError(null);
      console.log('SSE connection established');
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as StreamEvent;
        setEvents((prev) => [...prev, data]);
      } catch (err) {
        console.error('Failed to parse event:', err);
      }
    };

    eventSource.onerror = (err) => {
      setIsConnected(false);
      setError('Connection lost. Reconnecting...');
      console.error('SSE error:', err);
    };

    // Cleanup
    return () => {
      eventSource.close();
      eventSourceRef.current = null;
    };
  }, [url, options?.eventTypes, options?.sessionId, options?.includePerformance, options?.includeSystem]);

  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);

  return {
    events,
    isConnected,
    error,
    clearEvents,
  };
}

/**
 * Hook for WebSocket streaming
 */
export function useWebSocketStream(url: string) {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const subscribe = useCallback((eventTypes?: string[]) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          action: 'subscribe',
          event_types: eventTypes,
        })
      );
    }
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  useEffect(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      setError(null);
      console.log('WebSocket connection established');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as StreamEvent;
        setEvents((prev) => [...prev, data]);
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onerror = (err) => {
      setError('WebSocket error occurred');
      console.error('WebSocket error:', err);
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket connection closed');
    };

    // Cleanup
    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [url]);

  return {
    events,
    isConnected,
    error,
    subscribe,
    sendMessage,
  };
}

/**
 * Hook for making Claude queries
 */
export function useClaudeQuery(baseUrl: string) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<QueryResponse | null>(null);

  const query = useCallback(
    async (
      prompt: string,
      options?: {
        sessionId?: string;
        maxTurns?: number;
        model?: string;
        maxThinkingTokens?: number;
      }
    ) => {
      setIsLoading(true);
      setError(null);

      try {
        const res = await fetch(`${baseUrl}/api/v1/query`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            prompt,
            session_id: options?.sessionId,
            max_turns: options?.maxTurns || 30,
            model: options?.model || 'claude-3-5-sonnet-20241022',
            max_thinking_tokens: options?.maxThinkingTokens || 8000,
          }),
        });

        if (!res.ok) {
          throw new Error(`Query failed: ${res.statusText}`);
        }

        const data = await res.json() as QueryResponse;
        setResponse(data);
        return data;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Query failed';
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [baseUrl]
  );

  return {
    query,
    isLoading,
    error,
    response,
  };
}

// ============================================================================
// Components
// ============================================================================

/**
 * Event display component
 */
export function EventDisplay({ event }: { event: StreamEvent }) {
  const getEmoji = (type: string) => {
    const emojiMap: Record<string, string> = {
      query_start: '🚀',
      query_complete: '✅',
      thinking_start: '🤔',
      thinking_insight: '💡',
      tool_use: '🛠️',
      tool_result: '📦',
      todo_identified: '📝',
      performance_metric: '⚡',
      token_usage: '📊',
      system_message: 'ℹ️',
      query_error: '❌',
    };
    return emojiMap[type] || '📌';
  };

  const getSeverityColor = (severity: string) => {
    const colorMap: Record<string, string> = {
      info: 'text-blue-600',
      success: 'text-green-600',
      warning: 'text-yellow-600',
      error: 'text-red-600',
      critical: 'text-red-800',
    };
    return colorMap[severity] || 'text-gray-600';
  };

  return (
    <div className="p-3 border rounded-lg mb-2 bg-white shadow-sm">
      <div className="flex items-start space-x-2">
        <span className="text-2xl">{getEmoji(event.type)}</span>
        <div className="flex-1">
          <div className="flex items-center space-x-2">
            <span className="font-semibold">{event.type}</span>
            <span className={`text-sm ${getSeverityColor(event.severity)}`}>
              {event.severity}
            </span>
            <span className="text-xs text-gray-500">
              {new Date(event.timestamp).toLocaleTimeString()}
            </span>
          </div>
          <p className="text-gray-700 mt-1">{event.message}</p>
          {event.data && (
            <details className="mt-2">
              <summary className="cursor-pointer text-sm text-gray-500">
                Additional Data
              </summary>
              <pre className="mt-1 p-2 bg-gray-100 rounded text-xs overflow-x-auto">
                {JSON.stringify(event.data, null, 2)}
              </pre>
            </details>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Stream status component
 */
export function StreamStatus({ baseUrl }: { baseUrl: string }) {
  const [status, setStatus] = useState<StreamStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${baseUrl}/api/v1/stream/status`);
      if (!res.ok) throw new Error('Failed to fetch status');
      const data = await res.json() as StreamStatus;
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch status');
    }
  }, [baseUrl]);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, [fetchStatus]);

  if (error) {
    return <div className="text-red-600">Error: {error}</div>;
  }

  if (!status) {
    return <div className="text-gray-500">Loading status...</div>;
  }

  return (
    <div className="bg-gray-100 rounded-lg p-4">
      <h3 className="font-semibold mb-2">Stream Status</h3>
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div>Active Connections:</div>
        <div className="font-medium">{status.active_connections}</div>
        <div>Events Queued:</div>
        <div className="font-medium">{status.events_queued}</div>
        <div>Total Events Sent:</div>
        <div className="font-medium">{status.total_events_sent}</div>
        <div>Uptime:</div>
        <div className="font-medium">
          {Math.floor(status.uptime_seconds / 60)} minutes
        </div>
      </div>
    </div>
  );
}

/**
 * Main Claude streaming interface component
 */
export function ClaudeStreamingInterface({ baseUrl }: { baseUrl: string }) {
  const [prompt, setPrompt] = useState('');
  const [streamType, setStreamType] = useState<'sse' | 'websocket'>('sse');
  const [filterTypes, setFilterTypes] = useState<string[]>([]);

  const { query, isLoading, response } = useClaudeQuery(baseUrl);

  const sseStream = useSSEStream(`${baseUrl}/api/v1/stream/sse`, {
    eventTypes: filterTypes.length > 0 ? filterTypes : undefined,
    sessionId: response?.session_id,
    includePerformance: true,
  });

  const wsStream = useWebSocketStream(
    baseUrl.replace('http://', 'ws://').replace('https://', 'wss://') +
      '/api/v1/stream/ws'
  );

  const activeStream = streamType === 'sse' ? sseStream : wsStream;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    try {
      await query(prompt, {
        sessionId: response?.session_id,
        maxThinkingTokens: 5000,
      });
      setPrompt('');
    } catch (err) {
      console.error('Query failed:', err);
    }
  };

  const eventTypes = [
    'query_start',
    'thinking_insight',
    'tool_use',
    'tool_result',
    'todo_identified',
    'performance_metric',
    'query_complete',
  ];

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Claude SDK Streaming Interface</h1>

      {/* Query Form */}
      <form onSubmit={handleSubmit} className="mb-6">
        <div className="flex space-x-2">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Ask Claude something..."
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {isLoading ? 'Processing...' : 'Send'}
          </button>
        </div>
      </form>

      {/* Response Display */}
      {response && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <h3 className="font-semibold mb-2">Response:</h3>
          <p className="whitespace-pre-wrap">{response.response}</p>
          <p className="text-sm text-gray-500 mt-2">
            Session: {response.session_id}
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls */}
        <div className="lg:col-span-1">
          {/* Stream Type Selection */}
          <div className="mb-4">
            <h3 className="font-semibold mb-2">Stream Type</h3>
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="radio"
                  value="sse"
                  checked={streamType === 'sse'}
                  onChange={(e) => setStreamType('sse')}
                  className="mr-2"
                />
                Server-Sent Events
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  value="websocket"
                  checked={streamType === 'websocket'}
                  onChange={(e) => setStreamType('websocket')}
                  className="mr-2"
                />
                WebSocket
              </label>
            </div>
          </div>

          {/* Event Type Filters */}
          <div className="mb-4">
            <h3 className="font-semibold mb-2">Event Filters</h3>
            <div className="space-y-2">
              {eventTypes.map((type) => (
                <label key={type} className="flex items-center text-sm">
                  <input
                    type="checkbox"
                    value={type}
                    checked={filterTypes.includes(type)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setFilterTypes([...filterTypes, type]);
                      } else {
                        setFilterTypes(filterTypes.filter((t) => t !== type));
                      }
                    }}
                    className="mr-2"
                  />
                  {type}
                </label>
              ))}
            </div>
          </div>

          {/* Stream Status */}
          <StreamStatus baseUrl={baseUrl} />

          {/* Connection Status */}
          <div className="mt-4">
            <div
              className={`px-3 py-2 rounded-lg text-center ${
                activeStream.isConnected
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
              }`}
            >
              {activeStream.isConnected ? '🟢 Connected' : '🔴 Disconnected'}
            </div>
            {activeStream.error && (
              <div className="mt-2 text-sm text-red-600">
                {activeStream.error}
              </div>
            )}
          </div>

          {/* Clear Events Button */}
          <button
            onClick={() => activeStream.clearEvents?.()}
            className="mt-4 w-full px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
          >
            Clear Events
          </button>
        </div>

        {/* Event Stream */}
        <div className="lg:col-span-2">
          <h3 className="font-semibold mb-4">
            Event Stream ({activeStream.events.length} events)
          </h3>
          <div className="max-h-[600px] overflow-y-auto space-y-2">
            {activeStream.events.length === 0 ? (
              <div className="text-gray-500 text-center py-8">
                No events yet. Send a query to see events stream in real-time.
              </div>
            ) : (
              activeStream.events.map((event) => (
                <EventDisplay key={event.id} event={event} />
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Example App Component
// ============================================================================

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <ClaudeStreamingInterface baseUrl="http://localhost:8000" />
    </div>
  );
}