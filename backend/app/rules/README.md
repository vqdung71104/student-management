# Rule Engine Documentation

## Tổng quan

Rule Engine là hệ thống luật (Rule-Based System - RBS) cho chatbot, sử dụng cấu trúc if-else-then để đưa ra gợi ý thông minh.

## Subject Suggestion Rule Engine

### 📋 Mục đích

Gợi ý các học phần sinh viên nên đăng ký dựa trên:
- Tình trạng học tập hiện tại
- Điểm số các môn đã học
- Kỳ học hiện tại
- Yêu cầu chương trình đào tạo

### 🎯 Thứ tự ưu tiên các luật

#### 1. **RULE 1: Học lại môn điểm F** (Priority: Cao nhất)
```python
IF học phần có điểm F:
    THEN ưu tiên đăng ký học lại
    REASON: Bắt buộc học lại để đạt điểm đủ tốt nghiệp
```

#### 2. **RULE 2: Môn đúng kỳ học** (Priority: Cao)
```python
IF learning_semester của môn == số kỳ sinh viên đang học:
    THEN ưu tiên đăng ký
    REASON: Theo đúng chương trình đào tạo
    
EXAMPLE:
    Sinh viên đang kỳ 5 (20251)
    Môn MI1114 có learning_semester = 4
    → Nên đăng ký vào kỳ 4 (20242)
```

**Cách tính kỳ học:**
- Mỗi năm có 3 kỳ: Kỳ 1 (9-1), Kỳ 2 (2-7), Kỳ 3 (8)
- Tên kỳ: `YYYYS` (VD: 20251, 20242)
- Kỳ 3 là kỳ phụ, không đếm vào thứ tự kỳ
- Sinh viên năm 3 đã qua các kỳ: 20231, 20232, 20241, 20242, 20251 → Đang kỳ thứ 5

#### 3. **RULE 3: Môn triết/chính trị** (Priority: Trung bình - Cao)
```python
IF học phần thuộc danh sách:
    ['SSH1111', 'SSH1121', 'SSH1131', 'SSH1141', 'SSH1151', 'EM1170']
AND chưa hoàn thành:
    THEN ưu tiên đăng ký
    REASON: Bắt buộc học hết 6 môn triết
```

#### 4. **RULE 4: Môn thể chất** (Priority: Trung bình)
```python
IF học phần thuộc danh sách PE series
AND đã hoàn thành < 4 môn PE:
    THEN gợi ý đăng ký
    REASON: Bắt buộc chọn 4/42 môn PE
    
Danh sách 42 môn PE:
    PE2102, PE2202, PE2302, PE2402, PE2502, PE2101, PE2151,
    PE2201, PE2301, PE2401, PE2501, PE2601, PE2701, PE2801,
    PE2901, PE1024, PE1015, PE2261, PE2020-PE2029,
    PE1010, PE1020, PE1030, PE2010-PE2019
```

#### 5. **RULE 5: Môn bổ trợ** (Priority: Trung bình)
```python
IF học phần thuộc danh sách:
    ['CH2021', 'ME3123', 'ME3124', 'EM1010', 'EM1180',
     'ED3280', 'ED3220', 'ET3262', 'TEX3123']
AND đã hoàn thành < 3 môn:
    THEN gợi ý đăng ký
    REASON: Bắt buộc chọn 3/9 môn bổ trợ
```

#### 6. **RULE 6: Học nhanh (Fast Track)** (Priority: Thấp - Trung bình)
```python
IF CPA > 3.4
AND tổng tín chỉ < max_allowed:
    THEN gợi ý thêm các môn trong chương trình
    REASON: Sinh viên giỏi có thể học nhanh hơn
```

#### 7. **RULE 7: Cải thiện điểm** (Priority: Thấp)
```python
IF tổng tín chỉ đã đăng ký <= 20
AND có môn điểm D/D+/C:
    THEN gợi ý học cải thiện
    PRIORITY: F > D > D+ > C (môn ít TC trước)
    REASON: Nâng cao CPA
```

### 📊 Giới hạn tín chỉ

```python
# Tín chỉ tối thiểu mỗi kỳ
MIN_CREDITS = 8

# Tín chỉ tối đa
IF warning_level >= 2:
    MAX_CREDITS = 18  # Bị cảnh báo mức 2-3
ELSE:
    MAX_CREDITS = 28  # Bình thường

# Ngưỡng cải thiện điểm
IMPROVEMENT_THRESHOLD = 20  # Chỉ cải thiện nếu <= 20 TC
```

### 🔄 Flow hoạt động

```
┌─────────────────────────────────────────┐
│  Input: student_id                      │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Get Student Data:                      │
│  - CPA, GPA, warning_level              │
│  - Completed subjects with grades       │
│  - Current semester                     │
│  - Student semester number              │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Calculate Max Credits Allowed          │
│  (28 or 18 based on warning)            │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Get Available Subjects                 │
│  (from course_subjects)                 │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Apply RULE 1: Failed subjects (F)      │
│  → Add to suggestions                   │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Apply RULE 2: Semester match           │
│  → Add to suggestions                   │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Apply RULE 3: Political subjects       │
│  → Add to suggestions                   │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Apply RULE 4: Physical education       │
│  → Add max 4 subjects                   │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Apply RULE 5: Supplementary subjects   │
│  → Add max 3 subjects                   │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Apply RULE 6: Fast track (if CPA>3.4)  │
│  → Add remaining subjects               │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Apply RULE 7: Grade improvement        │
│  (if total_credits <= 20)               │
│  → Add D/D+/C subjects                  │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Check Constraints:                     │
│  - Total credits <= MAX_CREDITS         │
│  - Total credits >= MIN_CREDITS (8)     │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Output:                                │
│  - Suggested subjects (ordered)         │
│  - Total credits                        │
│  - Summary by category                  │
│  - Formatted response text              │
└─────────────────────────────────────────┘
```

### 📝 Usage Example

```python
from app.rules import SubjectSuggestionRuleEngine
from app.db.database import SessionLocal

# Initialize
db = SessionLocal()
rule_engine = SubjectSuggestionRuleEngine(db)

# Get suggestions for student
result = rule_engine.suggest_subjects(student_id=1)

# Format response
response_text = rule_engine.format_suggestion_response(result)

print(response_text)
```

**Output Example:**
```
📚 GỢI Ý ĐĂNG KÝ HỌC PHẦN
============================================================

📊 Thông tin sinh viên:
  • Kỳ học hiện tại: 20251
  • Đang ở kỳ thứ: 5
  • CPA: 3.45
  • Mức cảnh báo: 0

📋 Giới hạn tín chỉ:
  • Tối thiểu: 8 tín chỉ
  • Tối đa: 28 tín chỉ
  • Tổng gợi ý: 22 tín chỉ
  • Trạng thái: ✅ Đủ

🔴 PRIORITY 1: Học lại môn điểm F (1 môn)
  • MI1114 - Giải tích 1 (4 TC)

🟢 PRIORITY 2: Môn đúng kỳ học (3 môn)
  • IT4040 - Lập trình mạng (3 TC)
  • EM3180 - Quản lý dự án (2 TC)
  • IT4140 - Cơ sở dữ liệu (3 TC)

🟡 PRIORITY 3: Môn triết/chính trị (2 môn)
  • SSH1141 - Tư tưởng HCM (2 TC)
  • EM1170 - Kinh tế chính trị (3 TC)

🟠 PRIORITY 4: Môn thể chất (1 môn)
  • PE2202 - Bóng đá (1 TC)

⚡ PRIORITY 6: Học nhanh (CPA > 3.4) (2 môn)
  • IT4501 - Đồ án 1 (3 TC)
  • IT4421 - Trí tuệ nhân tạo (3 TC)

📌 TỔNG KẾT:
  • Tổng số môn gợi ý: 9 môn
  • Tổng tín chỉ: 22 TC
```

### 🧪 Testing

```bash
# Test rule engine
python -c "
from app.rules import SubjectSuggestionRuleEngine
from app.db.database import SessionLocal

db = SessionLocal()
engine = SubjectSuggestionRuleEngine(db)

# Test with student ID 1
result = engine.suggest_subjects(1)
print(engine.format_suggestion_response(result))
"
```

### 🔧 Extension

Để thêm rule mới:

1. Thêm method `rule_X_filter_...()` trong class
2. Gọi method trong `suggest_subjects()` theo thứ tự ưu tiên
3. Cập nhật `summary` dict
4. Cập nhật `format_suggestion_response()` để hiển thị rule mới

### 📚 Database Dependencies

Rule engine sử dụng các bảng sau:
- `students`: CPA, GPA, warning_level, course_id
- `learned_subjects`: Điểm các môn đã học
- `subjects`: Thông tin học phần
- `course_subjects`: Môn học trong chương trình, learning_semester
- `classes`: Thông tin lớp học
- `class_registers`: Lịch sử đăng ký

### ⚠️ Notes

1. **Semester calculation**: 
   - Kỳ 1 (tháng 9-1), Kỳ 2 (tháng 2-7), Kỳ 3 (tháng 8)
   - Kỳ 3 không được tính vào số thứ tự kỳ
   
2. **Credit limits**:
   - Cảnh báo mức 2-3: Chỉ được đăng ký tối đa 18 TC
   - Bình thường: Tối đa 28 TC
   - Tối thiểu: 8 TC

3. **Grade improvement**:
   - Chỉ cải thiện khi tổng TC <= 20
   - Ưu tiên: F > D > D+ > C
   - Ưu tiên môn ít TC hơn

4. **Special subject groups**:
   - Political: Phải học hết 6 môn
   - PE: Chọn 4 trong 42 môn
   - Supplementary: Chọn 3 trong 9 môn
