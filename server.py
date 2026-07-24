from http.server import HTTPServer, BaseHTTPRequestHandler
import json, os, hashlib

EMAIL = "24f2007860@ds.study.iitm.ac.in"

def solve(challenge):
    raw = f"{challenge}:{EMAIL}"
    digest = hashlib.sha256(raw.encode()).hexdigest()
    return digest[:16]

def handle_mcp(method, params, headers):
    if method == "initialize":
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "challenge-server", "version": "1.0.0"}
        }
    elif method == "notifications/initialized":
        return None
    elif method == "tools/list":
        return {
            "tools": [{
                "name": "solve_challenge",
                "description": "Solve the exam challenge from request headers.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }]
        }
    elif method == "tools/call":
        challenge = headers.get("x-exam-challenge", "")
        answer = solve(challenge)
        return {
            "content": [{"type": "text", "text": answer}]
        }
    else:
        return {}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._json(200, {"status": "ok"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        method = body.get("method", "")
        params = body.get("params", {})
        req_id = body.get("id")

        # Collect headers (lowercase keys)
        hdrs = {k.lower(): v for k, v in self.headers.items()}

        result = handle_mcp(method, params, hdrs)

        if result is None:
            # notification — no response needed but send 200
            self.send_response(200)
            self.end_headers()
            return

        response = {"jsonrpc": "2.0"}
        if req_id is not None:
            response["id"] = req_id
        response["result"] = result

        self._json(200, response)

    def _json(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"MCP server on port {port}")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
