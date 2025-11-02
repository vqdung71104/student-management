"""
Test script for chatbot routes with Rasa classifier
Kiểm tra xem chatbot routes có hoạt động với Rasa classifier không
"""
import asyncio
import sys
import os

# Add backend directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from app.chatbot.rasa_classifier import RasaIntentClassifier


def print_separator(char="=", length=70):
    """Print a separator line"""
    print(f"\n{char * length}")


async def test_rasa_classifier_for_chatbot():
    """Test Rasa classifier với các messages điển hình của chatbot"""
    print_separator("=")
    print("🧪 TESTING RASA CLASSIFIER FOR CHATBOT ROUTES")
    print_separator("=")
    
    try:
        # Initialize classifier (như trong chatbot_routes.py)
        print("\n📋 Initializing Rasa Intent Classifier...")
        intent_classifier = RasaIntentClassifier()
        print("✅ Classifier initialized successfully")
        
        # Test messages
        test_cases = [
            {
                "message": "Xin chào!",
                "expected_intent": "greeting",
                "expected_confidence": "high"
            },
            {
                "message": "Tôi muốn đăng ký môn học",
                "expected_intent": "registration_guide",
                "expected_confidence": "high"
            },
            {
                "message": "Kỳ này tôi nên đăng ký môn gì?",
                "expected_intent": "subject_registration_suggestion",
                "expected_confidence": "high"
            },
            {
                "message": "Tôi nên đăng ký lớp nào?",
                "expected_intent": "class_registration_suggestion",
                "expected_confidence": "high"
            },
            {
                "message": "Xem điểm",
                "expected_intent": "grade_view",
                "expected_confidence": "high"
            },
            {
                "message": "Lịch học",
                "expected_intent": "schedule_view",
                "expected_confidence": "high"
            },
            {
                "message": "Cảm ơn bạn!",
                "expected_intent": "thanks",
                "expected_confidence": "high"
            },
        ]
        
        print(f"\n📋 Testing {len(test_cases)} messages...\n")
        
        correct_predictions = 0
        high_confidence_count = 0
        
        for i, test_case in enumerate(test_cases, 1):
            message = test_case["message"]
            expected_intent = test_case["expected_intent"]
            expected_confidence = test_case["expected_confidence"]
            
            # Classify intent (như trong chatbot endpoint)
            result = await intent_classifier.classify_intent(message)
            
            intent = result["intent"]
            confidence = result["confidence"]
            confidence_score = result["confidence_score"]
            
            # Check if prediction is correct
            is_correct = intent == expected_intent
            is_high_confidence = confidence == "high"
            
            if is_correct:
                correct_predictions += 1
                status = "✅"
            else:
                status = "❌"
            
            if is_high_confidence:
                high_confidence_count += 1
            
            print(f"{i}. {status} Message: \"{message}\"")
            print(f"   Expected: {expected_intent} ({expected_confidence})")
            print(f"   Got: {intent} ({confidence}, {confidence_score:.4f})")
            
            # Get friendly name (như trong chatbot route)
            if confidence == "high" and intent != "unknown":
                if intent == "greeting":
                    response_text = "Xin chào! Mình là trợ lý ảo của hệ thống quản lý sinh viên."
                elif intent == "thanks":
                    response_text = "Rất vui được giúp đỡ bạn!"
                else:
                    friendly_name = intent_classifier.get_intent_friendly_name(intent)
                    response_text = f"Bạn định {friendly_name} phải không?"
            else:
                response_text = "Mình chưa hiểu rõ câu hỏi của bạn."
            
            print(f"   Response: \"{response_text}\"")
            print()
        
        # Summary
        print_separator("=")
        print("📊 SUMMARY")
        print_separator("=")
        accuracy = (correct_predictions / len(test_cases)) * 100
        high_conf_rate = (high_confidence_count / len(test_cases)) * 100
        
        print(f"Correct predictions: {correct_predictions}/{len(test_cases)} ({accuracy:.1f}%)")
        print(f"High confidence: {high_confidence_count}/{len(test_cases)} ({high_conf_rate:.1f}%)")
        
        # Get stats
        stats = intent_classifier.get_stats()
        print(f"\n📊 Classifier Stats:")
        print(f"   Total intents: {stats['total_intents']}")
        print(f"   Method: {stats['method']}")
        print(f"   Has Rasa: {stats['has_rasa']}")
        
        # Test get_intent_friendly_name for all common intents
        print(f"\n📝 Intent Friendly Names:")
        common_intents = [
            "greeting", "thanks", "registration_guide",
            "subject_registration_suggestion", "class_registration_suggestion",
            "grade_view", "schedule_view", "prerequisite_check"
        ]
        
        for intent_tag in common_intents:
            friendly_name = intent_classifier.get_intent_friendly_name(intent_tag)
            print(f"   {intent_tag}: {friendly_name}")
        
        print_separator("=")
        
        if accuracy >= 70:
            print("✅ TEST PASSED: Accuracy >= 70%")
        else:
            print(f"⚠️  TEST WARNING: Accuracy {accuracy:.1f}% < 70%")
        
        print_separator("=")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


async def test_intents_list():
    """Test getting intents list (như endpoint /intents)"""
    print_separator("=")
    print("🧪 TESTING INTENTS LIST ENDPOINT")
    print_separator("=")
    
    try:
        classifier = RasaIntentClassifier()
        
        # Simulate the /intents endpoint logic
        intents_list = []
        for intent in classifier.intents.get("intents", []):
            intents_list.append({
                "tag": intent["tag"],
                "description": intent["description"],
                "examples": intent["patterns"][:3]
            })
        
        print(f"\n📋 Total intents: {len(intents_list)}\n")
        
        for i, intent_info in enumerate(intents_list[:5], 1):  # Show first 5
            print(f"{i}. Tag: {intent_info['tag']}")
            print(f"   Description: {intent_info['description']}")
            print(f"   Examples: {', '.join(intent_info['examples'])}")
            print()
        
        if len(intents_list) > 5:
            print(f"... and {len(intents_list) - 5} more intents")
        
        print_separator("=")
        print("✅ Intents list retrieved successfully")
        print_separator("=")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function"""
    print("\n" + "="*70)
    print("🚀 CHATBOT ROUTES - RASA CLASSIFIER INTEGRATION TEST")
    print("="*70)
    
    await test_rasa_classifier_for_chatbot()
    await test_intents_list()
    
    print("\n" + "="*70)
    print("✅ ALL TESTS COMPLETED")
    print("="*70)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
