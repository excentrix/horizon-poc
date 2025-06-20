# backend/scripts/create_nextauth_tables.py
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from models.core import engine
from sqlmodel import Session, text

def create_nextauth_tables():
    """Create NextAuth tables with proper schema."""
    print("🔧 Creating NextAuth tables with proper ID generation...")
    
    # NextAuth expects these specific table structures
    nextauth_tables = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            name TEXT,
            email TEXT UNIQUE NOT NULL,
            "emailVerified" TIMESTAMP,
            image TEXT,
            degree TEXT,
            year INTEGER,
            goal TEXT,
            biggest_worry TEXT,
            fav_subject TEXT,
            skills TEXT,
            gpa REAL,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS accounts (
            id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            "userId" TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            type TEXT NOT NULL,
            provider TEXT NOT NULL,
            "providerAccountId" TEXT NOT NULL,
            refresh_token TEXT,
            access_token TEXT,
            expires_at INTEGER,
            token_type TEXT,
            scope TEXT,
            id_token TEXT,
            session_state TEXT,
            UNIQUE(provider, "providerAccountId")
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            "sessionToken" TEXT UNIQUE NOT NULL,
            "userId" TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            expires TIMESTAMP NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS verification_tokens (
            identifier TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires TIMESTAMP NOT NULL,
            PRIMARY KEY (identifier, token)
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS accounts_user_id_idx ON accounts("userId");
        CREATE INDEX IF NOT EXISTS sessions_user_id_idx ON sessions("userId");
        CREATE INDEX IF NOT EXISTS users_email_idx ON users(email);
        """
    ]
    
    try:
        with Session(engine) as session:
            for table_sql in nextauth_tables:
                session.exec(text(table_sql))
            session.commit()
        print("✅ NextAuth tables created successfully")
    except Exception as e:
        print(f"❌ Error creating NextAuth tables: {e}")
        raise

def create_horizon_tables():
    """Create our custom Horizon tables."""
    print("🔧 Creating Horizon tables...")
    
    horizon_tables = [
        """
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT DEFAULT 'New Conversation',
            summary TEXT,
            context TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            session_id TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
            content TEXT NOT NULL,
            is_user BOOLEAN DEFAULT TRUE,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            description TEXT,
            due_date TIMESTAMP,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            tags TEXT,
            created_by_ai BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW(),
            completed_at TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS fact_extractions (
            id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            session_id TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
            facts TEXT NOT NULL,
            confidence REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS chat_sessions_user_id_idx ON chat_sessions(user_id);
        CREATE INDEX IF NOT EXISTS chat_messages_session_id_idx ON chat_messages(session_id);
        CREATE INDEX IF NOT EXISTS tasks_user_id_idx ON tasks(user_id);
        CREATE INDEX IF NOT EXISTS fact_extractions_user_id_idx ON fact_extractions(user_id);
        """
    ]
    
    try:
        with Session(engine) as session:
            for table_sql in horizon_tables:
                session.exec(text(table_sql))
            session.commit()
        print("✅ Horizon tables created successfully")
    except Exception as e:
        print(f"❌ Error creating Horizon tables: {e}")
        raise

def main():
    """Create all tables with proper schema."""
    print("🗄️ Creating database schema for NextAuth + Horizon...")
    
    try:
        # Test database connection
        with Session(engine) as session:
            session.exec(text("SELECT 1"))
        print("✅ Database connection successful")
        
        # Create NextAuth tables first
        create_nextauth_tables()
        
        # Create Horizon tables
        create_horizon_tables()
        
        # Verify tables were created
        with Session(engine) as session:
            result = session.exec(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """))
            tables = result.all()
            print(f"📋 Created tables: {', '.join([table[0] for table in tables])}")
        
        print("✅ Database schema creation complete!")
        
    except Exception as e:
        print(f"❌ Database schema creation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()