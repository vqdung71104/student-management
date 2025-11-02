"""
Example script demonstrating Rasa Intent Classifier usage
Các ví dụ sử dụng Rasa classifier trong các tình huống khác nhau
"""
import asyncio
import sys
import os

# Add backend directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from app.chatbot.rasa_classifier import RasaIntentClassifier


async def example_1_basic_usage():
    """Example 1: Basic usage - Phân loại intent cơ bản"""
    print("\n" + "="*70)
    print("EXAMPLE 1: BASIC USAGE")
    print("="*70)
    
    # Initialize classifier
    classifier = RasaIntentClassifier()
    
    # Classify a single message
    message = "Tôi muốn đăng ký môn học"
    result = await classifier.classify_intent(message)
    
    print(f"\n💬 Message: \"{message}\"")
    print(f"🎯 Intent: {result['intent']}")
    print(f"📊 Confidence: {result['confidence']}")
    print(f"🔢 Score: {result['confidence_score']:.4f}")
    print(f"🔧 Method: {result['method']}")


async def example_2_batch_processing():
    """Example 2: Batch processing - Xử lý nhiều messages"""
    print("\n" + "="*70)
    print("EXAMPLE 2: BATCH PROCESSING")
    print("="*70)
    
    classifier = RasaIntentClassifier()
    
    messages = [
        "Xin chào!",
        "Tôi muốn đăng ký môn Giải tích 1",
        "Lớp nào phù hợp với tôi?",
        "Xem điểm của mình",
        "Cảm ơn bạn!"
    ]
    
    print(f"\n📋 Processing {len(messages)} messages...\n")
    
    for i, message in enumerate(messages, 1):
        result = await classifier.classify_intent(message)
        print(f"{i}. \"{message}\"")
        print(f"   ➜ {result['intent']} ({result['confidence']}, {result['confidence_score']:.4f})")


async def example_3_similarity_analysis():
    """Example 3: Similarity analysis - Phân tích độ tương đồng"""
    print("\n" + "="*70)
    print("EXAMPLE 3: SIMILARITY ANALYSIS")
    print("="*70)
    
    classifier = RasaIntentClassifier()
    
    message = "Tôi muốn hỏi về việc đăng ký lớp học"
    
    print(f"\n💬 Message: \"{message}\"\n")
    
    # Get all similarities
    similarities = classifier.get_all_similarities(message)
    
    print("📊 Top 5 similar intents:")
    for i, (intent, score) in enumerate(similarities[:5], 1):
        # Create a visual bar
        bar_length = int(score * 40)
        bar = "█" * bar_length + "░" * (40 - bar_length)
        print(f"{i}. {intent:35s} {score:.4f} {bar}")


async def example_4_confidence_levels():
    """Example 4: Understanding confidence levels"""
    print("\n" + "="*70)
    print("EXAMPLE 4: CONFIDENCE LEVELS")
    print("="*70)
    
    classifier = RasaIntentClassifier()
    
    test_cases = [
        ("Xin chào!", "Expected: High confidence for greeting"),
        ("Tôi muốn đăng ký môn học", "Expected: High confidence"),
        ("Có lớp nào không?", "Expected: Medium confidence (ambiguous)"),
        ("xyz123", "Expected: Low confidence or out_of_scope"),
    ]
    
    print("\n📊 Testing different confidence levels:\n")
    
    for message, expectation in test_cases:
        result = await classifier.classify_intent(message)
        
        confidence_emoji = {
            "high": "🟢",
            "medium": "🟡",
            "low": "🔴"
        }
        
        emoji = confidence_emoji.get(result['confidence'], "⚪")
        
        print(f"\n💬 \"{message}\"")
        print(f"   {expectation}")
        print(f"   {emoji} Actual: {result['confidence'].upper()} ({result['confidence_score']:.4f})")
        print(f"   Intent: {result['intent']}")


async def example_5_stats_and_config():
    """Example 5: Getting classifier statistics and configuration"""
    print("\n" + "="*70)
    print("EXAMPLE 5: STATS AND CONFIGURATION")
    print("="*70)
    
    classifier = RasaIntentClassifier()
    
    # Get statistics
    stats = classifier.get_stats()
    
    print("\n📊 Classifier Statistics:")
    print(f"   Total intents: {stats['total_intents']}")
    print(f"   Has Rasa installed: {stats['has_rasa']}")
    print(f"   Current method: {stats['method']}")
    
    print("\n⚙️  Thresholds:")
    for level, threshold in stats['thresholds'].items():
        print(f"   {level}: {threshold}")
    
    # Get configuration
    config = classifier.get_config()
    
    print("\n🔧 Configuration:")
    print(f"   Language: {config.get('language', 'N/A')}")
    print(f"   Pipeline components: {len(config.get('pipeline', []))}")


async def example_6_error_handling():
    """Example 6: Error handling and edge cases"""
    print("\n" + "="*70)
    print("EXAMPLE 6: ERROR HANDLING")
    print("="*70)
    
    classifier = RasaIntentClassifier()
    
    edge_cases = [
        "",  # Empty string
        "   ",  # Whitespace only
        "?????",  # Special characters
        None,  # None (will be handled in real usage)
    ]
    
    print("\n🧪 Testing edge cases:\n")
    
    for i, message in enumerate(edge_cases, 1):
        try:
            # Handle None case
            if message is None:
                message = ""
            
            result = await classifier.classify_intent(message)
            
            print(f"{i}. Input: {repr(message)}")
            print(f"   Result: {result['intent']} ({result['confidence']})")
        except Exception as e:
            print(f"{i}. Input: {repr(message)}")
            print(f"   ❌ Error: {str(e)}")


async def example_7_comparison_messages():
    """Example 7: Comparing similar messages"""
    print("\n" + "="*70)
    print("EXAMPLE 7: COMPARING SIMILAR MESSAGES")
    print("="*70)
    
    classifier = RasaIntentClassifier()
    
    # Messages with subtle differences
    message_groups = [
        [
            "Tôi muốn đăng ký môn học",
            "Tôi muốn đăng ký lớp học",
            "Tôi muốn đăng ký",
        ],
        [
            "Xem điểm",
            "Xem điểm số",
            "Xem kết quả học tập",
        ],
        [
            "Lịch học",
            "Thời khóa biểu",
            "Xem lịch",
        ]
    ]
    
    for group_idx, messages in enumerate(message_groups, 1):
        print(f"\n📋 Group {group_idx}:")
        
        for message in messages:
            result = await classifier.classify_intent(message)
            print(f"   \"{message}\"")
            print(f"   ➜ {result['intent']} ({result['confidence']}, {result['confidence_score']:.4f})")


async def example_8_real_conversation():
    """Example 8: Simulating a real conversation"""
    print("\n" + "="*70)
    print("EXAMPLE 8: REAL CONVERSATION SIMULATION")
    print("="*70)
    
    classifier = RasaIntentClassifier()
    
    conversation = [
        ("Student", "Xin chào!"),
        ("Bot", "[Greeting response]"),
        ("Student", "Tôi muốn hỏi về đăng ký môn học"),
        ("Bot", "[Registration guide response]"),
        ("Student", "Kỳ này tôi nên đăng ký môn gì?"),
        ("Bot", "[Subject suggestions response]"),
        ("Student", "Cảm ơn bạn!"),
        ("Bot", "[Thank you response]"),
    ]
    
    print("\n💬 Conversation Flow:\n")
    
    for speaker, message in conversation:
        if speaker == "Student":
            result = await classifier.classify_intent(message)
            print(f"👤 {speaker}: {message}")
            print(f"   🤖 Detected intent: {result['intent']} ({result['confidence']})")
        else:
            print(f"🤖 Bot: {message}")
        print()


async def example_9_performance_test():
    """Example 9: Simple performance test"""
    print("\n" + "="*70)
    print("EXAMPLE 9: PERFORMANCE TEST")
    print("="*70)
    
    classifier = RasaIntentClassifier()
    
    import time
    
    test_messages = [
        "Xin chào",
        "Đăng ký môn học",
        "Xem điểm",
        "Lịch học",
        "Cảm ơn",
    ]
    
    num_iterations = 10
    
    print(f"\n⏱️  Running {num_iterations} iterations with {len(test_messages)} messages each...\n")
    
    start_time = time.time()
    
    for _ in range(num_iterations):
        for message in test_messages:
            await classifier.classify_intent(message)
    
    total_time = time.time() - start_time
    total_messages = num_iterations * len(test_messages)
    avg_time = total_time / total_messages
    
    print(f"📊 Performance Results:")
    print(f"   Total messages: {total_messages}")
    print(f"   Total time: {total_time:.3f}s")
    print(f"   Average time: {avg_time:.4f}s per message")
    print(f"   Throughput: {total_messages/total_time:.2f} messages/second")


async def example_10_custom_thresholds():
    """Example 10: Understanding threshold impact"""
    print("\n" + "="*70)
    print("EXAMPLE 10: THRESHOLD IMPACT")
    print("="*70)
    
    classifier = RasaIntentClassifier()
    
    # Test message with medium confidence
    message = "Có lớp học nào không?"
    
    print(f"\n💬 Message: \"{message}\"\n")
    
    result = await classifier.classify_intent(message)
    
    print(f"🎯 Classification Result:")
    print(f"   Intent: {result['intent']}")
    print(f"   Confidence: {result['confidence']}")
    print(f"   Score: {result['confidence_score']:.4f}")
    
    print(f"\n📏 Current Thresholds:")
    for level, threshold in classifier.thresholds.items():
        print(f"   {level}: {threshold}")
    
    print(f"\n💡 Interpretation:")
    score = result['confidence_score']
    
    if score >= classifier.thresholds.get('high_confidence', 0.70):
        print(f"   Score {score:.4f} >= {classifier.thresholds.get('high_confidence', 0.70)} → HIGH confidence")
    elif score >= classifier.thresholds.get('medium_confidence', 0.50):
        print(f"   Score {score:.4f} >= {classifier.thresholds.get('medium_confidence', 0.50)} → MEDIUM confidence")
    else:
        print(f"   Score {score:.4f} < {classifier.thresholds.get('medium_confidence', 0.50)} → LOW confidence")


async def run_all_examples():
    """Run all examples"""
    examples = [
        example_1_basic_usage,
        example_2_batch_processing,
        example_3_similarity_analysis,
        example_4_confidence_levels,
        example_5_stats_and_config,
        example_6_error_handling,
        example_7_comparison_messages,
        example_8_real_conversation,
        example_9_performance_test,
        example_10_custom_thresholds,
    ]
    
    print("\n" + "="*70)
    print("🚀 RASA INTENT CLASSIFIER - USAGE EXAMPLES")
    print("="*70)
    
    for i, example_func in enumerate(examples, 1):
        try:
            await example_func()
            print()  # Extra spacing
        except Exception as e:
            print(f"\n❌ Example {i} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("✅ ALL EXAMPLES COMPLETED")
    print("="*70)


async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Rasa Intent Classifier Examples")
    parser.add_argument(
        "--example",
        type=int,
        choices=range(1, 11),
        help="Run a specific example (1-10)"
    )
    
    args = parser.parse_args()
    
    if args.example:
        example_map = {
            1: example_1_basic_usage,
            2: example_2_batch_processing,
            3: example_3_similarity_analysis,
            4: example_4_confidence_levels,
            5: example_5_stats_and_config,
            6: example_6_error_handling,
            7: example_7_comparison_messages,
            8: example_8_real_conversation,
            9: example_9_performance_test,
            10: example_10_custom_thresholds,
        }
        await example_map[args.example]()
    else:
        await run_all_examples()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Examples interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
