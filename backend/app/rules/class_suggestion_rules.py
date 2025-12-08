"""
Class Registration Suggestion Rule Engine
Rule-Based System (RBS) for suggesting classes based on student preferences

Student Preferences:
1. Time preference: early/late start, morning/afternoon/evening
2. Study schedule: continuous classes, maximize free days
3. Weekday preference: avoid specific days (e.g., no Saturday)
4. Teacher preference: specific teacher selection
5. Room preference: specific building/location

Rule-Based Filtering:
- Filter by study time (morning/afternoon/evening)
- Filter by study days (avoid specific weekdays)
- Filter by teacher name
- Sort by schedule optimization (continuous classes, free days)
- Sort by start/end time preference
"""

from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, time, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import os


class ClassSuggestionRuleEngine:
    """Rule-Based System for Class Registration Suggestions"""
    
    # Time periods definition
    MORNING_START = time(6, 0)
    MORNING_END = time(12, 0)
    AFTERNOON_START = time(12, 0)
    AFTERNOON_END = time(18, 0)
    EVENING_START = time(18, 0)
    EVENING_END = time(22, 0)
    
    # Early/late thresholds
    EARLY_START_THRESHOLD = time(8, 0)  # Classes starting before 8:00 are "early"
    LATE_END_THRESHOLD = time(17, 0)    # Classes ending after 17:00 are "late"
    
    # Continuous class threshold (in minutes)
    CONTINUOUS_CLASS_GAP = 30  # Max 30 minutes gap between classes
    MIN_DAILY_HOURS = 5.0  # Minimum 5 hours for "intensive" day
    
    # Days mapping
    WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    WEEKDAY_VI = {
        "Monday": "Thứ 2",
        "Tuesday": "Thứ 3",
        "Wednesday": "Thứ 4",
        "Thursday": "Thứ 5",
        "Friday": "Thứ 6",
        "Saturday": "Thứ 7",
        "Sunday": "Chủ nhật"
    }
    
    def __init__(self, db: Session, config_path: Optional[str] = None):
        """
        Initialize class suggestion rule engine
        
        Args:
            db: Database session
            config_path: Path to class_rules_config.json (optional)
        """
        self.db = db
        
        # Load configuration
        if config_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, 'class_rules_config.json')
        
        self._load_config(config_path)
    
    def _load_config(self, config_path: str):
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Load time preferences
            time_pref = config.get('time_preferences', {})
            self.MORNING_START = self._parse_time(time_pref.get('morning_start', '06:00'))
            self.MORNING_END = self._parse_time(time_pref.get('morning_end', '12:00'))
            self.AFTERNOON_START = self._parse_time(time_pref.get('afternoon_start', '12:00'))
            self.AFTERNOON_END = self._parse_time(time_pref.get('afternoon_end', '18:00'))
            
            # Load thresholds
            thresholds = config.get('thresholds', {})
            self.EARLY_START_THRESHOLD = self._parse_time(thresholds.get('early_start', '08:00'))
            self.LATE_END_THRESHOLD = self._parse_time(thresholds.get('late_end', '17:00'))
            self.CONTINUOUS_CLASS_GAP = thresholds.get('continuous_gap_minutes', 30)
            self.MIN_DAILY_HOURS = thresholds.get('min_daily_hours', 5.0)
            
            print(f"✅ Class rules configuration loaded from {config_path}")
            
        except FileNotFoundError:
            print(f"⚠️ Config file not found: {config_path}, using default values")
        except Exception as e:
            print(f"⚠️ Error loading config: {e}, using default values")
    
    def _parse_time(self, time_str: str) -> time:
        """Parse time string to time object"""
        try:
            return datetime.strptime(time_str, "%H:%M").time()
        except:
            return time(0, 0)
    
    def get_available_classes(
        self,
        student_id: int,
        subject_ids: Optional[List[int]] = None
    ) -> List[Dict]:
        """
        Get all available classes that student can register
        
        Args:
            student_id: Student ID
            subject_ids: Optional list of subject IDs to filter
        
        Returns:
            List of dicts with class info
        """
        # Base query
        query = """
            SELECT 
                c.id,
                c.class_id,
                c.class_name,
                c.classroom,
                c.study_date,
                c.study_time_start,
                c.study_time_end,
                c.study_week,
                c.teacher_name,
                c.max_student_number,
                s.subject_id,
                s.subject_name,
                s.credits,
                COUNT(cr.id) as registered_count
            FROM classes c
            JOIN subjects s ON c.subject_id = s.id
            LEFT JOIN class_registers cr ON c.id = cr.class_id
        """
        
        # Add subject filter if provided
        if subject_ids:
            placeholders = ','.join([':subj_' + str(i) for i in range(len(subject_ids))])
            query += f" WHERE c.subject_id IN ({placeholders})"
        
        query += """
            GROUP BY c.id
            HAVING COUNT(cr.id) < c.max_student_number
        """
        
        # Execute query
        params = {}
        if subject_ids:
            params = {f'subj_{i}': sid for i, sid in enumerate(subject_ids)}
        
        result = self.db.execute(text(query), params).fetchall()
        
        classes = []
        for row in result:
            # Parse study_week from JSON
            study_week_data = row[7]  # This is JSON from database
            if study_week_data:
                # If it's already a list (from JSON), convert to comma-separated string
                if isinstance(study_week_data, list):
                    study_weeks_str = ','.join(str(w) for w in study_week_data)
                else:
                    study_weeks_str = str(study_week_data)
            else:
                study_weeks_str = 'all'
            
            # Convert timedelta to time if needed
            study_time_start = row[5]
            study_time_end = row[6]
            
            # MySQL TIME type returns timedelta, convert to time
            if isinstance(study_time_start, timedelta):
                total_seconds = int(study_time_start.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                study_time_start = time(hours, minutes)
            
            if isinstance(study_time_end, timedelta):
                total_seconds = int(study_time_end.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                study_time_end = time(hours, minutes)
            
            classes.append({
                'id': row[0],
                'class_id': row[1],
                'class_name': row[2],
                'classroom': row[3],
                'study_date': row[4],
                'study_time_start': study_time_start,
                'study_time_end': study_time_end,
                'study_weeks': study_weeks_str,  # Study weeks as string (e.g., "1,3,5,7,9" or "all")
                'teacher_name': row[8],
                'max_students': row[9],
                'subject_id': row[10],
                'subject_name': row[11],
                'credits': row[12],
                'registered_count': row[13],
                'available_slots': row[9] - row[13]
            })
        
        return classes
    
    def parse_study_days(self, study_date: str) -> List[str]:
        """
        Parse study_date string into list of days
        
        Args:
            study_date: String like "Monday,Wednesday,Friday"
        
        Returns:
            List of day names
        """
        if not study_date:
            return []
        return [day.strip() for day in study_date.split(',')]
    
    def parse_study_weeks(self, study_weeks: str) -> Set[int]:
        """
        Parse study_weeks string into set of week numbers
        
        Args:
            study_weeks: String like "1,3,5,7,9,11,13,15" or "2-16" or "all"
        
        Returns:
            Set of week numbers
        """
        if not study_weeks or study_weeks.strip().lower() == 'all':
            # All weeks 1-16
            return set(range(1, 17))
        
        weeks = set()
        parts = study_weeks.split(',')
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                # Range: "2-16"
                start, end = part.split('-')
                weeks.update(range(int(start), int(end) + 1))
            else:
                # Single week: "1"
                weeks.add(int(part))
        
        return weeks
    
    def get_time_period(self, study_time: time) -> str:
        """
        Determine time period (morning/afternoon/evening)
        
        Args:
            study_time: Time object
        
        Returns:
            'morning', 'afternoon', or 'evening'
        """
        if self.MORNING_START <= study_time < self.MORNING_END:
            return 'morning'
        elif self.AFTERNOON_START <= study_time < self.AFTERNOON_END:
            return 'afternoon'
        else:
            return 'evening'
    
    def is_early_start(self, study_time_start: time) -> bool:
        """Check if class starts early"""
        return study_time_start < self.EARLY_START_THRESHOLD
    
    def is_late_end(self, study_time_end: time) -> bool:
        """Check if class ends late"""
        return study_time_end > self.LATE_END_THRESHOLD
    
    def calculate_class_duration(self, start: time, end: time) -> float:
        """
        Calculate class duration in hours
        
        Args:
            start: Start time
            end: End time
        
        Returns:
            Duration in hours
        """
        start_minutes = start.hour * 60 + start.minute
        end_minutes = end.hour * 60 + end.minute
        return (end_minutes - start_minutes) / 60.0
    
    def has_schedule_conflict(self, class1: Dict, class2: Dict) -> bool:
        """
        ABSOLUTE RULE: Check if two classes have schedule conflict
        
        Two classes conflict if:
        1. They share at least one study day (e.g., both on Monday)
        2. They share at least one study week (e.g., both in week 1)
        3. Their study times overlap on that day
        
        Examples:
            - Class A: Monday weeks 1,3,5 08:15-11:45
            - Class B: Monday weeks 2,4,6 09:25-14:00
            → NO CONFLICT (different weeks)
            
            - Class A: Monday weeks 1,3,5 08:15-11:45
            - Class B: Monday weeks 1,3,5 09:25-14:00
            → CONFLICT (same day, same weeks, time overlap)
            
            - Class A: Monday weeks 1,3,5 08:15-09:00
            - Class B: Monday weeks 1,3,5 09:25-10:00
            → NO CONFLICT (no time overlap)
        
        Args:
            class1: First class dict
            class2: Second class dict
        
        Returns:
            True if conflict exists, False otherwise
        """
        # Get study days
        days1 = set(self.parse_study_days(class1.get('study_date', '')))
        days2 = set(self.parse_study_days(class2.get('study_date', '')))
        
        # Check if they share any study day
        common_days = days1.intersection(days2)
        if not common_days:
            return False
        
        # Get study weeks
        weeks1 = self.parse_study_weeks(class1.get('study_weeks', 'all'))
        weeks2 = self.parse_study_weeks(class2.get('study_weeks', 'all'))
        
        # Check if they share any study week
        common_weeks = weeks1.intersection(weeks2)
        if not common_weeks:
            return False
        
        # They share both days and weeks → check time overlap
        start1 = class1['study_time_start']
        end1 = class1['study_time_end']
        start2 = class2['study_time_start']
        end2 = class2['study_time_end']
        
        # Convert to minutes for easier comparison
        start1_min = start1.hour * 60 + start1.minute
        end1_min = end1.hour * 60 + end1.minute
        start2_min = start2.hour * 60 + start2.minute
        end2_min = end2.hour * 60 + end2.minute
        
        # Check time overlap
        # No overlap if: class1 ends before class2 starts OR class2 ends before class1 starts
        no_overlap = (end1_min <= start2_min) or (end2_min <= start1_min)
        
        return not no_overlap
    
    def filter_by_time_preference(
        self,
        classes: List[Dict],
        preferences: Dict
    ) -> List[Dict]:
        """
        Filter classes by time preferences
        
        Preferences:
            - time_period: 'morning', 'afternoon', 'evening', or 'any'
            - avoid_early_start: bool
            - avoid_late_end: bool
        
        Returns:
            Filtered list of classes
        """
        filtered = []
        
        time_period = preferences.get('time_period', 'any')
        avoid_early = preferences.get('avoid_early_start', False)
        avoid_late = preferences.get('avoid_late_end', False)
        
        for cls in classes:
            start_time = cls['study_time_start']
            end_time = cls['study_time_end']
            
            # Check time period
            if time_period != 'any':
                class_period = self.get_time_period(start_time)
                if class_period != time_period:
                    continue
            
            # Check early start
            if avoid_early and self.is_early_start(start_time):
                continue
            
            # Check late end
            if avoid_late and self.is_late_end(end_time):
                continue
            
            filtered.append(cls)
        
        return filtered
    
    def filter_by_weekday_preference(
        self,
        classes: List[Dict],
        preferences: Dict
    ) -> List[Dict]:
        """
        Filter classes by weekday preferences
        
        Preferences:
            - avoid_days: List[str] - days to avoid (e.g., ['Saturday', 'Sunday'])
            - prefer_days: List[str] - preferred days (if specified, only these days)
        
        Returns:
            Filtered list of classes
        """
        filtered = []
        
        avoid_days = set(preferences.get('avoid_days', []))
        prefer_days = preferences.get('prefer_days', [])
        
        for cls in classes:
            study_days = self.parse_study_days(cls['study_date'])
            
            # Check if any study day is in avoid list
            if avoid_days and any(day in avoid_days for day in study_days):
                continue
            
            # Check if at least one study day is in prefer list (if specified)
            # User: "tôi muốn học vào thứ 5" → prefer_days: ['Thursday']
            # Class: "Tuesday,Thursday" → Keep it (has Thursday) ✅
            # Class: "Monday,Wednesday" → Filter out (no Thursday) ❌
            if prefer_days and not any(day in prefer_days for day in study_days):
                continue
            
            filtered.append(cls)
        
        return filtered
    
    def filter_by_teacher(
        self,
        classes: List[Dict],
        teacher_names: List[str]
    ) -> List[Dict]:
        """
        Filter classes by teacher names
        
        Args:
            classes: List of classes
            teacher_names: List of preferred teacher names
        
        Returns:
            Filtered list of classes
        """
        if not teacher_names:
            return classes
        
        teacher_set = set(name.lower().strip() for name in teacher_names)
        
        filtered = []
        for cls in classes:
            teacher = cls.get('teacher_name', '').lower().strip()
            if any(preferred in teacher or teacher in preferred for preferred in teacher_set):
                filtered.append(cls)
        
        return filtered
    
    def filter_no_schedule_conflict(
        self,
        classes: List[Dict],
        registered_classes: List[Dict]
    ) -> List[Dict]:
        """
        ABSOLUTE RULE: Filter out classes that conflict with already registered classes
        
        Args:
            classes: List of candidate classes
            registered_classes: List of already registered classes
        
        Returns:
            List of classes without schedule conflicts
        """
        if not registered_classes:
            return classes
        
        filtered = []
        for cls in classes:
            has_conflict = False
            conflict_with = []
            
            for registered in registered_classes:
                if self.has_schedule_conflict(cls, registered):
                    has_conflict = True
                    conflict_with.append(registered['class_id'])
            
            if not has_conflict:
                filtered.append(cls)
            else:
                # Mark conflict for debugging
                cls['schedule_conflict'] = True
                cls['conflict_with'] = conflict_with
        
        return filtered
    
    def filter_one_class_per_subject(
        self,
        classes: List[Dict],
        registered_classes: List[Dict]
    ) -> List[Dict]:
        """
        ABSOLUTE RULE: Each subject can only have one class registered
        
        Args:
            classes: List of candidate classes
            registered_classes: List of already registered classes
        
        Returns:
            List of classes for subjects not yet registered
        """
        # Get subject IDs already registered
        registered_subject_ids = set(cls['subject_id'] for cls in registered_classes)
        
        filtered = []
        for cls in classes:
            if cls['subject_id'] not in registered_subject_ids:
                filtered.append(cls)
            else:
                # Mark as duplicate subject
                cls['duplicate_subject'] = True
        
        return filtered
    
    def calculate_schedule_metrics(
        self,
        classes: List[Dict]
    ) -> Dict:
        """
        Calculate schedule optimization metrics
        
        Metrics:
            - total_study_days: Number of unique days
            - free_days: Number of free days (7 - study days)
            - continuous_sessions: Number of days with continuous classes
            - intensive_days: Number of days with > 5 hours of classes
        
        Returns:
            Dict with metrics
        """
        # Group classes by day
        day_schedules = {}
        for cls in classes:
            days = self.parse_study_days(cls['study_date'])
            for day in days:
                if day not in day_schedules:
                    day_schedules[day] = []
                day_schedules[day].append({
                    'start': cls['study_time_start'],
                    'end': cls['study_time_end'],
                    'class_id': cls['class_id']
                })
        
        # Calculate metrics
        total_study_days = len(day_schedules)
        free_days = 7 - total_study_days
        continuous_sessions = 0
        intensive_days = 0
        
        for day, sessions in day_schedules.items():
            # Sort by start time
            sessions.sort(key=lambda x: x['start'])
            
            # Check if continuous
            is_continuous = True
            total_duration = 0
            
            for i in range(len(sessions)):
                duration = self.calculate_class_duration(
                    sessions[i]['start'],
                    sessions[i]['end']
                )
                total_duration += duration
                
                # Check gap with next session
                if i < len(sessions) - 1:
                    gap_minutes = (
                        sessions[i+1]['start'].hour * 60 + sessions[i+1]['start'].minute -
                        sessions[i]['end'].hour * 60 - sessions[i]['end'].minute
                    )
                    if gap_minutes > self.CONTINUOUS_CLASS_GAP:
                        is_continuous = False
            
            if is_continuous and len(sessions) > 1:
                continuous_sessions += 1
            
            if total_duration >= self.MIN_DAILY_HOURS:
                intensive_days += 1
        
        return {
            'total_study_days': total_study_days,
            'free_days': free_days,
            'continuous_sessions': continuous_sessions,
            'intensive_days': intensive_days,
            'day_schedules': day_schedules
        }
    
    def count_preference_violations(
        self,
        cls: Dict,
        preferences: Dict
    ) -> Tuple[int, List[str]]:
        """
        Count how many preference rules a class violates
        (NOT including absolute rules like schedule conflict or duplicate subject)
        
        Args:
            cls: Class dict
            preferences: User preferences dict
        
        Returns:
            (violation_count, list_of_violations)
        """
        violations = 0
        violation_list = []
        
        start_time = cls['study_time_start']
        end_time = cls['study_time_end']
        study_days = set(self.parse_study_days(cls['study_date']))
        
        # Time period violation
        time_period = self.get_time_period(start_time)
        preferred_period = preferences.get('time_period', 'any')
        if preferred_period != 'any' and time_period != preferred_period:
            violations += 1
            violation_list.append(f'Not {preferred_period} class (is {time_period})')
        
        # Early start violation
        if preferences.get('avoid_early_start', False) and self.is_early_start(start_time):
            violations += 1
            violation_list.append(f'Starts too early ({start_time.strftime("%H:%M")} < 08:00)')
        
        # Late end violation
        if preferences.get('avoid_late_end', False) and self.is_late_end(end_time):
            violations += 1
            violation_list.append(f'Ends too late ({end_time.strftime("%H:%M")} > 17:00)')
        
        # Avoid days violation
        avoid_days = set(preferences.get('avoid_days', []))
        common_avoid = study_days.intersection(avoid_days)
        if common_avoid:
            violations += len(common_avoid)
            days_vi = [self.WEEKDAY_VI.get(d, d) for d in common_avoid]
            violation_list.append(f'Has avoided days: {", ".join(days_vi)}')
        
        # Prefer days violation
        prefer_days = preferences.get('prefer_days', [])
        if prefer_days:
            prefer_set = set(prefer_days)
            non_preferred = study_days - prefer_set
            if non_preferred:
                violations += len(non_preferred)
                days_vi = [self.WEEKDAY_VI.get(d, d) for d in non_preferred]
                violation_list.append(f'Has non-preferred days: {", ".join(days_vi)}')
        
        # Teacher preference violation
        preferred_teachers = preferences.get('preferred_teachers', [])
        if preferred_teachers:
            teacher_lower = cls.get('teacher_name', '').lower()
            is_preferred_teacher = any(pref.lower() in teacher_lower for pref in preferred_teachers)
            if not is_preferred_teacher:
                violations += 1
                violation_list.append(f'Not preferred teacher ({cls.get("teacher_name", "Unknown")})')
        
        return violations, violation_list
    
    def rank_classes_by_preferences(
        self,
        classes: List[Dict],
        preferences: Dict
    ) -> List[Dict]:
        """
        Rank and sort classes based on preferences
        
        Preferences:
            - maximize_free_days: bool - prefer schedules with more free days
            - prefer_continuous: bool - prefer continuous class sessions
            - prefer_intensive: bool - prefer intensive study days (>5h/day)
            - prefer_early_start: bool - prefer early start times
            - prefer_late_start: bool - prefer late start times
        
        Returns:
            Sorted list of classes with ranking scores
        """
        ranked = []
        
        for cls in classes:
            score = 0
            reasons = []
            
            # Count violations
            violation_count, violation_list = self.count_preference_violations(cls, preferences)
            cls['violation_count'] = violation_count
            cls['violations'] = violation_list
            
            # Time-based scoring
            start_time = cls['study_time_start']
            end_time = cls['study_time_end']
            
            if preferences.get('prefer_early_start') and self.is_early_start(start_time):
                score += 10
                reasons.append('Starts early')
            
            if preferences.get('prefer_late_start') and not self.is_early_start(start_time):
                score += 10
                reasons.append('Starts late')
            
            if not self.is_late_end(end_time):
                score += 5
                reasons.append('Ends before 17:00')
            
            # Time period scoring
            time_period = self.get_time_period(start_time)
            preferred_period = preferences.get('time_period', 'any')
            if preferred_period != 'any' and time_period == preferred_period:
                score += 15
                reasons.append(f'{time_period.capitalize()} class')
            
            # Weekday scoring
            study_days = self.parse_study_days(cls['study_date'])
            avoid_days = set(preferences.get('avoid_days', []))
            if not any(day in avoid_days for day in study_days):
                score += 5
                reasons.append('No avoided days')
            
            # Teacher preference
            preferred_teachers = preferences.get('preferred_teachers', [])
            if preferred_teachers:
                teacher_lower = cls.get('teacher_name', '').lower()
                if any(pref.lower() in teacher_lower for pref in preferred_teachers):
                    score += 20
                    reasons.append(f"Teacher: {cls.get('teacher_name')}")
            
            # Available slots
            availability_ratio = cls['available_slots'] / cls['max_students']
            if availability_ratio > 0.5:
                score += 5
                reasons.append('High availability')
            
            ranked.append({
                **cls,
                'preference_score': score,
                'match_reasons': reasons
            })
        
        # Sort by: fewer violations first, then higher score
        ranked.sort(key=lambda x: (-x.get('violation_count', 0), -x['preference_score']))
        
        return ranked
    
    def suggest_classes(
        self,
        student_id: int,
        subject_ids: List[int],
        preferences: Dict,
        registered_classes: Optional[List[Dict]] = None,
        min_suggestions: int = 5
    ) -> Dict:
        """
        Main method: Suggest classes based on preferences
        
        ABSOLUTE RULES (must not be violated):
        1. No schedule conflicts with registered classes
        2. One class per subject only
        
        PREFERENCE RULES (can be violated if not enough suggestions):
        - Time period (morning/afternoon/evening)
        - Avoid early start / late end
        - Avoid specific days
        - Teacher preference
        
        Args:
            student_id: Student ID
            subject_ids: List of subject IDs to find classes for
            preferences: Dict with user preferences
            registered_classes: List of already registered classes (for conflict check)
            min_suggestions: Minimum number of suggestions to return (default: 5)
        
        Returns:
            Dict with suggested classes and metrics
        """
        if registered_classes is None:
            registered_classes = []
        
        # Get available classes
        available_classes = self.get_available_classes(student_id, subject_ids)
        
        if not available_classes:
            return {
                'suggested_classes': [],
                'total_classes': 0,
                'schedule_metrics': {},
                'preferences_applied': preferences,
                'fully_satisfied': 0,
                'with_violations': 0
            }
        
        # STEP 1: Apply ABSOLUTE RULES (must pass)
        absolute_filtered = available_classes
        
        # Absolute Rule 1: No schedule conflicts
        absolute_filtered = self.filter_no_schedule_conflict(
            absolute_filtered,
            registered_classes
        )
        
        # Absolute Rule 2: One class per subject
        absolute_filtered = self.filter_one_class_per_subject(
            absolute_filtered,
            registered_classes
        )
        
        # STEP 2: Try to apply PREFERENCE RULES
        preference_filtered = absolute_filtered.copy()
        
        # Filter by time preference
        if 'time_period' in preferences or 'avoid_early_start' in preferences:
            preference_filtered = self.filter_by_time_preference(
                preference_filtered,
                preferences
            )
        
        # Filter by weekday preference
        if 'avoid_days' in preferences or 'prefer_days' in preferences:
            preference_filtered = self.filter_by_weekday_preference(
                preference_filtered,
                preferences
            )
        
        # Filter by teacher
        if preferences.get('preferred_teachers'):
            preference_filtered = self.filter_by_teacher(
                preference_filtered,
                preferences['preferred_teachers']
            )
        
        # STEP 3: Rank all classes (both fully satisfied and with violations)
        fully_satisfied = self.rank_classes_by_preferences(preference_filtered, preferences)
        
        # If not enough fully satisfied classes, add classes with fewest violations
        final_suggestions = fully_satisfied.copy()
        
        if len(final_suggestions) < min_suggestions:
            # Get classes that didn't pass preference filters
            satisfied_ids = set(cls['id'] for cls in fully_satisfied)
            not_satisfied = [
                cls for cls in absolute_filtered
                if cls['id'] not in satisfied_ids
            ]
            
            # Rank by violations (fewest first)
            not_satisfied_ranked = self.rank_classes_by_preferences(not_satisfied, preferences)
            
            # Add classes with fewest violations
            needed = min_suggestions - len(final_suggestions)
            final_suggestions.extend(not_satisfied_ranked[:needed])
        
        # Limit to top suggestions
        final_suggestions = final_suggestions[:min_suggestions * 2]  # Return up to 2x for variety
        
        # Mark which suggestions fully satisfy preferences
        fully_satisfied_ids = set(cls['id'] for cls in fully_satisfied)
        for cls in final_suggestions:
            cls['fully_satisfies_preferences'] = cls['id'] in fully_satisfied_ids
        
        # Calculate schedule metrics
        metrics = self.calculate_schedule_metrics(final_suggestions)
        
        return {
            'suggested_classes': final_suggestions,
            'total_classes': len(final_suggestions),
            'fully_satisfied': len([c for c in final_suggestions if c.get('fully_satisfies_preferences')]),
            'with_violations': len([c for c in final_suggestions if not c.get('fully_satisfies_preferences')]),
            'schedule_metrics': metrics,
            'preferences_applied': preferences,
            'total_available': len(available_classes),
            'passed_absolute_rules': len(absolute_filtered),
            'filtered_by_preferences': len(preference_filtered)
        }
    
    def format_class_suggestions(self, suggestion_result: Dict) -> str:
        """
        Format suggestion result into human-readable text
        
        Args:
            suggestion_result: Result from suggest_classes()
        
        Returns:
            Formatted text response
        """
        lines = []
        
        # Header
        lines.append("🎓 **GỢI Ý LỚP HỌC PHẦN**")
        lines.append("=" * 50)
        lines.append("")
        
        # Summary
        total = suggestion_result['total_classes']
        filtered_out = suggestion_result.get('filtered_out', 0)
        
        lines.append("📊 **TỔNG QUAN**")
        lines.append(f"• Tổng số lớp phù hợp: **{total}** lớp")
        if filtered_out > 0:
            lines.append(f"• Đã lọc bỏ: {filtered_out} lớp không phù hợp")
        lines.append("")
        
        # Schedule metrics
        metrics = suggestion_result.get('schedule_metrics', {})
        if metrics:
            lines.append("📅 **LỊCH HỌC DỰ KIẾN**")
            lines.append(f"• Số ngày học: {metrics.get('total_study_days', 0)} ngày/tuần")
            lines.append(f"• Số ngày nghỉ: {metrics.get('free_days', 0)} ngày/tuần")
            if metrics.get('continuous_sessions', 0) > 0:
                lines.append(f"• Số buổi học liên tục: {metrics['continuous_sessions']} buổi")
            if metrics.get('intensive_days', 0) > 0:
                lines.append(f"• Số ngày học tập trung (>5h): {metrics['intensive_days']} ngày")
            lines.append("")
        
        # Preferences applied
        prefs = suggestion_result.get('preferences_applied', {})
        if prefs:
            lines.append("⚙️ **TIÊU CHÍ ÁP DỤNG**")
            if prefs.get('time_period') and prefs['time_period'] != 'any':
                period_map = {'morning': 'Buổi sáng', 'afternoon': 'Buổi chiều', 'evening': 'Buổi tối'}
                lines.append(f"• Buổi học: {period_map.get(prefs['time_period'], prefs['time_period'])}")
            if prefs.get('avoid_early_start'):
                lines.append("• Tránh học sớm (trước 8:00)")
            if prefs.get('avoid_late_end'):
                lines.append("• Tránh kết thúc muộn (sau 17:00)")
            if prefs.get('avoid_days'):
                days_vi = [self.WEEKDAY_VI.get(d, d) for d in prefs['avoid_days']]
                lines.append(f"• Tránh các ngày: {', '.join(days_vi)}")
            if prefs.get('preferred_teachers'):
                lines.append(f"• Giáo viên ưu tiên: {', '.join(prefs['preferred_teachers'])}")
            lines.append("")
        
        # Class list
        classes = suggestion_result['suggested_classes']
        if classes:
            lines.append("📚 **DANH SÁCH LỚP GỢI Ý**")
            lines.append("")
            
            # Group by subject
            by_subject = {}
            for cls in classes:
                subj_name = cls['subject_name']
                if subj_name not in by_subject:
                    by_subject[subj_name] = []
                by_subject[subj_name].append(cls)
            
            for i, (subject_name, subject_classes) in enumerate(by_subject.items(), 1):
                lines.append(f"**{i}. {subject_name}** ({subject_classes[0]['credits']} TC)")
                lines.append("")
                
                for j, cls in enumerate(subject_classes[:5], 1):  # Limit to top 5 per subject
                    score = cls.get('preference_score', 0)
                    fully_satisfied = cls.get('fully_satisfies_preferences', False)
                    violation_count = cls.get('violation_count', 0)
                    
                    # Add badge for fully satisfied
                    badge = "✅" if fully_satisfied else f"⚠️ ({violation_count} vi phạm)"
                    lines.append(f"   **Lớp {j}:** {cls['class_id']} - {cls['class_name']} {badge}")
                    
                    # Time and days
                    days_vi = [self.WEEKDAY_VI.get(d, d) for d in self.parse_study_days(cls['study_date'])]
                    lines.append(f"   • Thời gian: {cls['study_time_start'].strftime('%H:%M')} - {cls['study_time_end'].strftime('%H:%M')}")
                    lines.append(f"   • Ngày học: {', '.join(days_vi)}")
                    lines.append(f"   • Phòng: {cls['classroom']}")
                    lines.append(f"   • Giảng viên: {cls['teacher_name']}")
                    lines.append(f"   • Chỗ trống: {cls['available_slots']}/{cls['max_students']}")
                    
                    # Match reasons or violations
                    if fully_satisfied and cls.get('match_reasons'):
                        lines.append(f"   • Phù hợp: {', '.join(cls['match_reasons'])}")
                    elif not fully_satisfied and cls.get('violations'):
                        lines.append(f"   • Vi phạm tiêu chí: {', '.join(cls['violations'][:2])}")
                        if len(cls['violations']) > 2:
                            lines.append(f"     ...và {len(cls['violations']) - 2} vi phạm khác")
                    
                    lines.append(f"   • Điểm ưu tiên: ⭐ {score}/60")
                    lines.append("")
                
                if len(subject_classes) > 5:
                    lines.append(f"   _(Còn {len(subject_classes) - 5} lớp khác...)_")
                    lines.append("")
        else:
            lines.append("⚠️ Không tìm thấy lớp nào phù hợp với tiêu chí của bạn.")
            lines.append("Hãy thử điều chỉnh tiêu chí hoặc liên hệ phòng đào tạo.")
            lines.append("")
        
        lines.append("**Chúc bạn đăng ký thành công! 🎉**")
        
        return "\n".join(lines)
