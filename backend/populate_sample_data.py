import json
import sys
import os
from sqlalchemy.orm import Session

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal, engine
from app.models.feedback_model import FAQ, Feedback, FeedbackStatus, FeedbackSubject
from app.db import database

def load_json_data(file_path):
    """Load data from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSON decode error in {file_path}: {e}")
        return []

def populate_faqs():
    """Populate FAQ table with sample data"""
    db = SessionLocal()
    try:
        # Check if FAQs already exist
        existing_faqs = db.query(FAQ).count()
        if existing_faqs > 0:
            print(f"FAQs table already has {existing_faqs} records. Skipping FAQ population.")
            return

        # Load sample FAQ data
        faq_data = load_json_data('data/sample_faqs.json')
        
        if not faq_data:
            print("No FAQ data to populate.")
            return

        # Insert FAQs
        for faq_item in faq_data:
            faq = FAQ(
                question=faq_item['question'],
                answer=faq_item['answer'],
                is_active=faq_item.get('is_active', True),
                order_index=faq_item.get('order_index', 0)
            )
            db.add(faq)

        db.commit()
        print(f"Successfully populated {len(faq_data)} FAQs.")

    except Exception as e:
        print(f"Error populating FAQs: {e}")
        db.rollback()
    finally:
        db.close()

def populate_feedbacks():
    """Populate Feedback table with sample data"""
    db = SessionLocal()
    try:
        # Check if Feedbacks already exist
        existing_feedbacks = db.query(Feedback).count()
        if existing_feedbacks > 0:
            print(f"Feedbacks table already has {existing_feedbacks} records. Skipping Feedback population.")
            return

        # Load sample feedback data
        feedback_data = load_json_data('data/sample_feedbacks.json')
        
        if not feedback_data:
            print("No feedback data to populate.")
            return

        # Insert Feedbacks
        for feedback_item in feedback_data:
            # Convert string enums to actual enum values
            subject_enum = FeedbackSubject(feedback_item['subject'])
            status_enum = FeedbackStatus(feedback_item.get('status', 'pending'))
            
            feedback = Feedback(
                email=feedback_item['email'],
                subject=subject_enum,
                feedback=feedback_item['feedback'],
                suggestions=feedback_item.get('suggestions'),
                status=status_enum
            )
            db.add(feedback)

        db.commit()
        print(f"Successfully populated {len(feedback_data)} feedbacks.")

    except Exception as e:
        print(f"Error populating feedbacks: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Main function to populate all sample data"""
    print("Starting database population with sample data...")
    
    # Create tables if they don't exist
    database.Base.metadata.create_all(bind=engine)
    print("Database tables ensured.")
    
    # Populate data
    populate_faqs()
    populate_feedbacks()
    
    print("Database population completed!")

if __name__ == "__main__":
    main()