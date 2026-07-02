# DELIBERATELY VULNERABLE DOCKERFILE - FOR EDUCATIONAL PURPOSES ONLY
# This Dockerfile contains intentional security vulnerabilities for teaching purposes.
# DO NOT use in production!

# CWE-1104: Use of Unmaintained Third Party Components
# VULNERABILITY: Using Python 3.11 base image without security patches
# Using an older minor version demonstrates the risk of not keeping up with patches
# Known issues: May contain security vulnerabilities from older Python releases
FROM python:3.11-slim

# VULNERABILITY: Using ADD instead of COPY (ADD has additional features that can be exploited)
# Best practice: Use COPY for local files
LABEL maintainer="vulnerable@example.com" \
      description="Deliberately vulnerable todo application for education" \
      version="0.1.0"

# CWE-798: Hardcoded credentials in Dockerfile
# VULNERABILITY: Exposing secrets as environment variables
ENV DATABASE_PASSWORD="insecure_password123" \
    SECRET_KEY="my-super-secret-key-12345" \
    API_KEY="hardcoded-api-key-xyz" \
    ADMIN_PASSWORD="admin"

# CWE-489: Debug mode enabled
ENV DEBUG=True \
    FLASK_ENV=development

# Feature flags configuration (CWE-22: path not validated inside the app)
# Override with -e FEATURE_FLAGS_FILE=/path/to/custom_flags.yml
# or mount a custom file at /app/feature_flags.yml
ENV FEATURE_FLAGS_FILE=/app/feature_flags.yml

WORKDIR /app

# VULNERABILITY: Not pinning package manager versions
# This can lead to supply chain attacks
# Install build dependencies for Python packages
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    vim \
    netcat-openbsd \
    telnet \
    gcc \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# VULNERABILITY: Using ADD with remote URL (can be exploited)
# ADD automatically extracts archives which can be dangerous
ADD . /app/

# VULNERABILITY: Installing packages without hash verification
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# VULNERABILITY: Installing additional vulnerable packages
RUN pip install --no-cache-dir \
    httplib2==0.9.2 \
    urllib3==1.24.3 \
    paramiko==1.16.0

# CWE-250: Execution with Unnecessary Privileges
# VULNERABILITY: Running as root user (no USER directive)
# Best practice: Always use a non-root user

# CWE-200: Information Disclosure
# VULNERABILITY: Exposing unnecessary ports
EXPOSE 8000 8080 3000 5000 9000

# VULNERABILITY: No healthcheck (would help detect compromised container)
# Commented out intentionally:
# HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8000/ || exit 1

# CWE-732: Incorrect Permission Assignment
# VULNERABILITY: Setting overly permissive file permissions
RUN chmod -R 777 /app

# VULNERABILITY: Leaving build cache and temporary files
# No cleanup of apt cache, pip cache, or temporary files

# Create directories with insecure permissions
RUN mkdir -p /app/uploads /app/data && \
    chmod 777 /app/uploads && \
    chmod 777 /app/data

# VULNERABILITY: Using shell form of CMD (can lead to unexpected behavior)
# Best practice: Use exec form CMD ["executable", "param1", "param2"]
CMD python run.py

# Educational notes:
# 1. Using EOL Python 3.6 (CVE-2021-29921, CVE-2021-23336, etc.)
# 2. Running as root user
# 3. Hardcoded secrets in environment variables
# 4. Overly permissive file permissions (777)
# 5. Using ADD instead of COPY
# 6. No health checks
# 7. Exposing unnecessary ports
# 8. No multi-stage build (larger attack surface)
# 9. Installing unnecessary tools (curl, wget, vim, netcat)
# 10. Debug mode enabled
# 11. No image scanning or vulnerability checks
# 12. Using shell form of CMD
# 13. Not using specific package versions (except vulnerable ones)
# 14. No .dockerignore to exclude sensitive files
