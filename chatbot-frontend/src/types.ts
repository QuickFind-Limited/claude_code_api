export type ModelType = 'claude-opus-4-1-20250805' | 'claude-sonnet-4-20250514';

export interface FileInfo {
  path: string;
  absolute_path: string;
  size: number;
  modified: string;
  is_new: boolean;
  is_updated: boolean;
}

export interface FileChanges {
  attachments: FileInfo[];
  new_files: string[];
  updated_files: string[];
  summary?: {
    total_files: number;
    new_count: number;
    updated_count: number;
  };
}

export interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  events?: EventLog[];
  isStreaming?: boolean;
  fileChanges?: FileChanges;
}

export interface EventLog {
  id: string;
  type: string;
  display: string;
  timestamp: string;
  details?: any;
  full_content?: string; // Assistant message full content
}

export interface ChatSession {
  sessionId?: string;
  model: ModelType;
  messages: Message[];
  systemPrompt?: string;
}