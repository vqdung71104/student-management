"""
Test cases for preference extraction logic
Run: pytest tests/test_preference_extraction.py -v
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.chatbot_service import ChatbotService
from unittest.mock import MagicMock

def test_prefer_days_extraction():
    """Test extraction of preferred days"""
    service = ChatbotService(db=MagicMock())
    
    # Test case 1: Simple prefer day
    prefs = service._extract_preferences_from_question("tôi muốn học vào thứ 5")
    assert 'prefer_days' in prefs
    assert 'Thursday' in prefs['prefer_days']
    assert 'avoid_days' not in prefs or 'Thursday' not in prefs.get('avoid_days', [])
    print("✅ Test 1 passed: Simple prefer day")
    
    # Test case 2: Multiple prefer days
    prefs = service._extract_preferences_from_question("tôi muốn học vào thứ 3 và thứ 5")
    assert 'prefer_days' in prefs
    assert 'Tuesday' in prefs['prefer_days']
    assert 'Thursday' in prefs['prefer_days']
    print("✅ Test 2 passed: Multiple prefer days")
    
    # Test case 3: Avoid day (negation)
    prefs = service._extract_preferences_from_question("tôi không muốn học thứ 7")
    assert 'avoid_days' in prefs
    assert 'Saturday' in prefs['avoid_days']
    assert 'prefer_days' not in prefs or 'Saturday' not in prefs.get('prefer_days', [])
    print("✅ Test 3 passed: Avoid day with negation")

def test_complex_sentences():
    """Test complex sentences with multiple preferences"""
    service = ChatbotService(db=MagicMock())
    
    # Test case 4: Complex sentence from user
    question = "tôi muốn đăng ký môn tự tưởng hồ chí minh, tôi không muốn học buổi sáng, tôi muốn học vào thứ 5"
    prefs = service._extract_preferences_from_question(question)
    
    # Should extract prefer Thursday
    assert 'prefer_days' in prefs, f"Expected prefer_days, got: {prefs}"
    assert 'Thursday' in prefs['prefer_days'], f"Expected Thursday in prefer_days, got: {prefs['prefer_days']}"
    
    # Should AVOID morning (not just ignore it)
    assert 'avoid_time_periods' in prefs, f"Expected avoid_time_periods, got: {prefs}"
    assert 'morning' in prefs['avoid_time_periods'], f"Expected morning in avoid_time_periods, got: {prefs}"
    
    print(f"✅ Test 4 passed: Complex sentence - {prefs}")
    
    # Test case 5: Another complex sentence
    question2 = "tôi muốn học vào thứ 5, buổi sáng, môn tự tưởng hồ chí minh, tôi có thể đăng ký lớp nào"
    prefs2 = service._extract_preferences_from_question(question2)
    
    assert 'prefer_days' in prefs2
    assert 'Thursday' in prefs2['prefer_days']
    assert prefs2.get('time_period') == 'morning'
    assert 'avoid_time_periods' not in prefs2, "Should not have avoid_time_periods for positive preference"
    
    print(f"✅ Test 5 passed: Positive morning preference - {prefs2}")
    
    # Test case 6: Negation before morning
    question3 = "không muốn học buổi sáng, học vào thứ 5"
    prefs3 = service._extract_preferences_from_question(question3)
    
    assert 'avoid_time_periods' in prefs3, f"Expected avoid_time_periods, got: {prefs3}"
    assert 'morning' in prefs3['avoid_time_periods'], f"Expected morning in avoid_time_periods"
    assert 'prefer_days' in prefs3
    assert 'Thursday' in prefs3['prefer_days']
    
    print(f"✅ Test 6 passed: Negation before morning - {prefs3}")

def test_short_forms():
    """Test short forms and compact sentences"""
    service = ChatbotService(db=MagicMock())
    
    # Test case 7: Short form
    prefs = service._extract_preferences_from_question("học vào thứ 5")
    assert 'prefer_days' in prefs
    assert 'Thursday' in prefs['prefer_days']
    print(f"✅ Test 7 passed: Short form - {prefs}")
    
    # Test case 8: Very compact
    prefs = service._extract_preferences_from_question("thứ 5, sáng")
    assert 'prefer_days' in prefs
    assert 'Thursday' in prefs['prefer_days']
    assert prefs.get('time_period') == 'morning'
    print(f"✅ Test 8 passed: Very compact - {prefs}")

def test_avoid_late_end():
    """Test avoid late end preferences"""
    service = ChatbotService(db=MagicMock())
    
    # Test case 9: Avoid late
    prefs = service._extract_preferences_from_question("tôi không muốn học muộn")
    assert prefs.get('avoid_late_end') == True
    print(f"✅ Test 9 passed: Avoid late end - {prefs}")
    
    # Test case 10: Early end preference
    prefs = service._extract_preferences_from_question("các lớp kết thúc sớm")
    assert prefs.get('avoid_late_end') == True
    print(f"✅ Test 10 passed: Early end preference - {prefs}")

def test_avoid_weekdays():
    """Test avoid specific weekdays - should find OTHER days"""
    service = ChatbotService(db=MagicMock())
    
    # Test case 11: Avoid Monday - should prefer other days
    prefs = service._extract_preferences_from_question("không muốn học thứ 2")
    assert 'avoid_days' in prefs
    assert 'Monday' in prefs['avoid_days']
    assert 'prefer_days' not in prefs or 'Monday' not in prefs.get('prefer_days', [])
    print(f"✅ Test 11 passed: Avoid Monday - {prefs}")
    
    # Test case 12: Avoid Saturday
    prefs = service._extract_preferences_from_question("tôi không học thứ 7")
    assert 'avoid_days' in prefs
    assert 'Saturday' in prefs['avoid_days']
    print(f"✅ Test 12 passed: Avoid Saturday - {prefs}")
    
    # Test case 13: Complex - prefer Thu but avoid Sat
    prefs = service._extract_preferences_from_question("học thứ 5, không học thứ 7")
    assert 'prefer_days' in prefs
    assert 'Thursday' in prefs['prefer_days']
    assert 'avoid_days' in prefs
    assert 'Saturday' in prefs['avoid_days']
    print(f"✅ Test 13 passed: Prefer Thu + Avoid Sat - {prefs}")

def test_avoid_time_periods():
    """Test avoid time periods - should find OTHER periods"""
    service = ChatbotService(db=MagicMock())
    
    # Test case 14: Avoid morning - should find afternoon
    prefs = service._extract_preferences_from_question("không muốn học buổi sáng")
    assert 'avoid_time_periods' in prefs
    assert 'morning' in prefs['avoid_time_periods']
    print(f"✅ Test 14 passed: Avoid morning - {prefs}")
    
    # Test case 15: Avoid afternoon
    prefs = service._extract_preferences_from_question("tôi không học buổi chiều")
    assert 'avoid_time_periods' in prefs
    assert 'afternoon' in prefs['avoid_time_periods']
    print(f"✅ Test 15 passed: Avoid afternoon - {prefs}")
    
    # Test case 16: Prefer afternoon (positive)
    prefs = service._extract_preferences_from_question("tôi muốn học buổi chiều")
    assert prefs.get('time_period') == 'afternoon'
    assert 'avoid_time_periods' not in prefs
    print(f"✅ Test 16 passed: Prefer afternoon - {prefs}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 Testing Preference Extraction Logic")
    print("="*60 + "\n")
    
    try:
        test_prefer_days_extraction()
        print()
        test_complex_sentences()
        print()
        test_short_forms()
        print()
        test_avoid_late_end()
        print()
        test_avoid_weekdays()
        print()
        test_avoid_time_periods()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60 + "\n")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        raise
