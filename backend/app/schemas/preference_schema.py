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
    is_not_important: bool = False    # User said "Không quan trọng"


class DayPreference(BaseModel):
    """Day-related preferences"""
    prefer_days: List[str] = Field(default_factory=list)  # ['Monday', 'Tuesday']
    avoid_days: List[str] = Field(default_factory=list)   # ['Saturday', 'Sunday']
    is_not_important: bool = False    # User said "Không quan trọng"


class ContinuousPreference(BaseModel):
    """Continuous study preference"""
    prefer_continuous: bool = False   # Học liên tục nhiều lớp 1 buổi (>5h/day)
    is_not_important: bool = False    # User said "Không quan trọng"


class FreeDaysPreference(BaseModel):
    """Free days preference"""
    prefer_free_days: bool = False    # Tối đa hóa ngày nghỉ
    is_not_important: bool = False    # User said "Không quan trọng"


class SpecificRequirement(BaseModel):
    """Specific requirements"""
    preferred_teachers: List[str] = Field(default_factory=list)
    specific_class_ids: List[str] = Field(default_factory=list)
    specific_times: Optional[Dict[str, str]] = None  # {'start': '08:00', 'end': '12:00'}


class CompletePreference(BaseModel):
    """Complete preference set for class suggestion (5 CRITERIA)"""
    time: TimePreference = Field(default_factory=TimePreference)
    day: DayPreference = Field(default_factory=DayPreference)
    continuous: ContinuousPreference = Field(default_factory=ContinuousPreference)
    free_days: FreeDaysPreference = Field(default_factory=FreeDaysPreference)
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
        result['time_is_not_important'] = self.time.is_not_important
        
        # Day preferences
        if self.day.prefer_days:
            result['prefer_days'] = self.day.prefer_days
        if self.day.avoid_days:
            result['avoid_days'] = self.day.avoid_days
        result['day_is_not_important'] = self.day.is_not_important
        
        # Continuous preference
        result['prefer_continuous'] = self.continuous.prefer_continuous
        result['continuous_is_not_important'] = self.continuous.is_not_important
        
        # Free days preference
        result['prefer_free_days'] = self.free_days.prefer_free_days
        result['free_days_is_not_important'] = self.free_days.is_not_important
        
        # Specific requirements
        if self.specific.preferred_teachers:
            result['preferred_teachers'] = self.specific.preferred_teachers
        if self.specific.specific_class_ids:
            result['specific_class_ids'] = self.specific.specific_class_ids
        if self.specific.specific_times:
            result['specific_times'] = self.specific.specific_times
        
        return result
    
    def is_complete(self) -> bool:
        """Check if all required preferences are collected (5 CRITERIA)
        
        Each preference can be in 4 states:
        - active: Has preference set (prefer_days, prefer_early_start, etc)
        - passive: Has avoidance set (avoid_days, etc)
        - not_important: User said "Không quan trọng"
        - none: Not answered yet
        
        Complete = all 5 categories have moved from 'none' state
        """
        # 1. Check day preference: has answer OR marked not important
        has_day_pref = bool(
            self.day.prefer_days or 
            self.day.avoid_days or 
            self.day.is_not_important
        )
        
        # 2. Check time preference: has answer OR marked not important
        has_time_pref = bool(
            self.time.prefer_early_start or
            self.time.prefer_late_start or
            self.time.is_not_important
        )
        
        # 3. Check continuous preference: has answer OR marked not important
        has_continuous_pref = bool(
            self.continuous.prefer_continuous or
            self.continuous.is_not_important
        )
        
        # 4. Check free_days preference: has answer OR marked not important
        has_free_days_pref = bool(
            self.free_days.prefer_free_days or
            self.free_days.is_not_important
        )
        
        # 5. Check specific requirements: at least answered (even if "không")
        has_specific_answered = bool(
            self.specific.preferred_teachers or
            self.specific.specific_class_ids or
            self.specific.specific_times
        )
        
        # Consider complete if we have all 5 criteria answered
        # Note: specific is now REQUIRED (must ask question 5)
        return has_day_pref and has_time_pref and has_continuous_pref and has_free_days_pref and has_specific_answered
    
    def get_missing_preferences(self) -> List[str]:
        """Get list of missing preference categories (only 'none' state)
        
        Returns categories that are not:
        - set (active/passive)
        - marked as not_important
        """
        missing = []
        
        # 1. Check day preference: missing if no answer AND not marked as not important
        if not (self.day.prefer_days or self.day.avoid_days or self.day.is_not_important):
            missing.append('day')
        
        # 2. Check time preference: missing if no answer AND not marked as not important
        if not (self.time.prefer_early_start or self.time.prefer_late_start or self.time.is_not_important):
            missing.append('time')
        
        # 3. Check continuous preference: missing if no answer AND not marked as not important
        if not (self.continuous.prefer_continuous or self.continuous.is_not_important):
            missing.append('continuous')
        
        # 4. Check free_days preference: missing if no answer AND not marked as not important
        if not (self.free_days.prefer_free_days or self.free_days.is_not_important):
            missing.append('free_days')
        
        # 5. Check specific requirements: missing if not answered at all
        if not (self.specific.preferred_teachers or
                self.specific.specific_class_ids or
                self.specific.specific_times):
            missing.append('specific')
        
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
