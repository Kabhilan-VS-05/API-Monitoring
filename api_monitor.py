"""
url_monitor_mitm.py
Desktop GUI to launch mitmdump and capture all request URLs (HTTP + HTTPS via mitm proxy).

Usage:
  1. Install mitmproxy: pip install mitmproxy
  2. Install watchdog: pip install watchdog
  3. Run: python url_monitor_mitm.py
  4. In your browser, set HTTP and HTTPS proxy to: 127.0.0.1 port 8080
  5. Install mitmproxy root CA for HTTPS: run `mitmproxy` once and follow instructions (or visit http://mitm.it while proxy is running).
"""

import os
import sys
import subprocess
import threading
import time
import json
import sqlite3
import tempfile
import queue
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# --- Configuration ---
MITM_PORT = 8080
DB_FILE = "captured_urls.db"
NDJSON_FILE = "captured_urls.ndjson"
ADDON_FILENAME = "mitm_addon.py"
MITMDUMP_CMD = "mitmdump"  # ensure mitmdump is in PATH (part of mitmproxy)
POLL_INTERVAL = 0.5  # GUI poll

# --- Helper: create mitmproxy addon file (writes to sqlite + ndjson) ---
MITM_ADDON_TEMPLATE = r'''
# Auto-generated mitmproxy addon.
# Writes each request as a JSON line into the configured NDJSON_FILE and also inserts into SQLite DB.

from mitmproxy import ctx
import json
import sqlite3
import os
from datetime import datetime

NDJSON = __NDJSON_PATH__
DB_PATH = __DB_PATH__

def ensure_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT,
            client_addr TEXT,
            method TEXT,
            scheme TEXT,
            host TEXT,
            path TEXT,
            full_url TEXT,
            req_headers TEXT
        )
    """)
    conn.commit()
    conn.close()

def request(flow):
    try:
        ensure_db()
        ts = datetime.utcnow().isoformat() + "Z"
        client_addr = "%s:%s" % (flow.client_conn.address[0], flow.client_conn.address[1]) if flow.client_conn.address else ""
        method = flow.request.method
        scheme = flow.request.scheme
        host = flow.request.host or ""
        path = flow.request.path or ""
        full_url = flow.request.pretty_url or ""
        headers = dict(flow.request.headers)

        # write to ndjson
        rec = {
            "ts": ts,
            "client": client_addr,
            "method": method,
            "scheme": scheme,
            "host": host,
            "path": path,
            "full_url": full_url,
            "headers": headers
        }
        # append to ndjson
        with open(NDJSON, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        # insert to sqlite
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO requests (ts, client_addr, method, scheme, host, path, full_url, req_headers)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ts, client_addr, method, scheme, host, path, full_url, json.dumps(headers)))
        conn.commit()
        conn.close()
    except Exception as e:
        ctx.log.warn("Addon write error: %s" % str(e))
'''

# --- GUI / Controller ---
class MitmController:
    def __init__(self, workdir: Path):
        self.workdir = workdir
        self.db_path = str(workdir / DB_FILE)
        self.ndjson_path = str(workdir / NDJSON_FILE)
        self.addon_path = str(workdir / ADDON_FILENAME)
        self.proc = None
        self._stop_event = threading.Event()
        self._poll_q = queue.Queue()
        # create DB if not exists
        self._ensure_db()

    def _ensure_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT,
                client_addr TEXT,
                method TEXT,
                scheme TEXT,
                host TEXT,
                path TEXT,
                full_url TEXT,
                req_headers TEXT
            )
        """)
        conn.commit()
        conn.close()

    def write_addon(self):
        tpl = MITM_ADDON_TEMPLATE
        tpl = tpl.replace("__NDJSON_PATH__", json.dumps(self.ndjson_path))
        tpl = tpl.replace("__DB_PATH__", json.dumps(self.db_path))
        with open(self.addon_path, "w", encoding="utf-8") as f:
            f.write(tpl)

    def start_mitmdump(self):
        if self.proc:
            raise RuntimeError("mitmdump already started")
        self.write_addon()
        cmd = [MITMDUMP_CMD, "-p", str(MITM_PORT), "-s", self.addon_path]
        # Launch mitmdump subprocess
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # start a thread to read stderr/stdout and push logs to queue
        threading.Thread(target=self._reader_thread, daemon=True).start()
        # start watcher thread to tail DB
        threading.Thread(target=self._db_watcher_thread, daemon=True).start()

    def stop_mitmdump(self):
        if not self.proc:
            return
        try:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=3)
            except Exception:
                self.proc.kill()
        except Exception:
            pass
        self.proc = None

    def is_running(self):
        return self.proc is not None and self.proc.poll() is None

    def _reader_thread(self):
        # read process stderr/stdout and forward to queue for GUI
        if not self.proc:
            return
        for stream in (self.proc.stdout, self.proc.stderr):
            def drain(s):
                try:
                    for line in iter(s.readline, ""):
                        if line:
                            self._poll_q.put(("log", line.strip()))
                except Exception:
                    pass
            threading.Thread(target=drain, args=(stream,), daemon=True).start()

    def _db_watcher_thread(self):
        # Poll the SQLite DB for new rows and push them to the queue for GUI.
        last_id = 0
        while self.is_running():
            try:
                conn = sqlite3.connect(self.db_path)
                cur = conn.cursor()
                cur.execute("SELECT id, ts, client_addr, method, scheme, host, path, full_url FROM requests WHERE id > ? ORDER BY id ASC", (last_id,))
                rows = cur.fetchall()
                conn.close()
                for r in rows:
                    last_id = max(last_id, r[0])
                    rec = {
                        "id": r[0],
                        "ts": r[1],
                        "client": r[2],
                        "method": r[3],
                        "scheme": r[4],
                        "host": r[5],
                        "path": r[6],
                        "full_url": r[7]
                    }
                    self._poll_q.put(("item", rec))
            except Exception as e:
                self._poll_q.put(("log", f"DB read error: {e}"))
            time.sleep(0.5)

    def get_queue(self):
        return self._poll_q

    def export_csv(self, outpath):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT ts, client_addr, method, scheme, host, path, full_url FROM requests ORDER BY id ASC")
        rows = cur.fetchall()
        conn.close()
        import csv
        with open(outpath, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ts","client","method","scheme","host","path","full_url"])
            w.writerows(rows)

    def clear_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM requests")
        conn.commit()
        conn.close()
        # remove ndjson
        try:
            if os.path.exists(self.ndjson_path):
                os.remove(self.ndjson_path)
        except Exception:
            pass

# --- GUI App ---
class App:
    def __init__(self, root):
        self.root = root
        root.title("URL Monitor (mitmproxy)")
        root.geometry("1000x650")
        self.workdir = Path.cwd()
        self.ctrl = MitmController(self.workdir)
        self.queue = self.ctrl.get_queue()

        top = ttk.Frame(root, padding=6)
        top.pack(fill="x")
        ttk.Label(top, text="Proxy:").pack(side="left")
        ttk.Label(top, text=f"127.0.0.1:{MITM_PORT}").pack(side="left", padx=(4,10))
        self.start_btn = ttk.Button(top, text="Start Proxy", command=self.start_stop)
        self.start_btn.pack(side="right", padx=6)
        ttk.Button(top, text="Install cert (open instructions)", command=self.open_cert_instructions).pack(side="right")

        mid = ttk.Frame(root, padding=6)
        mid.pack(fill="both", expand=True)

        cols = ("ts","client","method","host","full_url")
        self.tree = ttk.Treeview(mid, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            if c=="full_url":
                self.tree.column(c, width=500)
            elif c=="host":
                self.tree.column(c, width=200)
            else:
                self.tree.column(c, width=140)
        self.tree.pack(fill="both", expand=True, side="left")
        vsb = ttk.Scrollbar(mid, orient="vertical", command=self.tree.yview)
        vsb.pack(side="left", fill="y")
        self.tree.configure(yscrollcommand=vsb.set)

        right = ttk.Frame(root, padding=6)
        right.pack(fill="x")
        ttk.Button(right, text="Export CSV", command=self.export_csv).pack(side="left", padx=4)
        ttk.Button(right, text="Clear Log", command=self.clear_log).pack(side="left", padx=4)
        self.status = ttk.Label(right, text="Idle")
        self.status.pack(side="right")

        # poll queue
        root.after(200, self.poll_queue)

    def start_stop(self):
        if not self.ctrl.is_running():
            # start mitmdump
            try:
                # check mitmdump exists
                if not shutil_which(MITMDUMP_CMD):
                    messagebox.showerror("mitmdump not found", f"mitmdump not found. Install mitmproxy (pip install mitmproxy) and ensure '{MITMDUMP_CMD}' is in PATH.")
                    return
                self.ctrl.start_mitmdump()
                self.start_btn.config(text="Stop Proxy")
                self.status.config(text="Proxy running. Set browser proxy to 127.0.0.1:8080 and install mitmproxy CA for HTTPS from http://mitm.it")
            except Exception as e:
                messagebox.showerror("Start error", str(e))
        else:
            self.ctrl.stop_mitmdump()
            self.start_btn.config(text="Start Proxy")
            self.status.config(text="Stopped")

    def open_cert_instructions(self):
        messagebox.showinfo("mitmproxy cert", "To capture HTTPS you must install mitmproxy's CA cert:\n\n1. Start the proxy (click Start Proxy).\n2. In the browser (while proxy is running and browser proxy is set to 127.0.0.1:8080) open http://mitm.it\n3. Follow the platform-specific steps to install/trust the certificate.\n\nBe careful and remove the certificate later if you don't want it installed permanently.")

    def poll_queue(self):
        try:
            while True:
                typ, payload = self.queue.get_nowait()
                if typ == "log":
                    # currently just set status
                    self.status.config(text=payload[:200])
                elif typ == "item":
                    r = payload
                    self.tree.insert("", 0, values=(r["ts"], r["client"], r["method"], r["host"], r["full_url"]))
        except Exception:
            pass
        finally:
            self.root.after(int(POLL_INTERVAL*1000), self.poll_queue)

    def export_csv(self):
        out = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
        if not out:
            return
        try:
            self.ctrl.export_csv(out)
            messagebox.showinfo("Export", f"Exported to {out}")
        except Exception as e:
            messagebox.showerror("Export error", str(e))

    def clear_log(self):
        if not messagebox.askyesno("Clear", "Clear stored captured requests?"):
            return
        try:
            self.ctrl.clear_db()
            for iid in self.tree.get_children():
                self.tree.delete(iid)
        except Exception as e:
            messagebox.showerror("Clear error", str(e))

def shutil_which(cmd):
    from shutil import which
    return which(cmd)

def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
    