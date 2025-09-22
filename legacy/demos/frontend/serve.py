#!/usr/bin/env python3
"""
Simple HTTP server for the Claude SDK Server frontend.
Serves the dashboard on http://localhost:3000
"""

import http.server
import os
import socketserver
import sys
from pathlib import Path

PORT = 3000
DIRECTORY = Path(__file__).parent


class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Add CORS headers for development
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        super().end_headers()

    def do_GET(self):
        if self.path == "/":
            self.path = "/index.html"
        return super().do_GET()


def main():
    os.chdir(DIRECTORY)

    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║     🚀 Claude SDK Server - Live Dashboard                 ║
║                                                            ║
║     Frontend running at: http://localhost:{PORT}            ║
║                                                            ║
║     Make sure the API server is running:                  ║
║     $ make up                                              ║
║                                                            ║
║     Press Ctrl+C to stop                                  ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
        """)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Shutting down frontend server...")
            sys.exit(0)


if __name__ == "__main__":
    main()
