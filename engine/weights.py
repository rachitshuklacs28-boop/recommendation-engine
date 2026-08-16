"""
engine/weights.py
------------------
Central place to tune how much each signal contributes to the final
match score. Changing a number here changes recommendations everywhere,
which makes the scoring transparent and easy to experiment with.

Final score = (TFIDF_WEIGHT   * tfidf_cosine_similarity)
            + (SKILL_WEIGHT   * skill_overlap_ratio)
            + (GOAL_WEIGHT    * career_goal_keyword_overlap)
            + (EXPERIENCE_WEIGHT * experience_level_match)

All four weights must sum to 1.0 so the final score lands in [0, 1]
before being converted to a percentage.
"""

TFIDF_WEIGHT = 0.35        # content-based similarity (skills+interests+goal text vs item text)
SKILL_WEIGHT = 0.35        # explicit overlap between user skills and item's required skills
GOAL_WEIGHT = 0.15         # how well the item matches the user's stated career goal
EXPERIENCE_WEIGHT = 0.15   # how well the item's difficulty/level matches the user's experience

assert abs((TFIDF_WEIGHT + SKILL_WEIGHT + GOAL_WEIGHT + EXPERIENCE_WEIGHT) - 1.0) < 1e-9, \
    "Weights must sum to 1.0"

# How many times a field's words are repeated when building the user's
# weighted query document for TF-IDF. Repetition is a simple, well-known
# way to bias TF-IDF term frequency towards fields that matter more.
SKILLS_REPEAT = 4
CAREER_GOAL_REPEAT = 3
INTERESTS_REPEAT = 2
EXPERIENCE_REPEAT = 1

# Ordering used to compute "distance" between experience levels.
EXPERIENCE_ORDER = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}

# Score given based on how many levels apart the user and item are.
EXPERIENCE_MATCH_SCORE = {
    0: 1.0,   # exact match
    1: 0.5,   # one level apart
    2: 0.15,  # two levels apart (Beginner <-> Advanced)
}

TOP_N_DEFAULT = 6  # how many recommendations to return per category by default
