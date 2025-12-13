# Interactive Preference Collection - Implementation Summary

## Tổng quan

Đã implement hệ thống thu thập preferences tương tác cho class suggestion với khả năng:
1. ✅ Extract preferences từ câu hỏi ban đầu
2. ✅ Hỏi đa bước để thu thập preferences đầy đủ
3. ✅ Quản lý conversation state
4. ✅ Trả về 3-5 classes mỗi subject thay vì tất cả classes

## Các components đã tạo

### 1. Preference Schema (`app/schemas/preference_schema.py`)

**CompletePreference** - Bộ preference đầy đủ:
```python
preferences = {
    # Time preferences
    'time_period': 'morning' | 'afternoon',
    'avoid_time_periods': ['morning', 'afternoon'],
    'prefer_early_start': bool,
    'prefer_late_start': bool,
    'avoid_early_start': bool,
    'avoid_late_end': bool,
    
    # Day preferences
    'prefer_days': ['Monday', 'Tuesday'],
    'avoid_days': ['Saturday'],
    
    # Pattern preferences
    'prefer_continuous': bool,  # Học liên tục >5h/day
    'prefer_free_days': bool,   # Tối đa hóa ngày nghỉ
    
    # Specific requirements
    'preferred_teachers': ['Nguyễn Văn A'],
    'specific_class_ids': ['161084'],
    'specific_times': {'start': '08:00', 'end': '12:00'}
}
```

**PreferenceQuestion** - 5 CÂU HỎI (Updated Dec 12, 2025):
1. **day**: "📅 Bạn thích học vào những ngày nào trong tuần?" (multi_choice)
   - Hỗ trợ format compact: "thứ 2,3,4" hoặc "t2,3,4"
   - Hỗ trợ format đầy đủ: "Thứ 2, Thứ 3, Thứ 4"
2. **time**: "⏰ Bạn muốn học sớm hay học muộn?" (single_choice)
   - Học sớm: Ưu tiên lớp có `study_time_start` nhỏ hơn (soft filter - sort)
   - Học muộn: Ưu tiên lớp có `study_time_end` lớn hơn (soft filter - sort)
3. **continuous**: "📚 Bạn thích học liên tục nhiều lớp trong 1 buổi không?" (single_choice)
   - Úu tiên schedule có nhiều lớp liên tiếp trong cùng buổi
4. **free_days**: "🗓️ Bạn thích học ít ngày nhất có thể không?" (single_choice)
   - Tối đa hóa số ngày nghỉ trong tuần
5. **specific**: "🎯 Bạn còn yêu cầu nào cụ thể không?" (free_text)
   - Giáo viên yêu thích, mã lớp cụ thể, khoảng thời gian

### 2. Preference Service (`app/services/preference_service.py`)

**PreferenceCollectionService** - Service thu thập preferences:

Methods:
- `extract_initial_preferences(question)` - Extract từ câu hỏi đầu
- `get_next_question(preferences)` - Lấy câu hỏi tiếp theo
- `parse_user_response(response, question_key, preferences)` - Parse câu trả lời
- `format_preference_summary(preferences)` - Format summary hiển thị

Features:
- Context-aware negation detection (20-char window)
- Support multiple day formats (thứ 2, t2, Monday)
- Parse cả positive và negative preferences
- Priority order cho questions: day > time > pattern > specific

### 3. Conversation State (`app/services/conversation_state.py`)

**ConversationState** - Quản lý state của conversation:
```python
state = {
    'student_id': int,
    'session_id': str,
    'stage': 'initial' | 'collecting' | 'completed',
    'preferences': CompletePreference,
    'questions_asked': ['day', 'time'],
    'current_question': PreferenceQuestion,
    'timestamp': datetime
}
```

**ConversationStateManager** - In-memory state storage:
- `get_state(student_id)` - Lấy state
- `save_state(state)` - Lưu state
- `delete_state(student_id)` - Xóa state
- Auto-expire sau 60 phút

### 4. Updated ChatbotService (`app/services/chatbot_service.py`)

**New Flow in `process_class_suggestion()`:**

```
User: "gợi ý các lớp nên đăng ký"
  ↓
Check active conversation?
  ↓
NO → Extract initial prefs
    ↓
    Is complete?
    ↓
    NO → Ask first question
        → Save state (stage='collecting')
        
User: "Thứ 2, Thứ 5" (answering question)
  ↓
YES → Parse response
    → Update preferences
    ↓
    Is complete?
    ↓
    NO → Ask next question
        
User: "Học sớm"
  ↓
Parse response
  ↓
Is complete?
  ↓
YES → Generate suggestions
    → Return 3-5 classes PER SUBJECT
    → Clear state
```

**New Method: `_generate_class_suggestions_with_preferences()`**
- Generates suggestions with collected preferences
- Returns 3-5 classes per subject (instead of all)
- Formats response with preference summary

**New Method: `_format_class_suggestions_with_preferences()`**
- Shows collected preferences at top
- Groups classes by subject
- Shows 3-5 classes per subject max

## Conversation Examples

### Example 1: Complete preferences in initial question

```
User: "gợi ý các lớp học buổi sáng, thứ 2 và thứ 5, không học thứ 7"

Bot: [Extracts prefs]
     - time_period: morning
     - prefer_days: [Monday, Thursday]
     - avoid_days: [Saturday]
     
     [Checks] Is complete? → YES
     
     [Generates suggestions immediately]
     
     🎯 GỢI Ý LỚP HỌC THÔNG MINH
     ============================================================
     
     📊 Thông tin sinh viên:
       • Kỳ học: 20251
       • CPA: 3.30
     
     📋 Tổng hợp sở thích của bạn:
       📅 Ngày học ưu tiên: Thứ 2, Thứ 5
       📅 Ngày không muốn học: Thứ 7
       ⏰ Thời gian: Buổi sáng (7:00-12:00)
     
     📚 Tìm thấy 15 lớp từ 5 môn:
     
     1. IT3170 - Lập trình mạng (3 TC)
        Có 3 lớp phù hợp:
        ✅ 161084: Monday 09:00-11:25
           📍 Phòng D5-401 - GV: Nguyễn Văn A
           👥 30 chỗ trống / 50
        ...
```

### Example 2: Incomplete preferences - multi-turn

```
User: "gợi ý các lớp nên đăng ký kỳ sau"

Bot: [Extracts prefs] → empty
     [Checks] Is complete? → NO (missing: day, time, pattern)
     
     Để gợi ý chính xác nhất, tôi cần biết thêm về sở thích của bạn.
     
     📅 Bạn thích học vào những ngày nào trong tuần?
     (Chọn nhiều ngày, cách nhau bởi dấu phẩy)

User: "Thứ 2, Thứ 3, Thứ 5"

Bot: [Parse] → prefer_days: [Monday, Tuesday, Thursday]
     [Check] Is complete? → NO (missing: time, pattern)
     
     ⏰ Bạn muốn học sớm hay học muộn?
     1. Học sớm (7:00-12:00)
     2. Học muộn (13:00-18:00)
     3. Không quan trọng

User: "1"

Bot: [Parse] → prefer_early_start: True, time_period: morning
     [Check] Is complete? → YES
     
     [Generates suggestions with preferences]
```

### Example 3: Partial preferences extracted

```
User: "gợi ý các lớp học buổi sáng"

Bot: [Extracts] → time_period: morning
     [Check] Is complete? → NO (missing: day, pattern)
     
     Để gợi ý chính xác nhất, tôi cần biết thêm về sở thích của bạn.
     
     ✅ Tôi đã hiểu một số sở thích từ câu hỏi của bạn:
     📋 Tổng hợp sở thích của bạn:
     ⏰ Thời gian: Buổi sáng (7:00-12:00)
     
     📅 Bạn thích học vào những ngày nào trong tuần?
     ...
```

## Key Features

### 1. Smart Extraction
- ✅ Context-aware negation (20-char window)
- ✅ Multiple day formats (thứ 2, t2, Monday)
- ✅ Both positive and negative preferences
- ✅ Priority-based extraction

### 2. Flexible Flow
- ✅ Can extract all prefs from one question (if user provides)
- ✅ Can ask questions for missing prefs
- ✅ Remembers conversation state
- ✅ Auto-expires after 60 minutes

### 3. Better Results
- ✅ Returns 3-5 classes PER SUBJECT (not all classes)
- ✅ Groups by subject
- ✅ Shows preference summary
- ✅ Clear badges (✅/⚠️)

## Testing

### Test Results
```bash
$ python tests/test_interactive_preferences.py

✅ TEST 1: Extract from complex question
   - Extracted: time_period=morning, prefer_days=[Thursday], avoid_days=[Saturday]
   - Is complete: True

✅ TEST 2: Extract from simple question
   - Missing: ['day', 'time', 'pattern']
   - Next question: day preference

✅ TEST 3: Parse user responses
   - Day: "Thứ 2, Thứ 3, Thứ 5" → [Monday, Tuesday, Thursday]
   - Time: "1" → prefer_early_start=True, time_period=morning
   - Is complete: True

✅ TEST 4: Conversation flow
   - Step 1: Extract initial → Ask day question
   - Step 2: Parse day → Ask time question
   - Step 3: Parse time → Complete!
```

## Usage in Frontend

### Request to chatbot API:

**First message:**
```json
POST /api/chatbot/ask
{
  "message": "gợi ý các lớp nên đăng ký kỳ sau",
  "student_id": 1
}
```

**Response:**
```json
{
  "text": "Để gợi ý chính xác nhất...\n\n📅 Bạn thích học vào những ngày nào?",
  "intent": "class_registration_suggestion",
  "conversation_state": "collecting",
  "question_type": "multi_choice",
  "question_options": ["Thứ 2", "Thứ 3", ...]
}
```

**User responds:**
```json
POST /api/chatbot/ask
{
  "message": "Thứ 2, Thứ 5",
  "student_id": 1
}
```

**Response:**
```json
{
  "text": "⏰ Bạn muốn học sớm hay muộn?\n1. Học sớm...",
  "intent": "class_registration_suggestion",
  "conversation_state": "collecting",
  "question_type": "single_choice",
  "question_options": ["Học sớm", "Học muộn", "Không quan trọng"]
}
```

**After complete:**
```json
{
  "text": "🎯 GỢI Ý LỚP HỌC...\n\n📋 Tổng hợp sở thích...\n\n📚 Tìm thấy 15 lớp...",
  "intent": "class_registration_suggestion",
  "conversation_state": "completed",
  "data": [...classes...],
  "metadata": {
    "total_subjects": 5,
    "total_classes": 15,
    "preferences_applied": {...}
  }
}
```

## Completed Phases

### ✅ Phase 1: Interactive Preference Collection (Dec 12, 2025)
- [x] Extract preferences from initial question
- [x] Multi-turn conversation with 5 questions
- [x] Conversation state management
- [x] Parse user responses (multi-format support)

### ✅ Phase 2: Schedule Combinations (Dec 12, 2025)
- [x] Generate valid schedule combinations (no conflicts)
- [x] Score combinations by preferences
- [x] Return top 3 combinations
- [x] Show combination comparisons

### ✅ Critical Fixes (Dec 13, 2025)
- [x] **Conflict detection bug fixed** - Now checks 3 conditions: week + day + time
- [x] **Data structure fix** - study_week stored as LIST instead of string
- [x] **Time parsing fix** - Handle timedelta from database
- [x] **Efficient search** - Check up to 1000 combinations (lazy evaluation)
- [x] **Test coverage** - 17 comprehensive test cases (all passing)

### Improvements
- [x] Add conversation state before intent classification
- [x] Add efficient combination generation (10x search space)
- [ ] Add Redis integration for production (currently in-memory)
- [ ] Add more sophisticated NLP for parsing
- [ ] Support more preference types
- [ ] Add preference weights/priorities

## Files Created/Modified

### Created:
1. `app/schemas/preference_schema.py` - Preference models (5 questions)
2. `app/services/preference_service.py` - Preference collection logic
3. `app/services/conversation_state.py` - State management
4. `app/services/schedule_combination_service.py` - Combination generation & scoring
5. `tests/test_interactive_preferences.py` - Preference parsing tests
6. `tests/test_time_conflict_detection.py` - **Conflict detection tests (17 cases)**
7. `docs/INTERACTIVE_CLASS_SUGGESTION_DESIGN.md` - Design doc
8. `docs/CHATBOT_CLASS_SUGGESTION_COMPLETE.md` - Complete flow documentation

### Modified:
1. `app/services/chatbot_service.py` - Multi-turn conversation + combination generation
2. `app/rules/class_suggestion_rules.py` - **study_week as LIST, conflict detection fixed**
3. `app/routes/chatbot_routes.py` - **Check conversation state before intent classification**
4. `frontend/src/components/ChatBot/ChatBot.tsx` - Beautiful combination display
5. `frontend/src/components/ChatBot/ChatBot.css` - Card & table styling

### Key Bug Fixes (Dec 13, 2025):
1. **Conflict Detection:** Added study_week check (3 conditions: week + day + time)
2. **Data Structure:** Changed study_week from string `"1,2,3"` to list `[1,2,3]`
3. **Time Parsing:** Added timedelta support in `_parse_time()`
4. **Search Efficiency:** Check 1000 combinations instead of 100 (lazy evaluation)
5. **Intent Classification:** Check conversation state BEFORE running classifier

---

**Version:** 2.0  
**Implemented:** December 12-13, 2025  
**Status:** ✅ Phase 1 & 2 Complete + Critical Fixes Applied
**Test Coverage:** 17 test cases (100% passing)
**Next:** Production deployment with Redis
