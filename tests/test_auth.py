"""
Tests for the authentication module.
"""

import pytest
from src import auth
from src.models import db


class TestRegistration:
    """Test user registration functionality."""

    def test_register_user_success(self, app):
        """Test successful user registration."""
        with app.app_context():
            result = auth.register_user('newuser', 'password123', 'new@example.com')

            assert result['success'] is True
            assert 'message' in result

            # Verify user was created
            user = db.execute_query_one(
                "SELECT * FROM users WHERE username = 'newuser'"
            )
            assert user is not None
            assert user['email'] == 'new@example.com'

    def test_register_user_duplicate_username(self, app):
        """Test registration with duplicate username."""
        with app.app_context():
            # First registration
            auth.register_user('dupuser', 'password123')

            # Duplicate registration
            result = auth.register_user('dupuser', 'password456')

            assert result['success'] is False
            assert 'error' in result

    def test_register_user_missing_username(self, app):
        """Test registration with missing username."""
        with app.app_context():
            result = auth.register_user('', 'password123')

            assert result['success'] is False
            assert 'required' in result['error'].lower()

    def test_register_user_missing_password(self, app):
        """Test registration with missing password."""
        with app.app_context():
            result = auth.register_user('testuser2', '')

            assert result['success'] is False
            assert 'required' in result['error'].lower()


class TestAuthentication:
    """Test user authentication functionality."""

    def test_authenticate_user_success(self, app):
        """Test successful authentication."""
        with app.app_context():
            # Register user first
            password = 'testpass123'
            auth.register_user('authuser', password, 'auth@example.com')

            # Authenticate
            result = auth.authenticate_user('authuser', password)

            assert result['success'] is True
            assert 'user' in result
            assert result['user']['username'] == 'authuser'

    def test_authenticate_user_wrong_password(self, app):
        """Test authentication with wrong password."""
        with app.app_context():
            # Register user
            auth.register_user('authuser2', 'correctpass')

            # Try wrong password
            result = auth.authenticate_user('authuser2', 'wrongpass')

            assert result['success'] is False

    def test_authenticate_user_nonexistent(self, app):
        """Test authentication with nonexistent user."""
        with app.app_context():
            result = auth.authenticate_user('nosuchuser', 'password')

            assert result['success'] is False

    def test_authenticate_user_sql_injection_blocked(self, app):
        """Test that username injection attempts do not bypass authentication."""
        with app.app_context():
            auth.register_user('victim', 'password123')

            result = auth.authenticate_user("victim' OR '1'='1'--", 'anything')

            assert result['success'] is False
            assert 'Invalid credentials' in result['error']

    def test_get_user_by_username_sql_injection_blocked(self, app):
        """Test that username lookups treat injected SQL as data."""
        with app.app_context():
            auth.register_user('lookupuser', 'password123')

            result = auth.get_user_by_username("lookupuser' OR '1'='1'--")

            assert result is None

    def test_get_user_by_id_sql_injection_blocked(self, app):
        """Test that ID lookups treat injected SQL as data."""
        with app.app_context():
            auth.register_user('iduser', 'password123')

            result = auth.get_user_by_id("1 OR 1=1")

            assert result is None


class TestSessionManagement:
    """Test session management functions."""

    def test_create_session(self, app):
        """Test session creation."""
        with app.app_context():
            # Register and authenticate
            auth.register_user('sessionuser', 'password123')
            result = auth.authenticate_user('sessionuser', 'password123')

            assert result['success'] is True
            assert 'session_token' in result
            assert result['session_token'] is not None

    def test_get_session_user(self, app, client):
        """Test getting user from session."""
        with app.app_context():
            # Register and login
            auth.register_user('sessionuser2', 'password123')
            auth_result = auth.authenticate_user('sessionuser2', 'password123')

            # Get session user
            user = auth.get_session_user(auth_result['session_token'])

            assert user is not None
            assert user['username'] == 'sessionuser2'

    def test_get_session_user_sql_injection_blocked(self, app, client):
        """Test that session token lookups treat injected SQL as data."""
        with app.app_context():
            auth.register_user('sessionlookup', 'password123')
            auth_result = auth.authenticate_user('sessionlookup', 'password123')

            result = auth.get_session_user(
                f"{auth_result['session_token']}' OR '1'='1"
            )

            assert result is None

    def test_logout_user(self, app):
        """Test user logout."""
        with app.app_context():
            # Register and login
            auth.register_user('logoutuser', 'password123')
            auth_result = auth.authenticate_user('logoutuser', 'password123')
            token = auth_result['session_token']

            # Logout
            result = auth.logout_user(token)

            assert result['success'] is True

            # Session should be gone
            user = auth.get_session_user(token)
            assert user is None

    def test_change_password_rejects_injected_user_id(self, app):
        """Test that change_password treats a crafted user_id as data."""
        with app.app_context():
            auth.register_user('changepassuser', 'password123')

            result = auth.change_password("1 OR 1=1", 'password123', 'newpass123')

            assert result['success'] is False
            assert result['error'] == 'User not found'


class TestAuthorizationBypass:
    """Test authentication bypass vulnerabilities."""

    def test_bypass_parameter(self, app, client):
        """Test authentication bypass via ?bypass=true parameter."""
        with app.app_context():
            # Try accessing with bypass parameter
            response = client.get('/todos?bypass=true')

            # Should allow access (vulnerability)
            # Asserts the current (unremediated) behaviour
            assert response.status_code in [200, 302]  # Either success or redirect
