/**
 * ChatBot Component - Messenger-style Chat Interface
 */
import React, { useState, useRef, useEffect } from 'react';
import {
  sendMessage,
  sendMessageStream,
  exportScheduleToExcel,
  listConversations,
  getConversationMessages,
  deleteConversation,
  renameConversation,
} from '../../services/chatbot.service';
import type {
  ChatResponse,
  ChatStreamChunk,
  ChatConversation,
  ChatHistoryMessage,
  ClassSuggestionMetadata,
  LLMProcessingMetadata,
} from '../../services/chatbot.service';
import { useAuth } from '../../contexts/AuthContext';
import './ChatBot.css';

interface Message {
  id: number;
  text: string;
  isUser: boolean;
  timestamp: Date;
  intent?: string;
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
  llm_processing?: LLMProcessingMetadata;
  debug?: ChatResponse['debug'];
}

interface InteractiveQuestion {
  key: string;
  label: string;
  question: string;
  options?: string[] | null;
  type: 'single_choice' | 'multi_choice' | 'free_text';
}

type StreamStage = 'preprocessing' | 'classification' | 'query' | 'formatting' | 'complete';

const STREAM_STAGE_PROGRESS: Record<StreamStage, number> = {
  preprocessing: 20,
  classification: 45,
  query: 75,
  formatting: 90,
  complete: 100,
};

const STREAM_STAGE_LABEL: Record<StreamStage, string> = {
  preprocessing: 'Chuẩn hóa câu hỏi',
  classification: 'Phân loại ý định',
  query: 'Truy vấn dữ liệu',
  formatting: 'Định dạng kết quả',
  complete: 'Hoàn tất',
};

const logChatbotExecution = (
  label: string,
  payload: {
    debug?: ChatResponse['debug'] | ChatStreamChunk['debug'];
    intent?: string;
    confidence?: string;
    text?: string;
    stage?: StreamStage;
    type?: ChatStreamChunk['type'];
    message?: string;
  },
) => {
  const debug = payload.debug || {};
  console.log(`[CHATBOT][WEB][${label}]`, {
    trace_id: debug.trace_id,
    mode: debug.mode,
    route: debug.route,
    agent_enabled: debug.agent_enabled,
    llm_called: debug.llm_called,
    llm_paths: debug.llm_paths,
    tools_called: debug.tools_called,
    fallback_reason: debug.fallback_reason,
    intent: payload.intent,
    confidence: payload.confidence,
    stage: payload.stage,
    type: payload.type,
    message: payload.message,
    text: payload.text,
  });
};

const toggleDebug = (messageId: number, showDebug: Record<number, boolean>, setShowDebug: React.Dispatch<React.SetStateAction<Record<number, boolean>>>) => {
  setShowDebug((prev) => ({
    ...prev,
    [messageId]: !prev[messageId],
  }));
};

const hasDebugInfo = (message: Message): boolean => {
  return Boolean(
    message.llm_processing ||
    message.debug ||
    message.intent
  );
};

const renderLLMDebugSection = (llm_processing?: LLMProcessingMetadata, messageId?: number) => {
  if (!llm_processing) return null;

  return (
    <div className="llm-debug-section">
      <div className="llm-debug-header">
        <span className="llm-debug-icon">🔍</span>
        <span className="llm-debug-title">Process Info</span>
        {llm_processing.has_repetition && (
          <span className="llm-debug-warning" title="Phát hiện lặp trong output">
            ⚠️ Cảnh báo: Có dấu hiệu lặp
          </span>
        )}
      </div>

      <div className="llm-debug-content">
        <div className="llm-debug-row">
          <div className="llm-debug-label">Nội dung gửi LLM (Input):</div>
          <div className="llm-debug-value llm-debug-input">
            {llm_processing.user_input || '-'}
          </div>
        </div>

        <div className="llm-debug-row">
          <div className="llm-debug-label">Kết quả sau xử lý (Output):</div>
          <div className={`llm-debug-value llm-debug-output ${llm_processing.has_repetition ? 'has-repetition' : ''}`}>
            {llm_processing.llm_processed_output || '-'}
          </div>
        </div>

        {llm_processing.has_repetition && llm_processing.repetition_segments && llm_processing.repetition_segments.length > 0 && (
          <div className="llm-debug-row llm-debug-repetition">
            <div className="llm-debug-label">Đoạn bị lặp:</div>
            <div className="llm-debug-value">
              <ul className="repetition-list">
                {llm_processing.repetition_segments.map((segment, idx) => (
                  <li key={idx} className="repetition-item">
                    {segment.length > 100 ? `${segment.substring(0, 100)}...` : segment}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {llm_processing.processing_time_ms && (
          <div className="llm-debug-row llm-debug-meta">
            <div className="llm-debug-label">Thời gian xử lý:</div>
            <div className="llm-debug-value">
              {llm_processing.processing_time_ms.toFixed(2)} ms
            </div>
          </div>
        )}

        {llm_processing.model_used && (
          <div className="llm-debug-row llm-debug-meta">
            <div className="llm-debug-label">Model:</div>
            <div className="llm-debug-value">
              {llm_processing.model_used}
            </div>
          </div>
        )}

        {llm_processing.token_count && (
          <div className="llm-debug-row llm-debug-meta">
            <div className="llm-debug-label">Tokens sử dụng:</div>
            <div className="llm-debug-value">
              {llm_processing.token_count}
            </div>
          </div>
        )}

        {llm_processing.raw_data && (
          <details className="llm-debug-raw-data">
            <summary>Raw Data</summary>
            <pre>{JSON.stringify(llm_processing.raw_data, null, 2)}</pre>
          </details>
        )}
      </div>
    </div>
  );
};

const renderDebugSection = (message: Message, messageId: number, showDebug: Record<number, boolean>, setShowDebug: React.Dispatch<React.SetStateAction<Record<number, boolean>>>) => {
  if (!hasDebugInfo(message)) return null;

  return (
    <div className="message-debug-wrapper">
      <button
        className={`debug-toggle-btn ${showDebug[messageId] ? 'active' : ''}`}
        onClick={() => toggleDebug(messageId, showDebug, setShowDebug)}
        title={showDebug[messageId] ? 'Ẩn Debug Info' : 'Hiện Debug Info'}
      >
        {showDebug[messageId] ? '🔒 Ẩn Debug' : '🔓 Debug'}
      </button>

      {showDebug[messageId] && (
        <div className="message-debug-panel">
          <div className="debug-section-header">Debug / Process Info</div>

          {renderLLMDebugSection(message.llm_processing, messageId)}

          {message.debug && (
            <div className="debug-execution-info">
              <div className="debug-section-subheader">Execution Debug</div>
              <div className="debug-info-grid">
                <div className="debug-info-item">
                  <span className="debug-info-label">Trace ID:</span>
                  <span className="debug-info-value">{message.debug.trace_id || '-'}</span>
                </div>
                <div className="debug-info-item">
                  <span className="debug-info-label">Mode:</span>
                  <span className="debug-info-value">{message.debug.mode || '-'}</span>
                </div>
                <div className="debug-info-item">
                  <span className="debug-info-label">Route:</span>
                  <span className="debug-info-value">{message.debug.route || '-'}</span>
                </div>
                <div className="debug-info-item">
                  <span className="debug-info-label">Intent:</span>
                  <span className="debug-info-value">{message.intent || '-'}</span>
                </div>
                <div className="debug-info-item">
                  <span className="debug-info-label">LLM Called:</span>
                  <span className="debug-info-value">{message.debug.llm_called ? 'Yes' : 'No'}</span>
                </div>
                {message.debug.llm_paths && message.debug.llm_paths.length > 0 && (
                  <div className="debug-info-item">
                    <span className="debug-info-label">LLM Paths:</span>
                    <span className="debug-info-value">{message.debug.llm_paths.join(', ')}</span>
                  </div>
                )}
                {message.debug.fallback_reason && (
                  <div className="debug-info-item debug-info-warning">
                    <span className="debug-info-label">Fallback Reason:</span>
                    <span className="debug-info-value">{message.debug.fallback_reason}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const ChatBot: React.FC = () => {
  const { userInfo } = useAuth();
  const welcomeMessage: Message = {
    id: 0,
    text: 'Xin chào! Mình là trợ lý ảo của hệ thống quản lý sinh viên. Mình có thể giúp gì cho bạn?',
    isUser: false,
    timestamp: new Date(),
  };
  const activeConversationStorageKey = 'chatbot_active_conversation_id';

  const [messages, setMessages] = useState<Message[]>([
    welcomeMessage,
  ]);
  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [messagesPage, setMessagesPage] = useState(1);
  const [hasOlderMessages, setHasOlderMessages] = useState(false);
  const [isLoadingOlder, setIsLoadingOlder] = useState(false);
  const [contextMenu, setContextMenu] = useState<{
    x: number;
    y: number;
    conversation: ChatConversation;
  } | null>(null);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [streamingStatus, setStreamingStatus] = useState<string>('');
  const [streamingStage, setStreamingStage] = useState<StreamStage>('preprocessing');
  const [streamingProgress, setStreamingProgress] = useState<number>(0);
  const [pendingMultiOptions, setPendingMultiOptions] = useState<Record<number, string[]>>({});
  const [selectedComboClass, setSelectedComboClass] = useState<{
    combinationKey: string;
    classKey: string;
    classInfo: any;
  } | null>(null);
  const [showDebug, setShowDebug] = useState<Record<number, boolean>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const streamAbortRef = useRef<AbortController | null>(null);

  // Auto scroll to bottom when new message added
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [inputValue]);

  useEffect(() => {
    const closeContextMenu = () => setContextMenu(null);
    window.addEventListener('click', closeContextMenu);
    return () => window.removeEventListener('click', closeContextMenu);
  }, []);

  const mapHistoryMessages = (items: ChatHistoryMessage[]): Message[] => {
    return items.map((item) => ({
      id: item.id,
      text: item.content,
      isUser: item.role === 'user',
      timestamp: new Date(item.created_at),
      intent: item.intent,
      metadata: item.data_json?.metadata,
      data: Array.isArray(item.data_json)
        ? item.data_json
        : Array.isArray(item.data_json?.data)
          ? item.data_json.data
          : undefined,
      is_compound: Boolean(item.data_json?.is_compound),
      parts: Array.isArray(item.data_json?.parts) ? item.data_json.parts : undefined,
      llm_processing: item.data_json?.llm_processing,
      debug: item.data_json?.debug,
    }));
  };

  const loadConversation = async (conversationId: number, page: number = 1, appendOlder: boolean = false) => {
    if (!userInfo?.id) {
      return;
    }

    const result = await getConversationMessages(conversationId, userInfo.id, page, 20);
    const loaded = mapHistoryMessages(result.items);
    setMessages((prev) => {
      if (appendOlder) {
        const existingIds = new Set(prev.map((message) => message.id));
        const deduped = loaded.filter((message) => !existingIds.has(message.id));
        return [...deduped, ...prev];
      }

      return loaded.length > 0 ? loaded : [welcomeMessage];
    });
    setActiveConversationId(conversationId);
    setMessagesPage(page);
    setHasOlderMessages(result.has_more);
    localStorage.setItem(activeConversationStorageKey, String(conversationId));
  };

  const refreshConversations = async (preferredConversationId?: number) => {
    if (!userInfo?.id) {
      return;
    }

    const result = await listConversations(userInfo.id, 1, 30);
    setConversations(result.items);

    if (result.items.length === 0) {
      setActiveConversationId(null);
      setMessagesPage(1);
      setHasOlderMessages(false);
      localStorage.removeItem(activeConversationStorageKey);
      setMessages([welcomeMessage]);
      return;
    }

    const stored = Number(localStorage.getItem(activeConversationStorageKey));
    const candidate = preferredConversationId || (Number.isNaN(stored) ? undefined : stored) || result.items[0].id;
    const exists = result.items.some((item) => item.id === candidate);
    const resolved = exists ? candidate : result.items[0].id;
    await loadConversation(resolved);
  };

  useEffect(() => {
    const bootstrap = async () => {
      if (!userInfo?.id) {
        return;
      }

      setIsBootstrapping(true);
      try {
        await refreshConversations();
      } catch (error) {
        console.error('Error loading chat history:', error);
        setMessages([welcomeMessage]);
      } finally {
        setIsBootstrapping(false);
      }
    };

    bootstrap();
  }, [userInfo?.id]);

  const sendChatMessage = async (rawText: string) => {
    if (!rawText.trim() || isLoading) {
      return;
    }

    const outgoingText = rawText.trim();

    const userMessage: Message = {
      id: Date.now(),
      text: outgoingText,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setStreamingStatus('Đang gửi câu hỏi...');
    setStreamingStage('preprocessing');
    setStreamingProgress(10);
    streamAbortRef.current = new AbortController();

    try {
      console.log('[CHATBOT][UI] sendChatMessage start', {
        text: outgoingText,
        conversationId: activeConversationId || undefined,
        mode: 'stream-first',
      });
      const doneChunk = await sendMessageStream(
        outgoingText,
        userInfo?.id,
        activeConversationId || undefined,
        (chunk: ChatStreamChunk) => {
          logChatbotExecution('stream_chunk', {
            debug: chunk.debug,
            intent: chunk.intent,
            confidence: chunk.confidence,
            stage: chunk.stage as StreamStage | undefined,
            type: chunk.type,
            message: chunk.message,
            text: chunk.text,
          });
          console.log('[CHATBOT][UI][chunk]', {
            type: chunk.type,
            stage: chunk.stage,
            message: chunk.message,
            intent: chunk.intent,
            confidence: chunk.confidence,
            debug: chunk.debug,
          });
          if (chunk.stage) {
            const nextStage = chunk.stage as StreamStage;
            if (STREAM_STAGE_PROGRESS[nextStage] !== undefined) {
              setStreamingStage(nextStage);
              setStreamingProgress(STREAM_STAGE_PROGRESS[nextStage]);
            }
          }

          if (chunk.type === 'status' && chunk.message) {
            setStreamingStatus(chunk.message);
            return;
          }

          if (chunk.type === 'data' && chunk.message) {
            setStreamingStatus(chunk.message);
            setStreamingProgress((prev) => Math.max(prev, 82));
            return;
          }

          if (chunk.type === 'error') {
            throw new Error(chunk.error_detail || chunk.message || 'Streaming error');
          }
        },
        streamAbortRef.current.signal,
      );

      if (!doneChunk) {
        throw new Error('Không nhận được phản hồi cuối từ luồng streaming');
      }

      setStreamingStage('complete');
      setStreamingProgress(100);

      console.log('[CHATBOT][UI] stream final chunk', {
        intent: doneChunk.intent,
        confidence: doneChunk.confidence,
        debug: doneChunk.debug,
        text: doneChunk.text,
      });
      logChatbotExecution('stream_final', {
        debug: doneChunk.debug,
        intent: doneChunk.intent,
        confidence: doneChunk.confidence,
        text: doneChunk.text,
        stage: doneChunk.stage as StreamStage | undefined,
        type: doneChunk.type,
        message: doneChunk.message,
      });

      const finalResponse: ChatResponse = {
        text: doneChunk.text || 'Hoàn tất xử lý',
        intent: doneChunk.intent || 'unknown',
        confidence: doneChunk.confidence || 'low',
        data: doneChunk.data,
        metadata: doneChunk.metadata,
        is_compound: doneChunk.is_compound,
        parts: doneChunk.parts,
        conversation_id: doneChunk.conversation_id,
        message_id: doneChunk.message_id,
        created_at: doneChunk.created_at,
        debug: doneChunk.debug,
        llm_processing: doneChunk.llm_processing,
      };

      if (finalResponse.conversation_id && finalResponse.conversation_id !== activeConversationId) {
        setActiveConversationId(finalResponse.conversation_id);
        localStorage.setItem(activeConversationStorageKey, String(finalResponse.conversation_id));
        setIsHistoryOpen(true);
      }

      const botMessage: Message = {
        id: Date.now() + 1,
        text: finalResponse.text,
        isUser: false,
        timestamp: new Date(),
        intent: finalResponse.intent,
        data: finalResponse.data,
        metadata: finalResponse.metadata,
        is_compound: finalResponse.is_compound,
        parts: finalResponse.parts,
        llm_processing: finalResponse.llm_processing,
        debug: finalResponse.debug,
      };

      setMessages((prev) => [...prev, botMessage]);

      console.log('[CHATBOT][UI] rendered bot message', {
        intent: botMessage.intent,
        debug: finalResponse.debug,
      });

      if (userInfo?.id) {
        try {
          const result = await listConversations(userInfo.id, 1, 30);
          setConversations(result.items);
        } catch (refreshError) {
          console.error('Error refreshing conversation list:', refreshError);
        }
      }
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        const cancelledMessage: Message = {
          id: Date.now() + 1,
          text: 'Bạn đã hủy yêu cầu trước khi hệ thống trả kết quả.',
          isUser: false,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, cancelledMessage]);
        return;
      }

      console.error('Error streaming message, fallback to normal API:', error);

      try {
        setStreamingStatus('Streaming lỗi, đang chuyển sang chế độ thường...');
        console.log('[CHATBOT][UI] fallback to non-streaming sendMessage');
        const response: ChatResponse = await sendMessage(outgoingText, userInfo?.id, activeConversationId || undefined);

        console.log('[CHATBOT][UI] fallback response', {
          intent: response.intent,
          confidence: response.confidence,
          debug: response.debug,
          text: response.text,
        });
        logChatbotExecution('fallback_response', {
          debug: response.debug,
          intent: response.intent,
          confidence: response.confidence,
          text: response.text,
        });

        if (response.conversation_id && response.conversation_id !== activeConversationId) {
          setActiveConversationId(response.conversation_id);
          localStorage.setItem(activeConversationStorageKey, String(response.conversation_id));
          setIsHistoryOpen(true);
        }

        const botMessage: Message = {
          id: Date.now() + 1,
          text: response.text,
          isUser: false,
          timestamp: new Date(),
          intent: response.intent,
          data: response.data,
          metadata: response.metadata,
          is_compound: response.is_compound,
          parts: response.parts,
          llm_processing: response.llm_processing,
          debug: response.debug,
        };

        setMessages((prev) => [...prev, botMessage]);
        console.log('[CHATBOT][UI] rendered fallback bot message', {
          intent: botMessage.intent,
          debug: response.debug,
        });
      } catch (fallbackError) {
        console.error('Error sending message in fallback mode:', fallbackError);

        const errorMessage: Message = {
          id: Date.now() + 1,
          text: 'Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại sau.',
          isUser: false,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, errorMessage]);
      }
    } finally {
      streamAbortRef.current = null;
      setIsLoading(false);
      setStreamingStatus('');
      setStreamingProgress(0);
    }
  };

  const handleSendMessage = async () => {
    await sendChatMessage(inputValue);
  };

  const normalizeOptionPayload = (questionKey: string, selectedOptions: string[]): string => {
    if (selectedOptions.length === 0) {
      return '';
    }

    if (questionKey === 'day') {
      return selectedOptions.join(', ');
    }

    return selectedOptions.join(', ');
  };

  const handleSingleOptionSelect = async (option: string) => {
    if (isLoading) {
      return;
    }

    await sendChatMessage(option);
  };

  const handleToggleMultiOption = (messageId: number, option: string) => {
    if (isLoading) {
      return;
    }

    setPendingMultiOptions((prev) => {
      const current = prev[messageId] || [];
      const exists = current.includes(option);
      const next = exists ? current.filter((item) => item !== option) : [...current, option];
      return {
        ...prev,
        [messageId]: next,
      };
    });
  };

  const handleConfirmMultiChoice = async (messageId: number, questionKey: string) => {
    if (isLoading) {
      return;
    }

    const selected = pendingMultiOptions[messageId] || [];
    const payload = normalizeOptionPayload(questionKey, selected);

    if (!payload) {
      return;
    }

    setPendingMultiOptions((prev) => ({
      ...prev,
      [messageId]: [],
    }));

    await sendChatMessage(payload);
  };

  const handleCancelStreaming = () => {
    if (!isLoading) {
      return;
    }

    setStreamingStatus('Đang hủy yêu cầu...');
    streamAbortRef.current?.abort();
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('vi-VN', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Format message text with basic markdown support
  const formatMessageText = (text: string): string => {
    return text
      // Convert **bold** to <strong>
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      // Convert line breaks to <br/>
      .replace(/\n/g, '<br/>')
      // Convert bullet points • to proper list items
      .replace(/^• (.+)$/gm, '<div class="bullet-item">• $1</div>');
  };

  // Handle Excel download
  const handleDownloadExcel = async (combination: any, index: number) => {
    try {
      const blob = await exportScheduleToExcel(combination, {
        semester: userInfo?.semester,
        cpa: userInfo?.cpa,
      });

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Phuong_An_${index}_Lich_Hoc.xlsx`;
      document.body.appendChild(a);
      a.click();

      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading Excel:', error);
      alert('Có lỗi xảy ra khi tải file Excel. Vui lòng thử lại.');
    }
  };

  const COMBO_DAYS = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];
  const COMBO_TIME_SLOTS = Array.from({ length: 13 }, (_, idx) => {
    const hour = idx + 6;
    return `${hour.toString().padStart(2, '0')}:00`;
  });

  const dayToIndex = (studyDate: string | undefined): number => {
    if (!studyDate) return 1;
    const value = studyDate.toLowerCase();
    if (value.includes('sunday') || value.includes('chủ nhật') || value === 'cn') return 0;
    if (value.includes('monday') || value.includes('thứ 2') || value === 't2') return 1;
    if (value.includes('tuesday') || value.includes('thứ 3') || value === 't3') return 2;
    if (value.includes('wednesday') || value.includes('thứ 4') || value === 't4') return 3;
    if (value.includes('thursday') || value.includes('thứ 5') || value === 't5') return 4;
    if (value.includes('friday') || value.includes('thứ 6') || value === 't6') return 5;
    if (value.includes('saturday') || value.includes('thứ 7') || value === 't7') return 6;
    return 1;
  };

  const toMinutes = (time: string | undefined): number => {
    if (!time) return 0;
    const [h, m] = String(time).split(':');
    return Number(h || 0) * 60 + Number(m || 0);
  };

  const getComboDayLabel = (studyDate: string | undefined): string => {
    const index = dayToIndex(studyDate);
    return COMBO_DAYS[index] || 'T2';
  };

  const formatStudyWeek = (studyWeek: unknown): string => {
    if (studyWeek === null || studyWeek === undefined) return '-';
    const raw = String(studyWeek).trim();
    if (!raw) return '-';

    if (raw.includes(',') || raw.includes(' ') || raw.includes('-')) {
      return raw;
    }

    if (/^\d+$/.test(raw) && raw.length >= 4 && raw.length % 2 === 0) {
      const chunks = raw.match(/\d{2}/g);
      return chunks ? chunks.join(', ') : raw;
    }

    return raw;
  };

  const renderCombinationTimetable = (classes: any[], combinationKey: string) => {
    if (!Array.isArray(classes) || classes.length === 0) {
      return null;
    }

    const selectedInCurrentCombination =
      selectedComboClass && selectedComboClass.combinationKey === combinationKey
        ? selectedComboClass
        : null;

    return (
      <div className="combo-timetable-wrap">
        <div className="combo-timetable-header">
          <div className="combo-time-head" />
          {COMBO_DAYS.map((day) => (
            <div key={day} className="combo-day-head">{day}</div>
          ))}
        </div>

        <div className="combo-timetable-grid">
          <div className="combo-time-col">
            {COMBO_TIME_SLOTS.map((slot) => (
              <div key={slot} className="combo-time-slot">{slot}</div>
            ))}
          </div>

          {COMBO_DAYS.map((day) => (
            <div key={day} className="combo-day-col">
              {COMBO_TIME_SLOTS.map((slot) => (
                <div key={`${day}-${slot}`} className="combo-grid-cell" />
              ))}

              {classes
                .filter((cls) => dayToIndex(cls.study_date) === COMBO_DAYS.indexOf(day))
                .map((cls, index) => {
                  const start = toMinutes(cls.study_time_start);
                  const end = toMinutes(cls.study_time_end);
                  const top = ((start - 360) / 60) * 42;
                  const height = Math.max((((end - start) / 60) * 42), 36);
                  const classKey = `${cls.class_id || 'cls'}-${day}-${cls.study_time_start || ''}-${index}`;
                  const isSelected = selectedInCurrentCombination?.classKey === classKey;

                  return (
                    <div
                      key={classKey}
                      className={`combo-class-block ${isSelected ? 'is-selected' : ''}`}
                      style={{ top: `${top}px`, height: `${height}px` }}
                      title={`${cls.subject_id || '-'} - ${cls.subject_name || cls.class_name || '-'}\n${cls.study_time_start || '--:--'} - ${cls.study_time_end || '--:--'}\nPhòng: ${cls.classroom || '-'}${cls.teacher_name ? `\nGV: ${cls.teacher_name}` : ''}`}
                      onClick={() => setSelectedComboClass({
                        combinationKey,
                        classKey,
                        classInfo: cls,
                      })}
                    >
                      <div className="combo-class-name">{cls.subject_id || '-'} - {cls.subject_name || cls.class_name || '-'}</div>
                      <div className="combo-class-time">{cls.study_time_start || '--:--'} - {cls.study_time_end || '--:--'}</div>
                      <div className="combo-class-room">{cls.classroom || '-'}</div>
                    </div>
                  );
                })}
            </div>
          ))}
        </div>

        {selectedInCurrentCombination && (
          <div className="combo-class-detail" role="status" aria-live="polite">
            <div className="combo-class-detail-header">
              <span>Chi tiết lớp đã chọn</span>
              <button
                type="button"
                className="combo-class-detail-close"
                onClick={() => setSelectedComboClass(null)}
              >
                Đóng
              </button>
            </div>

            <div className="combo-class-detail-body">
              <div><strong>Môn:</strong> {selectedInCurrentCombination.classInfo.subject_id || '-'} - {selectedInCurrentCombination.classInfo.subject_name || selectedInCurrentCombination.classInfo.class_name || '-'}</div>
              <div><strong>Lớp:</strong> {selectedInCurrentCombination.classInfo.class_name || '-'}</div>
              <div><strong>Thời gian:</strong> {selectedInCurrentCombination.classInfo.study_time_start || '--:--'} - {selectedInCurrentCombination.classInfo.study_time_end || '--:--'}</div>
              <div><strong>Thứ:</strong> {getComboDayLabel(selectedInCurrentCombination.classInfo.study_date)}{selectedInCurrentCombination.classInfo.study_date ? ` (${selectedInCurrentCombination.classInfo.study_date})` : ''}</div>
              <div><strong>Phòng:</strong> {selectedInCurrentCombination.classInfo.classroom || '-'}</div>
              {selectedInCurrentCombination.classInfo.teacher_name && (
                <div><strong>Giảng viên:</strong> {selectedInCurrentCombination.classInfo.teacher_name}</div>
              )}
              {selectedInCurrentCombination.classInfo.study_week && (
                <div><strong>Tuần:</strong> {formatStudyWeek(selectedInCurrentCombination.classInfo.study_week)}</div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  // Render class schedule combinations (for class suggestion intent)
  const renderClassCombinations = (data: any[]) => {
    if (!data || data.length === 0) return null;

    return (
      <div className="class-combinations">
        {data.map((combination, idx) => (
          <div key={idx} className="combination-card">
            {/* Combination Header */}
            <div className="combination-header">
              <div className="combination-title">
                {combination.recommended && <span className="badge recommended">⭐ KHUYÊN DÙNG</span>}
                <span className="badge-number">Phương án {combination.combination_id || idx + 1}</span>
                {combination.score && (
                  <span className="combination-score">Điểm: {combination.score}/100</span>
                )}
              </div>
              <button
                className="download-excel-btn"
                onClick={() => handleDownloadExcel(combination, combination.combination_id || idx + 1)}
                title="Tải file Excel"
              >
                📥 Tải Excel
              </button>
            </div>

            {/* Metrics Summary */}
            {combination.metrics && (
              <div className="metrics-summary">
                <div className="metric-item">
                  <span className="metric-label">📚 Tổng:</span>
                  <span className="metric-value">
                    {combination.metrics.total_classes} môn - {combination.metrics.total_credits} TC
                  </span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">📅 Lịch:</span>
                  <span className="metric-value">
                    Học {combination.metrics.study_days} ngày/tuần
                  </span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">⏰ Giờ học:</span>
                  <span className="metric-value">
                    {combination.metrics.earliest_start} - {combination.metrics.latest_end}
                  </span>
                </div>
              </div>
            )}

            {Array.isArray(combination.reasoning) && combination.reasoning.length > 0 && (
              <div className="combination-reasoning">
                <div className="combination-reasoning-title">Vì sao phương án này tốt</div>
                <ul>
                  {combination.reasoning.map((reason: string, reasonIdx: number) => (
                    <li key={`${combination.combination_id || idx + 1}-reason-${reasonIdx}`}>{reason}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Timetable view */}
            {combination.classes && combination.classes.length > 0 && (
              renderCombinationTimetable(combination.classes, String(combination.combination_id || idx + 1))
            )}
          </div>
        ))}
      </div>
    );
  };

  // Render each part of a compound multi-intent response
  const renderCompoundParts = (parts: Message['parts']) => {
    if (!parts || parts.length === 0) return null;
    return (
      <div className="compound-parts">
        {parts.map((part, idx) => (
          <div key={idx} className="compound-part" style={{ marginTop: idx > 0 ? '16px' : '8px', paddingBottom: '16px', borderBottom: idx < parts.length - 1 ? '1px dashed #e2e8f0' : 'none' }}>
            {part.text && (
              <div 
                className="part-text"
                dangerouslySetInnerHTML={{
                  __html: formatMessageText(part.text)
                }}
                style={{ marginBottom: '8px' }}
              />
            )}
            {part.data && part.data.length > 0 && (
              <div className="part-data">
                {part.intent === 'class_registration_suggestion'
                  ? renderClassCombinations(part.data)
                  : renderDataTable(part.data)}
              </div>
            )}
            {part.data && part.data.length === 0 && (
              <div className="part-empty">Không tìm thấy dữ liệu cho phần này.</div>
            )}
            {part.sql_error && (
              <div className="part-error">⚠️ Lỗi: {part.sql_error}</div>
            )}
          </div>
        ))}
      </div>
    );
  };

  // Render data table if available (for other intents)
  const renderDataTable = (data: any[]) => {
    if (!data || data.length === 0) return null;

    const columns = Object.keys(data[0]);

    // Helper function to safely render cell content
    const renderCellContent = (value: any): string => {
      if (value === null || value === undefined) return '-';
      if (typeof value === 'object') {
        // If it's an array, join with commas
        if (Array.isArray(value)) {
          return value.map(item =>
            typeof item === 'object' ? JSON.stringify(item) : String(item)
          ).join(', ');
        }
        // If it's an object, stringify it
        return JSON.stringify(value);
      }
      return String(value);
    };

    return (
      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, idx) => (
              <tr key={idx}>
                {columns.map((col) => (
                  <td key={col}>{renderCellContent(row[col])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const buildInteractiveQuestion = (metadata?: ClassSuggestionMetadata): InteractiveQuestion | null => {
    if (!metadata) {
      return null;
    }

    const currentQuestion = metadata.conversation?.current_question;
    if (currentQuestion && currentQuestion.type) {
      return {
        key: currentQuestion.key,
        label: currentQuestion.label,
        question: currentQuestion.question,
        options: currentQuestion.options,
        type: currentQuestion.type as InteractiveQuestion['type'],
      };
    }

    if (metadata.conversation?.next_step === 'choose_subject_source') {
      return {
        key: 'subject_source',
        label: 'Nguồn học phần',
        question: 'Bạn muốn mình lấy nguồn học phần nào?',
        options: ['Học phần đã đăng ký', 'Học phần hệ thống gợi ý'],
        type: 'single_choice',
      };
    }

    return null;
  };

  const renderClassSuggestionMetadata = (
    metadata?: ClassSuggestionMetadata,
    messageId?: number,
    isLatestInteractiveMessage: boolean = false,
  ) => {
    if (!metadata) return null;

    const captured = metadata.preferences?.captured || [];
    const missing = metadata.preferences?.missing || [];
    const autoCapturedKeys = metadata.preferences?.auto_captured_keys || [];
    const progress = metadata.conversation?.progress;
    const interactiveQuestion = buildInteractiveQuestion(metadata);
    const selectedMultiOptions = messageId ? (pendingMultiOptions[messageId] || []) : [];
    const canInteract = isLatestInteractiveMessage && metadata.conversation?.next_step !== 'done';

    return (
      <div className="class-suggestion-metadata">
        <div className="metadata-banner">
          <div className="metadata-banner-title">{metadata.ui?.title || 'Mình đã ghi nhận yêu cầu của bạn'}</div>
          <div className="metadata-banner-subtitle">{metadata.ui?.subtitle || 'Mình sẽ giữ lại thông tin đã có và hỏi nốt phần còn thiếu.'}</div>
          {metadata.ui?.message && <div className="metadata-banner-message">{metadata.ui.message}</div>}
        </div>

        <div className="metadata-grid">
          <div className="metadata-panel">
            <div className="metadata-panel-title">Đã ghi nhận</div>
            <div className="metadata-chips">
              {captured.length > 0 ? captured.map((item) => (
                <span key={item.key} className="metadata-chip metadata-chip-success">
                  <strong>{item.label}:</strong>
                  <span className="metadata-chip-value">{item.value}</span>
                </span>
              )) : (
                <span className="metadata-empty">Chưa có preference nào được ghi nhận.</span>
              )}
            </div>
            {autoCapturedKeys.length > 0 && (
              <div className="metadata-hint-row">
                Tự động bắt được: {autoCapturedKeys.join(', ')}
              </div>
            )}
          </div>

          <div className="metadata-panel">
            <div className="metadata-panel-title">Còn thiếu</div>
            <div className="metadata-chips">
              {missing.length > 0 ? missing.map((item) => (
                <span key={item.key} className="metadata-chip metadata-chip-warning">
                  <strong>{item.label}:</strong>
                  <span className="metadata-chip-value">{item.hint}</span>
                </span>
              )) : (
                <span className="metadata-empty">Không còn thông tin nào cần hỏi thêm.</span>
              )}
            </div>
          </div>
        </div>

        <div className="metadata-footer">
          <div className="metadata-progress">
            <span className="metadata-progress-label">Tiến độ</span>
            <div className="metadata-progress-bar">
              <span style={{ width: `${progress?.percent ?? 0}%` }} />
            </div>
            <span className="metadata-progress-text">
              {progress?.completed ?? 0}/{progress?.total ?? 0} nhóm preference đã có
            </span>
          </div>
          {interactiveQuestion && metadata.conversation?.next_step !== 'done' && (
            <div className="metadata-next-step">
              <span className="metadata-next-label">Câu hỏi tiếp theo</span>
              <div className="metadata-next-question">{interactiveQuestion.question}</div>
            </div>
          )}
        </div>

        {canInteract && interactiveQuestion && (
          <div className="metadata-option-block">
            {interactiveQuestion.type === 'single_choice' && Array.isArray(interactiveQuestion.options) && interactiveQuestion.options.length > 0 && (
              <div className="metadata-option-grid">
                {interactiveQuestion.options.map((option) => (
                  <button
                    key={`${interactiveQuestion.key}-${option}`}
                    type="button"
                    className="metadata-option-btn"
                    onClick={() => handleSingleOptionSelect(option)}
                    disabled={isLoading}
                  >
                    {option}
                  </button>
                ))}
              </div>
            )}

            {interactiveQuestion.type === 'multi_choice' && Array.isArray(interactiveQuestion.options) && interactiveQuestion.options.length > 0 && messageId !== undefined && (
              <>
                <div className="metadata-option-grid">
                  {interactiveQuestion.options.map((option) => {
                    const isSelected = selectedMultiOptions.includes(option);
                    return (
                      <button
                        key={`${interactiveQuestion.key}-${option}`}
                        type="button"
                        className={`metadata-option-btn ${isSelected ? 'selected' : ''}`}
                        onClick={() => handleToggleMultiOption(messageId, option)}
                        disabled={isLoading}
                      >
                        {option}
                      </button>
                    );
                  })}
                </div>
                <div className="metadata-option-actions">
                  <span className="metadata-option-hint">Đã chọn: {selectedMultiOptions.length}</span>
                  <button
                    type="button"
                    className="metadata-option-confirm-btn"
                    onClick={() => handleConfirmMultiChoice(messageId, interactiveQuestion.key)}
                    disabled={isLoading || selectedMultiOptions.length === 0}
                  >
                    Xác nhận
                  </button>
                </div>
              </>
            )}

            {interactiveQuestion.type === 'free_text' && interactiveQuestion.key === 'specific' && (
              <div className="metadata-option-actions">
                <button
                  type="button"
                  className="metadata-option-btn quick-option"
                  onClick={() => handleSingleOptionSelect('không có yêu cầu')}
                  disabled={isLoading}
                >
                  Không có yêu cầu
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const latestInteractiveMessageId = [...messages]
    .reverse()
    .find((msg) => {
      if (msg.isUser || msg.intent !== 'class_registration_suggestion' || !msg.metadata) {
        return false;
      }

      const question = buildInteractiveQuestion(msg.metadata);
      return Boolean(question) && msg.metadata.conversation?.next_step !== 'done';
    })?.id;

  const handleNewConversation = async () => {
    if (isLoading) {
      return;
    }

    setActiveConversationId(null);
    setMessagesPage(1);
    setHasOlderMessages(false);
    localStorage.removeItem(activeConversationStorageKey);
    setMessages([welcomeMessage]);
    setInputValue('');
    setIsHistoryOpen(false);
  };

  const handleConversationSelect = async (conversationId: number) => {
    if (!conversationId || conversationId === activeConversationId) {
      return;
    }
    try {
      await loadConversation(conversationId);
      setIsHistoryOpen(false);
    } catch (error) {
      console.error('Error loading selected conversation:', error);
    }
  };

  const handleDeleteConversation = async (conversationId?: number) => {
    const targetConversationId = conversationId ?? activeConversationId;
    if (!userInfo?.id || !targetConversationId || isLoading) {
      return;
    }

    const confirmed = window.confirm('Bạn có chắc muốn xóa toàn bộ cuộc trò chuyện này không?');
    if (!confirmed) {
      return;
    }

    try {
      await deleteConversation(targetConversationId, userInfo.id);
      setContextMenu(null);
      await refreshConversations(targetConversationId === activeConversationId ? undefined : activeConversationId ?? undefined);
    } catch (error) {
      console.error('Error deleting conversation:', error);
    }
  };

  const handleRenameConversation = async (conversationId?: number) => {
    const targetConversationId = conversationId ?? activeConversationId;
    if (!userInfo?.id || !targetConversationId || isLoading) {
      return;
    }

    const currentConversation = conversations.find((conversation) => conversation.id === targetConversationId);
    const nextTitle = window.prompt('Nhập tên mới cho cuộc trò chuyện', currentConversation?.title || '');

    if (!nextTitle || !nextTitle.trim()) {
      return;
    }

    try {
      const updated = await renameConversation(targetConversationId, userInfo.id, nextTitle.trim());
      setConversations((prev) => prev.map((conversation) => (
        conversation.id === updated.id ? updated : conversation
      )));
      setContextMenu(null);
    } catch (error) {
      console.error('Error renaming conversation:', error);
    }
  };

  const handleConversationContextMenu = (
    event: React.MouseEvent<HTMLButtonElement>,
    conversation: ChatConversation
  ) => {
    event.preventDefault();
    setContextMenu({
      x: event.clientX,
      y: event.clientY,
      conversation,
    });
  };

  const handleLoadOlderMessages = async () => {
    if (!userInfo?.id || !activeConversationId || !hasOlderMessages || isLoadingOlder) {
      return;
    }

    setIsLoadingOlder(true);
    try {
      await loadConversation(activeConversationId, messagesPage + 1, true);
    } catch (error) {
      console.error('Error loading older messages:', error);
    } finally {
      setIsLoadingOlder(false);
    }
  };

  return (
    <div className="chatbot-container">
      <div className="chatbot-header">
        <div className="header-content">
          <div className="bot-avatar">🤖</div>
          <div className="header-info">
            <h3>Trợ lý ảo</h3>
            <span className="status">Đang hoạt động</span>
          </div>
          <div className="conversation-controls">
            <button className="conversation-btn" onClick={handleNewConversation} disabled={isLoading || isBootstrapping}>
              Cuộc trò chuyện mới
            </button>
            <button
              className="conversation-btn"
              onClick={() => setIsHistoryOpen((prev) => !prev)}
              disabled={isBootstrapping}
            >
              {isHistoryOpen ? 'Đóng lịch sử' : 'Lịch sử'}
            </button>
          </div>
        </div>
      </div>

      {isHistoryOpen && (
        <div className="conversation-panel">
          <div className="conversation-panel-header">
            <span>Lịch sử trò chuyện</span>
            <span className="conversation-panel-hint">Chuột phải hoặc bấm ⋮ để đổi tên / xóa</span>
          </div>
          <div className="conversation-list">
            {conversations.length === 0 ? (
              <div className="conversation-empty">Chưa có cuộc trò chuyện nào được lưu.</div>
            ) : (
              conversations.map((conversation) => (
                <div
                  key={conversation.id}
                  className={`conversation-item ${conversation.id === activeConversationId ? 'active' : ''}`}
                >
                  <button
                    className="conversation-item-main"
                    onClick={() => handleConversationSelect(conversation.id)}
                    onContextMenu={(event) => handleConversationContextMenu(event, conversation)}
                  >
                    <span className="conversation-item-title">{conversation.title || `Conversation #${conversation.id}`}</span>
                    <span className="conversation-item-time">{formatTime(new Date(conversation.updated_at))}</span>
                  </button>
                  <button
                    className="conversation-item-menu"
                    onClick={(event) => handleConversationContextMenu(event, conversation)}
                    title="Tùy chọn cuộc trò chuyện"
                  >
                    ⋮
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {contextMenu && (
        <div
          className="conversation-context-menu"
          style={{ top: contextMenu.y, left: contextMenu.x }}
        >
          <button onClick={() => handleRenameConversation(contextMenu.conversation.id)}>
            Đổi tên
          </button>
          <button className="danger" onClick={() => handleDeleteConversation(contextMenu.conversation.id)}>
            Xóa cuộc trò chuyện
          </button>
        </div>
      )}

      <div className="chatbot-messages">
        {hasOlderMessages && (
          <div className="messages-toolbar">
            <button
              className="load-older-btn"
              onClick={handleLoadOlderMessages}
              disabled={isLoadingOlder}
            >
              {isLoadingOlder ? 'Đang tải...' : 'Tải tin nhắn cũ hơn'}
            </button>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`message-wrapper ${message.isUser ? 'user' : 'bot'}`}
          >
            <div className="message-content">
              {!message.isUser && (
                <div className="message-avatar">  </div>
              )}
              <div className="message-bubble">
                <div
                  className="message-text"
                  dangerouslySetInnerHTML={{
                    __html: formatMessageText(message.text)
                  }}
                />
                {!message.isUser && message.intent === 'class_registration_suggestion' && renderClassSuggestionMetadata(
                  message.metadata,
                  message.id,
                  message.id === latestInteractiveMessageId,
                )}
                {message.is_compound && message.parts
                  ? renderCompoundParts(message.parts)
                  : message.data && message.data.length > 0 && (
                    message.intent === 'class_registration_suggestion'
                      ? renderClassCombinations(message.data)
                      : renderDataTable(message.data)
                  )
                }
                <span className="message-time">{formatTime(message.timestamp)}</span>
              </div>
              {!message.isUser && renderDebugSection(message, message.id, showDebug, setShowDebug)}
              {message.isUser && (
                <div className="message-avatar user-avatar">  </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message-wrapper bot">
            <div className="message-content">
              <div className="message-avatar">  </div>
              <div className="message-bubble typing">
                {streamingStatus && (
                  <div className="message-text streaming-status-text" style={{ marginBottom: '8px' }}>
                    {streamingStatus}
                  </div>
                )}
                <div className="streaming-meta">
                  <span className="streaming-stage-badge">{STREAM_STAGE_LABEL[streamingStage]}</span>
                  <span className="streaming-progress-number">{streamingProgress}%</span>
                </div>
                <div className="streaming-progress-track">
                  <span style={{ width: `${streamingProgress}%` }} />
                </div>
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <div className="typing-subtext">Bạn có thể hủy nếu muốn đổi câu hỏi.</div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chatbot-input">
        <textarea
          ref={textareaRef}
          placeholder="Nhập câu hỏi của bạn..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
          rows={1}
        />
        {isLoading ? (
          <button
            onClick={handleCancelStreaming}
            className="cancel-button"
            type="button"
          >
            Hủy
          </button>
        ) : (
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="send-button"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              width="24"
              height="24"
            >
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};

export default ChatBot;
