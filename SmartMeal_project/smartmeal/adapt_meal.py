# -*- coding: utf-8 -*-
"""
SmartMeal adaptation engine (evolution of the original adapt_quiz.py).

Rules are read from the SQLite `rules` table. Each rule has:
    condition   e.g.  "dietary_goal = muscle_gain AND available_time <= 15"
    adaptation  e.g.  "boost=high_protein:3;card_detail=compact"
    priority    higher = evaluated first and wins interface conflicts

CONDITION GRAMMAR
    condition := clause { (AND | OR) clause }        (AND binds tighter than OR)
    clause    := key operator value
    operator  := NOT CONTAINS | CONTAINS | >= | <= | != | = | > | <
    key       := profile key (dietary_goal, cooking_level, restrictions, ...)
               | context key (device_type, available_time, meal_budget, ...)
               | performance.<attribute>  (dynamic user model)
               | user.<key> / context.<key> (explicit namespace)
  * multi-character operators are matched before single-character ones, which
    fixes the original bug where "time_available<=10" was split on "=";
  * a key that does not exist makes the clause FALSE (the original failed open);
  * numbers are compared numerically, strings case-insensitively.

ADAPTATION ACTIONS (separated by ';')
    filter=<criterion>          hard constraint, all filters are combined (AND)
    boost=<criterion>:<w>       adds w to the score of matching meals (summed)
    penalize=<criterion>:<w>    subtracts w (summed)
    max_prep_time=<n|@key>      most restrictive (minimum) value wins
    <ui_setting>=<value>        merged with a per-setting policy (see UI_MERGE)
  '@key' takes the value from the user/context facts (e.g. @available_time).

Because every action type has its own combination policy, several applicable
rules are combined instead of the last one overwriting the others (the
original replaced `allowed_quizzes` with whatever the last matching rule said).
"""

import re

from backend.nutrition import MEAL_SHARE, NUTRIENT_LABELS, NUTRIENTS, REFERENCE_KCAL

# --------------------------------------------------------------------------
# Condition parser
# --------------------------------------------------------------------------
OPERATORS = ("NOT CONTAINS", "CONTAINS", ">=", "<=", "!=", "=", ">", "<")
_CLAUSE_RE = re.compile(
    r"^\s*([A-Za-z_][\w.]*)\s*(NOT\s+CONTAINS|CONTAINS|>=|<=|!=|=|>|<)\s*([^<>=!\s].*?)\s*$")
_OR_RE = re.compile(r"\s+OR\s+")
_AND_RE = re.compile(r"\s+AND\s+")


class RuleError(ValueError):
    """Raised when a rule stored in the database cannot be parsed."""


def parse_condition(condition):
    """Return a list of OR-groups, each a list of (key, operator, value) clauses."""
    if not condition or not condition.strip():
        raise RuleError("empty condition")
    groups = []
    for group in _OR_RE.split(condition.strip()):
        clauses = []
        for clause in _AND_RE.split(group):
            m = _CLAUSE_RE.match(clause)
            if not m:
                raise RuleError(f"cannot parse clause '{clause}'")
            key, op, value = m.group(1), re.sub(r"\s+", " ", m.group(2)), m.group(3)
            clauses.append((key, op, value.strip().strip("'\"")))
        groups.append(clauses)
    return groups


def build_facts(user, context):
    """Flatten the user model (static + dynamic) and the context into one dict."""
    facts = {}
    for key in ("id", "name", "dietary_goal", "budget_preference", "cooking_level",
                "food_preferences", "meal_types", "restrictions", "health_conditions",
                "allergies", "preferences", "age", "sex", "height_cm", "weight_kg",
                "body_fat_pct", "activity_level"):
        if user.get(key) is not None:          # optional body data left empty = unknown
            facts[key] = user[key]
    for key, value in (user.get("metrics") or {}).items():
        if value is not None and key != "method":
            facts[key] = value                  # bmi, bmr, daily_kcal_target, protein_target_g
    for key, value in (user.get("performance") or {}).items():
        facts["performance." + key] = value
    for key in ("device_type", "available_time", "meal_budget", "connection_quality",
                "meal_moment", "updates_count"):
        if context and key in context:
            facts[key] = context[key]
    return facts


def resolve(key, facts):
    """Return (found, value) for a key, accepting user./context. prefixes."""
    if key in facts:
        return True, facts[key]
    for prefix in ("user.", "context."):
        if key.startswith(prefix) and key[len(prefix):] in facts:
            return True, facts[key[len(prefix):]]
    return False, None


def _to_number(value):
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compare(actual, op, expected):
    if op in ("CONTAINS", "NOT CONTAINS"):
        if isinstance(actual, (list, tuple, set)):
            found = expected.lower() in {str(a).lower() for a in actual}
        elif actual is None:
            found = False
        else:
            found = expected.lower() in str(actual).lower()
        return found if op == "CONTAINS" else not found

    a, e = _to_number(actual), _to_number(expected)
    if op in (">=", "<=", ">", "<"):
        if a is None or e is None:
            return False                       # ordering only makes sense for numbers
        return {">=": a >= e, "<=": a <= e, ">": a > e, "<": a < e}[op]
    if a is not None and e is not None:
        equal = a == e
    else:
        equal = str(actual).strip().lower() == str(expected).strip().lower()
    return equal if op == "=" else not equal


def evaluate_condition(condition, user, context):
    """Same signature as the original function, now correct for every operator."""
    facts = build_facts(user, context)
    return _evaluate(parse_condition(condition), facts)


def _evaluate(groups, facts):
    for clauses in groups:                     # OR between groups
        ok = True
        for key, op, value in clauses:         # AND inside a group
            found, actual = resolve(key, facts)
            if not found or not compare(actual, op, value):
                ok = False
                break
        if ok:
            return True
    return False


# --------------------------------------------------------------------------
# Meal criteria used by filter / boost / penalize
# --------------------------------------------------------------------------
QUICK_MINUTES = 15

CRITERIA = {
    "high_protein": ("high in protein", lambda m, x: m["protein_level"] == "high"),
    "quick": (f"ready in ≤{QUICK_MINUTES} min", lambda m, x: m["prep_time"] <= QUICK_MINUTES),
    "affordable": ("low cost", lambda m, x: m["cost_category"] == "low"),
    "expensive": ("high cost", lambda m, x: m["cost_category"] == "high"),
    "vegetarian": ("vegetarian", lambda m, x: bool(m["vegetarian"])),
    "vegetables": ("vegetable-rich", lambda m, x: "veggie_rich" in m["dietary_tags"]),
    "balanced": ("balanced", lambda m, x: "balanced" in m["dietary_tags"]),
    "light": ("light", lambda m, x: "light" in m["dietary_tags"]),
    "easy": ("easy to make", lambda m, x: m["difficulty"] == "easy"),
    "hard": ("hard to make", lambda m, x: m["difficulty"] == "hard"),
    "challenging": ("challenging recipe", lambda m, x: m["difficulty"] in ("medium", "hard")),
    "saved": ("saved by you", lambda m, x: m["id"] in x["saved_ids"]),
    "favorite_category": ("your most-used category",
                          lambda m, x: m["category"] == x["facts"].get("performance.top_category")),
    "preferred_meal_type": ("preferred meal type",
                            lambda m, x: m["category"] in (x["facts"].get("meal_types") or [])),
}


def _personal(meal, x, key):
    """Personal per-meal target (None when the profile has no body data)."""
    daily = x["facts"].get(key)
    return daily * MEAL_SHARE[meal["category"]] if daily else None


def _kcal(meal):
    return meal["nutrition"]["calories_kcal"]


CRITERIA.update({
    "low_calorie": ("lower in calories",
                    lambda m, x: _kcal(m) <= 0.8 * REFERENCE_KCAL[m["category"]]),
    "high_calorie": ("energy-rich",
                     lambda m, x: _kcal(m) >= 0.9 * REFERENCE_KCAL[m["category"]]),
    "within_calorie_target": ("within your calorie target",
                              lambda m, x: _personal(m, x, "daily_kcal_target") is not None
                              and _kcal(m) <= 1.1 * _personal(m, x, "daily_kcal_target")),
    "reaches_calorie_target": ("reaches your calorie target",
                               lambda m, x: _personal(m, x, "daily_kcal_target") is not None
                               and _kcal(m) >= 0.85 * _personal(m, x, "daily_kcal_target")),
    "meets_protein_target": ("covers your protein target",
                             lambda m, x: _personal(m, x, "protein_target_g") is not None
                             and m["nutrition"]["protein_g"]
                             >= 0.8 * _personal(m, x, "protein_target_g")),
})


def criterion_label(criterion):
    if criterion.startswith("tag:"):
        return criterion[4:].replace("_", "-")
    if criterion.startswith("category:"):
        return criterion[9:]
    if criterion.startswith("no_allergen:"):
        return "no " + criterion[12:]
    if criterion.startswith(("max:", "min:")):
        bound, field, value = criterion.split(":")
        name, unit = NUTRIENT_LABELS[field]
        return f"{name.lower()} {'≤' if bound == 'max' else '≥'} {value} {unit}"
    return CRITERIA[criterion][0] if criterion in CRITERIA else criterion


def _check_criterion(criterion):
    if criterion in CRITERIA or criterion.startswith(("tag:", "category:", "no_allergen:")):
        return
    if criterion.startswith(("max:", "min:")):
        parts = criterion.split(":")
        if len(parts) == 3 and parts[1] in NUTRIENTS and _to_number(parts[2]) is not None:
            return
    raise RuleError(f"unknown meal criterion '{criterion}'")


def meal_matches(criterion, meal, extras):
    if criterion.startswith("tag:"):
        return criterion[4:] in meal["dietary_tags"]
    if criterion.startswith("category:"):
        return meal["category"] == criterion[9:]
    if criterion.startswith("no_allergen:"):
        return criterion[12:] not in meal.get("allergens", [])
    if criterion.startswith(("max:", "min:")):
        bound, field, value = criterion.split(":")
        amount = meal["nutrition"][field]
        return amount <= float(value) if bound == "max" else amount >= float(value)
    return CRITERIA[criterion][1](meal, extras)


# --------------------------------------------------------------------------
# Interface settings and their merge policies
# --------------------------------------------------------------------------
UI_DEFAULTS = {
    "layout": "grid",            # grid | two_column | single_column
    "cards_per_page": 9,
    "card_detail": "detailed",   # detailed | compact
    "media": "full",             # full | reduced
    "show_images": True,
    "show_tips": False,
    "nav": "top",                # top | bottom
    "text_size": "normal",       # normal | large
}
UI_MERGE = {
    "layout": "priority",        # highest-priority rule wins (conflict is reported)
    "card_detail": "priority",
    "nav": "priority",
    "text_size": "priority",
    "cards_per_page": "min",     # the most restrictive rule wins
    "media": "min_rank",         # 'reduced' beats 'full'
    "show_images": "all",        # images only if no rule disables them
    "show_tips": "any",          # tips if at least one rule asks for them
}
UI_ALLOWED = {
    "layout": {"grid", "two_column", "single_column"},
    "card_detail": {"detailed", "compact"},
    "media": {"full", "reduced"},
    "nav": {"top", "bottom"},
    "text_size": {"normal", "large"},
}
MEDIA_RANK = ["reduced", "full"]


def _convert_ui(key, value):
    if key not in UI_DEFAULTS:
        raise RuleError(f"unknown adaptation key '{key}'")
    default = UI_DEFAULTS[key]
    if isinstance(default, bool):
        if value.lower() not in ("true", "false"):
            raise RuleError(f"{key} expects true/false")
        return value.lower() == "true"
    if isinstance(default, int):
        try:
            return int(value)
        except ValueError:
            raise RuleError(f"{key} expects an integer")
    if value not in UI_ALLOWED[key]:
        raise RuleError(f"invalid value '{value}' for {key}")
    return value


# --------------------------------------------------------------------------
# Rule compilation
# --------------------------------------------------------------------------
def parse_adaptation(adaptation):
    """'a=1;b=x:2' -> [('a','1'), ('b','x:2')] with validation."""
    actions = []
    for part in (adaptation or "").split(";"):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise RuleError(f"action '{part}' has no '='")
        key, value = (s.strip() for s in part.split("=", 1))
        if key in ("boost", "penalize"):
            criterion, _, weight = value.rpartition(":")
            if not criterion or _to_number(weight) is None:
                raise RuleError(f"{key} expects criterion:weight, got '{value}'")
            _check_criterion(criterion)
            actions.append((key, (criterion, float(weight))))
        elif key == "filter":
            if not value.startswith("category:@"):
                _check_criterion(value)
            actions.append((key, value))
        elif key == "max_prep_time":
            if not value.startswith("@") and _to_number(value) is None:
                raise RuleError("max_prep_time expects a number or @key")
            actions.append((key, value))
        else:
            actions.append((key, _convert_ui(key, value)))
    if not actions:
        raise RuleError("empty adaptation")
    return actions


def compile_rule(rule):
    return {
        "rule": rule,
        "groups": parse_condition(rule["condition"]),
        "actions": parse_adaptation(rule["adaptation"]),
    }


def _deref(value, facts):
    if isinstance(value, str) and "@" in value:
        prefix, _, key = value.partition("@")
        found, v = resolve(key, facts)
        return (prefix + str(v)) if found else None
    return value


# --------------------------------------------------------------------------
# Engine
# --------------------------------------------------------------------------
def adapt_meal_plan(user, context, meals, rules, saved_ids=()):
    """
    Evaluate every rule against user + context and produce:
      ui            final interface settings
      ranked        recommended meals (score, reasons, breakdown), best first
      excluded      meals removed by a constraint, with the reason
      fired / not_fired / errors / conflicts   for transparency in the UI
    """
    facts = build_facts(user, context)
    extras = {"facts": facts, "saved_ids": set(saved_ids)}
    res = {"facts": facts, "fired": [], "not_fired": [], "errors": [], "conflicts": [],
           "filters": [], "boosts": [], "max_prep_time": None, "max_prep_rule": None,
           "ui": dict(UI_DEFAULTS), "ui_sources": {}}
    claims = {}

    ordered = sorted(rules, key=lambda r: (-int(r.get("priority", 50)), r.get("rule_id", 0)))
    for rule in ordered:
        try:
            compiled = compile_rule(rule)
        except RuleError as exc:
            res["errors"].append({"rule": rule, "error": str(exc)})
            continue
        if not _evaluate(compiled["groups"], facts):
            res["not_fired"].append(rule)
            continue
        res["fired"].append(rule)
        for key, value in compiled["actions"]:
            if key in ("boost", "penalize"):
                criterion, weight = value
                res["boosts"].append({"criterion": criterion,
                                      "weight": weight if key == "boost" else -weight,
                                      "rule": rule})
            elif key == "filter":
                crit = _deref(value, facts)
                if crit:
                    res["filters"].append({"criterion": crit, "rule": rule})
            elif key == "max_prep_time":
                v = _to_number(_deref(value, facts))
                if v is not None and (res["max_prep_time"] is None or v < res["max_prep_time"]):
                    res["max_prep_time"], res["max_prep_rule"] = int(v), rule
            else:
                claims.setdefault(key, []).append((rule, value))

    # merge interface settings, one policy per key
    for key, items in claims.items():
        policy = UI_MERGE[key]
        if policy == "priority":
            winner_rule, winner = items[0]                     # rules are priority-sorted
            losers = [(r, v) for r, v in items[1:] if v != winner]
            if losers:
                res["conflicts"].append({
                    "setting": key, "value": winner, "winner": winner_rule["name"],
                    "overridden": [f"{r['name']} ({v})" for r, v in losers]})
            res["ui"][key], res["ui_sources"][key] = winner, [winner_rule["name"]]
        else:
            values = [v for _, v in items]
            if policy == "min":
                final = min(values)
            elif policy == "min_rank":
                final = min(values, key=MEDIA_RANK.index)
            elif policy == "all":
                final = all(values)
            else:  # any
                final = any(values)
            res["ui"][key] = final
            res["ui_sources"][key] = [r["name"] for r, v in items if v == final]

    # filter and score meals
    candidates, excluded = [], []
    for meal in meals:
        failed = next((f for f in res["filters"]
                       if not meal_matches(f["criterion"], meal, extras)), None)
        if failed:
            excluded.append({"meal": meal, "reason": failed["rule"]["explanation"],
                             "rule": failed["rule"]["name"]})
            continue
        score, reasons, breakdown = 0.0, [], []
        for b in res["boosts"]:
            if meal_matches(b["criterion"], meal, extras):
                score += b["weight"]
                breakdown.append({"rule": b["rule"]["name"], "weight": b["weight"],
                                  "criterion": criterion_label(b["criterion"]),
                                  "criterion_key": b["criterion"]})
                text = b["rule"]["explanation"]
                if b["weight"] > 0 and text not in [t for t, _, _ in reasons]:
                    reasons.append((text, b["weight"], b["rule"]["name"]))
        # strongest reasons first (stable for equal weights: rule priority order)
        reasons.sort(key=lambda r: -r[1])
        reason_rules = [n for _, _, n in reasons]          # rule names, used for translation
        reasons = [t for t, _, _ in reasons]
        # constraints the meal satisfies, shown as "fits your settings" on the card
        check_rules = list(dict.fromkeys(
            f["rule"]["name"] for f in res["filters"]
            if f["rule"]["name"].startswith(("health_", "allergy_", "restriction_"))))
        checks = [next(f["rule"]["explanation"] for f in res["filters"] if f["rule"]["name"] == n)
                  for n in check_rules]
        candidates.append({"meal": meal, "score": score, "reasons": reasons,
                           "reason_rules": reason_rules, "breakdown": breakdown,
                           "checks": checks, "check_rules": check_rules})

    limit = res["max_prep_time"]
    fitting = [c for c in candidates if limit is None or c["meal"]["prep_time"] <= limit]
    res["relaxed_time"] = False
    if not fitting and candidates:
        # nothing fits in the available time: show the quickest options, clearly flagged
        res["relaxed_time"] = True
        fitting = sorted(candidates, key=lambda c: c["meal"]["prep_time"])[:4]
    for c in candidates:
        if c not in fitting:
            excluded.append({"meal": c["meal"], "rule": "fit_available_time",
                             "reason": f"Takes {c['meal']['prep_time']} min, more than your "
                                       f"{limit} min available"})

    ranked = sorted(fitting, key=lambda c: (-c["score"], c["meal"]["prep_time"],
                                            c["meal"]["name"]))
    for i, c in enumerate(ranked):
        c["rank"] = i + 1
        c["top_pick"] = i < 3 and c["score"] > 0
        c["explanation"] = explain(c, context, limit)
    res["ranked"] = ranked
    res["excluded"] = excluded
    return res


def explain(item, context, limit):
    """Human-readable 'why' sentence shown on each meal card."""
    reasons = list(item["reasons"])[:2]          # the two strongest reasons
    if limit is not None and item["meal"]["prep_time"] <= limit and context:
        fit = f"it fits your {context['available_time']}-minute window " \
              f"({item['meal']['prep_time']} min)"
    else:
        fit = None
    if not reasons:
        return ("Suggested because " + fit + ".") if fit else "Suggested to complete your plan."
    text = "Recommended because it is " if not reasons[0].startswith("you ") \
        else "Recommended because "
    if len(reasons) == 1:
        text += reasons[0]
    else:
        text += reasons[0] + "; and " + (reasons[1] if reasons[1].startswith("you ")
                                         else "it is " + reasons[1])
    return text + "."


def adapt_meal(user, context):
    """Convenience wrapper reading meals, rules and saved meals from SQLite."""
    from backend.db import get_all_meals, get_rules, get_saved_meal_ids
    return adapt_meal_plan(user, context, get_all_meals(), get_rules(),
                           get_saved_meal_ids(user["id"]))


# --------------------------------------------------------------------------
# Console demo: python adapt_meal.py
# --------------------------------------------------------------------------
if __name__ == "__main__":
    from backend.db import get_user
    from backend.init_db import init_databases

    init_databases()
    scenarios = [
        ("A", 101, {"device_type": "desktop", "available_time": 30, "meal_budget": "medium",
                    "connection_quality": "fast", "meal_moment": "any"}),
        ("B", 102, {"device_type": "mobile", "available_time": 10, "meal_budget": "low",
                    "connection_quality": "slow", "meal_moment": "any"}),
        ("C", 101, {"device_type": "mobile", "available_time": 10, "meal_budget": "medium",
                    "connection_quality": "normal", "meal_moment": "any"}),
    ]
    for label, uid, ctx in scenarios:
        user = get_user(uid)
        r = adapt_meal(user, ctx)
        print(f"\n=== Scenario {label}: {user['name']} ({user['dietary_goal']}) | {ctx}")
        print("Fired rules :", ", ".join(x["name"] for x in r["fired"]))
        print("Interface   :", r["ui"])
        for c in r["ranked"][:5]:
            m = c["meal"]
            print(f"  {c['rank']}. {m['name']:<34} score={c['score']:>4.0f} "
                  f"{m['prep_time']:>3} min  protein={m['protein_level']:<6} cost={m['cost_category']}")
