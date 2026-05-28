"""
Tests for the database models module.
"""

import pytest
import tempfile
import os
from src.models import Database, db


class TestDatabase:
    """Test the Database class."""

    def test_database_initialization(self, app):
        """Test database initialization."""
        with app.app_context():
            conn = db.get_connection()
            cursor = conn.cursor()

            # Check if tables exist
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]

            assert 'users' in tables
            assert 'todos' in tables
            assert 'sessions' in tables
            conn.close()

    def test_execute_query(self, app):
        """Test execute_query method."""
        with app.app_context():
            # Insert a test todo
            db.execute_query(
                "INSERT INTO todos (user_id, title, description) VALUES (?, ?, ?)",
                (1, 'Test Todo', 'Test Description')
            )

            # Query it back
            result = db.execute_query_one(
                "SELECT * FROM todos WHERE title = ?",
                ('Test Todo',)
            )

            assert result is not None
            assert result['title'] == 'Test Todo'
            assert result['description'] == 'Test Description'

    def test_execute_query_one(self, app):
        """Test execute_query_one method."""
        with app.app_context():
            # Query existing user
            user = db.execute_query_one(
                "SELECT * FROM users WHERE username = ?",
                ('testuser',)
            )

            assert user is not None
            assert user['username'] == 'testuser'

    def test_execute_query_one_no_result(self, app):
        """Test execute_query_one with no results."""
        with app.app_context():
            result = db.execute_query_one(
                "SELECT * FROM users WHERE username = ?",
                ('nonexistent',)
            )

            assert result is None

    def test_execute_query_all(self, app):
        """Test execute_query_all method."""
        with app.app_context():
            # Insert multiple todos
            db.execute_query(
                "INSERT INTO todos (user_id, title) VALUES (1, 'Todo 1')"
            )
            db.execute_query(
                "INSERT INTO todos (user_id, title) VALUES (1, 'Todo 2')"
            )

            # Query all
            results = db.execute_query_all(
                "SELECT * FROM todos WHERE user_id = 1"
            )

            assert len(results) >= 2

    def test_create_admin_user(self, app):
        """Test admin user creation."""
        with app.app_context():
            user = db.execute_query_one(
                "SELECT * FROM users WHERE username = 'admin'"
            )

            assert user is not None
            assert user['is_admin'] == 1
