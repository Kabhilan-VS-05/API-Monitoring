"""Auto-extracted route module from src/app.py."""

_registered = False

def register_routes(app, deps):
    globals().update(deps)
    global _registered
    if _registered:
        return
    _registered = True
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
        network_check = perform_network_speed_check(timeout=NETWORK_TEST_TIMEOUT_SECONDS)

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

        network_is_up = bool(network_check.get("network_up") or not network_check.get("error"))
        if not network_is_up and not res.get("up"):
            res["error"] = f"Low network: {network_check.get('error') or res.get('error') or 'connectivity issue'}"
            res["url_type"] = "Network"
            res["low_network"] = True
        else:
            res["low_network"] = False

        res.update({
            "api_url": api_url,
            "header_name": h_name or "",
            "header_value": h_val or "",
            "network_check": network_check
        })

        if not bool(res.get("up")):
            root_hint = classify_root_cause({
                "status_code": res.get("status_code"),
                "error_message": res.get("error"),
                "is_up": res.get("up"),
                "dns_latency_ms": res.get("dns_latency_ms"),
                "tls_latency_ms": res.get("tls_latency_ms"),
                "check_skipped": bool(res.get("low_network")),
                "skip_reason": "network_unavailable" if bool(res.get("low_network")) else None,
                "network_is_up": network_is_up,
            })
            res["root_cause_hint"] = root_hint
            res["root_cause_details"] = ROOT_CAUSE_DESCRIPTIONS.get(root_hint, ROOT_CAUSE_DESCRIPTIONS["unknown"])
        else:
            res["root_cause_hint"] = None
            res["root_cause_details"] = None
        
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
    @require_logged_in_api
    def get_monitors():
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        
        try:
            user_id = get_current_user_id()
            monitored_apis = db.monitored_apis
            monitoring_logs = db.monitoring_logs
            
            monitors = list(monitored_apis.find({"user_id": user_id}).sort([("category", ASCENDING), ("url", ASCENDING)]))
            
            for monitor in monitors:
                monitor = serialize_objectid(monitor)
                api_id = monitor["id"]

                slo_metrics = compute_slo_metrics(api_id)
                monitor["avg_latency_24h"] = slo_metrics.get("avg_latency_24h", 0.0)
                monitor["uptime_pct_24h"] = slo_metrics.get("uptime_pct_24h", 100.0)
                monitor["p95_latency_24h"] = slo_metrics.get("p95_latency_24h", 0.0)
                monitor["slo_target_uptime_pct"] = slo_metrics.get("slo_target_uptime_pct", SLO_TARGET_UPTIME_PCT)
                monitor["error_budget_remaining_pct"] = slo_metrics.get("error_budget_remaining_pct", 100.0)
                monitor["error_budget_consumed_pct"] = slo_metrics.get("error_budget_consumed_pct", 0.0)
                monitor["burn_rate_1h"] = slo_metrics.get("burn_rate_1h", 0.0)
                monitor["burn_rate_6h"] = slo_metrics.get("burn_rate_6h", 0.0)
                monitor["burn_rate_alert_level"] = slo_metrics.get("burn_rate_alert_level", "none")
                monitor["burn_rate_alert_message"] = slo_metrics.get("burn_rate_alert_message", "No burn-rate alert")

                # Recent checks
                recent = list(monitoring_logs.find({
                    "api_id": api_id,
                    "user_id": user_id,
                    "check_skipped": {"$ne": True}
                }).sort("timestamp", DESCENDING).limit(15))
                monitor['recent_checks'] = [
                    {'is_up': r['is_up'], 'timestamp': r['timestamp']} 
                    for r in reversed(recent)
                ]

                latest_failed = monitoring_logs.find_one(
                    {"api_id": api_id, "user_id": user_id, "is_up": False},
                    sort=[("timestamp", DESCENDING)]
                )
                monitor["last_root_cause_hint"] = (latest_failed or {}).get("root_cause_hint")
                monitor["last_root_cause_details"] = (latest_failed or {}).get("root_cause_details")

            return jsonify(monitors)

        except Exception as e:
            print(f"[DB ERROR] Failed to fetch dashboard monitors: {e}")
            return jsonify({"error": "Failed to retrieve monitor data from server."}), 500

    @app.route("/api/advanced/add_monitor", methods=["POST"])
    @require_logged_in_api
    def add_monitor():
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        
        user = get_current_user()
        user_id = str(user["_id"])
        plan = normalize_subscription_plan(user.get("subscription_plan"))
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

        if is_premium_frequency(freq) and not is_subscriber(plan):
            return jsonify({
                "error": "30s, 10s, 5s, and 1s intervals are subscriber-only",
                "subscription": subscription_features(plan),
            }), 403
        
        monitored_apis = db.monitored_apis

        if not is_subscriber(plan):
            monitor_count = monitored_apis.count_documents({"user_id": user_id})
            if monitor_count >= FREE_MAX_MONITORS:
                return jsonify({
                    "error": f"Free plan limit reached ({FREE_MAX_MONITORS} monitors). Upgrade for unlimited monitors.",
                    "subscription": subscription_features(plan),
                }), 403
        
        # Check if URL already exists
        if monitored_apis.find_one({"url": url, "user_id": user_id}):
            return jsonify({"error": "This URL is already monitored."}), 409
        
        monitor_doc = {
            "user_id": user_id,
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
        return jsonify({
            "success": True,
            "message": "Monitor added successfully.",
            "subscription": subscription_features(plan),
        })

    @app.route("/api/advanced/update_monitor", methods=["POST"])
    @require_logged_in_api
    def update_monitor():
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        
        user = get_current_user()
        user_id = str(user["_id"])
        plan = normalize_subscription_plan(user.get("subscription_plan"))
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

        if is_premium_frequency(freq) and not is_subscriber(plan):
            return jsonify({
                "error": "30s, 10s, 5s, and 1s intervals are subscriber-only",
                "subscription": subscription_features(plan),
            }), 403
        
        monitored_apis = db.monitored_apis
        result = monitored_apis.update_one(
            {"_id": ObjectId(data["id"]), "user_id": user_id},
            {"$set": {
                "url": url,
                "category": data.get("category"),
                "header_name": data.get("header_name"),
                "header_value": data.get("header_value"),
                "check_frequency_minutes": freq,
                "notification_email": data.get("notification_email")
            }}
        )
        if result.matched_count == 0:
            return jsonify({"error": "Monitor not found or access denied"}), 404
        
        return jsonify({"success": True, "message": "Monitor updated successfully."})

    @app.route("/api/advanced/delete_monitor", methods=["POST"])
    @require_logged_in_api
    def delete_monitor():
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        
        data = request.json or {}
        if "id" not in data: 
            return jsonify({"error": "'id' is required"}), 400
        user_id = get_current_user_id()
        
        monitored_apis = db.monitored_apis
        monitoring_logs = db.monitoring_logs
        
        api_id = data["id"]
        deleted = monitored_apis.delete_one({"_id": ObjectId(api_id), "user_id": user_id})
        if deleted.deleted_count == 0:
            return jsonify({"error": "Monitor not found or access denied"}), 404
        monitoring_logs.delete_many({"api_id": api_id, "user_id": user_id})
        
        return jsonify({"success": True})

    @app.route("/api/advanced/history")
    @require_logged_in_api
    def get_history():
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        
        api_id = request.args.get("id")
        if not api_id: 
            return jsonify({"error": "'id' (api_id) is required"}), 400
        user_id = get_current_user_id()
        api_doc, api_error = ensure_api_access_or_error(api_id, user_id)
        if api_error:
            return api_error
        
        page = request.args.get("page", 1, type=int)
        per_page = 15
        
        monitoring_logs = db.monitoring_logs
        total_items = monitoring_logs.count_documents({"api_id": api_id, "user_id": user_id})
        skip = (page - 1) * per_page
        
        logs = list(monitoring_logs.find({"api_id": api_id, "user_id": user_id}).sort("timestamp", DESCENDING).skip(skip).limit(per_page))
        
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
    @require_logged_in_api
    def get_last_checks(api_id):
        if db is None:
            return jsonify([])
        user_id = get_current_user_id()
        api_doc, api_error = ensure_api_access_or_error(api_id, user_id)
        if api_error:
            return api_error
        
        monitoring_logs = db.monitoring_logs
        logs = list(monitoring_logs.find({
            "api_id": api_id,
            "user_id": user_id,
            "check_skipped": {"$ne": True}
        }).sort("timestamp", DESCENDING).limit(15))
        
        result = [{"is_up": bool(log.get("is_up"))} for log in logs]
        return jsonify(result)

    @app.route("/api/advanced/log_details/<log_id>")
    @require_logged_in_api
    def get_log_details(log_id):
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        
        monitoring_logs = db.monitoring_logs
        log = monitoring_logs.find_one({"_id": ObjectId(log_id), "user_id": get_current_user_id()})
        
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
    @require_logged_in_api
    def get_uptime_history(api_id):
        """Calculates daily uptime percentage for the last 90 days."""
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        
        monitoring_logs = db.monitoring_logs
        user_id = get_current_user_id()
        api_doc, api_error = ensure_api_access_or_error(api_id, user_id)
        if api_error:
            return api_error
        ninety_days_ago = (datetime.utcnow() - timedelta(days=90)).isoformat() + "Z"
        
        try:
            pipeline = [
                {"$match": {
                    "api_id": api_id,
                    "user_id": user_id,
                    "timestamp": {"$gte": ninety_days_ago},
                    "check_skipped": {"$ne": True}
                }},
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


    @app.route("/api/advanced/slo/<api_id>")
    @require_logged_in_api
    def get_slo_metrics(api_id):
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        try:
            user_id = get_current_user_id()
            api_doc, api_error = ensure_api_access_or_error(api_id, user_id)
            if api_error:
                return api_error
            metrics = compute_slo_metrics(api_id)
            metrics["api_id"] = api_id
            return jsonify(metrics)
        except Exception as e:
            return jsonify({"error": str(e)}), 500


    @app.route("/api/advanced/slo_summary")
    @require_logged_in_api
    def get_slo_summary():
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        try:
            user_id = get_current_user_id()
            monitors = list(db.monitored_apis.find({"is_active": True, "user_id": user_id}, {"url": 1}))
            summary = {
                "total_monitors": len(monitors),
                "critical_burn_rate": 0,
                "warning_burn_rate": 0,
                "avg_uptime_pct_24h": 100.0,
                "avg_error_budget_remaining_pct": 100.0,
            }
            if not monitors:
                return jsonify(summary)

            uptime_values = []
            budget_values = []
            for monitor in monitors:
                api_id = str(monitor["_id"])
                metrics = compute_slo_metrics(api_id)
                uptime_values.append(metrics.get("uptime_pct_24h", 100.0))
                budget_values.append(metrics.get("error_budget_remaining_pct", 100.0))
                level = metrics.get("burn_rate_alert_level")
                if level == "critical":
                    summary["critical_burn_rate"] += 1
                elif level == "warning":
                    summary["warning_burn_rate"] += 1

            summary["avg_uptime_pct_24h"] = round(sum(uptime_values) / len(uptime_values), 2) if uptime_values else 100.0
            summary["avg_error_budget_remaining_pct"] = round(sum(budget_values) / len(budget_values), 2) if budget_values else 100.0
            return jsonify(summary)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
