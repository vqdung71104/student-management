"""
Schedule Combination Generator
Generate optimal schedule combinations from multiple subjects
"""
from typing import List, Dict, Tuple, Optional
from datetime import time, datetime
import itertools
from app.rules.class_suggestion_rules import ClassSuggestionRuleEngine


class ScheduleCombinationGenerator:
    """Generate and rank schedule combinations"""
    
    def __init__(self):
        self.rule_engine = ClassSuggestionRuleEngine
    
    def generate_combinations(
        self,
        classes_by_subject: Dict[str, List[Dict]],
        preferences: Dict,
        max_combinations: int = 100
    ) -> List[Dict]:
        """
        Generate valid schedule combinations from classes of different subjects
        
        Args:
            classes_by_subject: {subject_id: [class1, class2, ...]}
            preferences: User preferences
            max_combinations: Maximum combinations to generate
        
        Returns:
            List of combinations with scores and metrics
        """
        print(f"🔄 [COMBINATIONS] Generating combinations from {len(classes_by_subject)} subjects")
        
        # Step 0: Extract specific required class IDs (HARD FILTER - HIGHEST PRIORITY)
        specific_class_ids = preferences.get('specific_class_ids', [])
        if specific_class_ids:
            print(f"  🎯 [SPECIFIC] Required class IDs: {specific_class_ids}")
        
        # Step 1: Get candidate classes per subject
        subject_classes = []
        subject_ids = []
        
        for subject_id, classes in classes_by_subject.items():
            if classes:
                # If specific class IDs are required, ensure at least one is in this subject
                if specific_class_ids:
                    # Check if any required class belongs to this subject
                    required_classes = [cls for cls in classes if cls['class_id'] in specific_class_ids]
                    if required_classes:
                        # ONLY use required classes for this subject
                        subject_classes.append(required_classes)
                        subject_ids.append(subject_id)
                        print(f"  🎯 {subject_id}: Using {len(required_classes)} REQUIRED classes (out of {len(classes)})")
                    else:
                        # Use all classes for subjects without specific requirements
                        subject_classes.append(classes)
                        subject_ids.append(subject_id)
                        print(f"  📚 {subject_id}: {len(classes)} classes")
                else:
                    subject_classes.append(classes)
                    subject_ids.append(subject_id)
                    print(f"  📚 {subject_id}: {len(classes)} classes")
        
        if not subject_classes:
            return []
        
        # Step 2: Generate and filter combinations efficiently
        print(f"🔢 [COMBINATIONS] Generating combinations with conflict checking...")
        valid_combinations = []
        conflict_combinations = []
        
        # Use itertools.product generator (lazy evaluation)
        all_combinations = itertools.product(*subject_classes)
        
        checked_count = 0
        max_to_check = max_combinations * 10  # Check up to 10x more to find valid ones
        
        for combo in all_combinations:
            checked_count += 1
            
            combo_list = list(combo)
            
            # HARD FILTER: If specific class IDs required, verify ALL are present
            if specific_class_ids:
                combo_class_ids = [cls['class_id'] for cls in combo_list]
                if not all(req_id in combo_class_ids for req_id in specific_class_ids):
                    # Skip this combination - missing required class
                    continue
            
            # Check time conflicts
            if not self.has_time_conflicts(combo_list):
                valid_combinations.append(combo_list)
                # Stop if we have enough valid combinations
                if len(valid_combinations) >= max_combinations:
                    break
            else:
                # Keep first 10 conflicted combinations as backup
                if len(conflict_combinations) < 10:
                    conflict_combinations.append(combo_list)
            
            # Safety limit to avoid infinite loop
            if checked_count >= max_to_check:
                print(f"  ⚠️ Checked {checked_count} combinations, stopping search")
                break
        
        print(f"  ✅ Checked {checked_count} combinations")
        print(f"  ✅ Valid combinations (no conflicts): {len(valid_combinations)}")
        
        # If no valid combinations found
        if not valid_combinations:
            if specific_class_ids:
                print(f"  ❌ No valid combinations with required classes {specific_class_ids}")
                print(f"  💡 Suggestion: Required classes may have time conflicts with other subjects")
            else:
                print(f"  ⚠️ No valid combinations found, returning combinations with conflicts marked")
            valid_combinations = conflict_combinations[:10]
        
        # Step 4: Score and rank
        print(f"⭐ [COMBINATIONS] Scoring combinations...")
        scored_combinations = []
        
        for combo in valid_combinations:
            score = self.calculate_combination_score(combo, preferences)
            metrics = self.calculate_schedule_metrics(combo)
            
            # Check if this combination has conflicts
            has_conflicts = self.has_time_conflicts(combo)
            metrics['time_conflicts'] = has_conflicts
            
            scored_combinations.append({
                'classes': combo,
                'score': score,
                'metrics': metrics,
                'subject_ids': [cls['subject_id'] for cls in combo],
                'has_violations': has_conflicts  # Flag for frontend
            })
        
        # Step 5: Sort by score (highest first)
        scored_combinations.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"  🏆 Top score: {scored_combinations[0]['score']:.1f}")
        print(f"  📊 Score range: {scored_combinations[-1]['score']:.1f} - {scored_combinations[0]['score']:.1f}")
        
        return scored_combinations
    
    def has_time_conflicts(self, classes: List[Dict]) -> bool:
        """
        Check if any two classes have overlapping time
        
        ABSOLUTE RULE: Không được đăng ký 2 lớp trùng lịch
        Xung đột khi:
        1. Trùng study_week (có tuần chung)
        2. VÀ trùng study_date (có ngày chung)
        3. VÀ trùng giờ học
        
        Returns:
            True if conflict exists, False otherwise
        """
        for i, class1 in enumerate(classes):
            for class2 in classes[i+1:]:
                # Step 1: Check study_week overlap
                weeks1 = set(class1.get('study_week', []) or [])
                weeks2 = set(class2.get('study_week', []) or [])
                
                # If no common weeks, no conflict
                common_weeks = weeks1 & weeks2
                if not common_weeks:
                    continue
                
                # Step 2: Check study_date overlap
                days1 = set(self._parse_study_days(class1['study_date']))
                days2 = set(self._parse_study_days(class2['study_date']))
                
                # If no common days, no conflict
                common_days = days1 & days2
                if not common_days:
                    continue
                
                # Step 3: Check time overlap
                start1 = self._parse_time(class1['study_time_start'])
                end1 = self._parse_time(class1['study_time_end'])
                start2 = self._parse_time(class2['study_time_start'])
                end2 = self._parse_time(class2['study_time_end'])
                
                # Time conflict if:
                # - start2 is within [start1, end1) OR
                # - end2 is within (start1, end1] OR
                # - class2 completely covers class1 (start2 <= start1 AND end2 >= end1)
                
                start2_in_range = start1 <= start2 < end1
                end2_in_range = start1 < end2 <= end1
                class2_covers_class1 = start2 <= start1 and end2 >= end1
                
                if start2_in_range or end2_in_range or class2_covers_class1:
                    print(f"⚠️ [CONFLICT] Class {class1.get('class_id')} vs {class2.get('class_id')}:")
                    print(f"  Weeks: {common_weeks}, Days: {common_days}")
                    print(f"  Class1: {start1}-{end1}, Class2: {start2}-{end2}")
                    return True  # Conflict found!
        
        return False  # No conflicts
    
    def calculate_schedule_metrics(self, classes: List[Dict]) -> Dict:
        """
        Calculate schedule quality metrics
        """
        # Group classes by day
        schedule_by_day = {}
        
        for cls in classes:
            days = self._parse_study_days(cls['study_date'])
            for day in days:
                if day not in schedule_by_day:
                    schedule_by_day[day] = []
                schedule_by_day[day].append(cls)
        
        metrics = {
            'total_credits': sum(cls.get('credits', 0) for cls in classes),
            'total_classes': len(classes),
            'study_days': len(schedule_by_day),
            'free_days': 7 - len(schedule_by_day),
            'continuous_study_days': 0,
            'average_daily_hours': 0.0,
            'earliest_start': None,
            'latest_end': None,
            'total_weekly_hours': 0.0,
            'time_conflicts': False  # Always False since we filter conflicts
        }
        
        # Calculate daily hours
        daily_hours = []
        all_starts = []
        all_ends = []
        
        for day, day_classes in schedule_by_day.items():
            # Sort by start time
            day_classes_sorted = sorted(day_classes, key=lambda x: self._parse_time(x['study_time_start']))
            
            # Calculate span (first start to last end)
            first_start = self._parse_time(day_classes_sorted[0]['study_time_start'])
            last_end = self._parse_time(day_classes_sorted[-1]['study_time_end'])
            
            # Calculate hours
            hours = (self._time_to_minutes(last_end) - self._time_to_minutes(first_start)) / 60.0
            daily_hours.append(hours)
            
            all_starts.append(first_start)
            all_ends.append(last_end)
            
            # Check if continuous (>5h)
            if hours > 5.0:
                metrics['continuous_study_days'] += 1
            
            # Calculate actual class hours (sum of all class durations)
            for cls in day_classes:
                start = self._parse_time(cls['study_time_start'])
                end = self._parse_time(cls['study_time_end'])
                class_hours = (self._time_to_minutes(end) - self._time_to_minutes(start)) / 60.0
                metrics['total_weekly_hours'] += class_hours
        
        if daily_hours:
            metrics['average_daily_hours'] = sum(daily_hours) / len(daily_hours)
        
        if all_starts:
            metrics['earliest_start'] = min(all_starts).strftime('%H:%M')
            metrics['latest_end'] = max(all_ends).strftime('%H:%M')
        
        return metrics
    
    def calculate_combination_score(self, classes: List[Dict], preferences: Dict) -> float:
        """
        Calculate overall score for a combination
        Higher score = better match to preferences
        
        Base: 100 points
        Adjustments based on preferences
        """
        score = 100.0
        
        metrics = self.calculate_schedule_metrics(classes)
        
        # === PREFERENCE: Free days (weight: 20) (skip if free_days_is_not_important) ===
        if not preferences.get('free_days_is_not_important', False):
            if preferences.get('prefer_free_days'):
                # More free days = higher score
                # 4 free days = +20, 3 = +15, 2 = +10, etc.
                score += metrics['free_days'] * 5
        
        # === PREFERENCE: Continuous study (weight: 20) (skip if continuous_is_not_important) ===
        if not preferences.get('continuous_is_not_important', False):
            if preferences.get('prefer_continuous'):
                # More continuous days = higher score
                score += metrics['continuous_study_days'] * 5
            elif preferences.get('prefer_continuous') == False:
                # Penalty for continuous days if user doesn't want them
                score -= metrics['continuous_study_days'] * 3
        
        # === PREFERENCE: Time period (weight: 15) ===
        time_period = preferences.get('time_period')
        if time_period:
            matching_classes = sum(
                1 for cls in classes
                if self._get_time_period(cls['study_time_start']) == time_period
            )
            match_rate = matching_classes / len(classes) if classes else 0
            score += match_rate * 15
        
        # === PREFERENCE: Avoid time periods (weight: 15) ===
        avoid_periods = preferences.get('avoid_time_periods', [])
        if avoid_periods:
            violating_classes = sum(
                1 for cls in classes
                if self._get_time_period(cls['study_time_start']) in avoid_periods
            )
            score -= violating_classes * 5  # Penalty per violation
        
        # === PREFERENCE: Days (weight: 15) (skip if day_is_not_important) ===
        if not preferences.get('day_is_not_important', False):
            prefer_days = preferences.get('prefer_days', [])
            if prefer_days:
                matching_days = 0
                for cls in classes:
                    days = self._parse_study_days(cls['study_date'])
                    if any(day in prefer_days for day in days):
                        matching_days += 1
                match_rate = matching_days / len(classes) if classes else 0
                score += match_rate * 15
            
            avoid_days = preferences.get('avoid_days', [])
            if avoid_days:
                violating_classes = 0
                for cls in classes:
                    days = self._parse_study_days(cls['study_date'])
                    if any(day in avoid_days for day in days):
                        violating_classes += 1
                score -= violating_classes * 5
        
        # === PREFERENCE: Early/Late start (weight: 10) (skip if time_is_not_important) ===
        if not preferences.get('time_is_not_important', False):
            if preferences.get('prefer_early_start'):
                # Earlier average start = higher score
                all_starts = [self._parse_time(cls['study_time_start']) for cls in classes]
                avg_start_minutes = sum(self._time_to_minutes(t) for t in all_starts) / len(all_starts)
                # 7:00 = 420min → score+10, 12:00 = 720min → score+0
                score += max(0, (720 - avg_start_minutes) / 300 * 10)
            
            if preferences.get('prefer_late_start'):
                # Later average start = higher score
                all_starts = [self._parse_time(cls['study_time_start']) for cls in classes]
                avg_start_minutes = sum(self._time_to_minutes(t) for t in all_starts) / len(all_starts)
                # 13:00 = 780min → score+10, 7:00 = 420min → score+0
                score += max(0, (avg_start_minutes - 420) / 360 * 10)
        
        # === BONUS: Available slots (weight: 5) ===
        # More available slots = better (less crowded)
        avg_availability = sum(
            cls.get('available_slots', 0) / max(cls.get('max_students', 1), 1)
            for cls in classes
        ) / len(classes) if classes else 0
        score += avg_availability * 5
        
        # === BONUS: Credits balance (weight: 5) ===
        # Prefer combinations with reasonable credit count (12-18)
        total_credits = metrics['total_credits']
        if 12 <= total_credits <= 18:
            score += 5
        elif total_credits < 12:
            score -= (12 - total_credits)  # Penalty for too few
        
        return round(score, 2)
    
    # === Helper methods ===
    
    def _parse_study_days(self, study_date: str) -> List[str]:
        """Parse study_date string to list of days"""
        if not study_date:
            return []
        return [day.strip() for day in study_date.split(',')]
    
    def _parse_time(self, time_val) -> time:
        """Parse time value to time object"""
        from datetime import timedelta
        
        if isinstance(time_val, time):
            return time_val
        if isinstance(time_val, timedelta):
            # Convert timedelta (seconds) to time object
            total_seconds = int(time_val.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return time(hours, minutes)
        if isinstance(time_val, str):
            try:
                return datetime.strptime(time_val, '%H:%M').time()
            except:
                return time(0, 0)
        return time(0, 0)
    
    def _time_to_minutes(self, t: time) -> int:
        """Convert time to minutes since midnight"""
        return t.hour * 60 + t.minute
    
    def _get_time_period(self, time_val) -> str:
        """Get time period (morning/afternoon/evening)"""
        t = self._parse_time(time_val)
        minutes = self._time_to_minutes(t)
        
        if 0 <= minutes < 720:  # 0:00 - 12:00
            return 'morning'
        elif 720 <= minutes < 1080:  # 12:00 - 18:00
            return 'afternoon'
