import React, { useEffect, useRef, useState } from "react";
import "./App.css";
import { ChatSession, EventLog, Message, ModelType } from "./types";

// API Base URL constant
const API_BASE_URL = "http://localhost:8000";

// Create a simple event emitter for real-time updates
class EventEmitter extends EventTarget {
  emit(type: string, detail: any) {
    this.dispatchEvent(new CustomEvent(type, { detail }));
  }
}

const eventBus = new EventEmitter();

const App: React.FC = () => {
  const [session, setSession] = useState<ChatSession>({
    model: "claude-sonnet-4-20250514",
    messages: [],
    systemPrompt: "",
  });

  const [inputMessage, setInputMessage] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [session.messages]);

  const resetSession = () => {
    setSession((prev) => ({
      ...prev,
      sessionId: undefined,
      messages: [],
    }));
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isStreaming) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: inputMessage,
      timestamp: new Date(),
    };

    const assistantMessageId = (Date.now() + 1).toString();
    const assistantMessage: Message = {
      id: assistantMessageId,
      type: "assistant",
      content: "",
      timestamp: new Date(),
      events: [],
      isStreaming: true,
    };

    // Update session with new messages
    setSession((prev) => ({
      ...prev,
      messages: [...prev.messages, userMessage, assistantMessage],
    }));

    setInputMessage("");
    setIsStreaming(true);

    console.log("🎯 STARTING STREAMING REQUEST:", inputMessage);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/query/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify({
          prompt: inputMessage,
          system_prompt: session.systemPrompt || undefined,
          model: session.model,
          session_id: session.sessionId,
          max_turns: 30,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      if (reader) {
        console.log("🌊 STREAM READER STARTED - Listening for events...");
        let currentEventType = "";
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) {
              console.log("🏁 STREAM COMPLETED");
              break;
            }

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
              if (line.startsWith("event:")) {
                currentEventType = line.slice(6).trim();
                console.log("🔥 STREAMING EVENT TYPE:", currentEventType);
              } else if (line.startsWith("data:")) {
                try {
                  const data = JSON.parse(line.slice(5).trim());
                  console.log(`🚀 STREAMING DATA [${currentEventType}]:`, data);

                  // Enhanced logging for different event types
                  if (currentEventType === "log" && data.display) {
                    console.log("📝 LIVE MESSAGE:", data.display);
                  }

                  if (currentEventType === "connection") {
                    console.log("Connected:", data.client_id);
                  } else if (currentEventType === "response") {
                    // Final response with file changes
                    console.log("📁 FILES INFO:", {
                      attachments: data.attachments,
                      new_files: data.new_files,
                      updated_files: data.updated_files,
                      summary: data.file_changes_summary
                    });
                    
                    setSession((prev) => ({
                      ...prev,
                      sessionId: data.session_id,
                      messages: prev.messages.map((msg) =>
                        msg.id === assistantMessageId
                          ? {
                              ...msg,
                              content: data.response,
                              isStreaming: false,
                              fileChanges: {
                                attachments: data.attachments || [],
                                new_files: data.new_files || [],
                                updated_files: data.updated_files || [],
                                summary: data.file_changes_summary
                              }
                            }
                          : msg
                      ),
                    }));
                  } else if (currentEventType === "complete") {
                    setIsStreaming(false);
                  } else if (currentEventType === "error") {
                    setSession((prev) => ({
                      ...prev,
                      messages: prev.messages.map((msg) =>
                        msg.id === assistantMessageId
                          ? {
                              ...msg,
                              content: `Error: ${data.error}`,
                              isStreaming: false,
                            }
                          : msg
                      ),
                    }));
                    setIsStreaming(false);
                  } else if (currentEventType === "log" && data.display) {
                    // Handle assistant_message events with full_content
                    if (data.type === "assistant_message" && data.full_content) {
                      console.log("🔵 ASSISTANT MESSAGE WITH FULL CONTENT:", data.full_content);
                      // Update the assistant message content immediately
                      setSession((prev) => ({
                        ...prev,
                        messages: prev.messages.map((msg) =>
                          msg.id === assistantMessageId
                            ? {
                                ...msg,
                                content: data.full_content,
                                isStreaming: true, // Keep streaming state until complete event
                              }
                            : msg
                        ),
                      }));
                    }

                    // Emit event for real-time update
                    const event: EventLog = {
                      id: Date.now().toString() + Math.random(),
                      type: data.type,
                      display: data.display,
                      timestamp: data.timestamp || new Date().toISOString(),
                      details: data.details,
                      full_content: data.full_content, // Include full_content in event
                    };

                    console.log("Emitting event:", event.display);
                    eventBus.emit(`message-event-${assistantMessageId}`, event);
                  }
                } catch (e) {
                  console.error("Parse error:", e);
                }
              } else if (line.trim() === "") {
                currentEventType = "";
              }
            }
          }
        } finally {
          reader.releaseLock();
        }
      }
    } catch (error) {
      console.error("Stream error:", error);
      setSession((prev) => ({
        ...prev,
        messages: prev.messages.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: `Connection error: ${error}`,
                isStreaming: false,
              }
            : msg
        ),
      }));
      setIsStreaming(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
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
              onChange={(e) =>
                setSession((prev) => ({
                  ...prev,
                  model: e.target.value as ModelType,
                }))
              }
              disabled={isStreaming}
            >
              <option value="claude-sonnet-4-20250514">Claude Sonnet 4</option>
              <option value="claude-opus-4-1-20250805">Claude Opus 4</option>
            </select>
          </div>
          <button
            onClick={resetSession}
            disabled={isStreaming}
            className="reset-btn"
          >
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
        <div className="system-prompt-wrapper">
          <textarea
            value={session.systemPrompt}
            onChange={(e) => setSession(prev => ({ ...prev, systemPrompt: e.target.value }))}
            placeholder="System prompt (optional)..."
            disabled={isStreaming}
            rows={2}
            className="system-prompt"
          />
        </div>
        <div className="input-wrapper">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message... (Shift+Enter for new line)"
            disabled={isStreaming}
            rows={3}
          />
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isStreaming}
          >
            {isStreaming ? "⏳" : "📨"}
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
const RealtimeMessageComponent: React.FC<{ message: Message }> = ({
  message,
}) => {
  const [events, setEvents] = useState<EventLog[]>(message.events || []);
  const [eventsExpanded, setEventsExpanded] = useState(true);

  // Listen for events via event bus
  useEffect(() => {
    if (message.type === "assistant") {
      const handleEvent = (e: CustomEvent) => {
        const newEvent = e.detail as EventLog;
        console.log("🎉 COMPONENT RECEIVED EVENT:", newEvent.display);
        console.log("🔍 Event details:", newEvent);
        setEvents((prev) => [...prev, newEvent]);
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
          {message.type === "user" ? "👤 You" : "🤖 Claude"}
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
              {eventsExpanded ? "▼" : "▶"} Live Events ({events.length})
              {message.isStreaming && (
                <span className="streaming-badge"> • LIVE</span>
              )}
            </button>

            {eventsExpanded && (
              <div className="events-list">
                {events.map((event) => (
                  <div key={event.id} className="event-item event-item-live">
                    <div className="event-display">{event.display}</div>
                    {event.full_content && (
                      <div className="full-content">
                        <strong>Assistant Response:</strong>
                        <pre className="assistant-full-content">{event.full_content}</pre>
                      </div>
                    )}
                    {event.details && (
                      <div className="event-details">
                        {typeof event.details === "object"
                          ? Object.entries(event.details).map(
                              ([key, value]) => (
                                <span key={key}>
                                  {key}: {String(value)}{" "}
                                </span>
                              )
                            )
                          : String(event.details)}
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

        {/* Show file changes */}
        {message.fileChanges && (message.fileChanges.new_files.length > 0 || message.fileChanges.updated_files.length > 0) && (
          <div className="file-changes-section">
            <h4>📁 Fichiers modifiés</h4>
            
            {message.fileChanges.new_files.length > 0 && (
              <div className="new-files">
                <strong>🆕 Nouveaux fichiers ({message.fileChanges.new_files.length}):</strong>
                <ul>
                  {message.fileChanges.new_files.map((filePath, index) => {
                    const fileInfo = message.fileChanges?.attachments.find(f => f.absolute_path === filePath);
                    return (
                      <li key={index}>
                        <span className="file-name">{fileInfo?.path || filePath}</span>
                        {fileInfo && (
                          <span className="file-details">
                            ({(fileInfo.size / 1024).toFixed(1)} KB)
                          </span>
                        )}
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {message.fileChanges.updated_files.length > 0 && (
              <div className="updated-files">
                <strong>✏️ Fichiers modifiés ({message.fileChanges.updated_files.length}):</strong>
                <ul>
                  {message.fileChanges.updated_files.map((filePath, index) => {
                    const fileInfo = message.fileChanges?.attachments.find(f => f.absolute_path === filePath);
                    return (
                      <li key={index}>
                        <span className="file-name">{fileInfo?.path || filePath}</span>
                        {fileInfo && (
                          <span className="file-details">
                            ({(fileInfo.size / 1024).toFixed(1)} KB, modifié à {new Date(fileInfo.modified).toLocaleTimeString()})
                          </span>
                        )}
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
