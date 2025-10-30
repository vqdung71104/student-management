"""
Test script để kiểm tra việc lưu trữ văn bản dài có ký tự đặc biệt trong trường description
"""
import requests
import json
from datetime import datetime, timedelta

# Văn bản test với ký tự đặc biệt
test_description = """I. Đối tượng được xét, tài trợ học bổng

Sinh viên đang học đại học hệ chính quy tại Đại học Bách khoa Hà Nội các ngành sau: Kỹ thuật Điện; Kỹ thuật Điều khiển - Tự động hoá; Kỹ thuật Điện tử - Viễn thông; CNTT: Khoa học Máy tính; CNTT: Kỹ thuật Máy tính; Khoa học dữ liệu và Trí tuệ nhân tạo ; An toàn không gian số - Cyber security; Hệ thông tin quản lý; Kỹ thuật hàng không

Loại học bổng và điều kiện đạt học bổng
Học bổng loại đặc biệt: 
Áp dụng đối với sinh viên thỏa mãn cả 2 điều kiện sau:

- Sinh viên đạt điểm GPA kì 2024.2 loại xuất sắc (từ 3,60 trở lên)) và điểm rèn luyện kì 2024.2 từ 80 trở lên;

- Sinh viên là người địa phương, sinh sống tại các khu vực VATM quản lý và đang thiếu lực lượng lao động (các đài trạm xa, sân bay địa phương, biển đảo,…) có nguyện vọng làm việc tại các khu vực nêu trên sau khi tốt nghiệp.

Học bổng loại xuất sắc:
Áp dụng đối với sinh viên thỏa mãn điều kiện sau:

- Sinh viên đạt điểm GPA kì 2024.2 loại xuất sắc và điểm rèn luyện kì 2024.2 từ 80 trở lên; có nguyện vọng làm việc tại VATM sau khi tốt nghiệp.

Học bổng loại giỏi:
Áp dụng đối với sinh viên đạt điểm GPA kì 2024.2 loại giỏi và điểm rèn luyện kì 2024.2 từ 80 trở lên; có nguyện vọng làm việc tại VATM sau khi tốt nghiệp.

III. Mức học bổng, số lượng học bổng

Mức học bổng
- Mức học bổng loại đặc biệt: 7.000.000 VNĐ/suất/năm 

- Mức học bổng loại xuất sắc: 5.000.000 VNĐ/suất/năm

- Mức học bổng loại giỏi: 3.000.000 VNĐ/suất/năm 

Số lượng học bổng năm 2025
- Học bổng loại đặc biệt: 03 suất 

- Học bổng loại xuất sắc: 05 suất

- Học bổng loại giỏi: 10 suất 

Tiêu chuẩn; phương thức xét, tài trợ học bổng
Xét theo thành tích học tập: Sinh viên đạt điểm trung bình học tập học kỳ tại thời điểm xét, tài trợ học bổng từ loại giỏi trở lên và điểm rèn luyện đạt loại giỏi hoặc tương đương trở lên.
Xét, tài trợ học bổng theo điểm từ cao xuống thấp đến hết số suất học bổng đã được xác định.
Nếu cùng mức học bổng thì sẽ căn cứ vào điểm học tập để xét thứ tự ưu tiên.
Nếu cùng mức học bổng và cùng điểm học tập thì sẽ căn cứ vào mức độ ưu tiên để xét thứ tự ưu tiên. Mức độ ưu tiên được quy định theo thứ tự như sau:
a) Ưu tiên sinh viên là người địa phương, sinh sống tại các khu vực VATM quản lý và đang thiếu lực lượng lao động (các đài trạm xa, sân bay địa phương, biển đảo,…) có nguyện vọng làm việc tại các khu vực nêu trên.
(Chi tiết các Đài Kiểm soát không lưu xem TẠI ĐÂY)

        b) Ưu tiên sinh viên có hoàn cảnh khó khăn (có xác nhận của địa phương): sinh viên mồ côi, khuyết tật, nghèo, cận nghèo.

II. Hướng dẫn đăng kí:

- Đăng kí trực tiếp trên QLĐT đến 23:55 ngày 14/10/2025."""

# Dữ liệu test scholarship
scholarship_data = {
    "title": "Học bổng VATM 2025",
    "type": "Học bổng Doanh nghiệp", 
    "slots": 18,
    "value_per_slot": 5000000,
    "sponsor": "VATM - Vietnam Air Traffic Management",
    "register_start_at": datetime.now().isoformat(),
    "register_end_at": (datetime.now() + timedelta(days=30)).isoformat(),
    "target_departments": "Kỹ thuật Điện, CNTT, Kỹ thuật hàng không",
    "target_courses": "2022, 2023, 2024",
    "target_programs": "Cử nhân kỹ thuật",
    "contact_person": "Phòng Đào tạo VATM",
    "contact_info": "email@vatm.vn, 024-xxx-xxxx",
    "description": test_description,
    "note": "Học bổng dành cho sinh viên có nguyện vọng làm việc tại VATM"
}

def test_scholarship_creation():
    """Test tạo scholarship với description dài"""
    try:
        # URL API endpoint
        url = "http://localhost:8000/scholarships/"
        
        # Headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Gửi request
        response = requests.post(
            url,
            json=scholarship_data,
            headers=headers,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            print("✅ Tạo scholarship thành công!")
            print(f"ID: {result.get('id')}")
            print(f"Title: {result.get('title')}")
            print(f"Description length: {len(result.get('description', ''))}")
            print("Description preview:", result.get('description', '')[:200] + "...")
            return result.get('id')
        else:
            print("❌ Lỗi khi tạo scholarship:")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Lỗi kết nối: {e}")
    except Exception as e:
        print(f"❌ Lỗi không mong muốn: {e}")

def test_scholarship_retrieval(scholarship_id):
    """Test lấy thông tin scholarship và kiểm tra description"""
    try:
        url = f"http://localhost:8000/scholarships/{scholarship_id}"
        response = requests.get(url)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Lấy thông tin scholarship thành công!")
            print(f"Description được lưu đầy đủ: {len(result.get('description', '')) == len(test_description)}")
            
            # So sánh nội dung
            saved_desc = result.get('description', '')
            if saved_desc == test_description:
                print("✅ Nội dung description được lưu chính xác!")
            else:
                print("❌ Nội dung description bị thay đổi:")
                print("Original length:", len(test_description))
                print("Saved length:", len(saved_desc))
                
        else:
            print(f"❌ Lỗi khi lấy scholarship: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    print("🚀 Bắt đầu test lưu trữ văn bản dài...")
    print(f"Độ dài văn bản test: {len(test_description)} ký tự")
    print("=" * 50)
    
    # Test tạo scholarship
    scholarship_id = test_scholarship_creation()
    
    if scholarship_id:
        print("=" * 50)
        # Test lấy lại thông tin
        test_scholarship_retrieval(scholarship_id)