"""Auto-extracted route module from src/app.py."""

_registered = False

def register_routes(app, deps):
    globals().update(deps)
    global _registered
    if _registered:
        return
    _registered = True
    @app.route("/api/sync/github", methods=["POST"])
    @require_logged_in_api
    def sync_github():
        """Sync commits and PRs from GitHub using stored settings"""
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        
        data = request.json or {}
        repo_owner = data.get("repo_owner")
        repo_name = data.get("repo_name")
        since_days = data.get("since_days", 7)
        user_id = get_current_user_id()
        
        # If not provided in request, get from stored settings
        if not repo_owner or not repo_name:
            settings = db.github_settings.find_one({"user_id": user_id})
            if settings:
                repo_owner = settings.get("repo_owner")
                repo_name = settings.get("repo_name")
        
        if not repo_owner or not repo_name:
            return jsonify({"error": "repo_owner and repo_name required. Please save settings first."}), 400
        
        # Try to get token from stored settings first, then fall back to env variable
        github_token = None
        settings = db.github_settings.find_one({"user_id": user_id})
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
    @require_logged_in_api
    def sync_issues():
        """Sync issues from GitHub using stored settings"""
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        
        data = request.json or {}
        repo_owner = data.get("repo_owner")
        repo_name = data.get("repo_name")
        user_id = get_current_user_id()
        
        # If not provided in request, get from stored settings
        if not repo_owner or not repo_name:
            settings = db.github_settings.find_one({"user_id": user_id})
            if settings:
                repo_owner = settings.get("repo_owner")
                repo_name = settings.get("repo_name")
        
        if not repo_owner or not repo_name:
            return jsonify({"error": "repo_owner and repo_name required. Please save settings first."}), 400
        
        # Try to get token from stored settings first, then fall back to env variable
        github_token = None
        settings = db.github_settings.find_one({"user_id": user_id})
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



    @app.route("/api/github/settings", methods=["POST"])
    @require_logged_in_api
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
            user_id = get_current_user_id()
            settings_doc = {
                "user_id": user_id,
                "repo_owner": repo_owner,
                "repo_name": repo_name,
                "updated_at": now_isoutc()
            }
            
            # Only update token if provided (for security, don't overwrite with empty)
            if github_token:
                settings_doc["github_token"] = github_token
            
            # Upsert: update if exists, insert if not
            db.github_settings.update_one(
                {"user_id": user_id},
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
    @require_logged_in_api
    def get_github_settings():
        """Get saved GitHub repository settings (token masked for security)"""
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        
        try:
            settings = db.github_settings.find_one({"user_id": get_current_user_id()})
            
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
    @require_logged_in_api
    def export_monitoring_dataset():
        """Export monitoring data as CSV and push to GitHub repository"""
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        
        try:
            user_id = get_current_user_id()
            # Get GitHub settings
            settings = db.github_settings.find_one({"user_id": user_id})
            if not settings:
                return jsonify({"error": "GitHub settings not configured. Please save settings first."}), 400
            
            repo_owner = settings.get("repo_owner")
            repo_name = settings.get("repo_name")
            
            github_token = settings.get("github_token") or os.getenv("GITHUB_TOKEN")
            if not github_token:
                return jsonify({"error": "GitHub token not configured in settings or environment"}), 500
            
            # Get monitoring data from last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            logs = list(db.monitoring_logs.find({
                "timestamp": {"$gte": thirty_days_ago.isoformat()},
                "user_id": user_id,
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



    @app.route("/api/commits", methods=["GET"])
    @require_logged_in_api
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
    @require_logged_in_api
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
    @require_logged_in_api
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
    @require_logged_in_api
    def create_incident():
        """Create a new incident report"""
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        
        data = request.json or {}
        user_id = get_current_user_id()
        
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
            "user_id": user_id,
            "created_at": now_isoutc()
        }
        
        db.incident_reports.insert_one(incident_doc)
        serialize_objectid(incident_doc)
        
        return jsonify({"success": True, "incident": incident_doc})

    @app.route("/api/incidents", methods=["GET"])
    @require_logged_in_api
    def get_incidents():
        """Get all incident reports"""
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        
        incidents = list(db.incident_reports.find({"user_id": get_current_user_id()}).sort("created_at", -1).limit(50))
        
        for incident in incidents:
            serialize_objectid(incident)
        
        return jsonify(incidents)

    # --- GITHUB SETTINGS APIs ---

    @app.route("/api/context/<api_id>")
    @require_logged_in_api
    def get_developer_context(api_id):
        """Get all developer context for an API"""
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        
        try:
            user_id = get_current_user_id()
            api_doc, api_error = ensure_api_access_or_error(api_id, user_id)
            if api_error:
                return api_error
            # Get latest monitoring log
            latest_log = db.monitoring_logs.find_one(
                {"api_id": api_id, "user_id": user_id},
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
