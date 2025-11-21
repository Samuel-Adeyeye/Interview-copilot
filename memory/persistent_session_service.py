"""
Persistent Session Service with file-based and SQLite support
Provides session persistence across server restarts
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import json
import os
import sqlite3
import threading
import logging
from pathlib import Path
from .session_service import SessionState, InMemorySessionService

logger = logging.getLogger(__name__)


class PersistentSessionService(InMemorySessionService):
    """
    Session service with persistence support.
    Extends InMemorySessionService with file-based or SQLite persistence.
    """
    
    def __init__(
        self,
        storage_type: str = "file",
        storage_path: str = "./data/sessions",
        expiration_hours: int = 168,
        auto_save: bool = True
    ):
        """
        Initialize persistent session service
        
        Args:
            storage_type: "file" for JSON files, "sqlite" for SQLite database
            storage_path: Path to storage directory or SQLite file
            expiration_hours: Hours before sessions expire (default 7 days)
            auto_save: Automatically save on every update
        """
        super().__init__()
        self.storage_type = storage_type
        self.storage_path = Path(storage_path)
        self.expiration_hours = expiration_hours
        self.auto_save = auto_save
        self._lock = threading.Lock()
        
        # Ensure storage directory exists
        if storage_type == "file":
            self.storage_path.mkdir(parents=True, exist_ok=True)
            self.sessions_file = self.storage_path / "sessions.json"
        elif storage_type == "sqlite":
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.db_path = self.storage_path if storage_path.endswith(".db") else self.storage_path / "sessions.db"
            self._init_sqlite_db()
        else:
            raise ValueError(f"Unsupported storage_type: {storage_type}. Use 'file' or 'sqlite'")
        
        # Load existing sessions
        self._load_sessions()
        
        # Cleanup expired sessions on startup
        self.cleanup_expired_sessions(self.expiration_hours)
        
        logger.info(f"Initialized {storage_type} persistent session service with {len(self.sessions)} sessions")
    
    def _init_sqlite_db(self):
        """Initialize SQLite database schema"""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                state TEXT NOT NULL,
                agent_states TEXT,
                artifacts TEXT,
                checkpoints TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT
            )
        """)
        
        # Create index for faster user queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_id ON sessions(user_id)
        """)
        
        # Create index for faster state queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_state ON sessions(state)
        """)
        
        conn.commit()
        conn.close()
    
    def _load_sessions(self):
        """Load sessions from persistent storage"""
        try:
            if self.storage_type == "file":
                self._load_from_file()
            elif self.storage_type == "sqlite":
                self._load_from_sqlite()
            
            logger.info(f"Loaded {len(self.sessions)} sessions from {self.storage_type} storage")
        except Exception as e:
            logger.error(f"Error loading sessions: {e}")
            # Continue with empty sessions if load fails
            self.sessions = {}
    
    def _load_from_file(self):
        """Load sessions from JSON file"""
        if not self.sessions_file.exists():
            logger.info("No existing sessions file found, starting with empty sessions")
            return
        
        try:
            with open(self.sessions_file, 'r') as f:
                data = json.load(f)
                self.sessions = data.get("sessions", {})
                
                # Convert ISO format strings back to proper format
                for session_id, session in self.sessions.items():
                    # Ensure all timestamps are strings
                    if "created_at" in session:
                        session["created_at"] = str(session["created_at"])
                    if "updated_at" in session:
                        session["updated_at"] = str(session["updated_at"])
                    if "completed_at" in session:
                        session["completed_at"] = str(session["completed_at"])
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing sessions file: {e}")
            # Backup corrupted file
            backup_path = self.sessions_file.with_suffix('.json.bak')
            if self.sessions_file.exists():
                import shutil
                shutil.copy(self.sessions_file, backup_path)
                logger.warning(f"Backed up corrupted sessions file to {backup_path}")
        except Exception as e:
            logger.error(f"Error loading sessions from file: {e}")
    
    def _load_from_sqlite(self):
        """Load sessions from SQLite database"""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM sessions")
            rows = cursor.fetchall()
            
            for row in rows:
                session = {
                    "session_id": row["session_id"],
                    "user_id": row["user_id"],
                    "state": row["state"],
                    "agent_states": json.loads(row["agent_states"] or "{}"),
                    "artifacts": json.loads(row["artifacts"] or "[]"),
                    "checkpoints": json.loads(row["checkpoints"] or "[]"),
                    "metadata": json.loads(row["metadata"] or "{}"),
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }
                
                if row["completed_at"]:
                    session["completed_at"] = row["completed_at"]
                
                self.sessions[row["session_id"]] = session
        finally:
            conn.close()
    
    def _save_sessions(self):
        """Save sessions to persistent storage"""
        if not self.auto_save:
            return
        
        try:
            with self._lock:
                if self.storage_type == "file":
                    self._save_to_file()
                elif self.storage_type == "sqlite":
                    self._save_to_sqlite()
        except Exception as e:
            logger.error(f"Error saving sessions: {e}")
    
    def _save_to_file(self):
        """Save sessions to JSON file"""
        # Create backup before saving
        if self.sessions_file.exists():
            backup_path = self.sessions_file.with_suffix('.json.bak')
            import shutil
            shutil.copy(self.sessions_file, backup_path)
        
        # Save to temporary file first, then rename (atomic write)
        temp_file = self.sessions_file.with_suffix('.json.tmp')
        with open(temp_file, 'w') as f:
            json.dump({
                "sessions": self.sessions,
                "last_updated": datetime.utcnow().isoformat()
            }, f, indent=2, default=str)
        
        # Atomic rename
        temp_file.replace(self.sessions_file)
    
    def _save_to_sqlite(self):
        """Save sessions to SQLite database"""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        cursor = conn.cursor()
        
        try:
            # Use transaction for atomicity
            cursor.execute("BEGIN TRANSACTION")
            
            for session_id, session in self.sessions.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO sessions 
                    (session_id, user_id, state, agent_states, artifacts, checkpoints, 
                     metadata, created_at, updated_at, completed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    session["user_id"],
                    session["state"],
                    json.dumps(session.get("agent_states", {})),
                    json.dumps(session.get("artifacts", [])),
                    json.dumps(session.get("checkpoints", [])),
                    json.dumps(session.get("metadata", {})),
                    session["created_at"],
                    session["updated_at"],
                    session.get("completed_at")
                ))
            
            cursor.execute("COMMIT")
        except Exception as e:
            cursor.execute("ROLLBACK")
            raise e
        finally:
            conn.close()
    
    # Override parent methods to add persistence
    
    def create_session(self, session_id: str, user_id: str, metadata: Dict = None) -> Dict:
        """Create a new session and persist it"""
        session = super().create_session(session_id, user_id, metadata)
        self._save_sessions()
        return session
    
    def update_agent_state(self, session_id: str, agent_name: str, state: Dict):
        """Update agent state and persist"""
        super().update_agent_state(session_id, agent_name, state)
        self._save_sessions()
    
    def add_artifact(self, session_id: str, artifact_type: str, payload: Any):
        """Add artifact and persist"""
        super().add_artifact(session_id, artifact_type, payload)
        self._save_sessions()
    
    def pause_session(self, session_id: str):
        """Pause session and persist"""
        super().pause_session(session_id)
        self._save_sessions()
    
    def resume_session(self, session_id: str):
        """Resume session and persist"""
        super().resume_session(session_id)
        self._save_sessions()
    
    def complete_session(self, session_id: str):
        """Complete session and persist"""
        super().complete_session(session_id)
        self._save_sessions()
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session and persist"""
        result = super().delete_session(session_id)
        if result:
            self._save_sessions()
            
            # Also delete from persistent storage
            if self.storage_type == "sqlite":
                conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
                cursor = conn.cursor()
                try:
                    cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
                    conn.commit()
                finally:
                    conn.close()
        
        return result
    
    def update_session_metadata(self, session_id: str, metadata: Dict):
        """Update metadata and persist"""
        super().update_session_metadata(session_id, metadata)
        self._save_sessions()
    
    def cleanup_expired_sessions(self, max_age_hours: int = None):
        """Cleanup expired sessions and persist changes"""
        if max_age_hours is None:
            max_age_hours = self.expiration_hours
        
        deleted_count = super().cleanup_expired_sessions(max_age_hours)
        
        if deleted_count > 0:
            self._save_sessions()
            logger.info(f"Cleaned up {deleted_count} expired sessions")
        
        return deleted_count
    
    def force_save(self):
        """Manually trigger a save (useful for shutdown)"""
        self._save_sessions()
        logger.info("Force saved all sessions to persistent storage")
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get statistics about storage"""
        stats = {
            "storage_type": self.storage_type,
            "storage_path": str(self.storage_path),
            "total_sessions": len(self.sessions),
            "active_sessions": len(self.get_active_sessions()),
            "expiration_hours": self.expiration_hours,
            "auto_save": self.auto_save
        }
        
        if self.storage_type == "file":
            if self.sessions_file.exists():
                stats["file_size_bytes"] = self.sessions_file.stat().st_size
        elif self.storage_type == "sqlite":
            if self.db_path.exists():
                stats["db_size_bytes"] = self.db_path.stat().st_size
        
        return stats

