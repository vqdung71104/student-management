"""
Script to manually drop old tables that were removed from models
This handles foreign key constraints that prevent normal table dropping
"""
from sqlalchemy import create_engine, text
from app.core.config import settings

def drop_old_tables():
    """Drop old tables manually with proper foreign key handling"""
    engine = create_engine(settings.DATABASE_URL)
    
    # Tables to drop (order matters - drop dependent tables first)
    tables_to_drop = [
        'scholarship_applications',
        'scholarship_attachments', 
        'scholarships',
        'student_projects',
        'student_drl'
    ]
    
    print("🗑️  Dropping old tables...")
    
    with engine.connect() as conn:
        # Disable foreign key checks temporarily
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        conn.commit()
        
        for table in tables_to_drop:
            try:
                print(f"   Dropping table: {table}")
                conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
                conn.commit()
                print(f"   ✅ Dropped {table}")
            except Exception as e:
                print(f"   ⚠️  Could not drop {table}: {e}")
        
        # Re-enable foreign key checks
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        conn.commit()
        
    print("✅ Old tables cleanup completed!")

if __name__ == "__main__":
    drop_old_tables()
