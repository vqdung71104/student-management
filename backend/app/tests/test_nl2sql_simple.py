"""
Simple test for NL2SQL service
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.nl2sql_service import NL2SQLService
from app.chatbot.rasa_classifier import RasaIntentClassifier


async def test_basic():
    """Test basic NL2SQL"""
    print("\n" + "="*70)
    print("🧪 TEST NL2SQL SERVICE")
    print("="*70)
    
    # Initialize
    print("\n1️⃣ Initializing services...")
    nl2sql = NL2SQLService()
    classifier = RasaIntentClassifier()
    
    # Test cases
    test_cases = [
        {
            "question": "xem điểm của tôi",
            "student_id": 1
        },
        {
            "question": "các môn bị D",
            "student_id": 1
        },
        {
            "question": "danh sách các lớp môn Đại số",
            "student_id": None
        },
    ]
    
    print(f"\n2️⃣ Testing {len(test_cases)} cases...\n")
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}: \"{test['question']}\"")
        print(f"Student ID: {test['student_id']}")
        print(f"{'='*70}")
        
        # Classify intent
        intent_result = await classifier.classify_intent(test['question'])
        intent = intent_result['intent']
        confidence = intent_result['confidence']
        
        print(f"✅ Intent: {intent} ({confidence})")
        
        # Generate SQL
        sql_result = await nl2sql.generate_sql(
            question=test['question'],
            intent=intent,
            student_id=test['student_id']
        )
        
        sql = sql_result.get('sql')
        error = sql_result.get('error')
        method = sql_result.get('method')
        entities = sql_result.get('entities', {})
        
        print(f"Method: {method}")
        print(f"Entities: {entities}")
        
        if sql:
            print(f"\n✅ SQL Generated:")
            print(f"   {sql}")
            
            # Check if {student_id} is still in SQL
            if "{student_id}" in sql:
                print(f"\n❌ ERROR: {{student_id}} not replaced!")
        else:
            print(f"\n⚠️ No SQL generated")
            if error:
                print(f"   Error: {error}")


if __name__ == "__main__":
    asyncio.run(test_basic())
