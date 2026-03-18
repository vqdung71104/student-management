"""
Test Message Queue Service
Integration test for Redis + RabbitMQ
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest
import asyncio
from app.queue.message_queue_service import MessageQueueService


@pytest.mark.asyncio
async def test_handle_chat_message():
    """Test handling chat message"""
    success = await MessageQueueService.handle_chat_message(
        student_id=1,
        message="Tôi muốn đăng ký lớp",
        response="Bạn muốn học buổi nào?",
        intent="class_registration_suggestion",
        metadata={'step': 1}
    )
    
    assert success
    print("✅ Chat message handled successfully")
    
    # Verify cached in Redis
    history = await MessageQueueService.get_conversation_history(1)
    assert history is not None
    assert history['last_intent'] == 'class_registration_suggestion'
    print(f"✅ Conversation cached: {history['last_message']}")


@pytest.mark.asyncio
async def test_update_class_preferences_incremental():
    """Test incremental preference updates"""
    student_id = 1
    
    # Step 1: Time period
    prefs = await MessageQueueService.update_class_preferences(
        student_id=student_id,
        preference_key='time_period',
        preference_value='morning',
        step='in_progress'
    )
    assert prefs is not None
    assert prefs['time_period'] == 'morning'
    print(f"✅ Step 1: {prefs}")
    
    # Step 2: Avoid early
    prefs = await MessageQueueService.update_class_preferences(
        student_id=student_id,
        preference_key='avoid_early_start',
        preference_value=True,
        step='in_progress'
    )
    assert prefs['time_period'] == 'morning'  # Previous value preserved
    assert prefs['avoid_early_start'] == True
    print(f"✅ Step 2: {prefs}")
    
    # Step 3: Avoid days
    prefs = await MessageQueueService.update_class_preferences(
        student_id=student_id,
        preference_key='avoid_days',
        preference_value=['Saturday', 'Sunday'],
        step='in_progress'
    )
    assert len(prefs) >= 3  # All preferences accumulated
    print(f"✅ Step 3: {prefs}")
    
    # Step 4: Complete
    prefs = await MessageQueueService.update_class_preferences(
        student_id=student_id,
        preference_key='preferred_teachers',
        preference_value=['Nguyễn Văn A'],
        step='complete'
    )
    assert prefs['step'] == 'complete'
    print(f"✅ Step 4 (Complete): {prefs}")


@pytest.mark.asyncio
async def test_get_current_preferences():
    """Test getting current preferences"""
    student_id = 1
    
    # Update some preferences
    await MessageQueueService.update_class_preferences(
        student_id=student_id,
        preference_key='time_period',
        preference_value='afternoon',
        step='in_progress'
    )
    
    # Get preferences
    prefs = await MessageQueueService.get_current_preferences(student_id)
    assert prefs is not None
    assert prefs['time_period'] == 'afternoon'
    print(f"✅ Current preferences: {prefs}")


@pytest.mark.asyncio
async def test_clear_preferences():
    """Test clearing preferences"""
    student_id = 1
    
    # Set preferences
    await MessageQueueService.update_class_preferences(
        student_id=student_id,
        preference_key='time_period',
        preference_value='morning',
        step='in_progress'
    )
    
    # Verify exists
    prefs = await MessageQueueService.get_current_preferences(student_id)
    assert prefs is not None
    
    # Clear
    success = await MessageQueueService.clear_preferences(student_id)
    assert success
    
    # Verify cleared
    prefs = await MessageQueueService.get_current_preferences(student_id)
    assert prefs is None
    print("✅ Preferences cleared")





@pytest.mark.asyncio
async def test_full_workflow():
    """Test full workflow: chat + preferences + notification"""
    student_id = 2
    
    print("\n🔄 Testing full workflow...\n")
    
    # 1. User asks for class registration
    print("1️⃣ User: Tôi muốn đăng ký lớp")
    await MessageQueueService.handle_chat_message(
        student_id=student_id,
        message="Tôi muốn đăng ký lớp",
        response="Bạn muốn học buổi nào?",
        intent="class_registration_suggestion",
        metadata={'step': 'ask_time_period'}
    )
    
    # 2. User answers: morning
    print("2️⃣ User: Tôi muốn học sáng")
    await MessageQueueService.update_class_preferences(
        student_id=student_id,
        preference_key='time_period',
        preference_value='morning',
        step='in_progress'
    )
    await MessageQueueService.handle_chat_message(
        student_id=student_id,
        message="Tôi muốn học sáng",
        response="Bạn có muốn tránh học sớm (trước 8:00) không?",
        intent="class_registration_suggestion",
        metadata={'step': 'ask_avoid_early'}
    )
    
    # 3. User answers: yes, avoid early
    print("3️⃣ User: Có, tôi muốn tránh học sớm")
    await MessageQueueService.update_class_preferences(
        student_id=student_id,
        preference_key='avoid_early_start',
        preference_value=True,
        step='in_progress'
    )
    await MessageQueueService.handle_chat_message(
        student_id=student_id,
        message="Có, tôi muốn tránh học sớm",
        response="Bạn muốn tránh học vào ngày nào trong tuần?",
        intent="class_registration_suggestion",
        metadata={'step': 'ask_avoid_days'}
    )
    
    # 4. User answers: Saturday
    print("4️⃣ User: Tôi không muốn học thứ 7")
    await MessageQueueService.update_class_preferences(
        student_id=student_id,
        preference_key='avoid_days',
        preference_value=['Saturday'],
        step='complete'
    )
    await MessageQueueService.handle_chat_message(
        student_id=student_id,
        message="Tôi không muốn học thứ 7",
        response="Đang tìm kiếm lớp phù hợp...",
        intent="class_registration_suggestion",
        metadata={'step': 'searching'}
    )
    
    # 5. Show results
    print("5️⃣ Bot: Tìm thấy 5 lớp phù hợp")
    await MessageQueueService.handle_chat_message(
        student_id=student_id,
        message="",
        response="Đây là các lớp phù hợp: IT3170-001, IT3080-002...",
        intent="class_registration_result",
        metadata={'step': 'show_results', 'found_classes': 5}
    )
    
    # 6. Send notification
    print("6️⃣ Send notification about registration deadline")
    await MessageQueueService.send_notification(
        student_id=student_id,
        notification_type='deadline_reminder',
        title='Nhắc nhở đăng ký',
        content='Hạn đăng ký học phần là 31/12/2025',
        metadata={'deadline': '2025-12-31'}
    )
    
    # 7. Verify final state
    final_prefs = await MessageQueueService.get_current_preferences(student_id)
    print(f"\n✅ Final preferences: {final_prefs}")
    
    history = await MessageQueueService.get_conversation_history(student_id)
    print(f"✅ Final conversation: {history['last_intent']}")
    
    print("\n✅ Full workflow completed!")


if __name__ == "__main__":
    print("🧪 Running Message Queue Service Tests...\n")
    
    # Run with pytest
    pytest.main([__file__, "-v", "-s"])
