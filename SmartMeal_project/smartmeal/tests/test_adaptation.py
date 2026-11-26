# -*- coding: utf-8 -*-
"""Rule parser and adaptation engine (Step 4)."""
import pytest

from adapt_meal import (RuleError, adapt_meal, adapt_meal_plan, evaluate_condition,
                        parse_adaptation, parse_condition)
from backend import db

USER = {"id": 1, "name": "T", "dietary_goal": "muscle_gain", "cooking_level": "beginner",
        "budget_preference": "low", "food_preferences": ["fish", "spicy"], "meal_types": [],
        "restrictions": ["vegetarian"], "performance": {"avg_score": 72, "meals_selected": 4,
                                                         "vegetarian_ratio": 0.75}}


@pytest.mark.parametrize("condition, ctx, expected", [
    # the two cases that were broken in the original adapt_quiz.py
    ("available_time<=10", {"available_time": 60}, False),
    ("available_time<=10", {"available_time": 10}, True),
    ("performance.avg_score>=70", {}, True),
    ("performance.avg_score>=80", {}, False),
    ("available_time < 10", {"available_time": 10}, False),
    ("available_time > 5", {"available_time": 10}, True),
    ("device_type = mobile", {"device_type": "Mobile"}, True),      # case-insensitive
    ("device_type != mobile", {"device_type": "desktop"}, True),
    ("dietary_goal = muscle_gain AND available_time <= 15", {"available_time": 15}, True),
    ("dietary_goal = muscle_gain AND available_time <= 15", {"available_time": 16}, False),
    ("device_type = tablet OR available_time <= 15", {"device_type": "desktop",
                                                      "available_time": 12}, True),
    ("restrictions CONTAINS vegetarian", {}, True),
    ("restrictions NOT CONTAINS vegan", {}, True),
    ("food_preferences CONTAINS fish AND performance.vegetarian_ratio >= 0.6", {}, True),
    ("unknown_key = 3", {}, False),                                # fails closed
    ("performance.unknown >= 0", {}, False),
    ("device_type >= 3", {"device_type": "mobile"}, False),          # no ordering on text
])
def test_condition_operators(condition, ctx, expected):
    assert evaluate_condition(condition, USER, ctx) is expected


def test_and_inside_words_is_not_a_separator():
    groups = parse_condition("meal_moment = HIGHLAND AND device_type = BRANDY")
    assert groups == [[("meal_moment", "=", "HIGHLAND"), ("device_type", "=", "BRANDY")]]


@pytest.mark.parametrize("bad", ["", "device_type mobile", "available_time <=", "= 3"])
def test_invalid_conditions_raise(bad):
    with pytest.raises(RuleError):
        parse_condition(bad)


@pytest.mark.parametrize("bad", ["boost=high_protein", "boost=pizza:2", "layout=diagonal",
                                 "cards_per_page=many", "nonsense=1", "filter=unknown"])
def test_invalid_adaptations_raise(bad):
    with pytest.raises(RuleError):
        parse_adaptation(bad)


def rule(rid, name, cond, adapt, prio=50, kind="recommendation"):
    return {"rule_id": rid, "name": name, "kind": kind, "condition": cond, "adaptation": adapt,
            "priority": prio, "explanation": name.replace("_", " ")}


MEALS = [
    {"id": 1, "name": "Fast veg", "category": "lunch", "prep_time": 5, "cost_category": "low",
     "vegetarian": True, "protein_level": "high", "difficulty": "easy", "dietary_tags": ["light"]},
    {"id": 2, "name": "Slow veg", "category": "dinner", "prep_time": 40, "cost_category": "high",
     "vegetarian": True, "protein_level": "low", "difficulty": "hard", "dietary_tags": []},
    {"id": 3, "name": "Fast fish", "category": "lunch", "prep_time": 10, "cost_category": "high",
     "vegetarian": False, "protein_level": "high", "difficulty": "easy", "dietary_tags": ["fish"]},
]
CTX = {"device_type": "mobile", "available_time": 15, "meal_budget": "low",
       "connection_quality": "slow", "meal_moment": "any"}


def test_multiple_rules_are_combined_not_overwritten():
    rules = [
        rule(1, "protein", "dietary_goal = muscle_gain", "boost=high_protein:3"),
        rule(2, "cheap", "meal_budget = low", "boost=affordable:2;penalize=expensive:1"),
        rule(3, "mobile", "device_type = mobile",
             "layout=single_column;cards_per_page=4;card_detail=compact", 50, "interface"),
        rule(4, "slow", "connection_quality = slow",
             "show_images=false;media=reduced;cards_per_page=6", 80, "interface"),
        rule(5, "desk", "available_time >= 1", "layout=grid;card_detail=detailed", 10, "interface"),
        rule(6, "time", "available_time >= 1", "max_prep_time=@available_time", 90, "constraint"),
    ]
    r = adapt_meal_plan({**USER, "restrictions": []}, CTX, MEALS, rules)
    assert [c["meal"]["id"] for c in r["ranked"]] == [1, 3]          # meal 2 too slow
    assert r["ranked"][0]["score"] == 5                               # 3 + 2 (both rules)
    assert r["ranked"][1]["score"] == 2                               # 3 - 1
    ui = r["ui"]
    assert ui["layout"] == "single_column"                           # priority 50 beats 10
    assert ui["cards_per_page"] == 4                                  # min(4, 6)
    assert ui["show_images"] is False and ui["media"] == "reduced"    # untouched by mobile rule
    assert {c["setting"] for c in r["conflicts"]} == {"layout", "card_detail"}
    assert r["max_prep_time"] == 15


def test_hard_filters_and_reference_values():
    rules = [rule(1, "veg", "restrictions CONTAINS vegetarian", "filter=vegetarian", 100, "constraint"),
             rule(2, "moment", "meal_moment != any", "filter=category:@meal_moment", 95, "constraint")]
    r = adapt_meal_plan(USER, {**CTX, "meal_moment": "dinner"}, MEALS, rules)
    assert [c["meal"]["id"] for c in r["ranked"]] == [2]
    reasons = {e["meal"]["id"]: e["reason"] for e in r["excluded"]}
    assert reasons[3] == "veg" and reasons[1] == "moment"


def test_broken_rule_is_reported_and_skipped():
    rules = [rule(1, "broken", "available_time <=", "boost=quick:1"),
             rule(2, "ok", "available_time <= 30", "boost=quick:1")]
    r = adapt_meal_plan(USER, CTX, MEALS, rules)
    assert [e["rule"]["name"] for e in r["errors"]] == ["broken"]
    assert [f["name"] for f in r["fired"]] == ["ok"]


def test_relaxes_time_when_nothing_fits():
    rules = [rule(1, "time", "available_time >= 1", "max_prep_time=@available_time")]
    r = adapt_meal_plan(USER, {**CTX, "available_time": 2}, MEALS, rules)
    assert r["relaxed_time"] is True and r["ranked"][0]["meal"]["id"] == 1


def test_every_stored_rule_parses(fresh_db):
    r = adapt_meal(db.get_user(101), CTX)
    assert r["errors"] == []
    assert len(r["fired"]) + len(r["not_fired"]) == len(db.get_rules())


def test_rules_are_read_from_sqlite(fresh_db):
    alice = db.get_user(101)
    assert adapt_meal(alice, CTX)["ui"]["layout"] == "single_column"
    with db.connect(db.rules_db()) as con:          # disable the rule in the database only
        con.execute("UPDATE rules SET active=0 WHERE name='device_mobile'")
    assert adapt_meal(alice, CTX)["ui"]["layout"] == "grid"       # back to the default


def test_restrictions_are_always_respected(fresh_db):
    david = db.get_user(104)                       # vegetarian restriction
    carol = db.get_user(103)                       # gluten-free restriction
    for ctx in (CTX, {**CTX, "available_time": 90, "device_type": "desktop"}):
        assert all(c["meal"]["vegetarian"] for c in adapt_meal(david, ctx)["ranked"])
        assert all("gluten_free" in c["meal"]["dietary_tags"]
                   for c in adapt_meal(carol, ctx)["ranked"])


def test_recommendations_carry_an_explanation(fresh_db):
    r = adapt_meal(db.get_user(102), CTX)
    top = r["ranked"][0]
    assert top["explanation"].startswith("Recommended because")
    assert top["reasons"] and top["breakdown"]


def test_history_changes_adaptation(fresh_db):
    """Dynamic profile -> rule: choosing vegetarian meals boosts vegetarian meals."""
    ctx = db.start_session(103, {"available_time": 30})
    carol = db.get_user(103)
    before = adapt_meal(carol, ctx)
    assert "history_vegetarian" not in [f["name"] for f in before["fired"]]
    for mid in (9, 23, 24):                        # three vegetarian, gluten-free meals
        db.log_interaction(103, db.get_meal(mid), "selected", ctx)
    after = adapt_meal(db.get_user(103), ctx)
    assert "history_vegetarian" in [f["name"] for f in after["fired"]]
    score = lambda res, mid: next(c["score"] for c in res["ranked"] if c["meal"]["id"] == mid)
    assert score(after, 9) > score(before, 9)
