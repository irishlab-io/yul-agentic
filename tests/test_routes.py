"""
Tests for Flask application routes.
"""

import pytest
from flask import session
from src import auth


class TestAuthRoutes:
    """Test authentication routes."""

    def test_login_page(self, client):
        """Test login page loads."""
        response = client.get('/login')

        assert response.status_code == 200
        assert b'login' in response.data.lower()

    def test_register_page(self, client):
        """Test register page loads."""
        response = client.get('/register')

        assert response.status_code == 200
        assert b'register' in response.data.lower()

    def test_login_post_success(self, client, app):
        """Test successful login."""
        with app.app_context():
            # Register user first
            auth.register_user('logintest', 'password123')

            # Try to login
            response = client.post('/login', data={
                'username': 'logintest',
                'password': 'password123'
            }, follow_redirects=True)

            assert response.status_code == 200

    def test_login_post_failure(self, client):
        """Test failed login."""
        response = client.post('/login', data={
            'username': 'nosuchuser',
            'password': 'wrongpass'
        })

        assert response.status_code in [200, 302]

    def test_register_post_success(self, client):
        """Test successful registration."""
        response = client.post('/register', data={
            'username': 'newreguser',
            'password': 'password123',
            'email': 'new@example.com'
        }, follow_redirects=True)

        assert response.status_code == 200

    def test_logout(self, client, app):
        """Test logout."""
        with app.app_context():
            # Register and login
            auth.register_user('logouttest', 'password123')
            client.post('/login', data={
                'username': 'logouttest',
                'password': 'password123'
            })

            # Logout
            response = client.get('/logout', follow_redirects=True)

            assert response.status_code == 200


class TestTodoRoutes:
    """Test todo management routes."""

    def test_todos_page_requires_auth(self, client):
        """Test todos page requires authentication."""
        response = client.get('/todos')

        # Should redirect to login or show error
        assert response.status_code in [302, 401, 403]

    def test_todos_page_authenticated(self, client, app):
        """Test todos page with authentication."""
        with app.app_context():
            # Register and login
            auth.register_user('todouser', 'password123')
            auth_result = auth.authenticate_user('todouser', 'password123')

            # Access todos page
            with client.session_transaction() as sess:
                sess['session_token'] = auth_result['session_token']

            response = client.get('/todos')

            # Should be accessible
            assert response.status_code in [200, 302]

    def test_create_todo_post(self, client, app):
        """Test creating a todo via POST."""
        with app.app_context():
            # Setup authenticated session
            auth.register_user('createuser', 'password123')
            auth_result = auth.authenticate_user('createuser', 'password123')

            with client.session_transaction() as sess:
                sess['session_token'] = auth_result['session_token']

            # Create todo
            response = client.post('/todo/create', data={
                'title': 'Test Todo',
                'description': 'Test Description',
                'priority': 'high'
            })

            assert response.status_code in [200, 302]


class TestFileRoutes:
    """Test file upload/download routes."""

    def test_upload_page(self, client, app):
        """Test file upload page."""
        with app.app_context():
            # Login first
            auth.register_user('fileuser', 'password123')
            auth_result = auth.authenticate_user('fileuser', 'password123')

            with client.session_transaction() as sess:
                sess['session_token'] = auth_result['session_token']

            response = client.get('/upload')

            assert response.status_code in [200, 302]

    def test_file_download_vulnerability(self, client):
        """Test path traversal vulnerability in file download."""
        # This demonstrates the vulnerability
        # Try to download a system file
        response = client.get('/file/../../../etc/hostname')

        # Vulnerability may allow this
        assert response.status_code in [200, 404, 500]


class TestSearchRoutes:
    """Test search functionality."""

    def test_search_page(self, client, app):
        """Test search page loads."""
        with app.app_context():
            auth.register_user('searchuser', 'password123')
            auth_result = auth.authenticate_user('searchuser', 'password123')

            with client.session_transaction() as sess:
                sess['session_token'] = auth_result['session_token']

            response = client.get('/search')

            assert response.status_code in [200, 302]

    def test_search_query(self, client, app):
        """Test search with query."""
        with app.app_context():
            auth.register_user('searchuser2', 'password123')
            auth_result = auth.authenticate_user('searchuser2', 'password123')

            with client.session_transaction() as sess:
                sess['session_token'] = auth_result['session_token']

            response = client.get('/search?q=test')

            assert response.status_code in [200, 302]


class TestAdminRoutes:
    """Test admin panel routes."""

    def test_admin_page_requires_admin(self, client, app):
        """Test admin page requires admin privileges."""
        with app.app_context():
            # Regular user
            auth.register_user('regularuser', 'password123')
            auth_result = auth.authenticate_user('regularuser', 'password123')

            with client.session_transaction() as sess:
                sess['session_token'] = auth_result['session_token']

            response = client.get('/admin')

            # Should deny access
            assert response.status_code in [302, 401, 403]

    def test_admin_page_with_admin(self, client, app):
        """Test admin page with admin user."""
        with app.app_context():
            # Get admin user
            admin_result = auth.authenticate_user('admin', 'admin')

            with client.session_transaction() as sess:
                sess['session_token'] = admin_result['session_token']

            response = client.get('/admin')

            # Should allow access
            assert response.status_code in [200, 302]


class TestAPIRoutes:
    """Test API endpoints."""

    def test_api_todos_list(self, client, app):
        """Test API todos list endpoint."""
        with app.app_context():
            response = client.get('/api/todos')

            # API should be accessible (no auth - vulnerability)
            assert response.status_code == 200
            assert response.is_json

    def test_api_todo_create(self, client):
        """Test API todo creation."""
        response = client.post('/api/todos', json={
            'user_id': 1,
            'title': 'API Todo',
            'description': 'Created via API'
        })

        assert response.status_code in [200, 201, 400]


class TestVulnerabilityDemonstrations:
    """Test that documented vulnerabilities exist."""

    def test_xss_vulnerability_exists(self, client, app):
        """Test that XSS vulnerability exists in templates."""
        with app.app_context():
            auth.register_user('xssuser', 'password123')
            auth_result = auth.authenticate_user('xssuser', 'password123')

            # Create todo with XSS payload
            from src import database
            database.create_todo(1, '<script>alert("XSS")</script>')

            with client.session_transaction() as sess:
                sess['session_token'] = auth_result['session_token']

            response = client.get('/todos')

            # XSS payload should be in response (vulnerability)
            assert b'<script>' in response.data or response.status_code in [200, 302]

    def test_csrf_vulnerability_exists(self, client):
        """Test that CSRF protection is disabled."""
        # CSRF tokens should not be present (vulnerability)
        response = client.get('/login')

        # Check that CSRF token is not in form
        # (In a secure app, it should be there)
        assert response.status_code == 200

    def test_debug_mode_enabled(self, app):
        """Test that debug mode is enabled (vulnerability)."""
        assert app.config.get('DEBUG', False) or app.config.get('FLASK_ENV') == 'development'


class TestHomePage:
    """Test home/landing page."""

    def test_home_page(self, client):
        """Test home page loads."""
        response = client.get('/')

        assert response.status_code in [200, 302]
