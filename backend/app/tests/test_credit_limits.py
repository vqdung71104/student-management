"""
Test Credit Limits Logic
Test various scenarios for credit limits based on new regulations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.rules.subject_suggestion_rules import SubjectSuggestionRuleEngine


def test_credit_limits():
    """Test credit limits calculation for various scenarios"""
    
    # Create rule engine (no DB needed for this test)
    engine = SubjectSuggestionRuleEngine(db=None)
    
    print("=" * 80)
    print("TEST CREDIT LIMITS CALCULATION")
    print("=" * 80)
    
    # Test cases
    test_cases = [
        {
            "description": "Sinh viên bình thường - Học kỳ chính",
            "warning_level": 0,
            "semester": "20251",
            "student_semester": 5,
            "has_foreign_lang": False,
            "expected_min": 12,
            "expected_max": 24
        },
        {
            "description": "Sinh viên bình thường - Học kỳ hè",
            "warning_level": 0,
            "semester": "20253",
            "student_semester": 5,
            "has_foreign_lang": False,
            "expected_min": 0,
            "expected_max": 8
        },
        {
            "description": "Sinh viên cảnh cáo mức 1 - Học kỳ chính",
            "warning_level": 1,
            "semester": "20251",
            "student_semester": 4,
            "has_foreign_lang": False,
            "expected_min": 10,
            "expected_max": 18
        },
        {
            "description": "Sinh viên cảnh cáo mức 2 - Học kỳ chính",
            "warning_level": 2,
            "semester": "20251",
            "student_semester": 4,
            "has_foreign_lang": False,
            "expected_min": 8,
            "expected_max": 14
        },
        {
            "description": "Sinh viên chưa đạt ngoại ngữ - Học kỳ chính",
            "warning_level": 0,
            "semester": "20251",
            "student_semester": 4,
            "has_foreign_lang": True,
            "expected_min": 8,
            "expected_max": 14
        },
        {
            "description": "Sinh viên năm cuối (kỳ 7) - Không giới hạn tối thiểu",
            "warning_level": 0,
            "semester": "20251",
            "student_semester": 7,
            "has_foreign_lang": False,
            "expected_min": 0,
            "expected_max": 24
        },
        {
            "description": "Sinh viên năm cuối (kỳ 8) - Không giới hạn tối thiểu",
            "warning_level": 0,
            "semester": "20251",
            "student_semester": 8,
            "has_foreign_lang": False,
            "expected_min": 0,
            "expected_max": 24
        },
        {
            "description": "Sinh viên cảnh cáo mức 1 năm cuối - Không giới hạn tối thiểu",
            "warning_level": 1,
            "semester": "20251",
            "student_semester": 7,
            "has_foreign_lang": False,
            "expected_min": 0,
            "expected_max": 18
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['description']}")
        print(f"   Input: warning_level={test_case['warning_level']}, "
              f"semester={test_case['semester']}, "
              f"student_semester={test_case['student_semester']}, "
              f"has_foreign_lang={test_case['has_foreign_lang']}")
        
        min_credits, max_credits = engine.get_credit_limits(
            warning_level=test_case['warning_level'],
            current_semester=test_case['semester'],
            student_semester_number=test_case['student_semester'],
            has_foreign_lang_requirement=test_case['has_foreign_lang']
        )
        
        print(f"   Result: min={min_credits} TC, max={max_credits} TC")
        print(f"   Expected: min={test_case['expected_min']} TC, max={test_case['expected_max']} TC")
        
        if min_credits == test_case['expected_min'] and max_credits == test_case['expected_max']:
            print("   ✅ PASSED")
            passed += 1
        else:
            print("   ❌ FAILED")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print("=" * 80)


def test_semester_detection():
    """Test summer semester detection"""
    
    engine = SubjectSuggestionRuleEngine(db=None)
    
    print("\n" + "=" * 80)
    print("TEST SEMESTER DETECTION")
    print("=" * 80)
    
    test_semesters = [
        ("20251", False, "Học kỳ 1"),
        ("20252", False, "Học kỳ 2"),
        ("20253", True, "Học kỳ hè"),
        ("20243", True, "Học kỳ hè"),
        ("20231", False, "Học kỳ 1"),
    ]
    
    for semester, expected_summer, description in test_semesters:
        is_summer = engine.is_summer_semester(semester)
        status = "✅" if is_summer == expected_summer else "❌"
        print(f"{status} {semester} → is_summer={is_summer} ({description})")


def test_final_year_detection():
    """Test final year detection"""
    
    engine = SubjectSuggestionRuleEngine(db=None)
    
    print("\n" + "=" * 80)
    print("TEST FINAL YEAR DETECTION")
    print("=" * 80)
    
    test_semesters = [
        (1, False),
        (2, False),
        (3, False),
        (4, False),
        (5, False),
        (6, False),
        (7, True),
        (8, True),
    ]
    
    for semester_num, expected_final in test_semesters:
        is_final = engine.is_final_year(semester_num)
        status = "✅" if is_final == expected_final else "❌"
        print(f"{status} Semester {semester_num} → is_final={is_final}")


if __name__ == "__main__":
    test_credit_limits()
    test_semester_detection()
    test_final_year_detection()
