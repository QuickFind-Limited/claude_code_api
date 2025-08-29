export type ModelType = 'claude-opus-4-1-20250805' | 'claude-sonnet-4-20250514';

export interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  events?: EventLog[];
  isStreaming?: boolean;
}

export interface EventLog {
  id: string;
  type: string;
  display: string;
  timestamp: string;
  details?: any;
}

export interface ChatSession {
  sessionId?: string;
  model: ModelType;
  messages: Message[];
}