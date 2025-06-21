"""
Database connection and initialization for Charlie AI Assistant
"""

import logging
from typing import Optional

from supabase import create_client, Client
from app.core.config import settings
from postgrest.exceptions import APIError

logger = logging.getLogger(__name__)

# Global Supabase client
supabase: Optional[Client] = None


def get_supabase_client() -> Client:
    """Get Supabase client instance"""
    global supabase
    if supabase is None:
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return supabase


def get_supabase_admin_client() -> Client:
    """Get Supabase admin client with service role key"""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


async def init_db():
    """Initialize database connection and create tables if needed"""
    try:
        client = get_supabase_client()
        
        # Test connection
        try:
            response = client.table("users").select("id").limit(1).execute()
            logger.info("Database connection successful")
        except APIError as e:
            if "relation" in str(e) and "does not exist" in str(e):
                logger.info("Database tables don't exist, creating schema...")
                await create_database_schema()
            else:
                # Different database error
                raise
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            
            # If we're in development mode, create schema and proceed
            if settings.DEBUG:
                logger.info("Running in debug mode, attempting to create schema...")
                try:
                    await create_database_schema()
                    logger.info("Schema created successfully in development mode")
                except Exception as schema_error:
                    logger.error(f"Schema creation failed: {schema_error}")
            else:
                raise
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        if settings.DEBUG:
            logger.warning("Running in DEBUG mode without database - some features may not work")
        else:
            raise


async def create_database_schema():
    """Create database schema using Supabase admin client"""
    client = get_supabase_admin_client()
    
    # SQL for creating tables - these would normally be run as migrations
    sql_commands = [
        """
        -- Enable UUID extension if not already enabled
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        """,
        
        """
        -- Create users table
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            email VARCHAR UNIQUE NOT NULL,
            full_name VARCHAR,
            preferences JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        
        """
        -- Create conversations table
        CREATE TABLE IF NOT EXISTS conversations (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            session_id VARCHAR,
            user_input TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            context JSONB DEFAULT '{}',
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        
        """
        -- Create memories table
        CREATE TABLE IF NOT EXISTS memories (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            memory_type VARCHAR NOT NULL,
            content TEXT NOT NULL,
            importance INTEGER DEFAULT 1,
            tags TEXT[] DEFAULT '{}',
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        
        """
        -- Create task_logs table
        CREATE TABLE IF NOT EXISTS task_logs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            task_type VARCHAR NOT NULL,
            task_params JSONB NOT NULL,
            status VARCHAR NOT NULL,
            result JSONB,
            error_message TEXT,
            started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            completed_at TIMESTAMP WITH TIME ZONE
        );
        """,
        
        """
        -- Create indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
        CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);
        CREATE INDEX IF NOT EXISTS idx_memories_user_id ON memories(user_id);
        CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type);
        CREATE INDEX IF NOT EXISTS idx_task_logs_user_id ON task_logs(user_id);
        CREATE INDEX IF NOT EXISTS idx_task_logs_status ON task_logs(status);
        """,
        
        """
        -- Enable Row Level Security
        ALTER TABLE users ENABLE ROW LEVEL SECURITY;
        ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
        ALTER TABLE memories ENABLE ROW LEVEL SECURITY;
        ALTER TABLE task_logs ENABLE ROW LEVEL SECURITY;
        """,
        
        """
        -- Create RLS policies
        CREATE POLICY users_policy ON users 
            FOR ALL 
            USING (auth.uid() = id);
            
        CREATE POLICY conversations_policy ON conversations 
            FOR ALL 
            USING (auth.uid() = user_id);
            
        CREATE POLICY memories_policy ON memories 
            FOR ALL 
            USING (auth.uid() = user_id);
            
        CREATE POLICY task_logs_policy ON task_logs 
            FOR ALL 
            USING (auth.uid() = user_id);
        """
    ]
    
    for sql in sql_commands:
        try:
            client.rpc('execute_sql', {'sql': sql}).execute()
            logger.info("Executed SQL command successfully")
        except Exception as e:
            logger.warning(f"SQL command failed (may already exist): {e}") 