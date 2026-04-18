/**
 * Chatbot API Service
 */

import { API_BASE } from '../utils/apiBase';

const API_BASE_URL = API_BASE;

const getAuthHeaders = (): Record<string, string> => {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export interface ChatMessage {
  message: string;
  student_id?: number;
  conversation_id?: number;
}

export interface ChatResponse {
  text: string;
  intent: string;
  confidence: string;
  data?: any[];
  metadata?: ClassSuggestionMetadata;
  sql?: string;
  sql_error?: string;
  is_compound?: boolean;
  conversation_id?: number;
  message_id?: number;
  created_at?: string;
  debug?: {
    trace_id?: string;
    mode?: string;
    route?: string;
    agent_enabled?: boolean;
    llm_called?: boolean;
    llm_paths?: string[];
    tools_called?: string[];
    fallback_reason?: string;
    [key: string]: any;
  };
  parts?: Array<{
    intent: string;
    confidence: string;
    text: string;
    data?: any[];
    sql_error?: string | null;
    query: string;
  }>;
}

export interface ChatStreamChunk {
  type: 'status' | 'data' | 'error' | 'done';
  stage?: 'preprocessing' | 'classification' | 'query' | 'formatting' | 'complete';
  message?: string;
  timestamp?: string;
  partial_data?: any[];
  data_count?: number;
  total_count?: number;
  text?: string;
  intent?: string;
  confidence?: string;
  data?: any[];
  metadata?: ClassSuggestionMetadata;
  is_compound?: boolean;
  parts?: Array<{
    intent: string;
    confidence: string;
    text: string;
    data?: any[];
    sql_error?: string | null;
    query: string;
  }>;
  conversation_id?: number;
  message_id?: number;
  created_at?: string;
  error_code?: string;
  error_detail?: string;
  debug?: {
    trace_id?: string;
    mode?: string;
    route?: string;
    agent_enabled?: boolean;
    llm_called?: boolean;
    llm_paths?: string[];
    tools_called?: string[];
    fallback_reason?: string;
    [key: string]: any;
  };
}

export interface PreferenceSummaryItem {
  key: string;
  label: string;
  value: string;
  status: string;
}

export interface MissingPreferenceItem {
  key: string;
  label: string;
  hint: string;
}

export interface PreferenceProgress {
  completed: number;
  total: number;
  percent: number;
}

export interface ClassSuggestionMetadata {
  ui: {
    title: string;
    subtitle: string;
    status: string;
    message?: string | null;
  };
  conversation: {
    stage: string;
    next_step: string;
    progress: PreferenceProgress;
    source_choice: string;
    subject_ids_seed_count: number;
    nlq_constraints?: Record<string, any> | null;
    current_question?: {
      key: string;
      label: string;
      question: string;
      options?: string[] | null;
      type: string;
    } | null;
  };
  preferences: {
    captured: PreferenceSummaryItem[];
    missing: MissingPreferenceItem[];
    auto_captured_keys: string[];
    summary: Record<string, any>;
  };
  notes: string[];
  result?: {
    total_subjects?: number;
    total_combinations?: number;
    student_cpa?: number;
    current_semester?: string;
    preferences_applied?: Record<string, any>;
  } | null;
}

export interface Intent {
  tag: string;
  description: string;
  examples: string[];
}

export interface IntentsResponse {
  total: number;
  intents: Intent[];
}

export interface ChatConversation {
  id: number;
  student_pk: number;
  title?: string;
  created_at: string;
  updated_at: string;
}

export interface ChatConversationListResponse {
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
  items: ChatConversation[];
  cache_hit: boolean;
}

export interface ChatHistoryMessage {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  intent?: string;
  confidence?: string;
  data_json?: any;
  sql_text?: string;
  sql_error?: string;
  created_at: string;
}

export interface ConversationMessagesResponse {
  conversation: ChatConversation;
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
  items: ChatHistoryMessage[];
  cache_hit: boolean;
}

/**
 * Gửi tin nhắn tới chatbot
 */
export const sendMessage = async (
  message: string, 
  studentId?: number,
  conversationId?: number
): Promise<ChatResponse> => {
  const body: ChatMessage = { message };
  if (studentId) {
    body.student_id = studentId;
  }
  if (conversationId) {
    body.conversation_id = conversationId;
  }

  const url = `${API_BASE_URL}/chatbot/chat`;
  console.log('[CHATBOT][REQUEST][sendMessage]', { url, body });

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error('Failed to send message to chatbot');
  }

  const json = await response.json();
  console.log('[CHATBOT][RESPONSE][sendMessage]', {
    status: response.status,
    debug: json?.debug,
    intent: json?.intent,
    confidence: json?.confidence,
    text: json?.text,
  });
  return json;
};

export const sendMessageStream = async (
  message: string,
  studentId: number | undefined,
  conversationId: number | undefined,
  onChunk: (chunk: ChatStreamChunk) => void,
  signal?: AbortSignal,
): Promise<ChatStreamChunk | null> => {
  const body: ChatMessage = { message };
  if (studentId) {
    body.student_id = studentId;
  }
  if (conversationId) {
    body.conversation_id = conversationId;
  }

  const url = `${API_BASE_URL}/chatbot/chat-stream`;
  console.log('[CHATBOT][REQUEST][sendMessageStream]', { url, body });

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      ...getAuthHeaders(),
    },
    body: JSON.stringify(body),
    signal,
  });

  if (!response.ok || !response.body) {
    throw new Error('Failed to start message stream');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  let doneChunk: ChatStreamChunk | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split('\n\n');
    buffer = events.pop() || '';

    for (const event of events) {
      const lines = event.split('\n');
      for (const line of lines) {
        if (!line.startsWith('data: ')) {
          continue;
        }
        const payload = line.slice(6).trim();
        if (!payload) {
          continue;
        }

        try {
          const chunk = JSON.parse(payload) as ChatStreamChunk;
          console.log('[CHATBOT][STREAM_CHUNK]', {
            type: chunk.type,
            stage: chunk.stage,
            message: chunk.message,
            intent: chunk.intent,
            confidence: chunk.confidence,
            debug: chunk.debug,
          });
          onChunk(chunk);
          if (chunk.type === 'done') {
            doneChunk = chunk;
          }
        } catch (error) {
          // Skip malformed chunks and keep stream alive.
          console.warn('Malformed stream chunk:', error);
        }
      }
    }
  }

  console.log('[CHATBOT][STREAM_DONE]', { debug: doneChunk?.debug, intent: doneChunk?.intent, text: doneChunk?.text });
  return doneChunk;
};

export const listConversations = async (
  studentId: number,
  page: number = 1,
  pageSize: number = 20
): Promise<ChatConversationListResponse> => {
  const query = new URLSearchParams({
    student_id: String(studentId),
    page: String(page),
    page_size: String(pageSize),
  });

  const response = await fetch(`${API_BASE_URL}/chatbot/conversations?${query.toString()}`);
  if (!response.ok) {
    throw new Error('Failed to load conversations');
  }

  return response.json();
};

export const getConversationMessages = async (
  conversationId: number,
  studentId: number,
  page: number = 1,
  pageSize: number = 50
): Promise<ConversationMessagesResponse> => {
  const query = new URLSearchParams({
    student_id: String(studentId),
    page: String(page),
    page_size: String(pageSize),
  });

  const response = await fetch(
    `${API_BASE_URL}/chatbot/conversations/${conversationId}/messages?${query.toString()}`
  );
  if (!response.ok) {
    throw new Error('Failed to load conversation messages');
  }

  return response.json();
};

export const renameConversation = async (
  conversationId: number,
  studentId: number,
  title: string
): Promise<ChatConversation> => {
  const response = await fetch(`${API_BASE_URL}/chatbot/conversations/${conversationId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      student_id: studentId,
      title,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to rename conversation');
  }

  return response.json();
};

export const deleteConversation = async (
  conversationId: number,
  studentId: number
): Promise<void> => {
  const query = new URLSearchParams({
    student_id: String(studentId),
  });

  const response = await fetch(
    `${API_BASE_URL}/chatbot/conversations/${conversationId}?${query.toString()}`,
    { method: 'DELETE' }
  );

  if (!response.ok) {
    throw new Error('Failed to delete conversation');
  }
};

/**
 * Lấy danh sách các intent mà chatbot hỗ trợ
 */
export const getAvailableIntents = async (): Promise<IntentsResponse> => {
  const response = await fetch(`${API_BASE_URL}/chatbot/intents`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch available intents');
  }

  return response.json();
};

/**
 * Export schedule combination to Excel file
 */
export const exportScheduleToExcel = async (
  combination: any,
  studentInfo?: any
): Promise<Blob> => {
  const response = await fetch(`${API_BASE_URL}/chatbot/export-schedule`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      combination,
      student_info: studentInfo,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to export schedule to Excel');
  }

  return response.blob();
};

