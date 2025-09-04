#!/usr/bin/env python3
"""
Script to recreate all database tables
"""

from app.db.database import Base, engine
from app.models import *  # Import all models

def recreate_tables():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    
    print("Tables recreated successfully!")

if __name__ == "__main__":
    recreate_tables()
