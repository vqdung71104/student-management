"""
Subject Suggestion Rule Engine
Rule-Based System (RBS) for suggesting subjects to register

Priority Rules:
1. Register minimum credits and maximize (close to max allowed)
2. Priority for F-grade subjects (retake failed subjects)
3. Priority for subjects in current semester (based on learning_semester)
4. Register political subjects (SSH series)
5. Register physical education subjects (PE series)
6. Register supplementary subjects (CH, ME, EM, ED, ET, TEX series)
7. Register other program subjects if CPA > 3.4
8. Improve D/D+/C grades if credits <= 20

Credit Limits:
- Maximum: 28 credits (or 18 if warning level 2-3)
- Minimum: 8 credits
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import os


class SubjectSuggestionRuleEngine:
    """Rule-Based System for Subject Registration Suggestions"""
    
    def __init__(self, db: Session, config_path: Optional[str] = None):
        """
        Initialize rule engine with database session and configuration
        
        Args:
            db: Database session
            config_path: Path to rules_config.json (optional)
        """
        self.db = db
        
        # Load configuration from JSON file
        if config_path is None:
            # Default path relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, 'rules_config.json')
        
        self._load_config(config_path)
    
    def _load_config(self, config_path: str):
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Load subject categories
            self.POLITICAL_SUBJECTS = config['subject_categories']['political_subjects']
            self.PHYSICAL_EDUCATION_SUBJECTS = config['subject_categories']['physical_education_subjects']
            self.SUPPLEMENTARY_SUBJECTS = config['subject_categories']['supplementary_subjects']
            
            # Load credit limits
            self.MIN_CREDITS = config['credit_limits']['min_credits']
            self.MAX_CREDITS_NORMAL = config['credit_limits']['max_credits_normal']
            self.MAX_CREDITS_WARNING = config['credit_limits']['max_credits_warning']
            self.IMPROVEMENT_THRESHOLD = config['credit_limits']['improvement_threshold']
            
            # Credit limits by semester type and warning level
            self.MIN_CREDITS_MAIN_SEMESTER = config['credit_limits'].get('min_credits_main_semester', 12)
            self.MAX_CREDITS_MAIN_SEMESTER = config['credit_limits'].get('max_credits_main_semester', 24)
            self.MAX_CREDITS_SUMMER = config['credit_limits'].get('max_credits_summer', 8)
            
            # Credit limits for warning levels (main semester)
            self.MIN_CREDITS_WARNING_1 = config['credit_limits'].get('min_credits_warning_1', 10)
            self.MAX_CREDITS_WARNING_1 = config['credit_limits'].get('max_credits_warning_1', 18)
            self.MIN_CREDITS_WARNING_2 = config['credit_limits'].get('min_credits_warning_2', 8)
            self.MAX_CREDITS_WARNING_2 = config['credit_limits'].get('max_credits_warning_2', 14)
            
            # Credit limits for students not meeting foreign language requirements
            self.MIN_CREDITS_NO_FOREIGN_LANG = config['credit_limits'].get('min_credits_no_foreign_lang', 8)
            self.MAX_CREDITS_NO_FOREIGN_LANG = config['credit_limits'].get('max_credits_no_foreign_lang', 14)
            
            # Load grade thresholds
            self.FAST_TRACK_CPA = config['grade_thresholds']['fast_track_cpa']
            self.IMPROVEMENT_GRADES = config['grade_thresholds']['improvement_grades']
            self.FAILED_GRADE = config['grade_thresholds']['failed_grade']
            
            # Load grade priorities (conversion to scale 4.0)
            self.GRADE_PRIORITY = config['grade_conversion']
            
            # Load requirements
            self.POLITICAL_REQUIRED = config['requirements']['political_required']
            self.PE_REQUIRED = config['requirements']['pe_required']
            self.SUPPLEMENTARY_REQUIRED = config['requirements']['supplementary_required']
            
            print(f"✅ Rule engine configuration loaded from {config_path}")
            
        except FileNotFoundError:
            print(f"⚠️ Config file not found: {config_path}, using default values")
            self._set_default_config()
        except Exception as e:
            print(f"⚠️ Error loading config: {e}, using default values")
            self._set_default_config()
    
    def _set_default_config(self):
        """Set default configuration if JSON file is not available"""
        # Subject Categories
        self.POLITICAL_SUBJECTS = [
            'SSH1111', 'SSH1121', 'SSH1131', 'SSH1141', 'SSH1151', 'EM1170'
        ]
        self.PHYSICAL_EDUCATION_SUBJECTS = [
            'PE2102', 'PE2202', 'PE2302', 'PE2402', 'PE2502', 'PE2101', 'PE2151',
            'PE2201', 'PE2301', 'PE2401', 'PE2501', 'PE2601', 'PE2701', 'PE2801',
            'PE2901', 'PE1024', 'PE1015', 'PE2261', 'PE2020', 'PE2021', 'PE2022',
            'PE2023', 'PE2024', 'PE2025', 'PE2026', 'PE2027', 'PE2028', 'PE2029',
            'PE1010', 'PE1020', 'PE1030', 'PE2010', 'PE2011', 'PE2012', 'PE2013',
            'PE2014', 'PE2015', 'PE2016', 'PE2017', 'PE2018', 'PE2019'
        ]
        self.SUPPLEMENTARY_SUBJECTS = [
            'CH2021', 'ME3123', 'ME3124', 'EM1010', 'EM1180',
            'ED3280', 'ED3220', 'ET3262', 'TEX3123'
        ]
        
        # Credit limits
        self.MIN_CREDITS = 8
        self.MAX_CREDITS_NORMAL = 28
        self.MAX_CREDITS_WARNING = 18
        self.IMPROVEMENT_THRESHOLD = 20
        
        # Credit limits by semester type and warning level
        self.MIN_CREDITS_MAIN_SEMESTER = 12
        self.MAX_CREDITS_MAIN_SEMESTER = 24
        self.MAX_CREDITS_SUMMER = 8
        
        self.MIN_CREDITS_WARNING_1 = 10
        self.MAX_CREDITS_WARNING_1 = 18
        self.MIN_CREDITS_WARNING_2 = 8
        self.MAX_CREDITS_WARNING_2 = 14
        
        self.MIN_CREDITS_NO_FOREIGN_LANG = 8
        self.MAX_CREDITS_NO_FOREIGN_LANG = 14
        
        # Grade thresholds
        self.FAST_TRACK_CPA = 3.4
        self.IMPROVEMENT_GRADES = ['D', 'D+', 'C']
        self.FAILED_GRADE = 'F'
        
        # Grade priorities
        self.GRADE_PRIORITY = {
            'F': 0, 'D': 1, 'D+': 1.5, 'C': 2.0, 'C+': 2.5,
            'B': 3.0, 'B+': 3.5, 'A': 4.0, 'A+': 4.0
        }
        
        # Requirements
        self.POLITICAL_REQUIRED = 6
        self.PE_REQUIRED = 4
        self.SUPPLEMENTARY_REQUIRED = 3
    
    def get_current_semester(self) -> str:
        """
        Calculate current semester name based on current date
        
        Semester naming: YYYYS where:
        - YYYY: academic year start (e.g., 2024 for 2024-2025)
        - S: semester number (1, 2, 3)
        
        Semester periods:
        - Semester 2: September - January
        - Semester 3: February - July  
        - Semester 1: August (supplementary)
        
        Examples:
        - November 2025 → "20251" (semester 1 of 2024-2025)
        - March 2025 → "20242" (semester 2 of 2024-2025)
        - August 2025 → "20243" (semester 3 of 2024-2025)
        - Đăng ký học phần thì sẽ đăng ký cho kỳ sau đó
        """
        now = datetime.now()
        month = now.month
        year = now.year
        
        if 9 <= month <= 12:
            # September - December: Semester 1 of current year
            return f"{year}2"
        elif 1 <= month <= 1:
            # January: Semester 1 of previous year
            return f"{year - 1}3"
        elif 2 <= month <= 7:
            # February - July: Semester 2 of previous year
            return f"{year - 1}3"
        else:  # month == 8
            # August: Semester 3 of previous year
            return f"{year - 1}1"
    
    def calculate_student_semester_number(
        self, 
        student_id: int, 
        current_semester: str
    ) -> int:
        """
        Calculate which semester number the student is in
        (excluding supplementary semesters)
        
        Args:
            student_id: Student ID
            current_semester: Current semester (e.g., "20251")
        
        Returns:
            Semester number (1, 2, 3, 4, 5, 6, 7, 8)
        """
        # Get all semesters from learned_subjects (completed semesters)
        query = """
            SELECT DISTINCT ls.semester
            FROM learned_subjects ls
            WHERE ls.student_id = :student_id
            AND ls.semester IS NOT NULL
            ORDER BY ls.semester
        """
        
        result = self.db.execute(
            text(query),
            {"student_id": student_id}
        )
        
        completed_semesters = [row[0] for row in result.fetchall()]
        
        # Count non-supplementary semesters (exclude semester 3)
        semester_count = 0
        for sem in completed_semesters:
            if sem and not sem.endswith('3'):  # Exclude supplementary
                semester_count += 1
        
        # Add 1 for current semester if not yet in completed list
        if current_semester not in completed_semesters:
            semester_count += 1
        
        return semester_count
    
    def get_student_data(self, student_id: int) -> Dict:
        """
        Get comprehensive student data
        
        Returns:
            Dict with keys: cpa, gpa, warning_level, completed_subjects, grades
        """
        # Get student info
        student_query = """
            SELECT cpa, warning_level
            FROM students
            WHERE id = :student_id
        """
        student_result = self.db.execute(
            text(student_query),
            {"student_id": student_id}
        ).fetchone()
        
        if not student_result:
            raise ValueError(f"Student {student_id} not found")
        
        # Get learned subjects with grades
        learned_query = """
            SELECT 
                s.subject_id,
                s.subject_name,
                ls.letter_grade,
                s.credits
            FROM learned_subjects ls
            JOIN subjects s ON ls.subject_id = s.id
            WHERE ls.student_id = :student_id
        """
        learned_result = self.db.execute(
            text(learned_query),
            {"student_id": student_id}
        ).fetchall()
        
        completed_subjects = {}
        for row in learned_result:
            subject_id = row[0]
            completed_subjects[subject_id] = {
                'subject_id': subject_id,
                'subject_name': row[1],
                'grade': row[2],
                'credits': row[3]
            }
        
        # Parse warning_level from string like "Cảnh cáo mức 2" to int 2
        warning_str = student_result[1] if student_result[1] else "Cảnh cáo mức 0"
        try:
            warning_level = int(warning_str.split()[-1]) if warning_str else 0
        except:
            warning_level = 0
        
        return {
            'cpa': float(student_result[0]) if student_result[0] else 0.0,
            'warning_level': warning_level,
            'completed_subjects': completed_subjects
        }
    
    def is_summer_semester(self, semester: str) -> bool:
        """
        Check if semester is summer semester (ends with 3)
        
        Args:
            semester: Semester string (e.g., "20243", "20251")
        
        Returns:
            True if summer semester, False otherwise
        """
        return semester.endswith('3')
    
    def is_final_year(self, student_semester_number: int) -> bool:
        """
        Check if student is in final year (semester 7-8)
        
        Args:
            student_semester_number: Current semester number of student
        
        Returns:
            True if final year, False otherwise
        """
        return student_semester_number >= 7
    
    def get_credit_limits(
        self, 
        warning_level: int,
        current_semester: str,
        student_semester_number: int,
        has_foreign_lang_requirement: bool = False
    ) -> Tuple[int, int]:
        """
        Get min/max credits allowed based on regulations
        
        Quy định:
        - Học kỳ chính (1,2): Học lực bình thường 12-24 TC
        - Học kỳ hè (3): Tối đa 8 TC
        - Cảnh cáo mức 1: 10-18 TC (học kỳ chính)
        - Cảnh cáo mức 2: 8-14 TC (học kỳ chính)
        - Chưa đạt ngoại ngữ: 8-14 TC (học kỳ chính)
        - Năm cuối (kỳ 7-8): Không áp dụng giới hạn tối thiểu
        
        Args:
            warning_level: Student warning level (0, 1, 2, 3)
            current_semester: Current semester (e.g., "20251")
            student_semester_number: Student's current semester number
            has_foreign_lang_requirement: True if student hasn't met foreign language requirement
        
        Returns:
            Tuple of (min_credits, max_credits)
        """
        # Check if summer semester
        if self.is_summer_semester(current_semester):
            return (0, self.MAX_CREDITS_SUMMER)
        
        # Check if final year - no minimum requirement
        is_final = self.is_final_year(student_semester_number)
        
        # Determine limits based on warning level and foreign language requirement
        if has_foreign_lang_requirement:
            min_credits = 0 if is_final else self.MIN_CREDITS_NO_FOREIGN_LANG
            max_credits = self.MAX_CREDITS_NO_FOREIGN_LANG
        elif warning_level == 1:
            min_credits = 0 if is_final else self.MIN_CREDITS_WARNING_1
            max_credits = self.MAX_CREDITS_WARNING_1
        elif warning_level >= 2:
            min_credits = 0 if is_final else self.MIN_CREDITS_WARNING_2
            max_credits = self.MAX_CREDITS_WARNING_2
        else:
            # Normal student
            min_credits = 0 if is_final else self.MIN_CREDITS_MAIN_SEMESTER
            max_credits = self.MAX_CREDITS_MAIN_SEMESTER
        
        return (min_credits, max_credits)
    
    def get_max_credits_allowed(self, warning_level: int) -> int:
        """
        Get maximum credits allowed based on warning level (deprecated - use get_credit_limits)
        
        Args:
            warning_level: Student warning level (0, 1, 2, 3)
        
        Returns:
            Maximum credits allowed
        """
        if warning_level >= 2:
            return self.MAX_CREDITS_WARNING
        return self.MAX_CREDITS_NORMAL
    
    def get_available_subjects(
        self, 
        student_id: int,
        current_semester: str
    ) -> List[Dict]:
        """
        Get all available subjects that student can register
        (not yet completed with passing grade)
        
        Returns:
            List of dicts with subject info
        """
        # Get student's course
        course_query = """
            SELECT course_id
            FROM students
            WHERE id = :student_id
        """
        course_result = self.db.execute(
            text(course_query),
            {"student_id": student_id}
        ).fetchone()
        
        if not course_result:
            raise ValueError(f"Student {student_id} has no course assigned")
        
        course_id = course_result[0]
        
        # Get all subjects in the course with learning_semester
        subjects_query = """
            SELECT 
                s.id,
                s.subject_id,
                s.subject_name,
                s.credits,
                cs.learning_semester
            FROM course_subjects cs
            JOIN subjects s ON cs.subject_id = s.id
            WHERE cs.course_id = :course_id
        """
        subjects_result = self.db.execute(
            text(subjects_query),
            {"course_id": course_id}
        ).fetchall()
        
        available_subjects = []
        for row in subjects_result:
            available_subjects.append({
                'id': row[0],
                'subject_id': row[1],
                'subject_name': row[2],
                'credits': row[3],
                'learning_semester': row[4] if row[4] else None
            })
        
        return available_subjects
    
    def rule_1_filter_failed_subjects(
        self,
        available_subjects: List[Dict],
        student_data: Dict
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        RULE 1: Priority for F-grade subjects (must retake)
        
        Returns:
            (failed_subjects, remaining_subjects)
        """
        failed = []
        remaining = []
        
        completed = student_data['completed_subjects']
        
        for subject in available_subjects:
            subject_id = subject['subject_id']
            if subject_id in completed and completed[subject_id]['grade'] == 'F':
                subject['priority_reason'] = 'Failed subject (F) - Must retake'
                subject['priority_level'] = 1
                failed.append(subject)
            else:
                remaining.append(subject)
        
        return failed, remaining
    
    def rule_2_filter_semester_match(
        self,
        subjects: List[Dict],
        current_semester_number: int,
        student_data: Dict
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        RULE 2: Priority for subjects matching current semester
        Excludes subjects already learned (not failed)
        
        Args:
            subjects: List of available subjects
            current_semester_number: Current semester number (1-8)
            student_data: Student data including completed_subjects
        
        Returns:
            (matching_subjects, non_matching_subjects)
        """
        matching = []
        non_matching = []
        completed = student_data['completed_subjects']
        
        for subject in subjects:
            subject_id = subject['subject_id']
            learning_sem = subject.get('learning_semester')
            
            # Skip if subject already learned with passing grade
            if subject_id in completed and completed[subject_id]['grade'] != 'F':
                non_matching.append(subject)
                continue
            
            if learning_sem and learning_sem == current_semester_number:
                subject['priority_reason'] = f'Matches semester {current_semester_number}'
                subject['priority_level'] = 2
                matching.append(subject)
            else:
                non_matching.append(subject)
        
        return matching, non_matching
    
    def rule_3_filter_political_subjects(
        self,
        subjects: List[Dict],
        student_data: Dict
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        RULE 3: Register political subjects (SSH series, EM1170)
        Must complete all 6 subjects
        If all political subjects are completed, don't suggest any more
        
        Returns:
            (political_subjects, remaining_subjects)
        """
        political = []
        remaining = []
        
        completed = student_data['completed_subjects']
        
        # Count completed political subjects (with passing grade)
        political_completed_count = sum(
            1 for sid, data in completed.items()
            if sid in self.POLITICAL_SUBJECTS and data['grade'] != 'F'
        )
        
        # If all political subjects completed, don't suggest more
        if political_completed_count >= self.POLITICAL_REQUIRED:
            return political, subjects
        
        for subject in subjects:
            subject_id = subject['subject_id']
            
            if subject_id in self.POLITICAL_SUBJECTS:
                # Check if not yet completed with passing grade
                if subject_id not in completed or completed[subject_id]['grade'] == 'F':
                    subject['priority_reason'] = f'Political subject ({political_completed_count}/{self.POLITICAL_REQUIRED} completed)'
                    subject['priority_level'] = 3
                    political.append(subject)
            else:
                remaining.append(subject)
        
        return political, remaining
    
    def rule_4_filter_physical_education(
        self,
        subjects: List[Dict],
        student_data: Dict
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        RULE 4: Register physical education subjects (PE series)
        Must complete 4 out of all PE subjects
        If 4 PE subjects completed, don't suggest more
        
        Returns:
            (pe_subjects, remaining_subjects)
        """
        pe = []
        remaining = []
        
        completed = student_data['completed_subjects']
        
        # Count how many PE subjects already completed
        pe_completed_count = sum(
            1 for sid, data in completed.items()
            if sid in self.PHYSICAL_EDUCATION_SUBJECTS and data['grade'] != 'F'
        )
        
        # If already completed 4 PE subjects, don't suggest more
        if pe_completed_count >= self.PE_REQUIRED:
            return pe, subjects
        
        for subject in subjects:
            subject_id = subject['subject_id']
            
            if subject_id in self.PHYSICAL_EDUCATION_SUBJECTS:
                # Only suggest if not yet completed with passing grade
                if subject_id not in completed or completed[subject_id]['grade'] == 'F':
                    subject['priority_reason'] = f'PE subject ({pe_completed_count}/{self.PE_REQUIRED} completed)'
                    subject['priority_level'] = 4
                    pe.append(subject)
            else:
                remaining.append(subject)
        
        return pe, remaining
    
    def rule_5_filter_supplementary_subjects(
        self,
        subjects: List[Dict],
        student_data: Dict
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        RULE 5: Register supplementary subjects
        Must complete 3 out of the list
        If 3 supplementary subjects completed, don't suggest more
        
        Returns:
            (supplementary_subjects, remaining_subjects)
        """
        supplementary = []
        remaining = []
        
        completed = student_data['completed_subjects']
        
        # Count completed supplementary subjects
        supp_completed_count = sum(
            1 for sid, data in completed.items()
            if sid in self.SUPPLEMENTARY_SUBJECTS and data['grade'] != 'F'
        )
        
        # If already completed 3 supplementary subjects, don't suggest more
        if supp_completed_count >= self.SUPPLEMENTARY_REQUIRED:
            return supplementary, subjects
        
        for subject in subjects:
            subject_id = subject['subject_id']
            
            if subject_id in self.SUPPLEMENTARY_SUBJECTS:
                # Only suggest if not yet completed with passing grade
                if subject_id not in completed or completed[subject_id]['grade'] == 'F':
                    subject['priority_reason'] = f'Supplementary subject ({supp_completed_count}/{self.SUPPLEMENTARY_REQUIRED} completed)'
                    subject['priority_level'] = 5
                    supplementary.append(subject)
            else:
                remaining.append(subject)
        
        return supplementary, remaining
    
    def rule_6_filter_fast_track(
        self,
        subjects: List[Dict],
        student_data: Dict
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        RULE 6: Register additional subjects for fast track
        Only if CPA > 3.4
        
        Returns:
            (fast_track_subjects, remaining_subjects)
        """
        fast_track = []
        remaining = []
        
        cpa = student_data['cpa']
        completed = student_data['completed_subjects']
        
        if cpa > self.FAST_TRACK_CPA:
            for subject in subjects:
                subject_id = subject['subject_id']
                # Not yet completed or failed
                if subject_id not in completed or completed[subject_id]['grade'] == self.FAILED_GRADE:
                    subject['priority_reason'] = f'Fast track (CPA={cpa:.2f} > {self.FAST_TRACK_CPA})'
                    subject['priority_level'] = 6
                    fast_track.append(subject)
        else:
            remaining = subjects
        
        return fast_track, remaining
    
    def rule_7_filter_grade_improvement(
        self,
        subjects: List[Dict],
        student_data: Dict,
        current_total_credits: int,
        student_id: int
    ) -> List[Dict]:
        """
        RULE 7: Improve low grades (D, D+, C, C+)
        Only if total credits <= 20
        Only suggest if subject has fewer occurrences in learned_subjects
        Priority order: D+ > D > C+ > C (lower grades first)
        
        Returns:
            List of subjects to improve
        """
        if current_total_credits > self.IMPROVEMENT_THRESHOLD:
            return []
        
        improvement = []
        completed = student_data['completed_subjects']
        
        # Get count of each subject in learned_subjects
        count_query = """
            SELECT subject_id, COUNT(*) as count
            FROM learned_subjects
            WHERE student_id = :student_id
            GROUP BY subject_id
        """
        count_result = self.db.execute(
            text(count_query),
            {"student_id": student_id}
        ).fetchall()
        
        subject_counts = {row[0]: row[1] for row in count_result}
        
        # Improvement grades including C+
        improvement_grades = ['D+', 'D', 'C+', 'C']
        
        for subject in subjects:
            subject_id = subject['subject_id']
            
            if subject_id in completed:
                grade = completed[subject_id]['grade']
                
                # Check if grade needs improvement
                if grade in improvement_grades:
                    # Get occurrence count (default to 1 if not in query result)
                    occurrence_count = subject_counts.get(subject_id, 1)
                    
                    # Only suggest if has few occurrences (1 or 2 attempts)
                    if occurrence_count <= 2:
                        subject['priority_reason'] = f'Improve grade {grade} (attempt {occurrence_count})'
                        subject['priority_level'] = 7
                        subject['original_grade'] = grade
                        subject['occurrence_count'] = occurrence_count
                        
                        # Priority mapping: D+ = 0, D = 1, C+ = 2, C = 3
                        grade_order = {'D+': 0, 'D': 1, 'C+': 2, 'C': 3}
                        subject['grade_order'] = grade_order.get(grade, 99)
                        
                        improvement.append(subject)
        
        # Sort by grade order (D+ > D > C+ > C), then by credits (fewer first)
        improvement.sort(key=lambda x: (x['grade_order'], x['credits']))
        
        return improvement
    
    def suggest_subjects(
        self,
        student_id: int,
        max_credits: Optional[int] = None
    ) -> Dict:
        """
        Main method: Suggest subjects based on all rules
        
        Args:
            student_id: Student ID
            max_credits: Optional max credits override
        
        Returns:
            Dict with:
                - suggested_subjects: List of suggested subjects (ordered by priority)
                - total_credits: Total suggested credits
                - current_semester: Current semester
                - student_semester_number: Which semester student is in
                - max_credits_allowed: Max credits allowed
                - summary: Summary of suggestions by category
        """
        # Get current semester info
        current_semester = self.get_current_semester()
        student_semester_number = self.calculate_student_semester_number(
            student_id, current_semester
        )
        
        # Get student data
        student_data = self.get_student_data(student_id)
        
        # Get credit limits based on new regulations
        # TODO: Add check for foreign language requirement from database
        has_foreign_lang_requirement = False  # Placeholder
        
        min_credits_required, max_credits_allowed = self.get_credit_limits(
            warning_level=student_data['warning_level'],
            current_semester=current_semester,
            student_semester_number=student_semester_number,
            has_foreign_lang_requirement=has_foreign_lang_requirement
        )
        
        # Override if provided
        if max_credits is not None:
            max_credits_allowed = max_credits
        
        # Get available subjects
        available_subjects = self.get_available_subjects(
            student_id, current_semester
        )
        
        # Apply rules in priority order
        suggested = []
        total_credits = 0
        
        # Track subjects by category for summary
        summary = {
            'failed_retake': [],
            'semester_match': [],
            'political': [],
            'physical_education': [],
            'supplementary': [],
            'fast_track': [],
            'grade_improvement': []
        }
        
        # RULE 1: Failed subjects (F)
        failed, remaining = self.rule_1_filter_failed_subjects(
            available_subjects, student_data
        )
        
        for subject in failed:
            if total_credits + subject['credits'] <= max_credits_allowed:
                suggested.append(subject)
                summary['failed_retake'].append(subject)
                total_credits += subject['credits']
        
        # RULE 2: Semester match (with learned subjects check)
        semester_match, remaining = self.rule_2_filter_semester_match(
            remaining, student_semester_number, student_data
        )
        
        for subject in semester_match:
            if total_credits + subject['credits'] <= max_credits_allowed:
                suggested.append(subject)
                summary['semester_match'].append(subject)
                total_credits += subject['credits']
        
        # RULE 3: Political subjects
        political, remaining = self.rule_3_filter_political_subjects(
            remaining, student_data
        )
        
        for subject in political:
            if total_credits + subject['credits'] <= max_credits_allowed:
                suggested.append(subject)
                summary['political'].append(subject)
                total_credits += subject['credits']
        
        # RULE 4: Physical education
        pe, remaining = self.rule_4_filter_physical_education(
            remaining, student_data
        )
        
        for subject in pe[:self.PE_REQUIRED]:  # Max PE subjects required
            if total_credits + subject['credits'] <= max_credits_allowed:
                suggested.append(subject)
                summary['physical_education'].append(subject)
                total_credits += subject['credits']
        
        # RULE 5: Supplementary subjects
        supplementary, remaining = self.rule_5_filter_supplementary_subjects(
            remaining, student_data
        )
        
        for subject in supplementary[:self.SUPPLEMENTARY_REQUIRED]:  # Max supplementary required
            if total_credits + subject['credits'] <= max_credits_allowed:
                suggested.append(subject)
                summary['supplementary'].append(subject)
                total_credits += subject['credits']
        
        # RULE 6: Fast track (if CPA > threshold)
        fast_track, remaining = self.rule_6_filter_fast_track(
            remaining, student_data
        )
        
        for subject in fast_track:
            if total_credits + subject['credits'] <= max_credits_allowed:
                suggested.append(subject)
                summary['fast_track'].append(subject)
                total_credits += subject['credits']
        
        # RULE 7: Grade improvement (if credits <= 20)
        if total_credits <= self.IMPROVEMENT_THRESHOLD:
            improvement = self.rule_7_filter_grade_improvement(
                available_subjects, student_data, total_credits, student_id
            )
            
            for subject in improvement:
                if total_credits + subject['credits'] <= max_credits_allowed:
                    suggested.append(subject)
                    summary['grade_improvement'].append(subject)
                    total_credits += subject['credits']
        
        # RULE 8: Remaining course subjects (if total < 28 credits)
      #  if total_credits < 28:
      #      remaining_subjects = self.rule_8_filter_remaining_course_subjects(
      #          remaining, student_data
      #      )
      #      
      #      for subject in remaining_subjects:
      #          if total_credits + subject['credits'] <= max_credits_allowed:
      #              suggested.append(subject)
      #              if 'remaining_course' not in summary:
      #                  summary['remaining_course'] = []
      #              summary['remaining_course'].append(subject)
      #              total_credits += subject['credits']
        
        # Check minimum credits requirement
        meets_minimum = total_credits >= min_credits_required
        
        return {
            'suggested_subjects': suggested,
            'total_credits': total_credits,
            'current_semester': current_semester,
            'student_semester_number': student_semester_number,
            'max_credits_allowed': max_credits_allowed,
            'min_credits_required': min_credits_required,
            'meets_minimum': meets_minimum,
            'student_cpa': student_data['cpa'],
            'warning_level': student_data['warning_level'],
            'summary': summary
        }
    
    def format_suggestion_response(self, suggestion_result: Dict) -> str:
        """
        Format suggestion result into human-readable text

        Args:
            suggestion_result: Result from suggest_subjects()

        Returns:
            Formatted text response
        """
        response = []

        # Header
        response.append("🎓 **GỢI Ý ĐĂNG KÝ HỌC PHẦN**")
        response.append("=" * 50)

        # Student info section
        response.append("\n**📊 THÔNG TIN SINH VIÊN**")
        response.append(f"• Kỳ học hiện tại: {suggestion_result['current_semester']} \n")
        response.append(f"• Đang ở kỳ thứ: {suggestion_result['student_semester_number']}\n")
        response.append(f"• CPA hiện tại: {suggestion_result['student_cpa']:.2f}\n")
        response.append(f"• Mức cảnh báo: {suggestion_result['warning_level']}\n")

        # Credit limits section
        response.append("\n**📋 GIỚI HẠN TÍN CHỈ**")
        response.append(f"• Tín chỉ tối thiểu: {suggestion_result['min_credits_required']} TC\n")
        response.append(f"• Tín chỉ tối đa: {suggestion_result['max_credits_allowed']} TC\n")
        response.append(f"• Tổng tín chỉ gợi ý: {suggestion_result['total_credits']} TC\n")

        status = "✅ ĐẠT YÊU CẦU" if suggestion_result['meets_minimum'] else "⚠️ CHƯA ĐẠT YÊU CẦU"
        response.append(f"• Trạng thái: {status}\n")

        # Suggested subjects by priority
        response.append("\n**📚 DANH SÁCH MÔN HỌC ĐƯỢC GỢI Ý**")

        summary = suggestion_result['summary']

        if summary['failed_retake']:
            response.append("\n**🔴 ƯU TIÊN CAO NHẤT: Môn học lại (điểm F)**")
            response.append("Các môn bạn cần học lại do không đạt:")
            for i, subj in enumerate(summary['failed_retake'], 1):
                response.append(f"{i}. **{subj['subject_id']}** - {subj['subject_name']} ({subj['credits']} tín chỉ)")

        if summary['semester_match']:
            response.append("\n**🟢 ƯU TIÊN 2: Môn đúng lộ trình**")
            response.append("Các môn nên học trong kỳ này theo lộ trình:")
            for i, subj in enumerate(summary['semester_match'], 1):
                response.append(f"{i}. **{subj['subject_id']}** - {subj['subject_name']} ({subj['credits']} tín chỉ)")

        if summary['political']:
            response.append("\n**🟡 ƯU TIÊN 3: Môn chính trị**")
            response.append("Các môn chính trị bắt buộc:")
            for i, subj in enumerate(summary['political'], 1):
                response.append(f"{i}. **{subj['subject_id']}** - {subj['subject_name']} ({subj['credits']} tín chỉ)")

        if summary['physical_education']:
            response.append("\n**🏃 ƯU TIÊN 4: Môn thể chất**")
            response.append("Các môn giáo dục thể chất:")
            for i, subj in enumerate(summary['physical_education'], 1):
                response.append(f"{i}. **{subj['subject_id']}** - {subj['subject_name']} ({subj['credits']} tín chỉ)")

        if summary['supplementary']:
            response.append("\n**🔵 ƯU TIÊN 5: Môn bổ trợ**")
            response.append("Các môn bổ trợ kiến thức:")
            for i, subj in enumerate(summary['supplementary'], 1):
                response.append(f"{i}. **{subj['subject_id']}** - {subj['subject_name']} ({subj['credits']} tín chỉ)")

        if summary['fast_track']:
            response.append("\n**⚡ ƯU TIÊN 6: Học nhanh**")
            response.append(f"Các môn học nhanh (dành cho sinh viên CPA > {self.FAST_TRACK_CPA}):")
            for i, subj in enumerate(summary['fast_track'], 1):
                response.append(f"{i}. **{subj['subject_id']}** - {subj['subject_name']} ({subj['credits']} tín chỉ)")

        if summary['grade_improvement']:
            response.append("\n**📈 ƯU TIÊN 7: Cải thiện điểm**")
            response.append("Các môn nên học lại để cải thiện điểm:")
            for i, subj in enumerate(summary['grade_improvement'], 1):
                orig_grade = subj.get('original_grade', '?')
                response.append(f"{i}. **{subj['subject_id']}** - {subj['subject_name']} ({subj['credits']} TC) - Điểm hiện tại: {orig_grade}")
        
        if summary.get('remaining_course'):
            response.append("\n**📚 MÔN HỌC CÒN LẠI TRONG CHƯƠNG TRÌNH**")
            response.append("Các môn còn lại trong chương trình học:")
            for i, subj in enumerate(summary['remaining_course'], 1):
                response.append(f"{i}. **{subj['subject_id']}** - {subj['subject_name']} ({subj['credits']} tín chỉ)")

        # Total summary
        response.append("\n**📊 TỔNG KẾT**")
        response.append(f"• **Tổng số môn học:** {len(suggestion_result['suggested_subjects'])} môn")
        response.append(f"• **Tổng số tín chỉ:** {suggestion_result['total_credits']} TC")

        if not suggestion_result['meets_minimum']:
            response.append("\n**💡 LỜI KHUYÊN**")
            response.append(f"Bạn cần đăng ký thêm ít nhất {suggestion_result['min_credits_required'] - suggestion_result['total_credits']} tín chỉ nữa để đạt yêu cầu tối thiểu.")

        response.append("\n**Chúc bạn một kỳ học thành công! 🎉**")

        return "\n".join(response)