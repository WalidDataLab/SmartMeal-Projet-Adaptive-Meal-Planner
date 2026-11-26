# Test results

These results were produced by actually running the commands below on 2026-11-19 with Python 3.13.18, Flask 3.1.3 and pytest 9.1.1 on Linux (version 3 of SmartMeal). The same 93 tests were also run on the user's own copy of the project. Re-run them on your own machine before you put numbers in the report.

## 1. Automated tests: `python -m pytest -v`

```
collected 93 items

tests/test_adaptation.py::test_condition_operators[available_time<=10-ctx0-False] PASSED [  1%]
tests/test_adaptation.py::test_condition_operators[available_time<=10-ctx1-True] PASSED [  2%]
tests/test_adaptation.py::test_condition_operators[performance.avg_score>=70-ctx2-True] PASSED [  3%]
tests/test_adaptation.py::test_condition_operators[performance.avg_score>=80-ctx3-False] PASSED [  4%]
tests/test_adaptation.py::test_condition_operators[available_time < 10-ctx4-False] PASSED [  5%]
tests/test_adaptation.py::test_condition_operators[available_time > 5-ctx5-True] PASSED [  6%]
tests/test_adaptation.py::test_condition_operators[device_type = mobile-ctx6-True] PASSED [  7%]
tests/test_adaptation.py::test_condition_operators[device_type != mobile-ctx7-True] PASSED [  8%]
tests/test_adaptation.py::test_condition_operators[dietary_goal = muscle_gain AND available_time <= 15-ctx8-True] PASSED [  9%]
tests/test_adaptation.py::test_condition_operators[dietary_goal = muscle_gain AND available_time <= 15-ctx9-False] PASSED [ 10%]
tests/test_adaptation.py::test_condition_operators[device_type = tablet OR available_time <= 15-ctx10-True] PASSED [ 11%]
tests/test_adaptation.py::test_condition_operators[restrictions CONTAINS vegetarian-ctx11-True] PASSED [ 12%]
tests/test_adaptation.py::test_condition_operators[restrictions NOT CONTAINS vegan-ctx12-True] PASSED [ 13%]
tests/test_adaptation.py::test_condition_operators[food_preferences CONTAINS fish AND performance.vegetarian_ratio >= 0.6-ctx13-True] PASSED [ 15%]
tests/test_adaptation.py::test_condition_operators[unknown_key = 3-ctx14-False] PASSED [ 16%]
tests/test_adaptation.py::test_condition_operators[performance.unknown >= 0-ctx15-False] PASSED [ 17%]
tests/test_adaptation.py::test_condition_operators[device_type >= 3-ctx16-False] PASSED [ 18%]
tests/test_adaptation.py::test_and_inside_words_is_not_a_separator PASSED [ 19%]
tests/test_adaptation.py::test_invalid_conditions_raise[] PASSED         [ 20%]
tests/test_adaptation.py::test_invalid_conditions_raise[device_type mobile] PASSED [ 21%]
tests/test_adaptation.py::test_invalid_conditions_raise[available_time <=] PASSED [ 22%]
tests/test_adaptation.py::test_invalid_conditions_raise[= 3] PASSED      [ 23%]
tests/test_adaptation.py::test_invalid_adaptations_raise[boost=high_protein] PASSED [ 24%]
tests/test_adaptation.py::test_invalid_adaptations_raise[boost=pizza:2] PASSED [ 25%]
tests/test_adaptation.py::test_invalid_adaptations_raise[layout=diagonal] PASSED [ 26%]
tests/test_adaptation.py::test_invalid_adaptations_raise[cards_per_page=many] PASSED [ 27%]
tests/test_adaptation.py::test_invalid_adaptations_raise[nonsense=1] PASSED [ 29%]
tests/test_adaptation.py::test_invalid_adaptations_raise[filter=unknown] PASSED [ 30%]
tests/test_adaptation.py::test_multiple_rules_are_combined_not_overwritten PASSED [ 31%]
tests/test_adaptation.py::test_hard_filters_and_reference_values PASSED  [ 32%]
tests/test_adaptation.py::test_broken_rule_is_reported_and_skipped PASSED [ 33%]
tests/test_adaptation.py::test_relaxes_time_when_nothing_fits PASSED     [ 34%]
tests/test_adaptation.py::test_every_stored_rule_parses PASSED           [ 35%]
tests/test_adaptation.py::test_rules_are_read_from_sqlite PASSED         [ 36%]
tests/test_adaptation.py::test_restrictions_are_always_respected PASSED  [ 37%]
tests/test_adaptation.py::test_recommendations_carry_an_explanation PASSED [ 38%]
tests/test_adaptation.py::test_history_changes_adaptation PASSED         [ 39%]
tests/test_database.py::test_all_tables_created PASSED                   [ 40%]
tests/test_database.py::test_initialisation_is_safe_and_repeatable PASSED [ 41%]
tests/test_database.py::test_reset_rebuilds_sample_data PASSED           [ 43%]
tests/test_database.py::test_foreign_keys_are_enforced PASSED            [ 44%]
tests/test_database.py::test_unique_and_check_constraints PASSED         [ 45%]
tests/test_database.py::test_parameterised_queries_store_hostile_input_literally PASSED [ 46%]
tests/test_database.py::test_meal_dataset PASSED                         [ 47%]
tests/test_database.py::test_static_profile_update_filters_invalid_values PASSED [ 48%]
tests/test_database.py::test_context_insert_update_retrieve PASSED       [ 49%]
tests/test_database.py::test_clean_context_validation PASSED             [ 50%]
tests/test_database.py::test_dynamic_attributes_update_after_each_interaction PASSED [ 51%]
tests/test_database.py::test_session_duration_is_measured PASSED         [ 52%]
tests/test_database.py::test_dashboard_queries PASSED                    [ 53%]
tests/test_health.py::test_every_meal_has_nutrition_cost_and_allergens PASSED [ 54%]
tests/test_health.py::test_mifflin_st_jeor_and_targets PASSED            [ 55%]
tests/test_health.py::test_katch_mcardle_when_body_fat_is_known PASSED   [ 56%]
tests/test_health.py::test_goal_changes_energy_target_and_floor PASSED   [ 58%]
tests/test_health.py::test_protein_uses_reference_weight_above_bmi_25 PASSED [ 59%]
tests/test_health.py::test_missing_body_data_gives_no_targets PASSED     [ 60%]
tests/test_health.py::test_body_data_is_optional_and_validated PASSED    [ 61%]
tests/test_health.py::test_diabetes_limits_sugar PASSED                  [ 62%]
tests/test_health.py::test_hypertension_and_nut_allergy PASSED           [ 63%]
tests/test_health.py::test_cholesterol_and_fish_allergy PASSED           [ 64%]
tests/test_health.py::test_several_conditions_and_allergies_combine PASSED [ 65%]
tests/test_health.py::test_invalid_health_values_are_ignored PASSED      [ 66%]
tests/test_health.py::test_weight_loss_vs_weight_gain_rankings PASSED    [ 67%]
tests/test_health.py::test_personal_target_rules_need_body_data PASSED   [ 68%]
tests/test_health.py::test_age_60_plus_gets_large_text PASSED            [ 69%]
tests/test_health.py::test_profile_form_saves_health_and_body PASSED     [ 70%]
tests/test_health.py::test_cards_and_details_show_nutrition_and_cost PASSED [ 72%]
tests/test_health.py::test_own_photo_replaces_illustration PASSED        [ 73%]
tests/test_health.py::test_v1_databases_are_migrated_in_place PASSED     [ 74%]
tests/test_i18n_avatars.py::test_every_interface_string_is_translated PASSED [ 75%]
tests/test_i18n_avatars.py::test_translations_keep_the_same_placeholders PASSED [ 76%]
tests/test_i18n_avatars.py::test_labels_avatars_nutrients_and_methods_are_translated PASSED [ 77%]
tests/test_i18n_avatars.py::test_content_is_translated PASSED            [ 78%]
tests/test_i18n_avatars.py::test_arabic_and_french_explanations PASSED   [ 79%]
tests/test_i18n_avatars.py::test_language_switch_changes_text_and_direction[en-ltr-Build my meal plan] PASSED [ 80%]
tests/test_i18n_avatars.py::test_language_switch_changes_text_and_direction[fr-ltr-Cr\xe9er mon plan de repas] PASSED [ 81%]
tests/test_i18n_avatars.py::test_language_switch_changes_text_and_direction[ar-rtl-\u0623\u0646\u0634\u0626 \u062e\u0637\u0629 \u0648\u062c\u0628\u0627\u062a\u064a] PASSED [ 82%]
tests/test_i18n_avatars.py::test_plan_and_meal_page_in_arabic PASSED     [ 83%]
tests/test_i18n_avatars.py::test_browser_language_is_used_by_default PASSED [ 84%]
tests/test_i18n_avatars.py::test_unknown_language_is_ignored PASSED      [ 86%]
tests/test_i18n_avatars.py::test_avatar_files_exist PASSED               [ 87%]
tests/test_i18n_avatars.py::test_avatar_is_saved_validated_and_shown PASSED [ 88%]
tests/test_i18n_avatars.py::test_v2_database_gets_avatar_column PASSED   [ 89%]
tests/test_i18n_avatars.py::test_whole_meal_card_is_clickable PASSED     [ 90%]
tests/test_scenarios.py::test_scenario_A_muscle_gain_desktop PASSED      [ 91%]
tests/test_scenarios.py::test_scenario_B_healthy_mobile_slow PASSED      [ 92%]
tests/test_scenarios.py::test_scenario_C_same_user_new_context PASSED    [ 93%]
tests/test_scenarios.py::test_two_users_same_context_get_different_plans PASSED [ 94%]
tests/test_scenarios.py::test_ui_scenario_A_then_C_in_the_same_session PASSED [ 95%]
tests/test_scenarios.py::test_ui_scenario_B_reduced_media PASSED         [ 96%]
tests/test_scenarios.py::test_ui_interactions_update_profile_and_dashboard PASSED [ 97%]
tests/test_scenarios.py::test_profile_edit_changes_recommendations PASSED [ 98%]
tests/test_scenarios.py::test_pages_and_guards PASSED                    [100%]

============================== 93 passed in 3.74s ==============================
```

### What the tests cover

| File | Tests | What is verified |
|---|---|---|
| `tests/test_database.py` | 13 | All tables exist. Init is safe to repeat (data survives restarts) and `--reset` rebuilds. Foreign keys, UNIQUE and CHECK constraints are enforced. Parameterised queries store hostile input literally. The meal dataset is complete and every image exists. Profile updates drop invalid values. Context INSERT → UPDATE (same row) → retrieval works, and a new session closes the old one. Dynamic attributes are recomputed after each interaction. Session duration is measured. Dashboard queries return the expected data. |
| `tests/test_adaptation.py` | 37 | Every operator, including the two cases broken in the original (`<=` and `>=`). AND/OR. Unknown keys fail closed. `AND` inside a word is not a separator. Malformed conditions and actions are rejected. Several rules combine without overwriting each other (scores add up, `cards_per_page` takes the minimum, layout is decided by priority and the conflict is reported). Hard filters and `@references` work. A broken rule is reported and skipped. All 33 stored rules parse. **Rules really come from SQLite**: disabling `device_mobile` in the DB changes the layout. Restrictions are always respected. Every recommendation has an explanation. **Behaviour changes adaptation**: after 3 vegetarian choices, `history_vegetarian` fires. |
| `tests/test_health.py` | 19 | **Version 2.** Every meal has complete nutrition, cost and allergens, and they are consistent. Mifflin-St Jeor and Katch-McArdle give the expected values. Goal factors and the 1200 kcal floor apply. The protein reference weight applies above BMI 25. Body data is optional and validated. Diabetes, cholesterol, hypertension, coeliac and lactose filters work, alone and **combined** with several allergies. Weight-loss plans have fewer calories than weight-gain plans (compared within each meal type). Personal-target rules fire only when body data exists. Users aged 60+ get large text in the HTML. The profile form saves health and body data. Cards and the meal page show nutrition and cost. An own photo replaces the illustration. **A v1 database is migrated in place** (users and history kept). |
| `tests/test_i18n_avatars.py` | 15 | **Version 3.** Every interface string in the templates and app has a French and an Arabic translation with the same `{placeholders}`, as do every label, avatar, nutrient, rule, meal and ingredient. Explanations are built in each language. The language switch changes the text and `dir` (`rtl` for Arabic). The browser language is used by default and unknown codes are ignored. The Arabic plan and meal pages show translated content. The avatar files and logo exist. An avatar is saved, validated (a path-like value is rejected) and shown. A v2 database gets the `avatar` column without its rules being replaced. Every card is clickable and its buttons are still present. |
| `tests/test_scenarios.py` | 9 | Scenarios A, B and C on the engine. Two users in the same context get different plans. The **served HTML** for A then C *in the same session* (grid with 9 cards and images → single column with 4 compact cards and bottom nav; same Context row, `updates_count = 1`). B in the HTML (no `<img>` in the meal list, low-data notice). Clicks update the profile and dashboard, and recommendations are logged once. Editing the profile changes the plan. Route guards, the 404 page and ending a session. |

## 2. Scenario demonstration: `python adapt_meal.py`

```

=== Scenario A: Alice (muscle_gain) | {'device_type': 'desktop', 'available_time': 30, 'meal_budget': 'medium', 'connection_quality': 'fast', 'meal_moment': 'any'}
Fired rules : fit_available_time, goal_muscle_gain, target_calories_gain, target_protein, device_desktop, history_saved, pref_high_protein, pref_fish, pref_meal_type
Interface   : {'layout': 'grid', 'cards_per_page': 9, 'card_detail': 'detailed', 'media': 'full', 'show_images': True, 'show_tips': False, 'nav': 'top', 'text_size': 'normal'}
  1. Salmon with Roasted Vegetables     score=  10  30 min  protein=high   cost=high
  2. Tuna & Sweetcorn Wrap              score=   9   8 min  protein=high   cost=low
  3. Garlic Shrimp Zucchini Noodles     score=   9  15 min  protein=high   cost=high
  4. Smoked Salmon Bagel                score=   8   8 min  protein=high   cost=high
  5. Protein Energy Balls               score=   8  15 min  protein=high   cost=low

=== Scenario B: Bob (healthy_eating) | {'device_type': 'mobile', 'available_time': 10, 'meal_budget': 'low', 'connection_quality': 'slow', 'meal_moment': 'any'}
Fired rules : fit_available_time, connection_slow, short_time_quick, context_low_budget, beginner_short_time, goal_healthy_balanced, goal_healthy_vegetables, history_vegetarian, device_mobile, history_quick, history_favorite_category, history_saved, pref_vegetables, pref_balanced, budget_profile_low, beginner_easy, pref_meal_type
Interface   : {'layout': 'single_column', 'cards_per_page': 4, 'card_detail': 'compact', 'media': 'reduced', 'show_images': False, 'show_tips': False, 'nav': 'bottom', 'text_size': 'normal'}
  1. Chickpea & Vegetable Salad         score=  22  10 min  protein=medium cost=low
  2. Greek Yogurt Protein Bowl          score=  17   5 min  protein=high   cost=low
  3. Overnight Oats with Banana         score=  17   5 min  protein=medium cost=low
  4. Spinach & Feta Omelette            score=  17  10 min  protein=high   cost=low
  5. Hummus with Veggie Sticks          score=  16   5 min  protein=medium cost=low

=== Scenario C: Alice (muscle_gain) | {'device_type': 'mobile', 'available_time': 10, 'meal_budget': 'medium', 'connection_quality': 'normal', 'meal_moment': 'any'}
Fired rules : fit_available_time, short_time_quick, goal_muscle_gain, target_calories_gain, target_protein, device_mobile, history_saved, pref_high_protein, pref_fish, pref_meal_type
Interface   : {'layout': 'single_column', 'cards_per_page': 4, 'card_detail': 'compact', 'media': 'full', 'show_images': True, 'show_tips': False, 'nav': 'bottom', 'text_size': 'normal'}
  1. Tuna & Sweetcorn Wrap              score=  12   8 min  protein=high   cost=low
  2. Smoked Salmon Bagel                score=  11   8 min  protein=high   cost=high
  3. Cottage Cheese & Pineapple         score=   9   3 min  protein=high   cost=low
  4. Greek Yogurt Protein Bowl          score=   9   5 min  protein=high   cost=low
  5. Edamame with Sea Salt              score=   9   6 min  protein=high   cost=low
```

### Reading the results

* **A vs B (two users, two contexts).** Alice (muscle gain, desktop, 30 min) gets high-protein meals (the top 5 are all high protein, several with fish because of her preference) in a 9-card grid with images. Bob (healthy eating, beginner, mobile, 10 min, low budget, slow connection) gets cheap, quick, balanced or vegetable-rich meals. 17 rules fire for him, three of them coming from his history (`history_vegetarian`, `history_quick`, `history_favorite_category`). He gets a single column of 4 compact cards with no images.
* **A vs C (same user, two contexts).** Only the context changes. The time constraint removes the 30-minute salmon and the 15-minute shrimp. `short_time_quick` fires and promotes ≤15-minute meals, so the ranking changes (the Tuna Wrap moves to #1 and Cottage Cheese & Pineapple appears). The interface switches from a grid to a single column with compact cards and bottom navigation. Her goal still applies: all top-5 meals in C are high protein.
* **Visible in the browser.** `tests/test_scenarios.py` checks the same differences in the HTML that Flask serves. The screenshots in `docs/screenshots/` were taken from the running app with headless Chrome (`02` = scenario A, `04` = the same session after switching to mobile/10 min, `05` = scenario B on a 390 px phone viewport).

## 3. Bugs found and fixed during testing
Version 3:
* With a short time available, compact cards placed a stretched image beside the text in the desktop grid. Compact cards now keep the image on top (16:9).
* Some Arabic rule explanations were written in dialect and did not read correctly after «مقترحة لأنها». They were rewritten in Modern Standard Arabic.

Version 2:
* The generic "energy-rich" threshold for snacks (200 kcal) was too low. Weight-gain plans were promoting small snacks, and their top meals averaged fewer calories than weight-loss plans. The reference is now 250 kcal, and the test compares plans within each meal type.
* After the v1 → v2 migration, the statistics of existing users were not recalculated (the `performance` row was missing). The migration now refreshes every user.
* Two rule explanations produced "it is provides…". They were reworded.

Version 1:

* `available_time <=` (an operator with no value) was parsed as `<` with the value `=`. The clause regex now refuses a value that starts with an operator character, so the malformed rule is rejected and reported.
* Meal names containing `&` produced invalid SVG placeholder images. Names are now XML-escaped.
* Compact cards without images (slow connection) put the text into the 96 px thumbnail column. The thumbnail grid now applies only when an image is present.
