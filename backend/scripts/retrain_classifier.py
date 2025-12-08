"""
Quick script to retrain TF-IDF classifier after updating intents.json
"""
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.chatbot.tfidf_classifier import TfidfIntentClassifier

if __name__ == "__main__":
    print("🔄 Retraining TF-IDF Intent Classifier...")
    
    classifier = TfidfIntentClassifier()
    
    print("✅ Classifier retrained successfully!")
    print(f"📊 Total intents: {len(classifier.intents)}")
    
    # Test some patterns
    test_questions = [
        "gợi ý lớp kỳ sau",
        "tôi không muốn học muộn",
        "tôi không muốn học đến 17h30",
        "các lớp kết thúc sớm",
        "gợi ý môn học kỳ này",
        "tôi nên đăng ký môn gì"
    ]
    
    print("\n🧪 Testing classification:")
    for q in test_questions:
        import asyncio
        result = asyncio.run(classifier.classify_intent(q))
        print(f"  • '{q}'")
        print(f"    → Intent: {result['intent']} (confidence: {result['confidence']})")
    
    print("\n✅ Done!")
