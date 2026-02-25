# Hướng dẫn sử dụng tính năng xuất Excel

## Tổng quan

Tính năng xuất Excel cho phép sinh viên tải về file Excel (.xlsx) chứa chi tiết phương án lịch học từ chatbot. File Excel có thể mở trực tiếp trên:
- ✅ Google Sheets (kéo thả vào Google Drive)
- ✅ Microsoft Excel Online (OneDrive/Office 365)
- ✅ Microsoft Excel Desktop

## Cách sử dụng

### 1. Hỏi chatbot về gợi ý lịch học

Mở chatbot và hỏi về gợi ý lịch học, ví dụ:
- "Gợi ý lịch học cho tôi"
- "Tôi muốn đăng ký lớp học kỳ này"
- "Gợi ý lớp học buổi chiều"

### 2. Xem các phương án

Chatbot sẽ hiển thị 3 phương án lịch học tối ưu với:
- Điểm đánh giá
- Tổng quan (số môn, tín chỉ, ngày học)
- Bảng chi tiết lớp học

### 3. Tải file Excel

Mỗi phương án có nút **"📥 Tải Excel"** ở góc phải header.

Click vào nút này để tải file Excel về máy.

### 4. Mở file Excel

#### Cách 1: Mở bằng Google Sheets
1. Mở Google Drive (drive.google.com)
2. Kéo thả file Excel vào Google Drive
3. Double-click file để mở bằng Google Sheets
4. File sẽ tự động convert và hiển thị đầy đủ format

#### Cách 2: Mở bằng Excel Online
1. Mở OneDrive (onedrive.live.com)
2. Upload file Excel
3. Click vào file để mở bằng Excel Online
4. Có thể chỉnh sửa trực tiếp trên trình duyệt

#### Cách 3: Mở bằng Microsoft Excel Desktop
1. Double-click file Excel đã tải về
2. File sẽ mở trong Microsoft Excel
3. Có thể chỉnh sửa và lưu lại

## Nội dung file Excel

File Excel bao gồm 2 sheet:

### Sheet 1: Tổng quan
- Thông tin sinh viên (kỳ học, CPA)
- Điểm phương án
- Các chỉ số lịch học:
  - Tổng số môn và tín chỉ
  - Số ngày học/nghỉ
  - Giờ học sớm nhất/muộn nhất
  - Trung bình giờ/ngày

### Sheet 2: Chi tiết lớp học
Bảng chi tiết với các cột:
- **Mã lớp**: Mã lớp học
- **Tên lớp**: Tên môn học
- **Thời gian**: Giờ bắt đầu - kết thúc
- **Ngày học**: Thứ trong tuần
- **Tuần học**: Các tuần học trong kỳ
- **Phòng**: Phòng học
- **Giáo viên**: Tên giảng viên
- **Ghi chú**: Lý do ưu tiên (nếu có)

## Tính năng nổi bật

✨ **Format đẹp mắt**
- Header màu xanh với font trắng
- Border rõ ràng
- Cột tự động điều chỉnh độ rộng

✨ **Dễ dàng chia sẻ**
- Tải về và gửi cho bạn bè
- Upload lên Google Drive để xem online
- In ra giấy để tham khảo

✨ **Có thể chỉnh sửa**
- Thêm ghi chú cá nhân
- Highlight các lớp quan trọng
- Tạo bản sao để so sánh các phương án

## Lưu ý

> [!TIP]
> Nên tải về cả 3 phương án để so sánh và chọn phương án phù hợp nhất.

> [!NOTE]
> File Excel được tạo động từ dữ liệu chatbot, không lưu trên server. Mỗi lần tải sẽ tạo file mới.

> [!IMPORTANT]
> Tên file có format: `Phuong_An_X_Lich_Hoc.xlsx` (X là số phương án)

## Troubleshooting

### File không tải về được
- Kiểm tra trình duyệt có chặn popup không
- Thử lại với trình duyệt khác
- Kiểm tra kết nối internet

### File mở không đúng format
- Đảm bảo file có đuôi `.xlsx`
- Thử mở bằng Google Sheets thay vì Excel
- Kiểm tra phiên bản Excel (cần Excel 2007 trở lên)

### Không thấy nút "Tải Excel"
- Đảm bảo đã hỏi chatbot về gợi ý lịch học
- Refresh trang và thử lại
- Kiểm tra console log xem có lỗi không

## Hỗ trợ

Nếu gặp vấn đề, vui lòng liên hệ:
- Email: support@example.com
- Hoặc báo lỗi trực tiếp trong chatbot
