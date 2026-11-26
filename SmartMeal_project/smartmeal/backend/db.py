# -*- coding: utf-8 -*-
"""
SmartMeal data-access layer.

Evolution of the original adaptive_quiz_system/backend/db.py:
  * same three-part split (users.db / rules.db / content), but the quiz JSON
    files are replaced by a meals.db table seeded from backend/meals/*.json;
  * every connection enables PRAGMA foreign_keys;
  * every query is parameterised (no string formatting of user input);
  * new sections for the Context model (Step 3), the dynamic user model
    (Step 2: refresh_performance) and the interaction history (Step 6).
"""

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager

from backend.nutrition import NUTRIENTS, body_metrics

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEALS_JSON_DIR = os.path.join(BASE_DIR, "meals")

# Databases live next to this file by default. Tests point this to a temp dir.
_DATA_DIR = os.environ.get("SMARTMEAL_DATA_DIR", BASE_DIR)

# Allowed values, shared by the forms, the validation and the schema CHECKs.
DIETARY_GOALS = ["weight_loss", "weight_gain", "muscle_gain", "healthy_eating"]
BUDGETS = ["low", "medium", "high"]
COOKING_LEVELS = ["beginner", "intermediate", "advanced"]
DEVICES = ["desktop", "tablet", "mobile"]
CONNECTIONS = ["slow", "normal", "fast"]
MEAL_MOMENTS = ["any", "breakfast", "lunch", "dinner", "snack"]
CATEGORIES = ["breakfast", "lunch", "dinner", "snack"]
FOOD_PREFERENCES = ["high_protein", "vegetables", "balanced", "fish", "spicy", "light", "high_fiber"]
RESTRICTIONS = ["vegetarian", "vegan", "gluten_free", "dairy_free"]
HEALTH_CONDITIONS = ["diabetes", "high_cholesterol", "hypertension", "celiac",
                     "lactose_intolerance"]
ALLERGENS = ["gluten", "dairy", "eggs", "nuts", "peanuts", "fish", "shellfish", "soy", "sesame"]
SEXES = ["female", "male"]
AVATARS = [f"avatar_{i:02d}" for i in range(1, 21)]     # static/images/avatars/<key>.svg
ACTIVITY_LEVELS = ["low", "moderate", "high"]
# optional body data: (min, max) accepted values
BODY_RANGES = {"age": (14, 100), "height_cm": (120, 230), "weight_kg": (30, 300),
               "body_fat_pct": (3, 70)}
INTERACTIONS = ["recommended", "viewed", "selected", "saved", "unsaved"]


def set_data_dir(path):
    """Redirect all databases to another folder (used by the tests)."""
    global _DATA_DIR
    _DATA_DIR = path


def db_path(name):
    return os.path.join(_DATA_DIR, name)


def users_db():
    return db_path("users.db")


def rules_db():
    return db_path("rules.db")


def meals_db():
    return db_path("meals.db")


@contextmanager
def connect(path, attach_meals=False):
    """Open a connection with foreign keys ON and commit/rollback handling."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    if attach_meals:
        conn.execute("ATTACH DATABASE ? AS mdb", (meals_db(),))
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Users (static profile)  -- Step 2
# ---------------------------------------------------------------------------
def _hydrate_user(cur, user):
    cur.execute(
        "SELECT pref_type, preference FROM preferences WHERE user_id=? ORDER BY preference",
        (user["id"],),
    )
    rows = cur.fetchall()
    user["food_preferences"] = [r["preference"] for r in rows if r["pref_type"] == "food"]
    user["meal_types"] = [r["preference"] for r in rows if r["pref_type"] == "meal_type"]
    user["restrictions"] = [r["preference"] for r in rows if r["pref_type"] == "restriction"]
    user["health_conditions"] = [r["preference"] for r in rows if r["pref_type"] == "health"]
    user["allergies"] = [r["preference"] for r in rows if r["pref_type"] == "allergy"]
    # kept for backward compatibility with the original "preferences" list
    user["preferences"] = [r["preference"] for r in rows]
    cur.execute("SELECT * FROM performance WHERE user_id=?", (user["id"],))
    perf = cur.fetchone()
    user["performance"] = dict(perf) if perf else {}
    user["metrics"] = body_metrics(user)
    return user


def get_all_users():
    with connect(users_db()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users ORDER BY id")
        return [_hydrate_user(cur, dict(r)) for r in cur.fetchall()]


def get_user(user_id):
    with connect(users_db()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
        row = cur.fetchone()
        return _hydrate_user(cur, dict(row)) if row else None


def _clean_choice(value, allowed, default):
    value = (value or "").strip().lower()
    return value if value in allowed else default


def _clean_list(values, allowed):
    return sorted({v for v in (values or []) if v in allowed})


def _clean_body(body):
    """Validate the optional body data. Empty fields become NULL."""
    body = body or {}
    out = {}
    for key, (lo, hi) in BODY_RANGES.items():
        raw = body.get(key)
        if raw in (None, ""):
            out[key] = None
            continue
        try:
            value = float(str(raw).replace(",", "."))
        except ValueError:
            raise ValueError(f"{key.replace('_', ' ')} must be a number")
        if not lo <= value <= hi:
            raise ValueError(f"{key.replace('_', ' ')} must be between {lo} and {hi}")
        out[key] = int(value) if key == "age" else round(value, 1)
    out["sex"] = body.get("sex") if body.get("sex") in SEXES else None
    out["activity_level"] = _clean_choice(body.get("activity_level"), ACTIVITY_LEVELS, "moderate")
    return out


def save_user_profile(user_id, name, dietary_goal, budget_preference, cooking_level,
                      food_preferences=(), meal_types=(), restrictions=(),
                      health_conditions=(), allergies=(), body=None, avatar=None):
    """Create (user_id=None) or update a user's static profile. Returns the id."""
    name = (name or "").strip()[:60]
    if not name:
        raise ValueError("Name is required")
    goal = _clean_choice(dietary_goal, DIETARY_GOALS, "healthy_eating")
    budget = _clean_choice(budget_preference, BUDGETS, "medium")
    level = _clean_choice(cooking_level, COOKING_LEVELS, "beginner")
    b = _clean_body(body)
    avatar = avatar if avatar in AVATARS else None
    prefs = (
        [("food", p) for p in _clean_list(food_preferences, FOOD_PREFERENCES)]
        + [("meal_type", p) for p in _clean_list(meal_types, CATEGORIES)]
        + [("restriction", p) for p in _clean_list(restrictions, RESTRICTIONS)]
        + [("health", p) for p in _clean_list(health_conditions, HEALTH_CONDITIONS)]
        + [("allergy", p) for p in _clean_list(allergies, ALLERGENS)]
    )
    values = (name, goal, budget, level, b["age"], b["sex"], b["height_cm"], b["weight_kg"],
              b["body_fat_pct"], b["activity_level"], avatar)
    with connect(users_db()) as conn:
        cur = conn.cursor()
        if user_id is None:
            cur.execute(
                "INSERT INTO users (name, dietary_goal, budget_preference, cooking_level, age, sex, "
                "height_cm, weight_kg, body_fat_pct, activity_level, avatar) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", values)
            user_id = cur.lastrowid
            cur.execute("INSERT INTO performance (user_id) VALUES (?)", (user_id,))
        else:
            cur.execute(
                "UPDATE users SET name=?, dietary_goal=?, budget_preference=?, cooking_level=?, "
                "age=?, sex=?, height_cm=?, weight_kg=?, body_fat_pct=?, activity_level=?, avatar=? "
                "WHERE id=?", values + (user_id,))
            if cur.rowcount == 0:
                raise ValueError("Unknown user")
        cur.execute("DELETE FROM preferences WHERE user_id=?", (user_id,))
        cur.executemany(
            "INSERT INTO preferences (user_id, pref_type, preference) VALUES (?, ?, ?)",
            [(user_id, t, p) for t, p in prefs],
        )
    return user_id


# ---------------------------------------------------------------------------
# Rules  -- Step 4
# ---------------------------------------------------------------------------
def get_rules(active_only=True):
    sql = "SELECT * FROM rules"
    if active_only:
        sql += " WHERE active = 1"
    sql += " ORDER BY priority DESC, rule_id"
    with connect(rules_db()) as conn:
        return [dict(r) for r in conn.execute(sql).fetchall()]


# ---------------------------------------------------------------------------
# Meals (content -- replaces the quiz JSON files)
# ---------------------------------------------------------------------------
def _meal_from_row(row, tags, allergens):
    meal = dict(row)
    meal["ingredients"] = json.loads(meal["ingredients"])
    meal["vegetarian"] = bool(meal["vegetarian"])
    meal["dietary_tags"] = sorted(tags.get(meal["id"], []))
    meal["allergens"] = sorted(allergens.get(meal["id"], []))
    meal["nutrition"] = {k: meal[k] for k in NUTRIENTS}
    return meal


def _meal_lists(conn, where="", params=()):
    tags, allergens = {}, {}
    for r in conn.execute("SELECT meal_id, tag FROM meal_tags" + where, params):
        tags.setdefault(r["meal_id"], []).append(r["tag"])
    for r in conn.execute("SELECT meal_id, allergen FROM meal_allergens" + where, params):
        allergens.setdefault(r["meal_id"], []).append(r["allergen"])
    return tags, allergens


def get_all_meals():
    with connect(meals_db()) as conn:
        tags, allergens = _meal_lists(conn)
        rows = conn.execute("SELECT * FROM meals ORDER BY id").fetchall()
        return [_meal_from_row(r, tags, allergens) for r in rows]


def get_meal(meal_id):
    with connect(meals_db()) as conn:
        row = conn.execute("SELECT * FROM meals WHERE id=?", (meal_id,)).fetchone()
        if not row:
            return None
        tags, allergens = _meal_lists(conn, " WHERE meal_id=?", (meal_id,))
        return _meal_from_row(row, tags, allergens)


def load_meal_json_files():
    """Read backend/meals/*.json (the human-editable source of the dataset)."""
    meals = []
    for fname in sorted(os.listdir(MEALS_JSON_DIR)):
        if fname.endswith(".json"):
            with open(os.path.join(MEALS_JSON_DIR, fname), "r", encoding="utf-8") as f:
                meals.extend(json.load(f))
    return meals


# ---------------------------------------------------------------------------
# Context model  -- Step 3
# ---------------------------------------------------------------------------
CONTEXT_DEFAULTS = {"device_type": "desktop", "available_time": 30, "meal_budget": "medium",
                    "connection_quality": "normal", "meal_moment": "any"}


def clean_context(raw, base=None):
    """Validate a context dict coming from a form. Unknown values fall back to base/defaults."""
    base = dict(base or CONTEXT_DEFAULTS)
    raw = raw or {}
    ctx = {
        "device_type": _clean_choice(raw.get("device_type"), DEVICES, base["device_type"]),
        "meal_budget": _clean_choice(raw.get("meal_budget"), BUDGETS, base["meal_budget"]),
        "connection_quality": _clean_choice(raw.get("connection_quality"), CONNECTIONS,
                                            base["connection_quality"]),
        "meal_moment": _clean_choice(raw.get("meal_moment"), MEAL_MOMENTS, base["meal_moment"]),
    }
    try:
        t = int(raw.get("available_time", base["available_time"]))
    except (TypeError, ValueError):
        t = int(base["available_time"])
    ctx["available_time"] = max(1, min(240, t))
    return ctx


def start_session(user_id, raw_context):
    """Close any open session of this user, then INSERT a new context row."""
    ctx = clean_context(raw_context)
    with connect(users_db()) as conn:
        open_ids = [r["id"] for r in conn.execute(
            "SELECT id FROM context WHERE user_id=? AND is_active=1", (user_id,))]
    for cid in open_ids:
        close_session(cid)
    session_id = uuid.uuid4().hex
    with connect(users_db()) as conn:
        cur = conn.execute(
            "INSERT INTO context (user_id, session_id, device_type, available_time, meal_budget, "
            "connection_quality, meal_moment, started_at, last_seen_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'), datetime('now','localtime'))",
            (user_id, session_id, ctx["device_type"], ctx["available_time"], ctx["meal_budget"],
             ctx["connection_quality"], ctx["meal_moment"]),
        )
        context_id = cur.lastrowid
    refresh_performance(user_id)
    return get_context(context_id)


def update_context(context_id, raw_context):
    """UPDATE the context of a running session (e.g. user switches to mobile)."""
    current = get_context(context_id)
    if not current or not current["is_active"]:
        return None
    ctx = clean_context(raw_context, base=current)
    with connect(users_db()) as conn:
        conn.execute(
            "UPDATE context SET device_type=?, available_time=?, meal_budget=?, "
            "connection_quality=?, meal_moment=?, updates_count=updates_count+1, "
            "last_seen_at=datetime('now','localtime') WHERE id=?",
            (ctx["device_type"], ctx["available_time"], ctx["meal_budget"],
             ctx["connection_quality"], ctx["meal_moment"], context_id),
        )
    return get_context(context_id)


def get_context(context_id):
    with connect(users_db()) as conn:
        row = conn.execute("SELECT * FROM context WHERE id=?", (context_id,)).fetchone()
        return dict(row) if row else None


def get_current_context(user_id):
    """Latest active context of the user (used when generating recommendations)."""
    with connect(users_db()) as conn:
        row = conn.execute(
            "SELECT * FROM context WHERE user_id=? AND is_active=1 ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None


def touch_session(context_id):
    with connect(users_db()) as conn:
        conn.execute("UPDATE context SET last_seen_at=datetime('now','localtime') "
                     "WHERE id=? AND is_active=1", (context_id,))


def close_session(context_id):
    """End a session and update the session-level dynamic attributes."""
    with connect(users_db()) as conn:
        row = conn.execute("SELECT user_id FROM context WHERE id=?", (context_id,)).fetchone()
        if not row:
            return
        conn.execute(
            "UPDATE context SET is_active=0, ended_at=COALESCE(ended_at, last_seen_at) WHERE id=?",
            (context_id,),
        )
    refresh_performance(row["user_id"])


def context_snapshot(ctx):
    keys = ["device_type", "available_time", "meal_budget", "connection_quality", "meal_moment"]
    return json.dumps({k: ctx[k] for k in keys}) if ctx else None


# ---------------------------------------------------------------------------
# Interaction history  -- Step 6 (+ feeds the dynamic profile of Step 2)
# ---------------------------------------------------------------------------
def log_interaction(user_id, meal, interaction_type, ctx=None, source="direct", rank=None,
                    refresh=True):
    if interaction_type not in INTERACTIONS:
        raise ValueError("Unknown interaction type")
    if source not in ("recommendation", "direct", "dashboard"):
        source = "direct"
    with connect(users_db()) as conn:
        conn.execute(
            "INSERT INTO meal_history (user_id, context_id, meal_id, meal_name, meal_category, "
            "interaction_type, source, rank_position, context_snapshot, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))",
            (user_id, ctx["id"] if ctx else None, meal["id"], meal["name"], meal["category"],
             interaction_type, source, rank, context_snapshot(ctx)),
        )
        if ctx:
            conn.execute("UPDATE context SET last_seen_at=datetime('now','localtime') "
                         "WHERE id=? AND is_active=1", (ctx["id"],))
    if refresh:
        refresh_performance(user_id)


def log_recommendations(user_id, ranked_meals, ctx):
    """Store what was recommended (once per session + context state + meal)."""
    snap = context_snapshot(ctx)
    with connect(users_db()) as conn:
        for pos, item in enumerate(ranked_meals, start=1):
            meal = item["meal"]
            exists = conn.execute(
                "SELECT 1 FROM meal_history WHERE user_id=? AND context_id=? AND meal_id=? "
                "AND interaction_type='recommended' AND context_snapshot=?",
                (user_id, ctx["id"], meal["id"], snap),
            ).fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO meal_history (user_id, context_id, meal_id, meal_name, "
                    "meal_category, interaction_type, source, rank_position, context_snapshot, "
                    "created_at) VALUES (?, ?, ?, ?, ?, 'recommended', 'recommendation', ?, ?, "
                    "datetime('now','localtime'))",
                    (user_id, ctx["id"], meal["id"], meal["name"], meal["category"], pos, snap),
                )
    refresh_performance(user_id)


def get_saved_meal_ids(user_id):
    with connect(users_db()) as conn:
        return {r["meal_id"] for r in conn.execute(
            "SELECT meal_id FROM saved_meals WHERE user_id=?", (user_id,))}


def toggle_saved(user_id, meal, ctx=None, source="direct"):
    """Save / unsave a meal. Returns True if the meal is now saved."""
    with connect(users_db()) as conn:
        cur = conn.execute("DELETE FROM saved_meals WHERE user_id=? AND meal_id=?",
                           (user_id, meal["id"]))
        now_saved = cur.rowcount == 0
        if now_saved:
            conn.execute("INSERT INTO saved_meals (user_id, meal_id, saved_at) "
                         "VALUES (?, ?, datetime('now','localtime'))", (user_id, meal["id"]))
    log_interaction(user_id, meal, "saved" if now_saved else "unsaved", ctx, source)
    return now_saved


def refresh_performance(user_id):
    """
    Recompute every dynamic attribute of the user model from the raw data
    (meal_history, saved_meals, context) with SQL aggregates, then UPSERT it
    into the performance table. Called after each interaction and each session.
    """
    with connect(users_db(), attach_meals=True) as conn:
        c = conn.execute(
            "SELECT "
            " COALESCE(SUM(interaction_type='viewed'),0)   AS viewed, "
            " COALESCE(SUM(interaction_type='selected'),0) AS selected, "
            " COALESCE(SUM(interaction_type='viewed' AND source='recommendation'),0) AS rec_clicks, "
            " COALESCE(SUM(interaction_type='recommended'),0) AS recommended "
            "FROM meal_history WHERE user_id=?", (user_id,)).fetchone()
        ratios = conn.execute(
            "SELECT COUNT(*) AS n, AVG(m.vegetarian) AS veg, "
            " AVG(m.protein_level='high') AS prot, AVG(m.prep_time<=15) AS quick "
            "FROM meal_history h JOIN mdb.meals m ON m.id = h.meal_id "
            "WHERE h.user_id=? AND h.interaction_type IN ('selected','saved')",
            (user_id,)).fetchone()
        top = conn.execute(
            "SELECT meal_category, COUNT(*) AS n FROM meal_history "
            "WHERE user_id=? AND interaction_type IN ('viewed','selected','saved') "
            "GROUP BY meal_category ORDER BY n DESC, meal_category LIMIT 1",
            (user_id,)).fetchone()
        saved = conn.execute("SELECT COUNT(*) FROM saved_meals WHERE user_id=?",
                             (user_id,)).fetchone()[0]
        sess = conn.execute(
            "SELECT COUNT(*) AS n, "
            " AVG((julianday(COALESCE(ended_at,last_seen_at)) - julianday(started_at))*1440) AS avg_min, "
            " SUM(started_at >= datetime('now','localtime','-7 days')) AS last7, "
            " MAX(last_seen_at) AS last_active "
            "FROM context WHERE user_id=?", (user_id,)).fetchone()
        ctr = round(c["rec_clicks"] / c["recommended"], 3) if c["recommended"] else 0.0
        conn.execute(
            "INSERT INTO performance (user_id, meals_viewed, meals_selected, meals_saved, "
            " recommendation_clicks, recommendation_ctr, top_category, vegetarian_ratio, "
            " high_protein_ratio, quick_meal_ratio, sessions_count, avg_session_minutes, "
            " interaction_frequency, last_active, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?, datetime('now','localtime')) "
            "ON CONFLICT(user_id) DO UPDATE SET "
            " meals_viewed=excluded.meals_viewed, meals_selected=excluded.meals_selected, "
            " meals_saved=excluded.meals_saved, recommendation_clicks=excluded.recommendation_clicks, "
            " recommendation_ctr=excluded.recommendation_ctr, top_category=excluded.top_category, "
            " vegetarian_ratio=excluded.vegetarian_ratio, high_protein_ratio=excluded.high_protein_ratio, "
            " quick_meal_ratio=excluded.quick_meal_ratio, sessions_count=excluded.sessions_count, "
            " avg_session_minutes=excluded.avg_session_minutes, "
            " interaction_frequency=excluded.interaction_frequency, "
            " last_active=excluded.last_active, updated_at=excluded.updated_at",
            (user_id, c["viewed"], c["selected"], saved, c["rec_clicks"], ctr,
             top["meal_category"] if top else None,
             round(ratios["veg"] or 0, 3), round(ratios["prot"] or 0, 3),
             round(ratios["quick"] or 0, 3), sess["n"], round(sess["avg_min"] or 0, 1),
             sess["last7"] or 0, sess["last_active"]),
        )


# ---------------------------------------------------------------------------
# Dashboard queries  -- Step 6
# ---------------------------------------------------------------------------
def category_counts(user_id, interaction_type):
    with connect(users_db()) as conn:
        return [dict(r) for r in conn.execute(
            "SELECT meal_category AS label, COUNT(*) AS value FROM meal_history "
            "WHERE user_id=? AND interaction_type=? GROUP BY meal_category "
            "ORDER BY value DESC, label", (user_id, interaction_type))]


def top_meals(user_id, interaction_type="selected", limit=5):
    with connect(users_db()) as conn:
        return [dict(r) for r in conn.execute(
            "SELECT meal_id, meal_name AS label, meal_category, COUNT(*) AS value "
            "FROM meal_history WHERE user_id=? AND interaction_type=? "
            "GROUP BY meal_id ORDER BY value DESC, label LIMIT ?",
            (user_id, interaction_type, limit))]


def daily_activity(user_id, days=14):
    """Interactions per day (views/selections/saves) over the last N days, gaps filled."""
    with connect(users_db()) as conn:
        rows = {r["day"]: dict(r) for r in conn.execute(
            "SELECT date(created_at) AS day, "
            " SUM(interaction_type='viewed') AS viewed, "
            " SUM(interaction_type='selected') AS selected, "
            " SUM(interaction_type='saved') AS saved "
            "FROM meal_history WHERE user_id=? "
            " AND created_at >= date('now','localtime', ?) "
            "GROUP BY day", (user_id, f"-{days - 1} days"))}
        out = []
        for (day,) in conn.execute(
                "WITH RECURSIVE d(x) AS (SELECT date('now','localtime', ?) "
                " UNION ALL SELECT date(x,'+1 day') FROM d WHERE x < date('now','localtime')) "
                "SELECT x FROM d", (f"-{days - 1} days",)):
            r = rows.get(day, {})
            out.append({"day": day, "viewed": r.get("viewed", 0) or 0,
                        "selected": r.get("selected", 0) or 0, "saved": r.get("saved", 0) or 0})
        return out


def recent_history(user_id, interaction_types=None, limit=15):
    sql = ("SELECT h.*, c.session_id FROM meal_history h LEFT JOIN context c ON c.id=h.context_id "
           "WHERE h.user_id=?")
    params = [user_id]
    if interaction_types:
        sql += " AND h.interaction_type IN (%s)" % ",".join("?" * len(interaction_types))
        params += list(interaction_types)
    sql += " ORDER BY h.created_at DESC, h.id DESC LIMIT ?"
    params.append(limit)
    with connect(users_db()) as conn:
        rows = [dict(r) for r in conn.execute(sql, params)]
    for r in rows:
        r["context"] = json.loads(r["context_snapshot"]) if r["context_snapshot"] else None
    return rows


def session_history(user_id, limit=10):
    with connect(users_db()) as conn:
        return [dict(r) for r in conn.execute(
            "SELECT c.*, "
            " ROUND((julianday(COALESCE(c.ended_at,c.last_seen_at)) - julianday(c.started_at))*1440, 1) "
            "   AS minutes, "
            " (SELECT COUNT(*) FROM meal_history h WHERE h.context_id=c.id "
            "   AND h.interaction_type IN ('viewed','selected','saved')) AS interactions "
            "FROM context c WHERE c.user_id=? ORDER BY c.started_at DESC, c.id DESC LIMIT ?",
            (user_id, limit))]
