"""
Test Interactive Preference Collection Flow
"""
import asyncio
import sys
sys.path.append('.')

from app.services.preference_service import PreferenceCollectionService
from app.schemas.preference_schema import CompletePreference


def test_preference_extraction():
    """Test extracting preferences from questions"""
    service = PreferenceCollectionService()
    
    print("=" * 60)
    print("TEST 1: Extract from complex question")
    print("=" * 60)
    
    question = "gợi ý các lớp học buổi sáng, không học thứ 7, tôi muốn học vào thứ 5"
    preferences = service.extract_initial_preferences(question)
    
    print(f"\nQuestion: {question}")
    print(f"\nExtracted preferences:")
    print(f"  Time period: {preferences.time.time_period}")
    print(f"  Avoid time periods: {preferences.time.avoid_time_periods}")
    print(f"  Prefer days: {preferences.day.prefer_days}")
    print(f"  Avoid days: {preferences.day.avoid_days}")
    print(f"  Is complete: {preferences.is_complete()}")
    print(f"  Missing: {preferences.get_missing_preferences()}")
    
    print("\n" + "=" * 60)
    print("TEST 2: Extract from simple question")
    print("=" * 60)
    
    question = "gợi ý các lớp nên đăng ký kỳ sau"
    preferences = service.extract_initial_preferences(question)
    
    print(f"\nQuestion: {question}")
    print(f"\nExtracted preferences:")
    print(f"  Time period: {preferences.time.time_period}")
    print(f"  Prefer days: {preferences.day.prefer_days}")
    print(f"  Is complete: {preferences.is_complete()}")
    print(f"  Missing: {preferences.get_missing_preferences()}")
    
    # Get next question
    next_q = service.get_next_question(preferences)
    if next_q:
        print(f"\n📋 Next question to ask:")
        print(f"  Key: {next_q.key}")
        print(f"  Question: {next_q.question}")
        print(f"  Type: {next_q.type}")
        print(f"  Options: {next_q.options}")
    
    print("\n" + "=" * 60)
    print("TEST 3: Parse user responses")
    print("=" * 60)
    
    # Start with empty preferences
    preferences = CompletePreference()
    
    # Answer day question
    print("\n📅 User answers day question: 'Thứ 2, Thứ 3, Thứ 5'")
    preferences = service.parse_user_response(
        response="Thứ 2, Thứ 3, Thứ 5",
        question_key='day',
        current_preferences=preferences
    )
    print(f"  Updated prefer_days: {preferences.day.prefer_days}")
    
    # Answer time question
    print("\n⏰ User answers time question: '1' (Học sớm)")
    preferences = service.parse_user_response(
        response="1",
        question_key='time',
        current_preferences=preferences
    )
    print(f"  Updated prefer_early_start: {preferences.time.prefer_early_start}")
    print(f"  Updated time_period: {preferences.time.time_period}")
    
    # Answer continuous question
    print("\n📚 User answers continuous question: 'Không' (không muốn học liên tục)")
    preferences = service.parse_user_response(
        response="Không",
        question_key='continuous',
        current_preferences=preferences
    )
    print(f"  Updated prefer_continuous: {preferences.pattern.prefer_continuous}")
    
    # Check if complete
    print(f"\n✅ Is complete: {preferences.is_complete()}")
    print(f"📋 Missing: {preferences.get_missing_preferences()}")
    
    # Format summary
    print("\n" + "=" * 60)
    print("PREFERENCE SUMMARY")
    print("=" * 60)
    summary = service.format_preference_summary(preferences)
    print(summary)
    
    # Convert to dict for rule engine
    print("\n" + "=" * 60)
    print("DICT FOR RULE ENGINE")
    print("=" * 60)
    pref_dict = preferences.to_dict()
    for key, value in pref_dict.items():
        print(f"  {key}: {value}")


def test_conversation_flow():
    """Test full conversation flow"""
    from app.services.conversation_state import ConversationState, ConversationStateManager
    import uuid
    
    print("\n" + "=" * 60)
    print("TEST: CONVERSATION FLOW")
    print("=" * 60)
    
    manager = ConversationStateManager()
    service = PreferenceCollectionService()
    
    student_id = 1
    session_id = str(uuid.uuid4())
    
    # Step 1: User asks initial question
    print("\n📝 Step 1: User asks 'gợi ý các lớp học buổi sáng'")
    
    initial_question = "gợi ý các lớp học buổi sáng"
    initial_prefs = service.extract_initial_preferences(initial_question)
    
    state = ConversationState(student_id, session_id)
    state.preferences = initial_prefs
    state.stage = 'collecting'
    
    print(f"  Extracted: time_period={initial_prefs.time.time_period}")
    print(f"  Is complete: {initial_prefs.is_complete()}")
    print(f"  Missing: {initial_prefs.get_missing_preferences()}")
    
    # Get first question
    next_q = service.get_next_question(initial_prefs)
    state.current_question = next_q
    manager.save_state(state)
    
    print(f"\n❓ Bot asks: {next_q.question}")
    
    # Step 2: User answers day question
    print("\n📝 Step 2: User answers 'Thứ 2, Thứ 5'")
    
    user_response = "Thứ 2, Thứ 5"
    state = manager.get_state(student_id)
    
    state.preferences = service.parse_user_response(
        response=user_response,
        question_key=state.current_question.key,
        current_preferences=state.preferences
    )
    state.questions_asked.append(state.current_question.key)
    
    print(f"  Updated prefer_days: {state.preferences.day.prefer_days}")
    print(f"  Is complete: {state.preferences.is_complete()}")
    
    # Get next question
    next_q = service.get_next_question(state.preferences)
    if next_q:
        state.current_question = next_q
        manager.save_state(state)
        print(f"\n❓ Bot asks: {next_q.question}")
    else:
        print("\n✅ All preferences collected!")
        state.stage = 'completed'
        manager.save_state(state)
    
    # Step 3: User answers next question
    if next_q:
        print("\n📝 Step 3: User answers '2' (Học muộn)")
        
        user_response = "2"
        state = manager.get_state(student_id)
        
        state.preferences = service.parse_user_response(
            response=user_response,
            question_key=state.current_question.key,
            current_preferences=state.preferences
        )
        state.questions_asked.append(state.current_question.key)
        
        print(f"  Updated time prefs")
        print(f"  Is complete: {state.preferences.is_complete()}")
        
        if state.preferences.is_complete():
            print("\n✅ Preferences complete!")
            state.stage = 'completed'
            manager.save_state(state)
            
            # Show final summary
            summary = service.format_preference_summary(state.preferences)
            print("\n📋 Final preferences:")
            print(summary)
        else:
            next_q = service.get_next_question(state.preferences)
            if next_q:
                state.current_question = next_q
                manager.save_state(state)
                print(f"\n❓ Bot asks: {next_q.question}")


if __name__ == '__main__':
    test_preference_extraction()
    test_conversation_flow()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 60)
