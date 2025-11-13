"""Quick test to debug SQL customization - ALL 3 TEST CASES"""
import sys
sys.path.insert(0, 'C:/Users/Admin/student-management/backend')

from app.services.nl2sql_service import NL2SQLService

service = NL2SQLService()

test_cases = [
    {
        "name": "Test 1: Replace subject_id",
        "sql": "SELECT * FROM classes c JOIN subjects s ON c.subject_id = s.id WHERE s.subject_id = 'MI1114'",
        "entities": {"subject_id": "IT4040"},
        "expected": "IT4040"
    },
    {
        "name": "Test 2: Replace subject_name",
        "sql": "SELECT * FROM subjects WHERE subject_name LIKE '%Giải tích%'",
        "entities": {"subject_name": "Lập trình"},
        "expected": "Lập trình"
    },
    {
        "name": "Test 3: Replace class_id",
        "sql": "SELECT c.class_id, c.class_name FROM classes c WHERE c.class_id = '161084'",
        "entities": {"class_id": "123456"},
        "expected": "123456"
    },
]

print("=" * 80)
print("SQL CUSTOMIZATION DEBUG - ALL TEST CASES")
print("=" * 80)

for i, test in enumerate(test_cases, 1):
    print(f"\n{'=' * 80}")
    print(f"{test['name']}")
    print(f"{'=' * 80}")
    
    original = test["sql"]
    entities = test["entities"]
    expected = test["expected"]
    
    print(f"\nOriginal SQL:")
    print(f"  {original}")
    print(f"\nEntities: {entities}")
    print(f"Expected value: '{expected}'")
    
    customized = service._customize_sql(original, "", entities)
    
    print(f"\nCustomized SQL:")
    print(f"  {customized}")
    
    is_found = expected in customized
    status = "✓ PASS" if is_found else "✗ FAIL"
    print(f"\n{status}: '{expected}' {'found' if is_found else 'NOT FOUND'} in customized SQL")
    
    if not is_found:
        print(f"\n   DEBUG INFO:")
        print(f"   - Original contained '{expected}': {expected in original}")
        print(f"   - Check what changed:")
        print(f"     Before: ...{original[50:]}...")
        print(f"     After:  ...{customized[50:]}...")

print(f"\n{'=' * 80}")
print("SUMMARY")
print(f"{'=' * 80}")
