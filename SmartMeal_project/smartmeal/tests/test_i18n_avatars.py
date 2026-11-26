# -*- coding: utf-8 -*-
"""Version 3: three languages (EN / FR / AR with right-to-left), avatars, clickable cards."""
import glob
import os
import re
import sqlite3
import string

import pytest

import i18n
from backend import db
from backend.init_db import RULES, init_databases
from conftest import CTX_A

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def template_msgids():
    ids = set()
    for path in glob.glob(os.path.join(ROOT, "templates", "*.html")):
        text = open(path, encoding="utf-8").read()
        ids |= {m.group(2) for m in re.finditer(r"""_\(\s*(['"])(.*?)(?<!\\)\1""", text)}
    return ids


def app_msgids():
    text = open(os.path.join(ROOT, "app.py"), encoding="utf-8").read()
    ids = {m.group(1) for m in re.finditer(r'_\("((?:[^"\\]|\\.)*)"', text)}
    for m in re.finditer(r'msg = "(.*?)" if now_saved else "(.*?)"', text):
        ids |= {m.group(1), m.group(2)}
    from app import SCENARIOS
    for sc in SCENARIOS:
        ids |= {sc["title"], sc["expected"]}
    return ids


def placeholders(s):
    return {f for _, f, _, _ in string.Formatter().parse(s) if f}


# ------------------------------------------------------------------ coverage
def test_every_interface_string_is_translated():
    missing = sorted((template_msgids() | app_msgids()) - set(i18n.UI))
    assert not missing, f"untranslated: {missing}"


def test_translations_keep_the_same_placeholders():
    for en, (fr, ar) in i18n.UI.items():
        assert placeholders(fr) == placeholders(en), en
        assert placeholders(ar) == placeholders(en), en


def test_labels_avatars_nutrients_and_methods_are_translated():
    from backend.nutrition import NUTRIENT_LABELS
    needed = set(i18n.LABELS.values()) | set(i18n.AVATAR_LABELS.values())
    needed |= {name for name, _ in NUTRIENT_LABELS.values()} | {u for _, u in NUTRIENT_LABELS.values()}
    needed |= {"Katch-McArdle (uses body fat)", "Mifflin-St Jeor",
               "Mifflin-St Jeor (sex not given: average)"}
    assert not needed - set(i18n.UI)
    for enum in (db.DIETARY_GOALS + db.BUDGETS + db.COOKING_LEVELS + db.DEVICES + db.CONNECTIONS
                 + db.MEAL_MOMENTS + db.FOOD_PREFERENCES + db.RESTRICTIONS + db.HEALTH_CONDITIONS
                 + db.ALLERGENS + db.SEXES + db.INTERACTIONS):
        assert enum in i18n.LABELS, enum


def test_content_is_translated(fresh_db):
    rule_names = {r[0] for r in RULES}
    assert rule_names == set(i18n.content.RULES)
    for meal in db.get_all_meals():
        assert meal["id"] in i18n.content.MEALS
        for ing in meal["ingredients"]:
            assert ing in i18n.content.INGREDIENTS, ing
    assert set(db.AVATARS) == set(i18n.AVATAR_LABELS)


def test_arabic_and_french_explanations(fresh_db):
    from adapt_meal import adapt_meal
    item = adapt_meal(db.get_user(101), CTX_A)["ranked"][0]
    ar, fr = i18n.explain(item, CTX_A, "ar"), i18n.explain(item, CTX_A, "fr")
    assert ar.startswith("مقترحة لأنها") and fr.startswith("Recommandé :")
    assert i18n.explain(item, CTX_A, "en") == item["explanation"]
    assert i18n.criterion("max:salt_g:1.5", "x", "fr") == "Sel ≤ 1.5 g"
    assert i18n.money(3.5, "fr") == "3,50 €" and i18n.money(3.5, "en") == "€3.50"


# ------------------------------------------------------------------ UI in each language
def start(client, user_id=101, ctx=CTX_A):
    return client.post("/", data={"user_id": user_id, **ctx}, follow_redirects=True)


@pytest.mark.parametrize("code, direction, text", [
    ("en", "ltr", "Build my meal plan"),
    ("fr", "ltr", "Créer mon plan de repas"),
    ("ar", "rtl", "أنشئ خطة وجباتي"),
])
def test_language_switch_changes_text_and_direction(client, code, direction, text):
    html = client.get(f"/lang/{code}?next=/", follow_redirects=True).get_data(as_text=True)
    assert f'lang="{code}" dir="{direction}"' in html
    assert text in html


def test_plan_and_meal_page_in_arabic(client):
    client.get("/lang/ar")
    start(client)
    plan = client.get("/plan").get_data(as_text=True)
    assert "سلمون مع خضار مشوية" in plan and "مقترحة لأنها" in plan
    page = client.get("/meal/15").get_data(as_text=True)
    assert "القيم الغذائية للحصة" in page and "فيليه سلمون" in page


def test_browser_language_is_used_by_default(client):
    html = client.get("/", headers={"Accept-Language": "fr-FR,fr;q=0.9"}).get_data(as_text=True)
    assert 'lang="fr"' in html


def test_unknown_language_is_ignored(client):
    client.get("/lang/xx")
    assert 'lang="en"' in client.get("/").get_data(as_text=True)


# ------------------------------------------------------------------ avatars
def test_avatar_files_exist():
    for key in db.AVATARS:
        assert os.path.exists(os.path.join(ROOT, "static", "images", "avatars", key + ".svg"))
    assert os.path.exists(os.path.join(ROOT, "static", "images", "logo.svg"))


def test_avatar_is_saved_validated_and_shown(client):
    start(client, 102)
    client.post("/profile", data={"name": "Bob", "dietary_goal": "healthy_eating",
                                  "budget_preference": "low", "cooking_level": "beginner",
                                  "avatar": "avatar_11"})
    assert db.get_user(102)["avatar"] == "avatar_11"
    assert "avatars/avatar_11.svg" in client.get("/").get_data(as_text=True)
    client.post("/profile", data={"name": "Bob", "dietary_goal": "healthy_eating",
                                  "budget_preference": "low", "cooking_level": "beginner",
                                  "avatar": "../../secret"})
    assert db.get_user(102)["avatar"] is None                      # invalid value ignored
    page = client.get("/profile").get_data(as_text=True)
    assert page.count('name="avatar"') == len(db.AVATARS) + 1       # 20 avatars + initial


def test_v2_database_gets_avatar_column(tmp_path):
    db.set_data_dir(str(tmp_path))
    init_databases()
    con = sqlite3.connect(db.users_db())
    con.execute("ALTER TABLE users DROP COLUMN avatar")             # simulate a v2 database
    con.execute("PRAGMA user_version = 2"); con.commit(); con.close()
    init_databases()
    assert db.get_user(101)["avatar"] is None
    db.save_user_profile(101, "Alice", "muscle_gain", "medium", "intermediate", avatar="avatar_02")
    assert db.get_user(101)["avatar"] == "avatar_02"
    assert len(db.get_rules(False)) == len(RULES)                   # rules not replaced again


# ------------------------------------------------------------------ clickable cards
def test_whole_meal_card_is_clickable(client):
    start(client)
    html = client.get("/plan").get_data(as_text=True)
    assert html.count("meal-card") and html.count('class="card-link"') == html.count("is-clickable")
    assert 'class="meal-actions"' in html                           # buttons still present
