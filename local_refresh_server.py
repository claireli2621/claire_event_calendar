"""
Local refresh bridge for Claire assistant.

Lets the GitHub Pages form buttons directly trigger Claude (running on this
machine) to refresh weather / traffic / VIP bio for an event.

Usage:
    python local_refresh_server.py

Listens on http://127.0.0.1:8787. Only binds to loopback so other machines
on the network cannot reach it.

POST /refresh
Body: {"type": "weather|traffic|bio|all-weather|all-traffic|all-bio",
       "event_id": "...", "event_name": "...", "name": "..."}
Response: {"ok": true, "output": "..."} or {"ok": false, "error": "..."}
"""

import json
import subprocess
import sys
import os
import time
import threading
import http.server

CLAUDE_EXE = r"C:\Users\limiao.CMIT\AppData\Local\NiuClaude\bin\claude.exe"
PROJECT_DIR = r"C:\Users\limiao.CMIT\OneDrive - 神州网信技术有限公司\06 乾元\Claire_assistant"
PORT = 8787

# Each task type maps to a function that builds the trigger phrase from the body.
def build_phrase(body):
    t = (body.get("type") or "").strip()
    event_id = (body.get("event_id") or "").strip()
    event_name = (body.get("event_name") or "").strip()
    name = (body.get("name") or "").strip()

    if t == "weather":
        if event_name:
            return "刷新 " + event_name + " 的天气"
        if event_id:
            return "刷新 " + event_id + " 的天气"
        return "刷新天气"
    if t == "traffic":
        if event_name:
            return "刷新 " + event_name + " 的交通"
        if event_id:
            return "刷新 " + event_id + " 的交通"
        return "刷新交通"
    if t == "bio":
        if name:
            return "刷新 " + name + " 简介"
        if event_id:
            return "刷新 " + event_id + " 所有待员简介"
        return "刷新所有要员简介"
    if t == "all-weather":
        return "刷新所有活动的天气"
    if t == "all-traffic":
        return "刷新所有活动的交通"
    if t == "all-bio":
        return "刷新所有要员简介"
    if t == "all":
        return "刷新所有活动的天气、交通和要员简介"
    raise ValueError("unknown type: " + repr(t))


def run_claude(phrase):
    """Run claude.exe -p with the trigger phrase; return (ok, output)."""
    if not os.path.exists(CLAUDE_EXE):
        return False, "claude.exe not found at " + CLAUDE_EXE
    # NiuClaude redirects Claude's profile to C:\Users\<user>\NiuClaude. When
    # this server is launched via .bat from the desktop, USERPROFILE points to
    # the real Windows profile (C:\Users\<user>) and Claude can't find its auth
    # file there — fails in ~1s. Force the env vars to point at NiuClaude.
    env = os.environ.copy()
    niu = r"C:\Users\limiao.CMIT\NiuClaude"
    if os.path.isdir(niu):
        env["USERPROFILE"] = niu
        env["HOME"] = niu
    try:
        proc = subprocess.run(
            [CLAUDE_EXE, "-p", "--dangerously-skip-permissions", phrase],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
            env=env,
        )
        out = (proc.stdout or "") + ("\n[stderr]\n" + proc.stderr if proc.stderr else "")
        if proc.returncode != 0:
            return False, "claude exit " + str(proc.returncode) + "\n" + out
        return True, out
    except subprocess.TimeoutExpired:
        return False, "claude timed out (>600s)"
    except Exception as e:
        return False, "claude invocation failed: " + repr(e)


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        sys.stdout.write("[%s] %s - %s\n" % (ts, self.address_string(), fmt % args))
        sys.stdout.flush()

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "https://claireli2621.github.io")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._json(200, {"ok": True})

    def do_GET(self):
        if self.path == "/ping":
            self._json(200, {"ok": True, "service": "claire-local-refresh"})
            return
        self._json(404, {"ok": False, "error": "unknown path: " + self.path})

    def do_POST(self):
        # Wrap everything in a try/except so unexpected errors get logged and
        # returned as JSON, not swallowed by BaseHTTPRequestHandler (which
        # would send an empty 500 with no diagnostic).
        try:
            self._handle_post()
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            sys.stdout.write("[%s] UNHANDLED EXCEPTION in do_POST:\n%s\n" % (ts, tb))
            sys.stdout.flush()
            try:
                self._json(500, {"ok": False, "error": repr(e), "traceback": tb[:2000]})
            except Exception:
                pass  # connection may already be broken

    def _handle_post(self):
        if self.path != "/refresh":
            self._json(404, {"ok": False, "error": "unknown path: " + self.path})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length > 0 else b"{}"
            body = json.loads(raw.decode("utf-8") or "{}")
        except Exception as e:
            self._json(400, {"ok": False, "error": "bad json: " + repr(e)})
            return
        try:
            phrase = build_phrase(body)
        except ValueError as e:
            self._json(400, {"ok": False, "error": str(e)})
            return

        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        sys.stdout.write("[%s] REFRESH type=%s phrase=%r\n" % (ts, body.get("type"), phrase))
        sys.stdout.flush()

        # Run synchronously — the page will await the response.
        ok, output = run_claude(phrase)
        ts2 = time.strftime("%Y-%m-%d %H:%M:%S")
        sys.stdout.write("[%s] CLAUDE DONE ok=%s out_len=%d\n" % (ts2, ok, len(output or "")))
        sys.stdout.flush()
        summary = (output or "").strip()
        if len(summary) > 2000:
            summary = summary[:2000] + "\n...(truncated)"
        self._json(200 if ok else 500, {"ok": ok, "phrase": phrase, "output": summary})


def main():
    server = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
    print("=" * 60)
    print("Claire local refresh server")
    print("Listening on http://127.0.0.1:%d" % PORT)
    print("Project dir: %s" % PROJECT_DIR)
    print("Claude exe:  %s" % CLAUDE_EXE)
    print("Allowed origin: https://claireli2621.github.io")
    print("Press Ctrl+C to stop.")
    print("=" * 60)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
