import asyncio
from app.chatbot.tfidf_classifier import TfidfIntentClassifier
from app.services.text_preprocessor import get_text_preprocessor

async def test_intent_classification():
    classifier = TfidfIntentClassifier()
    preprocessor = get_text_preprocessor()
    
    test_cases = [
        "xem điểm",
        "xem lịch học",
        "gợi ý lớp học",
        "xin chào",
        "tôi nên đăng ký môn gì",
        "tôi nên đăng ký lớp nào",
        "thông tin môn học",
        "cảm ơn"
    ]
    
    print("\n" + "="*80)
    print("TESTING INTENT CLASSIFICATION WITH TEXT PREPROCESSING")
    print("="*80 + "\n")
    
    for test in test_cases:
        # Preprocess
        normalized = preprocessor.preprocess(test)
        
        # Classify
        result = await classifier.classify_intent(normalized)
        
        print(f"Input:      {test:40}")
        if normalized != test:
            print(f"Normalized: {normalized:40}")
        print(f"Intent:     {result['intent']:40}")
        print(f"Confidence: {result['confidence']:10} (score: {result.get('confidence_score', 0):.3f})")
        print(f"Method:     {result.get('method', 'N/A')}")
        print("-" * 80)

if __name__ == "__main__":
    asyncio.run(test_intent_classification())
