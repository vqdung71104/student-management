# Interactive Class Suggestion System - Design Document

## Tổng quan

Hệ thống gợi ý lớp học tương tác với khả năng:
1. Thu thập preferences qua hội thoại đa bước
2. Tạo các tổ hợp lớp từ nhiều môn (no conflicts, 1 class per subject)
3. Đưa ra 2-3 phương án tốt nhất

## Vấn đề hiện tại

**Current Flow:**
```
User: "gợi ý các lớp nên đăng ký kỳ sau"
  ↓
Extract preferences (nếu có)
  ↓
Get recommended subjects
  ↓
Get ALL classes of each subject (10+ classes per subject)
  ↓
Return: 10 classes of SSH1131 (all same subject) ❌
```

**Problem:**
- Trả về nhiều lớp của 1 môn → Không có ý nghĩa (học 1 môn chỉ cần 1 lớp)
- Không tạo schedule combinations
- Không kiểm tra time conflicts giữa các môn
- Chưa thu thập đầy đủ preferences

## Giải pháp đề xuất

### Phase 1: Conversation State Management

**New Flow:**
```
User: "gợi ý các lớp nên đăng ký kỳ sau"
  ↓
Extract initial preferences
  ↓
Check missing preferences
  ↓
If missing → Ask follow-up questions (interactive)
  ↓
Collect all preferences
  ↓
Generate schedule combinations
  ↓
Return top 2-3 combinations
```

### Phase 2: Preference Collection System

#### 2.1. Complete Preference Schema

```python
preferences = {
    # Time preferences
    'time_period': 'morning' | 'afternoon' | None,
    'avoid_time_periods': ['morning', 'afternoon'],  # List
    
    # Day preferences
    'prefer_days': ['Monday', 'Tuesday'],  # List
    'avoid_days': ['Saturday', 'Sunday'],  # List
    
    # Study time preferences
    'prefer_early_start': bool,  # Học sớm (start early, end early)
    'prefer_late_start': bool,   # Học muộn (start late, end late)
    'avoid_early_start': bool,   # Tránh học sớm
    'avoid_late_end': bool,      # Tránh học muộn
    
    # Schedule pattern preferences
    'prefer_continuous': bool,   # Học liên tục nhiều lớp 1 buổi (>5h/day)
    'prefer_free_days': bool,    # Tối đa hóa ngày nghỉ
    
    # Specific requirements
    'preferred_teachers': ['Nguyễn Văn A'],  # List
    'specific_class_ids': ['161084'],        # List
    'specific_times': {
        'start': '08:00',
        'end': '12:00'
    }
}
```

#### 2.2. Interactive Questions (5 CÂU)

**UPDATE:** Sử dụng đầy đủ 5 câu hỏi để thu thập preferences chi tiết.

```python
PREFERENCE_QUESTIONS = {
    'day': {
        'question': "📅 Bạn thích học vào những ngày nào trong tuần?",
        'options': ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật'],
        'type': 'multi_choice',
        'maps_to': ['prefer_days', 'avoid_days'],
        'supports_compact_format': True  # Hỗ trợ "thứ 2,3,4"
    },
    
    'time': {
        'question': "⏰ Bạn muốn học sớm hay học muộn?",
        'options': ['Học sớm (ưu tiên lớp bắt đầu sớm)', 'Học muộn (ưu tiên lớp kết thúc muộn)', 'Không quan trọng'],
        'type': 'single_choice',
        'maps_to': ['prefer_early_start', 'prefer_late_start']
    },
    
    'continuous_preference': {
        'question': "Bạn thích học liên tục nhiều lớp trong 1 buổi không?",
        'options': ['Có, tôi muốn học liên tục', 'Không, tôi muốn có khoảng nghỉ', 'Không quan trọng'],
        'type': 'single_choice',
        'maps_to': ['prefer_continuous']
    },
    
    'free_days_preference': {
        'question': "Bạn thích học ít ngày nhất có thể không?",
        'options': ['Có, tôi muốn tối đa hóa ngày nghỉ', 'Không, tôi muốn học đều các ngày', 'Không quan trọng'],
        'type': 'single_choice',
        'maps_to': ['prefer_free_days']
    },
    
    'specific_requirements': {
        'question': "Bạn còn yêu cầu nào cụ thể không? (giáo viên, mã lớp, thời gian cụ thể)",
        'type': 'free_text',
        'maps_to': ['preferred_teachers', 'specific_class_ids', 'specific_times']
    }
}
```

### Phase 3: Schedule Combination Algorithm

#### 3.1. Algorithm Overview

```python
def generate_schedule_combinations(
    student_id: int,
    preferences: Dict
) -> List[ScheduleCombination]:
    """
    Generate schedule combinations from multiple subjects
    
    Returns:
        List of schedule combinations, each containing:
        - classes: List of classes (1 per subject)
        - total_credits: Total credits
        - metrics: Schedule quality metrics
        - score: Overall score
    """
    
    # Step 1: Get recommended subjects
    subjects = get_recommended_subjects(student_id)  # From SubjectSuggestionRuleEngine
    
    # Step 2: Get candidate classes for each subject
    subject_classes = {}
    for subject in subjects:
        classes = get_classes_for_subject(subject.id)
        # Filter by preferences
        filtered_classes = filter_by_preferences(classes, preferences)
        # Keep top 5-10 classes per subject
        subject_classes[subject.id] = filtered_classes[:10]
    
    # Step 3: Generate all valid combinations
    combinations = []
    for combo in itertools.product(*subject_classes.values()):
        # Check absolute rules
        if not has_time_conflicts(combo):
            if not violates_one_class_per_subject(combo):
                combinations.append(combo)
    
    # Step 4: Score and rank combinations
    scored_combinations = []
    for combo in combinations:
        score = calculate_combination_score(combo, preferences)
        metrics = calculate_schedule_metrics(combo)
        scored_combinations.append({
            'classes': combo,
            'score': score,
            'metrics': metrics
        })
    
    # Step 5: Sort by score and return top 2-3
    scored_combinations.sort(key=lambda x: x['score'], reverse=True)
    return scored_combinations[:3]
```

#### 3.2. Time Conflict Detection

```python
def has_time_conflicts(classes: List[Dict]) -> bool:
    """
    Check if any two classes have overlapping time
    
    Conflict if:
    - Same day
    - Time ranges overlap
    """
    for i, class1 in enumerate(classes):
        for class2 in classes[i+1:]:
            # Parse study_date (e.g., "Monday,Wednesday")
            days1 = set(parse_study_days(class1['study_date']))
            
            # Step 1: Check study_week overlap (CRITICAL FIX Dec 13, 2025)
            weeks1 = set(class1.get('study_week', []) or [])
            weeks2 = set(class2.get('study_week', []) or [])
            
            common_weeks = weeks1 & weeks2
            if not common_weeks:
                continue  # No common weeks, no conflict
            
            # Step 2: Check study_date overlap
            days1 = set(parse_study_days(class1['study_date']))
            days2 = set(parse_study_days(class2['study_date']))
            
            common_days = days1 & days2
            if not common_days:
                continue  # No common days, no conflict
            
            # Step 3: Check time overlap
            start1 = parse_time(class1['study_time_start'])
            end1 = parse_time(class1['study_time_end'])
            start2 = parse_time(class2['study_time_start'])
            end2 = parse_time(class2['study_time_end'])
            
            # Conflict if start2 in [start1, end1) OR end2 in (start1, end1]
            # OR class2 covers class1 completely
            if (start1 <= start2 < end1) or (start1 < end2 <= end1) or \
               (start2 <= start1 and end2 >= end1):
                return True  # Conflict found
    
    return False  # No conflicts
```

#### 3.3. Schedule Metrics

```python
def calculate_schedule_metrics(classes: List[Dict]) -> Dict:
    """
    Calculate schedule quality metrics
    """
    # Group classes by day
    schedule_by_day = group_by_day(classes)
    
    metrics = {
        'total_credits': sum(cls['credits'] for cls in classes),
        'total_classes': len(classes),
        'study_days': len(schedule_by_day),  # Số ngày có học
        'free_days': 7 - len(schedule_by_day),  # Số ngày nghỉ
        'continuous_study_days': 0,  # Số ngày học liên tục >5h
        'average_daily_hours': 0,
        'earliest_start': None,
        'latest_end': None,
        'time_conflicts': False
    }
    
    # Calculate daily hours
    daily_hours = []
    for day, day_classes in schedule_by_day.items():
        # Sort by start time
        day_classes.sort(key=lambda x: x['study_time_start'])
        
        # Calculate total hours
        first_start = day_classes[0]['study_time_start']
        last_end = day_classes[-1]['study_time_end']
        hours = (last_end - first_start).total_seconds() / 3600
        daily_hours.append(hours)
        
        # Check if continuous (>5h)
        if hours > 5:
            metrics['continuous_study_days'] += 1
    
    metrics['average_daily_hours'] = sum(daily_hours) / len(daily_hours) if daily_hours else 0
    
    # Find earliest/latest
    all_starts = [cls['study_time_start'] for cls in classes]
    all_ends = [cls['study_time_end'] for cls in classes]
    metrics['earliest_start'] = min(all_starts)
    metrics['latest_end'] = max(all_ends)
    
    return metrics
```

#### 3.4. Combination Scoring

```python
def calculate_combination_score(
    classes: List[Dict],
    preferences: Dict
) -> float:
    """
    Calculate overall score for a combination
    
    Higher score = better match to preferences
    """
    score = 100.0  # Base score
    
    metrics = calculate_schedule_metrics(classes)
    
    # Preference: Free days (weight: 20)
    if preferences.get('prefer_free_days'):
        # More free days = higher score
        score += metrics['free_days'] * 4  # Max +20 (5 free days)
    
    # Preference: Continuous study (weight: 20)
    if preferences.get('prefer_continuous'):
        # More continuous days = higher score
        score += metrics['continuous_study_days'] * 5  # Max +20 (4 days)
    
    # Preference: Time period (weight: 15)
    time_period = preferences.get('time_period')
    if time_period:
        matching_classes = sum(
            1 for cls in classes
            if get_time_period(cls['study_time_start']) == time_period
        )
        score += (matching_classes / len(classes)) * 15
    
    # Preference: Avoid time periods (weight: 15)
    avoid_periods = preferences.get('avoid_time_periods', [])
    if avoid_periods:
        violating_classes = sum(
            1 for cls in classes
            if get_time_period(cls['study_time_start']) in avoid_periods
        )
        score -= violating_classes * 5  # Penalty
    
    # Preference: Days (weight: 15)
    prefer_days = preferences.get('prefer_days', [])
    if prefer_days:
        matching_days = 0
        for cls in classes:
            days = parse_study_days(cls['study_date'])
            if any(day in prefer_days for day in days):
                matching_days += 1
        score += (matching_days / len(classes)) * 15
    
    # Preference: Early/Late start (weight: 10)
    if preferences.get('prefer_early_start'):
        avg_start_hour = sum(
            cls['study_time_start'].hour for cls in classes
        ) / len(classes)
        # Earlier = higher score (7:00 = max, 12:00 = min)
        score += max(0, (12 - avg_start_hour) / 5 * 10)
    
    # Preference: Available slots (weight: 5)
    # More available slots = better
    avg_availability = sum(
        cls['available_slots'] / cls['max_students'] for cls in classes
    ) / len(classes)
    score += avg_availability * 5
    
    return score
```

### Phase 4: Conversation State Management

#### 4.1. State Schema

```python
conversation_state = {
    'student_id': int,
    'session_id': str,
    'intent': 'class_registration_suggestion',
    'stage': 'initial' | 'collecting_preferences' | 'generating_combinations' | 'completed',
    'preferences': {
        # Collected preferences
    },
    'questions_asked': ['day_preference', 'time_preference'],  # Track asked questions
    'questions_remaining': ['continuous_preference', 'free_days_preference'],
    'pending_question': {
        'key': 'day_preference',
        'question': '...',
        'options': [...]
    },
    'timestamp': datetime
}
```

#### 4.2. State Storage

Use Redis for temporary state storage:

```python
# In cache/redis_cache.py
def save_conversation_state(student_id: int, state: Dict):
    """Save conversation state to Redis"""
    key = f"conversation:class_suggestion:{student_id}"
    redis_client.setex(key, 3600, json.dumps(state))  # 1 hour TTL

def get_conversation_state(student_id: int) -> Dict:
    """Get conversation state from Redis"""
    key = f"conversation:class_suggestion:{student_id}"
    state = redis_client.get(key)
    return json.loads(state) if state else None
```

### Phase 5: Response Formatting

#### 5.1. Combination Response Format

```json
{
  "text": "🎯 GỢI Ý LỊCH HỌC THÔNG MINH\n\n📊 Thông tin:\n• CPA: 3.30\n• Tín chỉ gợi ý: 12-18 TC\n\n✨ Đã tạo 3 phương án lịch học tối ưu:\n\n🔵 PHƯƠNG ÁN 1 (Điểm: 95/100) ⭐ KHUYÊN DÙNG\n• 4 môn học - 12 tín chỉ\n• Học 3 ngày/tuần (Nghỉ 4 ngày)\n• Không xung đột thời gian\n\n  1. IT3170 - Lập trình mạng (3 TC)\n     📍 Lớp 161084: T3,T5 13:00-15:25 - D5-401 - GV: Nguyễn Văn A\n     ✅ Buổi chiều | 30 chỗ trống\n\n  2. SSH1131 - Tư tưởng HCM (2 TC)\n     📍 Lớp 164489: T2 09:20-11:45 - TC-312\n     ✅ Buổi sáng | 150 chỗ trống\n\n  3. ...\n\n🟢 PHƯƠNG ÁN 2 (Điểm: 88/100)\n...",
  
  "data": [
    {
      "combination_id": 1,
      "score": 95,
      "recommended": true,
      "classes": [
        {
          "class_id": "161084",
          "subject_id": "IT3170",
          "subject_name": "Lập trình mạng",
          "credits": 3,
          "study_date": "Tuesday,Thursday",
          "study_time_start": "13:00",
          "study_time_end": "15:25",
          "classroom": "D5-401",
          "teacher_name": "Nguyễn Văn A",
          "available_slots": 30
        },
        ...
      ],
      "metrics": {
        "total_credits": 12,
        "total_classes": 4,
        "study_days": 3,
        "free_days": 4,
        "continuous_study_days": 0,
        "average_daily_hours": 3.5,
        "time_conflicts": false
      }
    },
    ...
  ]
}
```

## Implementation Plan

### Step 1: Add Conversation State (Week 1)
- [ ] Create conversation state schema
- [ ] Implement Redis state storage
- [ ] Add state tracking in chatbot_service

### Step 2: Interactive Preference Collection (Week 1-2)
- [ ] Define preference questions
- [ ] Implement preference extraction from responses
- [ ] Add follow-up question logic
- [ ] Handle multi-turn conversation

### Step 3: Combination Generation (Week 2)
- [ ] Implement time conflict detection
- [ ] Create combination generator
- [ ] Add filtering by absolute rules

### Step 4: Scoring System (Week 2-3)
- [ ] Implement schedule metrics calculation
- [ ] Create scoring algorithm
- [ ] Tune weights based on feedback

### Step 5: Response Formatting (Week 3)
- [ ] Format combination responses
- [ ] Add visual indicators (emoji, badges)
- [ ] Create comparison view

### Step 6: Testing (Week 3-4)
- [ ] Unit tests for each component
- [ ] Integration tests
- [ ] User acceptance testing

## Performance Considerations

### Combination Count
- 5 subjects × 10 classes each = 100,000 combinations
- Need optimization: Prune early, limit candidates

### Optimization Strategies
1. **Early pruning**: Filter classes by preferences BEFORE combination
2. **Limit candidates**: Max 5-7 classes per subject
3. **Incremental building**: Build combinations incrementally, skip conflicts
4. **Caching**: Cache class data, preference filters
5. **Parallel processing**: Generate combinations in parallel

## Example Usage

### Scenario 1: Full Interactive Flow

```
User: "gợi ý các lớp nên đăng ký kỳ sau"

Bot: "Để gợi ý chính xác nhất, tôi cần biết thêm về sở thích của bạn.
      
      📅 Bạn thích học vào những ngày nào trong tuần?
      [Thứ 2] [Thứ 3] [Thứ 4] [Thứ 5] [Thứ 6] [Thứ 7] [CN]"

User: "Thứ 2, Thứ 3, Thứ 5"

Bot: "⏰ Bạn muốn học sớm hay học muộn?
      [Học sớm (7:00-12:00)] [Học muộn (13:00-18:00)] [Không quan trọng]"

User: "Học sớm"

Bot: "📚 Bạn thích học liên tục nhiều lớp trong 1 buổi không?
      [Có] [Không] [Không quan trọng]"

User: "Không"

Bot: "🗓️ Bạn thích học ít ngày nhất có thể không?
      [Có, tối đa hóa ngày nghỉ] [Không] [Không quan trọng]"

User: "Có"

Bot: "🎯 GỢI Ý LỊCH HỌC THÔNG MINH
      
      ✨ Đã tạo 3 phương án tối ưu cho bạn:
      
      🔵 PHƯƠNG ÁN 1 (Điểm: 95/100) ⭐
      • 4 môn - 12 TC
      • Học T2,T3,T5 (Nghỉ 4 ngày)
      • Tất cả buổi sáng (7:00-12:00)
      ..."
```

### Scenario 2: Partial Preferences

```
User: "gợi ý lớp học buổi chiều, không học thứ 7"

Bot: [Extract: time_period='afternoon', avoid_days=['Saturday']]
     [Missing: continuous, free_days, specific]
     
     "📚 Bạn thích học liên tục nhiều lớp trong 1 buổi không?
      [Có] [Không] [Không quan trọng]"
```

## Metrics & Success Criteria

### Success Metrics
- [x] **100%** combinations have no time conflicts (Fixed Dec 13, 2025)
- [x] Average response time < 3 seconds
- [ ] User satisfaction > 4/5
- [x] 80%+ of combinations match preferences

### Testing

**Test Suite:** `tests/test_time_conflict_detection.py` (Created Dec 13, 2025)

**Coverage:** 17 comprehensive test cases
- 7 NO CONFLICT cases (different weeks/days/times, edge cases)
- 6 CONFLICT cases (same start, overlap, covering)
- 2 Real world scenarios from production data
- 2 Multiple class combinations

**Results:** ✅ All tests passing

**Key Fixes:**
1. ✅ study_week now stored as LIST instead of string
2. ✅ Conflict detection checks 3 conditions: week + day + time
3. ✅ timedelta parsing fixed for database time values
4. ✅ Lazy evaluation for efficient combination search (1000 checks vs 100)

### Quality Metrics
- Combination diversity (different schedules)
- Score distribution (clear winners)
- Preference match rate
- User selection rate (which combination chosen)

---

## 🆕 Updates (December 13, 2025)

### 1. 4-State Preference System
- Added **is_not_important** state to all preference types
- Each criterion can be: active, passive, none, or not_important
- "Không quan trọng" response skips filtering/scoring for that criterion

### 2. 5 Independent Criteria (Split Pattern)
- **Previous:** 4 questions (day, time, pattern, specific)
- **Current:** 5 questions (day, time, continuous, free_days, specific)
- Continuous and free_days now have separate is_not_important flags

### 3. Specific Requirements = Required + Hard Filter
- Question 5 is now **REQUIRED** (must ask after question 4)
- `specific_class_ids` = **HARD FILTER** (not soft preference)
- ALL combinations MUST include specified classes

### 4. Fixed Parsing Logic
- Check "không quan trọng" BEFORE "không" alone
- Prevents option 3 being matched as option 2

---

**Version:** 2.0  
**Created:** December 12, 2025  
**Updated:** December 13, 2025  
**Status:** ✅ Implemented + 4-State System + 5 Criteria + Hard Filter
