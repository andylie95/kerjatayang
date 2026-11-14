"""Wander Atlas - desktop launcher.

Serves the app from this computer, opens it in the default browser and keeps
the travel log in a file in the user's data folder.

Run with:  python wander_atlas.py
Needs only the Python standard library (Python 3.8+).
"""
import argparse
import functools
import json
import os
import sys
import threading
import urllib.request
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

APP_NAME = "Wander Atlas"
APP_ID = "wander-atlas"
DEFAULT_PORT = 47615
MAX_BODY = 5 * 1024 * 1024


def web_dir():
    # PyInstaller unpacks bundled files to sys._MEIPASS
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / "web"


def data_dir():
    override = os.environ.get("WANDER_ATLAS_DATA")
    if override:
        return Path(override)
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "WanderAtlas"


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".js": "text/javascript",
        ".html": "text/html; charset=utf-8",
    }
    state_file = None
    lock = threading.Lock()

    def log_message(self, *args):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def _trusted(self):
        # Only this app's own page may talk to the API, not other websites.
        port = self.server.server_address[1]
        hosts = {"127.0.0.1:%d" % port, "localhost:%d" % port}
        if self.headers.get("Host") not in hosts:
            return False
        origin = self.headers.get("Origin")
        return origin is None or origin in {"http://" + h for h in hosts}

    def _json(self, status, payload):
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if not path.startswith("/api/"):
            return super().do_GET()
        if not self._trusted():
            return self._json(403, {"error": "forbidden"})
        if path == "/api/ping":
            return self._json(200, {"app": APP_ID})
        if path == "/api/state":
            with self.lock:
                try:
                    body = self.state_file.read_bytes()
                    json.loads(body)
                except (OSError, ValueError):
                    body = b"{}"
            return self._json(200, body)
        return self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/api/state":
            return self._json(404, {"error": "not found"})
        if not self._trusted() or not self.headers.get("Content-Type", "").startswith("application/json"):
            return self._json(403, {"error": "forbidden"})
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            return self._json(411, {"error": "length required"})
        if length < 0 or length > MAX_BODY:
            return self._json(413, {"error": "too large"})
        try:
            state = json.loads(self.rfile.read(length))
        except ValueError:
            state = None
        if not isinstance(state, dict):
            return self._json(400, {"error": "invalid data"})
        with self.lock:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.state_file.with_name(self.state_file.name + ".tmp")
            tmp.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, self.state_file)
        return self._json(200, {"ok": True})


class Server(ThreadingHTTPServer):
    daemon_threads = True
    # On Windows, address reuse would let two programs share the same port.
    allow_reuse_address = sys.platform != "win32"


def already_running(port):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open("http://127.0.0.1:%d/api/ping" % port, timeout=1) as res:
            return json.load(res).get("app") == APP_ID
    except Exception:
        return False


def control_window(url):
    """Small window with Open and Quit buttons. Returns False if no GUI is available."""
    try:
        import tkinter as tk

        root = tk.Tk()
    except Exception:
        return False
    root.title(APP_NAME)
    root.resizable(False, False)
    tk.Label(root, text=APP_NAME + " is running in your browser.", padx=28, pady=10).pack()
    tk.Label(root, text=url, fg="#555555").pack()
    buttons = tk.Frame(root, padx=16, pady=14)
    buttons.pack()
    tk.Button(buttons, text="Open " + APP_NAME, width=18, command=lambda: webbrowser.open(url)).pack(side="left", padx=4)
    tk.Button(buttons, text="Quit", width=10, command=root.destroy).pack(side="left", padx=4)
    root.mainloop()
    return True


def main():
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="local port (default %d)" % DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true", help="do not open the browser")
    args = parser.parse_args()

    if already_running(args.port):
        if not args.no_browser:
            webbrowser.open("http://127.0.0.1:%d/" % args.port)
        return

    Handler.state_file = data_dir() / "atlas.json"
    handler = functools.partial(Handler, directory=str(web_dir()))
    try:
        server = Server(("127.0.0.1", args.port), handler)
    except OSError:
        server = Server(("127.0.0.1", 0), handler)
    url = "http://127.0.0.1:%d/" % server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()

    if not args.no_browser:
        webbrowser.open(url)
    if not control_window(url):
        if sys.stdout:
            print("%s is running at %s\nYour data is saved in %s\nPress Ctrl+C to quit." % (APP_NAME, url, Handler.state_file), flush=True)
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
    server.shutdown()


if __name__ == "__main__":
    main()
