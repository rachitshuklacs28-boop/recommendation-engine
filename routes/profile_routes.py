"""
routes/profile_routes.py
--------------------------
REST endpoints for creating and reading user profiles.

    POST /api/profile        -> create a new profile, returns {id}
    GET  /api/profile/<id>   -> fetch a profile
    GET  /api/profiles       -> list all profiles (for a 'switch user' dropdown)
"""

from flask import Blueprint, request, jsonify, current_app
from models.db_models import create_user, get_user, list_users

profile_bp = Blueprint("profile_bp", __name__)

REQUIRED_FIELDS = ["name", "education", "skills", "interests", "experience_level", "career_goal"]
VALID_LEVELS = {"Beginner", "Intermediate", "Advanced"}


@profile_bp.route("/api/profile", methods=["POST"])
def create_profile():
    data = request.get_json(silent=True) or {}

    missing = [f for f in REQUIRED_FIELDS if not str(data.get(f, "")).strip()]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    if data["experience_level"] not in VALID_LEVELS:
        return jsonify({"error": f"experience_level must be one of {sorted(VALID_LEVELS)}"}), 400

    # Normalize skills/interests: accept either a list or a comma-separated
    # string from the frontend, and store as a semicolon-separated string.
    def normalize_list(value):
        if isinstance(value, list):
            items = value
        else:
            items = str(value).split(",")
        return ";".join(item.strip() for item in items if item.strip())

    skills = normalize_list(data["skills"])
    interests = normalize_list(data["interests"])

    if not skills:
        return jsonify({"error": "At least one skill is required."}), 400

    user_id = create_user(
        current_app.config["DB_PATH"],
        name=data["name"].strip(),
        education=data["education"].strip(),
        skills=skills,
        interests=interests,
        experience_level=data["experience_level"],
        career_goal=data["career_goal"].strip(),
    )

    return jsonify({"id": user_id, "message": "Profile created successfully."}), 201


@profile_bp.route("/api/profile/<int:user_id>", methods=["GET"])
def fetch_profile(user_id):
    user = get_user(current_app.config["DB_PATH"], user_id)
    if not user:
        return jsonify({"error": "Profile not found."}), 404
    return jsonify(user)


@profile_bp.route("/api/profiles", methods=["GET"])
def fetch_all_profiles():
    return jsonify(list_users(current_app.config["DB_PATH"]))
