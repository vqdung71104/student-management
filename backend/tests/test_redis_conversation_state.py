"""
Test Redis Conversation State Manager
Test Phase 4 implementation
"""
import time
from app.services.conversation_state import (
    ConversationState,
    RedisConversationStateManager,
    get_redis_conversation_manager
)
from app.schemas.preference_schema import CompletePreference


def test_redis_state_save_and_get():
    """Test save and get conversation state from Redis"""
    print("=" * 60)
    print("TEST 1: Redis Save and Get")
    print("=" * 60)
    
    try:
        manager = get_redis_conversation_manager()
        
        # Create test state
        state = ConversationState(
            student_id=12345,
            session_id="test_session_001",
            intent="class_registration_suggestion"
        )
        state.stage = "collecting_preferences"
        # Set preferences using nested structure
        state.preferences.time.time_period = "morning"
        state.preferences.day.prefer_days = ["Monday", "Wednesday"]
        state.questions_asked = ["day", "time"]
        state.questions_remaining = ["continuous", "free_days"]
        state.pending_question = {
            'key': 'continuous',
            'question': 'Bạn thích học liên tục không?',
            'options': ['Có', 'Không']
        }
        
        print(f"\nSaving state for student 12345...")
        manager.save_state(state)
        
        print(f"Retrieving state...")
        retrieved_state = manager.get_state(12345)
        
        if retrieved_state:
            print(f"✅ State retrieved successfully")
            print(f"  Student ID: {retrieved_state.student_id}")
            print(f"  Session ID: {retrieved_state.session_id}")
            print(f"  Stage: {retrieved_state.stage}")
            print(f"  Time period: {retrieved_state.preferences.time.time_period}")
            print(f"  Prefer days: {retrieved_state.preferences.day.prefer_days}")
            print(f"  Questions asked: {retrieved_state.questions_asked}")
            print(f"  Questions remaining: {retrieved_state.questions_remaining}")
            print(f"  Pending question: {retrieved_state.pending_question}")
            
            assert retrieved_state.student_id == 12345
            assert retrieved_state.stage == "collecting_preferences"
            assert retrieved_state.preferences.time.time_period == "morning"
            assert len(retrieved_state.questions_asked) == 2
            assert len(retrieved_state.questions_remaining) == 2
            assert retrieved_state.pending_question is not None
            
            print("\n✅ TEST 1 PASSED")
        else:
            print("❌ Failed to retrieve state")
            assert False
    
    except Exception as e:
        print(f"❌ TEST 1 FAILED: {e}")
        raise


def test_redis_state_delete():
    """Test delete conversation state from Redis"""
    print("\n" + "=" * 60)
    print("TEST 2: Redis Delete")
    print("=" * 60)
    
    try:
        manager = get_redis_conversation_manager()
        
        # Create and save test state
        state = ConversationState(
            student_id=54321,
            session_id="test_session_002"
        )
        manager.save_state(state)
        
        print(f"\nState saved for student 54321")
        
        # Verify it exists
        retrieved = manager.get_state(54321)
        assert retrieved is not None
        print(f"✅ State exists")
        
        # Delete it
        print(f"Deleting state...")
        manager.delete_state(54321)
        
        # Verify it's gone
        retrieved = manager.get_state(54321)
        assert retrieved is None
        print(f"✅ State deleted successfully")
        
        print("\n✅ TEST 2 PASSED")
    
    except Exception as e:
        print(f"❌ TEST 2 FAILED: {e}")
        raise


def test_redis_state_ttl():
    """Test state expiration with TTL"""
    print("\n" + "=" * 60)
    print("TEST 3: Redis TTL (Fast Test)")
    print("=" * 60)
    
    try:
        # Create manager with short TTL (5 seconds for testing)
        manager = RedisConversationStateManager(ttl_seconds=5)
        
        state = ConversationState(
            student_id=99999,
            session_id="test_session_ttl"
        )
        
        print(f"\nSaving state with 5 second TTL...")
        manager.save_state(state)
        
        # Immediate retrieval should work
        retrieved = manager.get_state(99999)
        assert retrieved is not None
        print(f"✅ State exists immediately after save")
        
        # Wait 6 seconds
        print(f"Waiting 6 seconds for TTL expiration...")
        time.sleep(6)
        
        # Should be expired now
        retrieved = manager.get_state(99999)
        assert retrieved is None
        print(f"✅ State expired after TTL")
        
        print("\n✅ TEST 3 PASSED")
    
    except Exception as e:
        print(f"❌ TEST 3 FAILED: {e}")
        raise


def test_redis_has_active_conversation():
    """Test has_active_conversation method"""
    print("\n" + "=" * 60)
    print("TEST 4: Has Active Conversation")
    print("=" * 60)
    
    try:
        manager = get_redis_conversation_manager()
        
        # Test 1: No conversation
        has_active = manager.has_active_conversation(77777)
        assert not has_active
        print(f"✅ No active conversation for student 77777")
        
        # Test 2: Create active conversation
        state = ConversationState(
            student_id=77777,
            session_id="test_session_active"
        )
        state.stage = "collecting_preferences"
        manager.save_state(state)
        
        has_active = manager.has_active_conversation(77777)
        assert has_active
        print(f"✅ Active conversation detected for student 77777")
        
        # Test 3: Completed conversation (not active)
        state.stage = "completed"
        manager.save_state(state)
        
        has_active = manager.has_active_conversation(77777)
        assert not has_active
        print(f"✅ Completed conversation not counted as active")
        
        # Cleanup
        manager.delete_state(77777)
        
        print("\n✅ TEST 4 PASSED")
    
    except Exception as e:
        print(f"❌ TEST 4 FAILED: {e}")
        raise


def test_redis_multiple_students():
    """Test multiple student conversations simultaneously"""
    print("\n" + "=" * 60)
    print("TEST 5: Multiple Students")
    print("=" * 60)
    
    try:
        manager = get_redis_conversation_manager()
        
        # Create states for 3 students
        students = [11111, 22222, 33333]
        
        print(f"\nCreating conversations for 3 students...")
        for student_id in students:
            state = ConversationState(
                student_id=student_id,
                session_id=f"session_{student_id}"
            )
            state.stage = "collecting_preferences"
            state.questions_asked = [f"question_{student_id}"]
            manager.save_state(state)
        
        print(f"✅ All states saved")
        
        # Verify all can be retrieved
        print(f"\nVerifying all states...")
        for student_id in students:
            state = manager.get_state(student_id)
            assert state is not None
            assert state.student_id == student_id
            assert state.session_id == f"session_{student_id}"
            print(f"  ✅ Student {student_id}: OK")
        
        # Delete all
        print(f"\nCleaning up...")
        for student_id in students:
            manager.delete_state(student_id)
        
        # Verify all deleted
        for student_id in students:
            state = manager.get_state(student_id)
            assert state is None
        
        print(f"✅ All states cleaned up")
        
        print("\n✅ TEST 5 PASSED")
    
    except Exception as e:
        print(f"❌ TEST 5 FAILED: {e}")
        raise


def cleanup_test_data():
    """Cleanup any test data left in Redis"""
    print("\n" + "=" * 60)
    print("CLEANUP: Removing test data")
    print("=" * 60)
    
    try:
        manager = get_redis_conversation_manager()
        test_students = [12345, 54321, 99999, 77777, 11111, 22222, 33333]
        
        for student_id in test_students:
            try:
                manager.delete_state(student_id)
            except:
                pass
        
        print("✅ Cleanup completed")
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")


if __name__ == '__main__':
    try:
        test_redis_state_save_and_get()
        test_redis_state_delete()
        test_redis_state_ttl()
        test_redis_has_active_conversation()
        test_redis_multiple_students()
        
        print("\n" + "=" * 60)
        print("✅ ALL REDIS TESTS COMPLETED")
        print("=" * 60)
        print("\n🚀 Phase 4 Implementation Benefits:")
        print("  • Persistent state across server restarts")
        print("  • Automatic TTL expiration (1 hour)")
        print("  • Multiple concurrent conversations")
        print("  • Production-ready with Redis")
        
    except Exception as e:
        print(f"\n❌ TESTS FAILED: {e}")
    finally:
        cleanup_test_data()
