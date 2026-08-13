# TODO APPLICATION — SECURITY REMEDIATION BACKLOG

This is a Flask web application carrying a large backlog of known security weaknesses, representing OWASP Top 10 categories and various CWEs (Common Weakness Enumerations). They are being remediated issue by issue through this repository's agentic workflow pipeline.

## 🚨 CURRENT STATE 🚨

**THIS APPLICATION IS CURRENTLY VULNERABLE — REMEDIATION IS IN PROGRESS.**

- ✅ **DO** work through [VULNERABILITIES.md](docs/VULNERABILITIES.md) — it is the remediation backlog
- ✅ **DO** open an issue for any weakness you find, catalogued or not
- ✅ **DO** run it in an isolated environment (local VM, air-gapped network) while weaknesses remain open

## 📚 Scope of the backlog

The open weaknesses cover:
- **14+ types of vulnerabilities** including SQL Injection, XSS, CSRF, IDOR, Path Traversal, Command Injection, XXE, SSRF, and more
- **Vulnerable dependencies** using outdated packages with known CVEs
- **Insecure Docker configuration** with multiple container security issues
- **Poor security practices** in authentication, session management, and data handling

## 🎯 Features

The vulnerable todo list application includes:
- User registration and authentication (currently weak — see the backlog)
- Create, read, update, and delete todos
- Share todos with other users
- File upload and download
- Search functionality
- Admin panel with system command execution
- REST API endpoints
- XML import/export

## 🔧 Prerequisites

- Python 3.11+ (currently pinned to a pre-release version — an open item in the backlog)
- `uv` package manager
- Docker and Docker Compose (for containerized deployment)

## 📦 Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd yul-agentic/main
   ```

2. **Set up Python environment**
   ```bash
   # Using uv package manager
   uv venv .venv --python 3.11
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   # Install dependencies
   uv pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python run.py
   ```

4. **Access the application**
   - Open browser to: `http://localhost:8000`
   - Default admin credentials: `admin / admin`

### Docker Deployment

**WARNING**: The Dockerfile is currently insecure — see the container items in the backlog.

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access at http://localhost:8000
```

## 🐛 Open Weaknesses

The following weaknesses are currently open (see [VULNERABILITIES.md](docs/VULNERABILITIES.md) for full detail, including how to fix each one):

### Application-Level Vulnerabilities

1. **SQL Injection (CWE-89)** - Raw SQL queries with string concatenation
2. **Cross-Site Scripting (CWE-79)** - Unsanitized user input rendering
3. **Cross-Site Request Forgery (CWE-352)** - No CSRF tokens
4. **Insecure Direct Object References (CWE-639)** - Missing authorization checks
5. **Path Traversal (CWE-22)** - Unvalidated file paths
6. **OS Command Injection (CWE-78)** - Unsafe system calls
7. **XML External Entity (CWE-611)** - Unsafe XML parsing
8. **Server-Side Request Forgery (CWE-918)** - Unvalidated URL fetching
9. **Insecure Deserialization (CWE-502)** - Pickle for session data
10. **Hardcoded Credentials (CWE-798)** - Secrets in source code
11. **Weak Cryptography (CWE-327)** - MD5 for password hashing
12. **Information Disclosure (CWE-200)** - Detailed error messages
13. **Missing Authentication (CWE-306)** - Unprotected API endpoints
14. **Unrestricted File Upload (CWE-434)** - No file type validation

### Dependency Vulnerabilities

Currently pinned to outdated packages:
- Flask 2.2.5 (CVE-2023-30861, CVE-2023-25577)
- SQLAlchemy 1.4.46 (CVE-2023-46695)
- Jinja2 3.0.3 (CVE-2024-22195)
- PyYAML 5.4 (CVE-2020-14343)
- requests 2.27.1 (CVE-2023-32681)
- Pillow 9.3.0 (CVE-2023-44271)

### Docker/Container Vulnerabilities

- Using Python 3.11.0a1 pre-release image (not production ready)
- Running as root user
- Hardcoded secrets in environment variables
- Privileged mode enabled
- Mounting Docker socket
- No resource limits
- Overly permissive file permissions

## 🎓 Working the Backlog

### Remediation loop

1. **Identify**: Pick a weakness from the backlog, or find one not yet catalogued
2. **Reproduce**: Confirm it is exploitable (in an isolated environment only!)
3. **Understand**: Read the `# VULNERABILITY:` markers and surrounding code to size the blast radius
4. **Fix**: Remediate it, leaving no equivalent bypass beside it
5. **Test**: Verify the fix holds and nothing else broke

### Suggested Exercises

- Exploit SQL injection in login, search, and todo operations
- Perform XSS attacks via todo titles and descriptions
- Bypass authentication using SQL injection or the backdoor
- Access other users' todos via IDOR
- Upload malicious files and execute them
- Perform path traversal to read system files
- Execute system commands via command injection
- Perform SSRF to access internal resources
- Extract data using XXE attacks

## 📖 File Structure

```
/home/irish/git/irishlab-io/yul-agentic/main/
├── src/                          # Python source code only
│   ├── __init__.py          # Main Flask application
│   ├── config/              # Configuration directory
│   │   └── config.py        # Configuration (hardcoded secrets)
│   ├── models.py            # Database models and operations
│   ├── auth.py              # Authentication (weak)
│   ├── database.py          # Todo operations (vulnerable)
│   └── utils.py             # Utility functions (dangerous)
├── web/                          # Web assets (non-code)
│   ├── templates/           # HTML templates (XSS vulnerable)
│   └── static/              # CSS and JavaScript
├── uploads/                      # File upload directory
├── data/                         # SQLite database location
├── requirements.txt             # Vulnerable dependencies
├── Dockerfile                   # Insecure container image
├── compose.yml                  # Vulnerable Docker Compose config
├── run.py                       # Application entry point
└── VULNERABILITIES.md           # Detailed vulnerability documentation
```

## 🛡️ Security Best Practices (What NOT to do)

This application violates many security best practices. **DO THE OPPOSITE** in real applications:

### ❌ DON'T (as shown in this app)
- Use string concatenation for SQL queries
- Render user input without sanitization
- Store passwords with MD5 or weak hashing
- Hardcode credentials in source code
- Run applications as root
- Disable CSRF protection
- Skip input validation
- Use `pickle` for untrusted data
- Enable debug mode in production
- Expose detailed error messages
- Use outdated dependencies with known CVEs

### ✅ DO (in real applications)
- Use parameterized queries or ORM
- Sanitize and escape all user input
- Use bcrypt, argon2, or scrypt for passwords
- Store secrets in environment variables or secret managers
- Run with least privileges (non-root user)
- Implement CSRF protection
- Validate all inputs (whitelist approach)
- Use JSON for serialization
- Disable debug mode in production
- Use generic error messages
- Keep dependencies updated

## 📚 Resources

### Learn More About Security

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE (Common Weakness Enumeration)](https://cwe.mitre.org/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security.html)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)

### Similar Educational Projects

- [OWASP WebGoat](https://owasp.org/www-project-webgoat/)
- [DVWA (Damn Vulnerable Web Application)](https://github.com/digininja/DVWA)
- [OWASP Juice Shop](https://owasp.org/www-project-juice-shop/)

## 🧪 Testing

Each vulnerability should be tested to ensure it's actually exploitable:

```bash
# Test SQL injection in login
# Try username: admin' OR '1'='1
# Try password: anything

# Test XSS in todo title
# Create todo with title: <script>alert('XSS')</script>

# Test path traversal
# Try downloading: /file/../../etc/passwd

# Test command injection (admin panel)
# Try command: whoami; cat /etc/passwd

# Test IDOR
# Access /todo/1, /todo/2, etc. with different user accounts
```

## 📝 License

This project is provided as-is. See LICENSE file for details.

## 🤝 Contributing

If you find a weakness that is not yet catalogued, or want to take on an open backlog item, please open an issue or pull request.

## ⚖️ Legal and Ethical Disclaimer

- This software has known, unremediated weaknesses
- Only run it in **isolated, controlled environments**
- Never use against systems you don't own or have permission to test
- The authors are not responsible for misuse of this software
- Understand the legal implications of security testing in your jurisdiction

## 📞 Contact

For questions about this project, please open an issue in the repository.

---

**Remember: The best way to build secure applications is to understand how they can be broken!** 🔒
