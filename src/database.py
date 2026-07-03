"""
DELIBERATELY VULNERABLE TODO OPERATIONS - FOR EDUCATIONAL PURPOSES ONLY

This module demonstrates IDOR, SQL injection, and authorization vulnerabilities.
"""

from .models import db
from datetime import datetime


def create_todo(user_id, title, description="", priority="medium"):
    """
    Create a new todo.

    CWE-89: SQL Injection via string concatenation
    """
    # VULNERABILITY: SQL Injection in INSERT statement
    query = f"""
        INSERT INTO todos (user_id, title, description, priority, created_at, updated_at)
        VALUES ({user_id}, '{title}', '{description}', '{priority}', datetime('now'), datetime('now'))
    """

    conn = db.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        last_id = cursor.lastrowid
        conn.commit()
        return {"success": True, "todo_id": last_id}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def get_todo_by_id(todo_id, user_id=None):
    """
    Get todo by ID.

    CWE-639: Insecure Direct Object Reference (IDOR)
    No authorization check - any user can access any todo!
    """
    # VULNERABILITY: IDOR - No check if user owns this todo
    # VULNERABILITY: SQL Injection
    query = f"SELECT * FROM todos WHERE id = {todo_id}"

    try:
        todo = db.execute_query_one(query)
        return {"success": True, "todo": dict(todo) if todo else None}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_user_todos(user_id):
    """
    Get all todos for a user.

    CWE-89: SQL Injection
    """
    # VULNERABILITY: SQL Injection
    query = f"SELECT * FROM todos WHERE user_id = {user_id} ORDER BY created_at DESC"

    try:
        todos = db.execute_query(query)
        return {"success": True, "todos": [dict(row) for row in todos]}
    except Exception as e:
        return {"success": False, "error": str(e)}


def update_todo(todo_id, title=None, description=None, completed=None, priority=None, user_id=None):
    """
    Update todo.

    CWE-639: IDOR - No authorization check
    CWE-89: SQL Injection
    """
    # VULNERABILITY: No check if user owns this todo
    # VULNERABILITY: SQL Injection via string concatenation

    updates = []
    if title is not None:
        updates.append(f"title = '{title}'")
    if description is not None:
        updates.append(f"description = '{description}'")
    if completed is not None:
        updates.append(f"completed = {1 if completed else 0}")
    if priority is not None:
        updates.append(f"priority = '{priority}'")

    if not updates:
        return {"success": False, "error": "No fields to update"}

    updates.append("updated_at = datetime('now')")
    update_clause = ", ".join(updates)

    query = f"UPDATE todos SET {update_clause} WHERE id = {todo_id}"

    try:
        db.execute_query(query)
        return {"success": True, "message": "Todo updated"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def delete_todo(todo_id, user_id=None):
    """
    Delete todo.

    CWE-639: IDOR - Any user can delete any todo!
    """
    # VULNERABILITY: No authorization check
    # VULNERABILITY: SQL Injection
    query = f"DELETE FROM todos WHERE id = {todo_id}"

    try:
        db.execute_query(query)
        # Also delete associated files and shares
        db.execute_query(f"DELETE FROM files WHERE todo_id = {todo_id}")
        db.execute_query(f"DELETE FROM shared_todos WHERE todo_id = {todo_id}")
        return {"success": True, "message": "Todo deleted"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def search_todos(user_id, search_term):
    """
    Search todos.

    CWE-89: SQL Injection via search parameter
    """
    # VULNERABILITY: SQL Injection in search query
    # VULNERABILITY: No user restriction - searches all todos
    query = f"SELECT * FROM todos WHERE title LIKE '%{search_term}%' OR description LIKE '%{search_term}%'"

    try:
        todos = db.execute_query(query)
        return {"success": True, "todos": [dict(row) for row in todos]}
    except Exception as e:
        # VULNERABILITY: Exposing SQL errors
        return {"success": False, "error": f"Search error: {str(e)}"}


def share_todo(todo_id, shared_with_user_id, can_edit=False, user_id=None):
    """
    Share todo with another user by their user ID.

    CWE-639: IDOR - No check if user owns the todo
    """
    # VULNERABILITY: No authorization check

    # Insert share record
    query = f"""
        INSERT INTO shared_todos (todo_id, shared_with_user_id, can_edit)
        VALUES ({todo_id}, {shared_with_user_id}, {1 if can_edit else 0})
    """

    try:
        db.execute_query(query)
        return {"success": True, "message": "Todo shared successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_shared_todos(user_id):
    """
    Get todos shared with user.

    CWE-89: SQL Injection
    """
    # VULNERABILITY: SQL Injection
    query = f"""
        SELECT t.*, u.username as owner_username, st.can_edit
        FROM todos t
        JOIN shared_todos st ON t.id = st.todo_id
        JOIN users u ON t.user_id = u.id
        WHERE st.shared_with_user_id = {user_id}
    """

    try:
        todos = db.execute_query(query)
        return {"success": True, "todos": [dict(row) for row in todos]}
    except Exception as e:
        return {"success": False, "error": str(e)}


def add_file_to_todo(todo_id, filename, filepath, uploaded_by):
    """
    Add file attachment to todo.

    CWE-434: Unrestricted file upload
    CWE-639: IDOR - No authorization check
    """
    # VULNERABILITY: No check if user has access to this todo
    # VULNERABILITY: SQL Injection
    query = f"""
        INSERT INTO files (todo_id, filename, filepath, uploaded_by)
        VALUES ({todo_id}, '{filename}', '{filepath}', {uploaded_by})
    """

    try:
        db.execute_query(query)
        return {"success": True, "message": "File added"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_todo_files(todo_id):
    """
    Get files attached to todo.

    CWE-639: IDOR - Anyone can list files for any todo
    """
    # VULNERABILITY: No authorization check
    query = f"SELECT * FROM files WHERE todo_id = {todo_id}"

    try:
        files = db.execute_query(query)
        return {"success": True, "files": [dict(row) for row in files]}
    except Exception as e:
        return {"success": False, "error": str(e)}
