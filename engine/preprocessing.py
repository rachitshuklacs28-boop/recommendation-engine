"""
engine/preprocessing.py
------------------------
Turns raw profile fields and catalog rows into clean text that the
TF-IDF vectorizer can work with, plus small helper functions for
splitting/normalizing the semicolon-separated skill lists used
throughout the datasets.
"""

import re
from engine.weights import (
    SKILLS_REPEAT,
    CAREER_GOAL_REPEAT,
    INTERESTS_REPEAT,
    EXPERIENCE_REPEAT,
)


def clean_text(text):
    """Lowercase, strip punctuation, collapse whitespace."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\+\#\.]", " ", text)  # keep + and # for C++, C#
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_list_field(value, sep=";"):
    """Split a semicolon-separated field into a clean, deduplicated set of items."""
    if not isinstance(value, str) or not value.strip():
        return set()
    items = [clean_text(v) for v in value.split(sep)]
    return {item for item in items if item}


def build_item_text(row, text_fields, skill_field):
    """
    Combine a catalog row's descriptive fields into one text blob used
    for TF-IDF. `skill_field` (e.g. required_skills) is included twice
    since it's the strongest signal of what the item is about.
    """
    parts = []
    for field in text_fields:
        parts.append(clean_text(str(row.get(field, ""))))
    skill_text = clean_text(str(row.get(skill_field, "")).replace(";", " "))
    parts.append(skill_text)
    parts.append(skill_text)  # counted twice -> stronger weight in TF-IDF
    return " ".join(p for p in parts if p)


def build_user_query_document(skills, interests, career_goal, experience_level):
    """
    Build the user's weighted "query document" for TF-IDF by repeating
    each field's words according to its importance weight (see
    engine/weights.py). Repeating words is a simple, explainable way to
    make TF-IDF term-frequency favor the fields we care about most.
    """
    skills_text = clean_text(" ".join(skills)) if isinstance(skills, (set, list)) else clean_text(skills.replace(";", " "))
    interests_text = clean_text(" ".join(interests)) if isinstance(interests, (set, list)) else clean_text(interests.replace(";", " "))
    goal_text = clean_text(career_goal)
    exp_text = clean_text(experience_level)

    doc_parts = (
        [skills_text] * SKILLS_REPEAT
        + [goal_text] * CAREER_GOAL_REPEAT
        + [interests_text] * INTERESTS_REPEAT
        + [exp_text] * EXPERIENCE_REPEAT
    )
    return " ".join(p for p in doc_parts if p)


STOPWORDS = {
    "a", "an", "the", "and", "or", "to", "of", "in", "on", "for",
    "with", "as", "is", "be", "become", "becoming", "i", "my", "want",
    "career", "goal", "role", "job", "work", "working", "at", "into",
}


def _meaningful_words(text):
    """Words from `text`, lowercased/cleaned, with stopwords and 1-char tokens removed."""
    return {w for w in clean_text(text).split() if w and len(w) > 1 and w not in STOPWORDS}


def keyword_overlap_ratio(query_text, target_text):
    """
    Fraction of distinct, meaningful words from `query_text` that appear
    in `target_text`. Used for scoring how well a career goal matches an
    item's title/domain/description.
    """
    query_words = _meaningful_words(query_text)
    if not query_words:
        return 0.0
    target_words = set(clean_text(target_text).split())
    matched = query_words & target_words
    return len(matched) / len(query_words)


def matched_keywords(query_text, target_text):
    """Return the actual set of meaningful matched words (for explanations)."""
    query_words = _meaningful_words(query_text)
    target_words = set(clean_text(target_text).split())
    return query_words & target_words
