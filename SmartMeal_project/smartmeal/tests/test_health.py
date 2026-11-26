# -*- coding: utf-8 -*-
"""Version 2 features: nutrition data, weight goals, optional body data,
health conditions and allergies (multi-select), estimated cost, migration, photos."""
import os
import sqlite3

import pytest

from adapt_meal import adapt_meal
from backend import db
from backend.init_db import RULES, init_databases
from backend.nutrition import NUTRIENTS, body_metrics
from conftest import CTX_A

CTX_ALL = {**CTX_A, "available_time": 90}      # no time filter: only health rules filter


# ------------------------------------------------------------------ meal data
def test_every_meal_has_nutrition_cost_and_allergens(fresh_db):
    for m in db.get_all_meals():
        n = m["nutrition"]
        assert set(n) == set(NUTRIENTS) and all(v >= 0 for v in n.values())
        assert m["cost_eur"] > 0
        # energy consistency: 4 kcal/g protein & carbs, 9 kcal/g fat (within 20 %)
        assert abs(4 * n["protein_g"] + 4 * n["carbs_g"] + 9 * n["fat_g"] - n["calories_kcal"]) \
            <= 0.2 * n["calories_kcal"]
        assert n["sugar_g"] <= n["carbs_g"] and n["sat_fat_g"] <= n["fat_g"]
        if "gluten_free" in m["dietary_tags"]:
            assert "gluten" not in m["allergens"]
        if m["vegetarian"]:
            assert not {"fish", "shellfish"} & set(m["allergens"])
        assert m["cost_category"] == ("low" if m["cost_eur"] < 4 else
                                      "medium" if m["cost_eur"] < 8 else "high")


# ------------------------------------------------------------------ body metrics
def test_mifflin_st_jeor_and_targets():
    m = body_metrics({"age": 30, "sex": "male", "height_cm": 180, "weight_kg": 80,
                      "activity_level": "moderate", "dietary_goal": "healthy_eating"})
    assert m["bmr"] == 1780 and m["daily_kcal_target"] == 2760
    assert m["bmi"] == 24.7 and m["protein_target_g"] == 80


def test_katch_mcardle_when_body_fat_is_known():
    m = body_metrics({"weight_kg": 80, "body_fat_pct": 20, "activity_level": "low",
                      "dietary_goal": "weight_loss"})
    assert m["bmr"] == 1752                                # 370 + 21.6 x 64 kg lean mass
    assert m["daily_kcal_target"] == 1680                  # 1752.4 x 1.2 x 0.8
    assert m["method"].startswith("Katch-McArdle")


def test_goal_changes_energy_target_and_floor():
    base = {"age": 40, "sex": "female", "height_cm": 160, "weight_kg": 55, "activity_level": "low"}
    loss = body_metrics({**base, "dietary_goal": "weight_loss"})["daily_kcal_target"]
    gain = body_metrics({**base, "dietary_goal": "weight_gain"})["daily_kcal_target"]
    assert loss < gain
    tiny = body_metrics({"age": 90, "sex": "female", "height_cm": 140, "weight_kg": 32,
                         "activity_level": "low", "dietary_goal": "weight_loss"})
    assert tiny["daily_kcal_target"] == 1200                # never below the safety floor


def test_protein_uses_reference_weight_above_bmi_25():
    m = body_metrics({"height_cm": 182, "weight_kg": 98, "dietary_goal": "weight_loss"})
    assert m["protein_target_g"] == round(25 * 1.82 ** 2 * 1.6)


def test_missing_body_data_gives_no_targets():
    m = body_metrics({"age": 34, "dietary_goal": "healthy_eating"})
    assert m["daily_kcal_target"] is None and m["protein_target_g"] is None and m["bmi"] is None


def test_body_data_is_optional_and_validated(fresh_db):
    uid = db.save_user_profile(None, "Nora", "weight_gain", "low", "beginner",
                               body={"age": "", "height_cm": "", "weight_kg": "61,5"})
    u = db.get_user(uid)
    assert u["age"] is None and u["height_cm"] is None and u["weight_kg"] == 61.5
    with pytest.raises(ValueError):
        db.save_user_profile(uid, "Nora", "weight_gain", "low", "beginner", body={"age": "5"})
    with pytest.raises(ValueError):
        db.save_user_profile(uid, "Nora", "weight_gain", "low", "beginner", body={"weight_kg": "abc"})


# ------------------------------------------------------------------ health & allergies
def test_diabetes_limits_sugar(fresh_db):
    r = adapt_meal(db.get_user(104), CTX_ALL)                # David: diabetes + vegetarian
    assert r["ranked"] and all(c["meal"]["nutrition"]["sugar_g"] <= 12 for c in r["ranked"])
    assert all(c["meal"]["vegetarian"] for c in r["ranked"])
    assert any("diabetes" in e["reason"] for e in r["excluded"])


def test_hypertension_and_nut_allergy(fresh_db):
    r = adapt_meal(db.get_user(103), CTX_ALL)                # Carol
    for c in r["ranked"]:
        assert c["meal"]["nutrition"]["salt_g"] <= 1.5
        assert "nuts" not in c["meal"]["allergens"] and "gluten" not in c["meal"]["allergens"]
        assert len(c["checks"]) == 3                         # gluten, salt, nuts shown on card


def test_cholesterol_and_fish_allergy(fresh_db):
    r = adapt_meal(db.get_user(105), CTX_ALL)                # Emma
    for c in r["ranked"]:
        n = c["meal"]["nutrition"]
        assert n["sat_fat_g"] <= 6 and n["cholesterol_mg"] <= 200
        assert "fish" not in c["meal"]["allergens"]


def test_several_conditions_and_allergies_combine(fresh_db):
    uid = db.save_user_profile(
        None, "Multi", "healthy_eating", "medium", "intermediate",
        health_conditions=["diabetes", "hypertension", "celiac", "lactose_intolerance"],
        allergies=["peanuts", "sesame", "eggs"])
    user = db.get_user(uid)
    assert len(user["health_conditions"]) == 4 and len(user["allergies"]) == 3
    r = adapt_meal(user, CTX_ALL)
    assert r["ranked"], "at least one meal should remain"
    for c in r["ranked"]:
        m, n = c["meal"], c["meal"]["nutrition"]
        assert n["sugar_g"] <= 12 and n["salt_g"] <= 1.5
        assert not {"gluten", "dairy", "peanuts", "sesame", "eggs"} & set(m["allergens"])


def test_invalid_health_values_are_ignored(fresh_db):
    uid = db.save_user_profile(None, "X", "healthy_eating", "low", "beginner",
                               health_conditions=["diabetes", "flu"], allergies=["kiwi", "soy"])
    u = db.get_user(uid)
    assert u["health_conditions"] == ["diabetes"] and u["allergies"] == ["soy"]


# ------------------------------------------------------------------ goals and targets
def mean_kcal(result, n=5):
    top = result["ranked"][:n]
    return sum(c["meal"]["nutrition"]["calories_kcal"] for c in top) / len(top)


def test_weight_loss_vs_weight_gain_rankings(fresh_db):
    profile = dict(name="G", budget_preference="medium", cooking_level="intermediate",
                   body={"age": 30, "sex": "female", "height_cm": 168, "weight_kg": 62})
    loss = db.get_user(db.save_user_profile(None, dietary_goal="weight_loss", **profile))
    profile["name"] = "H"
    gain = db.get_user(db.save_user_profile(None, dietary_goal="weight_gain", **profile))
    for moment in ("breakfast", "lunch", "dinner", "snack"):   # compare like with like
        ctx = {**CTX_ALL, "meal_moment": moment}
        r_loss, r_gain = adapt_meal(loss, ctx), adapt_meal(gain, ctx)
        assert mean_kcal(r_loss, 3) < mean_kcal(r_gain, 3), moment
    assert "target_calories_loss" in [f["name"] for f in r_loss["fired"]]
    assert "target_calories_gain" in [f["name"] for f in r_gain["fired"]]


def test_personal_target_rules_need_body_data(fresh_db):
    fired = lambda uid: {f["name"] for f in adapt_meal(db.get_user(uid), CTX_ALL)["fired"]}
    assert {"target_calories_gain", "target_protein"} <= fired(101)      # Alice: full data
    assert not {"target_calories_gain", "target_protein", "target_calories_loss"} & fired(103)


def test_age_60_plus_gets_large_text(fresh_db, client):
    assert adapt_meal(db.get_user(105), CTX_A)["ui"]["text_size"] == "large"
    assert adapt_meal(db.get_user(101), CTX_A)["ui"]["text_size"] == "normal"
    html = client.post("/", data={"user_id": 105, **CTX_A},
                       follow_redirects=True).get_data(as_text=True)
    assert 'class="text-large' in html


# ------------------------------------------------------------------ UI
def test_profile_form_saves_health_and_body(client):
    client.post("/", data={"user_id": 102, **CTX_A})
    client.post("/profile", data={
        "name": "Bob", "dietary_goal": "weight_loss", "budget_preference": "low",
        "cooking_level": "beginner", "health_conditions": ["diabetes", "hypertension"],
        "allergies": ["eggs"], "age": "45", "sex": "male", "height_cm": "178",
        "weight_kg": "92", "body_fat_pct": "", "activity_level": "low"})
    bob = db.get_user(102)
    assert bob["dietary_goal"] == "weight_loss"
    assert bob["health_conditions"] == ["diabetes", "hypertension"] and bob["allergies"] == ["eggs"]
    assert bob["body_fat_pct"] is None and bob["metrics"]["daily_kcal_target"] > 0
    page = client.get("/profile").get_data(as_text=True)
    assert "Energy per day for your goal" in page
    plan = client.get("/plan").get_data(as_text=True)
    assert "Fits your health and diet settings" in plan


def test_cards_and_details_show_nutrition_and_cost(client):
    client.post("/", data={"user_id": 101, **CTX_A})
    plan = client.get("/plan").get_data(as_text=True)
    assert "kcal" in plan and "≈ €" in plan and 'class="macros"' in plan
    page = client.get("/meal/15").get_data(as_text=True)
    assert "Nutrition per serving" in page and "Cholesterol" in page
    assert "Your target for this meal" in page                 # Alice has body data


def test_own_photo_replaces_illustration(tmp_path, monkeypatch):
    import app as app_module
    monkeypatch.setattr(app_module, "STATIC_DIR", str(tmp_path))   # never touch the real folder
    meal = {"id": 3, "image": "meals/meal_03.svg"}
    assert app_module.meal_image(meal) == "images/meals/meal_03.svg"
    photos = tmp_path / "images" / "meals" / "photos"
    photos.mkdir(parents=True)
    (photos / "meal_03.jpg").write_bytes(b"")
    assert app_module.meal_image(meal) == "images/meals/photos/meal_03.jpg"


# ------------------------------------------------------------------ migration
V1_USERS = """
CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE,
  dietary_goal TEXT NOT NULL DEFAULT 'healthy_eating'
    CHECK (dietary_goal IN ('muscle_gain','healthy_eating','weight_management')),
  budget_preference TEXT NOT NULL DEFAULT 'medium', cooking_level TEXT NOT NULL DEFAULT 'beginner',
  created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')));
CREATE TABLE preferences (id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  pref_type TEXT NOT NULL CHECK (pref_type IN ('food','meal_type','restriction')),
  preference TEXT NOT NULL, UNIQUE (user_id, pref_type, preference));
CREATE TABLE meal_history (id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, context_id INTEGER,
  meal_id INTEGER NOT NULL, meal_name TEXT NOT NULL, meal_category TEXT NOT NULL,
  interaction_type TEXT NOT NULL, source TEXT NOT NULL DEFAULT 'direct', rank_position INTEGER,
  context_snapshot TEXT, created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')));
INSERT INTO users (id, name, dietary_goal) VALUES (7, 'Old', 'weight_management');
INSERT INTO preferences (user_id, pref_type, preference) VALUES (7, 'restriction', 'vegan');
INSERT INTO meal_history (user_id, meal_id, meal_name, meal_category, interaction_type)
  VALUES (7, 9, 'Chickpea & Vegetable Salad', 'lunch', 'selected');
"""


def test_v1_databases_are_migrated_in_place(tmp_path):
    db.set_data_dir(str(tmp_path))
    con = sqlite3.connect(db.users_db()); con.executescript(V1_USERS); con.close()
    con = sqlite3.connect(db.rules_db())
    con.executescript("CREATE TABLE rules (rule_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, "
                      "kind TEXT NOT NULL, condition TEXT NOT NULL, adaptation TEXT NOT NULL, "
                      "priority INTEGER NOT NULL DEFAULT 50, explanation TEXT NOT NULL, "
                      "active INTEGER NOT NULL DEFAULT 1);"
                      "INSERT INTO rules (name, kind, condition, adaptation, explanation) "
                      "VALUES ('old', 'interface', 'device_type = mobile', 'layout=grid', 'x');")
    con.close()
    con = sqlite3.connect(db.meals_db())
    con.executescript("CREATE TABLE meals (id INTEGER PRIMARY KEY, name TEXT);"
                      "CREATE TABLE meal_tags (meal_id INTEGER, tag TEXT);")
    con.close()

    init_databases()

    old = db.get_user(7)
    assert old["dietary_goal"] == "weight_loss" and old["restrictions"] == ["vegan"]
    assert old["age"] is None and old["activity_level"] == "moderate"
    assert old["performance"]["meals_selected"] == 1          # history kept
    assert len(db.get_rules(False)) == len(RULES)              # rule base replaced
    assert db.get_meal(9)["nutrition"]["calories_kcal"] > 0    # meals rebuilt
    db.save_user_profile(7, "Old", "weight_gain", "low", "beginner",
                         health_conditions=["diabetes"], body={"age": 70})
    assert db.get_user(7)["health_conditions"] == ["diabetes"]
    init_databases()                                           # second run changes nothing
    assert db.get_user(7)["dietary_goal"] == "weight_gain"
