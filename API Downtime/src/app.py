"""
app_mongodb.py - API Monitoring with MongoDB storage and compression.

Features:
    - MongoDB for scalable data storage
    - BSON compression for efficient storage
    - All features from original app maintained
    - Improved query performance with indexes
    - Data compression for logs and certificates
"""

import threading
import time
import os
import json
import math
import io
import socket
import pycurl
import idna
import ssl
import zlib
import base64
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from urllib.parse import urlparse
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient, ASCENDING, DESCENDING
from bson import ObjectId
import requests
from twilio.rest import Client as TwilioClient

# Import new integration modules
from github_integration import GitHubIntegration
from issue_integration import IssueIntegration
from log_collector import MongoDBLogHandler, log_api_error, get_recent_logs, get_logs_by_api
from correlation_engine import CorrelationEngine
from ai_predictor import CategoryAwareAIPredictor as AIPredictor
from alert_manager import AlertManager
from ai_alert_manager import AIAlertManager

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up one level to project root for static folders
PROJECT_ROOT = os.path.dirname(BASE_DIR)
SIMPLE_STATIC_DIR = os.path.join(PROJECT_ROOT, "static")
ADVANCED_STATIC_DIR = os.path.join(PROJECT_ROOT, "static_advanced")
app = Flask(__name__, static_folder=SIMPLE_STATIC_DIR)
CORS(app)

# AI Training Service URL (runs on separate port)
AI_TRAINING_SERVICE_URL = "http://localhost:5001"

# WhatsApp notification provider configuration
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL", "https://api.example.com/whatsapp/send")
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN")

# SMS notification provider configuration (generic HTTP)
SMS_API_URL = os.getenv("SMS_API_URL", "https://api.example.com/sms/send")
SMS_API_TOKEN = os.getenv("SMS_API_TOKEN")

# Twilio SMS configuration (preferred when set)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_MESSAGING_SERVICE_SID = os.getenv("TWILIO_MESSAGING_SERVICE_SID")

twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    except Exception as e:
        print(f"[Twilio] Failed to initialize client: {e}")

# IVR notification provider configuration
IVR_API_URL = os.getenv("IVR_API_URL", "https://api.example.com/ivr/call")
IVR_API_TOKEN = os.getenv("IVR_API_TOKEN")

# Translation provider configuration
TRANSLATION_API_URL = os.getenv("TRANSLATION_API_URL", "https://translation.googleapis.com/language/translate/v2")
TRANSLATION_API_KEY = os.getenv("TRANSLATION_API_KEY")
SUPPORTED_LANGUAGES = {"EN", "TA", "HI"}

# --- MongoDB Configuration ---
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "api_monitoring")

# Global MongoDB client
mongo_client = None
db = None

# --- Compression Utilities ---
def compress_data(data):
    """Compress string data using zlib and encode to base64."""
    if not data:
        return None
    try:
        compressed = zlib.compress(data.encode('utf-8'), level=9)
        return base64.b64encode(compressed).decode('utf-8')
    except Exception as e:
        print(f"[COMPRESSION ERROR] {e}")
        return data

def decompress_data(compressed_data):
    """Decompress base64 encoded zlib data."""
    if not compressed_data:
        return None
    try:
        decoded = base64.b64decode(compressed_data.encode('utf-8'))
        return zlib.decompress(decoded).decode('utf-8')
    except Exception as e:
        print(f"[DECOMPRESSION ERROR] {e}")
        return compressed_data

# --- MongoDB Connection ---
def init_mongodb():
    """Initialize MongoDB connection and create indexes."""
    global mongo_client, db
    try:
        mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        mongo_client.server_info()
        db = mongo_client[MONGODB_DB]
        
        # Create collections and indexes
        monitored_apis = db.monitored_apis
        monitoring_logs = db.monitoring_logs
        
        # Indexes for monitored_apis
        monitored_apis.create_index([("url", ASCENDING)], unique=True)
        monitored_apis.create_index([("category", ASCENDING)])
        monitored_apis.create_index([("is_active", ASCENDING)])
        
        # Indexes for monitoring_logs
        monitoring_logs.create_index([("api_id", ASCENDING)])
        monitoring_logs.create_index([("timestamp", DESCENDING)])
        monitoring_logs.create_index([("api_id", ASCENDING), ("timestamp", DESCENDING)])
        
        # New collections for developer data
        git_commits = db.git_commits
        issues = db.issues
        application_logs = db.application_logs
        incident_reports = db.incident_reports
        data_correlations = db.data_correlations
        pull_requests = db.pull_requests
        
        # Indexes for git_commits
        git_commits.create_index([("commit_id", ASCENDING)], unique=True)
        git_commits.create_index([("timestamp", DESCENDING)])
        git_commits.create_index([("repository", ASCENDING)])
        
        # Indexes for issues
        issues.create_index([("issue_id", ASCENDING)], unique=True)
        issues.create_index([("state", ASCENDING)])
        issues.create_index([("created_at", DESCENDING)])
        
        # Indexes for application_logs
        application_logs.create_index([("timestamp", DESCENDING)])
        application_logs.create_index([("level", ASCENDING)])
        application_logs.create_index([("api_endpoint", ASCENDING)])
        
        # Indexes for incident_reports
        incident_reports.create_index([("incident_id", ASCENDING)], unique=True)
        incident_reports.create_index([("created_at", DESCENDING)])
        
        # Index for github_settings collection
        github_settings = db.github_settings
        github_settings.create_index([("user_id", ASCENDING)], unique=True)
        
        # Index for alert_history collection
        alert_history = db.alert_history
        alert_history.create_index([("api_id", ASCENDING)])
        alert_history.create_index([("created_at", DESCENDING)])
        alert_history.create_index([("status", ASCENDING)])

        # AI insights collection for LLM-style summaries
        ai_insights = db.ai_insights
        ai_insights.create_index([("api_id", ASCENDING), ("created_at", DESCENDING)])
        ai_insights.create_index([("training_session_id", ASCENDING)])

        # AI training run history (detailed logs per training session)
        ai_training_runs = db.ai_training_runs
        ai_training_runs.create_index([("api_id", ASCENDING), ("created_at", DESCENDING)])
        ai_training_runs.create_index([("training_session_id", ASCENDING)])

        # Worker responses for field teams
        worker_responses = db.worker_responses
        worker_responses.create_index([("api_id", ASCENDING)])
        worker_responses.create_index([("alert_id", ASCENDING)])
        worker_responses.create_index([("response", ASCENDING)])
        worker_responses.create_index([("worker_id", ASCENDING)])

        translation_cache = db.translation_cache
        translation_cache.create_index([("source_text", ASCENDING), ("target_language", ASCENDING)], unique=True)

        # Indexes for data_correlations
        data_correlations.create_index([("api_id", ASCENDING)])
        data_correlations.create_index([("timestamp", DESCENDING)])
        data_correlations.create_index([("monitoring_log_id", ASCENDING)])
        
        print(f"[MongoDB] Connected successfully to {MONGODB_DB}")
        print(f"[MongoDB] Initialized 9 collections with indexes")
        
        return True
    except Exception as e:
        print(f"[MongoDB ERROR] Failed to connect: {e}")
        print("[MongoDB] Please ensure MongoDB is running and accessible")
        return False

# --- Utility Functions ---
def now_isoutc():
    return datetime.utcnow().isoformat() + "Z"

def is_valid_url(url):
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and parsed.netloc != ""
    except Exception:
        return False

def serialize_objectid(doc):
    """Convert MongoDB ObjectId and datetime to string for JSON serialization."""
    if doc and "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    
    # Convert datetime objects to ISO format strings
    for key, value in list(doc.items()):
        if isinstance(value, datetime):
            doc[key] = value.isoformat() + "Z"
    
    return doc


def serialize_ai_insight(doc):
    if not doc:
        return None
    serialized = dict(doc)
    serialize_objectid(serialized)
    return serialized


def serialize_worker_response(doc):
    if not doc:
        return None
    serialized = dict(doc)
    serialize_objectid(serialized)
    return serialized


def fetch_worker_responses(api_id, limit=10):
    if db is None or not api_id:
        return []
    cursor = db.worker_responses.find({"api_id": api_id}).sort("timestamp", DESCENDING).limit(limit)
    return [serialize_worker_response(doc) for doc in cursor]


def build_whatsapp_message(payload):
    template = (
        "⚠️ API Alert: {api_name}\n"
        "Risk: {risk_percentage}%\n"
        "Cause: {cause_summary}\n"
        "Action: {recommendation}\n\n"
        "Reply:\n"
        "1 - FIXED\n"
        "2 - NEED HELP\n"
        "3 - RETRY"
    )
    return template.format(
        api_name=payload.get("api_name", "Unknown API"),
        risk_percentage=payload.get("risk_percentage", "N/A"),
        cause_summary=payload.get("cause_summary", "Unable to determine cause"),
        recommendation=payload.get("recommendation", "Follow standard recovery steps")
    )


def dispatch_whatsapp_message(phone_number, message_text):
    if not WHATSAPP_API_TOKEN:
        raise RuntimeError("Missing WHATSAPP_API_TOKEN")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WHATSAPP_API_TOKEN}"
    }
    body = {
        "to": phone_number,
        "type": "template",
        "text": message_text,
        "quick_replies": [
            {"label": "FIXED", "metadata": "FIXED"},
            {"label": "NEED HELP", "metadata": "NEED_HELP"},
            {"label": "RETRY", "metadata": "RETRY"}
        ]
    }
    last_error = None
    for attempt in range(3):
        try:
            response = requests.post(WHATSAPP_API_URL, json=body, headers=headers, timeout=5)
            response.raise_for_status()
            return True, response.json()
        except Exception as exc:
            last_error = str(exc)
            time.sleep(1)
    return False, last_error


def build_ivr_script(payload):
    body = (
        f"Emergency alert for {payload.get('api_name', 'Unknown API')}.\n"
        f"Risk level {payload.get('risk_level', 'high')}.\n"
        f"Cause: {payload.get('cause_voice', payload.get('cause_summary', 'Check system'))}.\n"
        "To confirm after action, press 1.\n"
        "To request help, press 2.\n"
        "To repeat this message, press 3."
    )
    return body


def dispatch_ivr_call(phone_number, payload):
    if not IVR_API_TOKEN:
        raise RuntimeError("Missing IVR_API_TOKEN")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {IVR_API_TOKEN}"
    }
    body = {
        "to": phone_number,
        "script": build_ivr_script(payload),
        "api_id": payload.get("api_id"),
        "alert_id": payload.get("alert_id")
    }
    last_error = None
    for attempt in range(3):
        try:
            response = requests.post(IVR_API_URL, json=body, headers=headers, timeout=5)
            response.raise_for_status()
            return True, response.json()
        except Exception as exc:
            last_error = str(exc)
            time.sleep(1)
    return False, last_error


def normalize_ivr_input(digit):
    mapping = {"1": "FIXED", "2": "NEED_HELP", "3": "RETRY"}
    return mapping.get(str(digit).strip(), "UNKNOWN")


def normalize_whatsapp_response(message_body):
    if not message_body:
        return "UNKNOWN"
    text = message_body.strip().upper()
    if text in {"1", "FIXED", "DONE", "RESOLVED"}:
        return "FIXED"
    if "HELP" in text:
        return "NEED_HELP"
    if "RETRY" in text or text == "3":
        return "RETRY"
    return "UNKNOWN"


def build_sms_message(payload):
    parts = [
        f"API ALERT: {payload.get('api_name', 'Unknown')}",
        f"Risk: {payload.get('risk_percentage', 'N/A')}%",
        f"Cause: {payload.get('cause_short', payload.get('cause_summary', 'Check system'))}",
        f"Action: {payload.get('fix_step', payload.get('recommendation', 'Follow standard recovery steps'))}",
        "Reply FIXED or HELP"
    ]
    message = " | ".join(parts)
    return message[:160]


def dispatch_sms_message(phone_number, message_text):
    """Send SMS via Twilio if configured, otherwise fall back to generic HTTP provider.

    This allows local/dev environments to use Twilio credentials, while keeping
    compatibility with the previous SMS_API_URL/SMS_API_TOKEN flow.
    """

    # Preferred path: Twilio
    if twilio_client and TWILIO_MESSAGING_SERVICE_SID:
        try:
            message = twilio_client.messages.create(
                messaging_service_sid=TWILIO_MESSAGING_SERVICE_SID,
                body=message_text,
                to=phone_number,
            )
            return True, {"sid": message.sid, "status": message.status}
        except Exception as exc:
            # If Twilio is configured but fails, bubble the error
            return False, str(exc)

    # Fallback: generic HTTP provider using SMS_API_URL/SMS_API_TOKEN
    if not SMS_API_TOKEN:
        raise RuntimeError("Missing SMS configuration: either Twilio or SMS_API_TOKEN must be set")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SMS_API_TOKEN}"
    }
    body = {
        "to": phone_number,
        "message": message_text
    }
    last_error = None
    for attempt in range(3):
        try:
            response = requests.post(SMS_API_URL, json=body, headers=headers, timeout=5)
            response.raise_for_status()
            return True, response.json()
        except Exception as exc:
            last_error = str(exc)
            time.sleep(1)
    return False, last_error


def store_ai_insight(api_id, insight_payload):
    """Persist LLM-style AI insight entries."""
    if db is None or not api_id or not insight_payload:
        return None

    insight_doc = {
        "api_id": api_id,
        "created_at": insight_payload.get("created_at") or datetime.utcnow().isoformat() + "Z",
        "summary": insight_payload.get("summary"),
        "details": insight_payload.get("details"),
        "risk_level": insight_payload.get("risk_level"),
        "confidence": insight_payload.get("confidence"),
        "risk_score": insight_payload.get("risk_score"),
        "training_session_id": insight_payload.get("training_session_id"),
        "model_version": insight_payload.get("model_version"),
        "actions": insight_payload.get("actions", []),
        "metrics": insight_payload.get("metrics", {}),
        "raw_prediction": insight_payload.get("raw_prediction", {}),
    }

    result = db.ai_insights.insert_one(insight_doc)
    insight_doc["_id"] = result.inserted_id
    return serialize_ai_insight(insight_doc)


def persist_worker_response(doc):
    if db is None or not doc:
        return None
    doc.setdefault("created_at", datetime.utcnow().isoformat() + "Z")
    result = db.worker_responses.insert_one(doc)
    doc["_id"] = result.inserted_id
    return serialize_worker_response(doc)


def get_cached_translation(text, target_language):
    if db is None:
        return None
    if not text or not target_language:
        return None
    cache = db.translation_cache
    cached = cache.find_one({"source_text": text, "target_language": target_language})
    if cached:
        return cached["translated_text"]
    return None


def cache_translation(text, target_language, translated_text):
    if db is None:
        return None
    cache = db.translation_cache
    cache.update_one(
        {"source_text": text, "target_language": target_language},
        {"$set": {"translated_text": translated_text, "updated_at": datetime.utcnow().isoformat() + "Z"}},
        upsert=True
    )


def translate_text(text, target_language):
    if not text or not target_language:
        return ""
    target_language = target_language.upper()
    if target_language not in SUPPORTED_LANGUAGES:
        target_language = "EN"

    cached = get_cached_translation(text, target_language)
    if cached:
        return cached

    if TRANSLATION_API_KEY:
        payload = {
            "q": text,
            "target": target_language.lower(),
            "key": TRANSLATION_API_KEY
        }
        try:
            response = requests.post(TRANSLATION_API_URL, json=payload, timeout=5)
            response.raise_for_status()
            data = response.json()
            translated = (
                data.get("data", {}).get("translations", [])[0].get("translatedText")
                if data.get("data") and data["data"].get("translations")
                else text
            )
        except Exception:
            translated = text
    else:
        params = {
            "q": text,
            "langpair": f"en|{target_language.lower()}"
        }
        try:
            response = requests.get("https://api.mymemory.translated.net/get", params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            translated = data.get("responseData", {}).get("translatedText", text)
        except Exception:
            translated = text

    cache_translation(text, target_language, translated)
    return translated


def update_alert_worker_ack(alert_id, response_type, channel, timestamp):
    if db is None or not alert_id:
        return False
    try:
        object_id = ObjectId(alert_id)
    except Exception:
        return False
    update_payload = {
        "worker_acknowledgment": {
            "response": response_type,
            "channel": channel,
            "timestamp": timestamp or datetime.utcnow().isoformat() + "Z"
        }
    }
    db.alert_history.update_one({"_id": object_id}, {"$set": update_payload})
    return True


def get_ai_insights_from_db(api_id, limit=5):
    if db is None:
        return []
    cursor = db.ai_insights.find({"api_id": api_id}).sort("created_at", DESCENDING).limit(limit)
    return [serialize_ai_insight(doc) for doc in cursor]


def serialize_training_run(doc):
    if not doc:
        return None
    serialized = dict(doc)
    serialize_objectid(serialized)
    return serialized


def store_ai_training_run(api_id, payload):
    """Persist detailed AI training run summaries."""
    if db is None or not api_id or not payload:
        return None

    training_doc = {
        "api_id": api_id,
        "training_session_id": payload.get("training_session_id"),
        "mode": payload.get("mode", "full"),
        "status": payload.get("status", "completed"),
        "started_at": payload.get("started_at") or datetime.utcnow().isoformat() + "Z",
        "completed_at": payload.get("completed_at"),
        "duration_seconds": payload.get("duration_seconds"),
        "duration_minutes": payload.get("duration_minutes"),
        "failure_probability": payload.get("failure_probability"),
        "confidence": payload.get("confidence"),
        "risk_level": payload.get("risk_level"),
        "risk_score": payload.get("risk_score"),
        "sample_size": payload.get("sample_size"),
        "model_metadata": payload.get("model_metadata", {}),
        "prediction": payload.get("prediction"),
        "metrics": payload.get("metrics") or payload.get("prediction_metrics"),
        "risk_factors": payload.get("risk_factors", []),
        "log_lines": payload.get("log_lines", []),
        "summary": payload.get("summary"),
        "actions": payload.get("actions", []),
        "created_at": payload.get("created_at") or datetime.utcnow().isoformat() + "Z",
        "alert_sent": payload.get("alert_sent", False)
    }

    result = db.ai_training_runs.insert_one(training_doc)
    training_doc["_id"] = result.inserted_id
    return serialize_training_run(training_doc)


def get_training_runs_from_db(api_id, limit=5):
    if db is None:
        return []
    cursor = db.ai_training_runs.find({"api_id": api_id}).sort("created_at", DESCENDING).limit(limit)
    return [serialize_training_run(doc) for doc in cursor]


def get_latest_training_run_from_db(api_id):
    if db is None:
        return None
    doc = db.ai_training_runs.find_one({"api_id": api_id}, sort=[("created_at", DESCENDING)])
    return serialize_training_run(doc)


@app.route("/api/ai/training_runs", methods=["POST"])
def receive_training_run():
    if db is None:
        return jsonify({"error": "Database not connected"}), 500

    payload = request.json or {}
    api_id = payload.get("api_id")
    if not api_id:
        return jsonify({"error": "api_id required"}), 400

    try:
        stored = store_ai_training_run(api_id, payload)
        return jsonify({"success": True, "training_run": stored})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ai/training_runs/<api_id>")
def list_training_runs(api_id):
    if db is None:
        return jsonify({"error": "Database not connected"}), 500

    limit = request.args.get("limit", 10, type=int)
    limit = min(max(limit, 1), 100)
    try:
        runs = get_training_runs_from_db(api_id, limit=limit)
        return jsonify(runs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ai/training_runs/latest/<api_id>")
def latest_training_run(api_id):
    if db is None:
        return jsonify({"error": "Database not connected"}), 500

    try:
        run = get_latest_training_run_from_db(api_id)
        if not run:
            return jsonify({"error": "No training runs found"}), 404
        return jsonify(run)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/notify/whatsapp/send", methods=["POST"])
def notify_whatsapp_send():
    if db is None:
        return jsonify({"error": "Database not connected"}), 500

    payload = request.json or {}
    phone_number = payload.get("phone_number")
    api_id = payload.get("api_id")
    alert_id = payload.get("alert_id")
    if not phone_number or not api_id or not alert_id:
        return jsonify({"error": "phone_number, api_id, and alert_id are required"}), 400

    message_text = payload.get("message_text") or build_whatsapp_message(payload)
    try:
        success, response_data = dispatch_whatsapp_message(phone_number, message_text)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

    if not success:
        return jsonify({"success": False, "error": response_data}), 500

    return jsonify({"success": True, "details": response_data})


@app.route("/notify/whatsapp/receive", methods=["POST"])
def notify_whatsapp_receive():
    if db is None:
        return jsonify({"error": "Database not connected"}), 500

    payload = request.json or {}
    phone_number = payload.get("phone_number")
    message_body = payload.get("message_body")
    timestamp = payload.get("timestamp")
    api_id = payload.get("api_id")
    alert_id = payload.get("alert_id")

    if not phone_number or not message_body:
        return jsonify({"error": "phone_number and message_body are required"}), 400

    response_type = normalize_whatsapp_response(message_body)
    response_doc = {
        "phone_number": phone_number,
        "api_id": api_id,
        "alert_id": alert_id,
        "response": response_type,
        "channel": "whatsapp",
        "raw_message": message_body,
        "timestamp": timestamp or datetime.utcnow().isoformat() + "Z"
    }
    stored = persist_worker_response(response_doc)
    update_alert_worker_ack(alert_id, response_type, "whatsapp", response_doc["timestamp"])

    return jsonify({"success": True, "worker_response": stored})


@app.route("/notify/sms/send", methods=["POST"])
def notify_sms_send():
    if db is None:
        return jsonify({"error": "Database not connected"}), 500

    payload = request.json or {}
    phone_number = payload.get("phone_number")
    api_id = payload.get("api_id")
    alert_id = payload.get("alert_id")
    if not phone_number or not api_id or not alert_id:
        return jsonify({"error": "phone_number, api_id, and alert_id are required"}), 400

    message_text = payload.get("message_text") or build_sms_message(payload)
    try:
        success, response_data = dispatch_sms_message(phone_number, message_text)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

    if not success:
        return jsonify({"success": False, "error": response_data}), 500

    return jsonify({"success": True, "details": response_data})


@app.route("/notify/sms/receive", methods=["POST"])
def notify_sms_receive():
    if db is None:
        return jsonify({"error": "Database not connected"}), 500

    payload = request.json or {}
    phone_number = payload.get("phone_number")
    message_body = payload.get("message_body")
    timestamp = payload.get("timestamp")
    api_id = payload.get("api_id")
    alert_id = payload.get("alert_id")

    if not phone_number or not message_body:
        return jsonify({"error": "phone_number and message_body are required"}), 400

    response_type = normalize_whatsapp_response(message_body)
    response_doc = {
        "phone_number": phone_number,
        "api_id": api_id,
        "alert_id": alert_id,
        "response": response_type,
        "channel": "sms",
        "raw_message": message_body,
        "timestamp": timestamp or datetime.utcnow().isoformat() + "Z"
    }
    stored = persist_worker_response(response_doc)
    update_alert_worker_ack(alert_id, response_type, "sms", response_doc["timestamp"])

    return jsonify({"success": True, "worker_response": stored})


@app.route("/notify/ivr/call", methods=["POST"])
def notify_ivr_call():
    if db is None:
        return jsonify({"error": "Database not connected"}), 500

    payload = request.json or {}
    phone_number = payload.get("phone_number")
    api_id = payload.get("api_id")
    alert_id = payload.get("alert_id")
    if not phone_number or not api_id or not alert_id:
        return jsonify({"error": "phone_number, api_id, and alert_id are required"}), 400

    try:
        success, response_data = dispatch_ivr_call(phone_number, payload)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

    if not success:
        return jsonify({"success": False, "error": response_data}), 500

    return jsonify({"success": True, "details": response_data})


@app.route("/notify/ivr/collect", methods=["POST"])
def notify_ivr_collect():
    if db is None:
        return jsonify({"error": "Database not connected"}), 500

    payload = request.json or {}
    digit = payload.get("digit")
    phone_number = payload.get("phone_number")
    api_id = payload.get("api_id")
    alert_id = payload.get("alert_id")
    timestamp = payload.get("timestamp")

    if digit is None or not phone_number:
        return jsonify({"error": "digit and phone_number are required"}), 400

    response_type = normalize_ivr_input(digit)
    response_doc = {
        "phone_number": phone_number,
        "api_id": api_id,
        "alert_id": alert_id,
        "response": response_type,
        "channel": "ivr",
        "raw_message": digit,
        "timestamp": timestamp or datetime.utcnow().isoformat() + "Z"
    }
    stored = persist_worker_response(response_doc)
    update_alert_worker_ack(alert_id, response_type, "ivr", response_doc["timestamp"])

    return jsonify({"success": True, "worker_response": stored})


@app.route("/utils/translate", methods=["POST"])
def utils_translate():
    payload = request.json or {}
    text = payload.get("text")
    target_language = payload.get("target_language", "EN")

    if not text:
        return jsonify({"error": "text is required"}), 400

    translated = translate_text(text, target_language)
    return jsonify({"translated_text": translated, "target_language": target_language.upper()})


@app.route("/incident/acknowledge", methods=["POST"])
def incident_acknowledge():
    if db is None:
        return jsonify({"error": "Database not connected"}), 500

    payload = request.json or {}
    worker_id = payload.get("worker_id")
    api_id = payload.get("api_id")
    alert_id = payload.get("alert_id")
    response_type = payload.get("response_type")
    timestamp = payload.get("timestamp")

    if not worker_id or not api_id or not alert_id or not response_type:
        return jsonify({"error": "worker_id, api_id, alert_id, and response_type are required"}), 400

    response_type = response_type.upper()
    if response_type not in {"FIXED", "NEED_HELP", "RETRY", "UNKNOWN"}:
        response_type = "UNKNOWN"

    response_doc = {
        "phone_number": payload.get("phone_number"),
        "worker_id": worker_id,
        "api_id": api_id,
        "alert_id": alert_id,
        "response": response_type,
        "channel": payload.get("channel", "manual"),
        "raw_message": payload.get("notes"),
        "timestamp": timestamp or datetime.utcnow().isoformat() + "Z"
    }
    stored = persist_worker_response(response_doc)
    update_alert_worker_ack(alert_id, response_type, "acknowledgement", response_doc["timestamp"])

    return jsonify({"success": True, "worker_response": stored})


# --- Advanced TLS Certificate Fetcher ---
def get_certificate_details_crypto(url):
    """Fetches and parses TLS certificate details using the cryptography library."""
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        port = parsed_url.port or 443
        if parsed_url.scheme != 'https':
            return None

        server_hostname = idna.encode(hostname).decode()
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        with socket.create_connection((hostname, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=server_hostname) as ssock:
                der_cert = ssock.getpeercert(binary_form=True)
                cipher = ssock.cipher()
                cert = x509.load_der_x509_certificate(der_cert, default_backend())

                sans_ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
                san_list = [name.value for name in sans_ext.value]

                def _to_utc_iso(dt):
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    else:
                        dt = dt.astimezone(timezone.utc)
                    return dt.isoformat().replace('+00:00', 'Z')

                return {
                    "subject": cert.subject.rfc4514_string(),
                    "issuer": cert.issuer.rfc4514_string(),
                    "sans": ", ".join(san_list),
                    "valid_from": _to_utc_iso(cert.not_valid_before),
                    "valid_until": _to_utc_iso(cert.not_valid_after),
                    "cipher": f"{cipher[0]} ({cipher[1]}, {cipher[2]} bits)"
                }
    except Exception as e:
        return {"error": f"Cert check failed: {str(e)}"}

# --- URL Type Determination ---
def determine_url_type(content_type):
    """Determines the type of URL based on its Content-Type header."""
    if not content_type:
        return "Unknown"
    ct = content_type.lower()
    if 'application/json' in ct or 'application/vnd.api+json' in ct:
        return "API"
    if 'text/html' in ct:
        return "Website"
    if 'application/xml' in ct or 'text/xml' in ct:
        return "XML Endpoint"
    if 'application/javascript' in ct or 'text/javascript' in ct:
        return "JavaScript File"
    if 'image/' in ct:
        return "Image"
    return "Resource"

# --- Core Latency Check using pycurl ---
def perform_latency_check(url, headers=None, timeout=10, body_snippet_len=500, required_body_substring=None):
    if headers is None: headers = {}
    
    result = {
        "status_code": None, "up": False, "total_latency_ms": None,
        "dns_latency_ms": None, "tcp_latency_ms": None, "tls_latency_ms": None,
        "server_processing_latency_ms": None, "content_download_latency_ms": None,
        "content_type": None, "body_snippet": None, "certificate_details": None,
        "error": None, "timestamp": now_isoutc(), "url_type": "Unknown"
    }
    
    buffer = io.BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.TIMEOUT, timeout)
    c.setopt(c.FOLLOWLOCATION, 1)
    if headers: c.setopt(c.HTTPHEADER, [f"{key}: {value}" for key, value in headers.items()])
    if hasattr(c, "CERTINFO"):
        c.setopt(c.CERTINFO, 1)
    else:
        print("[PycURL] CERTINFO not supported on this platform; skipping certificate detail collection")

    try:
        c.perform()

        # Latency
        dns_ms = c.getinfo(c.NAMELOOKUP_TIME) * 1000
        tcp_ms = (c.getinfo(c.CONNECT_TIME) - c.getinfo(c.NAMELOOKUP_TIME)) * 1000
        tls_ms = (c.getinfo(c.APPCONNECT_TIME) - c.getinfo(c.CONNECT_TIME)) * 1000 if url.startswith("https") else 0
        server_ms = (c.getinfo(c.PRETRANSFER_TIME) - c.getinfo(c.APPCONNECT_TIME)) * 1000 if url.startswith("https") else (c.getinfo(c.PRETRANSFER_TIME) - c.getinfo(c.CONNECT_TIME)) * 1000
        download_ms = (c.getinfo(c.TOTAL_TIME) - c.getinfo(c.PRETRANSFER_TIME)) * 1000
        total_ms = c.getinfo(c.TOTAL_TIME) * 1000

        # Response
        status_code = c.getinfo(c.RESPONSE_CODE)
        content_type = c.getinfo(c.CONTENT_TYPE)
        body = buffer.getvalue().decode('utf-8', errors='replace')
        snippet = body[:body_snippet_len]

        up = 200 <= status_code < 300
        if required_body_substring and not (snippet and required_body_substring in snippet):
            up = False
            result["error"] = "Required text not found in response body."

        result.update({
            "status_code": status_code, "up": up,
            "total_latency_ms": round(total_ms, 2),
            "dns_latency_ms": round(dns_ms, 2),
            "tcp_latency_ms": round(max(0, tcp_ms), 2),
            "tls_latency_ms": round(max(0, tls_ms), 2),
            "server_processing_latency_ms": round(max(0, server_ms), 2),
            "content_download_latency_ms": round(max(0, download_ms), 2),
            "content_type": content_type, "body_snippet": snippet,
            "url_type": determine_url_type(content_type),
        })

        cert_details = _extract_certificate_from_curl(url, c)
        if cert_details is not None:
            result["certificate_details"] = cert_details

    except pycurl.error as e:
        result.update({ "error": str(e), "up": False })
        if url.lower().startswith("https"):
            fallback_cert = get_certificate_details_crypto(url)
            if fallback_cert is not None:
                result["certificate_details"] = fallback_cert
    finally:
        c.close()

    return result


def _extract_certificate_from_curl(url, curl_handle):
    """Extract certificate metadata from a pycurl handle, with fallback helpers."""
    if not url.lower().startswith("https"):
        return None

    try:
        cert_info = curl_handle.getinfo(pycurl.CERTINFO)
    except (AttributeError, pycurl.error):
        return get_certificate_details_crypto(url)

    if cert_info:
        try:
            server_cert = cert_info[0] if cert_info else []
            info_map = {}
            for key, value in server_cert:
                info_map.setdefault(key, []).append(value)

            def _first(key):
                values = info_map.get(key)
                return values[0] if values else None

            def _parse_date(value):
                if not value:
                    return None
                for fmt in ("%b %d %H:%M:%S %Y %Z", "%Y-%m-%d %H:%M:%S %Z"):
                    try:
                        dt = datetime.strptime(value, fmt)
                        dt = dt.replace(tzinfo=timezone.utc)
                        return dt.isoformat().replace('+00:00', 'Z')
                    except ValueError:
                        continue
                return value

            sans_raw = _first("Subject Alternative Name")
            if sans_raw:
                sans = ", ".join(part.replace("DNS:", "").strip() for part in sans_raw.split(','))
            else:
                sans = None

            cipher = _first("Cipher")

            details = {
                "subject": _first("Subject"),
                "issuer": _first("Issuer"),
                "sans": sans,
                "valid_from": _parse_date(_first("Start date")),
                "valid_until": _parse_date(_first("Expire date")),
            }

            if cipher:
                details["cipher"] = cipher

            if any(details.values()):
                return details
        except Exception as parse_error:
            fallback = get_certificate_details_crypto(url)
            if isinstance(fallback, dict):
                if fallback.get("error"):
                    fallback["error"] = f"{fallback['error']} | curl parse error: {parse_error}"
                return fallback
            return {"error": f"Curl cert parse error: {parse_error}"}

    return get_certificate_details_crypto(url)

# --- Background Worker for Advanced Monitoring ---
def monitor_worker(sleep_seconds=30):
    print("🚀 Advanced Monitoring worker started.")
    while True:
        try:
            if db is None:
                print("[Monitor] MongoDB not connected, skipping check cycle")
                time.sleep(sleep_seconds)
                continue
                
            monitored_apis = db.monitored_apis
            monitoring_logs = db.monitoring_logs
            
            apis = list(monitored_apis.find({"is_active": True}))

            for api in apis:
                try:
                    now = datetime.utcnow()
                    should_check = True
                    last_checked = api.get("last_checked_at")
                    freq_value = api.get("check_frequency_minutes", 1)
                    try:
                        freq = float(freq_value)
                        if freq <= 0:
                            freq = 1.0
                    except (TypeError, ValueError):
                        freq = 1.0

                    if last_checked:
                        try:
                            if isinstance(last_checked, str):
                                last_checked_time = datetime.fromisoformat(last_checked.replace("Z", ""))
                            else:
                                last_checked_time = last_checked
                            if now < last_checked_time + timedelta(minutes=freq):
                                should_check = False
                        except Exception:
                            should_check = True

                    if not should_check:
                        continue

                    h_name = api.get("header_name") or ""
                    h_val = api.get("header_value") or ""
                    headers = {h_name: h_val} if h_name and h_val else {}

                    res = perform_latency_check(api["url"], headers=headers)
                    ts = res.get("timestamp", now_isoutc())
                    cert = res.get("certificate_details") or {}

                    # Compress body snippet if it exists
                    body_snippet_compressed = None
                    if res.get("body_snippet"):
                        body_snippet_compressed = compress_data(res.get("body_snippet"))

                    log_entry = {
                        "api_id": str(api["_id"]),
                        "timestamp": ts,
                        "status_code": res.get("status_code"),
                        "is_up": res.get("up"),
                        "total_latency_ms": res.get("total_latency_ms"),
                        "dns_latency_ms": res.get("dns_latency_ms"),
                        "tcp_latency_ms": res.get("tcp_latency_ms"),
                        "tls_latency_ms": res.get("tls_latency_ms"),
                        "server_processing_latency_ms": res.get("server_processing_latency_ms"),
                        "content_download_latency_ms": res.get("content_download_latency_ms"),
                        "error_message": res.get("error"),
                        "content_type": res.get("content_type"),
                        "body_snippet_compressed": body_snippet_compressed,
                        "url_type": res.get("url_type"),
                        "tls_cert_subject": cert.get("subject"),
                        "tls_cert_issuer": cert.get("issuer"),
                        "tls_cert_sans": cert.get("sans"),
                        "tls_cert_valid_from": cert.get("valid_from"),
                        "tls_cert_valid_until": cert.get("valid_until"),
                        "tls_cipher": cert.get("cipher")
                    }

                    result = monitoring_logs.insert_one(log_entry)
                    log_entry["_id"] = result.inserted_id

                    # Auto-correlate with developer data
                    try:
                        correlation_engine = CorrelationEngine(db)
                        correlation_engine.correlate_monitoring_event(log_entry)
                    except Exception as corr_err:
                        print(f"[Correlation] Error: {corr_err}")
                    
                    # System 1: Immediate downtime/recovery alerting
                    try:
                        alert_manager = AlertManager(db)
                        # Use same status logic as monitoring
                        current_status = "Up" if res.get("up") else ("Error" if res.get("error") else "Down")
                        alert_result = alert_manager.check_and_alert(
                            str(api["_id"]), 
                            api["url"], 
                            current_status
                        )
                        if alert_result:
                            print(f"[Alert] Downtime/Recovery alert: {alert_result.get('message', 'Success')}")
                    except Exception as alert_err:
                        print(f"[Alert] Error: {alert_err}")
                    
                    # System 2: AI predictive alerting (every 15 mins)
                    try:
                        ai_alert_manager = AIAlertManager(db)
                        ai_alert_result = ai_alert_manager.check_and_alert(
                            str(api["_id"]),
                            api["url"]
                        )
                        if ai_alert_result:
                            print(f"[AI Alert] Prediction alert: {ai_alert_result.get('message', 'Success')}")
                    except Exception as ai_err:
                        print(f"[AI Alert] Error: {ai_err}")

                    new_status = "Up" if res.get("up") else ("Error" if res.get("error") else "Down")
                    monitored_apis.update_one(
                        {"_id": api["_id"]},
                        {"$set": {"last_checked_at": ts, "last_status": new_status}}
                    )

                except Exception as e_inner:
                    print(f"Error checking API ID {api.get('_id')}: {e_inner}")

        except Exception as e:
            print("Monitor worker outer error:", e)

        time.sleep(sleep_seconds)

# --- ROUTING AND ENDPOINTS ---
@app.route("/")
def serve_index(): 
    return send_from_directory(SIMPLE_STATIC_DIR, "index.html")

@app.route("/static/<path:filename>")
def serve_static(filename): 
    return send_from_directory(SIMPLE_STATIC_DIR, filename)

@app.route("/advanced_monitor")
def serve_advanced_monitor(): 
    return send_from_directory(ADVANCED_STATIC_DIR, "monitor.html")

@app.route("/ai_showcase")
def serve_ai_showcase():
    """Serve the AI capabilities showcase page"""
    return send_from_directory(ADVANCED_STATIC_DIR, "ai_showcase.html")

@app.route('/advanced_monitor/<path:text>', methods=['GET'])
def serve_advanced_proxy(text): 
    return send_from_directory(ADVANCED_STATIC_DIR, "monitor.html")

@app.route("/static_advanced/<path:filename>")
def serve_static_advanced(filename): 
    return send_from_directory(ADVANCED_STATIC_DIR, filename)

@app.route("/check_api", methods=["POST"])
def check_api():
    data = request.json or {}
    api_url = data.get("api_url") or data.get("url")
    if not api_url: 
        return jsonify({"error": "API URL is required"}), 400
    if not is_valid_url(api_url): 
        return jsonify({"error": "Invalid URL"}), 400
    
    h_name = data.get("header_name")
    h_val = data.get("header_value")
    headers = {h_name: h_val} if h_name and h_val else {}
    required_body_substring = data.get("required_body_substring")

    try:
        res = perform_latency_check(
            api_url,
            headers=headers,
            required_body_substring=required_body_substring
        )
    except Exception as e:
        error_payload = {
            "api_url": api_url,
            "header_name": h_name or "",
            "header_value": h_val or "",
            "error": f"Unexpected error during check: {e}",
            "up": False
        }
        return jsonify(error_payload), 500

    res.update({"api_url": api_url, "header_name": h_name or "", "header_value": h_val or ""})
    
    # Save to MongoDB simple_logs collection
    if db is not None:
        simple_logs = db.simple_logs
        body_compressed = compress_data(res.get("body_snippet")) if res.get("body_snippet") else None
        log_doc = res.copy()
        log_doc["body_snippet_compressed"] = body_compressed
        log_doc.pop("body_snippet", None)
        simple_logs.insert_one(log_doc)
    
    return jsonify(res)

@app.route("/last_logs", methods=["GET"])
def last_logs():
    page = request.args.get("page", 1, type=int)
    per_page = 10
    
    if db is None:
        return jsonify({"logs": [], "total_pages": 0, "current_page": page})
    
    simple_logs = db.simple_logs
    total_items = simple_logs.count_documents({})
    skip = (page - 1) * per_page
    
    logs = list(simple_logs.find().sort("timestamp", DESCENDING).skip(skip).limit(per_page))
    
    # Decompress and serialize
    for log in logs:
        log = serialize_objectid(log)
        if log.get("body_snippet_compressed"):
            log["body_snippet"] = decompress_data(log["body_snippet_compressed"])
            del log["body_snippet_compressed"]
    
    return jsonify({
        "logs": logs,
        "total_pages": math.ceil(total_items / per_page) if per_page else 0,
        "current_page": page
    })

@app.route("/monitored_urls")
def monitored_urls():
    if db is None:
        return jsonify({"urls_data": []})
    
    simple_logs = db.simple_logs
    pipeline = [
        {"$sort": {"timestamp": -1}},
        {"$group": {
            "_id": "$api_url",
            "latest": {"$first": "$$ROOT"}
        }},
        {"$replaceRoot": {"newRoot": "$latest"}}
    ]
    
    latest_logs = list(simple_logs.aggregate(pipeline))
    for log in latest_logs:
        serialize_objectid(log)
    
    return jsonify({"urls_data": latest_logs})

@app.route("/chart_data", methods=["GET"])
def chart_data():
    api_url = request.args.get("url")
    
    if db is None:
        return jsonify({"labels": [], "data": []})
    
    simple_logs = db.simple_logs
    logs = list(simple_logs.find({"api_url": api_url}).sort("timestamp", ASCENDING).limit(50))
    
    return jsonify({
        "labels": [log.get("timestamp") for log in logs],
        "data": [log.get("total_latency_ms") for log in logs]
    })

# --- ADVANCED MONITOR API ---
@app.route("/api/advanced/monitors")
def get_monitors():
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    
    try:
        monitored_apis = db.monitored_apis
        monitoring_logs = db.monitoring_logs
        
        monitors = list(monitored_apis.find().sort([("category", ASCENDING), ("url", ASCENDING)]))
        
        twenty_four_hours_ago = (datetime.utcnow() - timedelta(hours=24)).isoformat() + "Z"

        for monitor in monitors:
            monitor = serialize_objectid(monitor)
            api_id = monitor["id"]
            
            # Stats
            pipeline = [
                {"$match": {"api_id": api_id, "timestamp": {"$gte": twenty_four_hours_ago}}},
                {"$group": {
                    "_id": None,
                    "avg_latency": {"$avg": "$total_latency_ms"},
                    "total_checks": {"$sum": 1},
                    "up_checks": {"$sum": {"$cond": ["$is_up", 1, 0]}}
                }}
            ]
            
            stats = list(monitoring_logs.aggregate(pipeline))
            
            if stats and stats[0].get("avg_latency") is not None:
                monitor['avg_latency_24h'] = round(stats[0]['avg_latency'], 2)
                monitor['uptime_pct_24h'] = round((stats[0]['up_checks'] / stats[0]['total_checks']) * 100, 2)
            else:
                monitor['avg_latency_24h'] = 0
                monitor['uptime_pct_24h'] = 100.0

            # Recent checks
            recent = list(monitoring_logs.find({"api_id": api_id}).sort("timestamp", DESCENDING).limit(15))
            monitor['recent_checks'] = [
                {'is_up': r['is_up'], 'timestamp': r['timestamp']} 
                for r in reversed(recent)
            ]

        return jsonify(monitors)

    except Exception as e:
        print(f"[DB ERROR] Failed to fetch dashboard monitors: {e}")
        return jsonify({"error": "Failed to retrieve monitor data from server."}), 500

@app.route("/api/advanced/add_monitor", methods=["POST"])
def add_monitor():
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    
    data = request.json or {}
    url = data.get("url") or data.get("api_url")
    
    if not url or not is_valid_url(url):
        return jsonify({"error": "Valid 'url' is required"}), 400
        
    freq = data.get("check_frequency_minutes", 1)
    try:
        freq = float(freq)
        if freq <= 0:
            freq = 1.0
    except (ValueError, TypeError):
        freq = 1.0
    
    monitored_apis = db.monitored_apis
    
    # Check if URL already exists
    if monitored_apis.find_one({"url": url}):
        return jsonify({"error": "This URL is already monitored."}), 409
    
    monitor_doc = {
        "url": url,
        "category": data.get("category"),
        "header_name": data.get("header_name"),
        "header_value": data.get("header_value"),
        "check_frequency_minutes": freq,
        "notification_email": data.get("notification_email"),
        "is_active": True,
        "last_checked_at": None,
        "last_status": "Pending"
    }
    
    monitored_apis.insert_one(monitor_doc)
    return jsonify({"success": True, "message": "Monitor added successfully."})

@app.route("/api/advanced/update_monitor", methods=["POST"])
def update_monitor():
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    
    data = request.json or {}
    if "id" not in data:
        return jsonify({"error": "'id' is required"}), 400

    url = data.get("url") or data.get("api_url")
    if not url or not is_valid_url(url):
        return jsonify({"error": "A valid 'url' is required for updating."}), 400

    freq = data.get("check_frequency_minutes", 1)
    try:
        freq = float(freq)
        if freq <= 0:
            freq = 1.0
    except (ValueError, TypeError):
        freq = 1.0
    
    monitored_apis = db.monitored_apis
    monitored_apis.update_one(
        {"_id": ObjectId(data["id"])},
        {"$set": {
            "url": url,
            "category": data.get("category"),
            "header_name": data.get("header_name"),
            "header_value": data.get("header_value"),
            "check_frequency_minutes": freq,
            "notification_email": data.get("notification_email")
        }}
    )
    
    return jsonify({"success": True, "message": "Monitor updated successfully."})

@app.route("/api/advanced/delete_monitor", methods=["POST"])
def delete_monitor():
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    
    data = request.json or {}
    if "id" not in data: 
        return jsonify({"error": "'id' is required"}), 400
    
    monitored_apis = db.monitored_apis
    monitoring_logs = db.monitoring_logs
    
    api_id = data["id"]
    monitored_apis.delete_one({"_id": ObjectId(api_id)})
    monitoring_logs.delete_many({"api_id": api_id})
    
    return jsonify({"success": True})

@app.route("/api/advanced/history")
def get_history():
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    
    api_id = request.args.get("id")
    if not api_id: 
        return jsonify({"error": "'id' (api_id) is required"}), 400
    
    page = request.args.get("page", 1, type=int)
    per_page = 15
    
    monitoring_logs = db.monitoring_logs
    total_items = monitoring_logs.count_documents({"api_id": api_id})
    skip = (page - 1) * per_page
    
    logs = list(monitoring_logs.find({"api_id": api_id}).sort("timestamp", DESCENDING).skip(skip).limit(per_page))
    
    for log in logs:
        serialize_objectid(log)
        if log.get("body_snippet_compressed"):
            log["body_snippet"] = decompress_data(log["body_snippet_compressed"])
            del log["body_snippet_compressed"]
    
    return jsonify({
        "history": logs,
        "total_pages": math.ceil(total_items / per_page) if per_page else 0,
        "current_page": page
    })

@app.route("/api/advanced/last_checks/<api_id>")
def get_last_checks(api_id):
    if db is None:
        return jsonify([])
    
    monitoring_logs = db.monitoring_logs
    logs = list(monitoring_logs.find({"api_id": api_id}).sort("timestamp", DESCENDING).limit(15))
    
    result = [{"is_up": bool(log.get("is_up"))} for log in logs]
    return jsonify(result)

@app.route("/api/advanced/log_details/<log_id>")
def get_log_details(log_id):
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    
    monitoring_logs = db.monitoring_logs
    log = monitoring_logs.find_one({"_id": ObjectId(log_id)})
    
    if not log: 
        return jsonify({"error": "Log not found"}), 404
    
    serialize_objectid(log)
    if log.get("body_snippet_compressed"):
        log["body_snippet"] = decompress_data(log["body_snippet_compressed"])
        del log["body_snippet_compressed"]
    
    if "is_up" in log: 
        log["is_up"] = bool(log["is_up"])
    
    return jsonify(log)

@app.route("/api/advanced/uptime_history/<api_id>")
def get_uptime_history(api_id):
    """Calculates daily uptime percentage for the last 90 days."""
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    
    monitoring_logs = db.monitoring_logs
    ninety_days_ago = (datetime.utcnow() - timedelta(days=90)).isoformat() + "Z"
    
    try:
        pipeline = [
            {"$match": {"api_id": api_id, "timestamp": {"$gte": ninety_days_ago}}},
            {"$group": {
                "_id": {"$substr": ["$timestamp", 0, 10]},
                "total_checks": {"$sum": 1},
                "up_checks": {"$sum": {"$cond": ["$is_up", 1, 0]}}
            }},
            {"$project": {
                "log_date": "$_id",
                "uptime_pct": {"$multiply": [{"$divide": ["$up_checks", "$total_checks"]}, 100]}
            }},
            {"$sort": {"log_date": 1}}
        ]
        
        daily_stats = list(monitoring_logs.aggregate(pipeline))
        stats_dict = {s['log_date']: round(s['uptime_pct'], 2) for s in daily_stats}
        
        # Fill in gaps
        result = []
        for i in range(90):
            day = datetime.utcnow().date() - timedelta(days=i)
            day_str = day.isoformat()
            uptime = stats_dict.get(day_str, None)
            result.append({'date': day_str, 'uptime_pct': uptime})
            
        return jsonify(list(reversed(result)))

    except Exception as e:
        print(f"[DB ERROR] Failed to fetch uptime history for api_id {api_id}: {e}")
        return jsonify({"error": "Failed to retrieve uptime history."}), 500

# --- DEVELOPER DATA INTEGRATION APIs ---

@app.route("/api/sync/github", methods=["POST"])
def sync_github():
    """Sync commits and PRs from GitHub using stored settings"""
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    
    data = request.json or {}
    repo_owner = data.get("repo_owner")
    repo_name = data.get("repo_name")
    since_days = data.get("since_days", 7)
    
    # If not provided in request, get from stored settings
    if not repo_owner or not repo_name:
        settings = db.github_settings.find_one({"user_id": "default_user"})
        if settings:
            repo_owner = settings.get("repo_owner")
            repo_name = settings.get("repo_name")
    
    if not repo_owner or not repo_name:
        return jsonify({"error": "repo_owner and repo_name required. Please save settings first."}), 400
    
    # Try to get token from stored settings first, then fall back to env variable
    github_token = None
    settings = db.github_settings.find_one({"user_id": "default_user"})
    if settings and "github_token" in settings:
        github_token = settings["github_token"]
    
    if not github_token:
        github_token = os.getenv("GITHUB_TOKEN")
    
    if not github_token:
        return jsonify({"error": "GitHub token not configured. Please add token in settings or environment."}), 500
    
    try:
        github = GitHubIntegration(github_token, db)
        
        # Fetch commits
        commit_result = github.fetch_commits(repo_owner, repo_name, since_days)
        
        # Fetch pull requests
        pr_result = github.fetch_pull_requests(repo_owner, repo_name)
        
        return jsonify({
            "success": True,
            "commits": commit_result,
            "pull_requests": pr_result
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/sync/issues", methods=["POST"])
def sync_issues():
    """Sync issues from GitHub using stored settings"""
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    
    data = request.json or {}
    repo_owner = data.get("repo_owner")
    repo_name = data.get("repo_name")
    
    # If not provided in request, get from stored settings
    if not repo_owner or not repo_name:
        settings = db.github_settings.find_one({"user_id": "default_user"})
        if settings:
            repo_owner = settings.get("repo_owner")
            repo_name = settings.get("repo_name")
    
    if not repo_owner or not repo_name:
        return jsonify({"error": "repo_owner and repo_name required. Please save settings first."}), 400
    
    # Try to get token from stored settings first, then fall back to env variable
    github_token = None
    settings = db.github_settings.find_one({"user_id": "default_user"})
    if settings and "github_token" in settings:
        github_token = settings["github_token"]
    
    if not github_token:
        github_token = os.getenv("GITHUB_TOKEN")
    
    if not github_token:
        return jsonify({"error": "GitHub token not configured. Please add token in settings or environment."}), 500
    
    try:
        issue_integration = IssueIntegration(github_token, db)
        result = issue_integration.fetch_github_issues(repo_owner, repo_name)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/alert-status/<api_id>", methods=["GET"])
def get_alert_status(api_id):
    """Get current alert status for an API (downtime alerts + AI predictions)"""
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    
    try:
        result = {
            "downtime_alert": None,
            "ai_prediction": None
        }
        
        # Check for open downtime alert
        downtime_alert = db.alert_history.find_one({
            "api_id": api_id,
            "status": "open",
            "alert_type": "downtime"
        })
        
        if downtime_alert:
            result["downtime_alert"] = {
                "created_at": downtime_alert.get("created_at"),
                "github_issue_number": downtime_alert.get("github_issue_number"),
                "github_issue_url": downtime_alert.get("github_issue_url"),
                "reason": downtime_alert.get("reason")
            }
        
        # Check for AI prediction alert
        ai_alert = db.alert_history.find_one({
            "api_id": api_id,
            "status": "open",
            "alert_type": "ai_prediction"
        })
        
        if ai_alert:
            result["ai_prediction"] = {
                "failure_probability": ai_alert.get("failure_probability", 0),
                "created_at": ai_alert.get("created_at"),
                "github_issue_number": ai_alert.get("github_issue_number"),
                "github_issue_url": ai_alert.get("github_issue_url"),
                "last_check": ai_alert.get("updated_at") or ai_alert.get("created_at")
            }
            ack = ai_alert.get("worker_acknowledgment")
            if ack:
                result["ai_prediction"]["worker_acknowledgment"] = ack

        result["worker_responses"] = fetch_worker_responses(api_id, limit=5)
        # Don't try to predict on-demand, just show if alert exists
        # AI predictions happen in background every 15 mins

        return jsonify(result)
        
    except Exception as e:
        print(f"[Alert Status] Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/worker-responses/<api_id>")
def get_worker_responses(api_id):
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    limit = request.args.get("limit", 20, type=int)
    limit = min(max(limit, 1), 100)
    try:
        responses = fetch_worker_responses(api_id, limit=limit)
        return jsonify(responses)
    except Exception as e:
        print(f"[Worker Responses] Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/github/create-downtime-alert", methods=["POST"])
def create_downtime_alert():
    """Create a GitHub issue for API downtime"""
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    
    data = request.json or {}
    api_id = data.get("api_id")
    
    if not api_id:
        return jsonify({"error": "api_id required"}), 400
    
    # Get GitHub settings
    settings = db.github_settings.find_one({"user_id": "default_user"})
    if not settings:
        return jsonify({"error": "GitHub settings not configured"}), 400
    
    repo_owner = settings.get("repo_owner")
    repo_name = settings.get("repo_name")
    github_token = settings.get("github_token") or os.getenv("GITHUB_TOKEN")
    
    if not github_token:
        return jsonify({"error": "GitHub token not configured"}), 500
    
    try:
        # Get API details
        api = db.monitored_apis.find_one({"_id": ObjectId(api_id)})
        if not api:
            return jsonify({"error": "API not found"}), 404
        
        # Get latest downtime log
        latest_log = db.monitoring_logs.find_one(
            {"api_id": api_id, "is_up": False},
            sort=[("timestamp", -1)]
        )
        
        if not latest_log:
            return jsonify({"error": "No downtime detected"}), 404
        
        # Prepare downtime data
        downtime_data = {
            "timestamp": latest_log.get("timestamp"),
            "status_code": latest_log.get("status_code"),
            "error_message": latest_log.get("error_message"),
            "total_latency_ms": latest_log.get("total_latency_ms"),
            "dns_latency_ms": latest_log.get("dns_latency_ms"),
            "tcp_latency_ms": latest_log.get("tcp_latency_ms"),
            "tls_latency_ms": latest_log.get("tls_latency_ms"),
            "server_processing_latency_ms": latest_log.get("server_processing_latency_ms"),
            "url_type": latest_log.get("url_type"),
            "incident_id": f"INC-{int(time.time())}",
            "history_summary": f"API has been down since {latest_log.get('timestamp')}"
        }
        
        # Create GitHub issue
        issue_integration = IssueIntegration(github_token, db)
        result = issue_integration.create_downtime_alert(
            repo_owner, repo_name, api["url"], downtime_data
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/commits", methods=["GET"])
def get_commits():
    """Get recent commits"""
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    
    hours = request.args.get("hours", 24, type=int)
    github_token = os.getenv("GITHUB_TOKEN", "")
    
    github = GitHubIntegration(github_token, db)
    commits = github.get_recent_commits(hours)
    
    for commit in commits:
        serialize_objectid(commit)
    
    return jsonify(commits)

@app.route("/api/issues", methods=["GET"])
def get_issues():
    """Get issues"""
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    
    state = request.args.get("state", "all")
    
    if state == "open":
        issues = list(db.issues.find({"state": "open"}).sort("created_at", -1).limit(50))
    else:
        issues = list(db.issues.find().sort("created_at", -1).limit(50))
    
    for issue in issues:
        serialize_objectid(issue)
    
    return jsonify(issues)

@app.route("/api/logs", methods=["GET"])
def get_logs():
    """Get application logs"""
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    
    hours = request.args.get("hours", 24, type=int)
    level = request.args.get("level")
    
    logs = get_recent_logs(db, hours, level)
    
    for log in logs:
        serialize_objectid(log)
    
    return jsonify(logs)

@app.route("/api/incidents", methods=["POST"])
def create_incident():
    """Create a new incident report"""
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    
    data = request.json or {}
    
    incident_doc = {
        "incident_id": f"INC-{int(time.time())}",
        "title": data.get("title"),
        "summary": data.get("summary"),
        "severity": data.get("severity", "medium"),
        "start_time": data.get("start_time"),
        "end_time": data.get("end_time"),
        "duration_minutes": data.get("duration_minutes"),
        "affected_apis": data.get("affected_apis", []),
        "root_cause": data.get("root_cause"),
        "fix_applied": data.get("fix_applied"),
        "prevention_steps": data.get("prevention_steps"),
        "related_commits": data.get("related_commits", []),
        "related_issues": data.get("related_issues", []),
        "created_by": data.get("created_by"),
        "created_at": now_isoutc()
    }
    
    db.incident_reports.insert_one(incident_doc)
    serialize_objectid(incident_doc)
    
    return jsonify({"success": True, "incident": incident_doc})

@app.route("/api/incidents", methods=["GET"])
def get_incidents():
    """Get all incident reports"""
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    
    incidents = list(db.incident_reports.find().sort("created_at", -1).limit(50))
    
    for incident in incidents:
        serialize_objectid(incident)
    
    return jsonify(incidents)

# --- GITHUB SETTINGS APIs ---

@app.route("/api/github/settings", methods=["POST"])
def save_github_settings():
    """Save or update GitHub repository settings including token"""
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    
    data = request.json or {}
    repo_owner = data.get("repo_owner", "").strip()
    repo_name = data.get("repo_name", "").strip()
    github_token = data.get("github_token", "").strip()
    
    if not repo_owner or not repo_name:
        return jsonify({"error": "repo_owner and repo_name are required"}), 400
    
    try:
        settings_doc = {
            "user_id": "default_user",  # Can be extended for multi-user
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "updated_at": now_isoutc()
        }
        
        # Only update token if provided (for security, don't overwrite with empty)
        if github_token:
            settings_doc["github_token"] = github_token
        
        # Upsert: update if exists, insert if not
        db.github_settings.update_one(
            {"user_id": "default_user"},
            {"$set": settings_doc},
            upsert=True
        )
        
        return jsonify({
            "success": True,
            "message": "GitHub settings saved successfully",
            "settings": {
                "repo_owner": repo_owner,
                "repo_name": repo_name,
                "has_token": bool(github_token)
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/github/settings", methods=["GET"])
def get_github_settings():
    """Get saved GitHub repository settings (token masked for security)"""
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    
    try:
        settings = db.github_settings.find_one({"user_id": "default_user"})
        
        if settings:
            serialize_objectid(settings)
            # Mask token for security - only show if it exists
            if "github_token" in settings:
                settings["has_token"] = True
                settings["github_token"] = "****" + settings["github_token"][-4:] if len(settings["github_token"]) > 4 else "****"
            else:
                settings["has_token"] = False
            return jsonify(settings)
        else:
            return jsonify({"repo_owner": "", "repo_name": "", "has_token": False})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/github/export-dataset", methods=["POST"])
def export_monitoring_dataset():
    """Export monitoring data as CSV and push to GitHub repository"""
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    
    try:
        # Get GitHub settings
        settings = db.github_settings.find_one({"user_id": "default_user"})
        if not settings:
            return jsonify({"error": "GitHub settings not configured. Please save settings first."}), 400
        
        repo_owner = settings.get("repo_owner")
        repo_name = settings.get("repo_name")
        
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            return jsonify({"error": "GITHUB_TOKEN not configured in environment"}), 500
        
        # Get monitoring data from last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        logs = list(db.monitoring_logs.find({
            "timestamp": {"$gte": thirty_days_ago.isoformat()}
        }).sort("timestamp", -1).limit(10000))
        
        if not logs:
            return jsonify({"error": "No monitoring data found"}), 404
        
        # Convert to CSV format
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "timestamp", "api_id", "url", "status_code", "is_up", 
            "total_latency_ms", "dns_latency_ms", "tcp_latency_ms", 
            "tls_latency_ms", "server_processing_latency_ms", 
            "content_download_latency_ms", "error_message", "url_type"
        ])
        
        # Write data rows
        for log in logs:
            writer.writerow([
                log.get("timestamp", ""),
                log.get("api_id", ""),
                log.get("url", ""),
                log.get("status_code", ""),
                log.get("is_up", False),
                log.get("total_latency_ms", 0),
                log.get("dns_latency_ms", 0),
                log.get("tcp_latency_ms", 0),
                log.get("tls_latency_ms", 0),
                log.get("server_processing_latency_ms", 0),
                log.get("content_download_latency_ms", 0),
                log.get("error_message", ""),
                log.get("url_type", "")
            ])
        
        csv_content = output.getvalue()
        
        # Push to GitHub using GitHub API
        import requests
        import base64
        
        file_path = "datasets/monitoring_data.csv"
        api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
        
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Check if file exists to get SHA
        existing_file = requests.get(api_url, headers=headers)
        sha = None
        if existing_file.status_code == 200:
            sha = existing_file.json().get("sha")
        
        # Prepare payload
        payload = {
            "message": f"Update monitoring dataset - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
            "content": base64.b64encode(csv_content.encode()).decode(),
            "branch": "main"
        }
        
        if sha:
            payload["sha"] = sha
        
        # Push to GitHub
        response = requests.put(api_url, headers=headers, json=payload)
        
        if response.status_code in [200, 201]:
            return jsonify({
                "success": True,
                "message": "Dataset exported to GitHub successfully",
                "file_url": response.json().get("content", {}).get("html_url"),
                "records_exported": len(logs)
            })
        else:
            return jsonify({
                "error": f"GitHub API error: {response.status_code}",
                "details": response.json()
            }), response.status_code
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/context/<api_id>")
def get_developer_context(api_id):
    """Get all developer context for an API"""
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    
    try:
        # Get latest monitoring log
        latest_log = db.monitoring_logs.find_one(
            {"api_id": api_id},
            sort=[("timestamp", -1)]
        )
        
        if not latest_log:
            return jsonify({"error": "No logs found"}), 404
        
        # Get or create correlation
        correlation_engine = CorrelationEngine(db)
        correlation = db.data_correlations.find_one({
            "monitoring_log_id": str(latest_log["_id"])
        })
        
        if not correlation:
            # Create correlation
            correlation = correlation_engine.correlate_monitoring_event(latest_log)
        
        if not correlation:
            return jsonify({"commits": [], "issues": [], "logs": [], "incidents": []})
        
        # Fetch related data
        commits = list(db.git_commits.find({
            "commit_id": {"$in": correlation.get("commit_ids", [])}
        }))
        
        issues = list(db.issues.find({
            "issue_id": {"$in": correlation.get("issue_ids", [])}
        }))
        
        logs = []
        for log_id in correlation.get("log_ids", []):
            try:
                log = db.application_logs.find_one({"_id": ObjectId(log_id)})
                if log:
                    logs.append(log)
            except:
                pass
        
        incidents = list(db.incident_reports.find({
            "incident_id": {"$in": correlation.get("incident_ids", [])}
        }))
        
        # Serialize all
        for commit in commits:
            serialize_objectid(commit)
        for issue in issues:
            serialize_objectid(issue)
        for log in logs:
            serialize_objectid(log)
        for incident in incidents:
            serialize_objectid(incident)
        
        return jsonify({
            "commits": commits,
            "issues": issues,
            "logs": logs,
            "incidents": incidents,
            "correlation_score": correlation.get("correlation_score", 0)
        })
        
    except Exception as e:
        print(f"[Context API] Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- AI/ML PREDICTION APIs ---

@app.route("/api/ai/train", methods=["POST"])
def train_ai_model():
    """
    Train AI model by calling separate training service
    Always uses FULL training (50 epochs) since it runs on separate port
    """
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    
    data = request.json or {}
    api_id = data.get("api_id")
    force_retrain = data.get("force_retrain", False)
    
    if not api_id:
        return jsonify({"error": "api_id required"}), 400
    
    try:
        # Always use FULL training (runs on separate port, won't block)
        endpoint = f"{AI_TRAINING_SERVICE_URL}/train/full"
        print(f"[AI Train] FULL training requested for API {api_id}")
        
        # Call training service (non-blocking, runs on separate port)
        try:
            response = requests.post(
                endpoint,
                json={"api_id": api_id, "force_retrain": force_retrain},
                timeout=1  # Don't wait for response, just trigger
            )
        except requests.exceptions.Timeout:
            # Timeout is expected - training is running in background
            pass
        except requests.exceptions.ConnectionError:
            return jsonify({
                "error": "AI Training Service not available. Please start it on port 5001"
            }), 503
        
        # Update last_ai_training timestamp immediately
        from bson import ObjectId
        db.monitored_apis.update_one(
            {"_id": ObjectId(api_id)},
            {"$set": {"last_ai_training": datetime.utcnow()}}
        )
        
        return jsonify({
            "success": True,
            "message": "Full training started on separate service (Port 5001)",
            "mode": "full",
            "epochs": 50,
            "service_port": 5001
        })
        
    except Exception as e:
        print(f"[AI Train] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/ai/predict/<api_id>")
def predict_failure(api_id):
    """Predict if API will fail in next hour"""
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    
    try:
        ai = AIPredictor(db)
        prediction = ai.predict_failure(api_id)
        return jsonify(prediction)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/ai/anomalies/<api_id>")
def detect_anomalies(api_id):
    """Detect anomalies in API performance"""
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    
    hours = request.args.get("hours", 24, type=int)
    
    try:
        ai = AIPredictor(db)
        anomalies = ai.detect_anomalies(api_id, hours)
        return jsonify(anomalies)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/ai/insights/<api_id>")
def get_ai_insights(api_id):
    """Get AI-generated insights and recommendations.

    This endpoint now also stores a richer, LLM-style summary in MongoDB
    (ai_insights collection) while preserving the existing card-style
    insights array used by the frontend.
    """
    if db is None:
        return jsonify({"error": "Database not connected"}), 500

    try:
        ai = AIPredictor(db)

        # Core prediction used for narrative + metrics
        prediction = ai.predict_failure(api_id)

        # Existing card-style insights for the UI
        insights = ai.generate_insights(api_id) or []

        # Build an LLM-style natural language summary
        try:
            failure_prob = float(prediction.get("failure_probability") or 0.0)
        except (TypeError, ValueError):
            failure_prob = 0.0

        try:
            confidence = float(prediction.get("confidence") or 0.0)
        except (TypeError, ValueError):
            confidence = 0.0

        risk_score = int(prediction.get("risk_score") or round(failure_prob * 100))
        category = prediction.get("category") or "API"
        risk_level = (prediction.get("risk_level") or
                      ("high" if failure_prob >= 0.70 else
                       "medium" if failure_prob >= 0.40 else
                       "low"))
        model_name = prediction.get("model") or "LSTM + Autoencoder"
        last_trained = prediction.get("last_trained")
        model_accuracy = prediction.get("model_accuracy")
        model_auc = prediction.get("model_auc")
        risk_factors = prediction.get("risk_factors") or []

        # High-level narrative
        summary_parts = []
        summary_parts.append(
            f"The {category} is currently assessed as {risk_level.upper()} risk "
            f"with a risk score of {risk_score}/100 and estimated failure probability "
            f"around {failure_prob*100:.1f}% (confidence ~{confidence*100:.0f}%)."
        )

        if last_trained:
            summary_parts.append(
                f"The model {model_name} was last trained at {last_trained}."
            )
        else:
            summary_parts.append(
                f"The model {model_name} has limited training metadata available; "
                f"results should be interpreted with caution."
            )

        if isinstance(model_accuracy, (int, float)) or isinstance(model_auc, (int, float)):
            acc_txt = f"accuracy ~{model_accuracy*100:.1f}%" if isinstance(model_accuracy, (int, float)) else None
            auc_txt = f"AUC ~{model_auc:.3f}" if isinstance(model_auc, (int, float)) else None
            perf_bits = ", ".join(bit for bit in [acc_txt, auc_txt] if bit)
            if perf_bits:
                summary_parts.append(f"Training performance: {perf_bits}.")

        if risk_factors:
            summary_parts.append(
                "Key contributing factors include: " + "; ".join(risk_factors[:3]) + "."
            )
        elif prediction.get("reason"):
            summary_parts.append(prediction["reason"])

        summary_text = " ".join(summary_parts)

        # Recommended actions for operators
        actions = [
            "Review recent deployments and code changes touching this API.",
            "Monitor latency, error rate, and HTTP status trends closely.",
            "Inspect logs around recent anomalies for root-cause clues.",
        ]

        # Store structured insight in MongoDB (best-effort; ignore failures)
        try:
            insight_payload = {
                "summary": summary_text,
                "details": prediction.get("reason"),
                "risk_level": risk_level,
                "confidence": confidence,
                "risk_score": risk_score,
                "training_session_id": None,
                "model_version": prediction.get("model_version"),
                "actions": actions,
                "metrics": {
                    "failure_probability": failure_prob,
                    "model_accuracy": model_accuracy,
                    "model_auc": model_auc,
                },
                "raw_prediction": prediction,
            }
            store_ai_insight(api_id, insight_payload)
        except Exception as store_err:
            print(f"[AI Insights] Failed to store insight: {store_err}")

        # Prepend a summary card so the UI shows a clear narrative first
        insights = list(insights)  # ensure list copy
        insights.insert(0, {
            "type": "summary",
            "title": "AI Summary",
            "message": summary_text,
            "details": prediction.get("reason") or "",
            "action": actions[0],
        })

        return jsonify(insights)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ai/insights/history/<api_id>")
def get_ai_insights_history(api_id):
    """Return stored AI insight history for an API from MongoDB."""
    if db is None:
        return jsonify({"error": "Database not connected"}), 500

    try:
        history = get_ai_insights_from_db(api_id, limit=20)
        return jsonify(history)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/ai/similar_incidents", methods=["POST"])
def find_similar_incidents():
    """Find similar past incidents"""
    if db is None:
        return jsonify({"error": "Database not connected"}), 500
    
    data = request.json or {}
    current_issue = data.get("issue", "")
    
    if not current_issue:
        return jsonify({"error": "Issue description required"}), 400
    
    try:
        ai = AIPredictor(db)
        similar = ai.find_similar_incidents(current_issue)
        
        # Serialize ObjectIds
        for item in similar:
            if "incident" in item:
                serialize_objectid(item["incident"])
        
        return jsonify(similar)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Main Execution ---
if __name__ == "__main__":
    if not init_mongodb():
        print("[ERROR] Failed to initialize MongoDB. Exiting...")
        exit(1)
    
    try:
        monitor_thread = threading.Thread(target=monitor_worker, daemon=True)
        monitor_thread.start()
        print("[Monitor] Background thread started.")
    except Exception as e:
        print(f"[Monitor ERROR] Could not start monitor thread: {e}")
    
    try:
        app.run(port=5000, debug=True, use_reloader=False)
    except Exception as e:
        print(f"[Flask ERROR] Could not start Flask app: {e}")
