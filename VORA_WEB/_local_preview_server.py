import http.server
import json
import os
import urllib.parse

os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open("vercel.json", encoding="utf-8") as f:
    config = json.load(f)

REWRITES = {r["source"]: r["destination"] for r in config.get("rewrites", [])}
REDIRECTS = {r["source"]: r["destination"] for r in config.get("redirects", [])}


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path = urllib.parse.unquote(self.path.split("?")[0])

        if path in REDIRECTS:
            self.send_response(301)
            self.send_header("Location", REDIRECTS[path])
            self.end_headers()
            return

        if path in REWRITES:
            self.path = urllib.parse.quote(REWRITES[path])
            return super().do_GET()

        return super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    port = 8765
    print(f"Serving with vercel.json rewrites on http://localhost:{port}")
    http.server.HTTPServer(("localhost", port), Handler).serve_forever()
