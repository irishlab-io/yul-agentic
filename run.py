#!/usr/bin/env python
"""
TODO APPLICATION ENTRY POINT
This application currently carries unremediated security weaknesses.
Do not expose it to the internet while they remain open.
"""

from src import create_app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8000, debug=app.config.get("DEBUG", False))
