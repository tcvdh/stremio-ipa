"""Rewrite Stremio's AltStore source so downloadURL points straight at the IPA.

python stremio.py            -> write source.json
python stremio.py serve 8080 -> serve it live at http://host:8080/
"""
import json
import sys
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

SOURCE = "https://dl.strem.io/apple/altstore/source.json"
IPA = "https://dl.strem.io/apple/{version}b{buildVersion}/ios/stremio_iOS.ipa"


def build():
    with urllib.request.urlopen(SOURCE, timeout=30) as r:
        src = json.load(r)
    for app in src["apps"]:
        for v in app["versions"]:
            url = IPA.format(**v)
            try:
                head = urllib.request.Request(url, method="HEAD")
                with urllib.request.urlopen(head, timeout=30) as r:
                    v["size"] = int(r.headers["Content-Length"])
                v["downloadURL"] = url
            except Exception as e:  # IPA missing: keep the original entry
                print(f"skip {url}: {e}", file=sys.stderr)
    return json.dumps(src, indent=2).encode()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            body, code = build(), 200
        except Exception as e:
            body, code = str(e).encode(), 502
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    if sys.argv[1:2] == ["serve"]:
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
        HTTPServer(("", port), Handler).serve_forever()
    else:
        open("source.json", "wb").write(build())
