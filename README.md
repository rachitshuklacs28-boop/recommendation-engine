# MATCH.ENGINE — Recommendation Engine for Internships, Projects & Learning Resources

A full-stack academic project that recommends **internships**, **projects**, and
**learning resources** to a student based on a profile they fill in — skills,
interests, career goal, and experience level.

Every recommendation is computed **live**, on every request, using a real
content-based recommendation engine (TF-IDF + cosine similarity + weighted
skill/goal/experience matching). Nothing is hard-coded.

---

## 1. What it does

1. You create a profile: name, education, skills, interests, experience level, career goal.
2. The engine loads three datasets (internships, projects, learning resources) from SQLite.
3. For your profile, it computes a **match score (0–100%)** for every item using:
   - **TF-IDF + cosine similarity** — how similar your profile text is to each item's description.
   - **Weighted explicit matching** — skill overlap, career-goal keyword overlap, and experience-level alignment.
4. The dashboard shows the top matches per category, each with:
   - A match percentage and color-coded confidence bar.
   - A breakdown of the four scoring components.
   - A plain-English explanation of *why* it was recommended.

---

## 2. Tech stack

| Layer            | Technology                                  |
|-------------------|----------------------------------------------|
| Backend            | Python, Flask                                |
| Recommendation engine | Pandas, NumPy, Scikit-learn (TF-IDF, cosine similarity) |
| Database            | SQLite                                       |
| Frontend             | HTML, CSS, vanilla JavaScript                |

---

## 3. Folder structure

```
recommendation-engine/
├── app.py                      # Flask app entrypoint
├── requirements.txt
├── README.md
├── database/
│   ├── schema.sql               # table definitions
│   └── db_setup.py              # creates DB + loads CSVs (run this first)
├── data/
│   ├── internships.csv
│   ├── projects.csv
│   └── learning_resources.csv
├── engine/
│   ├── preprocessing.py         # text cleaning, weighted profile document builder
│   ├── weights.py                # scoring weight constants (tune here)
│   └── recommender.py            # TF-IDF, cosine similarity, weighted engine
├── models/
│   └── db_models.py               # SQLite CRUD helpers for user profiles
├── routes/
│   ├── profile_routes.py          # POST/GET profile endpoints
│   └── recommend_routes.py        # GET recommendations endpoint
├── static/
│   ├── css/style.css
│   └── js/dashboard.js
├── templates/
│   ├── index.html                 # profile creation form
│   └── dashboard.html             # results dashboard
└── tests/
    └── test_recommender.py        # standalone sanity checks for the engine
```

---

## 4. How to run it locally

### Step 1 — Install Python dependencies
It's recommended to use a virtual environment:
```bash
python -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Step 2 — Create and seed the database
This creates `database/database.db`, builds the tables, and loads the three
CSV datasets into it.
```bash
python database/db_setup.py
```
You should see output confirming each table was seeded. You can re-run this
any time to reset the catalog data — it won't delete profiles you've created.

### Step 3 — Start the Flask app
```bash
python app.py
```
Then open **http://127.0.0.1:5000/** in your browser.

### Step 4 (optional) — Run the engine sanity test
This runs the recommendation engine standalone (no Flask needed) against a
few sample profiles and prints the results, to prove it responds differently
to different inputs:
```bash
python tests/test_recommender.py
```

---

## 5. How the recommendation engine works (explained simply)

For every request, for each of the three catalogs (internships/projects/resources):

1. **Build text for every item** — combine its title, description, domain, and
   required skills into one text blob.
2. **Build a "query document" for your profile** — combine your skills,
   interests, career goal, and experience level into one text blob, where
   more important fields (skills, career goal) are *repeated* more times so
   TF-IDF weighs them more heavily.
3. **TF-IDF vectorize** everything (items + your profile) into numeric vectors
   based on word importance.
4. **Cosine similarity** between your profile vector and each item vector
   gives a 0–1 "content similarity" score.
5. **Separately**, three explicit scores are computed for transparency:
   - `skill_score` = fraction of an item's required skills that you have.
   - `goal_score` = fraction of your career-goal keywords that appear in the item's text.
   - `experience_score` = how closely the item's difficulty level matches your experience level.
6. **Final score** = weighted sum of all four signals (weights live in `engine/weights.py`,
   and are documented there):
   ```
   final = 0.35 * content_similarity
         + 0.35 * skill_match
         + 0.15 * goal_alignment
         + 0.15 * experience_fit
   ```
7. Items are sorted by final score and the top N are returned, along with a
   generated explanation and a score breakdown, so every recommendation is
   explainable rather than a black box.

You can change the weights in `engine/weights.py` and the recommendations
will change immediately on the next request — there's nothing to retrain or
precompute.

---

## 6. API reference

| Method | Endpoint                              | Description                                  |
|--------|-----------------------------------------|-----------------------------------------------|
| POST   | `/api/profile`                          | Create a new user profile                     |
| GET    | `/api/profile/<id>`                     | Fetch a profile by id                         |
| GET    | `/api/profiles`                         | List all profiles                             |
| GET    | `/api/recommendations/<id>?top_n=6`     | Get live recommendations for a profile        |

Example request body for `POST /api/profile`:
```json
{
  "name": "Ananya Sharma",
  "education": "B.Tech CSE, 3rd Year",
  "skills": "Python, Pandas, Machine Learning, SQL",
  "interests": "Data Science, Artificial Intelligence",
  "experience_level": "Intermediate",
  "career_goal": "become a machine learning engineer"
}
```

---

## 7. Extending the project

- **Add more data**: just add rows to the CSV files in `/data` and re-run
  `python database/db_setup.py`.
- **Add a new catalog** (e.g. "hackathons"): add a table to `schema.sql`, a
  CSV in `/data`, an entry in `CATEGORY_CONFIG` in `engine/recommender.py`,
  and a new tab in `dashboard.html`.
- **Tune scoring**: edit the weights and repetition constants in
  `engine/weights.py` — everything else adapts automatically.
- **Swap SQLite for Postgres/MySQL**: the only file that talks to the
  database is `models/db_models.py` and the `sqlite3.connect(...)` calls in
  `engine/recommender.py` — everything else is database-agnostic.

---

## 8. Notes for beginners

- `engine/` is where all the "smart" logic lives — start there if you want
  to understand the recommendation algorithm.
- `routes/` files are intentionally thin — they just validate input, call
  into `engine/` or `models/`, and return JSON.
- The `recommendation_history` table isn't required for the app to work; it's
  there as a transparent log proving every recommendation was computed for
  that specific request rather than hard-coded.
- Nothing in this project needs an API key, external service, or internet
  connection to run — everything is local (SQLite + your own CSVs).
