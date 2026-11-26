# -*- coding: utf-8 -*-
"""
SmartMeal – Adaptive Meal Planner (Flask entry point).

Route mapping with the original adaptive_quiz_system/app.py:
    /                      index      -> choose user + context (now stored in the Context table)
    /quiz/<user_id>        show_quiz  -> /plan        adapted meal plan
    /quiz/<id>/<file>      play_quiz  -> /meal/<id>   meal details
New: /context, /meal/<id>/select, /meal/<id>/save, /profile, /profile/new,
     /dashboard, /scenarios, /rules, /end, /api/heartbeat
"""

import math
import os
import sqlite3
from functools import wraps

from flask import (Flask, abort, flash, g, redirect, render_template, request, session,
                   url_for)
from markupsafe import Markup, escape

import i18n

from adapt_meal import UI_DEFAULTS, adapt_meal, criterion_label
from backend import db
from backend.init_db import init_databases
from backend.nutrition import MEAL_SHARE, NUTRIENT_LABELS, NUTRIENTS

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
PHOTO_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")


def meal_image(meal):
    """Static path of a meal picture: a real photo dropped into
    static/images/meals/photos/meal_<id>.<jpg|jpeg|png|webp> wins over the SVG illustration."""
    for ext in PHOTO_EXTENSIONS:
        rel = f"images/meals/photos/meal_{meal['id']:02d}{ext}"
        if os.path.exists(os.path.join(STATIC_DIR, rel)):
            return rel
    return "images/" + meal["image"]

SCENARIOS = [
    {"key": "A", "title": "Scenario A: muscle gain at the desk", "user_id": 101,
     "context": {"device_type": "desktop", "available_time": 30, "meal_budget": "medium",
                 "connection_quality": "fast", "meal_moment": "any"},
     "expected": "High-protein meals, desktop grid"},
    {"key": "B", "title": "Scenario B: healthy eating on the go", "user_id": 102,
     "context": {"device_type": "mobile", "available_time": 10, "meal_budget": "low",
                 "connection_quality": "slow", "meal_moment": "any"},
     "expected": "Quick, affordable meals, mobile layout, reduced media"},
    {"key": "C", "title": "Scenario C: same user as A, new context", "user_id": 101,
     "context": {"device_type": "mobile", "available_time": 10, "meal_budget": "medium",
                 "connection_quality": "normal", "meal_moment": "any"},
     "expected": "Different (quick) meals and a mobile interface"},
]



def create_app(data_dir=None, testing=False):
    if data_dir:
        db.set_data_dir(data_dir)
    init_databases()          # safe: creates missing tables, never drops data

    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SMARTMEAL_SECRET_KEY", "smartmeal-local-dev-key")
    app.config["TESTING"] = testing

    # ------------------------------------------------------------ languages
    def lang():
        return g.get("lang", i18n.DEFAULT)

    def _(text, **values):
        return i18n.gettext(text, lang(), **values)

    def avatar_img(user, size=34):
        """<img> of the chosen avatar, or a coloured initial when none is chosen."""
        key = (user or {}).get("avatar")
        if key in db.AVATARS:
            src = url_for("static", filename=f"images/avatars/{key}.svg")
            return Markup(f'<img class="avatar-img" src="{src}" alt="" width="{size}" height="{size}">')
        letter = escape(((user or {}).get("name") or "?")[:1])
        return Markup(f'<span class="avatar" style="width:{size}px;height:{size}px;'
                      f'font-size:{size * .45:.0f}px">{letter}</span>')

    app.jinja_env.globals.update(
        _=_, avatar_img=avatar_img, languages=i18n.LANGUAGES,
        avatar_labels=i18n.AVATAR_LABELS,
        meal_name=lambda m: i18n.meal_name(m, lang()),
        meal_desc=lambda m: i18n.meal_desc(m, lang()),
        meal_name_by_id=lambda mid, en: i18n.meal_name_by_id(mid, en, lang()),
        ingredient=lambda name: i18n.ingredient(name, lang()),
        rule_text=lambda name, en=None: i18n.rule_text(name, en or name, lang()),
        crit=lambda key, en: i18n.criterion(key, en, lang()),
        why=lambda item: i18n.explain(item, g.get("ctx"), lang()),
        money=lambda eur: i18n.money(eur, lang()))
    app.jinja_env.filters["label"] = lambda v: i18n.label(v, lang())
    app.jinja_env.filters["rule_text"] = lambda name: i18n.rule_text(name, name, lang())
    app.jinja_env.filters["capitalize_first"] = lambda t: (t[:1].upper() + t[1:]) if t else t

    @app.context_processor
    def inject_globals():
        return {"current_user": g.get("user"), "current_ctx": g.get("ctx"),
                "lang": lang(), "text_dir": "rtl" if lang() in i18n.RTL else "ltr",
                "ui": g.get("ui", UI_DEFAULTS), "choices": {
                    "avatars": db.AVATARS,
                    "goals": db.DIETARY_GOALS, "budgets": db.BUDGETS,
                    "levels": db.COOKING_LEVELS, "devices": db.DEVICES,
                    "connections": db.CONNECTIONS, "moments": db.MEAL_MOMENTS,
                    "foods": db.FOOD_PREFERENCES, "restrictions": db.RESTRICTIONS,
                    "categories": db.CATEGORIES, "health": db.HEALTH_CONDITIONS,
                    "allergens": db.ALLERGENS, "sexes": db.SEXES,
                    "activities": db.ACTIVITY_LEVELS}}

    @app.before_request
    def load_session():
        g.lang = session.get("lang") or request.accept_languages.best_match(
            list(i18n.LANGUAGES)) or i18n.DEFAULT
        g.user, g.ctx = None, None
        uid, cid = session.get("user_id"), session.get("context_id")
        if uid:
            g.user = db.get_user(uid)
        if g.user and cid:
            ctx = db.get_context(cid)
            if ctx and ctx["is_active"] and ctx["user_id"] == g.user["id"]:
                g.ctx = ctx
                db.touch_session(cid)
                g.ui = adapt_meal(g.user, ctx)["ui"]     # e.g. large text on every page
        if g.user is None:
            session.pop("user_id", None)
            session.pop("context_id", None)

    def session_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not g.user or not g.ctx:
                flash(_("Choose a profile and your current context to start."), "info")
                return redirect(url_for("index"))
            return view(*args, **kwargs)
        return wrapped

    def load_meal_or_404(meal_id):
        meal = db.get_meal(meal_id)
        if not meal:
            abort(404)
        return meal

    def back(default="plan"):
        target = request.form.get("next") or ""
        return redirect(target if target.startswith("/") and not target.startswith("//")
                        else url_for(default))

    # ------------------------------------------------------------------ index
    @app.route("/", methods=["GET", "POST"])
    def index():
        users = db.get_all_users()
        if request.method == "POST":
            try:
                user_id = int(request.form["user_id"])
            except (KeyError, ValueError):
                flash(_("Please choose a profile."), "error")
                return redirect(url_for("index"))
            if not db.get_user(user_id):
                abort(404)
            ctx = db.start_session(user_id, request.form)
            session["user_id"], session["context_id"] = user_id, ctx["id"]
            return redirect(url_for("plan"))
        selected = request.args.get("user_id", type=int) or (g.user["id"] if g.user else None)
        last_ctx = g.ctx or (db.get_current_context(selected) if selected else None)
        return render_template("index.html", users=users, selected=selected,
                               defaults=db.clean_context(last_ctx or {}), fresh=last_ctx is None)

    # ------------------------------------------------------------------ plan
    @app.route("/plan")
    @session_required
    def plan():
        result = adapt_meal(g.user, g.ctx)
        g.ui = result["ui"]
        per_page = max(1, result["ui"]["cards_per_page"])
        ranked = result["ranked"]
        pages = max(1, math.ceil(len(ranked) / per_page))
        page = min(max(1, request.args.get("page", 1, type=int)), pages)
        shown = ranked[(page - 1) * per_page: page * per_page]
        db.log_recommendations(g.user["id"], shown, g.ctx)
        return render_template("meal_plan.html", result=result, meals=shown, page=page,
                               pages=pages, total=len(ranked),
                               saved_ids=db.get_saved_meal_ids(g.user["id"]))

    @app.route("/context", methods=["POST"])
    @session_required
    def update_context():
        db.update_context(g.ctx["id"], request.form)
        flash(_("Context updated. Your plan has been re-adapted."), "success")
        return back()

    # ------------------------------------------------------------------ meals
    @app.route("/meal/<int:meal_id>")
    @session_required
    def meal_details(meal_id):
        meal = load_meal_or_404(meal_id)
        src = "recommendation" if request.args.get("src") == "rec" else "direct"
        db.log_interaction(g.user["id"], meal, "viewed", g.ctx, src)
        result = adapt_meal(g.user, g.ctx)
        g.ui = result["ui"]
        item = next((c for c in result["ranked"] if c["meal"]["id"] == meal_id), None)
        excluded = next((e for e in result["excluded"] if e["meal"]["id"] == meal_id), None)
        return render_template("meal_details.html", meal=meal, item=item, excluded=excluded,
                               result=result, saved=meal_id in db.get_saved_meal_ids(g.user["id"]),
                               src=request.args.get("src", ""))

    @app.route("/meal/<int:meal_id>/select", methods=["POST"])
    @session_required
    def select_meal(meal_id):
        meal = load_meal_or_404(meal_id)
        src = request.form.get("src", "direct")
        db.log_interaction(g.user["id"], meal, "selected", g.ctx,
                           "recommendation" if src == "rec" else src)
        flash(_("“{meal}” added to your meal plan.", meal=i18n.meal_name(meal, lang())), "success")
        return back()

    @app.route("/meal/<int:meal_id>/save", methods=["POST"])
    @session_required
    def save_meal(meal_id):
        meal = load_meal_or_404(meal_id)
        src = request.form.get("src", "direct")
        now_saved = db.toggle_saved(g.user["id"], meal, g.ctx,
                                    "recommendation" if src == "rec" else src)
        msg = "“{meal}” saved." if now_saved else "“{meal}” removed from saved meals."
        flash(_(msg, meal=i18n.meal_name(meal, lang())), "success")
        return back()

    # ------------------------------------------------------------------ profile
    def _profile_from_form(user_id):
        f = request.form
        body = {k: f.get(k) for k in ("age", "sex", "height_cm", "weight_kg", "body_fat_pct",
                                      "activity_level")}
        return db.save_user_profile(
            user_id, f.get("name"), f.get("dietary_goal"), f.get("budget_preference"),
            f.get("cooking_level"), f.getlist("food_preferences"), f.getlist("meal_types"),
            f.getlist("restrictions"), f.getlist("health_conditions"), f.getlist("allergies"),
            body, f.get("avatar") or None)

    @app.route("/profile", methods=["GET", "POST"])
    def profile():
        if not g.user:
            return redirect(url_for("index"))
        if request.method == "POST":
            try:
                _profile_from_form(g.user["id"])
                flash(_("Profile updated. Recommendations now use your new profile."), "success")
            except (ValueError, sqlite3.IntegrityError) as exc:
                flash(_("Could not save profile: {error}", error=exc), "error")
            return redirect(url_for("profile"))
        return render_template("profile.html", user=g.user, is_new=False)

    @app.route("/profile/new", methods=["GET", "POST"])
    def new_profile():
        if request.method == "POST":
            try:
                uid = _profile_from_form(None)
            except (ValueError, sqlite3.IntegrityError) as exc:
                flash(_("Could not create profile: {error}", error=exc), "error")
                return redirect(url_for("new_profile"))
            flash(_("Profile created. Now tell us about your current context."), "success")
            return redirect(url_for("index", user_id=uid))
        blank = {"name": "", "dietary_goal": "healthy_eating", "budget_preference": "medium",
                 "cooking_level": "beginner", "food_preferences": [], "meal_types": [],
                 "restrictions": [], "health_conditions": [], "allergies": [],
                 "activity_level": "moderate", "performance": {}, "metrics": {}, "avatar": None}
        return render_template("profile.html", user=blank, is_new=True)

    # ------------------------------------------------------------------ dashboard
    @app.route("/dashboard")
    def dashboard():
        uid = request.args.get("user_id", type=int) or (g.user["id"] if g.user else None)
        user = db.get_user(uid) if uid else None
        if not user:
            return redirect(url_for("index"))
        if g.ctx:
            g.ui = adapt_meal(g.user, g.ctx)["ui"]
        return render_template(
            "dashboard.html", user=user, users=db.get_all_users(),
            viewed_cats=db.category_counts(uid, "viewed"),
            selected_cats=db.category_counts(uid, "selected"),
            top_selected=db.top_meals(uid, "selected"), top_viewed=db.top_meals(uid, "viewed"),
            activity=db.daily_activity(uid, 14),
            recommendations=db.recent_history(uid, ["recommended"], 12),
            interactions=db.recent_history(uid, ["viewed", "selected", "saved", "unsaved"], 12),
            sessions=db.session_history(uid, 8))

    # ------------------------------------------------------------------ evaluation
    @app.route("/scenarios")
    def scenarios():
        """Run the engine on the test scenarios side by side (nothing is logged)."""
        rows = []
        for sc in SCENARIOS:
            user = db.get_user(sc["user_id"])
            ctx = db.clean_context(sc["context"])
            rows.append({"sc": sc, "user": user, "ctx": ctx, "result": adapt_meal(user, ctx)})
        return render_template("scenarios.html", rows=rows)

    @app.route("/rules")
    def rules():
        return render_template("rules.html", rules=db.get_rules(active_only=False))

    # ------------------------------------------------------------------ session
    @app.route("/end", methods=["POST"])
    def end_session():
        if g.ctx:
            db.close_session(g.ctx["id"])
        session.clear()
        flash(_("Session ended. Your profile statistics were updated."), "success")
        return redirect(url_for("index"))

    @app.route("/lang/<code>")
    def set_language(code):
        if code in i18n.LANGUAGES:
            session["lang"] = code
        target = request.args.get("next") or ""
        return redirect(target if target.startswith("/") and not target.startswith("//")
                        else url_for("index"))

    @app.route("/api/heartbeat", methods=["POST"])
    def heartbeat():
        return ("", 204)          # before_request already refreshed last_seen_at

    # globals are also visible inside imported macros (_meal_card.html)
    app.jinja_env.globals.update(criterion_label=criterion_label, meal_image=meal_image,
                                 nutrient_labels=NUTRIENT_LABELS, nutrients=NUTRIENTS,
                                 meal_share=MEAL_SHARE)
    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
