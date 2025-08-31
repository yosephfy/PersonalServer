from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict

from . import config
from .commands import run_command, run_commands
from .scraper import fetch_url, html_to_text
from .storage import save_note, save_scrape, save_transaction, save_weight


class Handler(BaseHTTPRequestHandler):
    server_version = "PersonalServer/0.1"

    def log_message(self, fmt, *args):
        # Lean logging
        return super().log_message(fmt, *args)

    # Routing
    def do_GET(self):
        if self.path.startswith("/ping"):
            return self._json({"ok": True, "message": "pong"})
        return self._json({"ok": False, "error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self):
        try:
            body = self._json_body()
        except Exception as e:
            return self._json({"ok": False, "error": f"Invalid JSON: {e}"}, status=HTTPStatus.BAD_REQUEST)

        if self.path.startswith("/run"):
            timeout = body.get("timeout")
            cwd = body.get("cwd")

            # Accept single string or list of commands
            commands = None
            if isinstance(body.get("cmds"), list):
                commands = body.get("cmds")
            elif isinstance(body.get("commands"), list):
                commands = body.get("commands")
            elif isinstance(body.get("cmd"), list):
                commands = body.get("cmd")

            if commands is not None:
                # sequential execution of multiple commands
                stop_on_error = bool(body.get("stop_on_error", False))
                # coerce all entries to strings
                commands = [str(c) for c in commands]
                agg = run_commands(commands, timeout=timeout, cwd=cwd, stop_on_error=stop_on_error)
                return self._json(agg)

            # Fallback: single command string
            cmd = body.get("cmd") or body.get("command")
            if not cmd or not str(cmd).strip():
                return self._json({"ok": False, "error": "Missing 'cmd' or 'cmds'"}, status=HTTPStatus.BAD_REQUEST)
            result = run_command(str(cmd), timeout=timeout, cwd=cwd)
            return self._json(result)

        if self.path.startswith("/notes"):
            title = (body.get("title") or "").strip()
            content = body.get("content") or ""
            tags = body.get("tags")
            if not title:
                return self._json({"ok": False, "error": "Missing 'title'"}, status=HTTPStatus.BAD_REQUEST)
            rec = save_note(title=title, content=content, tags=",".join(tags) if isinstance(tags, list) else tags)
            return self._json({"ok": True, "note": rec.__dict__})

        if self.path.startswith("/transactions"):
            rec = save_transaction(body)
            return self._json({"ok": True, "transaction": rec.__dict__})

        if self.path.startswith("/scrape"):
            url = body.get("url")
            if not url:
                return self._json({"ok": False, "error": "Missing 'url'"}, status=HTTPStatus.BAD_REQUEST)
            try:
                final_url, html_text, title = fetch_url(url)
                text = html_to_text(html_text)
                rec = save_scrape(final_url, html_text, text, title)
                return self._json({"ok": True, "scrape": rec.__dict__})
            except Exception as e:
                return self._json({"ok": False, "error": f"Scrape failed: {e}"}, status=HTTPStatus.BAD_GATEWAY)

        if self.path.startswith("/weights"):
            rec = save_weight(body)
            return self._json({"ok": True, "weight": rec.__dict__})

        return self._json({"ok": False, "error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    # Helpers
    def _json_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            # allow form-ish single field bodies like cmd=ls
            try:
                s = raw.decode("utf-8")
                if "=" in s and "{" not in s:
                    return {k: v for k, v in (pair.split("=", 1) for pair in s.split("&"))}
            except Exception:
                pass
            raise

    def _json(self, obj: Dict[str, Any], status: int = 200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def run_server(host: str | None = None, port: int | None = None):
    server = ThreadingHTTPServer((host or config.DEFAULT_HOST, port or config.DEFAULT_PORT), Handler)
    try:
        print(f"PersonalServer running on http://{server.server_address[0]}:{server.server_address[1]}")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.server_close()
