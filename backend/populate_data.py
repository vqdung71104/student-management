import json
import sys
import os
import unicodedata
import hashlib
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.db.database import DATABASE_URL, Base, SessionLocal
from app.models.department_model import Department
from app.models.subject_model import Subject
from app.models.course_model import Course
from app.models.course_subject_model import CourseSubject
from app.models.student_model import Student
from app.models.feedback_model import FAQ, Feedback
from app.models.learned_subject_model import LearnedSubject
from app.models.notification_model import Notification
from app.models.admin_model import Admin

def create_database_session():
    """Create database session"""
    # Engine đã tạo sẵn trong database.py
    from app.db.database import engine, SessionLocal
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def clear_all_data(db):
    """Clear all data from tables (in correct order to respect foreign keys)"""
    print("🗑️ Clearing existing data...")
    try:
        from sqlalchemy import text
        # Delete in reverse order of dependencies to avoid foreign key constraints
        # First, delete tables that reference others
        db.execute(text("SET FOREIGN_KEY_CHECKS = 0"))  # Temporarily disable foreign key checks
        
        # Clear all tables
        db.execute(text("DELETE FROM otp_verifications"))
        db.execute(text("DELETE FROM admins"))
        db.execute(text("DELETE FROM notifications"))
        db.execute(text("DELETE FROM feedbacks"))
        db.execute(text("DELETE FROM faqs"))
        db.execute(text("DELETE FROM class_registers"))
        db.execute(text("DELETE FROM subject_registers"))
        db.execute(text("DELETE FROM learned_subjects"))
        db.execute(text("DELETE FROM semester_gpa"))
        db.execute(text("DELETE FROM classes"))
        db.execute(text("DELETE FROM students"))
        db.execute(text("DELETE FROM course_subjects"))
        db.execute(text("DELETE FROM courses"))
        db.execute(text("DELETE FROM subjects"))
        db.execute(text("DELETE FROM departments"))
        
        # Reset auto-increment counters
        db.execute(text("ALTER TABLE otp_verifications AUTO_INCREMENT = 1"))
        db.execute(text("ALTER TABLE admins AUTO_INCREMENT = 1"))
        db.execute(text("ALTER TABLE notifications AUTO_INCREMENT = 1"))
        db.execute(text("ALTER TABLE departments AUTO_INCREMENT = 1"))
        db.execute(text("ALTER TABLE subjects AUTO_INCREMENT = 1"))
        db.execute(text("ALTER TABLE courses AUTO_INCREMENT = 1"))
        db.execute(text("ALTER TABLE students AUTO_INCREMENT = 1"))
        db.execute(text("ALTER TABLE classes AUTO_INCREMENT = 1"))
        db.execute(text("ALTER TABLE faqs AUTO_INCREMENT = 1"))
        db.execute(text("ALTER TABLE feedbacks AUTO_INCREMENT = 1"))
        
        db.execute(text("SET FOREIGN_KEY_CHECKS = 1"))  # Re-enable foreign key checks
        db.commit()
        print("✅ All data cleared successfully")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"❌ Error clearing data: {e}")

def generate_email(student_name: str, student_id: str) -> str:
    """Tạo email từ tên + MSSV"""
    def remove_accents(text: str) -> str:
        return ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
    
    unaccented_name = remove_accents(student_name.strip())
    name_parts = unaccented_name.split()
    last_name = name_parts[-1].lower()
    initials = "".join([w[0].lower() for w in name_parts[:-1]])
    mssv_suffix = student_id[2:]  # bỏ 2 số đầu
    return f"{last_name}.{initials}{mssv_suffix}@sis.hust.edu.vn"

def calculate_letter_grade(score: float) -> str:
    """Tính letter grade từ điểm số"""
    if 0.0 <= score <= 3.9:
        return "F"
    elif 4.0 <= score <= 4.9:
        return "D"
    elif 5.0 <= score <= 5.4:
        return "D+"
    elif 5.5 <= score <= 6.4:
        return "C"
    elif 6.5 <= score <= 6.9:
        return "C+"
    elif 7.0 <= score <= 7.9:
        return "B"
    elif 8.0 <= score <= 8.4:
        return "B+"
    elif 8.5 <= score <= 9.4:
        return "A"
    elif 9.5 <= score <= 10.0:
        return "A+"
    return "F"

def calculate_total_score(midterm_score: float, final_score: float, weight: float) -> float:
    """Tính điểm tổng kết: midterm * (1-weight) + final * weight"""
    return midterm_score * (1 - weight) + final_score * weight

def load_json_file(filename):
    """Load data from a specific JSON file"""
    try:
        with open(f'data/{filename}', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: {filename} file not found!")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON in {filename}: {e}")
        return None

def populate_departments(db, departments_data):
    """Populate departments table"""
    print("📁 Populating departments...")
    for dept_data in departments_data:
        try:
            # Map JSON fields to model fields (already correct format)
            dept = Department(
                id=dept_data.get('id'),
                name=dept_data.get('name')
            )
            db.add(dept)
        except Exception as e:
            print(f"Error adding department {dept_data.get('id', '')}: {e}")
    
    try:
        db.commit()
        print(f"✅ Added {len(departments_data)} departments")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"❌ Error committing departments: {e}")

def populate_subjects(db, subjects_data):
    """Populate subjects table"""
    print("📚 Populating subjects...")
    seen_subject_ids = set()  # Track subject_ids to avoid duplicates in JSON
    
    for subject_data in subjects_data:
        try:
            subject_id = subject_data.get('subject_id')
            
            # Skip if we've already seen this subject_id in current batch
            if subject_id in seen_subject_ids:
                print(f"Duplicate subject_id {subject_id} found in JSON, skipping...")
                continue
            seen_subject_ids.add(subject_id)
            
            # Check if subject already exists in database
            existing = db.query(Subject).filter(Subject.subject_id == subject_id).first()
            if existing:
                print(f"Subject {subject_id} already exists in database, skipping...")
                continue
                
            # Map JSON fields to model fields (already correct format)
            subject = Subject(
                subject_id=subject_id,
                subject_name=subject_data.get('subject_name'),
                credits=subject_data.get('credits'),
                duration=subject_data.get('duration') or '',  # Convert None to empty string
                tuition_fee=int(float(subject_data.get('tuition_fee', 0))),
                english_subject_name=subject_data.get('english_subject_name', ''),
                weight=subject_data.get('weight'),
                conditional_subjects=subject_data.get('conditional_subjects'),
                department_id=subject_data.get('department_id')
            )
            db.add(subject)
        except Exception as e:
            print(f"Error adding subject {subject_data.get('subject_id', '')}: {e}")
    
    try:
        db.commit()
        print(f"✅ Added {len(seen_subject_ids)} unique subjects")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"❌ Error committing subjects: {e}")

def populate_courses(db, courses_data):
    """Populate courses table"""
    print("🎓 Populating courses...")
    for course_data in courses_data:
        try:
            # Map JSON fields to model fields
            course = Course(
                course_id=course_data.get('course_id'),
                course_name=course_data.get('course_name')
            )
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
            # Generate email from student_name and student_id using proper format
            student_id = student_data.get('student_id')
            student_name = student_data.get('student_name')
            email = generate_email(student_name, student_id)
            
            # Find the course by course_id string (not by auto-increment id)
            json_course_id = student_data.get('course_id')
            course = db.query(Course).filter(Course.course_id == json_course_id).first()
            if not course:
                print(f"Course with course_id '{json_course_id}' not found, skipping student {student_id}")
                continue
            
            # Map learning_status to match schema validation
            learning_status = student_data.get('learning_status', 'Đang học')
            if learning_status == 'Tốt nghiệp':
                learning_status = 'Đang học'  # Map "Tốt nghiệp" to "Đang học" since schema doesn't allow "Tốt nghiệp"
            
            # Map JSON fields to model fields (already correct format)
            student = Student(
                student_id=student_id,
                student_name=student_data.get('student_name'),
                course_id=course.id,  # Use the auto-increment id from database
                enrolled_year=student_data.get('enrolled_year'),
                training_level=student_data.get('training_level'),
                learning_status=learning_status,
                gender=student_data.get('gender'),
                classes=student_data.get('classes', ''),
                email=email,  # Auto-generated email
                login_password='e10adc3949ba59abbe56e057f20f883e',  # Default password hash
                newest_semester=student_data.get('newest_semester'),
                cpa=student_data.get('cpa', 0.0),
                failed_subjects_number=student_data.get('failed_subjects_number', 0),
                study_subjects_number=student_data.get('study_subjects_number', 0),
                total_learned_credits=student_data.get('total_learned_credits', 0),
                total_failed_credits=student_data.get('total_failed_credits', 0),
                year_level=student_data.get('year_level', 'Trình độ năm 1'),
                warning_level=student_data.get('warning_level', 'Cảnh cáo mức 0'),
                level_3_warning_number=student_data.get('level_3_warning_number', 0),
                department_id=student_data.get('department_id')
            )
            db.add(student)
        except Exception as e:
            print(f"Error adding student {student_data.get('student_id', '')}: {e}")
    
    try:
        db.commit()
        print(f"✅ Added {len(students_data)} students")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"❌ Error committing students: {e}")

def populate_course_subjects(db, courses_data):
    """Create course_subjects relationships from JSON data (following route logic)"""
    print("🔗 Creating course-subject relationships...")
    course_subject_count = 0
    
    for course_data in courses_data:
        try:
            course_id_str = course_data.get("course_id")
            subjects = course_data.get("subjects", [])
            
            # Find the course in database (like in route)
            course = db.query(Course).filter(Course.course_id == course_id_str).first()
            if not course:
                print(f"Course {course_id_str} not found in database, skipping...")
                continue
            
            # For each subject in JSON, create course_subject relationship (following route pattern)
            for subj in subjects:
                subj_id_str = subj.get("subject_id")
                learning_semester = subj.get("learning_semester", 1)  # Default semester 1 (like in route)
                
                # Find subject in database (like in route)
                subject = db.query(Subject).filter(Subject.subject_id == subj_id_str).first()
                if not subject:
                    print(f"Subject with subject_id '{subj_id_str}' not found, skipping...")
                    continue
                
                # Check if relationship already exists
                existing = db.query(CourseSubject).filter(
                    CourseSubject.course_id == course.id,
                    CourseSubject.subject_id == subject.id
                ).first()
                
                if not existing:
                    # Create new course_subject relationship (exactly like in route)
                    db_course_subject = CourseSubject(
                        course_id=course.id,   # int PK
                        subject_id=subject.id,    # int PK
                        learning_semester=learning_semester  # Add learning_semester
                    )
                    db.add(db_course_subject)
                    course_subject_count += 1
                else:
                    print(f"Course-Subject relationship already exists: {course_id_str} - {subj_id_str}")
                    
        except Exception as e:
            print(f"Error adding course_subjects for course {course_data.get('course_id', 'unknown')}: {e}")
    
    try:
        db.commit()
        print(f"✅ Added {course_subject_count} course-subject relationships")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"❌ Error committing course-subject relationships: {e}")

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

def populate_notifications(db, notifications_data):
    """Populate notifications table"""
    print("🔔 Populating notifications...")
    for notification_data in notifications_data:
        try:
            notification = Notification(**notification_data)
            db.add(notification)
        except Exception as e:
            print(f"Error adding notification: {e}")
    
    try:
        db.commit()
        print(f"✅ Added {len(notifications_data)} notifications")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"❌ Error committing notifications: {e}")

def populate_learned_subjects(db, learned_subjects_data):
    """Populate learned subjects table"""
    print("📚 Populating learned subjects...")
    try:
        for learned_data in learned_subjects_data:
            # Tính total score và letter grade
            total_score = calculate_total_score(
                learned_data['midterm_score'],
                learned_data['final_score'], 
                learned_data['weight']
            )
            letter_grade = calculate_letter_grade(total_score)
            
            # Lấy thông tin subject để có subject_name và credits
            subject = db.query(Subject).filter(Subject.id == learned_data['subject_id']).first()
            if not subject:
                print(f"⚠️ Subject with ID {learned_data['subject_id']} not found")
                continue
                
            learned_subject = LearnedSubject(
                final_score=learned_data['final_score'],
                midterm_score=learned_data['midterm_score'],
                weight=learned_data['weight'],
                total_score=total_score,
                letter_grade=letter_grade,
                semester=learned_data['semester'],
                student_id=learned_data['student_id'],
                subject_id=learned_data['subject_id'],
                subject_name=subject.subject_name,
                credits=subject.credits
            )
            db.add(learned_subject)
        
        db.commit()
        print(f"✅ Successfully populated {len(learned_subjects_data)} learned subjects")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"❌ Error committing learned subjects: {e}")


def populate_admin(db):
    """Populate admin user with secure password"""
    print("👤 Populating admin...")
    
    try:
        # Check if admin already exists
        existing_admin = db.query(Admin).filter(Admin.username == "admin").first()
        if existing_admin:
            print("ℹ️ Admin already exists, skipping...")
            return
        
        # Hash password using SHA256
        password = "Admin123!"  # Strong default password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        admin = Admin(
            username="admin",
            email="vuquangdung71104@gmail.com",
            password_hash=password_hash,
            password_updated_at=datetime.now(),
            is_active="active"
        )
        
        db.add(admin)
        db.commit()
        
        print("✅ Admin user created successfully")
        print(f"   📧 Email: vuquangdung71104@gmail.com")
        print(f"   🔑 Password: {password}")
        print("   ⚠️ Please change the password after first login!")
        
    except SQLAlchemyError as e:
        db.rollback()
        print(f"❌ Error creating admin: {e}")


def main():
    """Main function to populate all data"""
    print("🚀 Starting data population...")
    print("=" * 50)
    
    # Create database session
    try:
        db = create_database_session()
        print("✅ Database connection established")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return
    
    # Clear existing data first
    clear_all_data(db)
    
    try:
        # Populate data in correct order (respecting foreign key dependencies)
        
        # 0. Admin user (no dependencies)
        populate_admin(db)
        
        # 1. Departments (no dependencies)
        departments_data = load_json_file('sample_department.json')
        if departments_data:
            populate_departments(db, departments_data)
        
        # 2. Subjects (depends on departments)
        subjects_data = load_json_file('sample_subject.json')
        if subjects_data:
            populate_subjects(db, subjects_data)
        
        # 3. Courses (no dependencies in current model)
        courses_data = load_json_file('sample_courses.json')
        if courses_data:
            populate_courses(db, courses_data)
        
        # 3.5. Course-Subject relationships (depends on courses and subjects)
        populate_course_subjects(db, courses_data)
        
        # 4. Students (depends on courses)
        students_data = load_json_file('sample_student.json')
        if students_data:
            populate_students(db, students_data)
        
        # 5. Learned subjects (depends on students and subjects)
        learned_subjects_data = load_json_file('sample_learned_subjects.json')
        if learned_subjects_data:
            populate_learned_subjects(db, learned_subjects_data)
        
        # 6. FAQs (no dependencies)
        faqs_data = load_json_file('sample_faqs.json')
        if faqs_data:
            populate_faqs(db, faqs_data)
        
        # 7. Feedbacks (no dependencies)
        feedbacks_data = load_json_file('sample_feedbacks.json')
        if feedbacks_data:
            populate_feedbacks(db, feedbacks_data)
        
        # 8. Notifications (no dependencies)
        notifications_data = load_json_file('sample_notifications.json')
        if notifications_data:
            populate_notifications(db, notifications_data)
        
        print("=" * 50)
        print("🎉 Data population completed successfully!")
        
    except Exception as e:
        print(f"❌ Unexpected error during population: {e}")
    finally:
        db.close()
        print("🔒 Database connection closed")

if __name__ == "__main__":
    main()