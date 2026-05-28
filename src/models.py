"""
DELIBERATELY VULNERABLE DATABASE MODELS - FOR EDUCATIONAL PURPOSES ONLY

This module demonstrates insecure database design and operations.
"""

import sqlite3
import hashlib
from datetime import datetime
from . import config


class Database:
    """
    Vulnerable database class using raw SQL queries.
    CWE-89: SQL Injection vulnerabilities throughout.
    """

    def __init__(self):
        self.db_path = config.DATABASE_PATH
        self.init_db()

    def get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn

    def init_db(self):
        """Initialize database schema with vulnerable structure."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users table - stores authentication information
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                email TEXT,
                is_admin INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Todos table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                completed INTEGER DEFAULT 0,
                priority TEXT DEFAULT 'medium',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Shared todos table (for sharing between users)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shared_todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                todo_id INTEGER NOT NULL,
                shared_with_user_id INTEGER NOT NULL,
                can_edit INTEGER DEFAULT 0,
                FOREIGN KEY (todo_id) REFERENCES todos(id),
                FOREIGN KEY (shared_with_user_id) REFERENCES users(id)
            )
        """)

        # Files table (for attachments)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                todo_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                uploaded_by INTEGER NOT NULL,
                uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (todo_id) REFERENCES todos(id),
                FOREIGN KEY (uploaded_by) REFERENCES users(id)
            )
        """)

        # Sessions table (insecure session storage)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT NOT NULL,
                session_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        conn.commit()

        # Create default admin user if not exists
        # CWE-327: Using MD5 for password hashing
        admin_password_hash = hashlib.md5(config.DEFAULT_ADMIN_PASSWORD.encode()).hexdigest()

        try:
            cursor.execute(
                "INSERT INTO users (username, password, email, is_admin) VALUES (?, ?, ?, ?)",
                (config.DEFAULT_ADMIN_USERNAME, admin_password_hash, "admin@vulnerable-app.local", 1)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Admin already exists

        conn.close()

    # CWE-89: SQL Injection - String concatenation in queries
    def execute_query(self, query, params=None):
        """
        Execute a SQL query.
        VULNERABLE: Uses string concatenation when params is None
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        if params:
            cursor.execute(query, params)
        else:
            # VULNERABILITY: Direct string concatenation allows SQL injection
            cursor.execute(query)

        conn.commit()
        result = cursor.fetchall()
        conn.close()
        return result

    def execute_query_one(self, query, params=None):
        """Execute query and return single result."""
        conn = self.get_connection()
        cursor = conn.cursor()

        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        result = cursor.fetchone()
        conn.close()
        return result


# Global database instance
db = Database()
