"""
Preference Collection Service
Handles multi-turn conversation for collecting user preferences
"""
from typing import Dict, List, Optional, Set, Tuple
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

    def _is_not_important(self, text: str) -> bool:
        return any(
            phrase in text
            for phrase in [
                'không quan trọng',
                'ko quan trọng',
                'khong quan trong',
                'không ưu tiên',
                'khong uu tien',
            ]
        )

    def _is_negative_choice(self, text: str) -> bool:
        return any(
            marker in text
            for marker in ['không', 'ko', 'khong', 'khỏi', 'khong can']
        )

    def _is_no_specific_requirement(self, text: str) -> bool:
        return any(
            phrase in text
            for phrase in [
                'không có yêu cầu',
                'khong co yeu cau',
                'không yêu cầu gì',
                'khong yeu cau gi',
                'không cần yêu cầu',
                'khong can yeu cau',
                'không cần gì thêm',
                'khong can gi them',
            ]
        )

    def _merge_unique_list(self, target: List[str], source: List[str]) -> bool:
        changed = False
        for item in source:
            if item not in target:
                target.append(item)
                changed = True
        return changed

    def _mark_derived_answers(self, preferences: CompletePreference):
        if preferences.day.prefer_days or preferences.day.avoid_days or preferences.day.is_not_important:
            preferences.day.has_answer = True

        if (
            preferences.time.time_period
            or preferences.time.avoid_time_periods
            or preferences.time.prefer_early_start
            or preferences.time.prefer_late_start
            or preferences.time.avoid_early_start
            or preferences.time.avoid_late_end
            or preferences.time.is_not_important
        ):
            preferences.time.has_answer = True

        if preferences.continuous.prefer_continuous or preferences.continuous.is_not_important:
            preferences.continuous.has_answer = True

        if preferences.free_days.prefer_free_days or preferences.free_days.is_not_important:
            preferences.free_days.has_answer = True

        if (
            preferences.specific.preferred_teachers
            or preferences.specific.specific_class_ids
            or preferences.specific.specific_subjects
            or preferences.specific.specific_times
            or preferences.specific.has_answer
        ):
            preferences.specific.has_answer = True

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
        question_lower = self._normalize_response_text(question)
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

        if self._is_no_specific_requirement(question_lower):
            preferences.specific.has_answer = True

        self._mark_derived_answers(preferences)
        
        return preferences

    def merge_supplemental_preferences(
        self,
        response: str,
        current_preferences: CompletePreference,
        skip_keys: Optional[Set[str]] = None,
    ) -> Tuple[CompletePreference, List[str]]:
        """
        Parse free-text response for supplemental preferences and merge without
        overriding already-collected values.
        """
        skip_keys = skip_keys or set()
        extracted = self.extract_initial_preferences(response)
        captured_keys: List[str] = []

        if 'day' not in skip_keys:
            changed = False
            changed = self._merge_unique_list(current_preferences.day.prefer_days, extracted.day.prefer_days) or changed
            changed = self._merge_unique_list(current_preferences.day.avoid_days, extracted.day.avoid_days) or changed
            if extracted.day.is_not_important and not current_preferences.day.is_not_important:
                current_preferences.day.is_not_important = True
                changed = True
            if changed:
                current_preferences.day.has_answer = True
                captured_keys.append('day')

        if 'time' not in skip_keys:
            changed = False
            if extracted.time.time_period and not current_preferences.time.time_period:
                current_preferences.time.time_period = extracted.time.time_period
                changed = True
            changed = self._merge_unique_list(current_preferences.time.avoid_time_periods, extracted.time.avoid_time_periods) or changed
            if extracted.time.prefer_early_start and not current_preferences.time.prefer_early_start:
                current_preferences.time.prefer_early_start = True
                changed = True
            if extracted.time.prefer_late_start and not current_preferences.time.prefer_late_start:
                current_preferences.time.prefer_late_start = True
                changed = True
            if extracted.time.avoid_early_start and not current_preferences.time.avoid_early_start:
                current_preferences.time.avoid_early_start = True
                changed = True
            if extracted.time.avoid_late_end and not current_preferences.time.avoid_late_end:
                current_preferences.time.avoid_late_end = True
                changed = True
            if extracted.time.is_not_important and not current_preferences.time.is_not_important:
                current_preferences.time.is_not_important = True
                changed = True
            if changed:
                current_preferences.time.has_answer = True
                captured_keys.append('time')

        if 'continuous' not in skip_keys:
            changed = False
            if extracted.continuous.has_answer and not current_preferences.continuous.has_answer:
                current_preferences.continuous.has_answer = True
                changed = True
            if extracted.continuous.prefer_continuous != current_preferences.continuous.prefer_continuous and extracted.continuous.has_answer:
                current_preferences.continuous.prefer_continuous = extracted.continuous.prefer_continuous
                changed = True
            if extracted.continuous.is_not_important and not current_preferences.continuous.is_not_important:
                current_preferences.continuous.is_not_important = True
                changed = True
            if changed:
                captured_keys.append('continuous')

        if 'free_days' not in skip_keys:
            changed = False
            if extracted.free_days.has_answer and not current_preferences.free_days.has_answer:
                current_preferences.free_days.has_answer = True
                changed = True
            if extracted.free_days.prefer_free_days != current_preferences.free_days.prefer_free_days and extracted.free_days.has_answer:
                current_preferences.free_days.prefer_free_days = extracted.free_days.prefer_free_days
                changed = True
            if extracted.free_days.is_not_important and not current_preferences.free_days.is_not_important:
                current_preferences.free_days.is_not_important = True
                changed = True
            if changed:
                captured_keys.append('free_days')

        if 'specific' not in skip_keys:
            changed = False
            changed = self._merge_unique_list(current_preferences.specific.preferred_teachers, extracted.specific.preferred_teachers) or changed
            changed = self._merge_unique_list(current_preferences.specific.specific_class_ids, extracted.specific.specific_class_ids) or changed
            changed = self._merge_unique_list(current_preferences.specific.specific_subjects, extracted.specific.specific_subjects) or changed
            if not current_preferences.specific.specific_times and extracted.specific.specific_times:
                current_preferences.specific.specific_times = extracted.specific.specific_times
                changed = True
            if extracted.specific.has_answer and not current_preferences.specific.has_answer:
                current_preferences.specific.has_answer = True
                changed = True
            if changed:
                current_preferences.specific.has_answer = True
                captured_keys.append('specific')

        self._mark_derived_answers(current_preferences)
        return current_preferences, captured_keys
    
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
                time_pref.has_answer = True
                break
        
        # Check early/late preferences
        if 'học sớm' in question or 'sớm' in question:
            if has_negation_before(question, 'sớm'):
                time_pref.avoid_early_start = True
            else:
                time_pref.prefer_early_start = True
            time_pref.has_answer = True
        
        if 'học muộn' in question or 'muộn' in question or 'đến muộn' in question:
            if has_negation_before(question, 'muộn'):
                time_pref.avoid_late_end = True
            else:
                time_pref.prefer_late_start = True
            time_pref.has_answer = True
        
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
                        day_pref.has_answer = True
                else:
                    # Check context for prefer
                    if any(keyword in question for keyword in ['muốn học', 'thích học', 'học vào']):
                        if en_day not in day_pref.prefer_days:
                            day_pref.prefer_days.append(en_day)
                            day_pref.has_answer = True
        
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
            continuous_pref.has_answer = True
        
        # Free days
        if any(keyword in question for keyword in ['nghỉ nhiều', 'ít ngày', 'học ít ngày', 'tối đa hóa ngày nghỉ']):
            free_days_pref.prefer_free_days = True
            free_days_pref.has_answer = True
        
        return continuous_pref, free_days_pref
    
    def _extract_specific_requirements(self, question: str) -> SpecificRequirement:
        """Extract specific requirements"""
        specific_req = SpecificRequirement()

        def _normalize_teacher_name(raw_name: str) -> str:
            cleaned = re.sub(r'\s+', ' ', (raw_name or '').strip())
            return cleaned.title()

        def _parse_time_token(token: str) -> Optional[str]:
            normalized = (token or '').strip().lower().replace(' giờ', 'h').replace(' giờ ', 'h')
            match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(h|:)?', normalized)
            if not match:
                return None

            hour = int(match.group(1))
            minute = int(match.group(2) or 0)
            if hour > 23 or minute > 59:
                return None
            return f"{hour:02d}:{minute:02d}"

        def _add_time_range(start_raw: str, end_raw: str) -> None:
            start_time = _parse_time_token(start_raw)
            end_time = _parse_time_token(end_raw)
            if start_time and end_time:
                specific_req.specific_times = {'start': start_time, 'end': end_time}
                specific_req.has_answer = True
        
        # Extract teacher names with a more permissive pattern.
        teacher_pattern = r'(?:giáo viên|thầy|cô|gv|giảng viên)\s+([^\n,.;]+?)(?=(?:,|;|\bvà\b|\blớp\b|\bclass\b|\bmã lớp\b|\btừ\b|\bvào\b|$))'
        teacher_matches = [
            _normalize_teacher_name(match)
            for match in re.findall(teacher_pattern, question)
        ]
        if teacher_matches:
            specific_req.preferred_teachers = list(dict.fromkeys(teacher_matches))
            specific_req.has_answer = True
        
        # Extract class IDs and common class-code variants.
        class_id_patterns = [
            r'\b(?:lớp|lop|class)\s*[-:]?\s*([A-Z]{1,4}\d{2,6}|\d{3,8})\b',
            r'\b(\d{6})\b',
        ]
        class_id_matches: List[str] = []
        for pattern in class_id_patterns:
            for match in re.findall(pattern, question, flags=re.IGNORECASE):
                candidate = str(match).strip().upper()
                if candidate and candidate not in class_id_matches:
                    class_id_matches.append(candidate)
        if class_id_matches:
            specific_req.specific_class_ids = class_id_matches
            specific_req.has_answer = True

        # Extract specific subject requests from subject code or subject name hints.
        subject_matches: List[str] = []
        subject_code_patterns = [
            r'\b(?:môn|mon|học\s*phần|hoc\s*phan|subject)\s*[-:]?\s*([A-Z]{2,4}\d{3,4})\b',
            r'\b([A-Z]{2,4}\d{3,4})\b',
        ]
        for pattern in subject_code_patterns:
            for match in re.findall(pattern, question, flags=re.IGNORECASE):
                candidate = str(match).strip().upper()
                if candidate and candidate not in subject_matches:
                    subject_matches.append(candidate)

        subject_name_pattern = r'\b(?:môn|mon|học\s*phần|hoc\s*phan)\s*[-:]?\s*([^\n,.;]+?)(?=(?:,|;|\bvà\b|\blớp\b|\bclass\b|\btừ\b|\bvào\b|$))'
        for match in re.findall(subject_name_pattern, question, flags=re.IGNORECASE):
            candidate = re.sub(r'\s+', ' ', match.strip())
            if not candidate:
                continue
            if re.fullmatch(r'[A-Z]{2,4}\d{3,4}', candidate, flags=re.IGNORECASE):
                candidate = candidate.upper()
            if candidate and candidate not in subject_matches:
                subject_matches.append(candidate)

        if subject_matches:
            specific_req.specific_subjects = subject_matches
            specific_req.has_answer = True

        # Extract explicit time ranges for specific requirements.
        time_range_patterns = [
            r'(?:từ|tu)\s*(\d{1,2}(?::\d{2})?\s*(?:h|:)?(?:\d{2})?)\s*(?:đến|toi|toi)?\s*(\d{1,2}(?::\d{2})?\s*(?:h|:)?(?:\d{2})?)',
            r'(\d{1,2}(?::\d{2})?\s*(?:h|:)?(?:\d{2})?)\s*(?:-|–|—)\s*(\d{1,2}(?::\d{2})?\s*(?:h|:)?(?:\d{2})?)',
        ]
        for pattern in time_range_patterns:
            time_match = re.search(pattern, question, flags=re.IGNORECASE)
            if time_match:
                _add_time_range(time_match.group(1), time_match.group(2))
                break

        if not specific_req.specific_times:
            single_time_match = re.search(r'(?:vào|từ|sau)\s*(\d{1,2}(?::\d{2})?\s*(?:h|:)?(?:\d{2})?)', question, flags=re.IGNORECASE)
            if single_time_match:
                start_time = _parse_time_token(single_time_match.group(1))
                if start_time:
                    specific_req.specific_times = {'start': start_time, 'end': start_time}
                    specific_req.has_answer = True
        
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
        is_not_important = self._is_not_important(response_lower)
        
        if question_key == 'day':
            # Parse day preference
            # User can say: "Thứ 2, Thứ 3, Thứ 5" or "T2, T3, T5" or "thứ 2,3,4" or "không thích thứ 7"
            # Or "Không quan trọng" / "3" (option 3)
            
            # Check for "not important" response
            if is_not_important or any(phrase in response_lower for phrase in ['không đề cập', 'khong de cap']):
                current_preferences.day.is_not_important = True
                current_preferences.day.has_answer = True
                return current_preferences
            
            has_negation = self._is_negative_choice(response_lower) or ('tránh' in response_lower)
            parsed_days = self._extract_days_from_response(response_lower)

            for en_day in parsed_days:
                if has_negation:
                    if en_day not in current_preferences.day.avoid_days:
                        current_preferences.day.avoid_days.append(en_day)
                else:
                    if en_day not in current_preferences.day.prefer_days:
                        current_preferences.day.prefer_days.append(en_day)

            if parsed_days:
                current_preferences.day.has_answer = True
        
        elif question_key == 'time':
            # Parse time preference (CHẺ SET prefer_early_start hoặc prefer_late_start)
            if '1' in response_lower or 'sớm' in response_lower or 'học sớm' in response_lower:
                current_preferences.time.prefer_early_start = True
                current_preferences.time.prefer_late_start = False  # Clear opposite
                current_preferences.time.has_answer = True
            elif '2' in response_lower or 'muộn' in response_lower or 'học muộn' in response_lower:
                current_preferences.time.prefer_late_start = True
                current_preferences.time.prefer_early_start = False  # Clear opposite
                current_preferences.time.has_answer = True
            elif is_not_important:
                current_preferences.time.is_not_important = True
                current_preferences.time.prefer_early_start = False
                current_preferences.time.prefer_late_start = False
                current_preferences.time.has_answer = True
            else:
                # Option 3: không quan trọng - set flag
                current_preferences.time.is_not_important = True
                current_preferences.time.prefer_early_start = False
                current_preferences.time.prefer_late_start = False
                current_preferences.time.has_answer = True
        
        elif question_key == 'continuous':
            # Parse continuous preference
            # CHECK OPTION 3 FIRST (before checking 'không' alone)
            if '3' in response_lower or is_not_important:
                # Option 3: không quan trọng
                current_preferences.continuous.is_not_important = True
                current_preferences.continuous.has_answer = True
            elif '1' in response_lower or 'có' in response_lower or 'liên tục' in response_lower:
                current_preferences.continuous.prefer_continuous = True
                current_preferences.continuous.is_not_important = False
                current_preferences.continuous.has_answer = True
            elif '2' in response_lower or (self._is_negative_choice(response_lower) and 'quan trọng' not in response_lower and 'quan trong' not in response_lower) or 'khoảng nghỉ' in response_lower:
                # Option 2: không muốn học liên tục
                current_preferences.continuous.prefer_continuous = False
                current_preferences.continuous.is_not_important = False
                current_preferences.continuous.has_answer = True
        
        elif question_key == 'free_days':
            # Parse free days preference
            # CHECK OPTION 3 FIRST (before checking 'không' alone)
            if '3' in response_lower or is_not_important:
                # Option 3: không quan trọng
                current_preferences.free_days.is_not_important = True
                current_preferences.free_days.has_answer = True
            elif '1' in response_lower or 'có' in response_lower or 'tối đa' in response_lower or 'nghỉ' in response_lower:
                current_preferences.free_days.prefer_free_days = True
                current_preferences.free_days.is_not_important = False
                current_preferences.free_days.has_answer = True
            elif '2' in response_lower or (self._is_negative_choice(response_lower) and 'quan trọng' not in response_lower and 'quan trong' not in response_lower) or 'đều' in response_lower:
                # Option 2: không muốn tối đa hóa ngày nghỉ
                current_preferences.free_days.prefer_free_days = False
                current_preferences.free_days.is_not_important = False
                current_preferences.free_days.has_answer = True
        
        elif question_key == 'specific':
            # Parse specific requirements
            if self._is_no_specific_requirement(response_lower):
                current_preferences.specific.has_answer = True
            else:
                specific = self._extract_specific_requirements(response_lower)
                if specific.preferred_teachers:
                    current_preferences.specific.preferred_teachers.extend(specific.preferred_teachers)
                if specific.specific_class_ids:
                    current_preferences.specific.specific_class_ids.extend(specific.specific_class_ids)
                if specific.specific_subjects:
                    current_preferences.specific.specific_subjects.extend(specific.specific_subjects)
                if specific.specific_times:
                    current_preferences.specific.specific_times = specific.specific_times
                # Only mark as answered when we actually extracted a specific requirement.
                if (
                    specific.preferred_teachers
                    or specific.specific_class_ids
                    or specific.specific_subjects
                    or specific.specific_times
                ):
                    current_preferences.specific.has_answer = True

        self._mark_derived_answers(current_preferences)
        
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
        if preferences.specific.specific_subjects:
            lines.append(f"📘 Học phần cụ thể: {', '.join(preferences.specific.specific_subjects)}")
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
