from sqlalchemy.orm import Session
from app.models.__init__ import Student, LearnedSubject, SemesterGPA, Subject
from app.utils.grade_calculator import letter_grade_to_score
from typing import Dict, Any


def calculate_student_stats(student_id: str, db: Session) -> Dict[str, Any]:
    """
    Tính toán tất cả thống kê cho student dựa trên LearnedSubject
    """
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise ValueError(f"Student {student_id} not found")

    # Lấy tất cả learned subjects của student
    learned_subjects = db.query(LearnedSubject).filter(
        LearnedSubject.student_id == student_id
    ).all()

    if not learned_subjects:
        return {
            'cpa': 0.0,
            'failed_subjects_number': 0,
            'study_subjects_number': 0,
            'total_failed_credits': 0,
            'total_learned_credits': 0,
            'year_level': "Trình độ năm 1",
            'warning_level': "Cảnh cáo mức 0",
            'level_3_warning_number': 0
        }

    total_points = 0.0
    total_credits = 0
    failed_count = 0
    failed_credits = 0
    passed_credits = 0

    for learned in learned_subjects:
        # Lấy subject để có credits
        subject = db.query(Subject).filter(Subject.id == learned.subject_id).first()
        if not subject:
            continue

        grade_score = letter_grade_to_score(learned.grade)
        credits = subject.credits

        # Cộng vào tổng điểm và tín chỉ
        total_points += grade_score * credits
        total_credits += credits

        # Kiểm tra failed (điểm < 1.0)
        if grade_score < 1.0:
            failed_count += 1
            failed_credits += credits
        else:
            passed_credits += credits

    # Tính CPA
    cpa = total_points / total_credits if total_credits > 0 else 0.0

    # Tính year level dựa trên tín chỉ đã qua
    year_level = calculate_year_level(passed_credits)

    # Tính warning level dựa trên CPA
    warning_level, level_3_count = calculate_warning_level(student_id, cpa, db)

    return {
        'cpa': round(cpa, 2),
        'failed_subjects_number': failed_count,
        'study_subjects_number': len(learned_subjects),
        'total_failed_credits': failed_credits,
        'total_learned_credits': passed_credits,
        'year_level': year_level,
        'warning_level': warning_level,
        'level_3_warning_number': level_3_count
    }


def calculate_year_level(passed_credits: int) -> str:
    """
    Tính year level dựa trên số tín chỉ đã qua
    """
    if passed_credits >= 90:
        return "Trình độ năm 4"
    elif passed_credits >= 60:
        return "Trình độ năm 3"
    elif passed_credits >= 30:
        return "Trình độ năm 2"
    else:
        return "Trình độ năm 1"


def calculate_warning_level(student_id: str, current_cpa: float, db: Session) -> tuple[str, int]:
    """
    Tính warning level dựa trên CPA hiện tại và lịch sử semester GPA
    """
    # Đếm số lần CPA < 2.0 trong các semester trước
    semester_gpas = db.query(SemesterGPA).filter(
        SemesterGPA.student_id == student_id,
        SemesterGPA.gpa < 2.0
    ).all()

    low_gpa_count = len(semester_gpas)

    # Kiểm tra CPA hiện tại
    if current_cpa < 2.0:
        low_gpa_count += 1

    # Tính warning level
    if low_gpa_count == 0:
        return "Cảnh cáo mức 0", 0
    elif low_gpa_count == 1:
        return "Cảnh cáo mức 1", 0
    elif low_gpa_count == 2:
        return "Cảnh cáo mức 2", 0
    else:
        # Đếm số lần warning level 3
        level_3_warnings = db.query(SemesterGPA).filter(
            SemesterGPA.student_id == student_id
        ).count()  # Simplified - should track actual level 3 warnings
        
        return "Cảnh cáo mức 3", max(0, low_gpa_count - 2)


def update_student_stats(student_id: str, db: Session) -> None:
    """
    Cập nhật tất cả thống kê của student
    """
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise ValueError(f"Student {student_id} not found")

    stats = calculate_student_stats(student_id, db)
    
    for key, value in stats.items():
        setattr(student, key, value)
    
    db.commit()


def update_semester_gpa(student_id: str, semester: str, db: Session) -> None:
    """
    Tính và cập nhật GPA cho một semester cụ thể
    """
    # Lấy các learned subjects trong semester này
    learned_subjects = db.query(LearnedSubject).filter(
        LearnedSubject.student_id == student_id,
        LearnedSubject.semester == semester
    ).all()

    if not learned_subjects:
        return

    total_points = 0.0
    total_credits = 0

    for learned in learned_subjects:
        subject = db.query(Subject).filter(Subject.id == learned.subject_id).first()
        if not subject:
            continue

        grade_score = letter_grade_to_score(learned.grade)
        credits = subject.credits

        total_points += grade_score * credits
        total_credits += credits

    semester_gpa = total_points / total_credits if total_credits > 0 else 0.0

    # Kiểm tra xem đã có record SemesterGPA chưa
    existing_gpa = db.query(SemesterGPA).filter(
        SemesterGPA.student_id == student_id,
        SemesterGPA.semester == semester
    ).first()

    if existing_gpa:
        existing_gpa.gpa = round(semester_gpa, 2)
        existing_gpa.total_credits = total_credits
    else:
        new_gpa = SemesterGPA(
            student_id=student_id,
            semester=semester,
            gpa=round(semester_gpa, 2),
            total_credits=total_credits
        )
        db.add(new_gpa)

    db.commit()
