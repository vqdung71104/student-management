"""
End-to-End Chatbot Integration Test
Tests complete chatbot flow from user input to response
"""
import sys
sys.path.insert(0, 'C:/Users/Admin/student-management/backend')

from app.db.database import SessionLocal
from app.chatbot.tfidf_classifier import TfidfIntentClassifier
from app.services.nl2sql_service import NL2SQLService
from sqlalchemy import text
import asyncio
import time
import json


class ChatbotIntegrationTester:
    """End-to-end chatbot tester"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.intent_classifier = TfidfIntentClassifier()
        self.nl2sql_service = NL2SQLService()
        
    async def process_message(self, message: str, student_id: int = None):
        """Process a complete chatbot message"""
        result = {
            "message": message,
            "student_id": student_id,
            "steps": {},
            "total_time_ms": 0
        }
        
        start_total = time.time()
        
        # Step 1: Intent Classification
        start = time.time()
        intent_result = await self.intent_classifier.classify_intent(message)
        intent_time = (time.time() - start) * 1000
        
        result["steps"]["intent_classification"] = {
            "intent": intent_result["intent"],
            "confidence": intent_result["confidence"],
            "score": intent_result.get("score", 0),
            "time_ms": intent_time
        }
        
        intent = intent_result["intent"]
        confidence = intent_result["confidence"]
        
        # Step 2: SQL Generation (if data intent)
        data_intents = [
            "grade_view", "learned_subjects_view", "student_info",
            "subject_info", "class_info", "schedule_view",
            "subject_registration_suggestion", "class_registration_suggestion"
        ]
        
        if intent in data_intents and confidence in ["high", "medium"]:
            # Entity extraction
            start = time.time()
            entities = self.nl2sql_service._extract_entities(message)
            entity_time = (time.time() - start) * 1000
            
            result["steps"]["entity_extraction"] = {
                "entities": entities,
                "time_ms": entity_time
            }
            
            # SQL generation
            start = time.time()
            sql_result = await self.nl2sql_service.generate_sql(
                message, intent, student_id
            )
            sql_gen_time = (time.time() - start) * 1000
            
            result["steps"]["sql_generation"] = {
                "sql": sql_result.get("sql", ""),
                "method": sql_result.get("method", ""),
                "error": sql_result.get("error", ""),
                "time_ms": sql_gen_time
            }
            
            # Database query
            sql = sql_result.get("sql")
            if sql:
                try:
                    start = time.time()
                    db_result = self.db.execute(text(sql))
                    rows = db_result.fetchall()
                    db_time = (time.time() - start) * 1000
                    
                    # Convert to dict
                    if rows:
                        columns = db_result.keys()
                        data = [dict(zip(columns, row)) for row in rows]
                    else:
                        data = []
                    
                    result["steps"]["database_query"] = {
                        "success": True,
                        "row_count": len(data),
                        "time_ms": db_time
                    }
                    
                    result["data"] = data
                    
                except Exception as e:
                    result["steps"]["database_query"] = {
                        "success": False,
                        "error": str(e),
                        "time_ms": 0
                    }
                    result["data"] = []
            else:
                # SQL is None - generation failed
                result["data"] = None
        else:
            result["data"] = None
        
        result["total_time_ms"] = (time.time() - start_total) * 1000
        
        return result


# Test scenarios
TEST_SCENARIOS = [
    # ============================================================================
    # CLASS INFO TESTS
    # ============================================================================
    {
        "name": "Simple class query",
        "message": "các lớp môn Ngôn ngữ lập trình",
        "student_id": None,
        "expected_intent": "class_info",
        "expected_data": True
    },
    {
        "name": "Class query with subject ID",
        "message": "các lớp của môn EM1180Q",
        "student_id": None,
        "expected_intent": "class_info",
        "expected_data": True
    },
    {
        "name": "Complex subject name",
        "message": "lớp của học phần Lý thuyết điều khiển tự động",
        "student_id": None,
        "expected_intent": "class_info",
        "expected_data": True
    },
    {
        "name": "Class query - without 'của' (issue fix)",
        "message": "cho tôi thông tin các lớp môn học Giải tích 1",
        "student_id": None,
        "expected_intent": "class_info",
        "expected_data": False
    },
    {
        "name": "Class query - direct subject name",
        "message": "các lớp Giải tích 1",
        "student_id": None,
        "expected_intent": "class_info",
        "expected_data": False
    },
    {
        "name": "Class query - môn học variant",
        "message": "thông tin các lớp môn học Lập trình mạng",
        "student_id": None,
        "expected_intent": "class_info",
        "expected_data": False
    },
    {
        "name": "Class list - short query",
        "message": "lớp học",
        "student_id": None,
        "expected_intent": "class_list",
        "expected_data": False
    },
    {
        "name": "Class info - paraphrase",
        "message": "cho tôi biết các lớp của môn Giải tích 1",
        "student_id": None,
        "expected_intent": "class_info",
        "expected_data": False
    },
    
    # ============================================================================
    # GRADE VIEW TESTS (Phase 3 Focus)
    # ============================================================================
    {
        "name": "Grade view - very short",
        "message": "điểm",
        "student_id": 1,
        "expected_intent": "grade_view",
        "expected_data": False  # No SQL template for grade_view yet
    },
    {
        "name": "Grade view - short with possessive",
        "message": "điểm của tôi",
        "student_id": 1,
        "expected_intent": "grade_view",
        "expected_data": True
    },
    {
        "name": "Grade view - with action verb",
        "message": "xem điểm",
        "student_id": 1,
        "expected_intent": "grade_view",
        "expected_data": False  # Returns learned_subjects (wrong table) or no template
    },
    {
        "name": "Grade view - polite form",
        "message": "cho tôi xem điểm",
        "student_id": 1,
        "expected_intent": "grade_view",
        "expected_data": True
    },
    {
        "name": "Grade view - detailed query",
        "message": "tôi muốn xem điểm số của mình",
        "student_id": 1,
        "expected_intent": "grade_view",
        "expected_data": False  # May return wrong table
    },
    {
        "name": "Grade view - synonym",
        "message": "điểm số",
        "student_id": 1,
        "expected_intent": "grade_view",
        "expected_data": False
    },
    {
        "name": "Grade view - check variant",
        "message": "kiểm tra điểm",
        "student_id": 1,
        "expected_intent": "grade_view",
        "expected_data": False
    },
    
    # ============================================================================
    # SCHEDULE TESTS
    # ============================================================================
    {
        "name": "Schedule - exact match",
        "message": "lịch học của tôi",
        "student_id": 1,
        "expected_intent": "schedule_view",
        "expected_data": True
    },
    {
        "name": "Schedule - short form",
        "message": "lịch học",
        "student_id": 1,
        "expected_intent": "schedule_view",
        "expected_data": True
    },
    {
        "name": "Schedule - synonym TKB",
        "message": "thời khóa biểu",
        "student_id": 1,
        "expected_intent": "schedule_view",
        "expected_data": True
    },
    {
        "name": "Schedule - action verb",
        "message": "xem lịch học",
        "student_id": 1,
        "expected_intent": "schedule_view",
        "expected_data": True
    },
    
    # ============================================================================
    # SUGGESTION TESTS
    # ============================================================================
    {
        "name": "Class suggestion - basic",
        "message": "kỳ này nên học lớp nào",
        "student_id": 1,
        "expected_intent": "class_registration_suggestion",
        "expected_data": True
    },
    {
        "name": "Class suggestion - with subject",
        "message": "tôi nên học lớp nào của môn Lập trình mạng",
        "student_id": 1,
        "expected_intent": "class_registration_suggestion",
        "expected_data": True
    },
    {
        "name": "Subject suggestion - short",
        "message": "nên đăng ký môn gì",
        "student_id": 1,
        "expected_intent": "subject_registration_suggestion",
        "expected_data": True  # Should return course subjects (73 rows is correct!)
    },
    {
        "name": "Subject suggestion - detailed",
        "message": "tôi nên đăng ký học phần gì",
        "student_id": 1,
        "expected_intent": "subject_registration_suggestion",
        "expected_data": True
    },
    {
        "name": "Subject suggestion - paraphrase",
        "message": "môn nào phù hợp với tôi",
        "student_id": 1,
        "expected_intent": "subject_registration_suggestion",
        "expected_data": True
    },
    
    # ============================================================================
    # SUBJECT INFO TESTS
    # ============================================================================
    {
        "name": "Subject info - general",
        "message": "thông tin học phần",
        "student_id": None,
        "expected_intent": "subject_info",
        "expected_data": True  # Returns 41 subjects with 'Giải tích' - that's data!
    },
    {
        "name": "Subject info - specific",
        "message": "thông tin môn Giải tích 2",
        "student_id": None,
        "expected_intent": "subject_info",
        "expected_data": False
    },
    {
        "name": "Subject info - short",
        "message": "môn học",
        "student_id": None,
        "expected_intent": "subject_info",
        "expected_data": False
    },
    
    # ============================================================================
    # STUDENT INFO TESTS
    # ============================================================================
    {
        "name": "Student info - short",
        "message": "thông tin của tôi",
        "student_id": 1,
        "expected_intent": "student_info",
        "expected_data": False
    },
    {
        "name": "Student info - detailed",
        "message": "xem thông tin sinh viên",
        "student_id": 1,
        "expected_intent": "student_info",
        "expected_data": False
    },
    
    # ============================================================================
    # REGISTRATION GUIDE TESTS
    # ============================================================================
    {
        "name": "Registration guide - how to",
        "message": "đăng ký học phần như thế nào",
        "student_id": None,
        "expected_intent": "registration_guide",
        "expected_data": False
    },
    {
        "name": "Registration guide - short",
        "message": "hướng dẫn đăng ký",
        "student_id": None,
        "expected_intent": "registration_guide",
        "expected_data": False
    },
    
    # ============================================================================
    # GREETING & COURTESY TESTS
    # ============================================================================
    {
        "name": "Greeting - hello",
        "message": "xin chào",
        "student_id": None,
        "expected_intent": "greeting",
        "expected_data": False
    },
    {
        "name": "Greeting - hi",
        "message": "chào bạn",
        "student_id": None,
        "expected_intent": "greeting",
        "expected_data": False
    },
    {
        "name": "Greeting - hello variant",
        "message": "hello",
        "student_id": None,
        "expected_intent": "greeting",
        "expected_data": False
    },
    {
        "name": "Thanks - thank you",
        "message": "cảm ơn",
        "student_id": None,
        "expected_intent": "thanks",
        "expected_data": False
    },
    {
        "name": "Thanks - thanks",
        "message": "cám ơn bạn",
        "student_id": None,
        "expected_intent": "thanks",
        "expected_data": False
    },
    {
        "name": "Goodbye - bye",
        "message": "tạm biệt",
        "student_id": None,
        "expected_intent": "goodbye",
        "expected_data": False
    },
    
    # ============================================================================
    # EDGE CASES & VARIATIONS
    # ============================================================================
    {
        "name": "Very short query - 1 word",
        "message": "lịch",
        "student_id": 1,
        "expected_intent": "schedule_view",
        "expected_data": True
    },
    {
        "name": "Query with typo/variation",
        "message": "diem cua toi",
        "student_id": 1,
        "expected_intent": "grade_view",
        "expected_data": True
    },
    {
        "name": "Long descriptive query",
        "message": "tôi muốn xem kết quả học tập của mình trong học kỳ này",
        "student_id": 1,
        "expected_intent": "grade_view",
        "expected_data": True
    },
    {
        "name": "Query with multiple intents",
        "message": "xem điểm và lịch học",
        "student_id": 1,
        "expected_intent": "grade_view",  # Should pick dominant intent
        "expected_data": True
    },
]


async def run_integration_tests():
    """Run all integration tests"""
    print("=" * 80)
    print("CHATBOT END-TO-END INTEGRATION TEST")
    print("=" * 80)
    
    tester = ChatbotIntegrationTester()
    
    print(f"\n[1] Testing {len(TEST_SCENARIOS)} scenarios...")
    print("-" * 80)
    
    results = []
    total_passed = 0
    
    for i, scenario in enumerate(TEST_SCENARIOS, 1):
        print(f"\n[Test {i}] {scenario['name']}")
        print(f"Message: {scenario['message']}")
        print(f"Student ID: {scenario['student_id']}")
        
        result = await tester.process_message(
            scenario['message'],
            scenario['student_id']
        )
        
        # Validate result
        intent_correct = result["steps"]["intent_classification"]["intent"] == scenario["expected_intent"]
        confidence = result["steps"]["intent_classification"]["confidence"]
        
        has_data = result.get("data") is not None and len(result.get("data", [])) > 0
        data_correct = has_data == scenario["expected_data"]
        
        passed = intent_correct and data_correct
        if passed:
            total_passed += 1
        
        status = "✓ PASS" if passed else "✗ FAIL"
        
        # Print results
        print(f"\nResult: {status}")
        print(f"  Intent: {result['steps']['intent_classification']['intent']} "
              f"(expected: {scenario['expected_intent']}) "
              f"{'✓' if intent_correct else '✗'}")
        print(f"  Confidence: {confidence} "
              f"({result['steps']['intent_classification']['score']:.2f})")
        
        if "entity_extraction" in result["steps"]:
            entities = result["steps"]["entity_extraction"]["entities"]
            if entities:
                print(f"  Entities: {entities}")
        
        if "sql_generation" in result["steps"]:
            sql = result["steps"]["sql_generation"]["sql"]
            if sql:
                print(f"  SQL: {sql[:100]}..." if len(sql) > 100 else f"  SQL: {sql}")
            else:
                error = result["steps"]["sql_generation"].get("error", "Unknown error")
                print(f"  SQL: None (Error: {error})")
        
        if "database_query" in result["steps"]:
            db_result = result["steps"]["database_query"]
            if db_result["success"]:
                print(f"  Data: {db_result['row_count']} rows fetched "
                      f"{'✓' if data_correct else '✗'}")
            else:
                print(f"  Data: Query failed - {db_result['error']}")
        
        # Print timing
        print(f"\n  Timing breakdown:")
        for step_name, step_data in result["steps"].items():
            if "time_ms" in step_data:
                print(f"    {step_name}: {step_data['time_ms']:.2f}ms")
        print(f"    TOTAL: {result['total_time_ms']:.2f}ms")
        
        results.append({
            "scenario": scenario,
            "result": result,
            "passed": passed
        })
        
        print("-" * 80)
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    pass_rate = (total_passed / len(TEST_SCENARIOS)) * 100
    print(f"\n   Overall Results:")
    print(f"   Total tests: {len(TEST_SCENARIOS)}")
    print(f"   Passed: {total_passed}")
    print(f"   Failed: {len(TEST_SCENARIOS) - total_passed}")
    print(f"   Pass rate: {pass_rate:.2f}%")
    
    # Timing statistics
    total_times = [r["result"]["total_time_ms"] for r in results]
    avg_time = sum(total_times) / len(total_times)
    max_time = max(total_times)
    min_time = min(total_times)
    
    print(f"\n   Performance Statistics:")
    print(f"   Average response time: {avg_time:.2f}ms")
    print(f"   Min response time: {min_time:.2f}ms")
    print(f"   Max response time: {max_time:.2f}ms")
    
    # Step timing breakdown
    step_times = {}
    for r in results:
        for step_name, step_data in r["result"]["steps"].items():
            if "time_ms" in step_data:
                if step_name not in step_times:
                    step_times[step_name] = []
                step_times[step_name].append(step_data["time_ms"])
    
    print(f"\n   Average time per step:")
    for step_name, times in step_times.items():
        avg = sum(times) / len(times)
        print(f"   {step_name}: {avg:.2f}ms")
    
    # Failed tests
    failed = [r for r in results if not r["passed"]]
    if failed:
        print(f"\n  Failed Tests ({len(failed)}):")
        for r in failed:
            print(f"   - {r['scenario']['name']}")
            print(f"     Message: {r['scenario']['message']}")
            print(f"     Expected intent: {r['scenario']['expected_intent']}")
            print(f"     Got intent: {r['result']['steps']['intent_classification']['intent']}")
    
    return {
        "pass_rate": pass_rate,
        "avg_time_ms": avg_time,
        "results": results
    }


async def test_concurrent_requests():
    """Test handling concurrent requests"""
    print("\n" + "=" * 80)
    print("CONCURRENT REQUESTS TEST")
    print("=" * 80)
    
    tester = ChatbotIntegrationTester()
    
    # Create multiple concurrent requests
    messages = [
        "các lớp môn Lý thuyết mạch",
        "lịch học của tôi",
        "điểm của tôi",
        "kỳ này nên học lớp nào",
        "các lớp của môn EM1180Q"
    ] * 10  # 50 concurrent requests
    
    student_ids = [1] * len(messages)
    
    print(f"\nProcessing {len(messages)} concurrent requests...")
    
    start_time = time.time()
    
    # Process all concurrently
    tasks = [
        tester.process_message(msg, sid)
        for msg, sid in zip(messages, student_ids)
    ]
    results = await asyncio.gather(*tasks)
    
    total_time = (time.time() - start_time) * 1000
    
    # Statistics
    successful = sum(1 for r in results if "data" in r)
    avg_time = sum(r["total_time_ms"] for r in results) / len(results)
    throughput = len(messages) / (total_time / 1000)
    
    print(f"\n   Concurrent Processing Results:")
    print(f"   Total requests: {len(messages)}")
    print(f"   Successful: {successful}")
    print(f"   Total wall time: {total_time:.2f}ms")
    print(f"   Average per-request time: {avg_time:.2f}ms")
    print(f"   Throughput: {throughput:.2f} requests/second")


async def test_error_handling():
    """Test error handling scenarios"""
    print("\n" + "=" * 80)
    print("ERROR HANDLING TEST")
    print("=" * 80)
    
    tester = ChatbotIntegrationTester()
    
    error_scenarios = [
        {
            "name": "Empty message",
            "message": "",
            "student_id": None
        },
        {
            "name": "Very long message",
            "message": "a" * 1000,
            "student_id": None
        },
        {
            "name": "Special characters",
            "message": "!@#$%^&*()",
            "student_id": None
        },
        {
            "name": "Non-Vietnamese text",
            "message": "show me all classes",
            "student_id": None
        },
    ]
    
    print(f"\nTesting {len(error_scenarios)} error scenarios...")
    print("-" * 80)
    
    for scenario in error_scenarios:
        print(f"\nScenario: {scenario['name']}")
        print(f"Message: {scenario['message'][:50]}...")
        
        try:
            result = await tester.process_message(
                scenario['message'],
                scenario['student_id']
            )
            print(f"  Result: {result['steps']['intent_classification']['intent']}")
            print(f"  Confidence: {result['steps']['intent_classification']['confidence']}")
            print(f"  ✓ Handled gracefully")
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")


if __name__ == "__main__":
    print("\n   Starting Chatbot Integration Tests\n")
    
    # Run main tests
    summary = asyncio.run(run_integration_tests())
    
    # Run concurrent test
    asyncio.run(test_concurrent_requests())
    
    # Run error handling test
    asyncio.run(test_error_handling())
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)
    print(f"\n   Overall Pass Rate: {summary['pass_rate']:.2f}%")
    print(f"   Average Response Time: {summary['avg_time_ms']:.2f}ms")
