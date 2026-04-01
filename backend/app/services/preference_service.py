"""
Preference Collection Service
Handles multi-turn conversation for collecting user preferences
"""
from typing import Dict, List, Optional, Tuple
import re
import unicodedata
from app.schemas.preference_schema import (
    CompletePreference, 
    TimePreference, 
    DayPreference, 
    ContinuousPreference,
    FreeDaysPreference,
    SpecificRequirement,
    PREFERENCE_QUESTIONS,
    PreferenceQuestion
)


class PreferenceCollectionService:
    """Service for collecting preferences through conversation"""
    
    # Vietnamese day mapping
    DAY_MAPPING = {
        'thứ 2': 'Monday',
        'thứ hai': 'Monday',
        't2': 'Monday',
        'thứ 3': 'Tuesday',
        'thứ ba': 'Tuesday',
        't3': 'Tuesday',
        'thứ 4': 'Wednesday',
        'thứ tư': 'Wednesday',
        't4': 'Wednesday',
        'thứ 5': 'Thursday',
        'thứ năm': 'Thursday',
        't5': 'Thursday',
        'thứ 6': 'Friday',
        'thứ sáu': 'Friday',
        't6': 'Friday',
        'thứ 7': 'Saturday',
        'thứ bảy': 'Saturday',
        't7': 'Saturday',
        'chủ nhật': 'Sunday',
        'cn': 'Sunday'
    }
    
    def __init__(self):
        pass

    def _normalize_response_text(self, text: str) -> str:
        normalized = unicodedata.normalize('NFC', (text or '').strip().lower())
        normalized = re.sub(r'\s+', ' ', normalized)

        typo_replacements = {
            'thú': 'thứ',
            'thu ': 'thứ ',
            'thu,': 'thứ,',
            'thu2': 'thứ 2',
            'thu3': 'thứ 3',
            'thu4': 'thứ 4',
            'thu5': 'thứ 5',
            'thu6': 'thứ 6',
            'thu7': 'thứ 7',
        }
        for wrong, right in typo_replacements.items():
            normalized = normalized.replace(wrong, right)

        normalized = re.sub(r'\bthứ\s*,', 'thứ ', normalized)
        normalized = re.sub(r'\bthứ\s*([2-7])\b', r'thứ \1', normalized)
        return normalized

    def _extract_days_from_response(self, response_lower: str) -> List[str]:
        day_map = {
            '2': 'Monday',
            '3': 'Tuesday',
            '4': 'Wednesday',
            '5': 'Thursday',
            '6': 'Friday',
            '7': 'Saturday',
        }

        extracted_days: List[str] = []

        compact_patterns = [
            r'\bth[ứu]\s*([2-7](?:\s*,\s*[2-7])+)',
            r'\bt\s*([2-7](?:\s*,\s*[2-7])+)',
            r'\bt([2-7](?:\s*,\s*[2-7])+)',
        ]
        for pattern in compact_patterns:
            for match in re.findall(pattern, response_lower):
                for num in re.findall(r'[2-7]', match):
                    en_day = day_map.get(num)
                    if en_day and en_day not in extracted_days:
                        extracted_days.append(en_day)

        for full_match in re.findall(r'\bth[ứu]\s*([2-7])\b', response_lower):
            en_day = day_map.get(full_match)
            if en_day and en_day not in extracted_days:
                extracted_days.append(en_day)

        for short_match in re.findall(r'\bt\s*([2-7])\b', response_lower):
            en_day = day_map.get(short_match)
            if en_day and en_day not in extracted_days:
                extracted_days.append(en_day)

        for vn_day, en_day in self.DAY_MAPPING.items():
            if vn_day in response_lower and en_day not in extracted_days:
                extracted_days.append(en_day)

        return extracted_days
    
    def extract_initial_preferences(self, question: str) -> CompletePreference:
        """
        Extract preferences from initial user question
        Similar to existing _extract_preferences_from_question
        """
        question_lower = question.lower()
        preferences = CompletePreference()
        
        # Extract time preferences
        time_pref = self._extract_time_preferences(question_lower)
        preferences.time = time_pref
        
        # Extract day preferences
        day_pref = self._extract_day_preferences(question_lower)
        preferences.day = day_pref
        
        # Extract continuous and free_days preferences
        continuous_pref, free_days_pref = self._extract_pattern_preferences(question_lower)
        preferences.continuous = continuous_pref
        preferences.free_days = free_days_pref
        
        # Extract specific requirements
        specific_req = self._extract_specific_requirements(question_lower)
        preferences.specific = specific_req
        
        return preferences
    
    def _extract_time_preferences(self, question: str) -> TimePreference:
        """Extract time-related preferences"""
        time_pref = TimePreference()
        
        # Check for negation before keyword
        def has_negation_before(text: str, pattern: str, max_distance: int = 20) -> bool:
            pattern_pos = text.find(pattern)
            if pattern_pos == -1:
                return False
            start_pos = max(0, pattern_pos - max_distance)
            preceding_text = text[start_pos:pattern_pos]
            negation_words = ['không', 'tránh', 'chẳng', 'không muốn', 'ko']
            return any(neg in preceding_text for neg in negation_words)
        
        # Time period patterns
        time_patterns = {
            'sáng': 'morning',
            'buổi sáng': 'morning',
            'chiều': 'afternoon',
            'buổi chiều': 'afternoon'
        }
        
        for pattern, period in time_patterns.items():
            if pattern in question:
                if has_negation_before(question, pattern):
                    # Negative preference
                    time_pref.avoid_time_periods.append(period)
                else:
                    # Positive preference
                    time_pref.time_period = period
                break
        
        # Check early/late preferences
        if 'học sớm' in question or 'sớm' in question:
            if has_negation_before(question, 'sớm'):
                time_pref.avoid_early_start = True
            else:
                time_pref.prefer_early_start = True
        
        if 'học muộn' in question or 'muộn' in question or 'đến muộn' in question:
            if has_negation_before(question, 'muộn'):
                time_pref.avoid_late_end = True
            else:
                time_pref.prefer_late_start = True
        
        return time_pref
    
    def _extract_day_preferences(self, question: str) -> DayPreference:
        """Extract day-related preferences"""
        day_pref = DayPreference()
        
        def has_negation_before(text: str, pattern: str, max_distance: int = 20) -> bool:
            pattern_pos = text.find(pattern)
            if pattern_pos == -1:
                return False
            start_pos = max(0, pattern_pos - max_distance)
            preceding_text = text[start_pos:pattern_pos]
            negation_words = ['không', 'tránh', 'chẳng', 'không muốn', 'ko']
            return any(neg in preceding_text for neg in negation_words)
        
        # Extract days
        for vn_day, en_day in self.DAY_MAPPING.items():
            if vn_day in question:
                if has_negation_before(question, vn_day):
                    if en_day not in day_pref.avoid_days:
                        day_pref.avoid_days.append(en_day)
                else:
                    # Check context for prefer
                    if any(keyword in question for keyword in ['muốn học', 'thích học', 'học vào']):
                        if en_day not in day_pref.prefer_days:
                            day_pref.prefer_days.append(en_day)
        
        return day_pref
    
    def _extract_pattern_preferences(self, question: str) -> tuple[ContinuousPreference, FreeDaysPreference]:
        """Extract continuous and free_days preferences separately"""
        continuous_pref = ContinuousPreference()
        free_days_pref = FreeDaysPreference()
        
        # Continuous study
        if any(keyword in question for keyword in ['liên tục', 'học dồn', 'nhiều lớp 1 buổi']):
            if any(neg in question for neg in ['không', 'tránh']):
                continuous_pref.prefer_continuous = False
            else:
                continuous_pref.prefer_continuous = True
        
        # Free days
        if any(keyword in question for keyword in ['nghỉ nhiều', 'ít ngày', 'học ít ngày', 'tối đa hóa ngày nghỉ']):
            free_days_pref.prefer_free_days = True
        
        return continuous_pref, free_days_pref
    
    def _extract_specific_requirements(self, question: str) -> SpecificRequirement:
        """Extract specific requirements"""
        specific_req = SpecificRequirement()
        
        # Extract teacher names (simplified)
        teacher_pattern = r'giáo viên\s+([A-ZĐĂÂÊÔƠƯ][a-zđăâêôơư]+(?:\s+[A-ZĐĂÂÊÔƠƯ][a-zđăâêôơư]+)*)'
        teacher_matches = re.findall(teacher_pattern, question)
        if teacher_matches:
            specific_req.preferred_teachers = teacher_matches
        
        # Extract class IDs
        class_id_pattern = r'\b(\d{6})\b'
        class_id_matches = re.findall(class_id_pattern, question)
        if class_id_matches:
            specific_req.specific_class_ids = class_id_matches
        
        return specific_req
    
    def get_next_question(self, preferences: CompletePreference) -> Optional[PreferenceQuestion]:
        """
        Get next question to ask based on missing preferences (5 CÂU)
        
        Returns:
            PreferenceQuestion if there are missing preferences, None if complete
        """
        missing = preferences.get_missing_preferences()
        
        if not missing:
            return None
        
        # Priority order: day > time > continuous > free_days > specific
        priority = ['day', 'time', 'continuous', 'free_days', 'specific']
        
        for key in priority:
            if key in missing or (key == 'continuous' and 'pattern' in missing) or (key == 'free_days' and 'pattern' in missing):
                return PREFERENCE_QUESTIONS.get(key)
        
        return PREFERENCE_QUESTIONS.get('specific')  # Always ask specific as last question
    
    def parse_user_response(
        self, 
        response: str, 
        question_key: str, 
        current_preferences: CompletePreference
    ) -> CompletePreference:
        """
        Parse user response to a preference question and update preferences
        
        Args:
            response: User's response text
            question_key: Key of the question being answered
            current_preferences: Current preference state
        
        Returns:
            Updated CompletePreference
        """
        response_lower = self._normalize_response_text(response)
        
        if question_key == 'day':
            # Parse day preference
            # User can say: "Thứ 2, Thứ 3, Thứ 5" or "T2, T3, T5" or "thứ 2,3,4" or "không thích thứ 7"
            # Or "Không quan trọng" / "3" (option 3)
            
            # Check for "not important" response
            if any(phrase in response_lower for phrase in ['không quan trọng', 'ko quan trọng', 'không đề cập']):
                current_preferences.day.is_not_important = True
                return current_preferences
            
            has_negation = any(neg in response_lower for neg in ['không', 'tránh', 'ko'])
            parsed_days = self._extract_days_from_response(response_lower)

            for en_day in parsed_days:
                if has_negation:
                    if en_day not in current_preferences.day.avoid_days:
                        current_preferences.day.avoid_days.append(en_day)
                else:
                    if en_day not in current_preferences.day.prefer_days:
                        current_preferences.day.prefer_days.append(en_day)
        
        elif question_key == 'time':
            # Parse time preference (CHẺ SET prefer_early_start hoặc prefer_late_start)
            if '1' in response_lower or 'sớm' in response_lower or 'học sớm' in response_lower:
                current_preferences.time.prefer_early_start = True
                current_preferences.time.prefer_late_start = False  # Clear opposite
            elif '2' in response_lower or 'muộn' in response_lower or 'học muộn' in response_lower:
                current_preferences.time.prefer_late_start = True
                current_preferences.time.prefer_early_start = False  # Clear opposite
            else:
                # Option 3: không quan trọng - set flag
                current_preferences.time.is_not_important = True
                current_preferences.time.prefer_early_start = False
                current_preferences.time.prefer_late_start = False
        
        elif question_key == 'continuous':
            # Parse continuous preference
            # CHECK OPTION 3 FIRST (before checking 'không' alone)
            if '3' in response_lower or 'không quan trọng' in response_lower or 'ko quan trọng' in response_lower:
                # Option 3: không quan trọng
                current_preferences.continuous.is_not_important = True
            elif '1' in response_lower or 'có' in response_lower or 'liên tục' in response_lower:
                current_preferences.continuous.prefer_continuous = True
            elif '2' in response_lower or ('không' in response_lower and 'quan trọng' not in response_lower) or 'khoảng nghỉ' in response_lower:
                # Option 2: không muốn học liên tục
                current_preferences.continuous.prefer_continuous = False
        
        elif question_key == 'free_days':
            # Parse free days preference
            # CHECK OPTION 3 FIRST (before checking 'không' alone)
            if '3' in response_lower or 'không quan trọng' in response_lower or 'ko quan trọng' in response_lower:
                # Option 3: không quan trọng
                current_preferences.free_days.is_not_important = True
            elif '1' in response_lower or 'có' in response_lower or 'tối đa' in response_lower or 'nghỉ' in response_lower:
                current_preferences.free_days.prefer_free_days = True
            elif '2' in response_lower or ('không' in response_lower and 'quan trọng' not in response_lower) or 'đều' in response_lower:
                # Option 2: không muốn tối đa hóa ngày nghỉ
                current_preferences.free_days.prefer_free_days = False
        
        elif question_key == 'specific':
            # Parse specific requirements
            if 'không' in response_lower and len(response_lower) < 15:
                # User said "không" - mark as answered but no requirements
                # Set a placeholder to indicate question was answered
                current_preferences.specific.specific_times = {'answered': 'no_requirements'}
            else:
                specific = self._extract_specific_requirements(response_lower)
                if specific.preferred_teachers:
                    current_preferences.specific.preferred_teachers.extend(specific.preferred_teachers)
                if specific.specific_class_ids:
                    current_preferences.specific.specific_class_ids.extend(specific.specific_class_ids)
                # If no specific found but user responded, mark as answered
                if not specific.preferred_teachers and not specific.specific_class_ids:
                    current_preferences.specific.specific_times = {'answered': 'no_requirements'}
        
        return current_preferences
    
    def format_preference_summary(self, preferences: CompletePreference) -> str:
        """
        Format preferences as readable summary
        
        Returns:
            Formatted string with all collected preferences
        """
        lines = ["📋 **Tổng hợp sở thích của bạn:**\n"]
        
        # Day preferences
        if preferences.day.prefer_days:
            days_vn = [self._en_day_to_vn(day) for day in preferences.day.prefer_days]
            lines.append(f"📅 Ngày học ưu tiên: {', '.join(days_vn)}")
        if preferences.day.avoid_days:
            days_vn = [self._en_day_to_vn(day) for day in preferences.day.avoid_days]
            lines.append(f"📅 Ngày không muốn học: {', '.join(days_vn)}")
        
        # Time preferences
        if preferences.time.time_period:
            time_vn = {
                'morning': 'Buổi sáng (6:45-11:45)',
                'afternoon': 'Buổi chiều (12:30-17:30)'
            }
            lines.append(f"⏰ Thời gian: {time_vn.get(preferences.time.time_period)}")
        if preferences.time.avoid_time_periods:
            time_vn = [{'morning': 'sáng', 'afternoon': 'chiều'}.get(p) for p in preferences.time.avoid_time_periods]
            lines.append(f"⏰ Tránh: Buổi {', '.join(time_vn)}")
        if preferences.time.prefer_early_start:
            lines.append("⏰ Ưu tiên: Học sớm")
        if preferences.time.prefer_late_start:
            lines.append("⏰ Ưu tiên: Học muộn")
        
        # Continuous preference
        if preferences.continuous.prefer_continuous:
            lines.append("📚 Ưu tiên: Học liên tục nhiều lớp trong 1 buổi")
        elif preferences.continuous.is_not_important:
            lines.append("📚 Học liên tục: Không quan trọng")
        
        # Free days preference
        if preferences.free_days.prefer_free_days:
            lines.append("🗓️ Ưu tiên: Tối đa hóa ngày nghỉ")
        elif preferences.free_days.is_not_important:
            lines.append("🗓️ Ngày nghỉ: Không quan trọng")
        
        # Specific requirements
        if preferences.specific.preferred_teachers:
            lines.append(f"👨‍🏫 Giáo viên ưu tiên: {', '.join(preferences.specific.preferred_teachers)}")
        if preferences.specific.specific_class_ids:
            lines.append(f"🎯 Mã lớp cụ thể: {', '.join(preferences.specific.specific_class_ids)}")
        
        return '\n'.join(lines)
    
    def _en_day_to_vn(self, en_day: str) -> str:
        """Convert English day to Vietnamese"""
        day_map = {
            'Monday': 'Thứ 2',
            'Tuesday': 'Thứ 3',
            'Wednesday': 'Thứ 4',
            'Thursday': 'Thứ 5',
            'Friday': 'Thứ 6',
            'Saturday': 'Thứ 7',
            'Sunday': 'Chủ nhật'
        }
        return day_map.get(en_day, en_day)
