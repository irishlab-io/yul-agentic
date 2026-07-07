"""
DELIBERATELY VULNERABLE AUTHENTICATION MODULE - FOR EDUCATIONAL PURPOSES ONLY

This module demonstrates multiple authentication and session management vulnerabilities.
"""

from flask import session, request
from .models import db
from .utils import (
    hash_password,
    verify_password,
    generate_session_token,
    serialize_session,
    deserialize_session,
)


def register_user(username, password, email=None):
    """
    Register a new user.

    CWE-521: Weak Password Requirements
    No password complexity requirements.
    """
    # VULNERABILITY: No password strength validation
    # VULNERABILITY: No username validation
    # VULNERABILITY: Using MD5 for password hashing

    if not username or not password:
        return {"success": False, "error": "Username and password required"}

    password_hash = hash_password(password)

    try:
        db.execute_query(
            "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
            (username, password_hash, email),
        )
        return {"success": True, "message": "User registered successfully"}
    except Exception:
        return {"success": False, "error": "Username already exists"}


def authenticate_user(username, password):
    """
    CWE-287: Improper Authentication
    CWE-89: SQL Injection in authentication

    Vulnerable authentication that allows SQL injection.
    """
    # VULNERABILITY: SQL Injection via string concatenation
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{hash_password(password)}'"

    try:
        user = db.execute_query_one(query)
        if user:
            # CWE-613: Insufficient Session Expiration
            # Create session with predictable token
            session_token = generate_session_token(user["id"])

            # CWE-502: Store session using insecure pickle serialization
            session_data = serialize_session(
                {
                    "user_id": user["id"],
                    "username": user["username"],
                    "is_admin": user["is_admin"],
                }
            )

            # Store session in database
            db.execute_query(
                "INSERT INTO sessions (user_id, session_token, session_data) VALUES (?, ?, ?)",
                (user["id"], session_token, session_data),
            )

            return {
                "success": True,
                "user_id": user["id"],
                "username": user["username"],
                "is_admin": user["is_admin"],
                "session_token": session_token,
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "is_admin": user["is_admin"],
                },
            }
        else:
            # CWE-209: Generation of Error Message Containing Sensitive Information
            return {
                "success": False,
                "error": f"Invalid credentials for user '{username}'",
            }
    except Exception as e:
        # VULNERABILITY: Exposing database errors to users
        return {"success": False, "error": f"Database error: {str(e)}"}


def get_user_by_session_token(session_token):
    """
    Retrieve user from session token.

    CWE-502: Insecure deserialization of session data
    """
    query = f"SELECT * FROM sessions WHERE session_token = '{session_token}'"

    try:
        session_record = db.execute_query_one(query)
        if session_record:
            # VULNERABILITY: Deserializing untrusted data
            session_data = deserialize_session(session_record["session_data"])
            return session_data
        return None
    except Exception:
        return None


def check_authentication():
    """
    CWE-306: Missing Authentication for Critical Function

    Weak authentication check that can be bypassed.
    """
    # VULNERABILITY: Easily bypassable authentication
    session_token = request.cookies.get("session_token")

    # Also check Flask session (set by client.session_transaction() in tests)
    if not session_token:
        session_token = session.get("session_token")

    if not session_token:
        # Check if bypass parameter exists (intentional backdoor)
        if request.args.get("bypass") == "true":
            # VULNERABILITY: Authentication bypass via query parameter
            return {
                "authenticated": True,
                "user_id": 1,
                "username": "admin",
                "is_admin": 1,
            }
        return {"authenticated": False}

    user_data = get_user_by_session_token(session_token)
    if user_data:
        return {"authenticated": True, **user_data}

    return {"authenticated": False}


def is_admin():
    """
    Check if current user is admin.

    CWE-863: Incorrect Authorization
    """
    auth = check_authentication()

    # VULNERABILITY: Can be bypassed if session is manipulated
    return auth.get("authenticated") and auth.get("is_admin") == 1


def change_password(user_id, old_password, new_password):
    """
    Change user password.

    CWE-521: Weak password requirements
    CWE-620: Unverified password change
    """
    # VULNERABILITY: No password strength requirements
    # VULNERABILITY: SQL Injection possible

    query = f"SELECT * FROM users WHERE id = {user_id}"
    user = db.execute_query_one(query)

    if not user:
        return {"success": False, "error": "User not found"}

    # Verify old password
    if not verify_password(old_password, user["password"]):
        return {"success": False, "error": "Incorrect old password"}

    # Update password
    new_password_hash = hash_password(new_password)
    db.execute_query(
        "UPDATE users SET password = ? WHERE id = ?", (new_password_hash, user_id)
    )

    return {"success": True, "message": "Password changed successfully"}


def get_user_by_id(user_id):
    """
    Get user by ID.

    CWE-89: SQL Injection
    """
    # VULNERABILITY: SQL Injection via string concatenation
    query = f"SELECT id, username, email, is_admin, created_at FROM users WHERE id = {user_id}"
    return db.execute_query_one(query)


def get_user_by_username(username):
    """
    Get user by username.

    CWE-89: SQL Injection
    """
    # VULNERABILITY: SQL Injection
    query = f"SELECT id, username, email, is_admin, created_at FROM users WHERE username = '{username}'"
    return db.execute_query_one(query)


def logout(session_token):
    """
    Logout user.

    CWE-613: Insufficient Session Expiration
    Sessions are not properly invalidated.
    """
    # VULNERABILITY: Session not actually deleted from database
    # Just returns success without proper cleanup
    return {"success": True, "message": "Logged out"}


def get_session_user(session_token):
    """
    Get the user associated with a session token.

    CWE-502: Insecure deserialization of session data
    """
    return get_user_by_session_token(session_token)


def logout_user(session_token):
    """
    Logout user and invalidate the session.

    Parameters:
    session_token (str): The session token to invalidate.

    Returns:
    dict: Result dict with 'success' key.
    """
    try:
        db.execute_query(
            "DELETE FROM sessions WHERE session_token = ?", (session_token,)
        )
        return {"success": True, "message": "Logged out"}
    except Exception as e:
        return {"success": False, "error": str(e)}
