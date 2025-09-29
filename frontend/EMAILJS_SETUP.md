# Hướng dẫn cấu hình EmailJS

## 1. Tạo tài khoản EmailJS
1. Truy cập https://www.emailjs.com/
2. Đăng ký tài khoản miễn phí
3. Xác thực email

## 2. Tạo Email Service
1. Vào Dashboard > Email Services
2. Chọn "Add New Service" 
3. Chọn Gmail và kết nối với tài khoản Gmail của bạn
4. Lưu Service ID (ví dụ: service_jyg5mej)


## 3. Tạo Email Template
1. Vào Dashboard > Email Templates
2. Chọn "Create New Template"
3. Tạo template với các biến:
   - {{student_name}} - Tên sinh viên
   - {{student_id}} - MSSV
   - {{form_type}} - Loại biểu mẫu
   - {{form_content}} - Nội dung biểu mẫu
   - {{student_email}} - Email sinh viên
4. Lưu Template ID (ví dụ: template_fg0nqpf)

## 4. Lấy Public Key
1. Vào Dashboard > Account > General
2. Copy Public Key (ví dụ: user_def456)

## 5. Cấu hình trong code
Mở file `src/services/emailjs-service.ts` và cập nhật:

```typescript
const EMAIL_CONFIG = {
  serviceId: 'service_jyg5mej',      // Thay bằng Service ID của bạn
  templateId: 'template_fg0nqpf',    // Thay bằng Template ID của bạn  
  publicKey: '6o4vdH_ZvtsDI_SA8'          // Thay bằng Public Key của bạn
}
```

## 6. Template Email mẫu
Subject: Biểu mẫu: {{form_type}} - {{student_name}}

Nội dung:
```
Xin chào Admin,

Sinh viên {{student_name}} (MSSV: {{student_id}}) đã gửi {{form_type}}.

Thông tin chi tiết:
{{form_content}}

Email liên hệ: {{student_email}}

Trân trọng,
Hệ thống Student Portal
```

## 7. Test
Sau khi cấu hình xong, test bằng cách:
1. Mở http://localhost:5173/student/forms
2. Chọn một biểu mẫu
3. Điền thông tin và gửi
4. Kiểm tra email admin có nhận được không