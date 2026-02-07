/**
 * ChatBot Component - Messenger-style Chat Interface
 */
import React, { useState, useRef, useEffect } from 'react';
import { sendMessage, exportScheduleToExcel } from '../../services/chatbot.service';
import type { ChatResponse } from '../../services/chatbot.service';
import { useAuth } from '../../contexts/AuthContext';
import './ChatBot.css';

interface Message {
  id: number;
  text: string;
  isUser: boolean;
  timestamp: Date;
  intent?: string;
  data?: any[];
}

const ChatBot: React.FC = () => {
  const { userInfo } = useAuth();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 0,
      text: 'Xin chào! Mình là trợ lý ảo của hệ thống quản lý sinh viên. Mình có thể giúp gì cho bạn?',
      isUser: false,
      timestamp: new Date(),
    },
  ]);
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
      const response: ChatResponse = await sendMessage(inputValue, userInfo?.id);

      const botMessage: Message = {
        id: Date.now() + 1,
        text: response.text,
        isUser: false,
        timestamp: new Date(),
        intent: response.intent,
        data: response.data,
      };

      setMessages((prev) => [...prev, botMessage]);
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

  return (
    <div className="chatbot-container">
      <div className="chatbot-header">
        <div className="header-content">
          <div className="bot-avatar">🤖</div>
          <div className="header-info">
            <h3>Trợ lý ảo</h3>
            <span className="status">Đang hoạt động</span>
          </div>
        </div>
      </div>

      <div className="chatbot-messages">
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
                {message.data && message.data.length > 0 && (
                  message.intent === 'class_registration_suggestion'
                    ? renderClassCombinations(message.data)
                    : renderDataTable(message.data)
                )}
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
