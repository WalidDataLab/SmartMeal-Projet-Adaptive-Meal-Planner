# -*- coding: utf-8 -*-
"""
SmartMeal database initialisation (safe and repeatable).

    python backend/init_db.py           # create missing tables + seed empty tables
    python backend/init_db.py --reset   # delete the 3 databases and rebuild them

Differences with the original init_db.py:
  * the original ran DROP TABLE on every execution (data loss). Here tables are
    created with CREATE TABLE IF NOT EXISTS and sample data is inserted only
    into empty tables, so the app can call init_databases() at every start-up;
  * the meals dataset is UPSERTed from backend/meals/*.json each time, so the
    JSON files stay the single source of truth for the content;
  * foreign keys, UNIQUE and CHECK constraints are declared in the schema;
  * databases carry a schema version (PRAGMA user_version). A version-1 database
    (first SmartMeal release) is migrated in place to version 2: users and their
    history are kept, meals are rebuilt from JSON, default rules are replaced.
"""

import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import db  # noqa: E402

SCHEMA_VERSION = 3        # v2: nutrition/health/body data, v3: avatar

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id                INTEGER PRIMARY KEY,
    name              TEXT NOT NULL UNIQUE,
    dietary_goal      TEXT NOT NULL DEFAULT 'healthy_eating'
                      CHECK (dietary_goal IN ('weight_loss','weight_gain','muscle_gain','healthy_eating')),
    budget_preference TEXT NOT NULL DEFAULT 'medium'
                      CHECK (budget_preference IN ('low','medium','high')),
    cooking_level     TEXT NOT NULL DEFAULT 'beginner'
                      CHECK (cooking_level IN ('beginner','intermediate','advanced')),
    -- optional body data (NULL = not given)
    age               INTEGER CHECK (age IS NULL OR age BETWEEN 14 AND 100),
    sex               TEXT CHECK (sex IS NULL OR sex IN ('female','male')),
    height_cm         REAL CHECK (height_cm IS NULL OR height_cm BETWEEN 120 AND 230),
    weight_kg         REAL CHECK (weight_kg IS NULL OR weight_kg BETWEEN 30 AND 300),
    body_fat_pct      REAL CHECK (body_fat_pct IS NULL OR body_fat_pct BETWEEN 3 AND 70),
    activity_level    TEXT NOT NULL DEFAULT 'moderate'
                      CHECK (activity_level IN ('low','moderate','high')),
    avatar            TEXT,                         -- e.g. 'avatar_07' (NULL = initial letter)
    created_at        TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
"""
PREFERENCES_TABLE = """
-- Original table kept and typed: food preferences, preferred meal types, diet
-- restrictions, health conditions and allergies (several values per type allowed)
CREATE TABLE IF NOT EXISTS preferences (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    pref_type  TEXT NOT NULL
               CHECK (pref_type IN ('food','meal_type','restriction','health','allergy')),
    preference TEXT NOT NULL,
    UNIQUE (user_id, pref_type, preference)
);
"""

USERS_SCHEMA = USERS_TABLE + PREFERENCES_TABLE + """

-- Original "performance" table, now holding the DYNAMIC user model.
-- Every value is recomputed by db.refresh_performance() from the raw data.
CREATE TABLE IF NOT EXISTS performance (
    user_id               INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    meals_viewed          INTEGER NOT NULL DEFAULT 0,
    meals_selected        INTEGER NOT NULL DEFAULT 0,
    meals_saved           INTEGER NOT NULL DEFAULT 0,
    recommendation_clicks INTEGER NOT NULL DEFAULT 0,
    recommendation_ctr    REAL    NOT NULL DEFAULT 0,
    top_category          TEXT,
    vegetarian_ratio      REAL    NOT NULL DEFAULT 0,
    high_protein_ratio    REAL    NOT NULL DEFAULT 0,
    quick_meal_ratio      REAL    NOT NULL DEFAULT 0,
    sessions_count        INTEGER NOT NULL DEFAULT 0,
    avg_session_minutes   REAL    NOT NULL DEFAULT 0,
    interaction_frequency INTEGER NOT NULL DEFAULT 0,   -- sessions in the last 7 days
    last_active           TEXT,
    updated_at            TEXT
);

-- Step 3: one row per session, updated in place while the session runs
CREATE TABLE IF NOT EXISTS context (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id            INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id         TEXT NOT NULL UNIQUE,
    device_type        TEXT NOT NULL CHECK (device_type IN ('desktop','tablet','mobile')),
    available_time     INTEGER NOT NULL CHECK (available_time BETWEEN 1 AND 240),
    meal_budget        TEXT NOT NULL CHECK (meal_budget IN ('low','medium','high')),
    connection_quality TEXT NOT NULL CHECK (connection_quality IN ('slow','normal','fast')),
    meal_moment        TEXT NOT NULL DEFAULT 'any'
                       CHECK (meal_moment IN ('any','breakfast','lunch','dinner','snack')),
    updates_count      INTEGER NOT NULL DEFAULT 0,
    started_at         TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    last_seen_at       TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    ended_at           TEXT,
    is_active          INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1))
);
CREATE INDEX IF NOT EXISTS idx_context_user_active ON context(user_id, is_active);

-- Step 6: interaction history. meal_id refers to meals.db/meals(id); SQLite cannot
-- enforce a FOREIGN KEY across database files, so it is checked in the Flask layer
-- and name/category are stored as a snapshot.
CREATE TABLE IF NOT EXISTS meal_history (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    context_id       INTEGER REFERENCES context(id) ON DELETE SET NULL,
    meal_id          INTEGER NOT NULL,
    meal_name        TEXT NOT NULL,
    meal_category    TEXT NOT NULL,
    interaction_type TEXT NOT NULL
                     CHECK (interaction_type IN ('recommended','viewed','selected','saved','unsaved')),
    source           TEXT NOT NULL DEFAULT 'direct'
                     CHECK (source IN ('recommendation','direct','dashboard')),
    rank_position    INTEGER,
    context_snapshot TEXT,             -- JSON copy of the context at interaction time
    created_at       TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_history_user_type ON meal_history(user_id, interaction_type);
CREATE INDEX IF NOT EXISTS idx_history_context ON meal_history(context_id);

CREATE TABLE IF NOT EXISTS saved_meals (
    user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meal_id  INTEGER NOT NULL,
    saved_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    PRIMARY KEY (user_id, meal_id)
);
"""

RULES_SCHEMA = """
CREATE TABLE IF NOT EXISTS rules (
    rule_id     INTEGER PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    kind        TEXT NOT NULL CHECK (kind IN ('constraint','recommendation','interface')),
    condition   TEXT NOT NULL,
    adaptation  TEXT NOT NULL,
    priority    INTEGER NOT NULL DEFAULT 50,
    explanation TEXT NOT NULL,
    active      INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1))
);
"""

MEALS_SCHEMA = """
CREATE TABLE IF NOT EXISTS meals (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL UNIQUE,
    category      TEXT NOT NULL CHECK (category IN ('breakfast','lunch','dinner','snack')),
    ingredients   TEXT NOT NULL,      -- JSON array
    prep_time     INTEGER NOT NULL CHECK (prep_time > 0),
    cost_category TEXT NOT NULL CHECK (cost_category IN ('low','medium','high')),
    vegetarian    INTEGER NOT NULL CHECK (vegetarian IN (0,1)),
    protein_level TEXT NOT NULL CHECK (protein_level IN ('low','medium','high')),
    difficulty    TEXT NOT NULL CHECK (difficulty IN ('easy','medium','hard')),
    description   TEXT NOT NULL,
    image         TEXT,
    cost_eur      REAL NOT NULL CHECK (cost_eur >= 0),          -- estimated cost per serving
    -- estimated nutrition per serving
    calories_kcal  INTEGER NOT NULL CHECK (calories_kcal > 0),
    protein_g      REAL NOT NULL CHECK (protein_g >= 0),
    carbs_g        REAL NOT NULL CHECK (carbs_g >= 0),
    sugar_g        REAL NOT NULL CHECK (sugar_g >= 0),
    fat_g          REAL NOT NULL CHECK (fat_g >= 0),
    sat_fat_g      REAL NOT NULL CHECK (sat_fat_g >= 0),
    fiber_g        REAL NOT NULL CHECK (fiber_g >= 0),
    salt_g         REAL NOT NULL CHECK (salt_g >= 0),
    cholesterol_mg REAL NOT NULL CHECK (cholesterol_mg >= 0)
);
CREATE TABLE IF NOT EXISTS meal_tags (
    meal_id INTEGER NOT NULL REFERENCES meals(id) ON DELETE CASCADE,
    tag     TEXT NOT NULL,
    PRIMARY KEY (meal_id, tag)
);
CREATE TABLE IF NOT EXISTS meal_allergens (
    meal_id  INTEGER NOT NULL REFERENCES meals(id) ON DELETE CASCADE,
    allergen TEXT NOT NULL,
    PRIMARY KEY (meal_id, allergen)
);
"""

# ---------------------------------------------------------------------------
# Adaptation rules (Step 4). Grammar is documented in adapt_meal.py / README.
# (name, kind, condition, adaptation, priority, explanation)
# ---------------------------------------------------------------------------
RULES = [
    # --- hard constraints: diet restrictions ------------------------------------
    ("restriction_vegetarian", "constraint", "restrictions CONTAINS vegetarian",
     "filter=vegetarian", 100, "Only vegetarian meals, as set in your profile"),
    ("restriction_vegan", "constraint", "restrictions CONTAINS vegan",
     "filter=tag:vegan", 100, "Only vegan meals, as set in your profile"),
    ("restriction_gluten_free", "constraint", "restrictions CONTAINS gluten_free",
     "filter=no_allergen:gluten", 100, "Only gluten-free meals, as set in your profile"),
    ("restriction_dairy_free", "constraint", "restrictions CONTAINS dairy_free",
     "filter=no_allergen:dairy", 100, "Only dairy-free meals, as set in your profile"),

    # --- hard constraints: health conditions (generic limits per meal) ----------
    ("health_diabetes", "constraint", "health_conditions CONTAINS diabetes",
     "filter=max:sugar_g:12", 100, "At most 12 g of sugar per meal (diabetes setting)"),
    ("health_cholesterol", "constraint", "health_conditions CONTAINS high_cholesterol",
     "filter=max:sat_fat_g:6;filter=max:cholesterol_mg:200", 100,
     "At most 6 g saturated fat and 200 mg cholesterol (cholesterol setting)"),
    ("health_hypertension", "constraint", "health_conditions CONTAINS hypertension",
     "filter=max:salt_g:1.5", 100, "At most 1.5 g of salt per meal (blood pressure setting)"),
    ("health_celiac", "constraint", "health_conditions CONTAINS celiac",
     "filter=no_allergen:gluten", 100, "No gluten (coeliac disease setting)"),
    ("health_lactose", "constraint", "health_conditions CONTAINS lactose_intolerance",
     "filter=no_allergen:dairy", 100, "No dairy (lactose intolerance setting)"),

    # --- hard constraints: allergies (one rule per allergen) ----------------------
] + [
    (f"allergy_{a}", "constraint", f"allergies CONTAINS {a}", f"filter=no_allergen:{a}", 100,
     f"Contains no {a.replace('_', ' ')} (allergy setting)")
    for a in ["gluten", "dairy", "eggs", "nuts", "peanuts", "fish", "shellfish", "soy", "sesame"]
] + [
    # --- hard constraints: context -------------------------------------------------
    ("meal_moment_filter", "constraint", "meal_moment != any",
     "filter=category:@meal_moment", 95, "Only meals for the moment you chose"),
    ("fit_available_time", "constraint", "available_time >= 1",
     "max_prep_time=@available_time", 90, "Only meals that fit in your available time"),

    # --- recommendation: goals (static profile) --------------------------------
    ("goal_muscle_gain", "recommendation", "dietary_goal = muscle_gain",
     "boost=high_protein:3", 60, "high in protein, which fits your muscle-gain goal"),
    ("goal_weight_loss", "recommendation", "dietary_goal = weight_loss",
     "boost=low_calorie:3;penalize=high_calorie:2", 60,
     "lower in calories, which fits your weight-loss goal"),
    ("goal_weight_gain", "recommendation", "dietary_goal = weight_gain",
     "boost=high_calorie:3", 60, "energy-rich, which fits your weight-gain goal"),
    ("goal_weight_gain_protein", "recommendation", "dietary_goal = weight_gain",
     "boost=high_protein:1", 55, "a good source of protein to support weight gain"),
    ("goal_healthy_balanced", "recommendation", "dietary_goal = healthy_eating",
     "boost=balanced:2", 60, "a balanced meal, which fits your healthy-eating goal"),
    ("goal_healthy_vegetables", "recommendation", "dietary_goal = healthy_eating",
     "boost=vegetables:2", 60, "rich in vegetables, which fits your healthy-eating goal"),

    # --- recommendation: personal targets from the optional body data -----------
    ("target_calories_loss", "recommendation",
     "dietary_goal = weight_loss AND daily_kcal_target > 0",
     "boost=within_calorie_target:2", 58,
     "within your estimated calorie target for this meal"),
    ("target_calories_gain", "recommendation",
     "dietary_goal = weight_gain AND daily_kcal_target > 0 "
     "OR dietary_goal = muscle_gain AND daily_kcal_target > 0",
     "boost=reaches_calorie_target:2", 58, "close to the energy you need for this meal"),
    ("target_protein", "recommendation",
     "protein_target_g > 0 AND dietary_goal != healthy_eating",
     "boost=meets_protein_target:2", 58,
     "enough to cover your estimated protein need for this meal"),

    # --- recommendation: health-friendly choices (soft) ---------------------------
    ("health_diabetes_fibre", "recommendation", "health_conditions CONTAINS diabetes",
     "boost=min:fiber_g:8:1;penalize=min:carbs_g:65:2", 50,
     "rich in fibre, which suits your diabetes setting"),
    ("health_cholesterol_fibre", "recommendation", "health_conditions CONTAINS high_cholesterol",
     "boost=min:fiber_g:8:1", 50, "rich in fibre, which suits your cholesterol setting"),

    # --- recommendation: food preferences --------------------------------------
    ("pref_high_protein", "recommendation", "food_preferences CONTAINS high_protein",
     "boost=high_protein:1", 40, "you like high-protein meals"),
    ("pref_vegetables", "recommendation", "food_preferences CONTAINS vegetables",
     "boost=vegetables:1", 40, "you like vegetables"),
    ("pref_balanced", "recommendation", "food_preferences CONTAINS balanced",
     "boost=balanced:1", 40, "you like balanced meals"),
    ("pref_fish", "recommendation", "food_preferences CONTAINS fish",
     "boost=tag:fish:2", 40, "you like fish and seafood"),
    ("pref_spicy", "recommendation", "food_preferences CONTAINS spicy",
     "boost=tag:spicy:2", 40, "you like spicy food"),
    ("pref_light", "recommendation", "food_preferences CONTAINS light",
     "boost=light:1", 40, "you like light meals"),
    ("pref_high_fiber", "recommendation", "food_preferences CONTAINS high_fiber",
     "boost=min:fiber_g:8:1", 40, "you like fibre-rich meals"),
    ("pref_meal_type", "recommendation", "meal_moment = any",
     "boost=preferred_meal_type:1", 30, "a meal type you said you prefer"),
    ("budget_profile_low", "recommendation", "budget_preference = low AND meal_budget != high",
     "boost=affordable:1", 40, "affordable, in line with your usual budget"),

    # --- recommendation: context + profile combined ---------------------------
    ("short_time_quick", "recommendation", "available_time <= 15",
     "boost=quick:3;card_detail=compact", 70,
     "ready in 15 minutes or less, as you are short on time"),
    ("context_low_budget", "recommendation", "meal_budget = low",
     "boost=affordable:3;penalize=expensive:3", 70,
     "low cost, matching the budget you chose for this meal"),
    ("beginner_short_time", "recommendation", "cooking_level = beginner AND available_time <= 20",
     "boost=easy:2;penalize=hard:5", 65, "easy to make, suited to a beginner with little time"),
    ("beginner_easy", "recommendation", "cooking_level = beginner",
     "boost=easy:1", 35, "easy to make for a beginner cook"),
    ("advanced_with_time", "recommendation", "cooking_level = advanced AND available_time >= 40",
     "boost=challenging:2", 55, "a more ambitious recipe for an experienced cook with time"),

    # --- recommendation: behaviour / history (dynamic profile) ----------------
    ("history_vegetarian", "recommendation",
     "performance.vegetarian_ratio >= 0.6 AND performance.meals_selected >= 3",
     "boost=vegetarian:2", 50, "vegetarian, and you often choose vegetarian meals"),
    ("history_quick", "recommendation",
     "performance.quick_meal_ratio >= 0.7 AND performance.meals_selected >= 3",
     "boost=quick:1", 45, "quick to prepare, like the meals you usually pick"),
    ("history_favorite_category", "recommendation",
     "performance.meals_selected >= 5 AND meal_moment = any",
     "boost=favorite_category:1", 45, "from the meal category you use most"),
    ("history_saved", "recommendation", "performance.meals_saved >= 1",
     "boost=saved:1", 45, "one of your saved meals"),

    # --- interface (Step 5) ---------------------------------------------------
    ("device_desktop", "interface", "device_type = desktop",
     "layout=grid;cards_per_page=9;card_detail=detailed", 50,
     "Desktop: multi-column grid with detailed cards"),
    ("device_tablet", "interface", "device_type = tablet",
     "layout=two_column;cards_per_page=6", 50, "Tablet: two-column layout"),
    ("device_mobile", "interface", "device_type = mobile",
     "layout=single_column;cards_per_page=4;card_detail=compact;nav=bottom", 50,
     "Mobile: single column, fewer meals per screen, compact cards, bottom navigation"),
    ("connection_slow", "interface", "connection_quality = slow",
     "media=reduced;show_images=false;cards_per_page=6", 80,
     "Slow connection: images disabled and fewer meals loaded per page"),
    ("age_large_text", "interface", "age >= 60",
     "text_size=large", 60, "Aged 60 or over: larger text and buttons"),
    ("new_user_tips", "interface", "performance.sessions_count <= 1",
     "show_tips=true", 30, "New user: guidance tips are displayed"),
]

# ---------------------------------------------------------------------------
# Sample users (Step 2) + past sessions and interactions (Step 3 / Step 6)
# ---------------------------------------------------------------------------
AVATAR_OF = {101: "avatar_01", 102: "avatar_16", 103: "avatar_17", 104: "avatar_14", 105: "avatar_08"}

# id, name, goal, budget, level, food prefs, meal types, restrictions, health, allergies, body
USERS = [
    (101, "Alice", "muscle_gain", "medium", "intermediate",
     ["high_protein", "fish"], ["lunch", "dinner"], [], [], [],
     {"age": 24, "sex": "female", "height_cm": 165, "weight_kg": 60, "body_fat_pct": 22,
      "activity_level": "high"}),
    (102, "Bob", "healthy_eating", "low", "beginner",
     ["vegetables", "balanced"], ["breakfast", "lunch"], [], [], [],
     {"age": 45, "sex": "male", "height_cm": 178, "weight_kg": 92, "activity_level": "moderate"}),
    (103, "Carol", "healthy_eating", "medium", "intermediate",
     ["light", "vegetables"], ["lunch", "snack"], ["gluten_free"], ["hypertension"], ["nuts"],
     {"age": 34}),
    (104, "David", "weight_loss", "high", "advanced",
     ["spicy"], ["dinner"], ["vegetarian"], ["diabetes"], [],
     {"age": 52, "sex": "male", "height_cm": 182, "weight_kg": 98, "body_fat_pct": 28,
      "activity_level": "low"}),
    (105, "Emma", "weight_gain", "medium", "intermediate",
     ["balanced"], ["breakfast", "lunch"], [], ["high_cholesterol"], ["fish"],
     {"age": 68, "sex": "female", "height_cm": 160, "weight_kg": 48, "activity_level": "moderate"}),
]

# user_id -> list of (days_ago, device, time, budget, connection, moment, minutes, events)
# events: (meal_id, interaction_type, source)
SESSIONS = {
    101: [
        (12, "desktop", 30, "medium", "fast", "any", 14,
         [(8, "viewed", "recommendation"), (8, "selected", "recommendation"),
          (15, "viewed", "recommendation"), (10, "viewed", "direct")]),
        (7, "mobile", 15, "medium", "normal", "lunch", 6,
         [(10, "viewed", "recommendation"), (10, "selected", "recommendation"),
          (12, "viewed", "recommendation")]),
        (3, "desktop", 45, "high", "fast", "dinner", 22,
         [(15, "viewed", "recommendation"), (15, "selected", "recommendation"),
          (15, "saved", "recommendation"), (19, "viewed", "recommendation"),
          (16, "viewed", "direct")]),
    ],
    102: [
        (10, "mobile", 10, "low", "slow", "any", 5,
         [(9, "viewed", "recommendation"), (9, "selected", "recommendation"),
          (23, "viewed", "recommendation"), (23, "selected", "recommendation")]),
        (6, "tablet", 30, "low", "normal", "lunch", 11,
         [(11, "viewed", "recommendation"), (11, "selected", "recommendation"),
          (14, "viewed", "direct")]),
        (2, "mobile", 15, "low", "normal", "breakfast", 7,
         [(2, "viewed", "recommendation"), (2, "selected", "recommendation"),
          (10, "viewed", "direct"), (10, "selected", "direct"),
          (9, "saved", "recommendation")]),
    ],
    103: [
        (4, "mobile", 10, "medium", "normal", "any", 4,
         [(9, "viewed", "recommendation"), (24, "viewed", "recommendation")]),
    ],
    104: [],
    105: [],
}

SAVED = {101: [15], 102: [9]}


def cost_category(eur):
    return "low" if eur < 4 else "medium" if eur < 8 else "high"


def protein_level(grams, category):
    high, medium = (12, 6) if category == "snack" else (20, 12)
    return "high" if grams >= high else "medium" if grams >= medium else "low"


def _seed_meals(conn):
    meals = db.load_meal_json_files()
    for m in meals:
        n = m["nutrition"]
        conn.execute(
            "INSERT INTO meals (id, name, category, ingredients, prep_time, cost_category, "
            "vegetarian, protein_level, difficulty, description, image, cost_eur, calories_kcal, "
            "protein_g, carbs_g, sugar_g, fat_g, sat_fat_g, fiber_g, salt_g, cholesterol_mg) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET name=excluded.name, category=excluded.category, "
            "ingredients=excluded.ingredients, prep_time=excluded.prep_time, "
            "cost_category=excluded.cost_category, vegetarian=excluded.vegetarian, "
            "protein_level=excluded.protein_level, difficulty=excluded.difficulty, "
            "description=excluded.description, image=excluded.image, cost_eur=excluded.cost_eur, "
            "calories_kcal=excluded.calories_kcal, protein_g=excluded.protein_g, "
            "carbs_g=excluded.carbs_g, sugar_g=excluded.sugar_g, fat_g=excluded.fat_g, "
            "sat_fat_g=excluded.sat_fat_g, fiber_g=excluded.fiber_g, salt_g=excluded.salt_g, "
            "cholesterol_mg=excluded.cholesterol_mg",
            (m["id"], m["name"], m["category"], json.dumps(m["ingredients"]), m["prep_time"],
             cost_category(m["cost_eur"]), int(m["vegetarian"]),
             protein_level(n["protein_g"], m["category"]), m["difficulty"], m["description"],
             m.get("image"), m["cost_eur"], n["calories_kcal"], n["protein_g"], n["carbs_g"],
             n["sugar_g"], n["fat_g"], n["sat_fat_g"], n["fiber_g"], n["salt_g"],
             n["cholesterol_mg"]),
        )
        conn.execute("DELETE FROM meal_tags WHERE meal_id=?", (m["id"],))
        conn.executemany("INSERT INTO meal_tags (meal_id, tag) VALUES (?, ?)",
                         [(m["id"], t) for t in sorted(set(m["dietary_tags"]))])
        conn.execute("DELETE FROM meal_allergens WHERE meal_id=?", (m["id"],))
        conn.executemany("INSERT INTO meal_allergens (meal_id, allergen) VALUES (?, ?)",
                         [(m["id"], a) for a in sorted(set(m["allergens"]))])
    return len(meals)


def _seed_rules(conn):
    if conn.execute("SELECT COUNT(*) FROM rules").fetchone()[0]:
        return 0
    conn.executemany(
        "INSERT INTO rules (name, kind, condition, adaptation, priority, explanation) "
        "VALUES (?, ?, ?, ?, ?, ?)", RULES)
    return len(RULES)


def _seed_users(conn, meals_by_id):
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
        return 0
    now = datetime.now().replace(microsecond=0)
    fmt = "%Y-%m-%d %H:%M:%S"
    for uid, name, goal, budget, level, foods, types, restr, health, allerg, body in USERS:
        conn.execute(
            "INSERT INTO users (id, name, dietary_goal, budget_preference, cooking_level, age, sex, "
            "height_cm, weight_kg, body_fat_pct, activity_level, avatar) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (uid, name, goal, budget, level, body.get("age"), body.get("sex"),
             body.get("height_cm"), body.get("weight_kg"), body.get("body_fat_pct"),
             body.get("activity_level", "moderate"), AVATAR_OF.get(uid)))
        conn.execute("INSERT INTO performance (user_id) VALUES (?)", (uid,))
        conn.executemany(
            "INSERT INTO preferences (user_id, pref_type, preference) VALUES (?, ?, ?)",
            [(uid, "food", p) for p in foods] + [(uid, "meal_type", p) for p in types]
            + [(uid, "restriction", p) for p in restr] + [(uid, "health", p) for p in health]
            + [(uid, "allergy", p) for p in allerg])
        for n, (days, dev, t, bud, cq, moment, minutes, events) in enumerate(SESSIONS[uid]):
            start = (now - timedelta(days=days)).replace(hour=12 + n % 3, minute=5, second=0)
            end = start + timedelta(minutes=minutes)
            snap = json.dumps({"device_type": dev, "available_time": t, "meal_budget": bud,
                               "connection_quality": cq, "meal_moment": moment})
            cur = conn.execute(
                "INSERT INTO context (user_id, session_id, device_type, available_time, "
                "meal_budget, connection_quality, meal_moment, started_at, last_seen_at, "
                "ended_at, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)",
                (uid, f"seed-{uid}-{n}", dev, t, bud, cq, moment,
                 start.strftime(fmt), end.strftime(fmt), end.strftime(fmt)))
            cid = cur.lastrowid
            for k, (mid, itype, src) in enumerate(events):
                meal = meals_by_id[mid]
                ts = start + timedelta(minutes=1 + k * max(1, minutes // (len(events) + 1)))
                conn.execute(
                    "INSERT INTO meal_history (user_id, context_id, meal_id, meal_name, "
                    "meal_category, interaction_type, source, context_snapshot, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (uid, cid, mid, meal["name"], meal["category"], itype, src, snap,
                     ts.strftime(fmt)))
        for mid in SAVED.get(uid, []):
            conn.execute("INSERT INTO saved_meals (user_id, meal_id, saved_at) VALUES (?, ?, ?)",
                         (uid, mid, (now - timedelta(days=3)).strftime(fmt)))
    return len(USERS)


# ---------------------------------------------------------------------------
# Schema versioning / migration
# ---------------------------------------------------------------------------
def _version(path):
    if not os.path.exists(path):
        return None
    con = sqlite3.connect(path)
    try:
        has_tables = con.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        return con.execute("PRAGMA user_version").fetchone()[0] if has_tables else None
    finally:
        con.close()


def _set_version(path):
    con = sqlite3.connect(path)
    con.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    con.commit()
    con.close()


def _migrate_users_v1(path):
    """v1 -> v2: new goal values, optional body columns, new preference types.
    SQLite cannot change a CHECK constraint, so both tables are rebuilt and the
    rows copied (weight_management becomes weight_loss). History is untouched."""
    con = sqlite3.connect(path, isolation_level=None)      # explicit transaction below
    con.execute("PRAGMA foreign_keys = OFF")
    try:
        con.execute("BEGIN")
        con.execute(USERS_TABLE.replace("CREATE TABLE IF NOT EXISTS users", "CREATE TABLE users_new"))
        con.execute(
            "INSERT INTO users_new (id, name, dietary_goal, budget_preference, cooking_level, "
            "created_at) SELECT id, name, CASE dietary_goal WHEN 'weight_management' "
            "THEN 'weight_loss' ELSE dietary_goal END, budget_preference, cooking_level, created_at "
            "FROM users")
        con.execute("DROP TABLE users")
        con.execute("ALTER TABLE users_new RENAME TO users")
        con.execute(PREFERENCES_TABLE.split("\n", 3)[3].replace(
            "CREATE TABLE IF NOT EXISTS preferences", "CREATE TABLE preferences_new"))
        con.execute("INSERT INTO preferences_new SELECT id, user_id, pref_type, preference "
                    "FROM preferences")
        con.execute("DROP TABLE preferences")
        con.execute("ALTER TABLE preferences_new RENAME TO preferences")
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        con.close()


def init_databases(reset=False, verbose=False):
    """Create schemas and seed data. Safe to call at every application start."""
    if reset:
        for path in (db.users_db(), db.rules_db(), db.meals_db()):
            if os.path.exists(path):
                os.remove(path)
    os.makedirs(os.path.dirname(db.users_db()), exist_ok=True)
    notes = []

    # meals.db: pure content, rebuilt from the JSON files when the schema changes
    v = _version(db.meals_db())
    with db.connect(db.meals_db()) as conn:
        if v is not None and v < 2:
            conn.executescript("DROP TABLE IF EXISTS meal_tags; DROP TABLE IF EXISTS meal_allergens;"
                               "DROP TABLE IF EXISTS meals;")
            notes.append("meals.db upgraded to schema v2 (nutrition, cost, allergens)")
        conn.executescript(MEALS_SCHEMA)
        n_meals = _seed_meals(conn)
    _set_version(db.meals_db())

    # rules.db: the default rule base is replaced when the schema version changes
    v = _version(db.rules_db())
    with db.connect(db.rules_db()) as conn:
        conn.executescript(RULES_SCHEMA)
        if v is not None and v < 2:
            conn.execute("DELETE FROM rules")
            notes.append("rules.db upgraded: default rules replaced by the v2 rule base")
        n_rules = _seed_rules(conn)
    _set_version(db.rules_db())

    # users.db: users and history are kept, tables migrated in place
    v = _version(db.users_db())
    migrated = v is not None and v < 2
    if migrated:
        _migrate_users_v1(db.users_db())
        notes.append("users.db migrated to schema v2 (users and history kept)")
    if v is not None and v < 3:
        con = sqlite3.connect(db.users_db())
        cols = [r[1] for r in con.execute("PRAGMA table_info(users)")]
        if "avatar" not in cols:                       # v2 -> v3: one new nullable column
            con.execute("ALTER TABLE users ADD COLUMN avatar TEXT")
            con.commit()
            notes.append("users.db upgraded to schema v3 (avatar)")
        con.close()
    meals_by_id = {m["id"]: m for m in db.get_all_meals()}
    with db.connect(db.users_db()) as conn:
        conn.executescript(USERS_SCHEMA)
        n_users = _seed_users(conn, meals_by_id)
    _set_version(db.users_db())
    if n_users or migrated:
        for user in db.get_all_users():
            db.refresh_performance(user["id"])
    if verbose:
        for note in notes:
            print(note)
        print(f"meals.db : {n_meals} meals synchronised from backend/meals/*.json")
        print(f"rules.db : {n_rules} rules inserted" if n_rules else
              "rules.db : already populated, left unchanged")
        print(f"users.db : {n_users} sample users inserted" if n_users else
              "users.db : already populated, left unchanged")


if __name__ == "__main__":
    init_databases(reset="--reset" in sys.argv, verbose=True)
