# -*- coding: utf-8 -*-
"""
Required evaluation scenarios (A, B, C), checked twice:
  1. on the engine output (recommendations + interface settings);
  2. on the HTML actually served by Flask (visible adaptation).
"""
import re

from adapt_meal import adapt_meal
from backend import db
from conftest import CTX_A, CTX_B, CTX_C


def top_ids(result, n=5):
    return [c["meal"]["id"] for c in result["ranked"][:n]]


def test_scenario_A_muscle_gain_desktop(fresh_db):
    r = adapt_meal(db.get_user(101), CTX_A)
    assert all(c["meal"]["protein_level"] == "high" for c in r["ranked"][:5])
    assert all(c["meal"]["prep_time"] <= 30 for c in r["ranked"])
    assert r["ui"]["layout"] == "grid" and r["ui"]["cards_per_page"] == 9
    assert r["ui"]["show_images"] is True and r["ui"]["card_detail"] == "detailed"


def test_scenario_B_healthy_mobile_slow(fresh_db):
    r = adapt_meal(db.get_user(102), CTX_B)
    assert r["ranked"] and all(c["meal"]["prep_time"] <= 10 for c in r["ranked"])
    assert all(c["meal"]["cost_category"] == "low" for c in r["ranked"][:5])
    assert r["ui"]["layout"] == "single_column" and r["ui"]["nav"] == "bottom"
    assert r["ui"]["show_images"] is False and r["ui"]["media"] == "reduced"
    assert r["ui"]["cards_per_page"] <= 4


def test_scenario_C_same_user_new_context(fresh_db):
    alice = db.get_user(101)
    a, c = adapt_meal(alice, CTX_A), adapt_meal(alice, CTX_C)
    assert top_ids(a) != top_ids(c)
    assert all(x["meal"]["prep_time"] <= 10 for x in c["ranked"])
    assert all(x["meal"]["protein_level"] == "high" for x in c["ranked"][:5])  # goal still applies
    assert a["ui"] != c["ui"]
    assert (c["ui"]["layout"], c["ui"]["card_detail"]) == ("single_column", "compact")
    assert "short_time_quick" in [f["name"] for f in c["fired"]]
    assert "short_time_quick" not in [f["name"] for f in a["fired"]]


def test_two_users_same_context_get_different_plans(fresh_db):
    for ctx in (CTX_A, CTX_C):
        alice, bob = adapt_meal(db.get_user(101), ctx), adapt_meal(db.get_user(102), ctx)
        assert top_ids(alice) != top_ids(bob)


# ---------------------------------------------------------------- Flask (visible UI)
def start(client, user_id, ctx):
    return client.post("/", data={"user_id": user_id, **ctx}, follow_redirects=True)


def body_class(html):
    return re.search(r'<body class="([^"]+)"', html).group(1)


def test_ui_scenario_A_then_C_in_the_same_session(client):
    html = start(client, 101, CTX_A).get_data(as_text=True)
    assert "layout-grid" in body_class(html) and "device-desktop" in body_class(html)
    assert html.count('class="meal-card') == 9 and "<img" in html
    assert "Recommended because" in html
    ctx_before = db.get_current_context(101)

    html = client.post("/context", data={"device_type": "mobile", "available_time": 10,
                                         "next": "/plan"}, follow_redirects=True).get_data(as_text=True)
    cls = body_class(html)
    assert "layout-single_column" in cls and "nav-bottom" in cls and "detail-compact" in cls
    assert html.count('class="meal-card') == 4
    ctx_after = db.get_current_context(101)
    assert ctx_after["id"] == ctx_before["id"] and ctx_after["updates_count"] == 1
    assert ctx_after["device_type"] == "mobile" and ctx_after["available_time"] == 10


def test_ui_scenario_B_reduced_media(client):
    html = start(client, 102, CTX_B).get_data(as_text=True)
    assert "media-reduced" in body_class(html)
    assert "Low-data mode" in html
    meals_section = html.split('aria-label="Recommended meals"')[1].split("</section>")[0]
    assert "<img" not in meals_section


def test_ui_interactions_update_profile_and_dashboard(client):
    start(client, 104, CTX_A)
    assert client.get("/meal/17?src=rec").status_code == 200
    client.post("/meal/17/select", data={"src": "rec", "next": "/plan"})
    client.post("/meal/17/save", data={"src": "rec", "next": "/plan"})
    p = db.get_user(104)["performance"]
    assert (p["meals_viewed"], p["meals_selected"], p["meals_saved"]) == (1, 1, 1)
    assert p["recommendation_clicks"] == 1
    page = client.get("/dashboard").get_data(as_text=True)
    assert "Chickpea &amp; Spinach Curry" in page
    with db.connect(db.users_db()) as con:
        n = con.execute("SELECT COUNT(*) FROM meal_history WHERE user_id=104 "
                        "AND interaction_type='recommended'").fetchone()[0]
    assert n == 9                                  # the 9 cards shown were logged once
    client.get("/plan")
    with db.connect(db.users_db()) as con:
        assert con.execute("SELECT COUNT(*) FROM meal_history WHERE user_id=104 "
                           "AND interaction_type='recommended'").fetchone()[0] == 9


def test_profile_edit_changes_recommendations(client):
    start(client, 101, CTX_A)
    before = client.get("/plan").get_data(as_text=True)
    client.post("/profile", data={"name": "Alice", "dietary_goal": "healthy_eating",
                                  "budget_preference": "medium", "cooking_level": "intermediate",
                                  "restrictions": "vegetarian"})
    after = client.get("/plan").get_data(as_text=True)
    assert "Salmon with Roasted Vegetables" in before and "Salmon with Roasted" not in after


def test_pages_and_guards(client):
    assert client.get("/plan").status_code == 302           # no session yet
    assert client.get("/scenarios").status_code == 200
    assert client.get("/rules").get_data(as_text=True).count("<tr class=\"kind-") == len(db.get_rules(False))
    start(client, 101, CTX_A)
    assert client.get("/meal/999").status_code == 404
    assert client.get("/profile").status_code == 200
    assert client.post("/end").status_code == 302
    assert db.get_current_context(101) is None
