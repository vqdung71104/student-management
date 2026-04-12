import uuid

from app.services.conversation_state import ConversationState, ConversationStateManager


def test_conversation_state_manager_uses_conversation_id_as_key():
    manager = ConversationStateManager()
    state = ConversationState(
        student_id=1,
        session_id=str(uuid.uuid4()),
        conversation_id=101,
    )
    state.stage = "collecting"

    manager.save_state(state)

    loaded = manager.get_state(101)
    assert loaded is not None
    assert loaded.conversation_id == 101
    assert loaded.student_id == 1
    assert loaded.stage == "collecting"


def test_conversation_state_manager_keeps_conversations_isolated():
    manager = ConversationStateManager()

    first = ConversationState(
        student_id=1,
        session_id=str(uuid.uuid4()),
        conversation_id=101,
    )
    first.stage = "collecting"

    second = ConversationState(
        student_id=1,
        session_id=str(uuid.uuid4()),
        conversation_id=202,
    )
    second.stage = "choose_subject_source"

    manager.save_state(first)
    manager.save_state(second)

    manager.delete_state(101)

    assert manager.get_state(101) is None
    remaining = manager.get_state(202)
    assert remaining is not None
    assert remaining.conversation_id == 202
    assert remaining.stage == "choose_subject_source"
