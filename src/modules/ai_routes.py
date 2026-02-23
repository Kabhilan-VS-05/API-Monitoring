"""Auto-extracted route module from src/app.py."""

_registered = False

def register_routes(app, deps):
    globals().update(deps)
    global _registered
    if _registered:
        return
    _registered = True
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
    @require_logged_in_api
    def list_training_runs(api_id):
        if db is None:
            return jsonify({"error": "Database not connected"}), 500

        limit = request.args.get("limit", 10, type=int)
        limit = min(max(limit, 1), 100)
        try:
            api_doc, api_error = ensure_api_access_or_error(api_id, get_current_user_id())
            if api_error:
                return api_error
            runs = get_training_runs_from_db(api_id, limit=limit, user_id=get_current_user_id())
            return jsonify(runs)
        except Exception as e:
            return jsonify({"error": str(e)}), 500


    @app.route("/api/ai/training_runs/latest/<api_id>")
    @require_logged_in_api
    def latest_training_run(api_id):
        if db is None:
            return jsonify({"error": "Database not connected"}), 500

        try:
            api_doc, api_error = ensure_api_access_or_error(api_id, get_current_user_id())
            if api_error:
                return api_error
            run = get_latest_training_run_from_db(api_id, user_id=get_current_user_id())
            if not run:
                return jsonify({"error": "No training runs found"}), 404
            return jsonify(run)
        except Exception as e:
            return jsonify({"error": str(e)}), 500


    @app.route("/api/ai/train", methods=["POST"])
    @require_logged_in_api
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
        user_id = get_current_user_id()
        api_doc, api_error = ensure_api_access_or_error(api_id, user_id)
        if api_error:
            return api_error
        
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
                {"_id": ObjectId(api_id), "user_id": user_id},
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
    @require_logged_in_api
    def predict_failure(api_id):
        """Predict if API will fail in next hour"""
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        
        try:
            api_doc, api_error = ensure_api_access_or_error(api_id, get_current_user_id())
            if api_error:
                return api_error
            ai = AIPredictor(db)
            prediction = ai.predict_failure(api_id)
            return jsonify(prediction)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/ai/anomalies/<api_id>")
    @require_logged_in_api
    def detect_anomalies(api_id):
        """Detect anomalies in API performance"""
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        
        hours = request.args.get("hours", 24, type=int)
        
        try:
            api_doc, api_error = ensure_api_access_or_error(api_id, get_current_user_id())
            if api_error:
                return api_error
            ai = AIPredictor(db)
            anomalies = ai.detect_anomalies(api_id, hours)
            return jsonify(anomalies)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/ai/insights/<api_id>")
    @require_logged_in_api
    def get_ai_insights(api_id):
        """Get AI-generated insights and recommendations.

        This endpoint now also stores a richer, LLM-style summary in MongoDB
        (ai_insights collection) while preserving the existing card-style
        insights array used by the frontend.
        """
        if db is None:
            return jsonify({"error": "Database not connected"}), 500

        try:
            api_doc, api_error = ensure_api_access_or_error(api_id, get_current_user_id())
            if api_error:
                return api_error
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
    @require_logged_in_api
    def get_ai_insights_history(api_id):
        """Return stored AI insight history for an API from MongoDB."""
        if db is None:
            return jsonify({"error": "Database not connected"}), 500

        try:
            api_doc, api_error = ensure_api_access_or_error(api_id, get_current_user_id())
            if api_error:
                return api_error
            history = get_ai_insights_from_db(api_id, limit=20, user_id=get_current_user_id())
            return jsonify(history)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/ai/similar_incidents", methods=["POST"])
    @require_logged_in_api
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
