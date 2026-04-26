"""Test JSON extraction helper for LLM responses."""
import sys
sys.path.insert(0, ".")
from app.llm.llm_client import extract_json_from_text, safe_parse_llm_response


def test_clean_json():
    result = extract_json_from_text('{"intent": "grade_view", "confidence": 0.9}')
    assert result == {"intent": "grade_view", "confidence": 0.9}, f"test_clean_json failed: {result}"
    print("test_clean_json PASS")


def test_json_with_text_before():
    result = extract_json_from_text('Here is the result: {"intent": "grade_view", "confidence": 0.9}')
    assert result == {"intent": "grade_view", "confidence": 0.9}, f"test_json_with_text_before failed: {result}"
    print("test_json_with_text_before PASS")


def test_json_with_text_after():
    result = extract_json_from_text('{"intent": "grade_view", "confidence": 0.9} is my answer')
    assert result == {"intent": "grade_view", "confidence": 0.9}, f"test_json_with_text_after failed: {result}"
    print("test_json_with_text_after PASS")


def test_json_with_text_both_sides():
    result = extract_json_from_text('Answer: {"intent": "grade_view", "confidence": 0.9} - end')
    assert result == {"intent": "grade_view", "confidence": 0.9}, f"test_json_with_text_both_sides failed: {result}"
    print("test_json_with_text_both_sides PASS")


def test_nested_json():
    result = extract_json_from_text('{"data": {"score": 85}, "meta": "ok"}')
    assert result == {"data": {"score": 85}, "meta": "ok"}, f"test_nested_json failed: {result}"
    print("test_nested_json PASS")


def test_empty_string():
    result = extract_json_from_text("")
    assert result is None, f"test_empty_string failed: {result}"
    print("test_empty_string PASS")


def test_non_json():
    result = extract_json_from_text("Hello world, this is not JSON")
    assert result is None, f"test_non_json failed: {result}"
    print("test_non_json PASS")


def test_safe_parse_fallback():
    result = safe_parse_llm_response("not json at all")
    assert isinstance(result, dict), f"test_safe_parse_fallback failed: {result}"
    assert "text" in result, f"test_safe_parse_fallback failed: {result}"
    assert "error" in result, f"test_safe_parse_fallback failed: {result}"
    assert result["error"] == "parse_failed", f"test_safe_parse_fallback failed: {result}"
    print("test_safe_parse_fallback PASS")


def test_safe_parse_success():
    result = safe_parse_llm_response('{"key": "value"}')
    assert result == {"key": "value"}, f"test_safe_parse_success failed: {result}"
    print("test_safe_parse_success PASS")


def test_multiline_json():
    raw = '''The answer is:
{
    "intent": "grade_view",
    "confidence": 0.95,
    "data": [1, 2, 3]
}
That's all.'''
    result = extract_json_from_text(raw)
    assert result["intent"] == "grade_view", f"test_multiline_json failed: {result}"
    print("test_multiline_json PASS")


def test_llm_realistic_response():
    """Simulate a realistic LLM response with extra commentary."""
    raw = '''Sure! Here is the classification result:

{"intent": "schedule_view", "confidence": 0.87, "method": "tfidf_word2vec"}

Let me know if you need anything else!'''
    result = extract_json_from_text(raw)
    assert result["intent"] == "schedule_view", f"test_llm_realistic_response failed: {result}"
    print("test_llm_realistic_response PASS")


if __name__ == "__main__":
    test_clean_json()
    test_json_with_text_before()
    test_json_with_text_after()
    test_json_with_text_both_sides()
    test_nested_json()
    test_empty_string()
    test_non_json()
    test_safe_parse_fallback()
    test_safe_parse_success()
    test_multiline_json()
    test_llm_realistic_response()
    print("\n=== All tests passed! ===")
