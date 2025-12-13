# 🤖 Rule Engine Integration Guide

## 📋 Tổng quan

Tài liệu này mô tả cách Rule Engine được tích hợp vào hệ thống chatbot để cung cấp các gợi ý thông minh về đăng ký học phần và lớp học.

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────┐
│                     CHATBOT ROUTES                          │
│                  (chatbot_routes.py)                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ↓
        ┌───────────────────────────────────┐
        │   Intent Classification           │
        │   (TfidfIntentClassifier)         │
        └───────────────────────────────────┘
                        │
           ┌────────────┴────────────┐
           │                         │
           ↓                         ↓
┌──────────────────────┐   ┌──────────────────────┐
│   Rule Engine        │   │   NL2SQL Service     │
│   Intents:           │   │   Intents:           │
│   - subject_reg_sug  │   │   - grade_view       │
│   - class_reg_sug    │   │   - subject_info     │
└──────────────────────┘   │   - class_info       │
           │               │   - schedule_view     │
           ↓               └──────────────────────┘
┌──────────────────────┐
│  ChatbotService      │
│  - Subject Suggest   │
│  - Class Suggest     │
└──────────────────────┘
           │
           ↓
┌──────────────────────┐
│ SubjectSuggestion    │
│ RuleEngine           │
│ - 7 Priority Rules   │
│ - Config from JSON   │
└──────────────────────┘
```

## 📁 Cấu trúc file

```
backend/
├── app/
│   ├── rules/
│   │   ├── __init__.py
│   │   ├── rules_config.json          ← Configuration file
│   │   ├── subject_suggestion_rules.py ← Rule Engine
│   │   └── README.md
│   ├── services/
│   │   ├── chatbot_service.py         ← Service layer (NEW)
│   │   └── nl2sql_service.py
│   ├── routes/
│   │   └── chatbot_routes.py          ← Updated with Rule Engine
│   └── tests/
│       ├── test_rule_engine.py
│       └── test_rule_engine_integration.py ← Integration test (NEW)
└── docs/
    └── RULE_ENGINE_INTEGRATION.md     ← This file
```

## 🔧 Các thành phần chính

### 1. **rules_config.json** - Configuration File

Chứa tất cả các cấu hình cho Rule Engine:

```json
{
  "credit_limits": {
    "min_credits": 8,
    "max_credits_normal": 28,
    "max_credits_warning": 18,
    "improvement_threshold": 20
  },
  "subject_categories": {
    "political_subjects": ["SSH1111", ...],
    "physical_education_subjects": ["PE2102", ...],
    "supplementary_subjects": ["CH2021", ...]
  },
  "requirements": {
    "political_required": 6,
    "pe_required": 4,
    "supplementary_required": 3
  },
  "grade_thresholds": {
    "fast_track_cpa": 3.4,
    "improvement_grades": ["D", "D+", "C"]
  }
}
```

**Lợi ích:**
- ✅ Dễ thay đổi cấu hình mà không cần sửa code
- ✅ Version control cho business rules
- ✅ Tách biệt configuration và logic

### 2. **ChatbotService** - Service Layer

File: `app/services/chatbot_service.py`

**Responsibilities:**
- Xử lý business logic cho chatbot
- Tích hợp Rule Engine
- Format responses

**Key Methods:**

```python
class ChatbotService:
    async def process_subject_suggestion(student_id, question, max_credits):
        """Process subject registration suggestions using Rule Engine"""
        
    async def process_class_suggestion(student_id, question, subject_id):
        """Process class registration suggestions"""
```

### 3. **Updated ChatbotRoutes** - API Layer

File: `app/routes/chatbot_routes.py`

**Thay đổi chính:**

```python
# OLD: All intents use NL2SQL
if intent in data_intents and confidence in ["high", "medium"]:
    sql_result = await nl2sql_service.generate_sql(...)

# NEW: Rule Engine intents use ChatbotService
rule_engine_intents = ["subject_registration_suggestion", "class_registration_suggestion"]

if intent in rule_engine_intents:
    result = await chatbot_service.process_subject_suggestion(...)
    return result

# Other intents still use NL2SQL
nl2sql_intents = ["grade_view", "learned_subjects_view", ...]
if intent in nl2sql_intents:
    sql_result = await nl2sql_service.generate_sql(...)
```

## 🔄 Luồng xử lý

### **Subject Registration Suggestion Flow**

```
User: "tôi nên đăng ký môn gì?"
   ↓
[Intent Classification]
   → Intent: subject_registration_suggestion
   → Confidence: high
   ↓
[Check Intent Type]
   → Is rule_engine_intent? YES
   ↓
[ChatbotService.process_subject_suggestion]
   ↓
[SubjectSuggestionRuleEngine.suggest_subjects]
   │
   ├─ Get student data (CPA, grades, completed subjects)
   ├─ Get current semester (20251)
   ├─ Calculate student semester number (5)
   ├─ Get available subjects from course
   │
   ├─ Apply Rule 1: Failed subjects (F) → 1 subject
   ├─ Apply Rule 2: Semester match → 2 subjects
   ├─ Apply Rule 3: Political subjects → 1 subject
   ├─ Apply Rule 4: Physical education → 2 subjects
   ├─ Apply Rule 5: Supplementary → 0 subjects
   ├─ Apply Rule 6: Fast track (CPA > 3.4) → 3 subjects
   └─ Apply Rule 7: Grade improvement → 0 subjects
   │
   ↓ Total: 9 subjects, 22 credits
   ↓
[Format Response]
   ↓
[Return to User]
   → Text: "📚 GỢI Ý ĐĂNG KÝ HỌC PHẦN..."
   → Data: List of 9 subjects with priorities
   → Metadata: Credits, CPA, semester info
```

### **Class Registration Suggestion Flow**

```
User: "gợi ý lớp học cho tôi"
   ↓
[Intent Classification]
   → Intent: class_registration_suggestion
   ↓
[ChatbotService.process_class_suggestion]
   │
   ├─ Get subject suggestions from Rule Engine
   ├─ Take top 5 subjects
   │
   ├─ For each subject:
   │   ├─ Query available classes
   │   ├─ Filter: registered < max_students
   │   └─ Include: time, teacher, room, seats
   │
   ↓
[Format Class List]
   │
   ├─ Group by subject
   ├─ Show max 3 classes per subject
   └─ Include priority reason
   ↓
[Return to User]
   → Text: "🏫 GỢI Ý LỚP HỌC..."
   → Data: List of classes with details
```

## 📊 So sánh TRƯỚC vs SAU

### **TRƯỚC: Chỉ NL2SQL**

```json
// Request
POST /chatbot/chat
{
  "message": "tôi nên đăng ký môn gì?",
  "student_id": 1
}

// Response
{
  "text": "Gợi ý các học phần nên đăng ký (tìm thấy 45 học phần):",
  "intent": "subject_registration_suggestion",
  "confidence": "high",
  "data": [
    {"subject_id": "IT4040", "subject_name": "Lập trình mạng", "credits": 3},
    {"subject_id": "MI1114", "subject_name": "Giải tích 1", "credits": 4},
    // ... 43 subjects more (NO PRIORITY)
  ],
  "sql": "SELECT * FROM subjects WHERE ..."
}
```

❌ **Vấn đề:**
- Không có thứ tự ưu tiên
- Không kiểm tra điều kiện (TC min/max, CPA, warning level)
- Chỉ là danh sách thô từ database

### **SAU: Rule Engine**

```json
// Request (same)
POST /chatbot/chat
{
  "message": "tôi nên đăng ký môn gì?",
  "student_id": 1
}

// Response (with Rule Engine)
{
  "text": "📚 GỢI Ý ĐĂNG KÝ HỌC PHẦN\n...",
  "intent": "subject_registration_suggestion",
  "confidence": "high",
  "data": [
    {
      "subject_id": "IT3080",
      "subject_name": "Cơ sở dữ liệu",
      "credits": 3,
      "priority_level": 1,
      "priority_reason": "Failed subject (F) - Must retake"
    },
    {
      "subject_id": "IT4040",
      "subject_name": "Lập trình mạng",
      "credits": 3,
      "priority_level": 2,
      "priority_reason": "Matches semester 5"
    },
    // ... 7 more subjects (PRIORITIZED)
  ],
  "summary": {
    "failed_retake": 1,
    "semester_match": 2,
    "political": 1,
    "physical_education": 2,
    "total_credits": 22
  },
  "metadata": {
    "meets_minimum": true,
    "max_credits_allowed": 28,
    "student_cpa": 3.45
  },
  "rule_engine_used": true
}
```

✅ **Cải thiện:**
- Có 7 mức độ ưu tiên rõ ràng
- Kiểm tra đầy đủ điều kiện
- Chỉ gợi ý 8-12 môn quan trọng
- Response có cấu trúc và hữu ích

## 🧪 Testing

### **Run Integration Tests**

```bash
# Test rule engine integration
cd backend
python app/tests/test_rule_engine_integration.py
```

**Expected Output:**

```
================================================================================
🧪 TESTING RULE ENGINE INTEGRATION
================================================================================
✅ Database connection established
✅ ChatbotService initialized
✅ Rule engine loaded with config

================================================================================
📝 TEST 1: Subject Suggestion for Student ID = 1
================================================================================

📊 RESULT:
Intent: subject_registration_suggestion
Confidence: high
Rule Engine Used: True

📈 METADATA:
  Total Credits: 22
  Meets Minimum: True
  Max Allowed: 28
  Current Semester: 20251
  Student CPA: 3.45

📚 SUGGESTED SUBJECTS: 9 subjects
  1. IT3080 - Cơ sở dữ liệu
     Priority: 1 - Failed subject (F) - Must retake
  2. IT4040 - Lập trình mạng
     Priority: 2 - Matches semester 5
  ...

✅ TEST 1 PASSED
```

### **Test via API**

```bash
# Start backend server
cd backend
python main.py

# Test with curl
curl -X POST http://localhost:8000/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "tôi nên đăng ký môn gì?",
    "student_id": 1
  }'
```

## 🎯 Use Cases

### **Use Case 1: Sinh viên có môn F**

```
Input: "tôi nên đăng ký môn gì?"
Student: CPA 2.5, 2 môn F

Output:
🔴 PRIORITY 1: Học lại môn điểm F (2 môn)
  • IT3080 - Cơ sở dữ liệu (3 TC) ← PHẢI HỌC LẠI
  • MI1114 - Giải tích 1 (4 TC) ← PHẢI HỌC LẠI

Tổng: 7 TC (cần thêm 1 TC để đủ 8 TC minimum)
```

### **Use Case 2: Sinh viên CPA cao**

```
Input: "tôi nên đăng ký môn gì?"
Student: CPA 3.6, không có môn F

Output:
⚡ PRIORITY 6: Học nhanh (CPA 3.6 > 3.4)
  • IT4788 - Trí tuệ nhân tạo (3 TC)
  • IT5140 - Học máy (3 TC)
  • IT4895 - Blockchain (3 TC)

Tổng: 28 TC (đạt max) - Học nhanh tốt nghiệp sớm!
```

### **Use Case 3: Sinh viên bị cảnh báo**

```
Input: "tôi nên đăng ký môn gì?"
Student: CPA 1.8, warning_level 2

Output:
⚠️ Lưu ý: Bạn đang bị cảnh báo học vụ mức 2
Chỉ được đăng ký tối đa 18 TC/kỳ

Gợi ý tập trung các môn dễ để cải thiện CPA
Tổng: 17 TC (đủ điều kiện)
```

## 🔧 Maintenance

### **Cập nhật cấu hình**

Chỉnh sửa file `rules_config.json`:

```json
{
  "credit_limits": {
    "min_credits": 10,  // Thay đổi từ 8 → 10
    "max_credits_normal": 30  // Thay đổi từ 28 → 30
  }
}
```

**Không cần restart server** - Config được load khi khởi tạo Rule Engine.

### **Thêm môn học mới**

```json
{
  "subject_categories": {
    "political_subjects": [
      "SSH1111", "SSH1121", "SSH1131", 
      "SSH1141", "SSH1151", "EM1170",
      "SSH1161"  // ← Thêm môn mới
    ]
  }
}
```

### **Thay đổi ngưỡng CPA**

```json
{
  "grade_thresholds": {
    "fast_track_cpa": 3.2,  // Giảm từ 3.4 → 3.2
    "improvement_grades": ["D", "D+", "C", "C+"]  // Thêm C+
  }
}
```

## 🚀 Future Enhancements

### **1. Thêm rule mới**

File: `subject_suggestion_rules.py`

```python
def rule_8_filter_prerequisite_check(self, subjects, student_data):
    """RULE 8: Check prerequisites before suggesting"""
    # Implementation...
    pass
```

### **2. Personalization**

```json
{
  "personalization": {
    "learning_style": "fast/normal/slow",
    "preferred_study_time": "morning/afternoon"
  }
}
```

### **3. Machine Learning Integration**

```python
def rule_9_ml_recommendation(self, subjects, student_data):
    """Use ML model to predict success rate for each subject"""
    # Call ML model API
    pass
```

## 📚 References

- [Rule Engine Implementation](../app/rules/subject_suggestion_rules.py)
- [Chatbot Service](../app/services/chatbot_service.py)
- [Configuration File](../app/rules/rules_config.json)
- [Integration Tests](../app/tests/test_rule_engine_integration.py)

## 🤝 Contributing

Khi thêm rule mới hoặc cập nhật logic:

1. ✅ Cập nhật `rules_config.json` nếu cần
2. ✅ Implement rule trong `subject_suggestion_rules.py`
3. ✅ Thêm test case trong `test_rule_engine.py`
4. ✅ Cập nhật documentation
5. ✅ Run integration tests

---

**Last Updated:** November 25, 2025  
**Version:** 1.0.0
