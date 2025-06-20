# backend/src/db_init.py
from models.core import create_db_and_tables
from dotenv import load_dotenv
 

if __name__ == "__main__":
    load_dotenv()
    create_db_and_tables()
    print("✅ Database tables created successfully!")