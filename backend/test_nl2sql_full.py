"""
Test full NL2SQL generation flow
"""
import sys
import os
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.nl2sql_service import NL2SQLService

# Initialize service
nl2sql = NL2SQLService()

# Test cases
test_cases = [
    {
        "question": "thông tin lớp Kỹ thuật điện",
        "intent": "class_info"
    },
    {
        "question": "thông tin lớp Điều khiển nội mạng",
        "intent": "class_info"
    },
    {
        "question": "danh sách lớp môn Lý thuyết điều khiển tự động",
        "intent": "class_info"
    },
    {
        "question": "các lớp của môn IT4040",
        "intent": "class_info"
    },
]

async def test_nl2sql():
    print("=" * 80)
    print("TESTING NL2SQL GENERATION")
    print("=" * 80)
    
    for test in test_cases:
        question = test["question"]
        intent = test["intent"]
        
        print(f"\n{'=' * 80}")
        print(f"📝 Question: {question}")
        print(f"🎯 Intent: {intent}")
        print("-" * 80)
        
        result = await nl2sql.generate_sql(question, intent, student_id=None)
        
        print(f"\n✅ Generated SQL:")
        print(f"{result.get('sql')}")
        
        if 'entities' in result:
            print(f"\n📦 Entities: {result['entities']}")
        
        if 'template_match' in result:
            print(f"📋 Template match: {result['template_match']}")
        
        if result.get('sql') and 'Giải tích' in result['sql']:
            print("\n⚠️ WARNING: SQL still contains hardcoded 'Giải tích'!")
        elif result.get('sql'):
            print("\n✓ SQL customized correctly")

if __name__ == "__main__":
    asyncio.run(test_nl2sql())
