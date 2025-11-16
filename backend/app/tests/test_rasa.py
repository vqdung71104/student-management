"""
Test script cho Rasa NLU Intent Classifier
Kiểm tra hiệu năng và độ chính xác của Rasa classifier
"""
import asyncio
import sys
import os
from typing import List, Dict
import time

# Add backend directory to path (vì file đang ở app/tests/)
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
from app.chatbot.tfidf_classifier import TfidfIntentClassifier

# Load environment variables từ backend/.env
env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)


def print_separator(char="=", length=70):
    """Print a separator line"""
    print(f"\n{char * length}")


def print_result(message: str, result: Dict, time_taken: float = None):
    """Pretty print classification result"""
    print_separator()
    print(f"   Message: \"{message}\"")
    print(f"   Intent: {result['intent']}")
    print(f"   Confidence: {result['confidence']}")
    print(f"🔢 Confidence Score: {result['confidence_score']:.4f}")
    print(f"🔧 Method: {result['method']}")
    if time_taken:
        print(f"⏱️  Time: {time_taken:.3f}s")
    
    # Print top 3 alternatives if available
    if 'all_scores' in result and result['all_scores']:
        print(f"\n   Top 3 alternatives:")
        for i, score_data in enumerate(result['all_scores'][:3], 1):
            print(f"   {i}. {score_data['intent']}: {score_data['score']:.4f}")
    
    print_separator()


async def test_basic_classification():
    """Test basic classification với các message phổ biến"""
    print_separator("=")
    print("   TEST 1: BASIC CLASSIFICATION")
    print_separator("=")
    
    try:
        classifier = TfidfIntentClassifier()
    except Exception as e:
        print(f"  Failed to initialize Rasa classifier: {e}")
        return
    
    # Print classifier stats
    stats = classifier.get_stats()
    print("\n   Classifier Statistics:")
    print(f"   Total intents: {stats['total_intents']}")
    print(f"   Has Rasa: {stats['has_rasa']}")
    print(f"   Method: {stats['method']}")
    print(f"   Thresholds: {stats['thresholds']}")
    
    test_messages = [
        "Xin chào!",
        "Kỳ này tôi nên đăng ký môn gì?",
        "Tôi nên đăng ký học phần Giải tích 1 hay Giải tích 2?",
        "Tôi nên đăng ký lớp Triết sáng thứ 3 hay chiều thứ 4?",
        "Cho tôi danh sách các lớp môn Đại số?",
        "Bao giờ là thời điểm đăng ký lớp?",
        "Nên học lại môn Đại số tuyến tính hay Vật lý đại cương 1 trước?",
        "Em muốn xem điểm của mình",
        "Lịch học sau khi đăng ký như nào?",
        "Nên đăng ký lớp Nhật 6 ca 1 hay 2?",
        "Môn tiên quyết của IT4040 là gì?",
        "Cảm ơn bạn nhé",
    ]
    
    print(f"\n   Testing {len(test_messages)} messages...\n")
    
    results = []
    total_time = 0
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Testing: \"{message}\"")
        
        start_time = time.time()
        result = await classifier.classify_intent(message)
        time_taken = time.time() - start_time
        
        total_time += time_taken
        results.append((message, result, time_taken))
        
        print(f"   ➜ Intent: {result['intent']}")
        print(f"   ➜ Confidence: {result['confidence']} ({result['confidence_score']:.4f})")
        print(f"   ➜ Method: {result['method']}")
        print(f"   ➜ Time: {time_taken:.3f}s")
    
    # Summary
    print_separator("=")
    print("   SUMMARY")
    print_separator("=")
    print(f"Total messages: {len(test_messages)}")
    print(f"Total time: {total_time:.3f}s")
    print(f"Average time: {total_time/len(test_messages):.3f}s per message")
    
    # Count by confidence
    confidence_counts = {"high": 0, "medium": 0, "low": 0}
    for _, result, _ in results:
        confidence_counts[result['confidence']] += 1
    
    print(f"\nConfidence distribution:")
    print(f"   High: {confidence_counts['high']} ({confidence_counts['high']/len(test_messages)*100:.1f}%)")
    print(f"   Medium: {confidence_counts['medium']} ({confidence_counts['medium']/len(test_messages)*100:.1f}%)")
    print(f"   Low: {confidence_counts['low']} ({confidence_counts['low']/len(test_messages)*100:.1f}%)")


async def test_edge_cases():
    """Test với các edge cases"""
    print_separator("=")
    print("   TEST 2: EDGE CASES")
    print_separator("=")
    
    try:
        classifier = TfidfIntentClassifier()
    except Exception as e:
        print(f"  Failed to initialize Rasa classifier: {e}")
        return
    
    edge_cases = [
        "",  # Empty message
        "   ",  # Whitespace only
        "a",  # Single character
        "xyz123",  # Random string
        "Tôi muốn biết về điều gì đó mà không ai biết",  # Ambiguous
        "?????",  # Special characters only
        "Cảm ơn bạn đã giúp đỡ!",  # Thanking
        "Tạm biệt",  # Goodbye
    ]
    
    print(f"\n   Testing {len(edge_cases)} edge cases...\n")
    
    for i, message in enumerate(edge_cases, 1):
        print(f"\n{i}. Testing: \"{message}\"")
        
        start_time = time.time()
        result = await classifier.classify_intent(message)
        time_taken = time.time() - start_time
        
        print(f"   ➜ Intent: {result['intent']}")
        print(f"   ➜ Confidence: {result['confidence']} ({result['confidence_score']:.4f})")
        print(f"   ➜ Time: {time_taken:.3f}s")


async def test_all_intents():
    """Test với ít nhất một message từ mỗi intent"""
    print_separator("=")
    print("   TEST 3: COVERAGE TEST (ALL INTENTS)")
    print_separator("=")
    
    try:
        classifier = TfidfIntentClassifier()
    except Exception as e:
        print(f"  Failed to initialize Rasa classifier: {e}")
        return
    
    # Test messages covering different intents
    test_cases = {
        "greeting": ["Xin chào!", "Hello", "Chào bạn"],
        "registration_guide": ["Hướng dẫn đăng ký", "Cách đăng ký môn học"],
        "subject_registration_suggestion": ["Tôi nên đăng ký môn gì?", "Kỳ này học môn nào?"],
        "class_registration_suggestion": ["Tôi nên đăng ký lớp nào?", "Lớp nào phù hợp?"],
        "class_list": ["Danh sách lớp", "Các lớp môn Toán"],
        "schedule_view": ["Xem thời khóa biểu", "Lịch học của tôi"],
        "grade_view": ["Xem điểm", "Điểm số của tôi"],
        "prerequisite_check": ["Môn tiên quyết", "Điều kiện môn học"],
        "thanks": ["Cảm ơn", "Thank you"],
        "goodbye": ["Tạm biệt", "Bye"],
    }
    
    correct_predictions = 0
    total_predictions = 0
    
    for expected_intent, messages in test_cases.items():
        print(f"\n📌 Testing intent: {expected_intent}")
        
        for message in messages:
            result = await classifier.classify_intent(message)
            predicted_intent = result['intent']
            
            total_predictions += 1
            is_correct = predicted_intent == expected_intent
            
            if is_correct:
                correct_predictions += 1
                status = "  "
            else:
                status = " "
            
            print(f"   {status} \"{message}\"")
            print(f"      Expected: {expected_intent}")
            print(f"      Got: {predicted_intent} ({result['confidence']}, {result['confidence_score']:.4f})")
    
    # Accuracy summary
    print_separator("=")
    print("   ACCURACY SUMMARY")
    print_separator("=")
    accuracy = correct_predictions / total_predictions * 100 if total_predictions > 0 else 0
    print(f"Correct predictions: {correct_predictions}/{total_predictions}")
    print(f"Accuracy: {accuracy:.2f}%")


async def test_similarity_scores():
    """Test lấy similarity scores với tất cả intents"""
    print_separator("=")
    print("   TEST 4: SIMILARITY SCORES")
    print_separator("=")
    
    try:
        classifier = TfidfIntentClassifier()
    except Exception as e:
        print(f"  Failed to initialize Rasa classifier: {e}")
        return
    
    test_messages = [
        "Tôi muốn đăng ký môn học",
        "Làm sao để xem điểm?",
        "Lịch học như thế nào?",
    ]
    
    for message in test_messages:
        print(f"\n   Message: \"{message}\"")
        
        similarities = classifier.get_all_similarities(message)
        
        print(f"   Top 5 similar intents:")
        for i, (intent, score) in enumerate(similarities[:5], 1):
            bar_length = int(score * 40)
            bar = "█" * bar_length + "░" * (40 - bar_length)
            print(f"   {i}. {intent:30s} {score:.4f} {bar}")


async def test_performance():
    """Test hiệu năng với nhiều message"""
    print_separator("=")
    print("   TEST 5: PERFORMANCE TEST")
    print_separator("=")
    
    try:
        classifier = TfidfIntentClassifier()
    except Exception as e:
        print(f"  Failed to initialize Rasa classifier: {e}")
        return
    
    # Generate test messages
    test_messages = [
        "Xin chào",
        "Hướng dẫn đăng ký",
        "Tôi nên học môn gì?",
        "Lớp nào phù hợp?",
        "Xem điểm",
    ] * 20  # Repeat 20 times = 100 messages
    
    print(f"\n⏱️  Testing with {len(test_messages)} messages...")
    
    start_time = time.time()
    
    for message in test_messages:
        await classifier.classify_intent(message)
    
    total_time = time.time() - start_time
    avg_time = total_time / len(test_messages)
    
    print(f"\n   Performance Results:")
    print(f"   Total messages: {len(test_messages)}")
    print(f"   Total time: {total_time:.3f}s")
    print(f"   Average time: {avg_time:.4f}s per message")
    print(f"   Throughput: {len(test_messages)/total_time:.2f} messages/second")


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("🚀 RASA NLU INTENT CLASSIFIER - COMPREHENSIVE TESTS")
    print("="*70)
    
    tests = [
        ("Basic Classification", test_basic_classification),
        ("Edge Cases", test_edge_cases),
        ("All Intents Coverage", test_all_intents),
        ("Similarity Scores", test_similarity_scores),
        ("Performance", test_performance),
    ]
    
    for i, (test_name, test_func) in enumerate(tests, 1):
        print(f"\n\n{'='*70}")
        print(f"TEST {i}/{len(tests)}: {test_name.upper()}")
        print(f"{'='*70}")
        
        try:
            await test_func()
        except Exception as e:
            print(f"\n  Test failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n\n" + "="*70)
    print("   ALL TESTS COMPLETED")
    print("="*70)


async def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Rasa NLU Intent Classifier")
    parser.add_argument(
        "--test",
        choices=["basic", "edge", "coverage", "similarity", "performance", "all"],
        default="all",
        help="Which test to run"
    )
    
    args = parser.parse_args()
    
    if args.test == "basic":
        await test_basic_classification()
    elif args.test == "edge":
        await test_edge_cases()
    elif args.test == "coverage":
        await test_all_intents()
    elif args.test == "similarity":
        await test_similarity_scores()
    elif args.test == "performance":
        await test_performance()
    else:
        await run_all_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n   Tests interrupted by user")
    except Exception as e:
        print(f"\n\n  Fatal error: {e}")
        import traceback
        traceback.print_exc()

