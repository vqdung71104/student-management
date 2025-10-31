/**
 * Chatbot API Service
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export interface ChatMessage {
  message: string;
}

export interface ChatResponse {
  text: string;
  intent: string;
  confidence: string;
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

/**
 * Gửi tin nhắn tới chatbot
 */
export const sendMessage = async (message: string): Promise<ChatResponse> => {
  const response = await fetch(`${API_BASE_URL}/chatbot/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    throw new Error('Failed to send message to chatbot');
  }

  return response.json();
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
