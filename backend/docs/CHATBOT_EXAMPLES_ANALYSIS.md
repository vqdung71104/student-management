# Chatbot Processing Examples - Step by Step Analysis

##  Mục lục

1. [Example 1: Simple Class Query](#example-1-simple-class-query)
2. [Example 2: Complex Subject Name](#example-2-complex-subject-name)
3. [Example 3: Class Suggestion with Filtering](#example-3-class-suggestion-with-filtering)
4. [Example 4: Schedule Query with Auth](#example-4-schedule-query-with-auth)
5. [Example 5: Multi-Entity Query](#example-5-multi-entity-query)

---

## Example 1: Simple Class Query

### Input
```
User message: "các lớp môn Giải tích"
Student ID: None (không cần đăng nhập)
```

---

### STEP 1: API Endpoint Reception

**File**: `chatbot_routes.py`
**Function**: `chat(message, db)`

```python
# Receive request
message = ChatMessage(
    message="các lớp môn Giải tích",
    student_id=None
)

# Validate input
assert message.message is not None
assert len(message.message) > 0
```

**Output**: Request validated ✓

---

### STEP 2: Intent Classification

**File**: `rasa_classifier.py`
**Function**: `classify_intent(message)`

#### 2.1. Text Preprocessing

```python
# Original
text = "các lớp môn Giải tích"

# Normalization
normalized = "cac lop mon giai tich"

# Tokenization (Underthesea)
tokens = word_tokenize(normalized)
# Result: ["cac", "lop", "mon", "giai_tich"]
```

#### 2.2. Rasa NLU Processing

```python
# 1. WhitespaceTokenizer
tokens = ["cac", "lop", "mon", "giai_tich"]

# 2. Character n-grams (CountVectorsFeaturizer)
char_ngrams = {
    "c", "ca", "cac",           # từ "cac"
    "l", "lo", "lop",           # từ "lop"
    "m", "mo", "mon",           # từ "mon"
    "g", "gi", "gia", "giai"   # từ "giai_tich"
}

# 3. Feature vector
features = [0.21, 0.54, 0.32, 0.18, 0.42, ...]  # 5000-dim vector

# 4. DIET Classifier (Deep Learning)
# Neural network forward pass
intent_probabilities = {
    "class_info": 0.923,           # ✓ Highest
    "subject_info": 0.042,
    "schedule_view": 0.018,
    "greeting": 0.005,
    ...
}

# 5. Select best intent
best_intent = "class_info"
confidence_score = 0.923
```

#### 2.3. Confidence Level Determination

```python
thresholds = {
    "high": 0.60,
    "medium": 0.40,
    "low": 0.25
}

if confidence_score >= 0.60:
    confidence = "high"  # ✓ This case
elif confidence_score >= 0.40:
    confidence = "medium"
else:
    confidence = "low"
```

**Output**:
```python
{
    "intent": "class_info",
    "confidence": "high",
    "score": 0.923
}
```

**Time**: ~60ms

---

### STEP 3: Entity Extraction

**File**: `nl2sql_service.py`
**Function**: `_extract_entities(question)`

#### 3.1. Subject ID Pattern

```python
pattern = r'\b([A-Z]{2,4}\d{4}[A-Z]?)\b'
text = "các lớp môn Giải tích"

match = re.search(pattern, text)
# Result: None (không có mã môn)
```

#### 3.2. Subject Name Patterns

```python
patterns = [
    r'các lớp của môn ([^,\?\.]+?)(?:\s*$|,|\?|\.)',
    r'các lớp môn ([^,\?\.]+?)(?:\s*$|,|\?|\.)',  # ✓ Match this
    r'môn ([^,\?\.]+?)(?:\s*$|,|\?|\.)',
]

# Try pattern 2
pattern = r'các lớp môn ([^,\?\.]+?)(?:\s*$|,|\?|\.)'
text = "các lớp môn Giải tích"

match = re.search(pattern, text, re.IGNORECASE)
# match.group(1) = "Giải tích"

subject_name = match.group(1).strip()
# Result: "Giải tích"
```

#### 3.3. Pattern Breakdown

```
Regex: r'các lớp môn ([^,\?\.]+?)(?:\s*$|,|\?|\.)'

các lớp môn     # Literal match
(               # Start capture group
  [^,\?\.]+?    # Match any char EXCEPT comma/question/dot (non-greedy)
)               # End capture group
(?:             # Non-capturing group
  \s*$          # Optional whitespace + end of string
  |             # OR
  ,|\?|\.       # comma/question/dot
)
```

**Output**:
```python
{
    "subject_name": "Giải tích"
}
```

**Time**: ~5ms

---

### STEP 4: SQL Generation

**File**: `nl2sql_service.py`
**Function**: `generate_sql(question, intent, student_id)`

#### 4.1. Load Training Examples

```python
# From nl2sql_training_data.json
examples = [
    {
        "intent": "class_info",
        "question": "các lớp môn Giải tích",
        "sql": "SELECT c.class_id, c.class_name, ... WHERE s.subject_name LIKE '%Giải tích%'"
    },
    {
        "intent": "class_info",
        "question": "các lớp của môn IT4040",
        "sql": "SELECT ... WHERE s.subject_id = 'IT4040'"
    },
    ...
]

# Filter by intent
class_info_examples = [e for e in examples if e["intent"] == "class_info"]
# 10 examples found
```

#### 4.2. Find Best Match (TF-IDF Similarity)

```python
# Query
query = "các lớp môn Giải tích"

# Example questions
example_questions = [
    "các lớp môn Giải tích",           # Exact match!
    "các lớp của môn IT4040",
    "lớp học vào thứ 2",
    ...
]

# TF-IDF Vectorization
vectorizer = TfidfVectorizer(tokenizer=word_tokenize)
pattern_vectors = vectorizer.fit_transform(example_questions)
query_vector = vectorizer.transform([query])

# Cosine Similarity
similarities = cosine_similarity(query_vector, pattern_vectors)[0]
# Result: [1.000, 0.654, 0.321, ...]
#         ^^^^^ Perfect match!

# Best match
best_idx = np.argmax(similarities)  # index = 0
best_score = similarities[best_idx]  # 1.000
best_example = examples[best_idx]
```

#### 4.3. Get SQL Template

```python
template_sql = best_example["sql"]

# Template:
"""
SELECT 
    c.class_id, 
    c.class_name, 
    c.classroom, 
    c.study_date, 
    c.study_time_start, 
    c.study_time_end, 
    c.teacher_name, 
    s.subject_name 
FROM classes c 
JOIN subjects s ON c.subject_id = s.id 
WHERE s.subject_name LIKE '%Giải tích%'
"""
```

#### 4.4. Customize SQL with Entities

```python
def _customize_sql(sql, entities, student_id):
    # Replace subject_name if extracted
    if "subject_name" in entities:
        # Pattern: s.subject_name LIKE '%...'
        old_pattern = r"s\.subject_name LIKE '%[^']+%'"
        new_value = f"s.subject_name LIKE '%{entities['subject_name']}%'"
        sql = re.sub(old_pattern, new_value, sql)
    
    # Replace student_id placeholder
    if student_id:
        sql = sql.replace("{student_id}", str(student_id))
    
    return sql

# Apply customization
entities = {"subject_name": "Giải tích"}
final_sql = _customize_sql(template_sql, entities, None)

# Result: SQL unchanged (already has "Giải tích")
```

**Output**:
```python
{
    "sql": "SELECT c.class_id, c.class_name, c.classroom, c.study_date, c.study_time_start, c.study_time_end, c.teacher_name, s.subject_name FROM classes c JOIN subjects s ON c.subject_id = s.id WHERE s.subject_name LIKE '%Giải tích%'",
    "method": "rule-based",
    "entities": {"subject_name": "Giải tích"},
    "similarity": 1.000
}
```

**Time**: ~10ms

---

### STEP 5: Database Query

**File**: `chatbot_routes.py`
**Using**: SQLAlchemy

```python
from sqlalchemy import text

# Execute SQL
sql = "SELECT c.class_id, c.class_name, ... WHERE s.subject_name LIKE '%Giải tích%'"

result = db.execute(text(sql))
rows = result.fetchall()

# Database execution (MySQL):
# 1. Parse SQL
# 2. Query execution plan
# 3. Index scan on subjects.subject_name
# 4. Join with classes table
# 5. Return result set

# Results (5 rows):
# class_id | class_name      | classroom | study_date | ...
# ---------|-----------------|-----------|------------|----
# 161001   | Giải tích 1     | D3-301    | Monday     | ...
# 161002   | Giải tích 1     | D3-302    | Tuesday    | ...
# 161003   | Giải tích 2     | D3-401    | Wednesday  | ...
# 161004   | Giải tích 1     | D5-201    | Thursday   | ...
# 161005   | Giải tích 2     | D5-202    | Friday     | ...
```

#### Convert to Dict

```python
# Get column names
columns = result.keys()
# Result: ['class_id', 'class_name', 'classroom', 'study_date', ...]

# Convert rows to dictionaries
data = []
for row in rows:
    data.append(dict(zip(columns, row)))

# Result:
data = [
    {
        "class_id": "161001",
        "class_name": "Giải tích 1",
        "classroom": "D3-301",
        "study_date": "Monday",
        "study_time_start": "07:30:00",
        "study_time_end": "09:30:00",
        "teacher_name": "Nguyễn Văn A",
        "subject_name": "Giải tích 1"
    },
    # ... 4 more records
]
```

**Time**: ~50ms

---

### STEP 6: Response Generation

**File**: `chatbot_routes.py`
**Function**: `_generate_response_text(intent, confidence, data)`

```python
def _generate_response_text(intent, confidence, classifier, data, sql_error):
    # Check for errors
    if sql_error:
        return f"Xin lỗi, có lỗi khi truy vấn dữ liệu: {sql_error}"
    
    # Check confidence
    if confidence == "low":
        return "Mình chưa hiểu rõ câu hỏi của bạn..."
    
    # Check data availability
    if data is None or len(data) == 0:
        return "Không tìm thấy dữ liệu phù hợp..."
    
    # Generate response based on intent
    if intent == "class_info":
        return f"Danh sách lớp học (tìm thấy {len(data)} lớp):"
    
# Call
response_text = _generate_response_text(
    intent="class_info",
    confidence="high",
    classifier=intent_classifier,
    data=data,  # 5 records
    sql_error=None
)

# Result: "Danh sách lớp học (tìm thấy 5 lớp):"
```

#### Final Response Object

```python
response = ChatResponseWithData(
    text="Danh sách lớp học (tìm thấy 5 lớp):",
    intent="class_info",
    confidence="high",
    data=[
        {
            "class_id": "161001",
            "class_name": "Giải tích 1",
            "classroom": "D3-301",
            ...
        },
        # ... 4 more
    ],
    sql="SELECT c.class_id, ... WHERE s.subject_name LIKE '%Giải tích%'",
    sql_error=None
)
```

---

### Complete Timeline

```
┌─────────────────────────────────────────────────────────────┐
│  0ms: User sends "các lớp môn Giải tích"                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  0-60ms: Intent Classification                               │
│  - Tokenization: "cac lop mon giai_tich"                     │
│  - Rasa NLU: 0.923 confidence                                │
│  - Result: class_info (high)                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  60-65ms: Entity Extraction                                  │
│  - Pattern matching: subject_name = "Giải tích"              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  65-75ms: SQL Generation                                     │
│  - TF-IDF matching: 1.000 similarity                         │
│  - Template: SELECT ... LIKE '%Giải tích%'                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  75-125ms: Database Query                                    │
│  - Execute SQL on MySQL                                      │
│  - Fetch 5 rows                                              │
│  - Convert to dict                                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  125ms: Response sent to user                                │
│  - Text: "Danh sách lớp học (tìm thấy 5 lớp):"              │
│  - Data: 5 class records                                     │
└─────────────────────────────────────────────────────────────┘
```

**Total Time**: ~125ms

---

## Example 2: Complex Subject Name

### Input
```
User message: "lớp của học phần Lý thuyết điều khiển tự động"
Student ID: None
```

---

### Key Differences from Example 1

#### Entity Extraction Challenge

```python
# Complex subject name with multiple words
text = "lớp của học phần Lý thuyết điều khiển tự động"

# Pattern matching
pattern = r'lớp của học phần ([^,\?\.]+?)(?:\s*$|,|\?|\.)'
match = re.search(pattern, text, re.IGNORECASE)

# Extraction
subject_name = match.group(1).strip()
# Result: "Lý thuyết điều khiển tự động"

# Challenge: Long compound name
# - Must preserve full name
# - Must handle Vietnamese diacritics
# - Must stop at sentence boundary
```

#### SQL Customization

```python
# Template SQL
sql = "SELECT ... WHERE s.subject_name LIKE '%...%'"

# Customize with long name
entities = {"subject_name": "Lý thuyết điều khiển tự động"}

# Replace pattern
old = r"s\.subject_name LIKE '%[^']+%'"
new = f"s.subject_name LIKE '%{entities['subject_name']}%'"
sql = re.sub(old, new, sql)

# Final SQL
"SELECT ... WHERE s.subject_name LIKE '%Lý thuyết điều khiển tự động%'"
```

#### Database Query

```sql
-- MySQL LIKE with Vietnamese characters
SELECT * 
FROM subjects 
WHERE subject_name LIKE '%Lý thuyết điều khiển tự động%'

-- Case insensitive matching (MySQL default)
-- Matches:
-- ✓ "Lý thuyết điều khiển tự động I"
-- ✓ "Lý thuyết điều khiển tự động II"
-- ✓ "Lý Thuyết Điều Khiển Tự Động"
```

---

## Example 3: Class Suggestion with Filtering

### Input
```
User message: "kỳ này nên học lớp nào"
Student ID: 1
```

---

### Enhanced SQL Logic

#### Step 1: Base Query
```sql
SELECT 
    c.class_id, 
    c.class_name,
    s.subject_name,
    s.subject_id,
    s.conditional_subjects
FROM classes c
JOIN subjects s ON c.subject_id = s.id
```

#### Step 2: Filter by Registered Subjects
```sql
WHERE s.id IN (
    SELECT subject_id 
    FROM subject_registers 
    WHERE student_id = 1
)
```

**Logic**: Chỉ gợi ý các lớp của môn đã đăng ký

#### Step 3: Exclude Learned Subjects
```sql
AND s.id NOT IN (
    SELECT subject_id 
    FROM learned_subjects 
    WHERE student_id = 1 
    AND letter_grade NOT IN ('F', 'I')
)
```

**Logic**: 
- Loại bỏ môn đã học **ĐẠT** (grade ≠ F, I)
- Giữ lại môn **TRƯỢT** (grade = F) để học lại
- Giữ lại môn **CHƯA HOÀN THÀNH** (grade = I)

#### Step 4: Get Student CPA

```python
# After fetching classes, add student info
student_query = """
SELECT cpa, failed_subjects_number, warning_level 
FROM students 
WHERE id = :student_id
"""

student_result = db.execute(text(student_query), {"student_id": 1}).fetchone()

# Add to each class record
for class_data in data:
    class_data["student_cpa"] = student_result[0]  # 3.30
    class_data["student_warning_level"] = student_result[2]  # "Cảnh cáo mức 0"
```

#### Response Text with CPA

```python
# Enhanced response
if len(data) > 0 and "student_cpa" in data[0]:
    cpa = data[0]["student_cpa"]
    warning = data[0]["student_warning_level"]
    cpa_info = f" (CPA: {cpa:.2f}, {warning})"
else:
    cpa_info = ""

response_text = f"Gợi ý các lớp học nên đăng ký (tìm thấy {len(data)} lớp){cpa_info}:"

# Result: "Gợi ý các lớp học nên đăng ký (tìm thấy 6 lớp) (CPA: 3.30, Cảnh cáo mức 0):"
```

---

### Data Flow Diagram

```
Student 1
├── Registered subjects (subject_registers)
│   ├── SSH1111 (Triết học)
│   └── ... (more subjects)
│
├── Learned subjects (learned_subjects)
│   ├── IT4040 (Grade: A)   Exclude
│   ├── MI1114 (Grade: B)   Exclude
│   ├── IT3080 (Grade: F) ✓ Include (failed)
│   └── ... (14 subjects)
│
└── Suggested classes
    ├── SSH1111 classes (6 classes) ✓
    └── IT3080 classes (2 classes) ✓
```

---

## Example 4: Schedule Query with Auth

### Input
```
User message: "lịch học của tôi"
Student ID: 1 (required)
```

---

### Authentication Check

```python
# Intent: schedule_view requires authentication
requires_auth = True

if requires_auth and student_id is None:
    return {
        "text": "Bạn cần đăng nhập để xem thông tin này.",
        "intent": "schedule_view",
        "confidence": "high",
        "data": None
    }
```

### SQL with Student Filter

```sql
SELECT 
    c.class_id,
    c.class_name,
    c.classroom,
    c.study_date,
    c.study_time_start,
    c.study_time_end,
    c.teacher_name,
    s.subject_name
FROM class_registers cr
JOIN classes c ON cr.class_id = c.id
JOIN subjects s ON c.subject_id = s.id
WHERE cr.student_id = 1  -- Authenticated student
ORDER BY c.study_date, c.study_time_start
```

### Result Processing

```python
# Fetch data
rows = db.execute(text(sql), {"student_id": 1}).fetchall()

# Group by day (optional enhancement)
schedule_by_day = {}
for row in rows:
    day = row["study_date"]
    if day not in schedule_by_day:
        schedule_by_day[day] = []
    schedule_by_day[day].append(dict(row))

# Response
response = {
    "text": f"Các môn/lớp bạn đã đăng ký (tìm thấy {len(rows)} lớp):",
    "data": rows
}
```

---

## Example 5: Multi-Entity Query

### Input
```
User message: "lớp 161084 môn IT4040 vào thứ 2"
Student ID: None
```

---

### Multi-Entity Extraction

```python
def _extract_entities(question):
    entities = {}
    
    # 1. Class ID
    class_match = re.search(r'\blớp\s+(\d{6})\b', question)
    if class_match:
        entities['class_id'] = class_match.group(1)
        # Result: "161084"
    
    # 2. Subject ID
    subject_match = re.search(r'\b([A-Z]{2,4}\d{4}[A-Z]?)\b', question)
    if subject_match:
        entities['subject_id'] = subject_match.group(1)
        # Result: "IT4040"
    
    # 3. Day of week
    day_mapping = {
        'thứ 2': 'Monday',
        'thứ hai': 'Monday',
        ...
    }
    for vn_day, en_day in day_mapping.items():
        if vn_day in question.lower():
            entities['day'] = en_day
            # Result: "Monday"
            break
    
    return entities

# Final result
entities = {
    "class_id": "161084",
    "subject_id": "IT4040",
    "day": "Monday"
}
```

### SQL with Multiple Filters

```python
# Base SQL
sql = """
SELECT c.class_id, c.class_name, ...
FROM classes c
JOIN subjects s ON c.subject_id = s.id
WHERE 1=1
"""

# Add filters based on entities
if "class_id" in entities:
    sql += f" AND c.class_id = '{entities['class_id']}'"

if "subject_id" in entities:
    sql += f" AND s.subject_id = '{entities['subject_id']}'"

if "day" in entities:
    sql += f" AND c.study_date LIKE '%{entities['day']}%'"

# Final SQL
"""
SELECT c.class_id, c.class_name, ...
FROM classes c
JOIN subjects s ON c.subject_id = s.id
WHERE 1=1
  AND c.class_id = '161084'
  AND s.subject_id = 'IT4040'
  AND c.study_date LIKE '%Monday%'
"""
```

---

## Summary: Processing Patterns

### Pattern 1: Simple Query
```
User Input → Intent → Entity → SQL Template → Database → Response
Time: ~125ms
Accuracy: 95%+
```

### Pattern 2: Authenticated Query
```
User Input → Intent → Auth Check → SQL with student_id → Database → Response
Time: ~130ms
Requires: Valid student_id
```

### Pattern 3: Complex Filtering
```
User Input → Intent → Entity → Multi-table SQL → Business Logic → Response
Time: ~150ms
Accuracy: 85%+
```

### Pattern 4: Enhanced Suggestion
```
User Input → Intent → SQL (registers + learned) → Add CPA → Format → Response
Time: ~180ms
Features: Smart filtering, CPA display
```

---

**Document version**: 1.0
**Last updated**: November 13, 2025
