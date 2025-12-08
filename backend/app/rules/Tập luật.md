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

## 📋 TẬP LUẬT ĐĂNG KÝ LỚP HỌC (CLASS REGISTRATION RULES)

### 🎯 Tổng quan

Hệ thống **Class Registration Rule Engine** giúp sinh viên tìm lớp học phù hợp dựa trên **nhu cầu cá nhân** về:

- ⏰ Thời gian học (sáng/chiều/tối, sớm/muộn)
- 📅 Ngày học trong tuần (tránh thứ 7, tránh ngày cụ thể)
- 👨‍🏫 Giáo viên ưa thích
- 🏢 Phòng học/vị trí
- 📊 Tối ưu lịch học (học liên tục, nghỉ nhiều ngày)

### 🔄 Quy trình tương tác

```
┌─────────────────────────────────────────┐
│  1. User: "Tôi muốn đăng ký lớp"        │
│     Intent: class_registration_suggest  │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  2. Chatbot hỏi về preferences:         │
│     - Muốn học buổi nào?                │
│     - Tránh học sớm không?              │
│     - Tránh học thứ mấy?                │
│     - Muốn học liên tục không?          │
│     - Có giáo viên ưa thích không?      │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  3. Lưu preferences vào Redis Cache     │
│     Key: class_preferences:{student_id} │
│     TTL: 1 hour                         │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  4. Get suggested subjects              │
│     (từ subject_suggestion_rules)       │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  5. Get available classes               │
│     (từ database classes table)         │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  6. Apply filters:                      │
│     - Time preference filter            │
│     - Weekday preference filter         │
│     - Teacher filter                    │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  7. Rank classes by scoring:            │
│     - Time match: +15 points            │
│     - Teacher match: +20 points         │
│     - Early/late preference: +10        │
│     - No avoided days: +5               │
│     - High availability: +5             │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  8. Calculate schedule metrics:         │
│     - Study days per week               │
│     - Free days                         │
│     - Continuous sessions               │
│     - Intensive days (>5h)              │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  9. Format & return suggestions         │
└─────────────────────────────────────────┘
```

### 📝 Các tiêu chí lọc (Filters)

#### 1. **Time Period Filter** - Lọc theo buổi học

```python
IF time_period == 'morning':
    THEN chỉ giữ lớp có 06:00 <= study_time_start < 12:00
ELIF time_period == 'afternoon':
    THEN chỉ giữ lớp có 12:00 <= study_time_start < 18:00
ELIF time_period == 'evening':
    THEN chỉ giữ lớp có 18:00 <= study_time_start < 22:00
```

**Cách áp dụng:**
- User chọn "Tôi muốn học buổi sáng"
- Filter loại bỏ tất cả lớp có `study_time_start >= 12:00`

#### 2. **Early/Late Filter** - Lọc giờ bắt đầu/kết thúc

```python
IF avoid_early_start == True:
    THEN loại bỏ lớp có study_time_start < 08:00

IF avoid_late_end == True:
    THEN loại bỏ lớp có study_time_end > 17:00
```

**Ví dụ:**
- Lớp IT3170: 06:45-08:15 → LOẠI BỎ (nếu avoid_early_start)
- Lớp IT4040: 15:00-17:30 → LOẠI BỎ (nếu avoid_late_end)
- Lớp IT3080: 09:00-11:00 → GIỮ LẠI

#### 3. **Weekday Filter** - Lọc theo ngày trong tuần

```python
IF avoid_days = ['Saturday', 'Sunday']:
    THEN loại bỏ lớp có study_date chứa 'Saturday' hoặc 'Sunday'

IF prefer_days = ['Monday', 'Wednesday', 'Friday']:
    THEN chỉ giữ lớp có ALL study_date nằm trong prefer_days
```

**Ví dụ:**
- Lớp A: study_date = "Monday,Wednesday,Friday" → GIỮ LẠI
- Lớp B: study_date = "Tuesday,Thursday,Saturday" → LOẠI BỎ (có Saturday)

#### 4. **Teacher Filter** - Lọc theo giáo viên

```python
IF preferred_teachers = ['Nguyễn Văn A', 'Trần Thị B']:
    THEN chỉ giữ lớp có teacher_name chứa tên trong danh sách
```

**Cách áp dụng:**
- Tìm kiếm không phân biệt hoa thường
- Cho phép tìm kiếm một phần (partial match)
- VD: "Nguyễn" sẽ match với "Nguyễn Văn A", "Nguyễn Thị C"

### 🏆 Hệ thống chấm điểm (Scoring)

Mỗi lớp được chấm điểm dựa trên mức độ phù hợp:

```
Tổng điểm = 
    + 15 điểm (nếu đúng buổi học mong muốn)
    + 20 điểm (nếu đúng giáo viên ưa thích)
    + 10 điểm (nếu phù hợp early/late preference)
    + 5 điểm (nếu kết thúc trước 17:00)
    + 5 điểm (không có ngày bị tránh)
    + 5 điểm (còn nhiều chỗ trống >50%)

Điểm tối đa: 60 điểm
```

**Ví dụ:**

```
Lớp IT3170-001:
- Sáng (08:00-10:00): +15 (đúng buổi)
- GV: Nguyễn Văn A: +20 (đúng GV)
- Không học sớm: +10
- Kết thúc 10:00: +5
- Thứ 2,4,6: +5 (không có thứ 7)
- Chỗ trống: 40/50: +5
→ TỔNG: 60 điểm ⭐⭐⭐⭐⭐

Lớp IT3170-002:
- Chiều (14:00-16:00): +0 (không đúng buổi)
- GV: Trần Thị B: +0
- Kết thúc 16:00: +5
- Thứ 3,5: +5
- Chỗ trống: 10/50: +0
→ TỔNG: 10 điểm ⭐
```

### 📊 Schedule Metrics - Đánh giá lịch học

Hệ thống tính toán các chỉ số để đánh giá chất lượng lịch học:

#### 1. **Study Days** - Số ngày học

```python
study_days = số ngày unique có lớp học
free_days = 7 - study_days
```

**Ví dụ:**
- Lớp A: Monday, Wednesday, Friday → 3 ngày → 4 ngày nghỉ
- Lớp B: Monday, Tuesday, Wednesday, Thursday, Friday → 5 ngày → 2 ngày nghỉ

#### 2. **Continuous Sessions** - Buổi học liên tục

```python
IF gap giữa 2 lớp <= 30 phút:
    THEN đếm là "continuous session"
```

**Ví dụ:**
```
Thứ 2:
- Lớp 1: 08:00-09:30
- Lớp 2: 09:35-11:05 (gap = 5 phút)
- Lớp 3: 13:00-14:30 (gap = 115 phút)
→ 1 continuous session (lớp 1+2)
```

#### 3. **Intensive Days** - Ngày học tập trung

```python
IF tổng giờ học trong 1 ngày >= 5 giờ:
    THEN đếm là "intensive day"
```

**Ví dụ:**
```
Thứ 3:
- Lớp A: 08:00-10:00 (2h)
- Lớp B: 10:00-12:00 (2h)
- Lớp C: 13:00-15:00 (2h)
→ Tổng = 6h → Intensive day ✅
```

**Lợi ích:**
- Dành thời gian cho thực tập
- Giảm chi phí đi lại
- Tập trung học hết trong ít ngày

### 🗂️ Redis Cache - Lưu trữ preferences

Để hỗ trợ conversation flow (hỏi từng câu), hệ thống sử dụng **Redis Cache**:

```python
# Structure
Key: "class_preferences:{student_id}"
Value: JSON {
    "time_period": "morning",
    "avoid_early_start": true,
    "avoid_late_end": false,
    "avoid_days": ["Saturday"],
    "preferred_teachers": ["Nguyễn Văn A"],
    "maximize_free_days": true,
    "prefer_continuous": true,
    "timestamp": "2025-12-02T10:30:00"
}
TTL: 3600 seconds (1 hour)
```

**Workflow:**

1. **Câu hỏi đầu tiên:** Bạn muốn học buổi nào?
   - Lưu: `{"time_period": "morning"}`

2. **Câu hỏi thứ 2:** Tránh học sớm không?
   - Update: `{"time_period": "morning", "avoid_early_start": true}`

3. **Câu hỏi thứ 3:** Tránh ngày nào?
   - Update: `{"...", "avoid_days": ["Saturday"]}`

4. **Hoàn thành:** Áp dụng tất cả preferences và gợi ý lớp

### 📝 Preference Questions - Các câu hỏi thu thập

Định nghĩa trong `class_rules_config.json`:

```json
{
  "preference_questions": {
    "time_period": {
      "question": "Bạn muốn học vào buổi nào?",
      "options": [
        {"value": "morning", "label": "Sáng"},
        {"value": "afternoon", "label": "Chiều"},
        {"value": "evening", "label": "Tối"},
        {"value": "any", "label": "Không quan tâm"}
      ]
    },
    "avoid_early_start": {
      "question": "Bạn có muốn tránh học sớm (trước 8:00) không?",
      "type": "boolean"
    },
    ...
  }
}
```

**Chatbot sẽ hỏi theo thứ tự:**

1. Buổi học (morning/afternoon/evening)
2. Tránh học sớm? (yes/no)
3. Tránh kết thúc muộn? (yes/no)
4. Tránh ngày nào? (multi-select)
5. Tối đa hóa ngày nghỉ? (yes/no)
6. Học liên tục? (yes/no)
7. Giáo viên ưa thích? (text input)

### 🛠️ Implementation Details

**File:** `backend/app/rules/class_suggestion_rules.py`

**Main Class:** `ClassSuggestionRuleEngine`

**Key Methods:**

```python
get_available_classes(student_id, subject_ids) -> List[Dict]
    # Lấy danh sách lớp available (còn chỗ trống)

filter_by_time_preference(classes, preferences) -> List[Dict]
    # Lọc theo time_period, avoid_early_start, avoid_late_end

filter_by_weekday_preference(classes, preferences) -> List[Dict]
    # Lọc theo avoid_days, prefer_days

filter_by_teacher(classes, teacher_names) -> List[Dict]
    # Lọc theo teacher_name

rank_classes_by_preferences(classes, preferences) -> List[Dict]
    # Chấm điểm và sắp xếp

calculate_schedule_metrics(classes) -> Dict
    # Tính study_days, free_days, continuous_sessions, intensive_days

suggest_classes(student_id, subject_ids, preferences) -> Dict
    # Main method: tổng hợp tất cả

format_class_suggestions(suggestion_result) -> str
    # Format kết quả thành text
```

### 📚 Usage Example

```python
from app.rules import ClassSuggestionRuleEngine
from app.db.database import SessionLocal

# Initialize
db = SessionLocal()
class_engine = ClassSuggestionRuleEngine(db)

# User preferences (từ Redis hoặc input)
preferences = {
    'time_period': 'morning',
    'avoid_early_start': True,
    'avoid_late_end': True,
    'avoid_days': ['Saturday', 'Sunday'],
    'preferred_teachers': ['Nguyễn Văn A'],
    'maximize_free_days': True,
    'prefer_continuous': True
}

# Subject IDs (từ subject_suggestion_rules)
subject_ids = [101, 102, 103]  # IT3170, IT3080, IT4040

# Get suggestions
result = class_engine.suggest_classes(
    student_id=1,
    subject_ids=subject_ids,
    preferences=preferences
)

# Format response
response_text = class_engine.format_class_suggestions(result)
print(response_text)
```

**Output Example:**

```markdown
🎓 **GỢI Ý LỚP HỌC PHẦN**
==================================================

📊 **TỔNG QUAN**
• Tổng số lớp phù hợp: **8** lớp
• Đã lọc bỏ: 12 lớp không phù hợp

📅 **LỊCH HỌC DỰ KIẾN**
• Số ngày học: 3 ngày/tuần
• Số ngày nghỉ: 4 ngày/tuần
• Số buổi học liên tục: 2 buổi
• Số ngày học tập trung (>5h): 1 ngày

⚙️ **TIÊU CHÍ ÁP DỤNG**
• Buổi học: Buổi sáng
• Tránh học sớm (trước 8:00)
• Tránh kết thúc muộn (sau 17:00)
• Tránh các ngày: Thứ 7, Chủ nhật
• Giáo viên ưu tiên: Nguyễn Văn A

📚 **DANH SÁCH LỚP GỢI Ý**

**1. Thuật toán ứng dụng** (2 TC)

   **Lớp 1:** IT3170-001 - Thuật toán ứng dụng 1
   • Thời gian: 08:00 - 10:00
   • Ngày học: Thứ 2, Thứ 4, Thứ 6
   • Phòng: TC-201
   • Giảng viên: Nguyễn Văn A
   • Chỗ trống: 45/50
   • Phù hợp: Buổi sáng, Teacher: Nguyễn Văn A, No avoided days
   • Điểm ưu tiên: ⭐ 50/50

   **Lớp 2:** IT3170-002 - Thuật toán ứng dụng 2
   • Thời gian: 09:00 - 11:00
   • Ngày học: Thứ 3, Thứ 5
   • Phòng: TC-305
   • Giảng viên: Trần Thị B
   • Chỗ trống: 30/50
   • Phù hợp: Buổi sáng, Ends before 17:00
   • Điểm ưu tiên: ⭐ 25/50

**2. Mạng máy tính** (3 TC)
   ...

**Chúc bạn đăng ký thành công! 🎉**
```

### 🧪 Testing

**Test File:** `backend/app/tests/test_class_suggestion_rules.py`

```python
def test_filter_by_time_morning():
    # Test lọc lớp học buổi sáng
    
def test_filter_avoid_early_start():
    # Test tránh học sớm
    
def test_filter_by_weekday():
    # Test tránh thứ 7
    
def test_rank_by_teacher():
    # Test ưu tiên giáo viên
    
def test_calculate_schedule_metrics():
    # Test tính toán metrics
```

### ⚠️ Important Notes

1. **Redis Cache TTL:** 1 hour - đủ cho conversation flow
2. **Scoring Range:** 0-60 điểm (có thể mở rộng)
3. **Gap Threshold:** 30 phút cho continuous classes
4. **Intensive Day:** >= 5 giờ học/ngày
5. **Available Slots:** Chỉ gợi ý lớp còn chỗ trống

### 🔗 Integration với Subject Suggestion

```python
# Step 1: Get suggested subjects
subject_result = subject_engine.suggest_subjects(student_id)
subject_ids = [s['id'] for s in subject_result['suggested_subjects']]

# Step 2: Get preferences from Redis
preferences = redis_client.get(f"class_preferences:{student_id}")

# Step 3: Get class suggestions
class_result = class_engine.suggest_classes(
    student_id, subject_ids, preferences
)
```

---

**Document Version:** 3.0  
**Last Updated:** December 2, 2025  
**Author:** Student Management System Team
