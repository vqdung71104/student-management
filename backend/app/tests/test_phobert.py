"""
Test script để so sánh hiệu năng giữa PhoBERT và Gemini
"""
import asyncio
import sys
import os
from typing import List, Dict

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from app.chatbot.phobert_classifier import PhoBERTIntentClassifier
from app.chatbot.intent_classifier import IntentClassifier
from app.chatbot.hybrid_classifier import HybridIntentClassifier

# Load environment variables
load_dotenv()


def print_result(method: str, message: str, result: Dict, time_taken: float = None):
    """Pretty print classification result"""
    print(f"\n{'='*70}")
    print(f"📝 Method: {method}")
    print(f"💬 Message: \"{message}\"")
    print(f"🎯 Intent: {result['intent']}")
    print(f"📊 Confidence: {result['confidence']}")
    if 'similarity_score' in result:
        print(f"🔢 Similarity Score: {result['similarity_score']:.4f}")
    if time_taken:
        print(f"⏱️  Time: {time_taken:.3f}s")
    print(f"{'='*70}")


async def test_phobert_only():
    """Test PhoBERT classifier"""
    print("\n" + "="*70)
    print("🧪 TESTING PHOBERT CLASSIFIER")
    print("="*70)
    
    try:
        classifier = PhoBERTIntentClassifier()
    except Exception as e:
        print(f"❌ Failed to initialize PhoBERT: {e}")
        return
    
    test_messages = [
        "Xin chào!",
        "Kỳ này tôi nên đăng ký môn gì?",
        "Tôi nên đăng ký lớp Toán cao cấp 1 hay lớp Toán A1?",
        "Em muốn xem điểm của mình",
        "Lịch học tuần này như thế nào?",
        "Cho em hỏi về học bổng",
        "Môn tiên quyết của IT4040 là gì?",
        "Cảm ơn bạn nhé",
    ]
    
    print(f"\n📋 Testing {len(test_messages)} messages...\n")
    
    import time
    for i, message in enumerate(test_messages, 1):
        start_time = time.time()
        result = await classifier.classify_intent(message)
        time_taken = time.time() - start_time
        
        print(f"\n{i}. Message: \"{message}\"")
        print(f"   Intent: {result['intent']}")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Similarity: {result['similarity_score']:.4f}")
        print(f"   Time: {time_taken:.3f}s")
        
        # Show top 3 similar intents
        similarities = classifier.get_all_similarities(message)
        print(f"   Top 3: {similarities[:3]}")


async def test_hybrid_classifier():
    """Test Hybrid classifier"""
    print("\n" + "="*70)
    print("🧪 TESTING HYBRID CLASSIFIER (PhoBERT + Gemini)")
    print("="*70)
    
    try:
        classifier = HybridIntentClassifier(use_phobert=True, use_gemini=True)
    except Exception as e:
        print(f"❌ Failed to initialize Hybrid classifier: {e}")
        return
    
    test_messages = [
        "Xin chào bạn!",
        "Kỳ này em nên đăng ký môn nào?",
        "Tôi nên học lớp nào của môn Toán?",
        "Xem điểm số",
        "Thời khóa biểu",
        "Học bổng",
        "Môn tiên quyết IT4040",
        "Thanks!",
        "Hôm nay trời đẹp quá",  # Unknown
    ]
    
    print(f"\n📋 Testing {len(test_messages)} messages...\n")
    
    import time
    for i, message in enumerate(test_messages, 1):
        start_time = time.time()
        result = await classifier.classify_intent(message)
        time_taken = time.time() - start_time
        
        print(f"\n{i}. Message: \"{message}\"")
        print(f"   Intent: {result['intent']}")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Method: {result.get('method', 'unknown')}")
        if 'similarity_score' in result:
            print(f"   Similarity: {result['similarity_score']:.4f}")
        print(f"   Time: {time_taken:.3f}s")


async def test_comparison():
    """So sánh PhoBERT vs Gemini vs Hybrid"""
    print("\n" + "="*70)
    print("🔬 COMPARISON: PhoBERT vs Gemini vs Hybrid")
    print("="*70)
    
    # Initialize classifiers
    try:
        phobert = PhoBERTIntentClassifier()
        gemini = IntentClassifier()
        hybrid = HybridIntentClassifier(use_phobert=True, use_gemini=True)
    except Exception as e:
        print(f"❌ Failed to initialize classifiers: {e}")
        return
    
    test_messages = [
        "Kỳ này tôi nên đăng ký môn gì?",
        "Em muốn xem kết quả học tập",
        "Lớp học nào phù hợp với em?",
    ]
    
    import time
    for message in test_messages:
        print(f"\n{'='*70}")
        print(f"💬 Testing: \"{message}\"")
        print(f"{'='*70}")
        
        # PhoBERT
        start = time.time()
        phobert_result = await phobert.classify_intent(message)
        phobert_time = time.time() - start
        print(f"\n🤖 PhoBERT:")
        print(f"   Intent: {phobert_result['intent']}")
        print(f"   Confidence: {phobert_result['confidence']}")
        print(f"   Similarity: {phobert_result['similarity_score']:.4f}")
        print(f"   Time: {phobert_time:.3f}s")
        
        # Gemini
        start = time.time()
        gemini_result = await gemini.classify_intent(message)
        gemini_time = time.time() - start
        print(f"\n🌟 Gemini:")
        print(f"   Intent: {gemini_result['intent']}")
        print(f"   Confidence: {gemini_result['confidence']}")
        print(f"   Time: {gemini_time:.3f}s")
        
        # Hybrid
        start = time.time()
        hybrid_result = await hybrid.classify_intent(message)
        hybrid_time = time.time() - start
        print(f"\n🔀 Hybrid:")
        print(f"   Intent: {hybrid_result['intent']}")
        print(f"   Confidence: {hybrid_result['confidence']}")
        print(f"   Method: {hybrid_result.get('method', 'unknown')}")
        print(f"   Time: {hybrid_time:.3f}s")
        
        # Summary
        print(f"\n📊 Summary:")
        print(f"   Agreement: PhoBERT={phobert_result['intent']}, "
              f"Gemini={gemini_result['intent']}, "
              f"Hybrid={hybrid_result['intent']}")
        print(f"   Speed: PhoBERT={phobert_time:.3f}s, "
              f"Gemini={gemini_time:.3f}s, "
              f"Hybrid={hybrid_time:.3f}s")


async def main():
    """Main test function"""
    print("\n" + "🚀"*35)
    print("CHATBOT INTENT CLASSIFIER TESTING")
    print("🚀"*35)
    
    while True:
        print("\n📋 Choose test mode:")
        print("1. Test PhoBERT only")
        print("2. Test Hybrid (PhoBERT + Gemini)")
        print("3. Compare all methods")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            await test_phobert_only()
        elif choice == "2":
            await test_hybrid_classifier()
        elif choice == "3":
            await test_comparison()
        elif choice == "4":
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice!")


if __name__ == "__main__":
    asyncio.run(main())
