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
        - time_period (morning/afternoon) - POSITIVE preference
        - avoid_time_periods (['morning'], ['afternoon'], etc.) - NEGATIVE preference ⭐
        - avoid_early_start (< 08:25)
        - avoid_late_end (> 16:00)
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
- ✅ Result: ONLY morning classes on Mon/Tue/Wed/Fri/Sat
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

## 🆕 Major Updates (December 13, 2025)

### 10. **4-State Preference System** ⭐ CRITICAL ARCHITECTURE CHANGE

**Previous (2 states):**
- Active: Has preference (prefer_days, prefer_early_start)
- None: No information

**Current (4 states):**
1. **active**: User has clear preference → Apply positive filter
   - Example: "muốn học sớm" → `prefer_early_start=True`
2. **passive**: User wants to avoid → Apply negative filter
   - Example: "không muốn học muộn" → `avoid_late_end=True`
3. **none**: No information yet → **Must ask question**
4. **not_important**: User said "Không quan trọng" → **Skip filter/sort**
   - Example: "3. không quan trọng" → `is_not_important=True`

**Implementation:**
```python
# preference_schema.py
class TimePreference(BaseModel):
    prefer_early_start: bool = False     # active
    prefer_late_start: bool = False      # active
    is_not_important: bool = False       # not_important

# Check completion
has_time_pref = bool(
    self.time.prefer_early_start or      # active
    self.time.prefer_late_start or       # active
    self.time.is_not_important           # not_important → complete!
)
```

**Filtering Logic:**
```python
# Skip filtering if marked as not important
if not preferences.get('time_is_not_important', False):
    # Apply time-based scoring
    if preferences.get('prefer_early_start'):
        score += 10
```

### 11. **5 Independent Criteria** (Split Pattern into Continuous + Free Days)

**Previous (4 questions):**
1. Day preference
2. Time preference  
3. **Pattern preference** (continuous + free_days together)
4. Specific requirements

**Current (5 questions):**
1. Day preference
2. Time preference
3. **Continuous preference** (học liên tục)
4. **Free days preference** (tối đa hóa ngày nghỉ)
5. Specific requirements (**NOW REQUIRED**)

**Schema Changes:**
```python
# OLD
class SchedulePatternPreference(BaseModel):
    prefer_continuous: bool = False
    prefer_free_days: bool = False
    is_not_important: bool = False

# NEW - Split into 2 independent classes
class ContinuousPreference(BaseModel):
    prefer_continuous: bool = False
    is_not_important: bool = False

class FreeDaysPreference(BaseModel):
    prefer_free_days: bool = False
    is_not_important: bool = False

class CompletePreference(BaseModel):
    time: TimePreference
    day: DayPreference
    continuous: ContinuousPreference      # Separate
    free_days: FreeDaysPreference         # Separate
    specific: SpecificRequirement
```

### 12. **Fixed Parsing Logic** - "không" vs "không quan trọng"

**Bug:** "không quan trọng" was matched as option 2 (không) instead of option 3

**Root Cause:**
```python
# WRONG - checks "không" before "không quan trọng"
elif '2' in response or 'không' in response:  # Matches both!
    prefer_continuous = False
else:
    is_not_important = True  # Never reached!
```

**Fix:** Check option 3 FIRST
```python
# CORRECT - check full phrase first
if '3' in response or 'không quan trọng' in response:
    is_not_important = True  # Option 3
elif '1' in response or 'có' in response:
    prefer_continuous = True  # Option 1
elif '2' in response or ('không' in response and 'quan trọng' not in response):
    prefer_continuous = False  # Option 2 - with safeguard
```

**Files Updated:**
- `preference_service.py` - parse_user_response() for both 'continuous' and 'free_days'

### 13. **Specific Requirements = REQUIRED + HARD FILTER** ⭐ HIGHEST PRIORITY

**Previous:**
- Question 5 (specific) was optional
- Specific requirements were soft filters (sorting preference)

**Current:**
- **Question 5 is REQUIRED** - must ask after question 4
- **Specific class IDs = HARD FILTER** (mandatory, not optional)
- **ALL combinations MUST include specified classes**

**Changes:**

A. **Make Question 5 Required:**
```python
# preference_schema.py - is_complete()
has_specific_answered = bool(
    self.specific.preferred_teachers or
    self.specific.specific_class_ids or
    self.specific.specific_times
)
return has_day_pref and has_time_pref and has_continuous_pref and has_free_days_pref and has_specific_answered
```

B. **Handle "không" Response:**
```python
# preference_service.py
if 'không' in response_lower and len(response_lower) < 15:
    # Mark as answered with no requirements
    current_preferences.specific.specific_times = {'answered': 'no_requirements'}
```

C. **Hard Filter Implementation:**
```python
# schedule_combination_service.py - generate_combinations()

# Step 1: Filter classes by specific_class_ids
specific_class_ids = preferences.get('specific_class_ids', [])
for subject_id, classes in classes_by_subject.items():
    if specific_class_ids:
        required_classes = [cls for cls in classes if cls['class_id'] in specific_class_ids]
        if required_classes:
            # ONLY use required classes for this subject
            subject_classes.append(required_classes)

# Step 2: Verify each combination contains ALL required classes
for combo in all_combinations:
    if specific_class_ids:
        combo_class_ids = [cls['class_id'] for cls in combo]
        if not all(req_id in combo_class_ids for req_id in specific_class_ids):
            continue  # Skip - missing required class
```

**Example Flow:**
```
User: "gợi ý lớp"
Bot: Câu 1 - Ngày học? → "thứ 2,3,5"
Bot: Câu 2 - Sớm/muộn? → "học sớm"
Bot: Câu 3 - Liên tục? → "không" → prefer_continuous=False ✅
Bot: Câu 4 - Ngày nghỉ? → "không quan trọng" → is_not_important=True ✅
Bot: Câu 5 - Yêu cầu cụ thể? → "lớp 161322" → specific_class_ids=['161322'] ✅

Generate combinations:
  1. ✅ Use ONLY class 161322 for that subject (hard filter)
  2. ✅ Verify ALL combinations contain class 161322
  3. ✅ Filter time conflicts
  4. ✅ Score by other preferences
  
Result: Every combination includes class 161322! 🎯
```

### 14. **Improved is_not_important Handling**

**Exports to dict:**
```python
result['time_is_not_important'] = self.time.is_not_important
result['day_is_not_important'] = self.day.is_not_important
result['continuous_is_not_important'] = self.continuous.is_not_important
result['free_days_is_not_important'] = self.free_days.is_not_important
```

**Skip filtering when not_important:**
```python
# class_suggestion_rules.py
if preferences.get('day_is_not_important', False):
    return classes  # Skip day filtering

# schedule_combination_service.py
if not preferences.get('time_is_not_important', False):
    # Apply time scoring
    
if not preferences.get('continuous_is_not_important', False):
    # Apply continuous scoring

if not preferences.get('free_days_is_not_important', False):
    # Apply free_days scoring
```

---

**Document Version:** 3.0  
**Last Updated:** December 13, 2025  
**Status:** ✅ 4-State System + 5 Criteria + Hard Filter + All Bugs Fixed  
**Breaking Changes:** Schema updated, question flow changed, filtering logic improved
