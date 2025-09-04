#from sqlalchemy import create_engine
#from sqlalchemy.ext.declarative import declarative_base
#from sqlalchemy.orm import sessionmaker
#from app.core.config import settings

#engine = create_engine(settings.DATABASE_URL)
#SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#Base = declarative_base()


#def get_db():
#    db = SessionLocal()
#   try: 
#        yield db
#    finally:
#       db.close() 




# backend/app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Use the DATABASE_URL from settings which handles URL encoding
DATABASE_URL = settings.DATABASE_URL

# Engine và Session
engine = create_engine(DATABASE_URL, echo=False, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

## Base cho models
Base = declarative_base()

## Dependency cho FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
