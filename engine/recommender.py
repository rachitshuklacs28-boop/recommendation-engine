"""
engine/recommender.py
-----------------------
The heart of the project: a content-based recommendation engine that
combines

    1. TF-IDF + cosine similarity  (semantic/content similarity)
    2. Weighted explicit matching  (skill overlap, goal keyword overlap,
                                     experience-level alignment)

into one transparent, explainable match score per item, for three
catalogs: internships, projects, and learning resources.

Nothing here is hard-coded to a specific user or item — every score is
computed fresh from whatever profile is passed in, against whatever is
currently in the database.
"""

import sqlite3
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from engine.preprocessing import (
    build_item_text,
    build_user_query_document,
    split_list_field,
    keyword_overlap_ratio,
    matched_keywords,
    clean_text,
)
from engine.weights import (
    TFIDF_WEIGHT,
    SKILL_WEIGHT,
    GOAL_WEIGHT,
    EXPERIENCE_WEIGHT,
    EXPERIENCE_ORDER,
    EXPERIENCE_MATCH_SCORE,
    TOP_N_DEFAULT,
)

# Per-catalog configuration: which columns feed the TF-IDF text, which
# column holds the required/covered skills, and which column holds the
# difficulty/level used for the experience-match score.
CATEGORY_CONFIG = {
    "internship": {
        "table": "internships",
        "text_fields": ["title", "description", "domain"],
        "skill_field": "required_skills",
        "level_field": "level",
    },
    "project": {
        "table": "projects",
        "text_fields": ["title", "description", "domain", "category"],
        "skill_field": "skills_required",
        "level_field": "difficulty_level",
    },
    "learning_resource": {
        "table": "learning_resources",
        "text_fields": ["title", "description", "category", "resource_type"],
        "skill_field": "skills_covered",
        "level_field": "level",
    },
}


class RecommendationEngine:
    """
    Usage:
        engine = RecommendationEngine(db_path)
        result = engine.recommend_all(profile, top_n=6)
        # result = {
        #   "internship": [ {...item, match_score, explanation}, ... ],
        #   "project": [ ... ],
        #   "learning_resource": [ ... ],
        # }
    """

    def __init__(self, db_path):
        self.db_path = db_path

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------
    def _load_catalog(self, table_name):
        conn = sqlite3.connect(self.db_path)
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        finally:
            conn.close()
        return df

    def _log_recommendations(self, user_id, item_type, scored_items):
        if user_id is None:
            return
        conn = sqlite3.connect(self.db_path)
        try:
            rows = [
                (user_id, item_type, int(item["id"]), float(item["match_score"]))
                for item in scored_items
            ]
            conn.executemany(
                """INSERT INTO recommendation_history (user_id, item_type, item_id, match_score)
                   VALUES (?, ?, ?, ?)""",
                rows,
            )
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------
    @staticmethod
    def _experience_match_score(user_level, item_level):
        u = EXPERIENCE_ORDER.get(str(user_level).strip().title())
        i = EXPERIENCE_ORDER.get(str(item_level).strip().title())
        if u is None or i is None:
            return 0.5  # unknown level -> neutral score
        distance = abs(u - i)
        return EXPERIENCE_MATCH_SCORE.get(distance, 0.0)

    def _score_category(self, category, profile, top_n):
        config = CATEGORY_CONFIG[category]
        df = self._load_catalog(config["table"])
        if df.empty:
            return []

        # ---- 1. Content-based TF-IDF + cosine similarity ----
        item_texts = df.apply(
            lambda row: build_item_text(row, config["text_fields"], config["skill_field"]),
            axis=1,
        ).tolist()

        user_query_doc = build_user_query_document(
            profile["skills"], profile["interests"], profile["career_goal"], profile["experience_level"]
        )

        corpus = item_texts + [user_query_doc]
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(corpus)

        user_vector = tfidf_matrix[-1]
        item_vectors = tfidf_matrix[:-1]
        tfidf_scores = cosine_similarity(user_vector, item_vectors).flatten()

        # ---- 2. Weighted explicit matching ----
        user_skills = split_list_field(
            profile["skills"] if isinstance(profile["skills"], str) else ";".join(profile["skills"])
        )
        goal_text = profile["career_goal"]

        results = []
        for idx, row in df.iterrows():
            item_skills = split_list_field(row[config["skill_field"]])
            matched_skills = user_skills & item_skills

            skill_score = (len(matched_skills) / len(item_skills)) if item_skills else 0.0

            goal_target_text = " ".join(
                clean_text(str(row.get(f, ""))) for f in ["title", "domain", "description"] if f in row
            )
            goal_score = keyword_overlap_ratio(goal_text, goal_target_text)
            matched_goal_keywords = matched_keywords(goal_text, goal_target_text)

            exp_score = self._experience_match_score(profile["experience_level"], row[config["level_field"]])

            tfidf_score = float(tfidf_scores[idx])

            final_score = (
                TFIDF_WEIGHT * tfidf_score
                + SKILL_WEIGHT * skill_score
                + GOAL_WEIGHT * goal_score
                + EXPERIENCE_WEIGHT * exp_score
            )
            match_percentage = round(min(final_score, 1.0) * 100, 1)

            explanation = self._build_explanation(
                matched_skills=matched_skills,
                item_skill_count=len(item_skills),
                matched_goal_keywords=matched_goal_keywords,
                exp_score=exp_score,
                user_level=profile["experience_level"],
                item_level=row[config["level_field"]],
                tfidf_score=tfidf_score,
            )

            item_dict = row.to_dict()
            item_dict["match_score"] = match_percentage
            item_dict["score_breakdown"] = {
                "content_similarity": round(tfidf_score * 100, 1),
                "skill_match": round(skill_score * 100, 1),
                "goal_alignment": round(goal_score * 100, 1),
                "experience_fit": round(exp_score * 100, 1),
            }
            item_dict["matched_skills"] = sorted(matched_skills)
            item_dict["explanation"] = explanation
            results.append(item_dict)

        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results[:top_n]

    @staticmethod
    def _build_explanation(matched_skills, item_skill_count, matched_goal_keywords, exp_score, user_level, item_level, tfidf_score):
        parts = []

        if matched_skills:
            skill_list = ", ".join(sorted(matched_skills)[:5])
            parts.append(f"Matches {len(matched_skills)}/{item_skill_count} required skills you have ({skill_list}).")
        else:
            parts.append("Doesn't overlap with your listed skills yet, but is closely related to your interests/goal.")

        if matched_goal_keywords:
            parts.append(f"Aligned with your career goal via: {', '.join(sorted(matched_goal_keywords)[:4])}.")

        if exp_score >= 1.0:
            parts.append(f"Matches your experience level ({user_level}).")
        elif exp_score >= 0.5:
            parts.append(f"Slightly above/below your experience level ({user_level} vs {item_level}) — a good stretch goal.")
        else:
            parts.append(f"Experience gap: this is a {item_level} item, while you're at {user_level}.")

        if tfidf_score > 0.3:
            parts.append("Strong overall content similarity to your profile.")

        return " ".join(parts)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def recommend_internships(self, profile, top_n=TOP_N_DEFAULT, user_id=None):
        results = self._score_category("internship", profile, top_n)
        self._log_recommendations(user_id, "internship", results)
        return results

    def recommend_projects(self, profile, top_n=TOP_N_DEFAULT, user_id=None):
        results = self._score_category("project", profile, top_n)
        self._log_recommendations(user_id, "project", results)
        return results

    def recommend_learning_resources(self, profile, top_n=TOP_N_DEFAULT, user_id=None):
        results = self._score_category("learning_resource", profile, top_n)
        self._log_recommendations(user_id, "learning_resource", results)
        return results

    def recommend_all(self, profile, top_n=TOP_N_DEFAULT, user_id=None):
        return {
            "internship": self.recommend_internships(profile, top_n, user_id),
            "project": self.recommend_projects(profile, top_n, user_id),
            "learning_resource": self.recommend_learning_resources(profile, top_n, user_id),
        }
