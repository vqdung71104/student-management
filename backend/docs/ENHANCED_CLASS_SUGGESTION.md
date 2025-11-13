# Enhanced Class Registration Suggestion with Student Grade Filtering

## Tổng quan thay đổi

Đã cải thiện logic gợi ý đăng ký lớp học (`class_registration_suggestion`) để:

1.    **Lọc theo môn đã đăng ký** (subject_registers)
2.    **Loại bỏ môn đã học đạt** (learned_subjects với điểm không phải F/I)
3.    **Hiển thị điều kiện tiên quyết** (conditional_subjects)
4.    **Thêm thông tin CPA** vào response để sinh viên tham khảo

## Chi tiết thay đổi

### 1. Cập nhật SQL Queries (nl2sql_training_data.json)

**Trước đây:**
```sql
SELECT c.class_id, c.class_name, ..., s.subject_id 
FROM classes c 
JOIN subjects s ON c.subject_id = s.id 
WHERE s.id IN (
    SELECT subject_id FROM subject_registers WHERE student_id = {student_id}
)
```

**Bây giờ:**
```sql
SELECT c.class_id, c.class_name, ..., s.subject_id, s.conditional_subjects
FROM classes c 
JOIN subjects s ON c.subject_id = s.id 
WHERE s.id IN (
    SELECT subject_id FROM subject_registers WHERE student_id = {student_id}
) 
AND s.id NOT IN (
    SELECT subject_id FROM learned_subjects 
    WHERE student_id = {student_id} 
    AND letter_grade NOT IN ('F', 'I')
)
ORDER BY s.subject_name, c.study_date
```

**Thay đổi:**
-    Added: `s.conditional_subjects` trong SELECT để hiển thị môn tiên quyết
-    Added: `AND s.id NOT IN (...)` để loại bỏ môn đã học đạt
-    Logic: Chỉ loại bỏ môn có điểm **KHÔNG PHẢI 'F' hoặc 'I'** (tức là đã đạt)
-    Giữ lại: Môn có điểm F (Fail) hoặc I (Incomplete) để sinh viên có thể học lại

### 2. Cập nhật Response Handler (chatbot_routes.py)

**Thêm logic lấy CPA:**
```python
# For class_registration_suggestion, add student CPA info
if intent == "class_registration_suggestion" and message.student_id:
    student_result = db.execute(text(
        "SELECT cpa, failed_subjects_number, warning_level FROM students WHERE id = :student_id"
    ), {"student_id": message.student_id}).fetchone()
    
    if student_result:
        for item in data:
            item["student_cpa"] = student_result[0]
            item["student_failed_subjects"] = student_result[1]
            item["student_warning_level"] = student_result[2]
```

**Cập nhật response text:**
```python
elif intent == "class_registration_suggestion":
    cpa_info = ""
    if len(data) > 0 and "student_cpa" in data[0]:
        cpa = data[0]["student_cpa"]
        warning = data[0].get("student_warning_level", "")
        cpa_info = f" (CPA của bạn: {cpa:.2f}, {warning})"
    return f"Gợi ý các lớp học nên đăng ký (tìm thấy {len(data)} lớp){cpa_info}:"
```

## Test Results

### Student 1 (Vũ Quang Dũng)
- **CPA**: 3.3
- **Đã học**: 14 môn với điểm đạt (A+, A, B+, B, C+, C)
- **Đã đăng ký**: 1 môn (SSH1111 - Triết học Mác - Lênin)
- **Gợi ý**: 6 lớp của môn SSH1111 (môn chưa học)
- **Loại bỏ**: Tất cả 14 môn đã học đạt không xuất hiện trong gợi ý

### SQL Query Behavior

| Tình huống | Có xuất hiện trong gợi ý? |
|-----------|---------------------------|
| Môn đã đăng ký, chưa học |    CÓ |
| Môn đã đăng ký, đã học đạt (A, B, C, D) |   KHÔNG |
| Môn đã đăng ký, học không đạt (F) |    CÓ (để học lại) |
| Môn đã đăng ký, chưa hoàn thành (I) |    CÓ (để hoàn thành) |
| Môn chưa đăng ký |   KHÔNG |

## Benefits

1. **Tránh đăng ký nhầm**: Sinh viên không thấy gợi ý các môn đã học đạt
2. **Học lại môn trượt**: Môn có điểm F vẫn xuất hiện để sinh viên học lại
3. **Thông tin đầy đủ**: Hiển thị CPA, warning level, conditional subjects
4. **Logic rõ ràng**: SQL query phản ánh đúng quy trình học tập thực tế

## Files Modified

1. `backend/data/nl2sql_training_data.json` - Updated 6 SQL queries for class_registration_suggestion
2. `backend/app/routes/chatbot_routes.py` - Added CPA fetching and display logic
3. `backend/scripts/test_enhanced_suggestion.py` - Test script to verify new logic

## Next Steps

- [ ] Test với nhiều student khác nhau
- [ ] Consider thêm logic check điều kiện tiên quyết (conditional_subjects)
- [ ] Có thể thêm filter theo CPA threshold nếu cần
- [ ] Train ViT5 model với updated training data (optional)
