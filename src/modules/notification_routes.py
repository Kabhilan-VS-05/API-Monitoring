"""Auto-extracted route module from src/app.py."""

_registered = False

def register_routes(app, deps):
    globals().update(deps)
    global _registered
    if _registered:
        return
    _registered = True
    @app.route("/notify/whatsapp/send", methods=["POST"])
    @require_subscriber_api
    def notify_whatsapp_send():
        if db is None:
            return jsonify({"error": "Database not connected"}), 500

        payload = request.json or {}
        phone_number = payload.get("phone_number")
        api_id = payload.get("api_id")
        alert_id = payload.get("alert_id")
        if not phone_number or not api_id or not alert_id:
            return jsonify({"error": "phone_number, api_id, and alert_id are required"}), 400
        user_id = get_current_user_id()
        api_doc, api_error = ensure_api_access_or_error(api_id, user_id)
        if api_error:
            return api_error

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
    @require_subscriber_api
    def notify_sms_send():
        if db is None:
            return jsonify({"error": "Database not connected"}), 500

        payload = request.json or {}
        phone_number = payload.get("phone_number")
        api_id = payload.get("api_id")
        alert_id = payload.get("alert_id")
        if not phone_number or not api_id or not alert_id:
            return jsonify({"error": "phone_number, api_id, and alert_id are required"}), 400
        user_id = get_current_user_id()
        api_doc, api_error = ensure_api_access_or_error(api_id, user_id)
        if api_error:
            return api_error

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
    @require_subscriber_api
    def notify_ivr_call():
        if db is None:
            return jsonify({"error": "Database not connected"}), 500

        payload = request.json or {}
        phone_number = payload.get("phone_number")
        api_id = payload.get("api_id")
        alert_id = payload.get("alert_id")
        if not phone_number or not api_id or not alert_id:
            return jsonify({"error": "phone_number, api_id, and alert_id are required"}), 400
        user_id = get_current_user_id()
        api_doc, api_error = ensure_api_access_or_error(api_id, user_id)
        if api_error:
            return api_error

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
    @require_subscriber_api
    def utils_translate():
        payload = request.json or {}
        text = payload.get("text")
        target_language = payload.get("target_language", "EN")

        if not text:
            return jsonify({"error": "text is required"}), 400

        translated = translate_text(text, target_language)
        return jsonify({"translated_text": translated, "target_language": target_language.upper()})


    @app.route("/incident/acknowledge", methods=["POST"])
    @require_logged_in_api
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
            "user_id": get_current_user_id(),
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
