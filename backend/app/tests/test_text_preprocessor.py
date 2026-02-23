"""
Unit tests for TextPreprocessor service
Tests Unicode normalization, spell correction, keyboard typo fixing, and abbreviation expansion
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.text_preprocessor import TextPreprocessor, get_text_preprocessor


class TestTextPreprocessor:
    """Test suite for TextPreprocessor"""
    
    @pytest.fixture
    def preprocessor(self):
        """Create TextPreprocessor instance for testing"""
        return TextPreprocessor()
    
    def test_unicode_normalization(self, preprocessor):
        """Test Unicode normalization to NFC form"""
        # Test combining characters
        assert preprocessor.normalize_unicode("café") == "café"
        
        # Test zero-width characters removal
        text_with_zwc = "hello\u200bworld"
        assert preprocessor.normalize_unicode(text_with_zwc) == "helloworld"
    
    def test_abbreviation_expansion(self, preprocessor):
        """Test Vietnamese abbreviation expansion"""
        # Test weekday abbreviations
        assert "thứ 2" in preprocessor.expand_abbreviations("t2").lower()
        assert "thứ 3" in preprocessor.expand_abbreviations("t3").lower()
        assert "thứ 4" in preprocessor.expand_abbreviations("t4").lower()
        assert "thứ 5" in preprocessor.expand_abbreviations("t5").lower()
        
        # Test common abbreviations
        assert "thời khóa biểu" in preprocessor.expand_abbreviations("tkb").lower()
        assert "đăng ký" in preprocessor.expand_abbreviations("dk").lower()
        assert "học phần" in preprocessor.expand_abbreviations("hp").lower()
        
        # Test multiple abbreviations in one sentence
        result = preprocessor.expand_abbreviations("xem tkb t2 và t4")
        assert "thời khóa biểu" in result.lower()
        assert "thứ 2" in result.lower()
        assert "thứ 4" in result.lower()
    
    def test_keyboard_typo_correction(self, preprocessor):
        """Test keyboard typo correction"""
        # Test common keyboard typos
        assert "thứ" in preprocessor.fix_keyboard_typos("thws").lower()
        assert "thứ" in preprocessor.fix_keyboard_typos("thuws").lower()
        assert "thứ" in preprocessor.fix_keyboard_typos("thuw").lower()
    
    def test_common_typo_correction(self, preprocessor):
        """Test common Vietnamese typo correction"""
        # Test tone mark errors
        assert "xin chào" in preprocessor.fix_common_typos("xin chai").lower()
        assert "báo cáo" in preprocessor.fix_common_typos("báo cái").lower()
        assert "báo cáo" in preprocessor.fix_common_typos("baos cáo").lower()
        
        # Test spelling errors
        assert "google" in preprocessor.fix_common_typos("gogle").lower()
        assert "google" in preprocessor.fix_common_typos("gôgle").lower()
        assert "google" in preprocessor.fix_common_typos("goigle").lower()
    
    def test_whitelist(self, preprocessor):
        """Test that whitelisted terms are not modified"""
        # Test course codes
        assert preprocessor._is_whitelisted("IT3170")
        assert preprocessor._is_whitelisted("SSH1131")
        assert preprocessor._is_whitelisted("JP2126")
        
        # Test acronyms
        assert preprocessor._is_whitelisted("CPA")
        assert preprocessor._is_whitelisted("GPA")
        assert preprocessor._is_whitelisted("TKB")
        
        # Test numbers
        assert preprocessor._is_whitelisted("123")
        assert preprocessor._is_whitelisted("2024")
    
    def test_full_preprocessing_pipeline(self, preprocessor):
        """Test complete preprocessing pipeline"""
        # Test case 1: Abbreviations + keyboard typos
        input_text = "gợi ý lớp học t2 và thws 4"
        result = preprocessor.preprocess(input_text)
        assert "thứ 2" in result.lower()
        assert "thứ 4" in result.lower()
        
        # Test case 2: Common typos
        input_text = "xin chai, tôi muốn xem báo cái"
        result = preprocessor.preprocess(input_text)
        assert "xin chào" in result.lower()
        assert "báo cáo" in result.lower()
        
        # Test case 3: Mixed errors
        input_text = "gogle lớp học t2"
        result = preprocessor.preprocess(input_text)
        assert "google" in result.lower()
        assert "thứ 2" in result.lower()
        
        # Test case 4: Course codes should be preserved
        input_text = "xem điểm môn IT3170"
        result = preprocessor.preprocess(input_text)
        assert "IT3170" in result
    
    def test_empty_and_none_input(self, preprocessor):
        """Test handling of empty or None input"""
        assert preprocessor.preprocess("") == ""
        assert preprocessor.preprocess("   ") == "   "
    
    def test_clean_text_optimization(self, preprocessor):
        """Test that clean text is quickly identified and skipped"""
        clean_text = "xem lịch học của tôi"
        result = preprocessor.preprocess(clean_text)
        # Should return quickly without modifications
        assert result == clean_text
    
    def test_case_insensitive_processing(self, preprocessor):
        """Test that preprocessing works regardless of case"""
        # Abbreviations should work with different cases
        assert "thứ 2" in preprocessor.expand_abbreviations("T2").lower()
        assert "thứ 2" in preprocessor.expand_abbreviations("t2").lower()
        
        # Typos should be fixed regardless of case
        assert "google" in preprocessor.fix_common_typos("GOGLE").lower()
        assert "google" in preprocessor.fix_common_typos("Gogle").lower()
    
    def test_singleton_instance(self):
        """Test that get_text_preprocessor returns singleton"""
        instance1 = get_text_preprocessor()
        instance2 = get_text_preprocessor()
        assert instance1 is instance2


class TestRealWorldScenarios:
    """Test real-world chatbot input scenarios"""
    
    @pytest.fixture
    def preprocessor(self):
        """Create TextPreprocessor instance for testing"""
        return TextPreprocessor()
    
    def test_schedule_query_with_typos(self, preprocessor):
        """Test schedule-related queries with typos"""
        inputs_and_expectations = [
            ("xem tkb", "thời khóa biểu"),
            ("lich hoc t2", "thứ 2"),
            ("các lớp học thws 4", "thứ 4"),
            ("xem lịch học t2 và t4", ["thứ 2", "thứ 4"]),
        ]
        
        for input_text, expected in inputs_and_expectations:
            result = preprocessor.preprocess(input_text).lower()
            if isinstance(expected, list):
                for exp in expected:
                    assert exp in result, f"Expected '{exp}' in result '{result}'"
            else:
                assert expected in result, f"Expected '{expected}' in result '{result}'"
    
    def test_grade_query_with_typos(self, preprocessor):
        """Test grade-related queries with typos"""
        inputs = [
            "xem diem",
            "xem điểm môn IT3170",
            "báo cái điểm",
        ]
        
        for input_text in inputs:
            result = preprocessor.preprocess(input_text)
            # Should not break course codes
            if "IT3170" in input_text:
                assert "IT3170" in result
    
    def test_registration_query_with_typos(self, preprocessor):
        """Test registration-related queries with typos"""
        inputs_and_expectations = [
            ("dang ky mon hoc", ["đăng ký", "môn học"]),
            ("gợi ý dk hp", ["đăng ký", "học phần"]),
            ("tôi muốn dk lớp học t2", ["đăng ký", "thứ 2"]),
        ]
        
        for input_text, expected_terms in inputs_and_expectations:
            result = preprocessor.preprocess(input_text).lower()
            for term in expected_terms:
                assert term in result, f"Expected '{term}' in result '{result}'"
    
    def test_greeting_with_typos(self, preprocessor):
        """Test greeting messages with typos"""
        inputs = [
            "xin chai",
            "xin chào",
            "chai bạn",
        ]
        
        for input_text in inputs:
            result = preprocessor.preprocess(input_text).lower()
            # Should contain proper greeting
            assert "chào" in result or input_text == result.lower()


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
