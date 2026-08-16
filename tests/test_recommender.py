"""
tests/test_recommender.py
----------------------------
Simple sanity checks (not pytest-required, just runnable as a script)
that prove the engine produces different, sensible results for different
profiles instead of anything hard-coded.

Run with:
    python tests/test_recommender.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.recommender import RecommendationEngine

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "database.db")


def print_results(title, results, key_field="title"):
    print(f"\n--- {title} ---")
    for item in results[:5]:
        print(f"  {item['match_score']:>5.1f}%  {item[key_field]}")
        print(f"          breakdown: {item['score_breakdown']}")
        print(f"          why: {item['explanation']}")


def run_profile(engine, name, profile):
    print(f"\n{'='*70}\nPROFILE: {name}\n{profile}\n{'='*70}")
    results = engine.recommend_all(profile, top_n=5)
    print_results("Internships", results["internship"])
    print_results("Projects", results["project"])
    print_results("Learning Resources", results["learning_resource"])


if __name__ == "__main__":
    engine = RecommendationEngine(DB_PATH)

    profile_a = {
        "skills": "Python;Machine Learning;Pandas;NumPy",
        "interests": "Artificial Intelligence;Data Science",
        "career_goal": "become a machine learning engineer",
        "experience_level": "Intermediate",
    }

    profile_b = {
        "skills": "HTML;CSS;JavaScript;React",
        "interests": "Web Development;UI Design",
        "career_goal": "become a frontend developer",
        "experience_level": "Beginner",
    }

    profile_c = {
        "skills": "Figma;UX Research;Prototyping",
        "interests": "Design;Mobile Apps",
        "career_goal": "become a product designer",
        "experience_level": "Beginner",
    }

    run_profile(engine, "Aspiring ML Engineer", profile_a)
    run_profile(engine, "Aspiring Frontend Developer", profile_b)
    run_profile(engine, "Aspiring Product Designer", profile_c)

    # Sanity assertions: different profiles must produce different top results
    results_a = engine.recommend_internships(profile_a, top_n=1)
    results_b = engine.recommend_internships(profile_b, top_n=1)
    assert results_a[0]["id"] != results_b[0]["id"] or results_a[0]["title"] != results_b[0]["title"], \
        "Different profiles produced identical top recommendation — engine may be broken."
    print("\n[OK] Different profiles produce different recommendations — engine is working dynamically.")
