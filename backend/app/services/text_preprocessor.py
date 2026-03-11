"""
Text Preprocessing Service for Vietnamese Text Normalization
Handles spell correction, keyboard typos, and text normalization before intent classification
"""
import json
import os
import re
import unicodedata
from typing import Dict, List, Optional, Set
from functools import lru_cache
from pathlib import Path


class TextPreprocessor:
    """
    Vietnamese text preprocessor for chatbot input normalization
    
    Features:
    - Unicode normalization (NFC)
    - Spell correction with custom Vietnamese dictionary
    - Keyboard typo correction
    - Vietnamese tone normalization
    - Abbreviation expansion
    """
    
    def __init__(self, dictionary_path: Optional[str] = None):
        """
        Initialize text preprocessor
        
        Args:
            dictionary_path: Path to Vietnamese dictionary JSON file
        """
        print("🔧 Initializing Text Preprocessor...")
        
        # Load custom dictionary
        if dictionary_path is None:
            dictionary_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data",
                "vietnamese_dictionary.json"
            )
        
        self.dictionary = self._load_dictionary(dictionary_path)
        self.whitelist: Set[str] = set(self.dictionary.get("whitelist", []))
        self.abbreviations: Dict[str, str] = self.dictionary.get("abbreviations", {})
        self.common_typos: Dict[str, str] = self.dictionary.get("common_typos", {})
        self.keyboard_patterns: Dict[str, str] = self.dictionary.get("keyboard_patterns", {})
        
        # Initialize spell checker (lazy loading)
        self._spell_checker = None
        
        print(f"✅ Text Preprocessor initialized")
        print(f"   - Whitelist: {len(self.whitelist)} terms")
        print(f"   - Abbreviations: {len(self.abbreviations)} mappings")
        print(f"   - Common typos: {len(self.common_typos)} patterns")
    
    def _load_dictionary(self, path: str) -> Dict:
        """Load Vietnamese dictionary from JSON file"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Dictionary file not found at {path}, using empty dictionary")
            return {
                "whitelist": [],
                "abbreviations": {},
                "common_typos": {},
                "keyboard_patterns": {}
            }
    
    @property
    def spell_checker(self):
        """Lazy load spell checker to improve startup time"""
        if self._spell_checker is None:
            try:
                from spellchecker import SpellChecker
                self._spell_checker = SpellChecker(language=None)  # Start with empty
                # We'll use our custom dictionary instead of built-in
            except ImportError:
                print("⚠️ pyspellchecker not installed, spell checking disabled")
                self._spell_checker = None
        return self._spell_checker
    
    def normalize_unicode(self, text: str) -> str:
        """
        Normalize Unicode characters to NFC form
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
            
        Example:
            Input: "café" (with combining characters)
            Output: "café" (with composed characters)
        """
        # Normalize to NFC (Canonical Composition)
        text = unicodedata.normalize('NFC', text)
        
        # Remove zero-width characters
        text = re.sub(r'[\u200b-\u200d\ufeff]', '', text)
        
        return text
    
    def expand_abbreviations(self, text: str) -> str:
        """
        Expand common Vietnamese abbreviations
        
        Args:
            text: Input text
            
        Returns:
            Text with expanded abbreviations
            
        Example:
            Input: "xem tkb t2 và t4"
            Output: "xem thời khóa biểu thứ 2 và thứ 4"
        """
        text_lower = text.lower()
        result = text
        
        # Sort by length (longest first) to avoid partial replacements
        sorted_abbrevs = sorted(self.abbreviations.items(), key=lambda x: len(x[0]), reverse=True)
        
        for abbrev, expansion in sorted_abbrevs:
            # Use word boundaries to avoid partial replacements
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            result = re.sub(pattern, expansion, result, flags=re.IGNORECASE)
        
        return result
    
    def fix_keyboard_typos(self, text: str) -> str:
        """
        Fix common keyboard typos based on QWERTY layout
        
        Args:
            text: Input text
            
        Returns:
            Text with fixed keyboard typos
            
        Example:
            Input: "thws 4"
            Output: "thứ 4"
        """
        result = text
        
        # Apply keyboard pattern corrections
        for typo, correction in self.keyboard_patterns.items():
            pattern = r'\b' + re.escape(typo) + r'\b'
            result = re.sub(pattern, correction, result, flags=re.IGNORECASE)
        
        return result
    
    def fix_common_typos(self, text: str) -> str:
        """
        Fix common Vietnamese typos from dictionary
        
        Args:
            text: Input text
            
        Returns:
            Text with fixed common typos
            
        Example:
            Input: "xin chai báo cái"
            Output: "xin chào báo cáo"
        """
        result = text
        
        # Sort by length (longest first) to handle multi-word typos
        sorted_typos = sorted(self.common_typos.items(), key=lambda x: len(x[0]), reverse=True)
        
        for typo, correction in sorted_typos:
            # For multi-word typos, don't use word boundaries
            if ' ' in typo:
                pattern = re.escape(typo)
            else:
                pattern = r'\b' + re.escape(typo) + r'\b'
            
            result = re.sub(pattern, correction, result, flags=re.IGNORECASE)
        
        return result
    
    @lru_cache(maxsize=1000)
    def _is_whitelisted(self, word: str) -> bool:
        """
        Check if word is in whitelist (cached for performance)
        
        Args:
            word: Word to check
            
        Returns:
            True if word is whitelisted
        """
        word_upper = word.upper()
        
        # Check exact match
        if word_upper in self.whitelist:
            return True
        
        # Check if it's a course code pattern (e.g., IT3170, SSH1131)
        if re.match(r'^[A-Z]{2,4}\d{3,4}$', word_upper):
            return True
        
        # Check if it's a number
        if word.isdigit():
            return True
        
        return False
    
    
    def fix_doubled_characters(self, text: str) -> str:
        """
        Fix doubled/tripled characters that are typos (fast-typing errors).

        Handles:
        - Triple+ chars: aaa → aa (first pass)
        - General doubled letters inside non-whitelisted words: taoo→tao, nhaan→nhan, bii→bi
        - Specific consonant-cluster rules at word start: dd→d, tt→t, nn→n, gg→g

        Whitelisted tokens (course codes like IT3080, SSH1131) are left untouched.

        Example:
            Input:  "taoo nhaan moonn bii IT3080"
            Output: "tao nhan mon bi IT3080"
        """
        # 1. Fix triple+ characters first (definitely typos: aaa → aa)
        text = re.sub(r'(.)\1{2,}', r'\1\1', text)

        # 2. Per-word doubled-letter reduction for non-whitelisted tokens
        #    Vietnamese has NO regular doubled letters, so any doubled letter
        #    in a plain word is a typo.
        VOWELS = (
            'aeiouàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩ'
            'òóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹ'
        )
        CONSONANTS = 'bcdfghjklmnpqrstvwxyzđ'
        ALL_LETTERS = VOWELS + CONSONANTS

        def _reduce_doubles(word: str) -> str:
            """Reduce all doubled letters in a word to single."""
            result = []
            prev = ''
            for ch in word:
                if ch.lower() in ALL_LETTERS and ch.lower() == prev.lower():
                    continue  # skip the duplicate
                result.append(ch)
                prev = ch
            return ''.join(result)

        words = text.split()
        fixed_words = []
        for word in words:
            if self._is_whitelisted(word):
                fixed_words.append(word)
            else:
                fixed_words.append(_reduce_doubles(word))
        text = ' '.join(fixed_words)

        # 3. Keep legacy specific consonant patterns at word start (handles edge-cases
        #    where the per-word loop may have missed accented pairs)
        old_patterns = {
            r'\bdd([aeiouàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹ])': r'd\1',
            r'\btt([aeiouàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹ])': r't\1',
            r'\bnn([aeiouàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹ])': r'n\1',
            r'\bgg([aeiouàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹ])': r'g\1',
        }
        for pattern, replacement in old_patterns.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text
    
    def fix_tone_errors(self, text: str) -> str:
        """
        Fix common Vietnamese tone mark errors
        
        Args:
            text: Input text
            
        Returns:
            Text with fixed tone marks
            
        Example:
            Input: "đầy đỷ"
            Output: "đầy đủ"
        """
        # Common tone mark confusions
        tone_corrections = {
            'đỷ': 'đủ',
            'ỷ': 'ủ',
            'điem': 'điểm',
            'diem': 'điểm',
            'đang': 'đăng',  # when it should be đăng ký
            'đang ky': 'đăng ký',
            'đang ki': 'đăng ký',
        }
        
        for wrong, correct in tone_corrections.items():
            text = re.sub(r'\b' + re.escape(wrong) + r'\b', correct, text, flags=re.IGNORECASE)
        
        return text
    
    def correct_spelling(self, text: str) -> str:
        """
        Correct spelling errors using pattern-based corrections
        
        Args:
            text: Input text
            
        Returns:
            Text with corrected spelling
            
        Pipeline:
            1. Fix doubled/tripled characters
            2. Fix tone mark errors
            3. Apply dictionary-based corrections (already done in other methods)
        """
        # Fix doubled characters
        text = self.fix_doubled_characters(text)
        
        # Fix tone errors
        text = self.fix_tone_errors(text)
        
        return text

    
    def normalize_vietnamese_tones(self, text: str) -> str:
        """
        Normalize Vietnamese tone marks
        
        Args:
            text: Input text
            
        Returns:
            Text with normalized tones
            
        Note:
            This is already handled by common_typos dictionary
        """
        # Already handled by fix_common_typos
        return text
    
    def _is_clean(self, text: str) -> bool:
        """
        Quick check if text is already clean (optimization)
        
        Args:
            text: Input text
            
        Returns:
            True if text appears clean
        """
        # Check if text contains only ASCII and Vietnamese characters
        if not re.search(r'[^\w\sàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', text, re.IGNORECASE):
            # Check if any known typos exist
            text_lower = text.lower()
            for typo in self.common_typos.keys():
                if typo in text_lower:
                    return False
            for typo in self.keyboard_patterns.keys():
                if typo in text_lower:
                    return False
            return True
        return False
    
    def preprocess(self, text: str, verbose: bool = False) -> str:
        """
        Main preprocessing pipeline
        
        Args:
            text: Input text to preprocess
            verbose: If True, print preprocessing steps
            
        Returns:
            Preprocessed text
            
        Pipeline:
            1. Unicode normalization
            2. Expand abbreviations
            3. Fix keyboard typos
            4. Fix common typos
            5. Spell correction (optional)
            
        Example:
            Input: "gogle lớp học t2 và thws 4"
            Output: "google lớp học thứ 2 và thứ 4"
        """
        if not text or not text.strip():
            return text
        
        # Quick check if already clean (optimization)
        if self._is_clean(text):
            if verbose:
                print("✅ Text is already clean, skipping preprocessing")
            return text
        
        original_text = text
        
        # 1. Unicode normalization
        text = self.normalize_unicode(text)
        if verbose and text != original_text:
            print(f"1️⃣ Unicode normalized: {original_text} → {text}")
        
        # 2. Expand abbreviations
        prev_text = text
        text = self.expand_abbreviations(text)
        if verbose and text != prev_text:
            print(f"2️⃣ Abbreviations expanded: {prev_text} → {text}")
        
        # 3. Fix keyboard typos
        prev_text = text
        text = self.fix_keyboard_typos(text)
        if verbose and text != prev_text:
            print(f"3️⃣ Keyboard typos fixed: {prev_text} → {text}")
        
        # 4. Fix common typos
        prev_text = text
        text = self.fix_common_typos(text)
        if verbose and text != prev_text:
            print(f"4️⃣ Common typos fixed: {prev_text} → {text}")
        
        # 5. Spell correction (pattern-based)
        prev_text = text
        text = self.correct_spelling(text)
        if verbose and text != prev_text:
            print(f"5️⃣ Spelling corrected: {prev_text} → {text}")

        
        if verbose:
            print(f"✨ Final result: {original_text} → {text}")
        
        return text


# Singleton instance for global use
_preprocessor_instance: Optional[TextPreprocessor] = None


def get_text_preprocessor() -> TextPreprocessor:
    """
    Get singleton instance of TextPreprocessor
    
    Returns:
        TextPreprocessor instance
    """
    global _preprocessor_instance
    if _preprocessor_instance is None:
        _preprocessor_instance = TextPreprocessor()
    return _preprocessor_instance
