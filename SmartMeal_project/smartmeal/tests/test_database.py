# -*- coding: utf-8 -*-
"""Database layer: schema, constraints, safe initialisation, user and context models."""
import os
import sqlite3

import pytest

from backend import db
from backend.init_db import init_databases

TABLES = {
    "users.db": {"users", "preferences", "performance", "context", "meal_history", "saved_meals"},
    "rules.db": {"rules"},
    "meals.db": {"meals", "meal_tags"},
}


def tables(path):
    con = sqlite3.connect(path)
    names = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    con.close()
    return names


def test_all_tables_created(fresh_db):
    for fname, expected in TABLES.items():
        assert expected <= tables(os.path.join(fresh_db, fname))


def test_initialisation_is_safe_and_repeatable(fresh_db):
    db.save_user_profile(101, "Alice", "healthy_eating", "low", "advanced", ["fish"], [], [])
    before = (len(db.get_all_users()), len(db.get_rules(False)), len(db.get_all_meals()))
    init_databases()                      # second run, like a normal app restart
    init_databases()
    after = (len(db.get_all_users()), len(db.get_rules(False)), len(db.get_all_meals()))
    assert before == after
    assert db.get_user(101)["dietary_goal"] == "healthy_eating"   # edit not overwritten


def test_reset_rebuilds_sample_data(fresh_db):
    db.save_user_profile(None, "Temp", "muscle_gain", "low", "beginner")
    init_databases(reset=True)
    assert [u["name"] for u in db.get_all_users()] == ["Alice", "Bob", "Carol", "David", "Emma"]


def test_foreign_keys_are_enforced(fresh_db):
    with pytest.raises(sqlite3.IntegrityError):
        with db.connect(db.users_db()) as con:
            con.execute("INSERT INTO preferences (user_id, pref_type, preference) "
                        "VALUES (999, 'food', 'fish')")


def test_unique_and_check_constraints(fresh_db):
    with pytest.raises(sqlite3.IntegrityError):
        with db.connect(db.users_db()) as con:
            con.execute("INSERT INTO preferences (user_id, pref_type, preference) "
                        "VALUES (101, 'food', 'fish')")          # already exists for Alice
    with pytest.raises(sqlite3.IntegrityError):
        with db.connect(db.users_db()) as con:
            con.execute("INSERT INTO context (user_id, session_id, device_type, available_time, "
                        "meal_budget, connection_quality) VALUES (101,'x','smartwatch',10,'low','fast')")


def test_parameterised_queries_store_hostile_input_literally(fresh_db):
    name = "Robert'); DROP TABLE users;--"
    uid = db.save_user_profile(None, name, "healthy_eating", "low", "beginner")
    assert db.get_user(uid)["name"] == name
    assert "users" in tables(db.users_db())


def test_meal_dataset(fresh_db):
    meals = db.get_all_meals()
    assert len(meals) >= 20
    assert {m["category"] for m in meals} == {"breakfast", "lunch", "dinner", "snack"}
    static = os.path.join(os.path.dirname(db.BASE_DIR), "static", "images")
    for m in meals:
        for key in ("name", "ingredients", "prep_time", "cost_category", "dietary_tags",
                    "vegetarian", "protein_level", "description", "image"):
            assert key in m
        assert os.path.exists(os.path.join(static, m["image"]))


def test_static_profile_update_filters_invalid_values(fresh_db):
    db.save_user_profile(102, "Bob", "muscle_gain", "high", "advanced",
                         ["fish", "pizza"], ["dinner", "brunch"], ["vegan", "keto"])
    bob = db.get_user(102)
    assert (bob["dietary_goal"], bob["budget_preference"], bob["cooking_level"]) == \
        ("muscle_gain", "high", "advanced")
    assert bob["food_preferences"] == ["fish"]
    assert bob["meal_types"] == ["dinner"]
    assert bob["restrictions"] == ["vegan"]


def test_context_insert_update_retrieve(fresh_db):
    ctx = db.start_session(103, {"device_type": "mobile", "available_time": "12",
                                 "meal_budget": "low", "connection_quality": "slow"})
    assert db.get_current_context(103)["id"] == ctx["id"]
    updated = db.update_context(ctx["id"], {"device_type": "desktop", "available_time": 45})
    assert updated["id"] == ctx["id"] and updated["session_id"] == ctx["session_id"]
    assert (updated["device_type"], updated["available_time"], updated["meal_budget"]) == \
        ("desktop", 45, "low")             # unspecified values keep their current value
    assert updated["updates_count"] == 1
    second = db.start_session(103, {})     # a new session closes the previous one
    assert db.get_context(ctx["id"])["is_active"] == 0
    assert db.get_current_context(103)["id"] == second["id"]


def test_clean_context_validation():
    c = db.clean_context({"device_type": "fridge", "available_time": "9999",
                          "meal_budget": "HIGH", "connection_quality": None})
    assert c == {"device_type": "desktop", "available_time": 240, "meal_budget": "high",
                 "connection_quality": "normal", "meal_moment": "any"}


def test_dynamic_attributes_update_after_each_interaction(fresh_db):
    ctx = db.start_session(104, {})
    p0 = db.get_user(104)["performance"]
    assert (p0["meals_viewed"], p0["meals_selected"], p0["sessions_count"]) == (0, 0, 1)
    curry = db.get_meal(17)                       # vegetarian dinner
    db.log_interaction(104, curry, "viewed", ctx, "recommendation")
    db.log_interaction(104, curry, "selected", ctx, "recommendation")
    assert db.toggle_saved(104, curry, ctx) is True
    p = db.get_user(104)["performance"]
    assert p["meals_viewed"] == 1 and p["meals_selected"] == 1 and p["meals_saved"] == 1
    assert p["recommendation_clicks"] == 1
    assert p["top_category"] == "dinner"
    assert p["vegetarian_ratio"] == 1.0
    assert db.toggle_saved(104, curry, ctx) is False
    assert db.get_user(104)["performance"]["meals_saved"] == 0


def test_session_duration_is_measured(fresh_db):
    ctx = db.start_session(104, {})
    with db.connect(db.users_db()) as con:      # simulate a 10-minute session
        con.execute("UPDATE context SET started_at=datetime('now','localtime','-10 minutes') "
                    "WHERE id=?", (ctx["id"],))
    db.close_session(ctx["id"])
    p = db.get_user(104)["performance"]
    assert p["sessions_count"] == 1
    assert 9.9 <= p["avg_session_minutes"] <= 10.1
    assert p["interaction_frequency"] == 1


def test_dashboard_queries(fresh_db):
    acts = db.daily_activity(102, 14)
    assert len(acts) == 14 and sum(a["selected"] for a in acts) == 5
    assert db.category_counts(102, "selected")[0]["value"] >= 1
    assert [m["label"] for m in db.top_meals(101, "selected")] == [
        "Grilled Chicken Quinoa Bowl", "Salmon with Roasted Vegetables", "Tuna & Sweetcorn Wrap"]
    assert len(db.session_history(101)) == 3
