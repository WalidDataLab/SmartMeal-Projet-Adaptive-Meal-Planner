# Report guide

An outline for the final report, following the subjects the professor asked for. Each section says
what to write and where the material is in the code. Only what is listed under *Implemented* exists
in the code. Section 10 lists ideas that were **not** implemented.

## 1. Introduction and objectives
* Domain: *Personalized Nutrition Advisor* (one of the domains suggested in the PDF), named SmartMeal.
* Target users: people who want to eat healthily, with different goals (muscle gain, healthy eating,
  weight management), budgets, cooking skills, restrictions and very different amounts of time.
* Objective: show that the **same user** gets different recommendations **and** a different interface
  when the context changes, using an enriched profile, a Context table and rules stored in SQLite.

## 2. From the quiz system to SmartMeal
* Use the mapping table in README §3 and the list of bugs found in the starter project (README §3).
  These are good material: they show that the base code was analysed, not just copied.
* Design principle: keep the starter architecture (Flask + `db.py` + rule engine + `users.db`/`rules.db`
  + JSON content) and extend it, rather than replace it.

## 3. Architecture
Request flow for `/plan`:
```
browser ──► Flask route (app.py)
              ├─ db.get_user()            users + preferences + performance   (users.db)
              ├─ db.get_context()         current session context             (users.db)
              ├─ adapt_meal()
              │    ├─ db.get_rules()      rules ordered by priority           (rules.db)
              │    ├─ db.get_all_meals()  meals + tags                        (meals.db)
              │    ├─ evaluate conditions → collect actions → merge policies
              │    └─ score / filter / rank meals + explanations
              ├─ db.log_recommendations() history + refresh_performance()
              └─ render meal_plan.html with ui settings as <body> classes
```

## 4. User model
* Static attributes: `users` + typed `preferences` (form on the Profile page).
* Dynamic attributes: `performance`, recomputed by `refresh_performance()` (show the SQL).
* When the updates happen: after every interaction, and at the start and end of a session.
* Influence on adaptation: the `goal_*`, `pref_*`, `beginner_*`, `advanced_with_time` rules (static) and
  the `history_*` and `new_user_tips` rules (dynamic). Evidence: `test_history_changes_adaptation`.

* Version 2 additions: optional body data → `backend/nutrition.py` (BMI, BMR, energy and protein
  targets) → facts used by the `target_*` rules. Health conditions and allergies are multi-valued
  `preferences` rows, and each one triggers its own filter rule. Explain the safety choices: generic limits,
  a 1200 kcal floor, reference weight for protein, and "not medical advice" shown in the UI.

## 5. Context model
* `context` table: one row per session, INSERT at start, UPDATE when the context bar changes,
  closed at the end or when a new session starts.
* Automatic detection (`script.js`) with manual override.
* `meal_history.context_snapshot` keeps the context *at the moment* of each interaction. The
  Dashboard's "Sessions and their context" table shows one user in several contexts.

## 6. Rules and parser
* Grammar, actions and **merge policies** (README §5). The policies are what prevent one rule
  from overwriting another, which was a problem in the starter engine.
* Priority + conflict reporting (the "Conflicts resolved" section of the adaptation ticket, e.g. a
  desktop with 10 minutes: `card_detail` = compact from `short_time_quick` (70) beats `device_desktop` (50)).
* Robustness: rules are validated, and a broken rule is reported and skipped instead of crashing the app or matching everything.
* Rules are data: disabling a rule in SQLite changes the output (`test_rules_are_read_from_sqlite`).

## 7. Adaptive interface
Use screenshots (all real, taken from the running app):
* `02_alice_desktop_30.png` vs `04_alice_mobile_10_same_session.png`: the same user and session, context changed.
* `05_bob_mobile_slow.png`, `06_bob_meal_details_lowdata.png`: mobile and slow connection, no images.
* `03_meal_details.png`: explanation and per-rule score table.
* `09_scenarios.png`: A, B and C side by side.
* `11_emma_large_text_health.png`, `08_profile.png`, `12_emma_meal_nutrition.png`: age-based text size,
  health filters, nutrition and personal targets.

## 8. Evaluation
Copy the numbers from `docs/TEST_RESULTS.md` **after re-running the tests on your own machine**.
Discuss A vs B (two users) and A vs C (same user). Mention the bugs that the tests found and that were fixed.

## 9. Dashboard (optional step)
`meal_history` and `saved_meals`. Dashboard: KPIs, a 14-day activity chart, most viewed and most chosen categories,
most chosen meals, sessions with their context, recommendation history (with the context at that time),
and recent interactions. History is also fed back into the rules (`history_*`).

## 9b. Version 3 (beyond the brief)
Interface in three languages including right-to-left Arabic (translation layer in `i18n/`, data stays
in English), user-selected avatars (`users.avatar`, schema v3), logo, and fully clickable cards. These are
usability additions. The adaptation logic is unchanged.

## 10. Conclusion and future work (NOT implemented)
A rule editor in the UI, parentheses in conditions, a weekly plan and shopping list, time-of-day and
location context, learning rule weights from the history, and a user study.
