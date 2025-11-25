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
        - Semester 1: September - January
        - Semester 2: February - July  
        - Semester 3: August (supplementary)
        
        Examples:
        - November 2025 → "20251" (semester 1 of 2024-2025)
        - March 2025 → "20242" (semester 2 of 2024-2025)
        - August 2025 → "20243" (semester 3 of 2024-2025)
        """
        now = datetime.now()
        month = now.month
        year = now.year
        
        if 9 <= month <= 12:
            # September - December: Semester 1 of current year
            return f"{year}1"
        elif 1 <= month <= 1:
            # January: Semester 1 of previous year
            return f"{year - 1}1"
        elif 2 <= month <= 7:
            # February - July: Semester 2 of previous year
            return f"{year - 1}2"
        else:  # month == 8
            # August: Semester 3 of previous year
            return f"{year - 1}3"
    
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
    
    def get_max_credits_allowed(self, warning_level: int) -> int:
        """
        Get maximum credits allowed based on warning level
        
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
        current_semester_number: int
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        RULE 2: Priority for subjects matching current semester
        
        Args:
            subjects: List of available subjects
            current_semester_number: Current semester number (1-8)
        
        Returns:
            (matching_subjects, non_matching_subjects)
        """
        matching = []
        non_matching = []
        
        for subject in subjects:
            learning_sem = subject.get('learning_semester')
            
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
        
        Returns:
            (political_subjects, remaining_subjects)
        """
        political = []
        remaining = []
        
        completed = student_data['completed_subjects']
        
        for subject in subjects:
            subject_id = subject['subject_id']
            
            if subject_id in self.POLITICAL_SUBJECTS:
                # Check if not yet completed with passing grade
                if subject_id not in completed or completed[subject_id]['grade'] == 'F':
                    subject['priority_reason'] = 'Political subject (required)'
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
        
        for subject in subjects:
            subject_id = subject['subject_id']
            
            if subject_id in self.PHYSICAL_EDUCATION_SUBJECTS:
                # Only suggest if haven't completed 4 PE subjects yet
                if pe_completed_count < 4:
                    if subject_id not in completed or completed[subject_id]['grade'] == 'F':
                        subject['priority_reason'] = f'PE subject ({pe_completed_count}/4 completed)'
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
        
        for subject in subjects:
            subject_id = subject['subject_id']
            
            if subject_id in self.SUPPLEMENTARY_SUBJECTS:
                # Only suggest if haven't completed 3 yet
                if supp_completed_count < 3:
                    if subject_id not in completed or completed[subject_id]['grade'] == 'F':
                        subject['priority_reason'] = f'Supplementary subject ({supp_completed_count}/3 completed)'
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
        current_total_credits: int
    ) -> List[Dict]:
        """
        RULE 7: Improve low grades (D, D+, C)
        Only if total credits <= 20
        Priority: F > D > D+ > C (with fewer credits first)
        
        Returns:
            List of subjects to improve
        """
        if current_total_credits > self.IMPROVEMENT_THRESHOLD:
            return []
        
        improvement = []
        completed = student_data['completed_subjects']
        
        for subject in subjects:
            subject_id = subject['subject_id']
            
            if subject_id in completed:
                grade = completed[subject_id]['grade']
                
                # Check if grade needs improvement
                if grade in self.IMPROVEMENT_GRADES:
                    subject['priority_reason'] = f'Improve grade {grade}'
                    subject['priority_level'] = 7
                    subject['grade_priority'] = self.GRADE_PRIORITY[grade]
                    subject['original_grade'] = grade
                    improvement.append(subject)
        
        # Sort by grade priority (F > D > D+ > C) then by credits (fewer first)
        improvement.sort(key=lambda x: (x['grade_priority'], x['credits']))
        
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
        
        # Get max credits allowed
        max_credits_allowed = max_credits or self.get_max_credits_allowed(
            student_data['warning_level']
        )
        
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
        
        # RULE 2: Semester match
        semester_match, remaining = self.rule_2_filter_semester_match(
            remaining, student_semester_number
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
                available_subjects, student_data, total_credits
            )
            
            for subject in improvement:
                if total_credits + subject['credits'] <= max_credits_allowed:
                    suggested.append(subject)
                    summary['grade_improvement'].append(subject)
                    total_credits += subject['credits']
        
        # Check minimum credits requirement
        meets_minimum = total_credits >= self.MIN_CREDITS
        
        return {
            'suggested_subjects': suggested,
            'total_credits': total_credits,
            'current_semester': current_semester,
            'student_semester_number': student_semester_number,
            'max_credits_allowed': max_credits_allowed,
            'min_credits_required': self.MIN_CREDITS,
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
        response.append("📚 GỢI Ý ĐĂNG KÝ HỌC PHẦN")
        response.append("=" * 60)
        
        # Student info
        response.append(f"\n📊 Thông tin sinh viên:")
        response.append(f"  • Kỳ học hiện tại: {suggestion_result['current_semester']}")
        response.append(f"  • Đang ở kỳ thứ: {suggestion_result['student_semester_number']}")
        response.append(f"  • CPA: {suggestion_result['student_cpa']:.2f}")
        response.append(f"  • Mức cảnh báo: {suggestion_result['warning_level']}")
        
        # Credit limits
        response.append(f"\n📋 Giới hạn tín chỉ:")
        response.append(f"  • Tối thiểu: {suggestion_result['min_credits_required']} tín chỉ")
        response.append(f"  • Tối đa: {suggestion_result['max_credits_allowed']} tín chỉ")
        response.append(f"  • Tổng gợi ý: {suggestion_result['total_credits']} tín chỉ")
        
        status = "✅ Đủ" if suggestion_result['meets_minimum'] else "❌ Chưa đủ"
        response.append(f"  • Trạng thái: {status}")
        
        # Suggested subjects by priority
        summary = suggestion_result['summary']
        
        if summary['failed_retake']:
            response.append(f"\n🔴 PRIORITY 1: Học lại môn điểm F ({len(summary['failed_retake'])} môn)")
            for subj in summary['failed_retake']:
                response.append(f"  • {subj['subject_id']} - {subj['subject_name']} ({subj['credits']} TC)")
        
        if summary['semester_match']:
            response.append(f"\n🟢 PRIORITY 2: Môn đúng kỳ học ({len(summary['semester_match'])} môn)")
            for subj in summary['semester_match']:
                response.append(f"  • {subj['subject_id']} - {subj['subject_name']} ({subj['credits']} TC)")
        
        if summary['political']:
            response.append(f"\n🟡 PRIORITY 3: Môn triết/chính trị ({len(summary['political'])} môn)")
            for subj in summary['political']:
                response.append(f"  • {subj['subject_id']} - {subj['subject_name']} ({subj['credits']} TC)")
        
        if summary['physical_education']:
            response.append(f"\n🟠 PRIORITY 4: Môn thể chất ({len(summary['physical_education'])} môn)")
            for subj in summary['physical_education']:
                response.append(f"  • {subj['subject_id']} - {subj['subject_name']} ({subj['credits']} TC)")
        
        if summary['supplementary']:
            response.append(f"\n🔵 PRIORITY 5: Môn bổ trợ ({len(summary['supplementary'])} môn)")
            for subj in summary['supplementary']:
                response.append(f"  • {subj['subject_id']} - {subj['subject_name']} ({subj['credits']} TC)")
        
        if summary['fast_track']:
            response.append(f"\n⚡ PRIORITY 6: Học nhanh (CPA > {self.FAST_TRACK_CPA}) ({len(summary['fast_track'])} môn)")
            for subj in summary['fast_track']:
                response.append(f"  • {subj['subject_id']} - {subj['subject_name']} ({subj['credits']} TC)")
        
        if summary['grade_improvement']:
            response.append(f"\n🔧 PRIORITY 7: Cải thiện điểm ({len(summary['grade_improvement'])} môn)")
            for subj in summary['grade_improvement']:
                orig_grade = subj.get('original_grade', '?')
                response.append(f"  • {subj['subject_id']} - {subj['subject_name']} ({subj['credits']} TC) - Điểm hiện tại: {orig_grade}")
        
        # Total summary
        response.append(f"\n📌 TỔNG KẾT:")
        response.append(f"  • Tổng số môn gợi ý: {len(suggestion_result['suggested_subjects'])} môn")
        response.append(f"  • Tổng tín chỉ: {suggestion_result['total_credits']} TC")
        
        return "\n".join(response)
