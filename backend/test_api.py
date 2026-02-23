import requests
import json

# Test chatbot endpoint with different messages
base_url = "http://localhost:8000"

test_cases = [
    {"message": "xem điểm", "expected_intent": "grade_view"},
    {"message": "xem lịch học", "expected_intent": "schedule_view"},
    {"message": "gợi ý lớp học", "expected_intent": "class_registration_suggestion"},
    {"message": "xin chào", "expected_intent": "greeting"},
    {"message": "tôi nên đăng ký môn gì", "expected_intent": "subject_registration_suggestion"},
    {"message": "tôi nên đăng ký lớp nào", "expected_intent": "class_registration_suggestion"},
    {"message": "thông tin môn học", "expected_intent": "subject_info"},
    {"message": "cảm ơn", "expected_intent": "thanks"},
]

print("\n" + "="*100)
print("TESTING CHATBOT API WITH TEXT PREPROCESSING")
print("="*100 + "\n")

for i, test in enumerate(test_cases, 1):
    try:
        response = requests.post(
            f"{base_url}/chatbot/chat",
            json={"message": test["message"], "student_id": 1},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            intent = data.get("intent", "N/A")
            confidence = data.get("confidence", "N/A")
            
            status = "[PASS]" if intent == test["expected_intent"] else "[FAIL]"
            
            print(f"{i}. {status}")
            print(f"   Input:    {test['message']:40}")
            print(f"   Expected: {test['expected_intent']:40}")
            print(f"   Got:      {intent:40}")
            print(f"   Confidence: {confidence}")
            print("-" * 100)
        else:
            print(f"{i}. [ERROR] - Status code: {response.status_code}")
            print(f"   Input: {test['message']}")
            print("-" * 100)
            
    except Exception as e:
        print(f"{i}. [EXCEPTION]")
        print(f"   Input: {test['message']}")
        print(f"   Error: {str(e)}")
        print("-" * 100)

print("\nTest completed!")
