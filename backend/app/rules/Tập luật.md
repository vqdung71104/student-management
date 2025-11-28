# TẬP LUẬT ĐĂNG KÝ HỌC PHẦN - CHATBOT SINH VIÊN

## 📚 Tổng quan

Rule Engine là **hệ thống luật (Rule-Based System - RBS)** tích hợp trong chatbot sinh viên, sử dụng cấu trúc **if-else-then** để đưa ra gợi ý đăng ký học phần thông minh dựa trên:

- ✅ Tình trạng học tập hiện tại của sinh viên
- ✅ Điểm số các môn đã học  
- ✅ Kỳ học hiện tại và lộ trình đào tạo
- ✅ Quy định về tín chỉ và cảnh báo học tập
- ✅ Yêu cầu chương trình đào tạo

---

## 📋 QUY ĐỊNH VỀ TÍN CHỈ ĐĂNG KÝ

### 1. Học kỳ chính (Kỳ 1, Kỳ 2)

#### **Sinh viên học lực BÌNH THƯỜNG**

```
✅ Tín chỉ tối thiểu: 12 TC
✅ Tín chỉ tối đa: 24 TC
⚠️ Năm cuối khóa (kỳ 7-8): KHÔNG áp dụng giới hạn tối thiểu
```

#### **Sinh viên bị CẢNH BÁO HỌC TẬP MỨC 1**

```
⚠️ Tín chỉ tối thiểu: 10 TC
⚠️ Tín chỉ tối đa: 18 TC
```

#### **Sinh viên bị CẢNH BÁO HỌC TẬP MỨC 2 trở lên**

```
🔴 Tín chỉ tối thiểu: 8 TC
🔴 Tín chỉ tối đa: 14 TC
```

#### **Sinh viên CHƯA ĐẠT CHUẨN NGOẠI NGỮ**

```
🔴 Tín chỉ tối thiểu: 8 TC
🔴 Tín chỉ tối đa: 14 TC
```

### 2. Học kỳ hè (Kỳ 3)

```
📅 Áp dụng cho: Kỳ học có số 3 đứng sau (20243, 20253, 20223...)
✅ Tín chỉ tối đa: 8 TC
ℹ️ Không có giới hạn tối thiểu
```

### 3. Cách xác định loại học kỳ

**Format tên kỳ học:** `YYYYS`

- `YYYY`: Năm học bắt đầu (VD: 2024 cho năm 2024-2025)
- `S`: Số kỳ (1, 2, 3)

**Ví dụ:**

- `20251` = Kỳ 1 năm học 2024-2025 (tháng 9/2024 - 1/2025)
- `20242` = Kỳ 2 năm học 2024-2025 (tháng 2/2025 - 7/2025)
- `20243` = Kỳ hè năm học 2024-2025 (tháng 8/2025)

---

## 🎯 CÁC LUẬT ƯU TIÊN (PRIORITY RULES)

### **RULE 1: Học lại môn điểm F** 🔴

**Mức độ ưu tiên:** CAO NHẤT

```python
IF môn học có điểm F:
    THEN ưu tiên đăng ký học lại NGAY
    REASON: Bắt buộc học lại để đủ điều kiện tốt nghiệp
```

**Giải thích:**

- Môn điểm F là môn **bắt buộc phải học lại**
- Được ưu tiên cao nhất trong tất cả các luật
- Sinh viên không thể tốt nghiệp nếu còn môn điểm F

**Cách áp dụng trong chatbot:**

1. Lấy danh sách môn đã học từ bảng `learned_subjects`
2. Lọc các môn có `letter_grade = 'F'`
3. Đưa vào danh sách gợi ý với priority_level = 1

---

### **RULE 2: Môn đúng kỳ học (Theo lộ trình)** 🟢

**Mức độ ưu tiên:** CAO

```python
IF learning_semester của môn == số kỳ sinh viên đang học:
    THEN ưu tiên đăng ký
    REASON: Đúng theo chương trình đào tạo, đảm bảo kiến thức nền tảng
```

**Cách tính số kỳ sinh viên đang học:**

- Mỗi năm học có **3 kỳ**: Kỳ 1 (9-1), Kỳ 2 (2-7), Kỳ 3 (8)
- **Kỳ 3 (kỳ hè) KHÔNG đếm** vào số thứ tự kỳ
- Tính dựa trên số kỳ chính đã hoàn thành

**Ví dụ:**

```
Sinh viên nhập học năm 2023:
- 20231 (Kỳ 1) → Kỳ thứ 1
- 20232 (Kỳ 2) → Kỳ thứ 2
- 20233 (Kỳ hè) → KHÔNG đếm
- 20241 (Kỳ 1) → Kỳ thứ 3
- 20242 (Kỳ 2) → Kỳ thứ 4
- 20251 (Kỳ 1) → Kỳ thứ 5 ← Đang học tại đây
```

**Cách áp dụng trong chatbot:**

1. Tính `student_semester_number` từ bảng `learned_subjects`
2. So sánh với `learning_semester` trong bảng `course_subjects`
3. Gợi ý các môn có `learning_semester == student_semester_number`

---

### **RULE 3: Môn triết/chính trị** 🟡

**Mức độ ưu tiên:** TRUNG BÌNH - CAO

```python
IF môn thuộc danh sách POLITICAL_SUBJECTS:
    AND chưa hoàn thành (hoặc điểm F):
        THEN gợi ý đăng ký
        REASON: Bắt buộc học đủ 6 môn triết/chính trị
```

**Danh sách môn (6 môn bắt buộc):**

```
SSH1111 - Triết học Mác - Lênin
SSH1121 - Kinh tế chính trị Mác - Lênin
SSH1131 - Chủ nghĩa xã hội khoa học
SSH1141 - Lịch sử Đảng cộng sản Việt Nam
SSH1151 - Tư tưởng Hồ Chí Minh
EM1170 - Kinh tế chính trị
```

**Cách áp dụng trong chatbot:**

1. Kiểm tra `subject_id` có trong `POLITICAL_SUBJECTS`
2. Kiểm tra sinh viên chưa hoàn thành hoặc có điểm F
3. Gợi ý tất cả các môn còn thiếu

---

### **RULE 4: Môn thể chất (PE)** 🏃

**Mức độ ưu tiên:** TRUNG BÌNH

```python
IF môn thuộc danh sách PE_SUBJECTS:
    AND số môn PE đã hoàn thành < 4:
        THEN gợi ý đăng ký
        REASON: Bắt buộc chọn 4/42 môn PE
```

**Danh sách 42 môn PE:**

```
PE2102, PE2202, PE2302, PE2402, PE2502, PE2101, PE2151
PE2201, PE2301, PE2401, PE2501, PE2601, PE2701, PE2801
PE2901, PE1024, PE1015, PE2261, PE2020-PE2029
PE1010, PE1020, PE1030, PE2010-PE2019
```

**Cách áp dụng trong chatbot:**

1. Đếm số môn PE đã hoàn thành (điểm khác F)
2. Nếu < 4 môn, gợi ý thêm các môn PE còn lại
3. Tối đa gợi ý đủ 4 môn

---

### **RULE 5: Môn bổ trợ** 🔵

**Mức độ ưu tiên:** TRUNG BÌNH

```python
IF môn thuộc danh sách SUPPLEMENTARY_SUBJECTS:
    AND số môn bổ trợ đã hoàn thành < 3:
        THEN gợi ý đăng ký
        REASON: Bắt buộc chọn 3/9 môn bổ trợ
```

**Danh sách 9 môn bổ trợ:**

```
CH2021 - Hóa học
ME3123, ME3124 - Cơ học
EM1010, EM1180 - Kinh tế
ED3280, ED3220 - Giáo dục
ET3262 - Điện tử
TEX3123 - Dệt may
```

**Cách áp dụng trong chatbot:**

1. Đếm số môn bổ trợ đã hoàn thành
2. Nếu < 3 môn, gợi ý thêm các môn còn lại
3. Tối đa gợi ý đủ 3 môn

---

### **RULE 6: Học nhanh (Fast Track)** ⚡

**Mức độ ưu tiên:** THẤP - TRUNG BÌNH

```python
IF CPA > 3.4:
    AND tổng tín chỉ đã gợi ý < max_credits_allowed:
        THEN gợi ý thêm các môn trong chương trình
        REASON: Sinh viên giỏi có thể học nhanh hơn lộ trình
```

**Điều kiện:**

- CPA phải > 3.4
- Chỉ gợi ý khi còn dư tín chỉ trong giới hạn cho phép

**Cách áp dụng trong chatbot:**

1. Kiểm tra `cpa > FAST_TRACK_CPA` (3.4)
2. Gợi ý các môn chưa học trong chương trình đào tạo
3. Không vượt quá `max_credits_allowed`

---

### **RULE 7: Cải thiện điểm (Grade Improvement)** 📈

**Mức độ ưu tiên:** THẤP

```python
IF tổng tín chỉ đã đăng ký <= 20:
    AND có môn điểm D/D+/C:
        THEN gợi ý học lại để cải thiện
        PRIORITY: F > D > D+ > C (ưu tiên môn ít TC trước)
        REASON: Nâng cao CPA
```

**Thứ tự ưu tiên cải thiện:**

```
1. Điểm F (phải học lại)
2. Điểm D (nên cải thiện)
3. Điểm D+ (có thể cải thiện)
4. Điểm C (cân nhắc cải thiện)
```

**Cách áp dụng trong chatbot:**

1. Kiểm tra tổng TC đã gợi ý <= 20
2. Lọc các môn có điểm D/D+/C
3. Sắp xếp theo thứ tự: điểm thấp hơn trước, TC ít hơn trước
4. Gợi ý cho đến khi đủ 20 TC

---

## 🔄 QUY TRÌNH XỬ LÝ TRONG CHATBOT

```
┌─────────────────────────────────────────┐
│  1. Nhận câu hỏi từ user                │
│     VD: "tôi nên đăng ký môn gì?"       │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  2. Intent Classification                │
│     → Phân loại: "subject_suggestion"    │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  3. Extract student_id từ context       │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  4. Get Student Data:                   │
│     - CPA, warning_level                │
│     - Completed subjects với grades     │
│     - Current semester                  │
│     - Student semester number           │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  5. Calculate Credit Limits             │
│     (dựa trên warning_level + semester) │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  6. Get Available Subjects              │
│     (từ course_subjects của course)     │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  7. Apply RULE 1: Failed (F) subjects   │
│     → Add to suggestions                │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  8. Apply RULE 2: Semester match        │
│     → Add to suggestions                │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  9. Apply RULE 3: Political subjects    │
│     → Add to suggestions                │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  10. Apply RULE 4: PE subjects          │
│      → Add max 4 subjects               │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  11. Apply RULE 5: Supplementary        │
│      → Add max 3 subjects               │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  12. Apply RULE 6: Fast track           │
│      (if CPA > 3.4)                     │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  13. Apply RULE 7: Grade improvement    │
│      (if total_credits <= 20)           │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  14. Check Constraints:                 │
│      - Total <= max_credits             │
│      - Total >= min_credits             │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  15. Format Response                    │
│      → Structured text với emojis       │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  16. Return to user qua chatbot UI      │
└─────────────────────────────────────────┘
```

---

## 🛠️ IMPLEMENTATION DETAILS

### 1. Database Schema

**Bảng `students`:**
```sql
- id: int (primary key)
- student_name: varchar
- cpa: decimal(3,2)
- warning_level: varchar ("Cảnh cáo mức X")
- course_id: int (foreign key)
```

**Bảng `learned_subjects`:**
```sql
- id: int (primary key)
- student_id: int (foreign key)
- subject_id: int (foreign key)
- letter_grade: varchar ('A+', 'A', 'B+', 'B', 'C+', 'C', 'D+', 'D', 'F')
- semester: varchar ('20251', '20242', ...)
```

**Bảng `course_subjects`:**
```sql
- id: int (primary key)
- course_id: int (foreign key)
- subject_id: int (foreign key)
- learning_semester: int (1-8, kỳ nên học môn này)
```

**Bảng `subjects`:**
```sql
- id: int (primary key)
- subject_id: varchar (mã môn học)
- subject_name: varchar
- credits: int
```

### 2. Code Structure

**File:** `backend/app/rules/subject_suggestion_rules.py`

**Main Class:** `SubjectSuggestionRuleEngine`

**Key Methods:**

```python
__init__(db: Session, config_path: str)
    # Khởi tạo rule engine, load config từ JSON

get_current_semester() -> str
    # Tính kỳ học hiện tại dựa trên ngày tháng

calculate_student_semester_number(student_id: int, current_semester: str) -> int
    # Tính sinh viên đang ở kỳ thứ mấy

get_student_data(student_id: int) -> Dict
    # Lấy thông tin sinh viên: CPA, warning_level, completed_subjects

is_summer_semester(semester: str) -> bool
    # Kiểm tra có phải kỳ hè không

is_final_year(student_semester_number: int) -> bool
    # Kiểm tra có phải năm cuối không

get_credit_limits(warning_level, current_semester, student_semester_number, has_foreign_lang_requirement) -> Tuple[int, int]
    # Tính min/max tín chỉ theo quy định

get_available_subjects(student_id: int, current_semester: str) -> List[Dict]
    # Lấy danh sách môn có thể đăng ký

rule_1_filter_failed_subjects(...) -> Tuple[List[Dict], List[Dict]]
    # Lọc môn điểm F

rule_2_filter_semester_match(...) -> Tuple[List[Dict], List[Dict]]
    # Lọc môn đúng kỳ

rule_3_filter_political_subjects(...) -> Tuple[List[Dict], List[Dict]]
    # Lọc môn triết/chính trị

rule_4_filter_physical_education(...) -> Tuple[List[Dict], List[Dict]]
    # Lọc môn PE

rule_5_filter_supplementary_subjects(...) -> Tuple[List[Dict], List[Dict]]
    # Lọc môn bổ trợ

rule_6_filter_fast_track(...) -> Tuple[List[Dict], List[Dict]]
    # Lọc môn học nhanh

rule_7_filter_grade_improvement(...) -> List[Dict]
    # Lọc môn cải thiện điểm

suggest_subjects(student_id: int, max_credits: Optional[int]) -> Dict
    # Method chính: tổng hợp tất cả rules

format_suggestion_response(suggestion_result: Dict) -> str
    # Format kết quả thành text response
```

### 3. Configuration File

**File:** `backend/app/rules/rules_config.json`

```json
{
  "credit_limits": {
    "min_credits_main_semester": 12,
    "max_credits_main_semester": 24,
    "max_credits_summer": 8,
    "min_credits_warning_1": 10,
    "max_credits_warning_1": 18,
    "min_credits_warning_2": 8,
    "max_credits_warning_2": 14,
    "min_credits_no_foreign_lang": 8,
    "max_credits_no_foreign_lang": 14,
    "improvement_threshold": 20
  },
  "subject_categories": {
    "political_subjects": [...],
    "physical_education_subjects": [...],
    "supplementary_subjects": [...]
  },
  "requirements": {
    "political_required": 6,
    "pe_required": 4,
    "supplementary_required": 3
  },
  "grade_thresholds": {
    "fast_track_cpa": 3.4,
    "improvement_grades": ["D", "D+", "C"],
    "failed_grade": "F"
  }
}
```

---

## 📝 USAGE EXAMPLES

### Example 1: Basic Usage

```python
from app.rules import SubjectSuggestionRuleEngine
from app.db.database import SessionLocal

# Initialize
db = SessionLocal()
rule_engine = SubjectSuggestionRuleEngine(db)

# Get suggestions for student ID 1
result = rule_engine.suggest_subjects(student_id=1)

# Format response
response_text = rule_engine.format_suggestion_response(result)

print(response_text)
```

### Example 2: Integration with Chatbot

**File:** `backend/app/services/chatbot_service.py`

```python
async def handle_subject_suggestion(student_id: int, db: Session) -> str:
    """
    Handle subject suggestion intent
    """
    try:
        # Initialize rule engine
        rule_engine = SubjectSuggestionRuleEngine(db)
        
        # Get suggestions
        result = rule_engine.suggest_subjects(student_id)
        
        # Format response
        response = rule_engine.format_suggestion_response(result)
        
        return response
        
    except Exception as e:
        return f"❌ Lỗi khi xử lý: {str(e)}"
```

### Example 3: Output Format

```markdown
🎓 **GỢI Ý ĐĂNG KÝ HỌC PHẦN**
==================================================

**📊 THÔNG TIN SINH VIÊN**
• Kỳ học hiện tại: 20251
• Đang ở kỳ thứ: 5
• CPA hiện tại: 3.30
• Mức cảnh báo: 0

**📋 GIỚI HẠN TÍN CHỈ**
• Tín chỉ tối thiểu: 12 TC
• Tín chỉ tối đa: 24 TC
• Tổng tín chỉ gợi ý: 22 TC
• Trạng thái: ✅ ĐẠT YÊU CẦU

**📚 DANH SÁCH MÔN HỌC ĐƯỢC GỢI Ý**

**🟢 ƯU TIÊN 2: Môn đúng lộ trình**
Các môn nên học trong kỳ này theo lộ trình:
1. **IT3170** - Thuật toán ứng dụng (2 tín chỉ)
2. **IT3070** - Nguyên lý hệ điều hành (3 tín chỉ)
3. **IT3080** - Mạng máy tính (3 tín chỉ)

**🟡 ƯU TIÊN 3: Môn chính trị**
Các môn chính trị bắt buộc:
1. **SSH1111** - Triết học Mác - Lênin (3 tín chỉ)
2. **SSH1121** - Kinh tế chính trị Mác - Lênin (2 tín chỉ)

**🏃 ƯU TIÊN 4: Môn thể chất**
Các môn giáo dục thể chất:
1. **PE1024** - Bơi lội (0 tín chỉ)

**📊 TỔNG KẾT**
• **Tổng số môn học:** 6 môn
• **Tổng số tín chỉ:** 8 TC

**Chúc bạn một kỳ học thành công! 🎉**
```

---

## 🧪 TESTING

### Test File Location

`backend/app/tests/test_credit_limits.py`

### Running Tests

```bash
cd backend
python -m pytest app/tests/test_credit_limits.py -v
```

### Test Cases

```python
test_normal_student_main_semester()
    # Test sinh viên bình thường kỳ chính

test_warning_level_1()
    # Test sinh viên cảnh báo mức 1

test_warning_level_2()
    # Test sinh viên cảnh báo mức 2

test_summer_semester()
    # Test kỳ hè

test_final_year_no_minimum()
    # Test năm cuối không có giới hạn tối thiểu

test_foreign_language_requirement()
    # Test sinh viên chưa đạt ngoại ngữ
```

---

## 🔧 MAINTENANCE & EXTENSION

### Adding New Rules

1. Tạo method mới `rule_X_filter_...()` trong class
2. Gọi method trong `suggest_subjects()` theo thứ tự ưu tiên
3. Cập nhật `summary` dict
4. Cập nhật `format_suggestion_response()` để hiển thị rule mới

### Updating Credit Limits

Chỉnh sửa file `rules_config.json`:

```json
{
  "credit_limits": {
    "min_credits_main_semester": 12,  // Thay đổi ở đây
    "max_credits_main_semester": 24   // Thay đổi ở đây
  }
}
```

### Adding Subject Categories

Chỉnh sửa `subject_categories` trong `rules_config.json`:

```json
{
  "subject_categories": {
    "new_category": ["SUBJ01", "SUBJ02", "SUBJ03"]
  }
}
```

---

## ⚠️ IMPORTANT NOTES

### 1. Semester Calculation

- **Kỳ 3 (kỳ hè) KHÔNG được tính** vào số thứ tự kỳ
- Chỉ tính kỳ 1 và kỳ 2 của mỗi năm học
- Công thức: `semester_number = count(non-summer semesters) + 1`

### 2. Warning Level Parsing

- Database lưu warning_level dạng string: `"Cảnh cáo mức 2"`
- Code phải parse để lấy số: `int(warning_str.split()[-1])`

### 3. Grade Column Name

- Bảng `learned_subjects` dùng `letter_grade` KHÔNG phải `grade`
- Giá trị: 'A+', 'A', 'B+', 'B', 'C+', 'C', 'D+', 'D', 'F'

### 4. Credit Limits Priority

Order của checks:

1. Summer semester? → Max 8 TC, no minimum
2. Foreign language requirement? → 8-14 TC
3. Warning level 2+? → 8-14 TC
4. Warning level 1? → 10-18 TC
5. Normal student? → 12-24 TC
6. Final year? → Remove minimum requirement

### 5. Response Formatting

- Frontend cần CSS `white-space: pre-wrap` để hiển thị xuống dòng
- Hoặc convert `\n` thành `<br/>` trong HTML
- Markdown formatting: `**text**` cho bold

---

## 📚 REFERENCES

- **Rule Engine Code:** `backend/app/rules/subject_suggestion_rules.py`
- **Configuration:** `backend/app/rules/rules_config.json`
- **Tests:** `backend/app/tests/test_credit_limits.py`
- **Chatbot Integration:** `backend/app/services/chatbot_service.py`
- **Frontend Display:** `frontend/src/components/ChatBot/ChatBot.tsx`

---

**Document Version:** 2.0  
**Last Updated:** November 28, 2025  
**Author:** Student Management System Team
