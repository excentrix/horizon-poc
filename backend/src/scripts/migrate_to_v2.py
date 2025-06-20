# backend/scripts/migrate_to_v2.py
import sys
import os

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if os.path.exists(src_path) and os.path.isdir(src_path):
    sys.path.append(src_path)
else:
    print(f"❌ Error: The directory '{src_path}' does not exist or is not a valid directory.")
    sys.exit(1)

from models.core import engine 
from models.enhanced_models import ConversationMemory, SessionSummary, ProcessingJob
from sqlmodel import Session, text, SQLModel

def create_enhanced_tables():
    """Create new tables for enhanced system."""
    print("🔧 Creating enhanced system tables...")
    
    try:
        # Create pgvector extension if not exists
        with Session(engine) as session:
            session.exec(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            session.commit()
        
        # Create new tables
        SQLModel.metadata.create_all(engine)
        
        print("✅ Enhanced tables created successfully:")
        print("  - conversation_memories (with vector embeddings)")
        print("  - session_summaries")
        print("  - processing_jobs")
        
    except Exception as e:
        print(f"❌ Error creating enhanced tables: {e}")
        raise

def verify_tables():
    """Verify all tables exist."""
    with Session(engine) as session:
        result = session.exec(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result.all()]
        
        print(f"📋 Current tables: {', '.join(tables)}")
        
        required_tables = [
            'users', 'accounts', 'sessions', 'verification_tokens',
            'chat_sessions', 'chat_messages', 'tasks', 'fact_extractions',
            'conversation_memories', 'session_summaries', 'processing_jobs'
        ]
        
        missing_tables = [table for table in required_tables if table not in tables]
        if missing_tables:
            print(f"❌ Missing tables: {', '.join(missing_tables)}")
        else:
            print("✅ All required tables present")

def main():
    """Main migration function."""
    print("🚀 Starting v2 system migration...")
    
    try:
        create_enhanced_tables()
        verify_tables()
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()