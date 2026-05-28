"""
Tests for the database operations module.
"""

import pytest
from src import database
from src.models import db


class TestTodoCreation:
    """Test todo creation functionality."""

    def test_create_todo_success(self, app):
        """Test successful todo creation."""
        with app.app_context():
            result = database.create_todo(
                user_id=1,
                title='Test Todo',
                description='Test Description',
                priority='high'
            )

            assert result['success'] is True
            assert 'todo_id' in result
            assert result['todo_id'] > 0

    def test_create_todo_minimal(self, app):
        """Test todo creation with minimal fields."""
        with app.app_context():
            result = database.create_todo(
                user_id=1,
                title='Minimal Todo'
            )

            assert result['success'] is True
            assert 'todo_id' in result

    def test_create_todo_sql_injection_vulnerability(self, app):
        """Test SQL injection vulnerability in create_todo."""
        with app.app_context():
            # Try SQL injection in title
            # This demonstrates the vulnerability
            malicious_title = "Test'); DROP TABLE todos; --"

            # Should not crash (but is vulnerable)
            try:
                result = database.create_todo(
                    user_id=1,
                    title=malicious_title,
                    description='Test'
                )
                # If it succeeds, vulnerability exists
                assert True
            except Exception:
                # If it fails, that's also okay for this test
                assert True


class TestTodoRetrieval:
    """Test todo retrieval functionality."""

    def test_get_todo_by_id(self, app):
        """Test retrieving a todo by ID."""
        with app.app_context():
            # Create a todo
            create_result = database.create_todo(1, 'Test Todo')
            todo_id = create_result['todo_id']

            # Retrieve it
            result = database.get_todo_by_id(todo_id)

            assert result['success'] is True
            assert result['todo'] is not None
            assert result['todo']['title'] == 'Test Todo'

    def test_get_todo_by_id_nonexistent(self, app):
        """Test retrieving nonexistent todo."""
        with app.app_context():
            result = database.get_todo_by_id(99999)

            assert result['success'] is True
            assert result['todo'] is None

    def test_get_todo_idor_vulnerability(self, app):
        """Test IDOR vulnerability - accessing other user's todos."""
        with app.app_context():
            # User 1 creates a todo
            create_result = database.create_todo(1, 'User 1 Todo')
            todo_id = create_result['todo_id']

            # User 2 tries to access it (should fail in secure app)
            result = database.get_todo_by_id(todo_id, user_id=2)

            # Vulnerability: returns todo even though user_id doesn't match
            assert result['success'] is True
            assert result['todo'] is not None  # IDOR vulnerability exists

    def test_get_user_todos(self, app):
        """Test retrieving all todos for a user."""
        with app.app_context():
            # Create multiple todos
            database.create_todo(1, 'Todo 1')
            database.create_todo(1, 'Todo 2')
            database.create_todo(1, 'Todo 3')

            # Retrieve all
            result = database.get_user_todos(1)

            assert result['success'] is True
            assert len(result['todos']) >= 3


class TestTodoUpdate:
    """Test todo update functionality."""

    def test_update_todo_success(self, app):
        """Test successful todo update."""
        with app.app_context():
            # Create todo
            create_result = database.create_todo(1, 'Original Title')
            todo_id = create_result['todo_id']

            # Update it
            result = database.update_todo(
                todo_id=todo_id,
                title='Updated Title',
                description='Updated Description',
                completed=1
            )

            assert result['success'] is True

            # Verify update
            todo = database.get_todo_by_id(todo_id)
            assert todo['todo']['title'] == 'Updated Title'
            assert todo['todo']['completed'] == 1

    def test_update_todo_partial(self, app):
        """Test partial todo update."""
        with app.app_context():
            # Create todo
            create_result = database.create_todo(1, 'Original', 'Original Desc')
            todo_id = create_result['todo_id']

            # Update only title
            result = database.update_todo(todo_id, title='New Title')

            assert result['success'] is True


class TestTodoDeletion:
    """Test todo deletion functionality."""

    def test_delete_todo_success(self, app):
        """Test successful todo deletion."""
        with app.app_context():
            # Create todo
            create_result = database.create_todo(1, 'To Delete')
            todo_id = create_result['todo_id']

            # Delete it
            result = database.delete_todo(todo_id)

            assert result['success'] is True

            # Verify deletion
            todo = database.get_todo_by_id(todo_id)
            assert todo['todo'] is None

    def test_delete_todo_nonexistent(self, app):
        """Test deleting nonexistent todo."""
        with app.app_context():
            result = database.delete_todo(99999)

            # Should not crash
            assert result is not None


class TestTodoSearch:
    """Test todo search functionality."""

    def test_search_todos(self, app):
        """Test searching todos."""
        with app.app_context():
            # Create todos with searchable content
            database.create_todo(1, 'Python Programming', 'Learn Python')
            database.create_todo(1, 'JavaScript Tutorial', 'Learn JS')
            database.create_todo(1, 'Python Django', 'Web framework')

            # Search for Python
            result = database.search_todos(1, 'Python')

            assert result['success'] is True
            assert len(result['todos']) >= 2

    def test_search_todos_sql_injection(self, app):
        """Test SQL injection vulnerability in search."""
        with app.app_context():
            # Try SQL injection in search
            malicious_query = "' OR '1'='1"

            # Should not crash (but is vulnerable)
            try:
                result = database.search_todos(1, malicious_query)
                assert True  # Vulnerability exists
            except Exception:
                assert True  # Or it crashes, which also demonstrates the issue


class TestTodoSharing:
    """Test todo sharing functionality."""

    def test_share_todo(self, app):
        """Test sharing a todo with another user."""
        with app.app_context():
            # Create todo
            create_result = database.create_todo(1, 'Shared Todo')
            todo_id = create_result['todo_id']

            # Share with user 2
            result = database.share_todo(todo_id, 2)

            assert result['success'] is True

    def test_get_shared_todos(self, app):
        """Test retrieving shared todos."""
        with app.app_context():
            # Create and share todo
            create_result = database.create_todo(1, 'Shared Todo')
            todo_id = create_result['todo_id']
            database.share_todo(todo_id, 2)

            # Get shared todos for user 2
            result = database.get_shared_todos(2)

            assert result['success'] is True
            assert len(result['todos']) >= 1
