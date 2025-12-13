# ABSOLUTE RULES FOR CLASS REGISTRATION

## 🚫 Luật Tuyệt Đối (Không Được Vi Phạm)

Đây là 2 luật **BẮT BUỘC** phải tuân thủ khi gợi ý đăng ký lớp học phần. Các lớp vi phạm 2 luật này sẽ **BỊ LOẠI HOÀN TOÀN** khỏi danh sách gợi ý.

---

## 1️⃣ LUẬT 1: KHÔNG TRÙNG LỊCH HỌC

### 📋 Định nghĩa

Hai lớp học **trùng lịch** khi thỏa mãn **CẢ 3 ĐIỀU KIỆN** sau:

1. **Cùng ngày học** (study_date): Có ít nhất một ngày trùng nhau
2. **Cùng tuần học** (study_weeks): Có ít nhất một tuần trùng nhau
3. **Thời gian học chồng lấn**: Khoảng thời gian học (từ `study_time_start` đến `study_time_end`) có phần trùng nhau

### ✅ Ví dụ KHÔNG TRÙNG LỊCH (Hợp lệ)

#### Ví dụ 1: Khác tuần học
```
Lớp A: Thứ 2, tuần 1,3,5,7,9     08:15 - 11:45
Lớp B: Thứ 2, tuần 2,4,6,8,10    09:25 - 14:00
→ ✅ KHÔNG TRÙNG vì học khác tuần
```

#### Ví dụ 2: Khác ngày học
```
Lớp A: Thứ 2, tuần 1-16          08:15 - 11:45
Lớp B: Thứ 3, tuần 1-16          08:15 - 11:45
→ ✅ KHÔNG TRÙNG vì học khác ngày
```

#### Ví dụ 3: Không chồng lấn thời gian
```
Lớp A: Thứ 2, tuần 1-16          08:00 - 09:00
Lớp B: Thứ 2, tuần 1-16          09:25 - 11:00
→ ✅ KHÔNG TRÙNG vì thời gian không overlap (có khoảng trống 25 phút)
```

#### Ví dụ 4: Sát nhau (liền kề)
```
Lớp A: Thứ 4, tuần 1-16          08:00 - 09:00
Lớp B: Thứ 4, tuần 1-16          09:00 - 10:00
→ ✅ KHÔNG TRÙNG vì thời gian chỉ sát nhau (không overlap)
```

#### Ví dụ 5: Một phần khác tuần
```
Lớp A: Thứ 2, tuần 1-8           08:00 - 10:00
Lớp B: Thứ 2, tuần 9-16          08:00 - 10:00
→ ✅ KHÔNG TRÙNG vì không có tuần nào trùng nhau
```

### ❌ Ví dụ TRÙNG LỊCH (Vi phạm)

#### Ví dụ 1: Trùng hoàn toàn
```
Lớp A: Thứ 2, tuần 1,3,5,7,9     08:15 - 11:45
Lớp B: Thứ 2, tuần 1,3,5,7,9     09:25 - 14:00
→ ❌ TRÙNG LỊCH vì:
   - Cùng ngày (Thứ 2)
   - Cùng tuần (1,3,5,7,9)
   - Thời gian overlap (09:25-11:45)
```

#### Ví dụ 2: Một phần tuần trùng
```
Lớp A: Thứ 3, tuần 1-8           08:00 - 10:00
Lớp B: Thứ 3, tuần 5-12          09:00 - 11:00
→ ❌ TRÙNG LỊCH vì:
   - Cùng ngày (Thứ 3)
   - Có tuần chung (5,6,7,8)
   - Thời gian overlap (09:00-10:00)
```

#### Ví dụ 3: Nhiều ngày, trùng một ngày
```
Lớp A: Thứ 2,4, tuần 1-16        08:00 - 10:00
Lớp B: Thứ 3,4, tuần 1-16        09:00 - 11:00
→ ❌ TRÙNG LỊCH vì:
   - Có ngày chung (Thứ 4)
   - Cùng tuần (1-16)
   - Thời gian overlap (09:00-10:00)
```

#### Ví dụ 4: Thời gian bao phủ
```
Lớp A: Thứ 5, tuần 1-16          08:00 - 12:00
Lớp B: Thứ 5, tuần 1-16          09:00 - 10:00
→ ❌ TRÙNG LỊCH vì:
   - Cùng ngày (Thứ 5)
   - Cùng tuần (1-16)
   - Lớp B nằm hoàn toàn trong Lớp A
```

### 🔍 Thuật toán kiểm tra

```python
def has_schedule_conflict(class1, class2):
    # Bước 1: Kiểm tra ngày học
    days1 = parse_days(class1.study_date)  # e.g., {"Monday", "Wednesday"}
    days2 = parse_days(class2.study_date)  # e.g., {"Wednesday", "Friday"}
    common_days = days1 ∩ days2            # e.g., {"Wednesday"}
    
    if common_days is empty:
        return False  # Không trùng vì khác ngày
    
    # Bước 2: Kiểm tra tuần học
    weeks1 = parse_weeks(class1.study_weeks)  # e.g., {1,3,5,7,9}
    weeks2 = parse_weeks(class2.study_weeks)  # e.g., {1,2,3,4,5}
    common_weeks = weeks1 ∩ weeks2            # e.g., {1,3,5}
    
    if common_weeks is empty:
        return False  # Không trùng vì khác tuần
    
    # Bước 3: Kiểm tra thời gian overlap
    start1 = class1.study_time_start  # e.g., 08:15
    end1 = class1.study_time_end      # e.g., 11:45
    start2 = class2.study_time_start  # e.g., 09:25
    end2 = class2.study_time_end      # e.g., 14:00
    
    # Không overlap nếu: lớp 1 kết thúc trước lớp 2 bắt đầu
    #                    HOẶC lớp 2 kết thúc trước lớp 1 bắt đầu
    no_overlap = (end1 <= start2) OR (end2 <= start1)
    
    if no_overlap:
        return False  # Không trùng vì thời gian không overlap
    
    return True  # TRÙNG LỊCH!
```

### 📊 Parse study_weeks

Hỗ trợ các format:

```python
"all"           → {1,2,3,...,16}     # Tất cả 16 tuần
"1,3,5,7,9"     → {1,3,5,7,9}        # Danh sách các tuần
"1-8"           → {1,2,3,4,5,6,7,8}  # Range
"1-4,7,9-11"    → {1,2,3,4,7,9,10,11} # Mixed
""              → {1,2,3,...,16}     # Default all
```

---

## 2️⃣ LUẬT 2: MỖI MÔN CHỈ ĐĂNG KÝ 1 LỚP

### 📋 Định nghĩa

Một sinh viên **chỉ được đăng ký TỐI ĐA 1 LỚP** cho mỗi môn học (subject_id).

### ✅ Ví dụ HỢP LỆ

```python
# Đã đăng ký:
- IT3080-001 (subject_id = 1, Cơ sở dữ liệu)
- IT3170-001 (subject_id = 2, Lập trình mạng)

# Có thể đăng ký thêm:
✅ IT3090-001 (subject_id = 3, Kỹ thuật phần mềm)   # Môn mới
✅ IT3100-001 (subject_id = 4, Trí tuệ nhân tạo)    # Môn mới
```

### ❌ Ví dụ VI PHẠM

```python
# Đã đăng ký:
- IT3080-001 (subject_id = 1, Cơ sở dữ liệu)

# KHÔNG được đăng ký:
❌ IT3080-002 (subject_id = 1, Cơ sở dữ liệu)  # Trùng môn!
❌ IT3080-003 (subject_id = 1, Cơ sở dữ liệu)  # Trùng môn!
```

### 🔍 Thuật toán kiểm tra

```python
def filter_one_class_per_subject(candidates, registered):
    # Lấy danh sách subject_id đã đăng ký
    registered_subjects = {cls.subject_id for cls in registered}
    
    # Lọc chỉ giữ lại môn chưa đăng ký
    valid_classes = []
    for cls in candidates:
        if cls.subject_id NOT IN registered_subjects:
            valid_classes.append(cls)
    
    return valid_classes
```

---

## 🎯 LOGIC GỢI Ý TỔI THIỂU 5 LỚP

### Quy tắc đưa ra gợi ý

1. **Bước 1**: Lọc theo 2 luật tuyệt đối (ABSOLUTE RULES)
   - Loại bỏ lớp trùng lịch
   - Loại bỏ lớp trùng môn

2. **Bước 2**: Lọc theo tiêu chí ưu tiên (PREFERENCE RULES)
   - Buổi học (morning/afternoon)
   - Tránh học sớm/muộn
   - Tránh ngày cụ thể
   - Giáo viên ưu tiên

3. **Bước 3**: Xếp hạng và chọn gợi ý
   - Nếu có **≥ 5 lớp** thỏa mãn hoàn toàn preferences:
     ```
     → Trả về tất cả lớp thỏa mãn (đánh dấu ✅)
     ```
   
   - Nếu có **< 5 lớp** thỏa mãn hoàn toàn:
     ```
     → Trả về tất cả lớp thỏa mãn (✅)
     → Thêm các lớp có ít vi phạm nhất (đánh dấu ⚠️)
     → Đủ 5 gợi ý hoặc hết lớp khả dụng
     ```

### Ví dụ cụ thể

#### Case 1: Đủ lớp thỏa mãn

```python
Available classes after absolute rules: 15 classes
Fully satisfy preferences: 8 classes

Result:
✅ Class 1: IT3170-001 (0 violations)
✅ Class 2: IT3170-002 (0 violations)
✅ Class 3: IT3170-003 (0 violations)
✅ Class 4: IT3080-001 (0 violations)
✅ Class 5: IT3080-002 (0 violations)
✅ Class 6: IT3090-001 (0 violations)
✅ Class 7: IT3090-002 (0 violations)
✅ Class 8: IT3100-001 (0 violations)
```

#### Case 2: Không đủ 5 lớp thỏa mãn

```python
Preferences:
- Time period: morning
- Avoid early start: True
- Avoid days: [Saturday]

Available classes after absolute rules: 10 classes
Fully satisfy preferences: 2 classes
  ✅ IT3170-001 (0 violations)
  ✅ IT3080-001 (0 violations)

Classes with violations (sorted by fewest violations):
  ⚠️ IT3170-002 (1 violation: early start)
  ⚠️ IT3090-001 (1 violation: afternoon class)
  ⚠️ IT3100-001 (2 violations: afternoon + Saturday)

Result (top 5):
✅ IT3170-001 (0 violations)
✅ IT3080-001 (0 violations)
⚠️ IT3170-002 (1 violation: Starts too early 06:45)
⚠️ IT3090-001 (1 violation: Not morning class)
⚠️ IT3100-001 (2 violations: Not morning class, Has Saturday)
```

### 📊 Vi phạm tiêu chí (Preference Violations)

Các vi phạm được đếm như sau:

| Vi phạm | Mô tả | Điểm phạt |
|---------|-------|-----------|
| Wrong time period | Không đúng buổi học (morning/afternoon) | +1 |
| Early start | Học sớm hơn 08:00 | +1 |
| Late end | Kết thúc muộn hơn 17:00 | +1 |
| Avoided day | Mỗi ngày bị tránh | +1/day |
| Non-preferred day | Mỗi ngày không được ưu tiên | +1/day |
| Wrong teacher | Không phải giáo viên ưu tiên | +1 |

**Lưu ý**: Các vi phạm này **CHỈ ẢNH HƯỞNG XẾP HẠNG**, không loại bỏ lớp khỏi danh sách (khác với 2 luật tuyệt đối).

---

## 💻 Code Implementation

### Main function: suggest_classes()

```python
def suggest_classes(
    student_id: int,
    subject_ids: List[int],
    preferences: Dict,
    registered_classes: List[Dict] = [],
    min_suggestions: int = 5
) -> Dict:
    # Get all available classes
    all_classes = get_available_classes(student_id, subject_ids)
    
    # STEP 1: Apply ABSOLUTE RULES
    absolute_filtered = all_classes
    absolute_filtered = filter_no_schedule_conflict(absolute_filtered, registered_classes)
    absolute_filtered = filter_one_class_per_subject(absolute_filtered, registered_classes)
    
    # STEP 2: Apply PREFERENCE RULES
    preference_filtered = apply_preference_filters(absolute_filtered, preferences)
    
    # STEP 3: Rank and select
    fully_satisfied = rank_by_preferences(preference_filtered, preferences)
    
    # STEP 4: Add classes with violations if needed
    if len(fully_satisfied) < min_suggestions:
        remaining = [c for c in absolute_filtered if c not in fully_satisfied]
        with_violations = rank_by_preferences(remaining, preferences)
        needed = min_suggestions - len(fully_satisfied)
        fully_satisfied.extend(with_violations[:needed])
    
    return {
        'suggested_classes': fully_satisfied,
        'fully_satisfied': count(classes with 0 violations),
        'with_violations': count(classes with >0 violations)
    }
```

---

## 📝 Output Format

### Response format

```markdown
🎓 **GỢI Ý LỚP HỌC PHẦN**

📊 **TỔNG QUAN**
• Tổng số lớp phù hợp: 5 lớp
• Thỏa mãn hoàn toàn: 2 lớp
• Có vi phạm tiêu chí: 3 lớp

📚 **DANH SÁCH LỚP GỢI Ý**

**1. Lập trình mạng** (3 TC)

   **Lớp 1:** IT3170-001 - Lập trình mạng ✅
   • Thời gian: 08:00 - 10:00
   • Ngày học: Thứ 2, Thứ 4
   • Phòng: D3-301
   • Giảng viên: Nguyễn Văn A
   • Chỗ trống: 25/40
   • Phù hợp: Morning class, No avoided days, Ends before 17:00
   • Điểm ưu tiên: ⭐ 25/60

   **Lớp 2:** IT3170-002 - Lập trình mạng ⚠️ (1 vi phạm)
   • Thời gian: 06:45 - 09:15
   • Ngày học: Thứ 3, Thứ 5
   • Phòng: D3-302
   • Giảng viên: Nguyễn Văn B
   • Chỗ trống: 30/40
   • Vi phạm tiêu chí: Starts too early (06:45 < 08:00)
   • Điểm ưu tiên: ⭐ 15/60
```

---

## 🧪 Testing

Xem file test: `backend/app/tests/test_class_suggestion_rules.py`

Chạy test:
```bash
cd backend
python app/tests/test_class_suggestion_rules.py
```

Expected output:
```
✅ Test 1: Same day, same weeks, overlapping → CONFLICT
✅ Test 2: Same day, different weeks → NO CONFLICT
✅ Test 3: Same day, same weeks, no time overlap → NO CONFLICT
✅ Test 4: Different days → NO CONFLICT
✅ Filter no schedule conflict: OK (2/3 classes passed)
✅ Filter one class per subject: OK (2/4 classes passed)
✅ Count preference violations: OK
```

---

**Document Version:** 2.0  
**Last Updated:** December 2, 2025  
**Status:** ✅ Implemented & Tested
