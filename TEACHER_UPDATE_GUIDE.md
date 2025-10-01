# Hướng dẫn sử dụng chức năng "Cập nhật giáo viên"

## 🎯 Mục đích
Chức năng này cho phép cập nhật thông tin giáo viên cho các lớp học đã có trong hệ thống bằng cách tải lên file Excel.

## 📍 Vị trí
- Truy cập: Admin Dashboard → Cập nhật thời khóa biểu
- Nút: "Cập nhật giáo viên" (màu xanh, biểu tượng tải lên)

## 📋 Yêu cầu file Excel

### Định dạng file
File Excel cần có các cột sau (có thể có header ở các dòng đầu):
- **Mã_lớp**: Mã lớp chính
- **Mã_lớp_kèm**: Mã lớp kèm theo  
- **Giảng viên giảng dạy**: Tên giáo viên

### Ví dụ cấu trúc:
```
Kỳ | Mã_lớp | Mã_lớp_kèm | Tên_HP | Giảng viên giảng dạy | ...
20251 | 161084 | 161084 | Kỹ năng mềm | Nguyễn Thị A | ...
20251 | 161085 | 161085 | Kỹ thuật điện | Nguyễn Văn A | ...
```

### Lưu ý quan trọng:
- ✅ Chỉ cập nhật lớp đã tồn tại trong database
- ✅ Tìm lớp dựa trên `class_id` hoặc `class_id_kem`
- ✅ Bỏ qua các dòng có ô trống trong 3 cột cần thiết
- ✅ Hệ thống tự động tìm header trong file
- ✅ Hỗ trợ file có nhiều dòng tiêu đề ở đầu

## 🚀 Cách sử dụng

### Bước 1: Chuẩn bị file
1. Mở file Excel thời khóa biểu
2. Đảm bảo có đầy đủ 3 cột: Mã_lớp, Mã_lớp_kèm, Giảng viên giảng dạy
3. Kiểm tra dữ liệu không có ô trống quan trọng

### Bước 2: Tải file lên
1. Click nút "Cập nhật giáo viên"
2. Chọn file Excel (.xlsx hoặc .xls)
3. Hoặc kéo thả file vào vùng upload

### Bước 3: Xác nhận
1. Click "Cập nhật" để xử lý
2. Chờ hệ thống xử lý file
3. Xem kết quả thông báo

## 📊 Kết quả xử lý

### Thông báo thành công:
```
Cập nhật thành công! X lớp đã được cập nhật giáo viên.
```

### Thông báo lỗi có thể gặp:
- **"Không tìm thấy header"**: File không có các cột bắt buộc
- **"Không tìm thấy dữ liệu hợp lệ"**: Tất cả dòng đều có ô trống
- **"Lỗi khi đọc file"**: File bị lỗi hoặc không đúng định dạng

## 🔧 Xử lý sự cố

### File không đọc được:
- Kiểm tra định dạng file (.xlsx/.xls)
- Đảm bảo file không bị khóa
- Thử mở file bằng Excel để kiểm tra

### Không tìm thấy lớp:
- Kiểm tra mã lớp trong file có khớp với database không
- Đảm bảo lớp đã được tạo trước đó trong hệ thống

### Một số lớp không được cập nhật:
- Xem chi tiết lỗi trong thông báo
- Kiểm tra các ô có dữ liệu đầy đủ không
- Kiểm tra mã lớp có chính xác không

## 📝 Lưu ý kỹ thuật

### Backend API:
- Endpoint: `POST /classes/update-teachers`
- Xử lý cập nhật theo batch
- Rollback nếu có lỗi nghiêm trọng

### Frontend:
- Hỗ trợ drag & drop
- Validation file trước khi upload
- Loading state trong quá trình xử lý

### Database:
- Cập nhật trường `teacher` trong bảng `classes`
- Tìm kiếm dựa trên `class_id` hoặc `class_id_kem`
- Transaction an toàn với rollback

## ✅ Checklist trước khi sử dụng

- [ ] File Excel có đúng format
- [ ] Các cột Mã_lớp, Mã_lớp_kèm, Giảng viên giảng dạy đầy đủ
- [ ] Dữ liệu trong các ô không có ký tự đặc biệt
- [ ] Các lớp cần cập nhật đã tồn tại trong hệ thống
- [ ] Backup dữ liệu trước khi cập nhật (nếu cần)

## 🆘 Liên hệ hỗ trợ
Nếu gặp vấn đề, vui lòng liên hệ admin với thông tin:
- File Excel đang sử dụng
- Thông báo lỗi chi tiết
- Số lượng bản ghi cần cập nhật