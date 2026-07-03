"""
Pytest configuration and fixtures for testing the vulnerable todo app.
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import create_app
from src.models import db


@pytest.fixture(scope='function')
def app():
    """Create and configure a test Flask application."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')

    # Override config for testing
    os.environ['DATABASE_PATH'] = db_path
    os.environ['TESTING'] = 'True'

    # Create app
    app = create_app()
    app.config['TESTING'] = True
    app.config['DATABASE_PATH'] = db_path

    # Point the global db instance at the per-test temp database so that
    # parallel workers never share the same SQLite file.
    db.db_path = db_path

    # Initialize database
    with app.app_context():
        db.init_db()  # creates schema and default admin user
        # Create an additional test user
        db.execute_query(
            "INSERT INTO users (username, password, email, is_admin) VALUES (?, ?, ?, ?)",
            ('testuser', 'test_hash', 'test@example.com', 0)
        )

    yield app

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def test_user():
    """Return test user credentials."""
    return {
        'username': 'testuser',
        'password': 'testpass123',
        'email': 'test@example.com'
    }


@pytest.fixture
def admin_user():
    """Return admin user credentials."""
    return {
        'username': 'admin',
        'password': 'admin',
        'email': 'admin@example.com'
    }
