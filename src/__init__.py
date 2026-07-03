"""
DELIBERATELY VULNERABLE FLASK APPLICATION - FOR EDUCATIONAL PURPOSES ONLY

This application contains intentional security vulnerabilities for educational purposes.
DO NOT deploy in production or expose to the internet.

Vulnerabilities demonstrated:
- SQL Injection (CWE-89)
- Cross-Site Scripting (CWE-79)
- CSRF (CWE-352)
- IDOR (CWE-639)
- Path Traversal (CWE-22)
- Command Injection (CWE-78)
- XXE (CWE-611)
- SSRF (CWE-918)
- Insecure Deserialization (CWE-502)
- Hardcoded Credentials (CWE-798)
- Weak Cryptography (CWE-327)
- Feature Flag Bypass (CWE-284)
- Feature Flag Information Disclosure (CWE-200)
And many more...
"""

from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import json

from . import config
from .models import db
from . import auth
from . import database
from . import utils
from . import feature_flags


def create_app():
    """Create and configure the Flask application."""
    # CWE-200: Templates and static files in separate web/ directory
    # Initialize Flask with custom template and static folders
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_folder = os.path.join(base_dir, 'web', 'templates')
    static_folder = os.path.join(base_dir, 'web', 'static')

    app = Flask(__name__,
                template_folder=template_folder,
                static_folder=static_folder)

    # Load configuration
    app.config.from_object(config)

    # Ensure upload directory exists
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)

    # ==================== Feature Flag Helper ====================

    def flag_enabled(feat: str, sub: str = None) -> bool:
        """
        Check whether a feature is enabled, allowing query-parameter override.

        CWE-284: Improper Access Control – any unauthenticated caller can
        re-enable a disabled feature by appending
        ``?override_flag=<feature>[.<sub_feature>]`` to any URL.  This
        bypass requires no credentials and is intentional for education.

        Parameters:
        feat (str): Top-level feature name.
        sub (str): Optional sub-feature name.

        Returns:
        bool: True if the feature should be treated as enabled.
        """
        # VULNERABILITY: No authentication/authorisation check.
        # Anyone can override any feature flag via a query parameter.
        override = request.args.get("override_flag", "")
        if override:
            expected = f"{feat}.{sub}" if sub else feat
            if override == expected or override == feat:
                # VULNERABILITY: Silently re-enables the feature for this request.
                return True

        return feature_flags.is_enabled(feat, sub)

    # ==================== Feature Flag Before-Request Hook ====================

    @app.before_request
    def log_feature_flag_override():
        """
        CWE-200: Log override attempts to stdout (information disclosure).

        The override_flag parameter value is logged without sanitisation,
        and anyone watching the server log can observe flag names in use.
        """
        override = request.args.get("override_flag")
        if override:
            # VULNERABILITY: Logs user-supplied data directly (log injection too).
            print(f"[FeatureFlags] Override requested: {override} from {request.remote_addr}")

    # ==================== Authentication Routes ====================

    @app.route('/')
    def index():
        """Home page - redirects to todos or login."""
        auth_info = auth.check_authentication()
        if auth_info['authenticated']:
            return redirect(url_for('todos_page'))
        return redirect(url_for('login_page'))

    @app.route('/login', methods=['GET'])
    def login_page():
        """Login page."""
        if not flag_enabled('authentication', 'login'):
            return "Feature disabled", 404
        return render_template('login.html')

    @app.route('/login', methods=['POST'])
    def login():
        """
        CWE-352: No CSRF protection
        CWE-287: Weak authentication
        CWE-89: SQL Injection in authentication
        """
        if not flag_enabled('authentication', 'login'):
            return "Feature disabled", 404

        username = request.form.get('username', '')
        password = request.form.get('password', '')

        result = auth.authenticate_user(username, password)

        if result['success']:
            # CWE-614: Sensitive Cookie Without 'Secure' Flag
            response = make_response(redirect(url_for('todos_page')))
            response.set_cookie('session_token', result['session_token'], httponly=False)
            return response
        else:
            # CWE-209: Information exposure through error message
            return render_template('login.html', error=result['error'])

    @app.route('/register', methods=['GET'])
    def register_page():
        """Registration page."""
        if not flag_enabled('authentication', 'register'):
            return "Feature disabled", 404
        return render_template('register.html')

    @app.route('/register', methods=['POST'])
    def register():
        """
        CWE-352: No CSRF protection
        CWE-521: Weak password requirements
        """
        if not flag_enabled('authentication', 'register'):
            return "Feature disabled", 404

        username = request.form.get('username', '')
        password = request.form.get('password', '')
        email = request.form.get('email', '')

        result = auth.register_user(username, password, email)

        if result['success']:
            return redirect(url_for('login_page'))
        else:
            return render_template('register.html', error=result['error'])

    @app.route('/logout')
    def logout():
        """Logout user."""
        session_token = request.cookies.get('session_token')
        auth.logout(session_token)

        response = make_response(redirect(url_for('login_page')))
        response.set_cookie('session_token', '', expires=0)
        return response

    # ==================== Todo Routes ====================

    @app.route('/todos')
    def todos_page():
        """
        Todo list page.
        CWE-79: XSS via unsanitized todo content
        """
        if not flag_enabled('todos', 'read'):
            return "Feature disabled", 404

        auth_info = auth.check_authentication()
        if not auth_info['authenticated']:
            return redirect(url_for('login_page'))

        user_id = auth_info['user_id']
        username = auth_info['username']

        # Get user's todos
        todos_result = database.get_user_todos(user_id)
        todos = todos_result.get('todos', [])

        # Get shared todos
        shared_result = database.get_shared_todos(user_id)
        shared_todos = shared_result.get('todos', [])

        return render_template('todos.html',
                             username=username,
                             todos=todos,
                             shared_todos=shared_todos,
                             is_admin=auth_info.get('is_admin', 0))

    @app.route('/todo/<int:todo_id>')
    def todo_detail(todo_id):
        """
        Todo detail page.
        CWE-639: IDOR - No authorization check
        CWE-79: XSS vulnerabilities
        """
        if not flag_enabled('todos', 'read'):
            return "Feature disabled", 404

        auth_info = auth.check_authentication()
        if not auth_info['authenticated']:
            return redirect(url_for('login_page'))

        # VULNERABILITY: No check if user has access to this todo
        result = database.get_todo_by_id(todo_id)
        todo = result.get('todo')

        if not todo:
            return "Todo not found", 404

        # Get files
        files_result = database.get_todo_files(todo_id)
        files = files_result.get('files', [])

        return render_template('todo_detail.html',
                             todo=todo,
                             files=files,
                             username=auth_info['username'])

    @app.route('/todo/create', methods=['POST'])
    def create_todo():
        """
        Create new todo.
        CWE-352: No CSRF protection
        CWE-89: SQL Injection
        """
        if not flag_enabled('todos', 'create'):
            return "Feature disabled", 404

        auth_info = auth.check_authentication()
        if not auth_info['authenticated']:
            return redirect(url_for('login_page'))

        title = request.form.get('title', '')
        description = request.form.get('description', '')
        priority = request.form.get('priority', 'medium')

        result = database.create_todo(auth_info['user_id'], title, description, priority)

        return redirect(url_for('todos_page'))

    @app.route('/todo/<int:todo_id>/update', methods=['POST'])
    def update_todo(todo_id):
        """
        Update todo.
        CWE-639: IDOR vulnerability
        CWE-352: No CSRF protection
        """
        if not flag_enabled('todos', 'update'):
            return "Feature disabled", 404

        auth_info = auth.check_authentication()
        if not auth_info['authenticated']:
            return redirect(url_for('login_page'))

        title = request.form.get('title')
        description = request.form.get('description')
        completed = request.form.get('completed') == 'on'
        priority = request.form.get('priority')

        # VULNERABILITY: No check if user owns this todo
        database.update_todo(todo_id, title, description, completed, priority)

        return redirect(url_for('todo_detail', todo_id=todo_id))

    @app.route('/todo/<int:todo_id>/delete', methods=['POST'])
    def delete_todo(todo_id):
        """
        Delete todo.
        CWE-639: IDOR - Any user can delete any todo
        """
        if not flag_enabled('todos', 'delete'):
            return "Feature disabled", 404

        auth_info = auth.check_authentication()
        if not auth_info['authenticated']:
            return redirect(url_for('login_page'))

        # VULNERABILITY: No authorization check
        database.delete_todo(todo_id)

        return redirect(url_for('todos_page'))

    @app.route('/search')
    def search():
        """
        Search todos.
        CWE-89: SQL Injection via search parameter
        """
        if not flag_enabled('search'):
            return "Feature disabled", 404

        auth_info = auth.check_authentication()
        if not auth_info['authenticated']:
            return redirect(url_for('login_page'))

        user_id = auth_info['user_id']
        search_term = request.args.get('q', '')

        if search_term:
            result = database.search_todos(user_id, search_term)
            todos = result.get('todos', [])
            error = result.get('error')
        else:
            todos = []
            error = None

        return render_template('search.html',
                             search_term=search_term,
                             todos=todos,
                             error=error,
                             username=auth_info['username'])

    # ==================== File Upload Routes ====================

    @app.route('/upload')
    def upload_page():
        """
        File upload landing page.
        Redirects authenticated users to todos, unauthenticated users to login.
        """
        auth_info = auth.check_authentication()
        if not auth_info['authenticated']:
            return redirect(url_for('login_page'))
        return redirect(url_for('todos_page'))

    @app.route('/todo/<int:todo_id>/upload', methods=['POST'])
    def upload_file(todo_id):
        """
        Upload file attachment.
        CWE-434: Unrestricted file upload
        CWE-22: Path traversal possible
        """
        if not flag_enabled('files', 'upload'):
            return "Feature disabled", 404

        auth_info = auth.check_authentication()
        if not auth_info['authenticated']:
            return redirect(url_for('login_page'))

        if 'file' not in request.files:
            return redirect(url_for('todo_detail', todo_id=todo_id))

        file = request.files['file']
        if file.filename == '':
            return redirect(url_for('todo_detail', todo_id=todo_id))

        # VULNERABILITY: No file validation, no filename sanitization
        filename = file.filename  # Should use secure_filename()
        result = utils.save_uploaded_file(file, filename)
        filepath = result['filepath']

        # Add file to database
        database.add_file_to_todo(todo_id, filename, filepath, auth_info['user_id'])

        return redirect(url_for('todo_detail', todo_id=todo_id))

    @app.route('/file/<path:filename>')
    def download_file(filename):
        """
        Download file.
        CWE-22: Path traversal vulnerability
        """
        if not flag_enabled('files', 'download'):
            return "Feature disabled", 404

        # VULNERABILITY: No path validation - allows ../../../etc/passwd
        try:
            file_path = os.path.join(config.UPLOAD_FOLDER, filename)
            return send_file(file_path)
        except Exception as e:
            return f"Error: {str(e)}", 404

    # ==================== API Routes ====================

    @app.route('/api/todos', methods=['GET', 'POST'])
    def api_get_todos():
        """
        API endpoint to get or create todos.
        CWE-306: Missing authentication
        """
        if not flag_enabled('api', 'todos'):
            return jsonify({"error": "Feature disabled"}), 404

        if request.method == 'POST':
            # VULNERABILITY: No authentication
            data = request.get_json() or request.form
            user_id = data.get('user_id', 1)
            title = data.get('title', '')
            description = data.get('description', '')
            priority = data.get('priority', 'medium')
            result = database.create_todo(user_id, title, description, priority)
            return jsonify(result)

        # VULNERABILITY: No authentication required
        user_id = request.args.get('user_id', 1)
        result = database.get_user_todos(user_id)
        return jsonify(result)

    @app.route('/api/todo/<int:todo_id>', methods=['GET'])
    def api_get_todo(todo_id):
        """
        API endpoint to get single todo.
        CWE-639: IDOR vulnerability
        """
        if not flag_enabled('api', 'todos'):
            return jsonify({"error": "Feature disabled"}), 404

        # VULNERABILITY: No authentication or authorization
        result = database.get_todo_by_id(todo_id)
        return jsonify(result)

    @app.route('/api/todo/create', methods=['POST'])
    def api_create_todo():
        """
        API endpoint to create todo.
        CWE-352: No CSRF protection
        CWE-306: Missing authentication
        """
        if not flag_enabled('api', 'todos'):
            return jsonify({"error": "Feature disabled"}), 404

        # VULNERABILITY: No authentication
        data = request.get_json() or request.form
        user_id = data.get('user_id', 1)
        title = data.get('title', '')
        description = data.get('description', '')
        priority = data.get('priority', 'medium')

        result = database.create_todo(user_id, title, description, priority)
        return jsonify(result)

    # ==================== Admin Routes ====================

    @app.route('/admin')
    def admin_page():
        """
        Admin page.
        CWE-863: Incorrect authorization
        """
        if not flag_enabled('admin', 'panel'):
            return "Feature disabled", 404

        auth_info = auth.check_authentication()

        # VULNERABILITY: Weak admin check
        if not auth_info.get('authenticated') or not auth_info.get('is_admin'):
            return "Access denied", 403

        # Get all users (SQL injection possible)
        query = "SELECT id, username, email, is_admin, created_at FROM users"
        users = db.execute_query(query)

        return render_template('admin.html',
                             users=[dict(u) for u in users],
                             username=auth_info['username'])

    @app.route('/admin/execute', methods=['POST'])
    def admin_execute_command():
        """
        Admin command execution.
        CWE-78: OS Command Injection
        """
        if not flag_enabled('admin', 'command_execution'):
            return jsonify({"error": "Feature disabled"}), 404

        auth_info = auth.check_authentication()
        if not auth_info.get('is_admin'):
            return jsonify({"error": "Access denied"}), 403

        command = request.form.get('command', '')

        # VULNERABILITY: Command injection
        result = utils.run_system_command(command)

        return jsonify({"output": result})

    # ==================== Utility Routes ====================

    @app.route('/fetch-url', methods=['POST'])
    def fetch_url_route():
        """
        Fetch external URL.
        CWE-918: SSRF vulnerability
        """
        if not flag_enabled('utilities', 'ssrf'):
            return jsonify({"error": "Feature disabled"}), 404

        url = request.form.get('url', '')

        # VULNERABILITY: SSRF - No URL validation
        result = utils.fetch_url(url)

        return jsonify(result)

    @app.route('/import-xml', methods=['POST'])
    def import_xml():
        """
        Import todos from XML.
        CWE-611: XXE vulnerability
        """
        if not flag_enabled('utilities', 'xxe'):
            return jsonify({"error": "Feature disabled"}), 404

        auth_info = auth.check_authentication()
        if not auth_info['authenticated']:
            return jsonify({"error": "Not authenticated"}), 401

        xml_data = request.form.get('xml', '')

        # VULNERABILITY: XXE attack possible
        root = utils.parse_xml(xml_data)

        if isinstance(root, str):
            return jsonify({"error": root})

        return jsonify({"success": True, "message": "XML parsed successfully"})

    # ==================== Feature Flag Routes ====================

    @app.route('/api/features', methods=['GET'])
    def api_get_features():
        """
        Return all current feature flag values.

        CWE-200: Information Disclosure – this endpoint requires no
        authentication and exposes the full feature flag configuration.
        An attacker can use this to discover which vulnerability demos are
        active and plan targeted exploits.  Restrict to admins in real apps.
        """
        # VULNERABILITY: No authentication check.
        all_flags = feature_flags.get_all_flags()
        return jsonify({"features": all_flags})

    # ==================== Error Handlers ====================

    @app.errorhandler(404)
    def not_found(e):
        """CWE-209: Information exposure in error messages."""
        return f"404 Not Found: {request.url}", 404

    @app.errorhandler(500)
    def server_error(e):
        """CWE-209: Detailed error messages expose system information."""
        return f"500 Internal Server Error: {str(e)}", 500

    return app
