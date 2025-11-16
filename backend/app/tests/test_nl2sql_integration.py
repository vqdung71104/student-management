"""
Test NL2SQL integration với chatbot
"""
import asyncio
import sys
import os

# Add backend directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from app.chatbot.tfidf_classifier import TfidfIntentClassifier
from app.services.nl2sql_service import NL2SQLService


async def test_nl2sql_basic():
    """Test basic NL2SQL functionality"""
    print("\n" + "="*70)
    print("   TEST 1: BASIC NL2SQL FUNCTIONALITY")
    print("="*70)
    
    # Initialize services
    print("\n   Initializing services...")
    intent_classifier = TfidfIntentClassifier()
    nl2sql_service = NL2SQLService()
    
    test_cases = [
        {
            "question": "xem điểm",
            "expected_intent": "grade_view",
            "student_id": 1
        },
        {
            "question": "các môn bị D",
            "expected_intent": "student_info",
            "student_id": 1
        },
        {
            "question": "môn tiên quyết của IT4040",
            "expected_intent": "subject_info",
            "student_id": None
        },
        {
            "question": "danh sách các lớp môn Đại số",
            "expected_intent": "class_info",
            "student_id": None
        },
        {
            "question": "lịch học của tôi",
            "expected_intent": "schedule_view",
            "student_id": 1
        },
    ]
    
    print(f"\n   Testing {len(test_cases)} cases...\n")
    
    correct_intent = 0
    sql_generated = 0
    
    for i, test_case in enumerate(test_cases, 1):
        question = test_case["question"]
        expected_intent = test_case["expected_intent"]
        student_id = test_case["student_id"]
        
        # 1. Classify intent
        intent_result = await intent_classifier.classify_intent(question)
        detected_intent = intent_result["intent"]
        confidence = intent_result["confidence"]
        
        # 2. Generate SQL
        sql_result = await nl2sql_service.generate_sql(
            question=question,
            intent=detected_intent,
            student_id=student_id
        )
        
        sql = sql_result.get("sql")
        method = sql_result.get("method")
        entities = sql_result.get("entities", {})
        
        # Check results
        intent_correct = detected_intent == expected_intent
        has_sql = sql is not None
        
        if intent_correct:
            correct_intent += 1
            status = "  "
        else:
            status = " "
        
        if has_sql:
            sql_generated += 1
        
        print(f"{i}. {status} Question: \"{question}\"")
        print(f"   Expected intent: {expected_intent}")
        print(f"   Detected intent: {detected_intent} ({confidence})")
        print(f"   SQL: {sql[:80] + '...' if sql and len(sql) > 80 else sql}")
        print(f"   Method: {method}")
        if entities:
            print(f"   Entities: {entities}")
        print()
    
    # Summary
    print("="*70)
    print("   SUMMARY")
    print("="*70)
    print(f"Intent classification: {correct_intent}/{len(test_cases)} ({correct_intent/len(test_cases)*100:.1f}%)")
    print(f"SQL generated: {sql_generated}/{len(test_cases)} ({sql_generated/len(test_cases)*100:.1f}%)")


async def test_entity_extraction():
    """Test entity extraction"""
    print("\n" + "="*70)
    print("   TEST 2: ENTITY EXTRACTION")
    print("="*70)
    
    nl2sql_service = NL2SQLService()
    intent_classifier = TfidfIntentClassifier()
    
    test_cases = [
        {
            "question": "danh sách các lớp môn Đại số học vào thứ 2",
            "expected_entities": {
                "subject_name": "Đại số",
                "study_days": ["Monday"]
            }
        },
        {
            "question": "lớp buổi chiều thứ 3",
            "expected_entities": {
                "study_days": ["Tuesday"],
                "time_period": "afternoon"
            }
        },
        {
            "question": "môn tiên quyết của IT4040",
            "expected_entities": {
                "subject_id": "IT4040"
            }
        },
        {
            "question": "các lớp môn Giải tích 1 vào sáng thứ 4",
            "expected_entities": {
                "subject_name": "Giải tích 1",
                "study_days": ["Wednesday"],
                "time_period": "morning"
            }
        },
    ]
    
    print(f"\n   Testing {len(test_cases)} cases...\n")
    
    for i, test_case in enumerate(test_cases, 1):
        question = test_case["question"]
        expected_entities = test_case["expected_entities"]
        
        # Get intent
        intent_result = await intent_classifier.classify_intent(question)
        intent = intent_result["intent"]
        
        # Generate SQL and extract entities
        sql_result = await nl2sql_service.generate_sql(
            question=question,
            intent=intent,
            student_id=None
        )
        
        entities = sql_result.get("entities", {})
        
        print(f"{i}. Question: \"{question}\"")
        print(f"   Expected: {expected_entities}")
        print(f"   Extracted: {entities}")
        
        # Check if all expected entities were extracted
        all_found = True
        for key, value in expected_entities.items():
            if key not in entities:
                print(f"     Missing entity: {key}")
                all_found = False
            elif entities[key] != value:
                print(f"       Entity mismatch: {key} = {entities[key]} (expected {value})")
        
        if all_found:
            print(f"      All entities extracted correctly")
        
        print()


async def test_sql_customization():
    """Test SQL query customization with entities"""
    print("\n" + "="*70)
    print("   TEST 3: SQL CUSTOMIZATION")
    print("="*70)
    
    nl2sql_service = NL2SQLService()
    intent_classifier = TfidfIntentClassifier()
    
    test_cases = [
        {
            "question": "danh sách các lớp môn Toán",
            "check_contains": ["subject_name LIKE '%Toán%'"]
        },
        {
            "question": "lớp học vào thứ 2",
            "check_contains": ["study_date LIKE '%Monday%'"]
        },
        {
            "question": "lớp buổi sáng",
            "check_contains": ["study_time_start < '12:00:00'"]
        },
        {
            "question": "môn tiên quyết của IT4040",
            "check_contains": ["subject_id = 'IT4040'"]
        },
    ]
    
    print(f"\n   Testing {len(test_cases)} cases...\n")
    
    for i, test_case in enumerate(test_cases, 1):
        question = test_case["question"]
        check_contains = test_case["check_contains"]
        
        # Get intent
        intent_result = await intent_classifier.classify_intent(question)
        intent = intent_result["intent"]
        
        # Generate SQL
        sql_result = await nl2sql_service.generate_sql(
            question=question,
            intent=intent,
            student_id=None
        )
        
        sql = sql_result.get("sql", "")
        
        print(f"{i}. Question: \"{question}\"")
        print(f"   SQL: {sql}")
        
        # Check if SQL contains expected parts
        all_found = True
        for expected_part in check_contains:
            if expected_part not in sql:
                print(f"     Missing: {expected_part}")
                all_found = False
            else:
                print(f"      Contains: {expected_part}")
        
        if not all_found:
            print(f"       SQL may not be fully customized")
        
        print()


async def test_full_workflow():
    """Test full workflow: intent → SQL → response"""
    print("\n" + "="*70)
    print("   TEST 4: FULL WORKFLOW SIMULATION")
    print("="*70)
    
    intent_classifier = TfidfIntentClassifier()
    nl2sql_service = NL2SQLService()
    
    test_messages = [
        ("Xin chào!", 1),
        ("xem điểm của tôi", 1),
        ("danh sách các lớp môn Đại số", None),
        ("Cảm ơn!", 1),
    ]
    
    print(f"\n   Simulating conversation...\n")
    
    for message, student_id in test_messages:
        print(f"   User: {message}")
        
        # 1. Classify intent
        intent_result = await intent_classifier.classify_intent(message)
        intent = intent_result["intent"]
        confidence = intent_result["confidence"]
        
        print(f"      Intent: {intent} ({confidence})")
        
        # 2. Generate SQL if needed
        data_intents = [
            "grade_view", "student_info", "subject_info", 
            "class_info", "schedule_view"
        ]
        
        if intent in data_intents and confidence in ["high", "medium"]:
            sql_result = await nl2sql_service.generate_sql(
                question=message,
                intent=intent,
                student_id=student_id
            )
            
            sql = sql_result.get("sql")
            if sql:
                print(f"      SQL: {sql[:80]}{'...' if len(sql) > 80 else ''}")
                print(f"      Response: Đã tìm thấy dữ liệu từ database")
            else:
                print(f"       No SQL generated")
        else:
            # Non-data intent
            if intent == "greeting":
                print(f"      Response: Xin chào! Mình là trợ lý ảo...")
            elif intent == "thanks":
                print(f"      Response: Rất vui được giúp đỡ bạn!")
        
        print()


async def test_schema_info():
    """Test schema information"""
    print("\n" + "="*70)
    print("   TEST 5: SCHEMA INFORMATION")
    print("="*70)
    
    nl2sql_service = NL2SQLService()
    
    schema = nl2sql_service.get_schema_info()
    
    print(f"\n   Database Schema ({len(schema)} tables):\n")
    
    for table_name, table_info in schema.items():
        columns = table_info.get("columns", [])
        description = table_info.get("description", "")
        
        print(f"   {table_name}")
        print(f"   Description: {description}")
        print(f"   Columns ({len(columns)}): {', '.join(columns[:5])}")
        if len(columns) > 5:
            print(f"              {', '.join(columns[5:10])}")
        print()


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("🚀 NL2SQL INTEGRATION TESTS")
    print("="*70)
    
    tests = [
        test_nl2sql_basic,
        test_entity_extraction,
        test_sql_customization,
        test_full_workflow,
        test_schema_info,
    ]
    
    for test_func in tests:
        try:
            await test_func()
        except Exception as e:
            print(f"\n  Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("   ALL TESTS COMPLETED")
    print("="*70)


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n\n   Tests interrupted by user")
    except Exception as e:
        print(f"\n\n  Fatal error: {e}")
        import traceback
        traceback.print_exc()

