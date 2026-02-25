"""
Test Subject Suggestion Rule Engine
Run: python backend/app/tests/test_rule_engine.py
"""
import sys
sys.path.insert(0, 'C:/Users/Admin/student-management/backend')

from app.rules import SubjectSuggestionRuleEngine
from app.db.database import SessionLocal


def test_rule_engine():
    """Test the subject suggestion rule engine"""
    print("=" * 80)
    print("TESTING SUBJECT SUGGESTION RULE ENGINE")
    print("=" * 80)
    
    # Initialize
    db = SessionLocal()
    engine = SubjectSuggestionRuleEngine(db)
    
    # Test 1: Get current semester
    print("\n[Test 1] Current Semester Calculation")
    print("-" * 80)
    current_semester = engine.get_current_semester()
    print(f"Current semester: {current_semester}")
    
    # Test 2: Get student data
    print("\n[Test 2] Student Data Retrieval")
    print("-" * 80)
    try:
        student_id = 1
        student_data = engine.get_student_data(student_id)
        print(f"Student ID: {student_id}")
        print(f"CPA: {student_data['cpa']:.2f}")
        print(f"GPA: {student_data['gpa']:.2f}")
        print(f"Warning Level: {student_data['warning_level']}")
        print(f"Completed Subjects: {len(student_data['completed_subjects'])} subjects")
        
        # Show some completed subjects
        if student_data['completed_subjects']:
            print("\nSample completed subjects:")
            for i, (subject_id, data) in enumerate(list(student_data['completed_subjects'].items())[:5]):
                print(f"  {i+1}. {subject_id} - {data['subject_name']} - Grade: {data['grade']} ({data['credits']} TC)")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Calculate student semester number
    print("\n[Test 3] Student Semester Number")
    print("-" * 80)
    try:
        semester_num = engine.calculate_student_semester_number(student_id, current_semester)
        print(f"Student is in semester: {semester_num}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Get available subjects
    print("\n[Test 4] Available Subjects")
    print("-" * 80)
    try:
        available_subjects = engine.get_available_subjects(student_id, current_semester)
        print(f"Total available subjects: {len(available_subjects)}")
        
        # Show some available subjects
        if available_subjects:
            print("\nSample available subjects:")
            for i, subject in enumerate(available_subjects[:10]):
                learning_sem = subject.get('learning_semester', 'N/A')
                print(f"  {i+1}. {subject['subject_id']} - {subject['subject_name']} ({subject['credits']} TC) - Semester: {learning_sem}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 5: Main suggestion
    print("\n[Test 5] Complete Subject Suggestion")
    print("=" * 80)
    try:
        result = engine.suggest_subjects(student_id)
        
        # Print formatted response
        formatted_response = engine.format_suggestion_response(result)
        print(formatted_response)
        
        # Print detailed breakdown
        print("\n" + "=" * 80)
        print("DETAILED BREAKDOWN")
        print("=" * 80)
        
        print("\n📋 Summary by Category:")
        summary = result['summary']
        
        for category, subjects in summary.items():
            if subjects:
                print(f"\n{category.upper().replace('_', ' ')}: {len(subjects)} subjects")
                for subj in subjects:
                    priority = subj.get('priority_level', '?')
                    reason = subj.get('priority_reason', 'N/A')
                    print(f"  • {subj['subject_id']} - Priority {priority}: {reason}")
        
        # Validation
        print("\n✅ Validation:")
        print(f"  • Meets minimum credits: {result['meets_minimum']}")
        print(f"  • Total suggested credits: {result['total_credits']}/{result['max_credits_allowed']}")
        print(f"  • Number of subjects: {len(result['suggested_subjects'])}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 6: Test with custom max credits
    print("\n[Test 6] Custom Max Credits (15 TC)")
    print("-" * 80)
    try:
        result = engine.suggest_subjects(student_id, max_credits=15)
        print(f"Total suggested: {result['total_credits']} TC")
        print(f"Number of subjects: {len(result['suggested_subjects'])}")
        
        for i, subj in enumerate(result['suggested_subjects'], 1):
            print(f"  {i}. {subj['subject_id']} - {subj['subject_name']} ({subj['credits']} TC)")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 7: Rule-specific tests
    print("\n[Test 7] Individual Rule Testing")
    print("-" * 80)
    
    try:
        # Get data for testing
        student_data = engine.get_student_data(student_id)
        available_subjects = engine.get_available_subjects(student_id, current_semester)
        
        # Test Rule 1: Failed subjects
        failed, remaining = engine.rule_1_filter_failed_subjects(
            available_subjects, student_data
        )
        print(f"\nRule 1 - Failed subjects (F): {len(failed)} subjects")
        for subj in failed[:3]:
            print(f"  • {subj['subject_id']} - {subj['subject_name']}")
        
        # Test Rule 3: Political subjects
        political, remaining = engine.rule_3_filter_political_subjects(
            available_subjects, student_data
        )
        print(f"\nRule 3 - Political subjects: {len(political)} subjects")
        for subj in political[:3]:
            print(f"  • {subj['subject_id']} - {subj['subject_name']}")
        
        # Test Rule 4: Physical education
        pe, remaining = engine.rule_4_filter_physical_education(
            available_subjects, student_data
        )
        print(f"\nRule 4 - Physical education: {len(pe)} subjects (max 4)")
        for subj in pe[:3]:
            print(f"  • {subj['subject_id']} - {subj['subject_name']}")
        
        # Test Rule 5: Supplementary
        supp, remaining = engine.rule_5_filter_supplementary_subjects(
            available_subjects, student_data
        )
        print(f"\nRule 5 - Supplementary subjects: {len(supp)} subjects (max 3)")
        for subj in supp[:3]:
            print(f"  • {subj['subject_id']} - {subj['subject_name']}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    test_rule_engine()
