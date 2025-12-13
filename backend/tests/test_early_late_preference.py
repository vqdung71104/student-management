"""
Test Early/Late Preference Logic
Test that prefer_early_start sorts by earliest start time
Test that prefer_late_start sorts by latest end time
"""
from datetime import time
from app.services.preference_filter import PreferenceFilter


def test_prefer_early_start_sorting():
    """Test that prefer_early_start sorts classes by start time (earliest first)"""
    print("=" * 60)
    print("TEST 1: prefer_early_start Sorting")
    print("=" * 60)
    
    filter = PreferenceFilter()
    
    # Mock classes with different start times
    classes = [
        {
            'class_id': '1',
            'class_name': 'Class 1',
            'study_time_start': '13:00',
            'study_time_end': '15:00'
        },
        {
            'class_id': '2',
            'class_name': 'Class 2',
            'study_time_start': '07:00',
            'study_time_end': '09:00'
        },
        {
            'class_id': '3',
            'class_name': 'Class 3',
            'study_time_start': '09:30',
            'study_time_end': '11:30'
        }
    ]
    
    preferences = {
        'prefer_early_start': True
    }
    
    filtered = filter.filter_by_preferences(classes, preferences)
    
    print(f"\nOriginal order: {[c['class_id'] for c in classes]}")
    print(f"After prefer_early_start: {[c['class_id'] for c in filtered]}")
    
    # Should be sorted: 07:00 < 09:30 < 13:00
    assert filtered[0]['class_id'] == '2', f"First should be class 2 (07:00), got {filtered[0]['class_id']}"
    assert filtered[1]['class_id'] == '3', f"Second should be class 3 (09:30), got {filtered[1]['class_id']}"
    assert filtered[2]['class_id'] == '1', f"Third should be class 1 (13:00), got {filtered[2]['class_id']}"
    
    print("\n✅ TEST 1 PASSED: Classes sorted by earliest start time")


def test_prefer_late_end_sorting():
    """Test that prefer_late_start sorts classes by end time (latest first)"""
    print("\n" + "=" * 60)
    print("TEST 2: prefer_late_start Sorting")
    print("=" * 60)
    
    filter = PreferenceFilter()
    
    # Mock classes with different end times
    classes = [
        {
            'class_id': '1',
            'class_name': 'Class 1',
            'study_time_start': '07:00',
            'study_time_end': '09:00'
        },
        {
            'class_id': '2',
            'class_name': 'Class 2',
            'study_time_start': '13:00',
            'study_time_end': '17:00'
        },
        {
            'class_id': '3',
            'class_name': 'Class 3',
            'study_time_start': '09:30',
            'study_time_end': '11:30'
        }
    ]
    
    preferences = {
        'prefer_late_start': True
    }
    
    filtered = filter.filter_by_preferences(classes, preferences)
    
    print(f"\nOriginal order: {[c['class_id'] for c in classes]}")
    print(f"After prefer_late_start: {[c['class_id'] for c in filtered]}")
    
    # Should be sorted by end time (latest first): 17:00 > 11:30 > 09:00
    assert filtered[0]['class_id'] == '2', f"First should be class 2 (end 17:00), got {filtered[0]['class_id']}"
    assert filtered[1]['class_id'] == '3', f"Second should be class 3 (end 11:30), got {filtered[1]['class_id']}"
    assert filtered[2]['class_id'] == '1', f"Third should be class 1 (end 09:00), got {filtered[2]['class_id']}"
    
    print("\n✅ TEST 2 PASSED: Classes sorted by latest end time")


def test_only_two_questions():
    """Test that only 2 questions are asked"""
    print("\n" + "=" * 60)
    print("TEST 3: Only 2 Questions")
    print("=" * 60)
    
    from app.services.preference_service import PreferenceCollectionService
    from app.schemas.preference_schema import CompletePreference, PREFERENCE_QUESTIONS
    
    service = PreferenceCollectionService()
    preferences = CompletePreference()
    
    # Initially should have 2 missing
    missing = preferences.get_missing_preferences()
    print(f"\nInitial missing preferences: {missing}")
    assert len(missing) == 2, f"Should have 2 missing, got {len(missing)}"
    assert 'day' in missing and 'time' in missing
    
    # Get first question
    q1 = service.get_next_question(preferences)
    assert q1 is not None, "Should have first question"
    assert q1.key == 'day', f"First question should be 'day', got {q1.key}"
    print(f"\nQuestion 1: {q1.key}")
    
    # Answer first question
    preferences.day.prefer_days = ['Monday', 'Wednesday']
    
    # Get second question
    q2 = service.get_next_question(preferences)
    assert q2 is not None, "Should have second question"
    assert q2.key == 'time', f"Second question should be 'time', got {q2.key}"
    print(f"Question 2: {q2.key}")
    
    # Answer second question
    preferences.time.prefer_early_start = True
    
    # Should be complete now
    assert preferences.is_complete(), "Should be complete after 2 questions"
    
    # No more questions
    q3 = service.get_next_question(preferences)
    assert q3 is None, f"Should have no more questions, got {q3}"
    print(f"Question 3: None (complete)")
    
    # Check that PREFERENCE_QUESTIONS only has 2 items
    print(f"\nTotal questions defined: {len(PREFERENCE_QUESTIONS)}")
    assert len(PREFERENCE_QUESTIONS) == 2, f"Should have only 2 questions, got {len(PREFERENCE_QUESTIONS)}"
    assert 'day' in PREFERENCE_QUESTIONS
    assert 'time' in PREFERENCE_QUESTIONS
    
    print("\n✅ TEST 3 PASSED: Only 2 questions asked, flow complete")


if __name__ == '__main__':
    try:
        test_prefer_early_start_sorting()
        test_prefer_late_end_sorting()
        test_only_two_questions()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\n🎉 Early/Late preference logic verified:")
        print("  • prefer_early_start: ✅ Sorts by earliest start time")
        print("  • prefer_late_start: ✅ Sorts by latest end time")
        print("  • Questions: ✅ Only 2 questions (day + time)")
        print("  • Conversation: ✅ Ends after 2 answers")
        
    except Exception as e:
        print(f"\n❌ TESTS FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise
