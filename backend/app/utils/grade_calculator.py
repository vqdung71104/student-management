"""
Utility functions for GPA and student status calculations
"""

def letter_grade_to_score(letter_grade: str) -> float:
    """Convert letter grade to 4.0 scale score"""
    grade_mapping = {
        'F': 0.0,
        'D': 1.0,
        'D+': 1.5,
        'C': 2.0,
        'C+': 2.5,
        'B': 3.0,
        'B+': 3.5,
        'A': 4.0,
        'A+': 4.0
    }
    return grade_mapping.get(letter_grade.upper(), 0.0)

def calculate_warning_level(total_failed_credits: int) -> str:
    """Calculate warning level based on failed credits"""
    if total_failed_credits >= 27:
        return "Cảnh cáo mức 3"
    elif total_failed_credits >= 16:
        return "Cảnh cáo mức 2"
    elif total_failed_credits >= 8:
        return "Cảnh cáo mức 1"
    else:
        return "Cảnh cáo mức 0"

def calculate_year_level(total_learned_credits: int) -> str:
    """Calculate year level based on learned credits"""
    if total_learned_credits >= 128:
        return "Trình độ năm 5"
    elif total_learned_credits >= 96:
        return "Trình độ năm 4"
    elif total_learned_credits >= 64:
        return "Trình độ năm 3"
    elif total_learned_credits >= 32:
        return "Trình độ năm 2"
    else:
        return "Trình độ năm 1"
