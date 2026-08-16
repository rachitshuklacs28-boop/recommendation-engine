"""
app.py
-------
Entry point for the Flask application. Serves the two frontend pages
(profile form + dashboard) and registers the API blueprints.

Run with:
    python app.py
Then open http://127.0.0.1:5000/ in your browser.
"""

import os
from flask import Flask, render_template, redirect, url_for

from routes.profile_routes import profile_bp
from routes.recommend_routes import recommend_bp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "database.db")


def create_app():
    app = Flask(__name__)
    app.config["DB_PATH"] = DB_PATH

    app.register_blueprint(profile_bp)
    app.register_blueprint(recommend_bp)

    @app.route("/")
    def index():
        """Profile creation page."""
        return render_template("index.html")

    @app.route("/dashboard/<int:user_id>")
    def dashboard(user_id):
        """Recommendations dashboard for a given user id."""
        return render_template("dashboard.html", user_id=user_id)

    @app.errorhandler(404)
    def not_found(e):
        return redirect(url_for("index"))

    return app


app = create_app()

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("Database not found — run 'python database/db_setup.py' first.")
    app.run(debug=True, host="127.0.0.1", port=5000)
