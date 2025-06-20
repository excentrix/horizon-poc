# # backend/src/db_init.py
# from models.core import create_db_and_tables
# from dotenv import load_dotenv

# if __name__ == "__main__":
#     load_dotenv()
#     create_db_and_tables()
#     print("✅ Database tables created successfully!")

# backend/scripts/clean_init_db.py (update with verification token fix)
# backend/scripts/clean_init_db.py (updated)
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
load_dotenv()

from models.core import engine
from sqlmodel import Session, text

def drop_all_tables():
    """Drop all existing tables."""
    print("🗑️ Dropping all existing tables...")
    
    drop_queries = [
        "DROP TABLE IF EXISTS fact_extractions CASCADE;",
        "DROP TABLE IF EXISTS chat_messages CASCADE;", 
        "DROP TABLE IF EXISTS chat_sessions CASCADE;",
        "DROP TABLE IF EXISTS tasks CASCADE;",
        "DROP TABLE IF EXISTS verification_tokens CASCADE;",
        "DROP TABLE IF EXISTS sessions CASCADE;",
        "DROP TABLE IF EXISTS accounts CASCADE;",
        "DROP TABLE IF EXISTS users CASCADE;",
    ]
    
    try:
        with Session(engine) as session:
            for query in drop_queries:
                session.exec(text(query))
            session.commit()
        print("✅ All tables dropped successfully")
    except Exception as e:
        print(f"⚠️ Error dropping tables (may not exist): {e}")

def main():
    """Clean initialization of database."""
    print("🗄️ Clean initializing Horizon database...")
    
    try:
        # Test database connection
        with Session(engine) as session:
            session.exec(text("SELECT 1"))
        print("✅ Database connection successful")
        
        # Drop existing tables
        drop_all_tables()
        
        # Import and run the schema creation
        from scripts.create_nextauth_tables import create_nextauth_tables, create_horizon_tables
        
        create_nextauth_tables()
        create_horizon_tables()
        
        print("✅ Clean database initialization complete!")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()