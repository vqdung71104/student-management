 # HỆ THỐNG LUẬT ĐĂNG KÝ HỌC PHẦN VÀ LỚP

 ## I. LUẬT ĐĂNG KÝ HỌC PHẦN

 ### 1. Quy định tín chỉ theo học lực và kỳ học
 - Học kỳ chính:
	 - Sinh viên bình thường: 12 ≤ TC ≤ 24
	 - Cảnh báo mức 1: 10 ≤ TC ≤ 18
	 - Cảnh báo mức 2 trở lên hoặc chưa đạt ngoại ngữ: 8 ≤ TC ≤ 14
	 - Năm cuối: Không giới hạn tối thiểu
 - Học kỳ hè: tối đa 8 TC, không giới hạn tối thiểu

 ### 2. Luật ưu tiên gợi ý môn học
 - **Ưu tiên 1:** Học lại môn điểm F (bắt buộc)
 - **Ưu tiên 2:** Môn đúng lộ trình kỳ học (theo learning_semester)
 - **Ưu tiên 3:** Môn chính trị (6 môn SSH/EM bắt buộc)
 - **Ưu tiên 4:** Môn thể chất (chọn đủ 4/42 môn PE)
 - **Ưu tiên 5:** Môn bổ trợ (chọn đủ 3/9 môn bổ trợ)
 - **Ưu tiên 6:** Học nhanh (CPA > 3.4, đăng ký thêm nếu còn TC)
 - **Ưu tiên 7:** Cải thiện điểm (D/D+/C, nếu tổng TC ≤ 20)

 ### 3. Quy trình xử lý
 - Tính số kỳ, CPA, cảnh báo, các môn đã học
 - Tính giới hạn tín chỉ
 - Lọc và gợi ý môn theo thứ tự ưu tiên trên
 - Đảm bảo tổng TC nằm trong giới hạn

 ### 4. Cấu trúc code và config
 - Class: `SubjectSuggestionRuleEngine`
 - File config: `rules_config.json` (danh sách môn, giới hạn TC, ngưỡng điểm...)

 ---

## III. CÁCH TẠO COMBINATION (TỔ HỢP LỊCH HỌC)

### 1. Mục tiêu
Sinh tổ hợp các lịch học khả thi từ danh sách các lớp của nhiều môn, đảm bảo không trùng lịch và tối ưu theo tiêu chí cá nhân.

### 2. Quy trình sinh combination
- **Bước 1:** Gom tất cả các lớp khả dụng theo từng môn (classes_by_subject: {subject_id: [class1, class2, ...]})
- **Bước 2:** Dùng `itertools.product` để sinh ra mọi tổ hợp chọn 1 lớp cho mỗi môn.
- **Bước 3:** Với mỗi tổ hợp, kiểm tra xung đột lịch (trùng ngày, tuần, giờ học giữa các lớp).
- **Bước 4:** Chỉ giữ lại các combination không có xung đột (hoặc ưu tiên combination hợp lệ, nếu không có thì trả về một số tổ hợp có xung đột để tham khảo).
- **Bước 5:** Tính điểm cho từng combination dựa trên các tiêu chí: số ngày nghỉ, số ngày học liên tục, thời gian bắt đầu/kết thúc, số tín chỉ, tỷ lệ chỗ trống, v.v.
- **Bước 6:** Sắp xếp các combination theo điểm số giảm dần, trả về top N tổ hợp tốt nhất.

### 3. Thuật toán kiểm tra xung đột
- Hai lớp trùng lịch nếu:
	- Có ít nhất một ngày học trùng nhau
	- Có ít nhất một tuần học trùng nhau
	- Thời gian học overlap (giao nhau)

### 4. Chấm điểm tổ hợp
- Ưu tiên nhiều ngày nghỉ, nhiều ngày học liên tục, thời gian học phù hợp preference, số tín chỉ hợp lý, lớp còn nhiều chỗ trống...
- Có thể điều chỉnh trọng số từng tiêu chí qua config hoặc code.

### 5. Tham khảo code
- File: `app/services/schedule_combination_service.py`
- Class: `ScheduleCombinationGenerator`
- Hàm chính: `generate_combinations`, `has_time_conflicts`, `calculate_combination_score`

---

 ## II. LUẬT ĐĂNG KÝ LỚP HỌC PHẦN

 ### 1. Luật tuyệt đối (ABSOLUTE RULES)
 - **Luật 1:** Không trùng lịch học (cùng ngày, cùng tuần, thời gian overlap)
 - **Luật 2:** Mỗi môn chỉ đăng ký 1 lớp

 ### 2. Luật ưu tiên (PREFERENCE RULES)
 - Buổi học: morning/afternoon
 - Tránh học sớm (<8:25) hoặc muộn (>16:00)
 - Tránh ngày cụ thể (thứ 2-7)
 - Giáo viên ưu tiên
 - Tối ưu lịch: liên tục, nhiều ngày nghỉ, ngày học tập trung

 ### 3. Quy trình gợi ý lớp
 - Bước 1: Lọc theo luật tuyệt đối
 - Bước 2: Lọc theo tiêu chí ưu tiên
 - Bước 3: Xếp hạng, chọn tối thiểu 5 lớp (ưu tiên lớp thỏa mãn hoàn toàn, nếu thiếu thì thêm lớp ít vi phạm nhất)

 ### 4. Cấu trúc code và config
 - Class: `ClassSuggestionRuleEngine`
 - File config: `class_rules_config.json` (ngưỡng thời gian, câu hỏi preferences...)

 ### 5. Định dạng kết quả
 - Đánh dấu lớp thỏa mãn hoàn toàn (✅), lớp có vi phạm tiêu chí (⚠️)
 - Hiển thị lý do phù hợp/vi phạm, điểm ưu tiên

 ---

 ## III. Thuật toán kiểm tra trùng lịch & trùng môn

 - Trùng lịch: cùng ngày, cùng tuần, thời gian overlap
 - Trùng môn: chỉ đăng ký 1 lớp cho mỗi môn

 ---

 ## IV. Tích hợp chatbot

 - Intent: `subject_registration_suggestion` → gợi ý môn học
 - Intent: `class_registration_suggestion` → gợi ý lớp học phần theo preferences

 ---

 Tất cả các luật trên đều được triển khai đầy đủ trong mã nguồn, không thêm hoặc bớt. Nếu cần chi tiết từng luật, có thể tham khảo các file:  
 - Tập luật đăng ký học phần.md  
 - ABSOLUTE_RULES.md  
 - class_suggestion_rules.py  
 - subject_suggestion_rules.py  
