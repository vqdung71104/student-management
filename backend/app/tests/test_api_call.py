#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests

# Test data
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
    "description": "I. Đối tượng được xét, tài trợ học bổng\n\nSinh viên đang học đại học hệ chính quy tại Đại học Bách khoa Hà Nội các ngành sau: Kỹ thuật Điện; Kỹ thuật Điều khiển - Tự động hoá; Kỹ thuật Điện tử - Viễn thông; CNTT: Khoa học Máy tính; CNTT: Kỹ thuật Máy tính; Khoa học dữ liệu và Trí tuệ nhân tạo ; An toàn không gian số - Cyber security; Hệ thông tin quản lý; Kỹ thuật hàng không\n\nLoại học bổng và điều kiện đạt học bổng\nHọc bổng loại đặc biệt:\nÁp dụng đối với sinh viên thỏa mãn cả 2 điều kiện sau:\n\n- Sinh viên đạt điểm GPA kì 2024.2 loại xuất sắc (từ 3,60 trở lên)) và điểm rèn luyện kì 2024.2 từ 80 trở lên;\n\n- Sinh viên là người địa phương, sinh sống tại các khu vực VATM quản lý và đang thiếu lực lượng lao động (các đài trạm xa, sân bay địa phương, biển đảo,…) có nguyện vọng làm việc tại các khu vực nêu trên sau khi tốt nghiệp.",
    "note": ""
}

def test_api():
    try:
        url = "http://localhost:8000/api/scholarships/"
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        
        print("Sending API request...")
        response = requests.post(url, json=test_data, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print("   Success!")
            result = response.json()
            print(f"Created scholarship ID: {result.get('id')}")
        else:
            print("  Failed!")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_api()