"""
Preference Schema for Interactive Class Suggestion
"""
from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field


class TimePreference(BaseModel):
    """Time-related preferences"""
    time_period: Optional[Literal['morning', 'afternoon']] = None
    avoid_time_periods: List[Literal['morning', 'afternoon']] = Field(default_factory=list)
    prefer_early_start: bool = False  # Học sớm (start early, end early)
    prefer_late_start: bool = False   # Học muộn (start late, end late)
    avoid_early_start: bool = False   # Tránh học sớm
    avoid_late_end: bool = False      # Tránh học muộn


class DayPreference(BaseModel):
    """Day-related preferences"""
    prefer_days: List[str] = Field(default_factory=list)  # ['Monday', 'Tuesday']
    avoid_days: List[str] = Field(default_factory=list)   # ['Saturday', 'Sunday']


class SchedulePatternPreference(BaseModel):
    """Schedule pattern preferences"""
    prefer_continuous: bool = False   # Học liên tục nhiều lớp 1 buổi (>5h/day)
    prefer_free_days: bool = False    # Tối đa hóa ngày nghỉ


class SpecificRequirement(BaseModel):
    """Specific requirements"""
    preferred_teachers: List[str] = Field(default_factory=list)
    specific_class_ids: List[str] = Field(default_factory=list)
    specific_times: Optional[Dict[str, str]] = None  # {'start': '08:00', 'end': '12:00'}


class CompletePreference(BaseModel):
    """Complete preference set for class suggestion"""
    time: TimePreference = Field(default_factory=TimePreference)
    day: DayPreference = Field(default_factory=DayPreference)
    pattern: SchedulePatternPreference = Field(default_factory=SchedulePatternPreference)
    specific: SpecificRequirement = Field(default_factory=SpecificRequirement)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for ClassSuggestionRuleEngine"""
        result = {}
        
        # Time preferences
        if self.time.time_period:
            result['time_period'] = self.time.time_period
        if self.time.avoid_time_periods:
            result['avoid_time_periods'] = self.time.avoid_time_periods
        result['prefer_early_start'] = self.time.prefer_early_start
        result['prefer_late_start'] = self.time.prefer_late_start
        result['avoid_early_start'] = self.time.avoid_early_start
        result['avoid_late_end'] = self.time.avoid_late_end
        
        # Day preferences
        if self.day.prefer_days:
            result['prefer_days'] = self.day.prefer_days
        if self.day.avoid_days:
            result['avoid_days'] = self.day.avoid_days
        
        # Pattern preferences
        result['prefer_continuous'] = self.pattern.prefer_continuous
        result['prefer_free_days'] = self.pattern.prefer_free_days
        
        # Specific requirements
        if self.specific.preferred_teachers:
            result['preferred_teachers'] = self.specific.preferred_teachers
        if self.specific.specific_class_ids:
            result['specific_class_ids'] = self.specific.specific_class_ids
        if self.specific.specific_times:
            result['specific_times'] = self.specific.specific_times
        
        return result
    
    def is_complete(self) -> bool:
        """Check if all required preferences are collected (5 PREFERENCES)"""
        # Required: day, time, and at least one pattern preference
        has_day_pref = bool(self.day.prefer_days or self.day.avoid_days)
        has_time_pref = bool(
            self.time.prefer_early_start or
            self.time.prefer_late_start
        )
        has_pattern_pref = bool(
            self.pattern.prefer_continuous or
            self.pattern.prefer_free_days
        )
        
        # Consider complete if we have day + time + pattern
        # Specific requirements are optional
        return has_day_pref and has_time_pref and has_pattern_pref
    
    def get_missing_preferences(self) -> List[str]:
        """Get list of missing preference categories (5 CÂU HỎI)"""
        missing = []
        
        # Check day preference
        if not (self.day.prefer_days or self.day.avoid_days):
            missing.append('day')
        
        # Check time preference
        if not (self.time.prefer_early_start or self.time.prefer_late_start):
            missing.append('time')
        
        # Check pattern preferences
        if not (self.pattern.prefer_continuous or self.pattern.prefer_free_days):
            missing.append('pattern')

        #if not (self.specific.preferred_teachers or
        #        self.specific.specific_class_ids or
        #        self.specific.specific_times):
        #    missing.append('specific')
        
        return missing


class PreferenceQuestion(BaseModel):
    """Question to ask user for preference"""
    key: str  # 'day', 'time', 'continuous', 'free_days', 'specific'
    question: str
    options: Optional[List[str]] = None
    type: Literal['single_choice', 'multi_choice', 'free_text']
    maps_to: List[str]  # Which preference fields this question affects


# Define all preference questions 
PREFERENCE_QUESTIONS = {
    'day': PreferenceQuestion(
        key='day',
        question='📅 Bạn thích học vào những ngày nào trong tuần?\n(Chọn nhiều ngày, cách nhau bởi dấu phẩy. Ví dụ: Thứ 2, Thứ 4, Thứ 6)',
        options=['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật'],
        type='multi_choice',
        maps_to=['prefer_days', 'avoid_days']
    ),
    
    'time': PreferenceQuestion(
        key='time',
        question='⏰ Bạn muốn học sớm hay học muộn?\n1. Học sớm (ưu tiên lớp bắt đầu sớm)\n2. Học muộn (ưu tiên lớp kết thúc muộn)\n3. Không quan trọng',
        options=['Học sớm', 'Học muộn', 'Không quan trọng'],
        type='single_choice',
        maps_to=['prefer_early_start', 'prefer_late_start']
    ),
    
    'continuous': PreferenceQuestion(
        key='continuous',
        question='📚 Bạn thích học liên tục nhiều lớp trong 1 buổi không?\n(Ví dụ: 3 lớp liên tiếp trong buổi sáng)\n1. Có, tôi muốn học liên tục\n2. Không, tôi muốn có khoảng nghỉ\n3. Không quan trọng',
        options=['Có, tôi muốn học liên tục', 'Không, tôi muốn có khoảng nghỉ', 'Không quan trọng'],
        type='single_choice',
        maps_to=['prefer_continuous']
    ),
    
    'free_days': PreferenceQuestion(
        key='free_days',
        question='🗓️ Bạn thích học ít ngày nhất có thể không?\n(Ví dụ: chỉ học 3 ngày/tuần thay vì 5 ngày)\n1. Có, tôi muốn tối đa hóa ngày nghỉ\n2. Không, tôi muốn học đều các ngày\n3. Không quan trọng',
        options=['Có, tôi muốn tối đa hóa ngày nghỉ', 'Không, tôi muốn học đều các ngày', 'Không quan trọng'],
        type='single_choice',
        maps_to=['prefer_free_days']
    ),
    
    'specific': PreferenceQuestion(
        key='specific',
        question='🎯 Bạn còn yêu cầu nào cụ thể không?\n(Ví dụ: giáo viên yêu thích, mã lớp cụ thể, hoặc trả lời "không")',
        type='free_text',
        maps_to=['preferred_teachers', 'specific_class_ids', 'specific_times']
    )
}
