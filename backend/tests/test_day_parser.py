"""
Test Day Parser - Support compact format like "thứ 2,3,4"
"""
from app.services.preference_service import PreferenceCollectionService
from app.schemas.preference_schema import CompletePreference


def test_day_parsing():
    print("=" * 60)
    print("TEST: Day Parsing")
    print("=" * 60)
    
    service = PreferenceCollectionService()
    
    test_cases = [
        ("thứ 2,3,4", ['Monday', 'Tuesday', 'Wednesday']),
        ("thứ 2, thứ 3, thứ 4", ['Monday', 'Tuesday', 'Wednesday']),
        ("t2,3,4", ['Monday', 'Tuesday', 'Wednesday']),
        ("thứ 2, 4, 6", ['Monday', 'Wednesday', 'Friday']),
        ("thứ hai, thứ ba", ['Monday', 'Tuesday']),
    ]
    
    for input_str, expected in test_cases:
        preferences = CompletePreference()
        result = service.parse_user_response(input_str, 'day', preferences)
        
        print(f"\nInput: '{input_str}'")
        print(f"Expected: {expected}")
        print(f"Got: {result.day.prefer_days}")
        
        # Check if all expected days are present
        assert set(expected) == set(result.day.prefer_days), \
            f"Expected {expected}, got {result.day.prefer_days}"
        
        print("✅ PASSED")
    
    print("\n" + "=" * 60)
    print("✅ ALL DAY PARSING TESTS PASSED")
    print("=" * 60)


if __name__ == '__main__':
    try:
        test_day_parsing()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise
