"""
Vercel Python entrypoint.
Serves the standalone 100 Apps Research Case Study dashboard.
Supports ASGI, WSGI, and BaseHTTPRequestHandler runtimes on Vercel.
"""

import os
from http.server import BaseHTTPRequestHandler

HTML_FILE = os.path.join(os.path.dirname(__file__), "index.html")

def get_html_bytes():
    if os.path.exists(HTML_FILE):
        with open(HTML_FILE, "rb") as f:
            return f.read()
    alt_file = os.path.join(os.path.dirname(__file__), "web", "index.html")
    if os.path.exists(alt_file):
        with open(alt_file, "rb") as f:
            return f.read()
    return b"<h1>Dashboard not found</h1>"

# 1. BaseHTTPRequestHandler for Vercel Serverless
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        content = get_html_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

# 2. ASGI application entrypoint for Vercel ASGI
async def app(scope, receive, send):
    if scope["type"] == "http":
        content = get_html_bytes()
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [
                [b"content-type", b"text/html; charset=utf-8"],
                [b"content-length", str(len(content)).encode("utf-8")],
            ],
        })
        await send({
            "type": "http.response.body",
            "body": content,
        })

# 3. WSGI application entrypoint for Vercel WSGI
def application(environ, start_response):
    content = get_html_bytes()
    status = "200 OK"
    headers = [
        ("Content-type", "text/html; charset=utf-8"),
        ("Content-Length", str(len(content)))
    ]
    start_response(status, headers)
    return [content]

if __name__ == "__main__":
    from http.server import HTTPServer
    server = HTTPServer(("0.0.0.0", 8000), handler)
    print("Serving on http://localhost:8000")
    server.serve_forever()
