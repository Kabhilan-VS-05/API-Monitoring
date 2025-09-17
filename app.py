import sqlite3
import threading
import time
import os
import json
import math
import smtplib
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from urllib.parse import urlparse
import socket
import ssl
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# --- Configuration ---
SIMPLE_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
ADVANCED_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static_advanced")

app = Flask(__name__, static_folder=SIMPLE_STATIC_DIR)
CORS(app)

DATA_FILE = "api_logs.json"
DATABASE_FILE = "monitoring.db"

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monitored_apis (
            id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT NOT NULL UNIQUE, header_name TEXT,
            header_value TEXT, check_frequency_minutes INTEGER NOT NULL, category TEXT,
            notification_email TEXT, is_active BOOLEAN DEFAULT 1, 
            last_checked_at TIMESTAMP, last_status TEXT DEFAULT 'Pending'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monitoring_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, api_id INTEGER, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status_code INTEGER, is_up BOOLEAN, total_latency_ms REAL, error_message TEXT,
            dns_lookup_ms REAL, tcp_connection_ms REAL, tls_handshake_ms REAL,
            server_processing_ms REAL, content_download_ms REAL,
            FOREIGN KEY(api_id) REFERENCES monitored_apis(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

# --- Email Alerting ---
def send_downtime_alert(api, error_message):
    SENDER_EMAIL = "kabhilan2905@gmail.com"
    SENDER_PASSWORD = "iycq ldeq qhds ekee"
    
    receiver_email = api.get('notification_email')
    if not receiver_email:
        return

    subject = f"API Alert: {api['url']} is Down"
    body = f"""
    Hello,
    An alert has been triggered for an API you are monitoring.

    URL: {api['url']}
    Category: {api.get('category', 'N/A')}
    Status: Down / Error
    Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

    Details:
    {error_message}

    The system will not send further notifications until it is operational again.
    """
    try:
        msg = MIMEMultipart(); msg["From"], msg["To"], msg["Subject"] = SENDER_EMAIL, receiver_email, subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        print(f"✅ Downtime alert sent to {receiver_email} for URL {api['url']}")
    except Exception as e:
        print(f"❌ Failed to send downtime alert for {api['url']}: {e}")

# --- Core Helper Functions ---
def perform_latency_check(url, headers={}):
    parsed_url = urlparse(url); host = parsed_url.hostname
    if not host: raise ValueError("Invalid URL: Host not found")
    port = 443 if parsed_url.scheme == "https" else 80
    t1 = time.time(); ip = socket.gethostbyname(host); dns_lookup = (time.time() - t1) * 1000
    t2 = time.time(); sock = socket.create_connection((ip, port), timeout=10); tcp_conn = (time.time() - t2) * 1000
    tls_handshake = 0
    if parsed_url.scheme == "https":
        t3 = time.time(); context = ssl.create_default_context(); sock = context.wrap_socket(sock, server_hostname=host); tls_handshake = (time.time() - t3) * 1000
    sock.close()
    t4 = time.time(); response = requests.get(url, timeout=10, headers=headers); t5 = time.time()
    content_type = response.headers.get('Content-Type', '').lower()
    server_processing = response.elapsed.total_seconds() * 1000
    content_download = ((t5 - t4) * 1000) - server_processing
    total_latency = dns_lookup + tcp_conn + tls_handshake + server_processing + content_download
    result = {"status_code": response.status_code, "up": response.ok, "total_latency_ms": round(total_latency, 2), "dns_lookup_ms": round(dns_lookup, 2), "tcp_connection_ms": round(tcp_conn, 2), "tls_handshake_ms": round(tls_handshake, 2), "server_processing_ms": round(server_processing, 2), "content_download_ms": round(content_download, 2), "timestamp": datetime.now().isoformat()}
    if 'application/json' in content_type or 'application/xml' in content_type: result['url_type'] = 'API'
    else: result['url_type'] = 'Other'
    return result

# --- Background Worker ---
def monitor_worker():
    print("🚀 Advanced Monitoring worker started.")
    while True:
        conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
        cursor.execute("SELECT * FROM monitored_apis WHERE is_active = 1")
        apis_to_check = [dict(row) for row in cursor.fetchall()]
        now = time.time()
        for api in apis_to_check:
            api_id, url, old_status, frequency, last_checked = api['id'], api['url'], api['last_status'], api['check_frequency_minutes'], api['last_checked_at']
            if last_checked is None or (now - last_checked) >= (frequency * 60):
                new_status, error_msg = 'Pending', ""
                try:
                    res = perform_latency_check(url, {api.get('header_name'): api.get('header_value')} if api.get('header_name') else {})
                    cursor.execute(
                        "INSERT INTO monitoring_logs (api_id, status_code, is_up, total_latency_ms, dns_lookup_ms, tcp_connection_ms, tls_handshake_ms, server_processing_ms, content_download_ms, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (api_id, res["status_code"], res["up"], res["total_latency_ms"], res["dns_lookup_ms"], res["tcp_connection_ms"], res["tls_handshake_ms"], res["server_processing_ms"], res["content_download_ms"], res["timestamp"])
                    )
                    new_status = "Up" if res["up"] else "Down"
                except Exception as e:
                    error_msg = str(e)
                    cursor.execute("INSERT INTO monitoring_logs (api_id, is_up, error_message, timestamp) VALUES (?, ?, ?, ?)", (api_id, 0, error_msg, datetime.now().isoformat()))
                    new_status = "Error"
                
                if new_status in ["Down", "Error"] and old_status == "Up":
                    send_downtime_alert(api, error_msg)
                    
                cursor.execute("UPDATE monitored_apis SET last_checked_at = ?, last_status = ? WHERE id = ?", (now, new_status, api_id))
                conn.commit()
        conn.close(); time.sleep(30)

# --- Simple Checker functions and routes ---
def read_logs_safely():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f: json.dump([], f)
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except json.JSONDecodeError:
        backup_file = f"{DATA_FILE}.bak_{int(time.time())}"; os.rename(DATA_FILE, backup_file)
        with open(DATA_FILE, "w") as f: json.dump([], f)
        return []
read_logs_safely()
def save_to_json(data): logs = read_logs_safely(); logs.append(data); open(DATA_FILE, "w").write(json.dumps(logs, indent=4))
def check_api_logic(api_url, header_name=None, header_value=None):
    try:
        headers = {header_name: header_value} if header_name and header_value else {}
        result = perform_latency_check(api_url, headers)
        result.update({"api_url": api_url, "header_name": header_name or "", "header_value": header_value or "", "diagnosis": "API appears healthy."})
        save_to_json(result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"api_url": api_url, "status_code": 500, "up": False, "error": str(e)}), 500

@app.route("/")
def serve_index(): return send_from_directory(SIMPLE_STATIC_DIR, "index.html")
@app.route("/static/<path:filename>")
def serve_static(filename): return send_from_directory(SIMPLE_STATIC_DIR, filename)
@app.route("/advanced_monitor")
def serve_advanced_monitor(): return send_from_directory(ADVANCED_STATIC_DIR, "monitor.html")
@app.route("/static_advanced/<path:filename>")
def serve_static_advanced(filename): return send_from_directory(ADVANCED_STATIC_DIR, filename)
@app.route("/check_api", methods=["POST"])
def check_api():
    data = request.json
    api_url, h_name, h_value = data.get("api_url"), data.get("header_name"), data.get("header_value")
    return check_api_logic(api_url, h_name, h_value)
@app.route("/last_logs", methods=["GET"])
def last_logs():
    page = request.args.get('page', 1, type=int); per_page = 10
    logs = read_logs_safely(); total_items = len(logs)
    start = (page - 1) * per_page; end = start + per_page
    paginated_logs = logs[::-1][start:end]
    total_pages = math.ceil(total_items / per_page)
    return jsonify({"logs": paginated_logs, "total_pages": total_pages, "current_page": page})
@app.route("/monitored_urls")
def monitored_urls():
    logs = read_logs_safely()
    latest_logs_by_url = {log["api_url"]: log for log in logs if log.get("api_url")}
    return jsonify({"urls_data": list(latest_logs_by_url.values())})
@app.route("/chart_data", methods=["GET"])
def chart_data():
    api_url = request.args.get('url'); logs = read_logs_safely()
    url_logs = sorted([log for log in logs if log.get("api_url") == api_url], key=lambda x: x.get("timestamp", ""))
    return jsonify({"labels": [log.get("timestamp") for log in url_logs], "data": [log.get("total_latency_ms") for log in url_logs]})
@app.route("/api/advanced/monitors")
def get_monitors():
    conn = sqlite3.connect(DATABASE_FILE); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT * FROM monitored_apis")
    monitors = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(monitors)
@app.route("/api/advanced/add_monitor", methods=["POST"])
def add_monitor():
    data = request.json
    conn = sqlite3.connect(DATABASE_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO monitored_apis (url, category, header_name, header_value, check_frequency_minutes, notification_email) VALUES (?, ?, ?, ?, ?, ?)",
            (data['url'], data['category'], data.get('header_name'), data.get('header_value'), data['frequency'], data.get('notification_email')))
        conn.commit()
    except sqlite3.IntegrityError: return jsonify({"error": "This URL is already monitored."}), 409
    finally: conn.close()
    return jsonify({"success": True})
@app.route("/api/advanced/update_monitor", methods=["POST"])
def update_monitor():
    data = request.json
    conn = sqlite3.connect(DATABASE_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE monitored_apis SET url = ?, category = ?, header_name = ?, header_value = ?, check_frequency_minutes = ?, notification_email = ? WHERE id = ?",
            (data['url'], data['category'], data.get('header_name'), data.get('header_value'), data['frequency'], data.get('notification_email'), data['id']))
        conn.commit()
    finally: conn.close()
    return jsonify({"success": True})
@app.route("/api/advanced/delete_monitor", methods=["POST"])
def delete_monitor():
    data = request.json
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM monitored_apis WHERE id = ?", (data['id'],))
    conn.commit()
    conn.close()
    return jsonify({"success": True})
@app.route("/api/advanced/history")
def get_history():
    api_id = request.args.get('id', type=int); page = request.args.get('page', 1, type=int); per_page = 15
    conn = sqlite3.connect(DATABASE_FILE); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT COUNT(id) FROM monitoring_logs WHERE api_id = ?", (api_id,))
    total_items = cursor.fetchone()[0]
    total_pages = math.ceil(total_items / per_page)
    offset = (page - 1) * per_page
    cursor.execute("SELECT * FROM monitoring_logs WHERE api_id = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?", (api_id, per_page, offset))
    history = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"history": history, "total_pages": total_pages, "current_page": page})
@app.route("/api/advanced/daily_summary")
def get_daily_summary():
    api_id = request.args.get('id', type=int)
    now = datetime.now(); start_time = now - timedelta(days=1)
    conn = sqlite3.connect(DATABASE_FILE); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT timestamp, is_up, total_latency_ms, error_message FROM monitoring_logs WHERE api_id = ? AND timestamp >= ? ORDER BY timestamp ASC",
                   (api_id, start_time.strftime("%Y-%m-%d %H:%M:%S")))
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(logs)
@app.route("/api/advanced/log_details/<int:log_id>")
def get_log_details(log_id):
    conn = sqlite3.connect(DATABASE_FILE); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
    cursor.execute("SELECT * FROM monitoring_logs WHERE id = ?", (log_id,))
    log_details = cursor.fetchone()
    conn.close()
    return jsonify(dict(log_details) if log_details else {"error": "Log not found"})


# --- Main Execution Block ---
if __name__ == "__main__":
    init_db()
    monitor_thread = threading.Thread(target=monitor_worker, daemon=True)
    monitor_thread.start()
    app.run(port=5000, debug=True, use_reloader=False)