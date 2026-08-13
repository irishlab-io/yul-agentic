#!/usr/bin/env python
"""
TODO APPLICATION ENTRY POINT
This application currently carries unremediated security weaknesses.
Do not expose it to the internet while they remain open.
"""

from src import create_app

if __name__ == "__main__":
    app = create_app()
    # CWE-489: Debug mode enabled in production
    # This exposes sensitive debug information and the Werkzeug debugger
    app.run(host="0.0.0.0", port=8000, debug=True)
