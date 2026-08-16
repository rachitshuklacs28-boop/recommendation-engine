"""
routes/recommend_routes.py
-----------------------------
    GET /api/recommendations/<user_id>?top_n=6

Loads the user's profile from SQLite, runs it through the
RecommendationEngine (fresh, every request), and returns ranked
internships, projects, and learning resources with match percentages
and explanations.
"""

from flask import Blueprint, jsonify, request, current_app
from models.db_models import get_user
from engine.recommender import RecommendationEngine

recommend_bp = Blueprint("recommend_bp", __name__)


@recommend_bp.route("/api/recommendations/<int:user_id>", methods=["GET"])
def get_recommendations(user_id):
    db_path = current_app.config["DB_PATH"]

    user = get_user(db_path, user_id)
    if not user:
        return jsonify({"error": "Profile not found."}), 404

    top_n = request.args.get("top_n", default=6, type=int)
    top_n = max(1, min(top_n, 20))  # sane bounds

    profile = {
        "skills": user["skills"],
        "interests": user["interests"],
        "career_goal": user["career_goal"],
        "experience_level": user["experience_level"],
    }

    engine = RecommendationEngine(db_path)
    results = engine.recommend_all(profile, top_n=top_n, user_id=user_id)

    return jsonify({
        "user": user,
        "recommendations": results,
    })
