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
│   → Extract subject keyword (if mentioned) 🎯   │
│   → SubjectSuggestionRuleEngine (get subjects)  │
│   → Match & filter by subject (if extracted) 🎯 │
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
- **"tôi muốn học vào thứ 5"** ⭐ NEW
- **"gợi ý lớp tiếng nhật"** 🎯 NEW
- **"lớp SSH1131 nào"** 🎯 NEW

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
| **"tôi không muốn học buổi sáng"** ⭐ | `avoid_time_periods: ['morning']` |
| **"không muốn học buổi chiều"** ⭐ | `avoid_time_periods: ['afternoon']` |
| **"tránh học buổi tối"** ⭐ | `avoid_time_periods: ['evening']` |
| "tôi không muốn học sớm" | `avoid_early_start: True` |
| "tôi không muốn học thứ 7" | `avoid_days: ['Saturday']` |
| "tôi không muốn học thứ 2" | `avoid_days: ['Monday']` |
| **"tôi muốn học vào thứ 5"** ⭐ | `prefer_days: ['Thursday']` |
| **"học vào thứ 3 và thứ 5"** ⭐ | `prefer_days: ['Tuesday', 'Thursday']` |
| **"gợi ý lớp tiếng nhật"** 🎯 | Extract subject: `'JP'` → match `JP2126` |
| **"lớp SSH1131 nào"** 🎯 | Extract subject: `'SSH1131'` |

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
        3. Extract specific subject from question (if mentioned) ⭐ NEW
        4. Get classes with filtering (ClassSuggestionRuleEngine)
        5. Format response with ✅/⚠️ badges
        """
        # Extract preferences
        preferences = self._extract_preferences_from_question(question)
        
        # Get subjects
        subject_result = self.subject_rule_engine.suggest_subjects(student_id)
        suggested_subjects = subject_result['suggested_subjects']
        
        # Extract specific subject (NEW) ⭐
        if not subject_id:
            subject_keyword = self._extract_subject_from_question(question)
            if subject_keyword:
                # Match keyword with suggested_subjects
                for subj in suggested_subjects:
                    if subj['subject_id'].startswith(subject_keyword) or \
                       subject_keyword.lower() in subj['subject_name'].lower():
                        subject_id = subj['subject_id']
                        break
        
        # Filter by subject_id if found
        if subject_id:
            suggested_subjects = [s for s in suggested_subjects 
                                 if s['subject_id'] == subject_id]
        
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
        
        Context-Aware Negation Detection (20-char window):
        - Checks negation words ('không', 'tránh', 'ko', etc.) within 20 characters BEFORE keyword
        - Prevents false negatives from global negation check
        - Example: "không muốn học buổi sáng, học thứ 5" correctly extracts both
        
        Keywords:
        - "không muốn học muộn", "kết thúc sớm" → avoid_late_end: True
        - "không muốn học sớm" → avoid_early_start: True
        - "muốn học sáng" → time_period: 'morning' (positive)
        - "không muốn học buổi sáng" → avoid_time_periods: ['morning'] (negative) ⭐
        - "không học thứ 7" → avoid_days: ['Saturday'] (negative)
        - "muốn học vào thứ 5" → prefer_days: ['Thursday'] (positive) ⭐
        
        Filter Priority: Negative preferences (avoid_*) applied BEFORE positive preferences
        """
        pass
    
    def _extract_subject_from_question(question: str):
        """
        Extract specific subject from natural language ⭐ NEW
        
        Keywords:
        - "tiếng nhật" → 'JP'
        - "tiếng anh" → 'ENG'
        - "lập trình mạng" → 'IT3170'
        - "SSH1131" → 'SSH1131' (exact code)
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
        - time_period (morning/afternoon/evening) - POSITIVE preference
        - avoid_time_periods (['morning'], ['afternoon'], etc.) - NEGATIVE preference ⭐
        - avoid_early_start (< 08:00)
        - avoid_late_end (> 17:00)
        - avoid_days (Saturday, Sunday, etc.) - NEGATIVE preference
        - prefer_days (Monday, Tuesday, etc.) - POSITIVE preference ⭐
        - preferred_teachers
        
        Filter Priority:
        1. Negative filters applied FIRST (avoid_time_periods, avoid_days)
        2. Then positive filters (time_period, prefer_days)
        3. Return fully satisfied classes first (✅)
        4. If < min_suggestions, add classes with fewest violations (⚠️)
        """
        # Step 1: Apply absolute rules
        filtered = filter_no_schedule_conflict(classes, registered)
        filtered = filter_one_class_per_subject(filtered, registered)
        
        # Step 2: Apply preference rules
        preference_filtered = filter_by_time_preference(filtered, preferences)
        # Note: filter_by_time_preference checks:
        #   - avoid_time_periods: filter OUT classes with avoided periods (FIRST)
        #   - time_period: keep ONLY classes with this period (SECOND)
        
        preference_filtered = filter_by_weekday_preference(filtered, preferences)
        # Note: filter_by_weekday_preference handles:
        #   - avoid_days: filter OUT classes with these days (FIRST)
        #   - prefer_days: keep ONLY classes with at least one of these days (SECOND) ⭐
        
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

## 🔍 Detailed Logic: `prefer_days` vs `avoid_days`

### Understanding Day Preferences

| Type | Purpose | Example | Filter Logic |
|------|---------|---------|--------------|
| `avoid_days` | **NEGATIVE** - Days to avoid | "không học thứ 7" | Filter OUT classes with ANY avoided day |
| `prefer_days` | **POSITIVE** - Days to prefer | "muốn học vào thứ 5" | Keep ONLY classes with AT LEAST ONE preferred day |

### Example Scenarios

#### Scenario 1: `avoid_days: ['Saturday']`
```python
Class A: "Monday,Wednesday"        → ✅ Keep (no Saturday)
Class B: "Saturday"                → ❌ Filter out (has Saturday)
Class C: "Friday,Saturday"         → ❌ Filter out (has Saturday)
```

#### Scenario 2: `prefer_days: ['Thursday']`
```python
Class A: "Monday,Wednesday"        → ❌ Filter out (no Thursday)
Class B: "Thursday"                → ✅ Keep (has Thursday)
Class C: "Tuesday,Thursday"        → ✅ Keep (has Thursday)
Class D: "Thursday,Friday"         → ✅ Keep (has Thursday)
```

#### Scenario 3: Both `prefer_days: ['Thursday']` AND `avoid_days: ['Saturday']`
```python
Class A: "Monday,Wednesday"        → ❌ Filter out (no Thursday)
Class B: "Thursday"                → ✅ Keep (has Thursday, no Saturday)
Class C: "Thursday,Saturday"       → ❌ Filter out (has Saturday)
Class D: "Tuesday,Thursday"        → ✅ Keep (has Thursday, no Saturday)
```

### Code Implementation

```python
# In filter_by_weekday_preference():

for cls in classes:
    study_days = parse_study_days(cls['study_date'])
    
    # Step 1: Check avoid_days (negative filter)
    if avoid_days and any(day in avoid_days for day in study_days):
        continue  # Skip this class
    
    # Step 2: Check prefer_days (positive filter)
    # IMPORTANT: Use 'any' not 'all'
    if prefer_days and not any(day in prefer_days for day in study_days):
        continue  # Skip this class
    
    filtered.append(cls)
```

**Key Insight**: `any()` ensures we keep classes with **at least one** preferred day, not requiring ALL days to be preferred.

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

### Test Case 3.1: Negative time period preference ⭐ NEW

**Question:** "tôi không muốn học buổi chiều, không muốn học thứ 5, môn Tư tưởng Hồ chí minh"

**Intent:** `class_registration_suggestion`

**Expected:**
- ✅ Extract: `{avoid_time_periods: ['afternoon'], avoid_days: ['Thursday']}`, subject: 'SSH1131'
- ✅ Filter OUT afternoon classes (negative filter FIRST)
- ✅ Filter OUT Thursday classes (negative filter FIRST)
- ✅ Result: ONLY morning/evening classes on Mon/Tue/Wed/Fri/Sat/Sun
- ❌ NO afternoon classes should appear
- ❌ NO Thursday classes should appear

**Key Implementation:**
```python
# In filter_by_time_preference():
if avoid_time_periods and class_period in avoid_time_periods:
    continue  # Skip this class (active exclusion)
```

---

### Test Case 4: Prefer specific days ⭐ NEW

**Question:** "tôi muốn học vào thứ 5, tôi nên đăng ký lớp nào?"

**Intent:** `class_registration_suggestion`

**Expected:**
- ✅ Extract: `{prefer_days: ['Thursday']}`
- ✅ Keep classes with **at least one day** = Thursday
  - Class "Monday,Thursday" → ✅ Keep (has Thursday)
  - Class "Tuesday,Wednesday" → ❌ Filter out (no Thursday)
- ✅ Return only classes on Thursday
- ✅ Show badges for fully satisfied classes

**Important Logic:**
```python
# CORRECT (implemented):
if prefer_days and not any(day in prefer_days for day in study_days):
    continue  # Filter out if NO study day matches prefer_days

# WRONG (previous bug):
if prefer_days and not all(day in prefer_days for day in study_days):
    continue  # Would filter out "Monday,Thursday" class
```

---

### Test Case 5: Specific subject filtering 🎯 NEW

**Question:** "gợi ý lớp tiếng nhật vào thứ 5"

**Intent:** `class_registration_suggestion`

**Expected:**
- ✅ Extract: `{prefer_days: ['Thursday']}`, subject_keyword: `'JP'` or `'tiếng nhật'`
- ✅ Match subject: Find `JP2126` in suggested_subjects
- ✅ Filter: Only show classes of JP2126
- ✅ Filter: Only show classes on Thursday
- ✅ Result: **ONLY** JP2126 classes on Thursday (not SSH or other subjects)

---

### Test Case 6: Exact subject code

**Question:** "lớp SSH1131 nào học vào sáng?"

**Intent:** `class_registration_suggestion`

**Expected:**
- ✅ Extract: `{time_period: 'morning'}`, subject_id: `'SSH1131'`
- ✅ Filter: Only show classes of SSH1131
- ✅ Filter: Only morning classes (before 12:00)
- ✅ Result: SSH1131 morning classes only

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
5. ✅ **NEW**: `prefer_days` supports positive day preferences (vs `avoid_days` for negative)
6. ✅ **NEW**: Subject extraction from natural language (e.g., "tiếng nhật" → JP2126)
7. ✅ **NEW**: Handles both exact subject codes (SSH1131) and keywords (tiếng nhật)

---

## 🆕 Recent Updates (December 8, 2025)

### 1. Fixed `prefer_days` Logic
- **Bug**: Used `all()` instead of `any()` → filtered out classes incorrectly
- **Fix**: Changed to `any()` → keep classes with at least one preferred day
- **File**: `app/rules/class_suggestion_rules.py` line ~438

### 2. Added `prefer_days` Extraction
- **Feature**: Extract positive day preferences from questions
- **Examples**: "muốn học vào thứ 5" → `prefer_days: ['Thursday']`
- **File**: `app/services/chatbot_service.py` method `_extract_preferences_from_question()`

### 3. Added Subject Extraction
- **Feature**: Extract specific subject from question
- **Examples**: 
  - "gợi ý lớp tiếng nhật" → match JP2126
  - "lớp SSH1131" → exact match
- **File**: `app/services/chatbot_service.py` method `_extract_subject_from_question()`

### 4. Added New Intent Patterns
- **File**: `backend/data/intents.json`
- **New patterns**:
  - "tôi muốn học vào thứ 5"
  - "gợi ý lớp tiếng nhật"
  - "lớp SSH1131 nào"
  - etc. (9 new patterns total)

### 5. Context-Aware Negation Detection ⭐ CRITICAL
- **Problem**: Global negation check caused false negatives
  - "không muốn học buổi sáng, học thứ 5" → lost "thứ 5" because "không" exists
- **Solution**: Check negation within 20-character window BEFORE keyword
- **File**: `app/services/chatbot_service.py` → `has_negation_before()` helper
- **Impact**: Fixed extraction for complex sentences with multiple preferences

### 6. Active Negative Filtering with `avoid_time_periods` ⭐ NEW
- **Feature**: Separate negative time preferences from positive ones
- **Implementation**:
  - Added `avoid_time_periods` field (list of periods to exclude)
  - "không muốn học buổi sáng" → `avoid_time_periods: ['morning']`
  - Filter OUT morning classes (active exclusion, not passive ignore)
- **Files**: 
  - `app/services/chatbot_service.py` → extraction logic
  - `app/rules/class_suggestion_rules.py` → filtering logic (line 363-410)
- **Filter Priority**: Negative filters (avoid_*) applied BEFORE positive filters

### 7. Fixed `avoid_time_periods` Not Applied ⭐ BUG FIX
- **Bug**: Condition `if 'time_period' in preferences` didn't check `avoid_time_periods`
  - Result: Even with `avoid_time_periods: ['afternoon']`, afternoon classes still shown
- **Fix**: Added `or 'avoid_time_periods' in preferences` to condition
- **File**: `app/rules/class_suggestion_rules.py` line ~844
- **Impact**: Now correctly filters out avoided time periods

### 8. Enhanced Violation Tracking
- **Feature**: Count violations for both positive and negative preferences
- **Implementation**: Added violation counting for `avoid_time_periods`
- **File**: `app/rules/class_suggestion_rules.py` → `count_preference_violations()`

### 9. Comprehensive Test Suite
- **File**: `tests/test_preference_extraction.py` (NEW)
- **Coverage**: 16 test cases covering:
  - Simple preferences (positive/negative)
  - Complex sentences with multiple preferences
  - Context-aware negation detection
  - Avoid patterns (time periods, weekdays)
- **Status**: All 16 tests passing ✅

---

**Document Version:** 2.1  
**Last Updated:** December 8, 2025  
**Status:** ✅ Implemented & Documented & Updated & Bug Fixed
