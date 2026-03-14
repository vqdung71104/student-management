/**
 * ChatBot Component - Messenger-style Chat Interface
 */
import React, { useState, useRef, useEffect } from 'react';
import {
  sendMessage,
  exportScheduleToExcel,
  listConversations,
  getConversationMessages,
  deleteConversation,
  renameConversation,
} from '../../services/chatbot.service';
import type {
  ChatResponse,
  ChatConversation,
  ChatHistoryMessage,
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
  is_compound?: boolean;
  parts?: Array<{
    intent: string;
    confidence: string;
    text: string;
    data?: any[];
    sql_error?: string | null;
    query: string;
  }>;
}

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
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

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
      data: Array.isArray(item.data_json)
        ? item.data_json
        : Array.isArray(item.data_json?.data)
          ? item.data_json.data
          : undefined,
      is_compound: Boolean(item.data_json?.is_compound),
      parts: Array.isArray(item.data_json?.parts) ? item.data_json.parts : undefined,
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

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now(),
      text: inputValue,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Send message with student_id from userInfo
      const response: ChatResponse = await sendMessage(inputValue, userInfo?.id, activeConversationId || undefined);

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
        is_compound: response.is_compound,
        parts: response.parts,
      };

      setMessages((prev) => [...prev, botMessage]);

      if (userInfo?.id) {
        try {
          const result = await listConversations(userInfo.id, 1, 30);
          setConversations(result.items);
        } catch (refreshError) {
          console.error('Error refreshing conversation list:', refreshError);
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);

      const errorMessage: Message = {
        id: Date.now() + 1,
        text: 'Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại sau.',
        isUser: false,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
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

            {/* Classes Table */}
            {combination.classes && combination.classes.length > 0 && (
              <div className="classes-table-container">
                <table className="classes-table">
                  <thead>
                    <tr>
                      <th>Mã lớp</th>
                      <th>Tên lớp</th>
                      <th>Thời gian</th>
                      <th>Ngày học</th>
                      <th>Tuần học</th>
                      <th>Phòng</th>
                      <th>Giáo viên</th>
                      <th>Ghi chú</th>
                    </tr>
                  </thead>
                  <tbody>
                    {combination.classes.map((cls: any, clsIdx: number) => {
                      // Debug: Log class data to see study_week
                      if (clsIdx === 0) {
                        console.log('Class data:', cls);
                        console.log('study_week:', cls.study_week, 'Type:', typeof cls.study_week, 'IsArray:', Array.isArray(cls.study_week));
                      }

                      return (
                        <tr key={clsIdx}>
                          <td className="class-id">{cls.class_id || '-'}</td>
                          <td className="class-name">{cls.class_name || cls.subject_name || '-'}</td>
                          <td className="class-time">
                            {cls.study_time_start && cls.study_time_end
                              ? `${cls.study_time_start} - ${cls.study_time_end}`
                              : '-'}
                          </td>
                          <td className="class-days">{cls.study_date || '-'}</td>
                          <td className="class-weeks">
                            {cls.study_week && Array.isArray(cls.study_week) && cls.study_week.length > 0
                              ? cls.study_week.join(', ')
                              : '-'}
                          </td>
                          <td className="class-room">{cls.classroom || '-'}</td>
                          <td className="class-teacher">{cls.teacher_name || '-'}</td>
                          <td className="class-note">
                            {cls.priority_reason || 'Không'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
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
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
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
      </div>
    </div>
  );
};

export default ChatBot;
