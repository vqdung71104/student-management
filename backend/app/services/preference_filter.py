"""
Preference-based Class Filter
Filter classes based on user preferences BEFORE generating combinations
This implements early pruning optimization to reduce combination space
"""
from typing import List, Dict, Optional
from datetime import time


class PreferenceFilter:
    """Filter classes based on user preferences for optimization"""
    
    def __init__(self):
        self.time_periods = {
            'morning': (time(6, 45), time(11, 45)),
            'afternoon': (time(12, 30), time(17, 30))
        }
    
    def filter_by_preferences(
        self,
        classes: List[Dict],
        preferences: Dict,
        strict: bool = False
    ) -> List[Dict]:
        """
        Filter classes based on preferences
        
        Args:
            classes: List of classes to filter
            preferences: User preferences dict
            strict: If True, only return classes matching ALL preferences
                   If False, return classes matching ANY preference (softer filter)
        
        Returns:
            Filtered list of classes
        """
        if not classes:
            return []
        
        filtered = classes.copy()
        
        print(f"🔍 [FILTER] Starting with {len(filtered)} classes")
        
        # Filter 1: Time period
        if preferences.get('time_period'):
            filtered = self._filter_by_time_period(filtered, preferences['time_period'])
            print(f"  ⏰ After time_period filter: {len(filtered)} classes")
        
        # Filter 2: Avoid time periods
        if preferences.get('avoid_time_periods'):
            filtered = self._filter_avoid_time_periods(filtered, preferences['avoid_time_periods'])
            print(f"  🚫 After avoid_time_periods filter: {len(filtered)} classes")
        
        # Filter 3: Preferred days
        if preferences.get('prefer_days') and strict:
            filtered = self._filter_by_preferred_days(filtered, preferences['prefer_days'])
            print(f"  📅 After prefer_days filter: {len(filtered)} classes")
        
        # Filter 4: Avoid days
        if preferences.get('avoid_days'):
            filtered = self._filter_avoid_days(filtered, preferences['avoid_days'])
            print(f"  ❌ After avoid_days filter: {len(filtered)} classes")
        
        # Filter 5: Early start time (soft filter - sort by start time)
        if preferences.get('prefer_early_start'):
            filtered = self._sort_by_early_start(filtered)
            print(f"  🌅 After prefer_early_start sort: {len(filtered)} classes")
        
        # Filter 6: Late end time (soft filter - sort by end time)
        if preferences.get('prefer_late_start'):
            filtered = self._sort_by_late_end(filtered)
            print(f"  🌙 After prefer_late_start sort: {len(filtered)} classes")
        
        # Filter 7: Preferred teachers
        if preferences.get('preferred_teachers'):
            # Soft filter - boost matching but don't exclude
            filtered = self._boost_preferred_teachers(filtered, preferences['preferred_teachers'])
            print(f"  👨‍🏫 After preferred_teachers boost: {len(filtered)} classes")
        
        # Filter 8: Specific class IDs
        if preferences.get('specific_class_ids'):
            # Hard filter - only these classes
            filtered = self._filter_specific_classes(filtered, preferences['specific_class_ids'])
            print(f"  🎯 After specific_class_ids filter: {len(filtered)} classes")
        
        # Filter 9: Specific times
        if preferences.get('specific_times'):
            filtered = self._filter_by_specific_times(filtered, preferences['specific_times'])
            print(f"  🕐 After specific_times filter: {len(filtered)} classes")
        
        print(f"✅ [FILTER] Final result: {len(filtered)} classes (from {len(classes)})")
        
        # ALWAYS return something (never empty list)
        if not filtered:
            print(f"  ⚠️ Filter removed all classes, returning original (with violations)")
            return classes
        
        return filtered
    
    def _filter_by_time_period(self, classes: List[Dict], time_period: str) -> List[Dict]:
        """Filter classes by time period (morning/afternoon)"""
        if time_period not in self.time_periods:
            return classes
        
        period_start, period_end = self.time_periods[time_period]
        
        filtered = []
        for cls in classes:
            class_start = self._parse_time(cls.get('study_time_start'))
            if class_start and period_start <= class_start < period_end:
                filtered.append(cls)
        
        return filtered if filtered else classes  # Return original if no match
    
    def _filter_avoid_time_periods(self, classes: List[Dict], avoid_periods: List[str]) -> List[Dict]:
        """Filter out classes in avoided time periods"""
        filtered = []
        
        for cls in classes:
            class_start = self._parse_time(cls.get('study_time_start'))
            if not class_start:
                filtered.append(cls)
                continue
            
            # Check if class is in any avoided period
            in_avoided_period = False
            for period in avoid_periods:
                if period in self.time_periods:
                    period_start, period_end = self.time_periods[period]
                    if period_start <= class_start < period_end:
                        in_avoided_period = True
                        break
            
            if not in_avoided_period:
                filtered.append(cls)
        
        return filtered if filtered else classes
    
    def _filter_by_preferred_days(self, classes: List[Dict], prefer_days: List[str]) -> List[Dict]:
        """Filter classes that match preferred days"""
        filtered = []
        
        for cls in classes:
            study_date = cls.get('study_date', '')
            class_days = self._parse_study_days(study_date)
            
            # Check if any class day is in preferred days
            if any(day in prefer_days for day in class_days):
                filtered.append(cls)
        
        return filtered if filtered else classes
    
    def _filter_avoid_days(self, classes: List[Dict], avoid_days: List[str]) -> List[Dict]:
        """Filter out classes on avoided days"""
        filtered = []
        
        for cls in classes:
            study_date = cls.get('study_date', '')
            class_days = self._parse_study_days(study_date)
            
            # Check if any class day is in avoided days
            if not any(day in avoid_days for day in class_days):
                filtered.append(cls)
        
        return filtered if filtered else classes
    
    def _sort_by_early_start(self, classes: List[Dict]) -> List[Dict]:
        """Sort classes by start time (earlier first)"""
        return sorted(
            classes,
            key=lambda cls: self._parse_time(cls.get('study_time_start')) or time(23, 59)
        )
    
    def _sort_by_late_end(self, classes: List[Dict]) -> List[Dict]:
        """Sort classes by end time (later first)"""
        return sorted(
            classes,
            key=lambda cls: self._parse_time(cls.get('study_time_end')) or time(0, 0),
            reverse=True
        )
    
    def _boost_preferred_teachers(self, classes: List[Dict], preferred_teachers: List[str]) -> List[Dict]:
        """
        Boost classes with preferred teachers (soft filter)
        Put preferred teachers first, but keep others
        """
        preferred = []
        others = []
        
        for cls in classes:
            teacher_name = cls.get('teacher_name', '').lower()
            
            # Check if teacher is in preferred list
            is_preferred = any(
                pref.lower() in teacher_name or teacher_name in pref.lower()
                for pref in preferred_teachers
            )
            
            if is_preferred:
                preferred.append(cls)
            else:
                others.append(cls)
        
        # Return preferred first, then others
        return preferred + others
    
    def _filter_specific_classes(self, classes: List[Dict], specific_class_ids: List[str]) -> List[Dict]:
        """Filter to only specific class IDs (hard filter)"""
        filtered = []
        
        for cls in classes:
            class_id = str(cls.get('class_id', ''))
            if class_id in specific_class_ids:
                filtered.append(cls)
        
        return filtered
    
    def _filter_by_specific_times(self, classes: List[Dict], specific_times: Dict) -> List[Dict]:
        """Filter classes within specific time range"""
        if not specific_times or 'start' not in specific_times or 'end' not in specific_times:
            return classes
        
        try:
            desired_start = self._parse_time_string(specific_times['start'])
            desired_end = self._parse_time_string(specific_times['end'])
        except:
            return classes
        
        filtered = []
        
        for cls in classes:
            class_start = self._parse_time(cls.get('study_time_start'))
            class_end = self._parse_time(cls.get('study_time_end'))
            
            if class_start and class_end:
                # Class must be within desired time range
                if desired_start <= class_start and class_end <= desired_end:
                    filtered.append(cls)
        
        return filtered if filtered else classes
    
    def _parse_study_days(self, study_date: str) -> List[str]:
        """Parse study_date string to list of days"""
        if not study_date:
            return []
        
        # Handle comma-separated days
        days = [day.strip() for day in study_date.split(',')]
        return days
    
    def _parse_time(self, time_value) -> Optional[time]:
        """Parse time from various formats"""
        if isinstance(time_value, time):
            return time_value
        
        if isinstance(time_value, str):
            return self._parse_time_string(time_value)
        
        return None
    
    def _parse_time_string(self, time_str: str) -> Optional[time]:
        """Parse time string (HH:MM)"""
        try:
            parts = time_str.split(':')
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            return time(hour, minute)
        except:
            return None
    
    def get_filter_stats(self, original_count: int, filtered_count: int) -> Dict:
        """Get statistics about filtering"""
        reduction = original_count - filtered_count
        reduction_pct = (reduction / original_count * 100) if original_count > 0 else 0
        
        return {
            'original_count': original_count,
            'filtered_count': filtered_count,
            'reduction': reduction,
            'reduction_percentage': round(reduction_pct, 1),
            'efficiency_gain': f"{reduction_pct:.1f}% fewer combinations to check"
        }
