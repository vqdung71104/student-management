"""
Test Intent Classification Accuracy and Performance
Tests Rasa NLU + TF-IDF Fallback classifier
"""
import sys
import time
sys.path.insert(0, 'C:/Users/Admin/student-management/backend')

from app.chatbot.rasa_classifier import RasaIntentClassifier
import asyncio


# Test cases with expected intents
TEST_CASES = [
    # Greeting
    ("xin chào", "greeting"),
    ("chào bạn", "greeting"),
    ("hello", "greeting"),
    ("hi", "greeting"),
    
    # Thanks
    ("cảm ơn", "thanks"),
    ("thanks", "thanks"),
    ("cám ơn bạn", "thanks"),
    
    # Grade view
    ("điểm của tôi", "grade_view"),
    ("xem điểm", "grade_view"),
    ("CPA của tôi", "grade_view"),
    ("xem điểm học kỳ 20241", "grade_view"),
    
    # Learned subjects view
    ("điểm các môn đã học", "learned_subjects_view"),
    ("xem điểm chi tiết", "learned_subjects_view"),
    ("điểm từng môn", "learned_subjects_view"),
    
    # Subject info
    ("thông tin môn IT4040", "subject_info"),
    ("môn tiên quyết của MI1114", "subject_info"),
    ("học phần Giải tích có bao nhiêu tín chỉ", "subject_info"),
    
    # Class info
    ("các lớp môn Giải tích", "class_info"),
    ("các lớp của môn IT4040", "class_info"),
    ("lớp học vào thứ 2", "class_info"),
    ("cho tôi các lớp thuộc học phần MI1114", "class_info"),
    ("lớp của học phần Lý thuyết mạch", "class_info"),
    ("các lớp của môn EM1180Q", "class_info"),
    ("xem thông tin lớp 161084", "class_info"),
    
    # Schedule view
    ("lịch học của tôi", "schedule_view"),
    ("các môn đã đăng ký", "schedule_view"),
    ("môn học kỳ này", "schedule_view"),
    ("xem thời khóa biểu", "schedule_view"),
    
    # Subject registration suggestion
    ("nên đăng ký môn nào", "subject_registration_suggestion"),
    ("môn nào nên học", "subject_registration_suggestion"),
    ("gợi ý môn học", "subject_registration_suggestion"),
    
    # Class registration suggestion
    ("nên học lớp nào", "class_registration_suggestion"),
    ("kỳ này nên học lớp nào", "class_registration_suggestion"),
    ("tôi nên đăng ký lớp nào", "class_registration_suggestion"),
    ("gợi ý lớp học", "class_registration_suggestion"),
    ("tôi nên học lớp nào của môn Giải tích", "class_registration_suggestion"),
]


async def test_intent_classification():
    """Test intent classification accuracy"""
    print("=" * 80)
    print("INTENT CLASSIFICATION TEST")
    print("=" * 80)
    
    # Initialize classifier
    print("\n[1] Initializing classifier...")
    classifier = RasaIntentClassifier()
    
    # Test each case
    print(f"\n[2] Testing {len(TEST_CASES)} cases...")
    print("-" * 80)
    
    correct = 0
    total = len(TEST_CASES)
    results = []
    
    total_time = 0
    confidence_distribution = {"high": 0, "medium": 0, "low": 0}
    
    for i, (message, expected_intent) in enumerate(TEST_CASES, 1):
        start_time = time.time()
        result = await classifier.classify_intent(message)
        elapsed = (time.time() - start_time) * 1000  # Convert to ms
        
        predicted_intent = result["intent"]
        confidence = result["confidence"]
        score = result.get("score", 0)
        
        is_correct = predicted_intent == expected_intent
        if is_correct:
            correct += 1
        
        confidence_distribution[confidence] += 1
        total_time += elapsed
        
        # Print result
        status = "✓" if is_correct else "✗"
        print(f"{status} [{i:2d}] {message:50s} | Expected: {expected_intent:30s} | "
              f"Got: {predicted_intent:30s} | Confidence: {confidence:6s} ({score:.2f}) | {elapsed:.1f}ms")
        
        results.append({
            "message": message,
            "expected": expected_intent,
            "predicted": predicted_intent,
            "correct": is_correct,
            "confidence": confidence,
            "score": score,
            "time_ms": elapsed
        })
    
    # Calculate metrics
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    accuracy = (correct / total) * 100
    avg_time = total_time / total
    
    print(f"\n📊 Overall Metrics:")
    print(f"   Total test cases: {total}")
    print(f"   Correct predictions: {correct}")
    print(f"   Incorrect predictions: {total - correct}")
    print(f"   Accuracy: {accuracy:.2f}%")
    print(f"   Average response time: {avg_time:.2f}ms")
    
    print(f"\n📈 Confidence Distribution:")
    print(f"   High confidence: {confidence_distribution['high']} ({confidence_distribution['high']/total*100:.1f}%)")
    print(f"   Medium confidence: {confidence_distribution['medium']} ({confidence_distribution['medium']/total*100:.1f}%)")
    print(f"   Low confidence: {confidence_distribution['low']} ({confidence_distribution['low']/total*100:.1f}%)")
    
    # Show errors
    errors = [r for r in results if not r["correct"]]
    if errors:
        print(f"\n❌ Errors ({len(errors)}):")
        for err in errors:
            print(f"   Message: {err['message']}")
            print(f"   Expected: {err['expected']}, Got: {err['predicted']}")
            print(f"   Confidence: {err['confidence']} ({err['score']:.2f})")
            print()
    
    # Performance by intent
    print(f"\n📋 Performance by Intent:")
    intent_stats = {}
    for r in results:
        intent = r["expected"]
        if intent not in intent_stats:
            intent_stats[intent] = {"total": 0, "correct": 0}
        intent_stats[intent]["total"] += 1
        if r["correct"]:
            intent_stats[intent]["correct"] += 1
    
    for intent, stats in sorted(intent_stats.items()):
        acc = (stats["correct"] / stats["total"]) * 100
        print(f"   {intent:35s}: {stats['correct']}/{stats['total']} ({acc:.1f}%)")
    
    return {
        "accuracy": accuracy,
        "avg_time_ms": avg_time,
        "confidence_distribution": confidence_distribution,
        "results": results
    }


async def test_edge_cases():
    """Test edge cases and special scenarios"""
    print("\n" + "=" * 80)
    print("EDGE CASES TEST")
    print("=" * 80)
    
    classifier = RasaIntentClassifier()
    
    edge_cases = [
        # Typos
        ("cac lop mon giai tich", "class_info"),
        ("diem cua toi", "grade_view"),
        
        # Mixed language
        ("xem class môn IT4040", "class_info"),
        ("schedule của tôi", "schedule_view"),
        
        # Very short
        ("điểm", "grade_view"),
        ("lớp", "class_info"),
        
        # Very long
        ("tôi muốn xem thông tin chi tiết về các lớp học của môn Giải tích 1 trong học kỳ này", "class_info"),
        
        # Ambiguous
        ("xem", None),  # Too ambiguous
        ("thông tin", None),
    ]
    
    print(f"\nTesting {len(edge_cases)} edge cases...")
    print("-" * 80)
    
    for message, expected in edge_cases:
        result = await classifier.classify_intent(message)
        print(f"Message: {message:70s} | Intent: {result['intent']:30s} | "
              f"Confidence: {result['confidence']:6s} ({result.get('score', 0):.2f})")


if __name__ == "__main__":
    print("\n🧪 Starting Intent Classification Tests\n")
    
    # Run main test
    results = asyncio.run(test_intent_classification())
    
    # Run edge cases
    asyncio.run(test_edge_cases())
    
    print("\n✅ All tests completed!")
    print(f"\n📊 Final Accuracy: {results['accuracy']:.2f}%")
    print(f"⚡ Average Response Time: {results['avg_time_ms']:.2f}ms")
