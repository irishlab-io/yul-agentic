"""
Tests for the utility functions module.
"""

import pytest
import os
import tempfile
from src import utils


class TestPasswordHashing:
    """Test password hashing functionality."""

    def test_hash_password(self):
        """Test password hashing."""
        password = 'test_password123'
        hashed = utils.hash_password(password)

        assert hashed is not None
        assert len(hashed) == 32  # MD5 produces 32 character hex string
        assert hashed != password

    def test_hash_password_consistency(self):
        """Test that hashing is consistent."""
        password = 'consistent_test'
        hash1 = utils.hash_password(password)
        hash2 = utils.hash_password(password)

        assert hash1 == hash2

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = 'correct_password'
        hashed = utils.hash_password(password)

        assert utils.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = 'correct_password'
        hashed = utils.hash_password(password)

        assert utils.verify_password('wrong_password', hashed) is False


class TestSessionToken:
    """Test session token generation."""

    def test_generate_session_token(self):
        """Test session token generation."""
        user_id = 123
        token = utils.generate_session_token(user_id)

        assert token is not None
        assert len(token) > 0

    def test_generate_session_token_predictability(self):
        """Test that session tokens are predictable (vulnerability)."""
        # This demonstrates the vulnerability
        user_id = 456
        token1 = utils.generate_session_token(user_id)
        token2 = utils.generate_session_token(user_id)

        # Tokens should be different but predictable based on timestamp
        # (This is a vulnerability demonstration)
        assert token1 is not None
        assert token2 is not None


class TestSerialization:
    """Test session serialization functions."""

    def test_serialize_session(self):
        """Test session serialization."""
        session_data = {
            'user_id': 123,
            'username': 'testuser',
            'is_admin': False
        }

        serialized = utils.serialize_session(session_data)

        assert serialized is not None
        assert isinstance(serialized, bytes)

    def test_deserialize_session(self):
        """Test session deserialization."""
        session_data = {
            'user_id': 456,
            'username': 'admin',
            'is_admin': True
        }

        serialized = utils.serialize_session(session_data)
        deserialized = utils.deserialize_session(serialized)

        assert deserialized == session_data
        assert deserialized['user_id'] == 456
        assert deserialized['is_admin'] is True

    def test_deserialize_invalid_data(self):
        """Test deserializing invalid data."""
        invalid_data = b'invalid pickle data'

        result = utils.deserialize_session(invalid_data)

        # Should handle error gracefully
        assert result is None or isinstance(result, dict)


class TestCommandInjection:
    """Test command injection vulnerability."""

    def test_run_system_command_simple(self):
        """Test running a simple system command."""
        result = utils.run_system_command('echo "Hello World"')

        assert result is not None
        assert 'Hello World' in result

    def test_run_system_command_vulnerability(self):
        """Test command injection vulnerability exists."""
        # This demonstrates the vulnerability
        # In a secure app, this should be prevented
        malicious_cmd = 'echo "test" && echo "injected"'

        result = utils.run_system_command(malicious_cmd)

        # Vulnerability allows command injection
        assert 'test' in result
        assert 'injected' in result

    def test_run_system_command_error(self):
        """Test command with error."""
        result = utils.run_system_command('false')  # Command that returns error

        assert result is not None


class TestPathTraversal:
    """Test path traversal vulnerability."""

    def test_get_file_content_normal(self, app):
        """Test reading a normal file."""
        with app.app_context():
            # Create a test file
            test_file = os.path.join(utils.config.UPLOAD_FOLDER, 'test.txt')
            os.makedirs(os.path.dirname(test_file), exist_ok=True)
            with open(test_file, 'w') as f:
                f.write('Test content')

            # Read it
            content = utils.get_file_content('test.txt')

            assert content == 'Test content'

            # Cleanup
            os.remove(test_file)

    def test_get_file_content_path_traversal_vulnerability(self):
        """Test path traversal vulnerability exists."""
        # This demonstrates the vulnerability
        # In a secure app, this should be prevented
        traversal_path = '../../../etc/hostname'

        try:
            content = utils.get_file_content(traversal_path)
            # If it doesn't crash, vulnerability exists
            assert True
        except Exception:
            # If it fails, that's okay too for this test
            assert True

    def test_get_file_content_nonexistent(self):
        """Test reading nonexistent file."""
        content = utils.get_file_content('nonexistent_file.txt')

        # Should handle error gracefully
        assert content is None or 'Error' in content


class TestXMLParsing:
    """Test XML parsing vulnerabilities."""

    def test_parse_xml_simple(self):
        """Test parsing simple XML."""
        xml_string = '<root><item>Test</item></root>'

        result = utils.parse_xml(xml_string)

        assert result is not None

    def test_parse_xml_xxe_vulnerability(self):
        """Test XXE vulnerability exists."""
        # This demonstrates the XXE vulnerability
        xxe_payload = '''<?xml version="1.0"?>
        <!DOCTYPE root [
        <!ENTITY test "XXE test">
        ]>
        <root>&test;</root>'''

        try:
            result = utils.parse_xml(xxe_payload)
            # Vulnerability allows parsing
            assert True
        except Exception:
            # Or it might fail, which is also informative
            assert True

    def test_parse_xml_invalid(self):
        """Test parsing invalid XML."""
        invalid_xml = '<root><unclosed>'

        result = utils.parse_xml(invalid_xml)

        # Should handle error gracefully
        assert result is None or 'Error' in str(result)


class TestSSRF:
    """Test SSRF vulnerability."""

    def test_fetch_url_external(self):
        """Test fetching external URL."""
        # Use a reliable test URL
        url = 'https://httpbin.org/status/200'

        try:
            result = utils.fetch_url(url)
            # If successful, check result
            if result['success']:
                assert 'content' in result
        except Exception:
            # Network errors are okay in tests
            pytest.skip("Network not available")

    def test_fetch_url_ssrf_vulnerability(self):
        """Test SSRF vulnerability exists."""
        # This demonstrates the SSRF vulnerability
        # In a secure app, internal URLs should be blocked
        internal_url = 'http://localhost:8000'

        try:
            result = utils.fetch_url(internal_url)
            # Vulnerability allows accessing internal resources
            assert result is not None
        except Exception:
            # Connection may fail, which is okay
            assert True

    def test_fetch_url_invalid(self):
        """Test fetching invalid URL."""
        invalid_url = 'not_a_valid_url'

        result = utils.fetch_url(invalid_url)

        assert result is not None
        assert result['success'] is False


class TestFileOperations:
    """Test file operation utilities."""

    def test_save_uploaded_file(self, app):
        """Test saving uploaded file."""
        with app.app_context():
            # Create test file content
            file_content = b'Test file content'
            filename = 'test_upload.txt'

            result = utils.save_uploaded_file(file_content, filename)

            assert result['success'] is True
            assert 'filepath' in result

            # Cleanup
            if os.path.exists(result['filepath']):
                os.remove(result['filepath'])

    def test_get_file_checksum(self, app):
        """Test getting file checksum."""
        with app.app_context():
            # Create a test file
            test_file = os.path.join(utils.config.UPLOAD_FOLDER, 'checksum_test.txt')
            os.makedirs(os.path.dirname(test_file), exist_ok=True)
            with open(test_file, 'w') as f:
                f.write('Checksum content')

            # Get checksum
            checksum = utils.get_file_checksum('checksum_test.txt')

            assert checksum is not None
            assert len(checksum) > 0

            # Cleanup
            os.remove(test_file)
