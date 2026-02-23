"""Auto-extracted route module from src/app.py."""

_registered = False

def register_routes(app, deps):
    globals().update(deps)
    global _registered
    if _registered:
        return
    _registered = True
    @app.route("/api/alert-status/<api_id>", methods=["GET"])
    @require_logged_in_api
    def get_alert_status(api_id):
        """Get current alert status for an API (downtime alerts + AI predictions)"""
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        
        try:
            user_id = get_current_user_id()
            api_doc, api_error = ensure_api_access_or_error(api_id, user_id)
            if api_error:
                return api_error
            result = {
                "downtime_alert": None,
                "ai_prediction": None,
                "burn_rate_alert": None
            }
            
            # Check for open downtime alert
            downtime_alert = db.alert_history.find_one({
                "api_id": api_id,
                "user_id": user_id,
                "status": "open",
                "alert_type": "downtime"
            })
            
            if downtime_alert:
                result["downtime_alert"] = {
                    "created_at": downtime_alert.get("created_at"),
                    "github_issue_number": downtime_alert.get("github_issue_number"),
                    "github_issue_url": downtime_alert.get("github_issue_url"),
                    "reason": downtime_alert.get("reason"),
                    "incident_id": downtime_alert.get("incident_id"),
                    "root_cause_hint": downtime_alert.get("root_cause_hint"),
                }
            
            # Check for AI prediction alert
            ai_alert = db.alert_history.find_one({
                "api_id": api_id,
                "user_id": user_id,
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

            burn_rate_alert = db.alert_history.find_one({
                "api_id": api_id,
                "user_id": user_id,
                "status": "open",
                "alert_type": "burn_rate"
            })
            if burn_rate_alert:
                result["burn_rate_alert"] = {
                    "severity": burn_rate_alert.get("severity"),
                    "reason": burn_rate_alert.get("reason"),
                    "burn_rate_1h": burn_rate_alert.get("burn_rate_1h"),
                    "burn_rate_6h": burn_rate_alert.get("burn_rate_6h"),
                    "error_budget_remaining_pct": burn_rate_alert.get("error_budget_remaining_pct"),
                    "created_at": burn_rate_alert.get("created_at"),
                    "updated_at": burn_rate_alert.get("updated_at"),
                }

            incident_status = db.alert_incidents.find_one(
                {"api_id": api_id, "user_id": user_id, "status": "open"},
                sort=[("created_at", DESCENDING)]
            )
            if incident_status:
                result["incident_status"] = {
                    "incident_id": incident_status.get("incident_id"),
                    "status": incident_status.get("status"),
                    "created_at": incident_status.get("created_at"),
                    "last_seen_at": incident_status.get("last_seen_at"),
                    "failure_events": incident_status.get("failure_events", 0),
                    "suppressed_alerts": incident_status.get("suppressed_alerts", 0),
                    "root_cause_hint": incident_status.get("root_cause_hint"),
                    "latest_reason": incident_status.get("latest_reason"),
                }
            else:
                result["incident_status"] = None

            result["worker_responses"] = fetch_worker_responses(api_id, limit=5, user_id=user_id)
            # Don't try to predict on-demand, just show if alert exists
            # AI predictions happen in background every 20 minutes

            return jsonify(result)
            
        except Exception as e:
            print(f"[Alert Status] Error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/worker-responses/<api_id>")
    @require_logged_in_api
    def get_worker_responses(api_id):
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        limit = request.args.get("limit", 20, type=int)
        limit = min(max(limit, 1), 100)
        try:
            user_id = get_current_user_id()
            api_doc, api_error = ensure_api_access_or_error(api_id, user_id)
            if api_error:
                return api_error
            responses = fetch_worker_responses(api_id, limit=limit, user_id=user_id)
            return jsonify(responses)
        except Exception as e:
            print(f"[Worker Responses] Error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/github/create-downtime-alert", methods=["POST"])
    @require_logged_in_api
    def create_downtime_alert():
        """Create a GitHub issue for API downtime"""
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        
        data = request.json or {}
        api_id = data.get("api_id")
        user_id = get_current_user_id()
        
        if not api_id:
            return jsonify({"error": "api_id required"}), 400
        
        # Get GitHub settings
        settings = db.github_settings.find_one({"user_id": user_id})
        if not settings:
            return jsonify({"error": "GitHub settings not configured"}), 400
        
        repo_owner = settings.get("repo_owner")
        repo_name = settings.get("repo_name")
        github_token = settings.get("github_token") or os.getenv("GITHUB_TOKEN")
        
        if not github_token:
            return jsonify({"error": "GitHub token not configured"}), 500
        
        try:
            # Get API details
            api = db.monitored_apis.find_one({"_id": ObjectId(api_id), "user_id": user_id})
            if not api:
                return jsonify({"error": "API not found"}), 404

            latest_log = db.monitoring_logs.find_one(
                {"api_id": api_id, "user_id": user_id, "is_up": False, "check_skipped": {"$ne": True}},
                sort=[("timestamp", -1)]
            )
            if not latest_log:
                return jsonify({"error": "No downtime detected"}), 404

            # Reuse unified alert pipeline so manual triggers and auto alerts behave identically.
            alert_manager = AlertManager(db)
            reason = (
                f"Manual alert request: API downtime detected "
                f"(root cause hint: {latest_log.get('root_cause_hint') or 'unknown'})"
            )
            result = alert_manager.create_downtime_alert(api_id, api["url"], reason)
            if not result:
                return jsonify({"error": "No downtime detected"}), 404
            if not result.get("success"):
                return jsonify(result), 500
            return jsonify(result), 201
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

