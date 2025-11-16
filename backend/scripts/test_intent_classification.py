"""
Quick test for intent classification on "các lớp Giải tích 1"
"""
import sys
sys.path.insert(0, 'C:/Users/Admin/student-management/backend')

import asyncio
from app.chatbot.tfidf_classifier import TfidfIntentClassifier


async def test():
    classifier = TfidfIntentClassifier()
    
    test_cases = [
        "các lớp Giải tích 1",
        "các lớp Giải tích I",
        "cho tôi thông tin các lớp môn học Giải tích I",
        "tôi nên học lớp nào của môn Giải tích",
        "kỳ này nên học lớp nào",
        "các lớp môn Lập trình mạng",
    ]
    
    print("=" * 80)
    print("INTENT CLASSIFICATION TEST - class_info vs class_registration_suggestion")
    print("=" * 80)
    
    for msg in test_cases:
        result = await classifier.classify_intent(msg)
        intent = result['intent']
        confidence = result['confidence']
        score = result.get('score', 0)
        
        # Expected
        if "nên học" in msg or "nên đăng ký" in msg:
            expected = "class_registration_suggestion"
        else:
            expected = "class_info"
        
        status = "✓" if intent == expected else "✗"
        
        print(f"\n{status} Message: {msg}")
        print(f"  Intent: {intent} (expected: {expected})")
        print(f"  Confidence: {confidence} ({score:.2f})")


if __name__ == "__main__":
    asyncio.run(test())
