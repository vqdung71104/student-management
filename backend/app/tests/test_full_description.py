#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests

# Test data với description đầy đủ như user cung cấp
test_data = {
    "title": "Học bổng KKHT kỳ 2023.2 trường cntt và tt",
    "type": "Học bổng nhà trường",
    "slots": 10,
    "value_per_slot": 10000000,
    "sponsor": "Trường cntt và tt",
    "register_start_at": "2025-10-04T00:00:00",
    "register_end_at": "2025-12-04T00:00:00",
    "target_departments": "SOICT",
    "target_courses": "2022,2023,2024",
    "target_programs": "ITE6",
    "contact_person": "Vũ Quang Dũng",
    "contact_info": "dung@gmail.com",
    "document_url": "https://storage.googleapis.com/hust-files/2025-09-30/1759197344549/6152002371321856/mau_%C4%91on_%C4%91on_%C4%91ang_ky_xet_hb_tai_tro_vatm_45.1k.doc",
    "description": """I. Đối tượng được xét, tài trợ học bổng

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

- Đăng kí trực tiếp trên QLĐT đến 23:55 ngày 14/10/2025.""",
    "note": ""
}

def test_full_description():
    try:
        url = "http://localhost:8000/api/scholarships/"
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        
        print("Testing with full description...")
        print(f"Description length: {len(test_data['description'])} characters")
        
        response = requests.post(url, json=test_data, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print("   Success!")
            result = response.json()
            print(f"Created scholarship ID: {result.get('id')}")
            print(f"Description saved length: {len(result.get('description', ''))}")
        else:
            print("  Failed!")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_full_description()