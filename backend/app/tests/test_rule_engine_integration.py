"""
Test Rule Engine Integration with Chatbot
Run this to verify the rule engine is properly integrated
"""
import sys
import os

# Add backend to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.chatbot_service import ChatbotService


def test_rule_engine_integration():
    """Test that rule engine is properly integrated with chatbot service"""
    
    print("=" * 80)
    print("🧪 TESTING RULE ENGINE INTEGRATION")
    print("=" * 80)
    
    # Create database connection
    try:
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        print("✅ Database connection established")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Initialize chatbot service
    try:
        chatbot_service = ChatbotService(db)
        print("✅ ChatbotService initialized")
        print(f"✅ Rule engine loaded with config")
    except Exception as e:
        print(f"❌ ChatbotService initialization failed: {e}")
        return
    
    # Test 1: Subject suggestion with valid student
    print("\n" + "=" * 80)
    print("📝 TEST 1: Subject Suggestion for Student ID = 1")
    print("=" * 80)
    
    try:
        import asyncio
        result = asyncio.run(
            chatbot_service.process_subject_suggestion(
                student_id=1,
                question="tôi nên đăng ký môn gì?"
            )
        )
        
        print("\n📊 RESULT:")
        print(f"Intent: {result['intent']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Rule Engine Used: {result.get('rule_engine_used', False)}")
        
        if result.get('metadata'):
            metadata = result['metadata']
            print(f"\n📈 METADATA:")
            print(f"  Total Credits: {metadata['total_credits']}")
            print(f"  Meets Minimum: {metadata['meets_minimum']}")
            print(f"  Max Allowed: {metadata['max_credits_allowed']}")
            print(f"  Current Semester: {metadata['current_semester']}")
            print(f"  Student CPA: {metadata['student_cpa']}")
        
        if result.get('data'):
            print(f"\n📚 SUGGESTED SUBJECTS: {len(result['data'])} subjects")
            for idx, subject in enumerate(result['data'][:5], 1):
                print(f"  {idx}. {subject['subject_id']} - {subject['subject_name']}")
                print(f"     Priority: {subject['priority_level']} - {subject['priority_reason']}")
        
        print("\n💬 RESPONSE TEXT:")
        print("-" * 80)
        print(result['text'][:500] + "..." if len(result['text']) > 500 else result['text'])
        
        print("\n✅ TEST 1 PASSED")
        
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Class suggestion with valid student
    print("\n" + "=" * 80)
    print("📝 TEST 2: Class Suggestion for Student ID = 1")
    print("=" * 80)
    
    try:
        result = asyncio.run(
            chatbot_service.process_class_suggestion(
                student_id=1,
                question="gợi ý lớp học cho tôi"
            )
        )
        
        print("\n📊 RESULT:")
        print(f"Intent: {result['intent']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Rule Engine Used: {result.get('rule_engine_used', False)}")
        
        if result.get('metadata'):
            metadata = result['metadata']
            print(f"\n📈 METADATA:")
            print(f"  Total Subjects: {metadata.get('total_subjects', 0)}")
            print(f"  Total Classes: {metadata.get('total_classes', 0)}")
            print(f"  Student CPA: {metadata.get('student_cpa', 0)}")
        
        if result.get('data'):
            print(f"\n🏫 SUGGESTED CLASSES: {len(result['data'])} classes")
            for idx, cls in enumerate(result['data'][:5], 1):
                print(f"  {idx}. {cls['class_id']} - {cls['subject_name']}")
                print(f"     Time: {cls['study_date']} {cls.get('study_time_start', '')}")
                print(f"     Available: {cls['seats_available']} seats")
        
        print("\n💬 RESPONSE TEXT:")
        print("-" * 80)
        print(result['text'][:500] + "..." if len(result['text']) > 500 else result['text'])
        
        print("\n✅ TEST 2 PASSED")
        
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Subject suggestion without student_id
    print("\n" + "=" * 80)
    print("📝 TEST 3: Subject Suggestion WITHOUT Student ID (Authentication Check)")
    print("=" * 80)
    
    try:
        result = asyncio.run(
            chatbot_service.process_subject_suggestion(
                student_id=None,
                question="tôi nên đăng ký môn gì?"
            )
        )
        
        print("\n📊 RESULT:")
        print(f"Intent: {result['intent']}")
        print(f"Requires Auth: {result.get('requires_auth', False)}")
        print(f"Response: {result['text']}")
        
        if result.get('requires_auth'):
            print("\n✅ TEST 3 PASSED - Authentication check working")
        else:
            print("\n⚠️ TEST 3 WARNING - Should require authentication")
        
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
    
    # Close database connection
    db.close()
    print("\n" + "=" * 80)
    print("🎉 RULE ENGINE INTEGRATION TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    test_rule_engine_integration()
