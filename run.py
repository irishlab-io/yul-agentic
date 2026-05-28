#!/usr/bin/env python
"""
DELIBERATELY VULNERABLE APPLICATION - FOR EDUCATIONAL PURPOSES ONLY
This application contains intentional security vulnerabilities.
DO NOT deploy in production or expose to the internet.
"""

from src import create_app

if __name__ == "__main__":
    app = create_app()
    # CWE-489: Debug mode enabled in production
    # This exposes sensitive debug information and the Werkzeug debugger
    app.run(host="0.0.0.0", port=8000, debug=True)
