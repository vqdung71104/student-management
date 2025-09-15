import json
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SQLALCHEMY_DATABASE_URL, Base
from app.models.department_model import Department
from app.models.subject_model import Subject
from app.models.course_model import Course
from app.models.student_model import Student
from app.models.class_model import Class
from app.models.feedback_model import FAQ, Feedback

def create_database_session():
    """Create database session"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def load_sample_data():
    """Load sample data from JSON file"""
    try:
        with open('data/sample_data.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print("Error: sample_data.json file not found!")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None

def populate_departments(db, departments_data):
    """Populate departments table"""
    print("📁 Populating departments...")
    for dept_data in departments_data:
        try:
            dept = Department(**dept_data)
            db.add(dept)
        except Exception as e:
            print(f"Error adding department {dept_data.get('department_id', '')}: {e}")
    
    try:
        db.commit()
        print(f"✅ Added {len(departments_data)} departments")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"❌ Error committing departments: {e}")

def populate_subjects(db, subjects_data):
    """Populate subjects table"""
    print("📚 Populating subjects...")
    for subject_data in subjects_data:
        try:
            subject = Subject(**subject_data)
            db.add(subject)
        except Exception as e:
            print(f"Error adding subject {subject_data.get('subject_id', '')}: {e}")
    
    try:
        db.commit()
        print(f"✅ Added {len(subjects_data)} subjects")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"❌ Error committing subjects: {e}")

def populate_courses(db, courses_data):
    """Populate courses table"""
    print("🎓 Populating courses...")
    for course_data in courses_data:
        try:
            course = Course(**course_data)
            db.add(course)
        except Exception as e:
            print(f"Error adding course {course_data.get('course_id', '')}: {e}")
    
    try:
        db.commit()
        print(f"✅ Added {len(courses_data)} courses")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"❌ Error committing courses: {e}")

def populate_students(db, students_data):
    """Populate students table"""
    print("👨‍🎓 Populating students...")
    for student_data in students_data:
        try:
            student = Student(**student_data)
            db.add(student)
        except Exception as e:
            print(f"Error adding student {student_data.get('student_id', '')}: {e}")
    
    try:
        db.commit()
        print(f"✅ Added {len(students_data)} students")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"❌ Error committing students: {e}")

def populate_classes(db, classes_data):
    """Populate classes table"""
    print("🏫 Populating classes...")
    for class_data in classes_data:
        try:
            cls = Class(**class_data)
            db.add(cls)
        except Exception as e:
            print(f"Error adding class {class_data.get('class_id', '')}: {e}")
    
    try:
        db.commit()
        print(f"✅ Added {len(classes_data)} classes")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"❌ Error committing classes: {e}")

def populate_faqs(db, faqs_data):
    """Populate FAQs table"""
    print("❓ Populating FAQs...")
    for faq_data in faqs_data:
        try:
            faq = FAQ(**faq_data)
            db.add(faq)
        except Exception as e:
            print(f"Error adding FAQ: {e}")
    
    try:
        db.commit()
        print(f"✅ Added {len(faqs_data)} FAQs")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"❌ Error committing FAQs: {e}")

def populate_feedbacks(db, feedbacks_data):
    """Populate feedbacks table"""
    print("💬 Populating feedbacks...")
    for feedback_data in feedbacks_data:
        try:
            feedback = Feedback(**feedback_data)
            db.add(feedback)
        except Exception as e:
            print(f"Error adding feedback: {e}")
    
    try:
        db.commit()
        print(f"✅ Added {len(feedbacks_data)} feedbacks")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"❌ Error committing feedbacks: {e}")

def main():
    """Main function to populate all data"""
    print("🚀 Starting data population...")
    print("=" * 50)
    
    # Load sample data
    sample_data = load_sample_data()
    if not sample_data:
        return
    
    # Create database session
    try:
        db = create_database_session()
        print("✅ Database connection established")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return
    
    try:
        # Populate data in correct order (respecting foreign key dependencies)
        
        # 1. Departments (no dependencies)
        if 'departments' in sample_data:
            populate_departments(db, sample_data['departments'])
        
        # 2. Subjects (no dependencies)
        if 'subjects' in sample_data:
            populate_subjects(db, sample_data['subjects'])
        
        # 3. Courses (depends on departments)
        if 'courses' in sample_data:
            populate_courses(db, sample_data['courses'])
        
        # 4. Students (depends on courses)
        if 'students' in sample_data:
            populate_students(db, sample_data['students'])
        
        # 5. Classes (depends on subjects)
        if 'classes' in sample_data:
            populate_classes(db, sample_data['classes'])
        
        # 6. FAQs (no dependencies)
        if 'faqs' in sample_data:
            populate_faqs(db, sample_data['faqs'])
        
        # 7. Feedbacks (no dependencies)
        if 'feedbacks' in sample_data:
            populate_feedbacks(db, sample_data['feedbacks'])
        
        print("=" * 50)
        print("🎉 Data population completed successfully!")
        
    except Exception as e:
        print(f"❌ Unexpected error during population: {e}")
    finally:
        db.close()
        print("🔒 Database connection closed")

if __name__ == "__main__":
    main()