from flask import Blueprint, request, redirect, jsonify, session, current_app as app
from app import oauth, google
from datetime import datetime
import os

FRONTEND_URL = os.getenv("FRONTEND_URL")
REDIRECT_URI = os.getenv("REDIRECT_URI") 

bp = Blueprint("auth", __name__, url_prefix="/api")

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

def update_last_active(email: str):
    now = datetime.utcnow().isoformat()
    app.config["SESSION_REDIS"].hset(f"user:{email}", "last_active", now)

def get_user_limit(email: str) -> int:
    key = f"user:{email}"
    val = app.config["SESSION_REDIS"].hget(key, "limit")
    return int(val.decode()) if val else 5

@bp.route("/google-login")
def google_login():
    return google.authorize_redirect(REDIRECT_URI)

@bp.route("/google-callback")
def google_callback():
    token = google.authorize_access_token()
    user_info = google.get("https://openidconnect.googleapis.com/v1/userinfo").json()
    email = user_info["email"]
    redis_key = f"user:{email}"

    if app.config["SESSION_REDIS"].hget(redis_key, "banned") == b"true":
        return redirect(f"{FRONTEND_URL}/?banned=true")

    session["user"] = email
    print(f"User {email} logged in, session set: {session.get('user')}")
    session_id = request.cookies.get(app.config["SESSION_COOKIE_NAME"])

    app.config["SESSION_REDIS"].hset(redis_key, mapping={
        "name": user_info.get("name", ""),
        "google": "true",
        "picture": user_info.get("picture", ""),
        "login_time": datetime.utcnow().isoformat(),
        "ip": request.remote_addr,
        "agent": request.headers.get("User-Agent", ""),
        "session_id": session_id or ""
    })

    # ✅ Instead of passing login success via query string,
    # use frontend polling after redirect to /auth-success
    return redirect(f"{FRONTEND_URL}/auth-success")

@bp.route("/user")
def get_user():
    print("Session contents:", dict(session)) 
    email = session.get("user")
    if not email:
        return jsonify({"error": "Not logged in"}), 401

    update_last_active(email)
    data = app.config["SESSION_REDIS"].hgetall(f"user:{email}")
    return jsonify({
        "user": {
            "name": data.get(b"name", b"").decode(),
            "email": email,
            "picture": data.get(b"picture", b"").decode()
        },
        "isAdmin": email == ADMIN_EMAIL,
        "limit": get_user_limit(email)
    })

@bp.route("/logout", methods=["POST"])
def logout():
    if "user" in session:
        update_last_active(session["user"])
    session.pop("user", None)
    return jsonify({"message": "Logged out"})

@bp.route("/debug-session")
def debug_session():
    return jsonify({
        "session": dict(session),
        "cookies": dict(request.cookies),
        "user": session.get("user")
    })
