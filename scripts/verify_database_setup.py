#!/usr/bin/env python3
"""
Database Setup Verification Script
Verifies PostgreSQL database is properly configured for Interview Co-Pilot
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_status(message, status="info"):
    """Print colored status message"""
    if status == "success":
        print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")
    elif status == "error":
        print(f"{Colors.RED}❌ {message}{Colors.RESET}")
    elif status == "warning":
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")
    elif status == "info":
        print(f"{Colors.BLUE}ℹ️  {message}{Colors.RESET}")
    else:
        print(f"{message}")

def parse_database_url(db_url: str):
    """Parse PostgreSQL connection URL"""
    # Format: postgresql://user:password@host:port/database
    try:
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "")
        
        if "@" in db_url:
            auth, rest = db_url.split("@", 1)
            if ":" in auth:
                user, password = auth.split(":", 1)
            else:
                user, password = auth, ""
        else:
            user, password = "postgres", ""
        
        if "/" in rest:
            host_port, database = rest.split("/", 1)
        else:
            host_port, database = rest, "postgres"
        
        if ":" in host_port:
            host, port = host_port.split(":", 1)
            port = int(port)
        else:
            host, port = host_port, 5432
        
        return {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password
        }
    except Exception as e:
        logger.error(f"Error parsing database URL: {e}")
        return None

def test_connection(conn_params):
    """Test database connection"""
    try:
        conn = psycopg2.connect(**conn_params)
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return False

def check_database_exists(conn_params, db_name):
    """Check if database exists"""
    try:
        # Connect to default postgres database to check
        check_params = conn_params.copy()
        check_params["database"] = "postgres"
        conn = psycopg2.connect(**check_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,)
        )
        exists = cursor.fetchone() is not None
        
        cursor.close()
        conn.close()
        return exists
    except Exception as e:
        logger.error(f"Error checking database: {e}")
        return False

def create_database(conn_params, db_name):
    """Create database if it doesn't exist"""
    try:
        check_params = conn_params.copy()
        check_params["database"] = "postgres"
        conn = psycopg2.connect(**check_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        cursor.execute(
            sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(db_name)
            )
        )
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        return False

def check_adk_tables(conn_params):
    """Check if ADK DatabaseSessionService tables exist"""
    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # ADK DatabaseSessionService typically creates tables automatically
        # But we can check for common table patterns
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return tables
    except Exception as e:
        logger.error(f"Error checking tables: {e}")
        return []

def verify_database_setup():
    """Main verification function"""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}PostgreSQL Database Setup Verification{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")
    
    # Get database URL from settings
    db_url = settings.DATABASE_URL
    print_status(f"Database URL: {db_url}", "info")
    
    # Parse connection parameters
    conn_params = parse_database_url(db_url)
    if not conn_params:
        print_status("Failed to parse database URL", "error")
        return False
    
    db_name = conn_params["database"]
    
    # Test connection to postgres database first
    print_status(f"\n[Step 1] Testing PostgreSQL Connection", "info")
    check_params = conn_params.copy()
    check_params["database"] = "postgres"
    
    if not test_connection(check_params):
        print_status("Cannot connect to PostgreSQL server", "error")
        print_status("Please ensure PostgreSQL is running and accessible", "warning")
        return False
    
    print_status("PostgreSQL server is accessible", "success")
    
    # Check if target database exists
    print_status(f"\n[Step 2] Checking Database: {db_name}", "info")
    if not check_database_exists(conn_params, db_name):
        print_status(f"Database '{db_name}' does not exist", "warning")
        response = input(f"Create database '{db_name}'? (y/n): ").strip().lower()
        if response == 'y':
            if create_database(conn_params, db_name):
                print_status(f"Database '{db_name}' created successfully", "success")
            else:
                print_status(f"Failed to create database '{db_name}'", "error")
                return False
        else:
            print_status("Database creation skipped", "warning")
            return False
    else:
        print_status(f"Database '{db_name}' exists", "success")
    
    # Test connection to target database
    print_status(f"\n[Step 3] Testing Connection to '{db_name}'", "info")
    if not test_connection(conn_params):
        print_status(f"Cannot connect to database '{db_name}'", "error")
        return False
    
    print_status(f"Successfully connected to '{db_name}'", "success")
    
    # Check existing tables
    print_status(f"\n[Step 4] Checking Database Tables", "info")
    tables = check_adk_tables(conn_params)
    
    if tables:
        print_status(f"Found {len(tables)} table(s):", "info")
        for table in tables:
            print(f"  - {table}")
    else:
        print_status("No tables found (this is normal for new database)", "info")
        print_status("ADK DatabaseSessionService will create tables automatically on first use", "info")
    
    # Check session storage configuration
    print_status(f"\n[Step 5] Checking Session Storage Configuration", "info")
    storage_type = settings.SESSION_STORAGE_TYPE
    print_status(f"Current SESSION_STORAGE_TYPE: {storage_type}", "info")
    
    if storage_type == "file":
        print_status("Using file-based session storage (not PostgreSQL)", "info")
        print_status("To use PostgreSQL for sessions, set SESSION_STORAGE_TYPE=database", "warning")
    elif storage_type == "database":
        print_status("PostgreSQL session storage is configured", "success")
        print_status("ADK DatabaseSessionService will use PostgreSQL for sessions", "info")
    else:
        print_status(f"Unknown storage type: {storage_type}", "warning")
    
    # Summary
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}Summary{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")
    
    print_status("PostgreSQL database is properly configured", "success")
    print_status(f"Database: {db_name}", "info")
    print_status(f"Host: {conn_params['host']}:{conn_params['port']}", "info")
    print_status(f"User: {conn_params['user']}", "info")
    
    if storage_type != "database":
        print_status("\nNote: To enable PostgreSQL session storage:", "info")
        print_status("  1. Set SESSION_STORAGE_TYPE=database in .env", "info")
        print_status("  2. Set SESSION_STORAGE_PATH to your DATABASE_URL", "info")
        print_status("  3. Restart the application", "info")
    
    return True

if __name__ == "__main__":
    try:
        success = verify_database_setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_status("\n\nVerification cancelled by user", "warning")
        sys.exit(1)
    except Exception as e:
        print_status(f"\nUnexpected error: {e}", "error")
        import traceback
        traceback.print_exc()
        sys.exit(1)

