-- Chat history tables for chatbot persistence
-- Ownership key uses students.id (INT) as student_pk

CREATE TABLE IF NOT EXISTS chat_conversations (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  student_pk INT NOT NULL,
  title VARCHAR(255) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_chat_conv_student_updated (student_pk, updated_at),
  INDEX idx_chat_conv_updated (updated_at),
  CONSTRAINT fk_chat_conv_student
    FOREIGN KEY (student_pk) REFERENCES students(id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS chat_messages (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  conversation_id BIGINT NOT NULL,
  role ENUM('user', 'assistant', 'system') NOT NULL,
  content TEXT NOT NULL,
  intent VARCHAR(64) NULL,
  confidence VARCHAR(16) NULL,
  data_json JSON NULL,
  sql_text TEXT NULL,
  sql_error TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_chat_msg_conv_created (conversation_id, created_at),
  CONSTRAINT fk_chat_msg_conversation
    FOREIGN KEY (conversation_id) REFERENCES chat_conversations(id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
