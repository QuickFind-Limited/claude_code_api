import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Message, ModelType, EventLog, ChatSession } from './types';
import './App.css';

// Create a simple event emitter for real-time updates
class EventEmitter extends EventTarget {
  emit(type: string, detail: any) {
    this.dispatchEvent(new CustomEvent(type, { detail }));
  }
}

const eventBus = new EventEmitter();

const App: React.FC = () => {
  const [session, setSession] = useState<ChatSession>({
    model: 'claude-sonnet-4-20250514',
    messages: []
  });
  
  const [inputMessage, setInputMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [session.messages]);

  const resetSession = () => {
    setSession(prev => ({
      ...prev,
      sessionId: undefined,
      messages: []
    }));
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isStreaming) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    const assistantMessageId = (Date.now() + 1).toString();
    const assistantMessage: Message = {
      id: assistantMessageId,
      type: 'assistant',
      content: '',
      timestamp: new Date(),
      events: [],
      isStreaming: true
    };

    // Update session with new messages
    setSession(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage, assistantMessage]
    }));

    setInputMessage('');
    setIsStreaming(true);

    try {
      const response = await fetch('/api/v1/query/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({
          prompt: inputMessage,
          model: session.model,
          session_id: session.sessionId,
          max_turns: 30
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      if (reader) {
        let currentEventType = '';
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              if (line.startsWith('event:')) {
                currentEventType = line.slice(6).trim();
                console.log('Event type:', currentEventType);
              } else if (line.startsWith('data:')) {
                try {
                  const data = JSON.parse(line.slice(5).trim());
                  console.log(`SSE ${currentEventType}:`, data);
                  
                  if (currentEventType === 'connection') {
                    console.log('Connected:', data.client_id);
                  } else if (currentEventType === 'response') {
                    // Final response
                    setSession(prev => ({
                      ...prev,
                      sessionId: data.session_id,
                      messages: prev.messages.map(msg => 
                        msg.id === assistantMessageId 
                          ? { ...msg, content: data.response, isStreaming: false }
                          : msg
                      )
                    }));
                  } else if (currentEventType === 'complete') {
                    setIsStreaming(false);
                  } else if (currentEventType === 'error') {
                    setSession(prev => ({
                      ...prev,
                      messages: prev.messages.map(msg => 
                        msg.id === assistantMessageId 
                          ? { ...msg, content: `Error: ${data.error}`, isStreaming: false }
                          : msg
                      )
                    }));
                    setIsStreaming(false);
                  } else if (currentEventType === 'log' && data.display) {
                    // Emit event for real-time update
                    const event: EventLog = {
                      id: Date.now().toString() + Math.random(),
                      type: data.type,
                      display: data.display,
                      timestamp: data.timestamp || new Date().toISOString(),
                      details: data.details
                    };
                    
                    console.log('Emitting event:', event.display);
                    eventBus.emit(`message-event-${assistantMessageId}`, event);
                  }
                } catch (e) {
                  console.error('Parse error:', e);
                }
              } else if (line.trim() === '') {
                currentEventType = '';
              }
            }
          }
        } finally {
          reader.releaseLock();
        }
      }
    } catch (error) {
      console.error('Stream error:', error);
      setSession(prev => ({
        ...prev,
        messages: prev.messages.map(msg => 
          msg.id === assistantMessageId 
            ? { ...msg, content: `Connection error: ${error}`, isStreaming: false }
            : msg
        )
      }));
      setIsStreaming(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🤖 Claude Chatbot</h1>
        <div className="header-controls">
          <div className="model-selector">
            <label htmlFor="model">Model:</label>
            <select
              id="model"
              value={session.model}
              onChange={(e) => setSession(prev => ({ ...prev, model: e.target.value as ModelType }))}
              disabled={isStreaming}
            >
              <option value="claude-sonnet-4-20250514">Claude Sonnet 4</option>
              <option value="claude-opus-4-1-20250805">Claude Opus 4</option>
            </select>
          </div>
          <button onClick={resetSession} disabled={isStreaming} className="reset-btn">
            🔄 New Session
          </button>
        </div>
      </header>

      <div className="messages-container">
        <div className="messages">
          {session.messages.map((message) => (
            <RealtimeMessageComponent key={message.id} message={message} />
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="input-container">
        <div className="input-wrapper">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message... (Shift+Enter for new line)"
            disabled={isStreaming}
            rows={3}
          />
          <button onClick={sendMessage} disabled={!inputMessage.trim() || isStreaming}>
            {isStreaming ? '⏳' : '📨'}
          </button>
        </div>
      </div>

      {session.sessionId && (
        <div className="session-info">
          Session: {session.sessionId.substring(0, 8)}...
        </div>
      )}
    </div>
  );
};

// Separate component that manages its own events state
const RealtimeMessageComponent: React.FC<{ message: Message }> = ({ message }) => {
  const [events, setEvents] = useState<EventLog[]>(message.events || []);
  const [eventsExpanded, setEventsExpanded] = useState(true);
  
  // Listen for events via event bus
  useEffect(() => {
    if (message.type === 'assistant') {
      const handleEvent = (e: CustomEvent) => {
        const newEvent = e.detail as EventLog;
        console.log('Received event in component:', newEvent.display);
        setEvents(prev => [...prev, newEvent]);
      };
      
      const eventName = `message-event-${message.id}`;
      eventBus.addEventListener(eventName, handleEvent as EventListener);
      
      return () => {
        eventBus.removeEventListener(eventName, handleEvent as EventListener);
      };
    }
  }, [message.id, message.type]);
  
  // Auto-expand for streaming messages
  useEffect(() => {
    if (message.isStreaming && events.length > 0) {
      setEventsExpanded(true);
    }
  }, [message.isStreaming, events]);
  
  return (
    <div className={`message ${message.type}`}>
      <div className="message-header">
        <span className="message-type">
          {message.type === 'user' ? '👤 You' : '🤖 Claude'}
        </span>
        <span className="message-time">
          {message.timestamp.toLocaleTimeString()}
        </span>
      </div>
      
      <div className="message-content">
        {/* Show events real-time */}
        {events.length > 0 && (
          <div className="events-section">
            <button 
              className="events-toggle"
              onClick={() => setEventsExpanded(!eventsExpanded)}
            >
              {eventsExpanded ? '▼' : '▶'} Live Events ({events.length})
              {message.isStreaming && <span className="streaming-badge"> • LIVE</span>}
            </button>
            
            {eventsExpanded && (
              <div className="events-list">
                {[...events].reverse().map((event) => (
                  <div key={event.id} className="event-item event-item-live">
                    <div className="event-display">{event.display}</div>
                    {event.details && (
                      <div className="event-details">
                        {typeof event.details === 'object' 
                          ? Object.entries(event.details).map(([key, value]) => (
                              <span key={key}>{key}: {String(value)} </span>
                            ))
                          : String(event.details)
                        }
                      </div>
                    )}
                    <div className="event-time">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        
        {/* Show content or thinking indicator */}
        {message.isStreaming && !message.content ? (
          <div className="streaming-indicator">
            <div className="dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
            Processing response...
          </div>
        ) : message.content ? (
          <pre className="message-text">{message.content}</pre>
        ) : null}
      </div>
    </div>
  );
};

export default App;