"""Auto-extracted route module from src/app.py."""

_registered = False

def register_routes(app, deps):
    globals().update(deps)
    global _registered
    if _registered:
        return
    _registered = True
    @app.route("/auth")
    @app.route("/auth/login-page")
    def serve_auth_page():
        return send_from_directory(SIMPLE_STATIC_DIR, "auth.html")


    @app.route("/auth/register", methods=["POST"])
    def auth_register():
        if db is None:
            return jsonify({"error": "Database not connected"}), 500

        data = request.json or {}
        email = normalize_email(data.get("email"))
        password = data.get("password") or ""
        name = (data.get("name") or "").strip() or email.split("@")[0]
        requested_plan = normalize_subscription_plan(data.get("subscription_plan"))

        if not is_valid_email(email):
            return jsonify({"error": "Valid email is required"}), 400
        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400

        existing = db.auth_users.find_one({"email": email})
        if existing:
            if AUTH_REQUIRE_EMAIL_VERIFICATION and not existing.get("is_verified"):
                token = build_email_verification_token(email)
                sent, error = send_verification_email(email, token)
                db.auth_users.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {"verification_sent_at": now_isoutc(), "email_delivery_error": error, "updated_at": now_isoutc()}},
                )
                payload = build_verification_delivery_payload(
                    {
                        "success": True,
                        "message": "Email already registered but not verified. Verification has been re-issued.",
                    },
                    token,
                    sent,
                    error,
                )
                return jsonify(payload), 200
            return jsonify({"error": "Email already registered"}), 409

        now = now_isoutc()
        user_doc = {
            "email": email,
            "name": name,
            "password_hash": generate_password_hash(password),
            "is_verified": not AUTH_REQUIRE_EMAIL_VERIFICATION,
            "subscription_plan": requested_plan if requested_plan == "subscriber" else "free",
            "subscription_status": "active",
            "created_at": now,
            "updated_at": now,
            "last_login_at": None,
        }
        result = db.auth_users.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id

        if AUTH_REQUIRE_EMAIL_VERIFICATION:
            token = build_email_verification_token(email)
            sent, error = send_verification_email(email, token)
            db.auth_users.update_one(
                {"_id": user_doc["_id"]},
                {"$set": {"verification_sent_at": now_isoutc(), "email_delivery_error": error}},
            )
            payload = build_verification_delivery_payload(
                {
                "success": True,
                "message": "Registered. Verify your email before login.",
                },
                token,
                sent,
                error,
            )
            return jsonify(payload), 201

        session.permanent = True
        session["user_id"] = str(user_doc["_id"])
        return jsonify({"success": True, "user": auth_user_payload(user_doc)}), 201


    @app.route("/auth/resend-verification", methods=["POST"])
    def auth_resend_verification():
        if db is None:
            return jsonify({"error": "Database not connected"}), 500

        data = request.json or {}
        email = normalize_email(data.get("email"))
        if not is_valid_email(email):
            return jsonify({"error": "Valid email is required"}), 400

        user = db.auth_users.find_one({"email": email})
        if not user:
            return jsonify({"error": "User not found"}), 404
        if user.get("is_verified"):
            return jsonify({"success": True, "message": "Email already verified"}), 200

        token = build_email_verification_token(email)
        sent, error = send_verification_email(email, token)
        db.auth_users.update_one(
            {"_id": user["_id"]},
            {"$set": {"verification_sent_at": now_isoutc(), "email_delivery_error": error}},
        )
        payload = build_verification_delivery_payload(
            {
                "success": True,
                "message": "Verification email sent" if sent else "Verification link generated for local use",
            },
            token,
            sent,
            error,
        )
        return jsonify(payload), 200


    @app.route("/auth/verify-email", methods=["GET"])
    def auth_verify_email():
        if db is None:
            return jsonify({"error": "Database not connected"}), 500

        token = request.args.get("token", "")
        if not token:
            return jsonify({"error": "Verification token is required"}), 400

        try:
            email = read_email_verification_token(token)
        except SignatureExpired:
            return jsonify({"error": "Verification token expired"}), 400
        except BadSignature:
            return jsonify({"error": "Invalid verification token"}), 400

        update = db.auth_users.update_one(
            {"email": email},
            {
                "$set": {
                    "is_verified": True,
                    "verified_at": now_isoutc(),
                    "updated_at": now_isoutc(),
                }
            },
        )
        if update.matched_count == 0:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"success": True, "message": "Email verified successfully"})


    @app.route("/auth/login", methods=["POST"])
    def auth_login():
        if db is None:
            return jsonify({"error": "Database not connected"}), 500

        data = request.json or {}
        email = normalize_email(data.get("email"))
        password = data.get("password") or ""
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        user = db.auth_users.find_one({"email": email})
        if not user or not check_password_hash(user.get("password_hash", ""), password):
            return jsonify({"error": "Invalid email or password"}), 401

        if AUTH_REQUIRE_EMAIL_VERIFICATION and not user.get("is_verified"):
            token = build_email_verification_token(email)
            sent, error = send_verification_email(email, token)
            db.auth_users.update_one(
                {"_id": user["_id"]},
                {"$set": {"verification_sent_at": now_isoutc(), "email_delivery_error": error, "updated_at": now_isoutc()}},
            )
            payload = build_verification_delivery_payload(
                {
                    "error": "Email is not verified",
                    "message": "Verification email sent. Please verify and login again." if sent else "Email is not verified. Use verification link below for local setup.",
                },
                token,
                sent,
                error,
            )
            return jsonify(payload), 403

        session.permanent = True
        session["user_id"] = str(user["_id"])
        session["user_email"] = user.get("email")
        db.auth_users.update_one({"_id": user["_id"]}, {"$set": {"last_login_at": now_isoutc()}})
        user["last_login_at"] = now_isoutc()
        return jsonify({"success": True, "user": auth_user_payload(user)})


    @app.route("/auth/logout", methods=["POST"])
    def auth_logout():
        session.clear()
        return jsonify({"success": True})


    @app.route("/auth/me", methods=["GET"])
    def auth_me():
        user = get_current_user()
        if not user:
            return jsonify({"authenticated": False}), 200
        return jsonify({"authenticated": True, "user": auth_user_payload(user)})


    @app.route("/auth/subscription", methods=["GET"])
    @require_logged_in_api
    def auth_get_subscription():
        user = get_current_user()
        plan = normalize_subscription_plan(user.get("subscription_plan"))
        return jsonify({
            "success": True,
            "subscription": {
                "plan": plan,
                "status": user.get("subscription_status", "active"),
                "features": subscription_features(plan),
            }
        })


    @app.route("/auth/subscription", methods=["POST"])
    @require_logged_in_api
    def auth_set_subscription():
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        user = get_current_user()
        data = request.json or {}
        plan = normalize_subscription_plan(data.get("plan"))
        db.auth_users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "subscription_plan": plan,
                    "subscription_status": "active",
                    "subscription_updated_at": now_isoutc(),
                }
            }
        )
        return jsonify({
            "success": True,
            "subscription": {
                "plan": plan,
                "status": "active",
                "features": subscription_features(plan),
            }
        })


    @app.route("/api/subscription/capacity", methods=["GET"])
    @require_logged_in_api
    def estimate_subscription_capacity():
        rps = request.args.get("rps", type=float, default=0.0)
        interval_seconds = request.args.get("interval_seconds", type=float, default=0.0)
        if rps <= 0 or interval_seconds <= 0:
            return jsonify({"error": "rps and interval_seconds must be greater than 0"}), 400
        max_apis = int(rps * interval_seconds)
        return jsonify({
            "rps": rps,
            "interval_seconds": interval_seconds,
            "max_apis_estimate": max_apis,
            "formula": "max_apis = rps * interval_seconds",
        })
