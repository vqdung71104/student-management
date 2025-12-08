# CLASS SUGGESTION FLOW - CHATBOT ARCHITECTURE

## 📊 Luồng Hoạt Động Tổng Quan

```
User Question
    ↓
[1] Intent Classification (TF-IDF)
    ↓
[2] Route to Appropriate Handler
    ↓
┌─────────────────────────────────────────────────┐
│ IF intent = "subject_registration_suggestion"   │
│ → process_subject_suggestion()                  │
│   → SubjectSuggestionRuleEngine                 │
│   → Return môn học nên đăng ký                  │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│ IF intent = "class_registration_suggestion"     │
│ → process_class_suggestion()                    │
│   → Extract preferences from question           │
│   → SubjectSuggestionRuleEngine (get subjects)  │
│   → ClassSuggestionRuleEngine (with prefs)      │
│   → Return lớp học với bộ lọc thông minh        │
└─────────────────────────────────────────────────┘
    ↓
[3] Format Response
    ↓
User Response
```

---

## 🎯 Intent Classification

### Intent: `subject_registration_suggestion`

**Patterns:**
- "gợi ý môn học"
- "tôi nên đăng ký môn gì"
- "kỳ này nên học môn nào"

**Handler:** `process_subject_suggestion()`

**Rule Engine:** `SubjectSuggestionRuleEngine`

**Output:**
```
🎓 GỢI Ý ĐĂNG KÝ HỌC PHẦN

📊 THÔNG TIN SINH VIÊN
• Kỳ học hiện tại: 20251
• CPA: 3.45
• Mức cảnh báo: 0

📋 GIỚI HẠN TÍN CHỈ
• Tín chỉ tối thiểu: 12 TC
• Tín chỉ tối đa: 24 TC
• Tổng tín chỉ gợi ý: 18 TC

📚 DANH SÁCH MÔN HỌC
1. IT3170 - Lập trình mạng (3 TC)
2. IT3080 - Cơ sở dữ liệu (3 TC)
...
```

---

### Intent: `class_registration_suggestion`

**Patterns:**
- "gợi ý lớp cho tôi"
- "tôi nên đăng ký lớp nào"
- "tôi không muốn học muộn" ⭐
- "các lớp kết thúc sớm" ⭐
- "tôi muốn học sáng" ⭐
- "tôi không muốn học thứ 7" ⭐

**Handler:** `process_class_suggestion()`

**Rule Engines:** 
1. `SubjectSuggestionRuleEngine` (get recommended subjects)
2. `ClassSuggestionRuleEngine` (filter classes with preferences)

**Preference Extraction:**

| User Question | Extracted Preference |
|---------------|---------------------|
| "tôi không muốn học muộn" | `avoid_late_end: True` |
| "tôi không muốn học đến 17h30" | `avoid_late_end: True` |
| "các lớp kết thúc sớm" | `avoid_late_end: True` |
| "tôi muốn học sáng" | `time_period: 'morning'` |
| "tôi muốn học chiều" | `time_period: 'afternoon'` |
| "tôi không muốn học sớm" | `avoid_early_start: True` |
| "tôi không muốn học thứ 7" | `avoid_days: ['Saturday']` |
| "tôi không muốn học thứ 2" | `avoid_days: ['Monday']` |

**Output:**
```
🏫 GỢI Ý LỚP HỌC THÔNG MINH
============================================================

📊 Thông tin sinh viên:
  • Kỳ học: 20251
  • CPA: 3.45

⚙️ Đã áp dụng bộ lọc thông minh:
  • Lớp thỏa mãn hoàn toàn: 8 lớp ✅
  • Lớp có vi phạm tiêu chí: 2 lớp ⚠️

📚 Tìm thấy 10 lớp cho 3 môn:

1. IT3170 - Lập trình mạng (3 TC)
   Có 4 lớp khả dụng:
     • 161084: Tuesday PT45000S-PT53700S - Phòng C7-113 - GV: Nguyễn Văn A (25 chỗ trống) ✅
     • 161085: Thursday PT33600S-PT42300S - Phòng D5-401 - GV: Trần Thị B (30 chỗ trống) ✅
     • 161086: Wednesday PT51000S-PT63000S - Phòng D5-401 - GV: Lê Văn C (20 chỗ trống) ⚠️
       ⚠️ Ends too late (17:30 > 17:00)

💡 Ghi chú:
   ✅ = Thỏa mãn hoàn toàn tiêu chí
   ⚠️ = Có vi phạm tiêu chí nhưng vẫn khả dụng
```

---

## 🔧 Code Structure

### File: `app/services/chatbot_service.py`

```python
class ChatbotService:
    def __init__(self, db: Session):
        self.db = db
        self.subject_rule_engine = SubjectSuggestionRuleEngine(db)
        self.class_rule_engine = ClassSuggestionRuleEngine(db)
    
    async def process_subject_suggestion():
        """
        For intent: subject_registration_suggestion
        Returns: List of recommended subjects
        """
        pass
    
    async def process_class_suggestion():
        """
        For intent: class_registration_suggestion
        
        Steps:
        1. Extract preferences from question
        2. Get recommended subjects (SubjectSuggestionRuleEngine)
        3. Get classes with filtering (ClassSuggestionRuleEngine)
        4. Format response with ✅/⚠️ badges
        """
        # Extract preferences
        preferences = self._extract_preferences_from_question(question)
        
        # Get subjects
        subject_result = self.subject_rule_engine.suggest_subjects(student_id)
        
        # Get classes with preferences
        class_result = self.class_rule_engine.suggest_classes(
            student_id=student_id,
            subject_ids=subject_ids,
            preferences=preferences,  # ⭐ Key feature
            min_suggestions=5
        )
        
        return formatted_response
    
    def _extract_preferences_from_question(question: str):
        """
        Extract preferences from natural language
        
        Keywords:
        - "không muốn học muộn", "kết thúc sớm" → avoid_late_end: True
        - "không muốn học sớm" → avoid_early_start: True
        - "muốn học sáng" → time_period: 'morning'
        - "không học thứ 7" → avoid_days: ['Saturday']
        """
        pass
```

### File: `app/rules/class_suggestion_rules.py`

```python
class ClassSuggestionRuleEngine:
    def suggest_classes(
        student_id: int,
        subject_ids: List[int],
        preferences: Dict,  # ⭐ Preferences from user question
        registered_classes: List[Dict],
        min_suggestions: int = 5
    ):
        """
        Smart class suggestions with preferences
        
        ABSOLUTE RULES (must pass):
        1. No schedule conflict
        2. One class per subject
        
        PREFERENCE RULES (can be violated):
        - time_period (morning/afternoon/evening)
        - avoid_early_start (< 08:00)
        - avoid_late_end (> 17:00)
        - avoid_days (Saturday, Sunday, etc.)
        - preferred_teachers
        
        Logic:
        - Return fully satisfied classes first (✅)
        - If < min_suggestions, add classes with fewest violations (⚠️)
        """
        # Step 1: Apply absolute rules
        filtered = filter_no_schedule_conflict(classes, registered)
        filtered = filter_one_class_per_subject(filtered, registered)
        
        # Step 2: Apply preference rules
        preference_filtered = filter_by_time_preference(filtered, preferences)
        preference_filtered = filter_by_weekday_preference(filtered, preferences)
        
        # Step 3: Rank and select
        ranked = rank_by_preferences(preference_filtered, preferences)
        
        # Step 4: Add violations if needed
        if len(ranked) < min_suggestions:
            remaining = get_with_violations(filtered)
            ranked.extend(remaining[:needed])
        
        return {
            'suggested_classes': ranked,
            'fully_satisfied': count_with_0_violations,
            'with_violations': count_with_violations
        }
```

---

## 🧪 Testing

### Test Case 1: Subject Suggestion (NO preferences)

**Question:** "gợi ý môn học kỳ này"

**Intent:** `subject_registration_suggestion`

**Expected:**
- ✅ Call `process_subject_suggestion()`
- ✅ Use `SubjectSuggestionRuleEngine`
- ✅ Return môn học theo priority rules
- ❌ NO preference extraction
- ❌ NO ClassSuggestionRuleEngine

---

### Test Case 2: Class Suggestion WITH preferences

**Question:** "tôi không muốn học đến 17h30, nên đăng ký lớp nào?"

**Intent:** `class_registration_suggestion`

**Expected:**
- ✅ Call `process_class_suggestion()`
- ✅ Extract: `{avoid_late_end: True}`
- ✅ Use `SubjectSuggestionRuleEngine` for subjects
- ✅ Use `ClassSuggestionRuleEngine` with preferences
- ✅ Filter classes ending after 17:00
- ✅ Return classes with ✅/⚠️ badges

---

### Test Case 3: Class Suggestion with multiple preferences

**Question:** "tôi muốn học sáng, không học thứ 7, gợi ý lớp nào?"

**Intent:** `class_registration_suggestion`

**Expected:**
- ✅ Extract: `{time_period: 'morning', avoid_days: ['Saturday']}`
- ✅ Filter by morning classes
- ✅ Filter out Saturday classes
- ✅ Show violations for non-matching classes

---

## 📝 Summary

| Intent | Rule Engine | Preferences? | Output |
|--------|-------------|--------------|---------|
| `subject_registration_suggestion` | SubjectSuggestionRuleEngine | ❌ No | Môn học nên đăng ký |
| `class_registration_suggestion` | SubjectSuggestionRuleEngine + ClassSuggestionRuleEngine | ✅ Yes | Lớp học với bộ lọc thông minh |

**Key Points:**
1. ✅ Preferences ONLY extracted for `class_registration_suggestion`
2. ✅ ClassSuggestionRuleEngine ONLY used for `class_registration_suggestion`
3. ✅ Both intents use SubjectSuggestionRuleEngine (to get recommended subjects)
4. ✅ Clear separation of concerns

---

**Document Version:** 1.0  
**Last Updated:** December 8, 2025  
**Status:** ✅ Implemented & Documented
