# -*- coding: utf-8 -*-
"""
Body metrics and per-meal nutrition targets derived from the OPTIONAL body data
of the user profile (age, sex, height, weight, body fat, activity level).

These are standard textbook estimates used only to rank meal ideas. They are
not medical or dietetic advice; the interface says so wherever they appear.

    BMR (body fat known)   Katch-McArdle : 370 + 21.6 x lean mass (kg)
    BMR (otherwise)        Mifflin-St Jeor: 10 W + 6.25 H - 5 A + s
                           s = +5 (male), -161 (female), -78 (not given: average)
    Daily energy           BMR x activity factor x goal factor (floor 1200 kcal)
    Daily protein          g/kg of body weight, depending on the goal; above a BMI of
                           25 the weight at BMI 25 is used (reference weight)
    Per meal               daily value x share of the meal category
"""

ACTIVITY_FACTOR = {"low": 1.2, "moderate": 1.55, "high": 1.725}
GOAL_ENERGY_FACTOR = {"weight_loss": 0.80, "weight_gain": 1.15, "muscle_gain": 1.10,
                      "healthy_eating": 1.00}
PROTEIN_PER_KG = {"weight_loss": 1.6, "weight_gain": 1.4, "muscle_gain": 1.8,
                  "healthy_eating": 1.0}
MEAL_SHARE = {"breakfast": 0.25, "lunch": 0.35, "dinner": 0.30, "snack": 0.10}
# Generic per-meal energy reference (kcal) used when no personal target exists
REFERENCE_KCAL = {"breakfast": 450, "lunch": 600, "dinner": 600, "snack": 250}
MIN_DAILY_KCAL = 1200

NUTRIENTS = ["calories_kcal", "protein_g", "carbs_g", "sugar_g", "fat_g", "sat_fat_g",
             "fiber_g", "salt_g", "cholesterol_mg"]
NUTRIENT_LABELS = {
    "calories_kcal": ("Energy", "kcal"), "protein_g": ("Protein", "g"),
    "carbs_g": ("Carbohydrates", "g"), "sugar_g": ("of which sugars", "g"),
    "fat_g": ("Fat", "g"), "sat_fat_g": ("of which saturated", "g"),
    "fiber_g": ("Fibre", "g"), "salt_g": ("Salt", "g"), "cholesterol_mg": ("Cholesterol", "mg"),
}


def body_metrics(user):
    """Return the derived metrics that can be computed from the data available."""
    age, sex = user.get("age"), user.get("sex")
    h, w, bf = user.get("height_cm"), user.get("weight_kg"), user.get("body_fat_pct")
    goal = user.get("dietary_goal", "healthy_eating")
    activity = user.get("activity_level") or "moderate"
    out = {"bmi": None, "bmr": None, "method": None, "daily_kcal_target": None,
           "protein_target_g": None}
    if h and w:
        out["bmi"] = round(w / (h / 100) ** 2, 1)
    if w and bf:
        out["bmr"] = 370 + 21.6 * w * (1 - bf / 100)
        out["method"] = "Katch-McArdle (uses body fat)"
    elif w and h and age:
        s = {"male": 5, "female": -161}.get(sex, -78)
        out["bmr"] = 10 * w + 6.25 * h - 5 * age + s
        out["method"] = "Mifflin-St Jeor" + ("" if sex else " (sex not given: average)")
    if out["bmr"]:
        daily = out["bmr"] * ACTIVITY_FACTOR.get(activity, 1.55) * GOAL_ENERGY_FACTOR.get(goal, 1.0)
        out["bmr"] = round(out["bmr"])
        out["daily_kcal_target"] = int(round(max(MIN_DAILY_KCAL, daily) / 10.0) * 10)
    if w:
        ref_w = min(w, 25 * (h / 100) ** 2) if h else w
        out["protein_target_g"] = int(round(ref_w * PROTEIN_PER_KG.get(goal, 1.0)))
    return out


def meal_target(value, category):
    """Share of a daily value for one meal category."""
    return value * MEAL_SHARE[category] if value else None
