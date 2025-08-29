import React, { useState, useEffect, useRef } from 'react';
import { flushSync } from 'react-dom';
import { Message, ModelType, EventLog, ChatSession } from './types';
import './App.css';

const App: React.FC = () => {
  const [session, setSession] = useState<ChatSession>({
    model: 'claude-sonnet-4-20250514',
    messages: []
  });
  
  const [inputMessage, setInputMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [, forceUpdate] = useState({});

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

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
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
        let currentEventType = '';  // Move this outside the while loop
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              if (line.startsWith('event:')) {
                // Store the event type for the next data line
                currentEventType = line.slice(6).trim();
                console.log('Event type set to:', currentEventType);
              } else if (line.startsWith('data:')) {
                try {
                  const data = JSON.parse(line.slice(5).trim());
                  console.log(`SSE ${currentEventType || 'data'} received:`, data);
                  
                  // Handle different event types
                  if (currentEventType === 'connection') {
                    // Connection established
                    console.log('SSE connected:', data.client_id);
                  } else if (currentEventType === 'response') {
                    // Final response received
                    setSession(prev => ({
                      ...prev,
                      sessionId: data.session_id,
                      messages: prev.messages.map(msg => 
                        msg.id === assistantMessage.id 
                          ? { ...msg, content: data.response, isStreaming: false }
                          : msg
                      )
                    }));
                  } else if (currentEventType === 'complete') {
                    // Stream completed
                    setIsStreaming(false);
                  } else if (currentEventType === 'error') {
                    // Error occurred
                    setSession(prev => ({
                      ...prev,
                      messages: prev.messages.map(msg => 
                        msg.id === assistantMessage.id 
                          ? { ...msg, content: `Error: ${data.error}`, isStreaming: false }
                          : msg
                      )
                    }));
                    setIsStreaming(false);
                  } else if (currentEventType === 'log' && data.display) {
                    // Event log received - update immediately
                    const event: EventLog = {
                      id: Date.now().toString() + Math.random(),
                      type: data.type,
                      display: data.display,
                      timestamp: data.timestamp || new Date().toISOString(),
                      details: data.details
                    };
                    
                    console.log('📌 Adding live event to UI:', event.display);
                    console.log('Current assistant message ID:', assistantMessage.id);
                    
                    // Force immediate state update and render with flushSync
                    flushSync(() => {
                      setSession(prev => {
                        console.log('Previous messages:', prev.messages.length);
                        const updated = {
                          ...prev,
                          messages: prev.messages.map(msg => {
                            if (msg.id === assistantMessage.id) {
                              const newMsg = { ...msg, events: [...(msg.events || []), event] };
                              console.log('Updated message events:', newMsg.events?.length);
                              return newMsg;
                            }
                            return msg;
                          })
                        };
                        console.log('Updated session with event');
                        return updated;
                      });
                    });
                  }
                  
                  // Don't reset event type here - it might be needed for the next data line
                } catch (e) {
                  console.error('Failed to parse SSE data:', e, 'Line:', line);
                }
              } else if (line.trim() === '') {
                // Empty line indicates end of an event, reset the type
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
          msg.id === assistantMessage.id 
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
            <MessageComponent key={message.id} message={message} />
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

const MessageComponent: React.FC<{ message: Message }> = ({ message }) => {
  const [eventsExpanded, setEventsExpanded] = useState(true); // Default to expanded for streaming messages
  
  // Auto-expand events for streaming messages
  React.useEffect(() => {
    if (message.isStreaming && message.events && message.events.length > 0) {
      setEventsExpanded(true);
    }
  }, [message.isStreaming, message.events]);
  
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
        {/* Show events real-time even while streaming */}
        {message.events && message.events.length > 0 && (
          <div className="events-section">
            <button 
              className="events-toggle"
              onClick={() => setEventsExpanded(!eventsExpanded)}
            >
              {eventsExpanded ? '▼' : '▶'} Live Events ({message.events.length})
              {message.isStreaming && <span className="streaming-badge"> • LIVE</span>}
            </button>
            
            {eventsExpanded && (
              <div className="events-list">
                {/* Show events in reverse order (newest first) for better UX */}
                {[...message.events].reverse().map((event) => (
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