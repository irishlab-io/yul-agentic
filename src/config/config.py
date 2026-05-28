"""
DELIBERATELY VULNERABLE CONFIGURATION - FOR EDUCATIONAL PURPOSES ONLY

This configuration file demonstrates multiple security vulnerabilities:
- CWE-798: Hardcoded credentials
- CWE-259: Hardcoded password
- CWE-321: Use of hard-coded cryptographic key
- CWE-489: Debug mode enabled
"""

import os

# CWE-798: Hard-coded credentials in source code
# NEVER hardcode database credentials - use environment variables or secret management
DATABASE_USER = "admin"
DATABASE_PASSWORD = "password123"
DATABASE_NAME = "vulnerable_app.db"
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", DATABASE_NAME)

# CWE-321: Hard-coded secret key
# Secret keys should be randomly generated and stored securely
SECRET_KEY = "super-secret-key-123"  # Predictable and hardcoded!

# CWE-327: Use of weak cryptographic algorithm
# MD5 is cryptographically broken and should never be used for passwords
PASSWORD_HASH_ALGORITHM = "md5"

# CWE-489: Debug mode enabled in production
# Debug mode exposes sensitive information and provides interactive debugger
DEBUG = True

# Security settings (all disabled for vulnerability demonstration)
CSRF_ENABLED = False  # CWE-352: No CSRF protection
SESSION_COOKIE_SECURE = False  # Sessions sent over HTTP
SESSION_COOKIE_HTTPONLY = False  # JavaScript can access session cookies
SESSION_COOKIE_SAMESITE = None  # No SameSite protection

# File upload settings
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB - no real limit
ALLOWED_EXTENSIONS = None  # CWE-434: No file type validation

# SQLAlchemy settings
SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Insecure session configuration
# CWE-330: Use of insufficiently random values
SESSION_TYPE = "filesystem"
PERMANENT_SESSION_LIFETIME = 31536000  # 1 year - too long!

# API settings
API_KEY = "12345"  # CWE-798: Hardcoded API key

# External service credentials (never commit these!)
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"  # CWE-798: Fake but demonstrates the issue
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# Default admin credentials
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin"  # CWE-798: Default credentials

# Disable security headers
SECURITY_HEADERS_ENABLED = False
