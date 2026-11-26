# -*- coding: utf-8 -*-
"""
Minimal internationalisation for SmartMeal: English (source), French, Arabic (RTL).

Templates call _("English text", **values). The English text is the key; the
translation is looked up in UI below and then formatted with str.format(**values).
Content (meal names, ingredients, rule explanations) lives in i18n/content.py.
No external library is needed (Flask-Babel would be the production choice).
"""
from i18n.content import ALLERGEN_NAMES, CRITERIA, INGREDIENTS, MEALS, RULES, TAGS

LANGUAGES = {"en": "English", "fr": "Français", "ar": "العربية"}
RTL = {"ar"}
DEFAULT = "en"
_IDX = {"fr": 0, "ar": 1}

# Display names (English) of every enum value stored in the database
LABELS = {
    "weight_loss": "Weight loss", "weight_gain": "Weight gain", "muscle_gain": "Muscle gain",
    "healthy_eating": "Healthy eating",
    "low": "Low", "medium": "Medium", "high": "High",
    "beginner": "Beginner", "intermediate": "Intermediate", "advanced": "Advanced",
    "desktop": "Desktop", "tablet": "Tablet", "mobile": "Mobile",
    "slow": "Slow", "normal": "Normal", "fast": "Fast",
    "any": "Any time", "breakfast": "Breakfast", "lunch": "Lunch", "dinner": "Dinner", "snack": "Snack",
    "high_protein": "High protein", "vegetables": "Vegetables", "balanced": "Balanced",
    "fish": "Fish & seafood", "spicy": "Spicy", "light": "Light", "high_fiber": "High fibre",
    "vegetarian": "Vegetarian", "vegan": "Vegan", "gluten_free": "Gluten-free", "dairy_free": "Dairy-free",
    "veggie_rich": "Veggie-rich",
    "diabetes": "Diabetes", "high_cholesterol": "High cholesterol",
    "hypertension": "High blood pressure (salt)", "celiac": "Coeliac disease",
    "lactose_intolerance": "Lactose intolerance",
    "gluten": "Gluten", "dairy": "Dairy", "eggs": "Eggs", "nuts": "Tree nuts", "peanuts": "Peanuts",
    "shellfish": "Shellfish", "soy": "Soy", "sesame": "Sesame",
    "female": "Female", "male": "Male",
    "activity_low": "Low (mostly sitting)", "activity_moderate": "Moderate", "activity_high": "High (very active)",
    "grid": "Grid", "two_column": "Two columns", "single_column": "Single column",
    "detailed": "Detailed", "compact": "Compact",
    "easy": "Easy", "hard": "Hard",
    "recommended": "Recommended", "viewed": "Viewed", "selected": "Chosen", "saved": "Saved",
    "unsaved": "Removed", "recommendation": "Recommendation", "direct": "Direct",
    "constraint": "Constraint", "interface": "Interface",
}

AVATAR_LABELS = {
    "avatar_01": "Runner with ponytail", "avatar_02": "Athlete with whistle",
    "avatar_03": "Young man in a hoodie", "avatar_04": "Young woman with long hair",
    "avatar_05": "Boy", "avatar_06": "Girl with pigtails", "avatar_07": "Grandfather with glasses",
    "avatar_08": "Grandmother with a bun", "avatar_09": "Tech fan with headphones",
    "avatar_10": "Developer with a bob", "avatar_11": "Woman with hijab",
    "avatar_12": "Woman with hijab and glasses", "avatar_13": "Woman with afro",
    "avatar_14": "Woman with braids", "avatar_15": "Man with a beard",
    "avatar_16": "Man in a flannel shirt", "avatar_17": "Woman with curly hair", "avatar_18": "Chef",
    "avatar_19": "Professional in a blazer", "avatar_20": "Teen with a cap",
}

# English -> (French, Arabic)
UI = {
    # navigation / chrome
    "Main": ("Principal", "الرئيسية"), "My plan": ("Mon plan", "خطتي"), "Profile": ("Profil", "الملف الشخصي"),
    "Dashboard": ("Tableau de bord", "لوحة المتابعة"), "Scenarios": ("Scénarios", "السيناريوهات"),
    "Rules": ("Règles", "القواعد"), "Language": ("Langue", "اللغة"), "End session": ("Terminer la session", "إنهاء الجلسة"),
    "Start a session": ("Commencer une session", "ابدأ جلسة"), "Start": ("Accueil", "البداية"),
    "SmartMeal, an adaptive meal planner built on the Adaptive Quiz System starter project. Suggestions are general meal ideas, not dietary or medical advice.":
        ("SmartMeal, un planificateur de repas adaptatif construit sur le projet de départ Adaptive Quiz System. Les suggestions sont des idées de repas générales, pas un conseil diététique ou médical.",
         "SmartMeal، مخطِّط وجبات تكيّفي مبني على مشروع Adaptive Quiz System. الاقتراحات أفكار وجبات عامة، وليست نصيحة غذائية أو طبية."),
    # index
    "What should you eat, given the time you have right now?":
        ("Que manger, avec le temps dont vous disposez maintenant ?", "ماذا تأكل بالوقت المتاح لك الآن؟"),
    "Pick a profile, tell SmartMeal about your situation, and get a meal plan that adapts to your goal, your habits, your device and your schedule.":
        ("Choisissez un profil, décrivez votre situation et obtenez un plan de repas qui s'adapte à votre objectif, vos habitudes, votre appareil et votre emploi du temps.",
         "اختر ملفاً شخصياً، وأخبر SmartMeal عن وضعك، واحصل على خطة وجبات تتكيّف مع هدفك وعاداتك وجهازك ووقتك."),
    "Detected:": ("Détecté :", "تم الكشف:"), "Could not be detected; choose manually.": ("Détection impossible ; choisissez manuellement.", "تعذّر الكشف؛ اختر يدوياً."),
    "your last session used": ("votre dernière session utilisait", "جلستك الأخيرة استخدمت"),
    "Who is cooking?": ("Qui cuisine ?", "من سيطبخ؟"),
    "{n} sessions, {m} meals chosen": ("{n} sessions, {m} repas choisis", "{n} جلسات، {m} وجبات مختارة"),
    "New profile": ("Nouveau profil", "ملف جديد"), "Your situation right now": ("Votre situation actuelle", "وضعك الآن"),
    "Time available to cook:": ("Temps disponible pour cuisiner :", "الوقت المتاح للطبخ:"), "min": ("min", "د"),
    "Budget for this meal": ("Budget pour ce repas", "ميزانية هذه الوجبة"), "Which meal?": ("Quel repas ?", "أي وجبة؟"),
    "Device": ("Appareil", "الجهاز"), "Connection": ("Connexion", "الاتصال"),
    "Build my meal plan": ("Créer mon plan de repas", "أنشئ خطة وجباتي"),
    # card / ticket
    "Top pick for you": ("Notre choix pour vous", "الأنسب لك"), "Adaptation score": ("Score d'adaptation", "درجة التكيّف"),
    "Estimated cost per serving": ("Coût estimé par portion", "التكلفة التقديرية للحصة"),
    "Vegetarian": ("Végétarien", "نباتية"), "Estimated nutrition per serving": ("Valeurs nutritionnelles estimées par portion", "القيم الغذائية التقديرية للحصة"),
    "Protein": ("Protéines", "بروتين"), "g": ("g", "غ"), "Carbs": ("Glucides", "كربوهيدرات"), "Fat": ("Lipides", "دهون"),
    "Sugars": ("Sucres", "سكريات"), "Why this meal:": ("Pourquoi ce repas :", "لماذا هذه الوجبة:"),
    "Fits your health and diet settings ({n} checks)": ("Compatible avec vos réglages santé et régime ({n} vérifications)", "تناسب إعداداتك الصحية والغذائية ({n} شروط)"),
    "{n} more reasons": ("{n} autres raisons", "{n} أسباب أخرى"), "Choose": ("Choisir", "اختر"),
    "Saved": ("Enregistré", "محفوظة"), "Save": ("Enregistrer", "احفظ"),
    "How this plan was adapted": ("Comment ce plan a été adapté", "كيف تكيّفت هذه الخطة"),
    "Adaptation ticket": ("Ticket d'adaptation", "بطاقة التكيّف"),
    "{n} of {total} rules applied": ("{n} règles appliquées sur {total}", "طُبّقت {n} من أصل {total} قاعدة"),
    "Est. daily energy": ("Énergie quotidienne est.", "الطاقة اليومية التقديرية"),
    "Health and allergies": ("Santé et allergies", "الصحة والحساسية"), "Time": ("Temps", "الوقت"), "Budget": ("Budget", "الميزانية"),
    "Meal": ("Repas", "الوجبة"), "Interface": ("Interface", "الواجهة"), "Layout:": ("Disposition :", "التخطيط:"),
    "Meals per page:": ("Repas par page :", "وجبات بالصفحة:"), "Cards:": ("Cartes :", "البطاقات:"), "Images:": ("Images :", "الصور:"),
    "shown": ("affichées", "ظاهرة"), "hidden (low-data mode)": ("masquées (mode économie de données)", "مخفية (وضع توفير البيانات)"),
    "Text:": ("Texte :", "النص:"), "large": ("grand", "كبير"), "Rules applied": ("Règles appliquées", "القواعد المطبّقة"),
    "Conflicts resolved": ("Conflits résolus", "تعارضات محلولة"), "higher priority than": ("priorité plus haute que", "أولوية أعلى من"),
    "{n} meals match, {x} filtered out": ("{n} repas correspondent, {x} exclus", "{n} وجبة مناسبة، {x} مستبعدة"),
    "max {t} min": ("max {t} min", "حد أقصى {t} د"),
    # plan
    "{name}, here is your plan": ("{name}, voici votre plan", "{name}، هذه خطتك"),
    "{n} meals fit your {t}-minute window, ranked by your profile, habits and context.":
        ("{n} repas tiennent dans vos {t} minutes, classés selon votre profil, vos habitudes et votre contexte.",
         "{n} وجبة تناسب الـ {t} دقيقة المتاحة لك، مرتّبة حسب ملفك وعاداتك وسياقك."),
    "Update": ("Mettre à jour", "تحديث"),
    "Low-data mode: images are switched off and fewer meals load per page because your connection is slow.":
        ("Mode économie de données : images désactivées et moins de repas par page, car votre connexion est lente.",
         "وضع توفير البيانات: الصور مخفية ووجبات أقل بالصفحة لأن اتصالك بطيء."),
    "New here? Choose or save meals you like: SmartMeal learns from what you pick and adjusts future plans. Change the bar above when your situation changes.":
        ("Nouveau ici ? Choisissez ou enregistrez les repas que vous aimez : SmartMeal apprend de vos choix et ajuste vos prochains plans. Modifiez la barre ci-dessus quand votre situation change.",
         "جديد هنا؟ اختر أو احفظ الوجبات التي تعجبك: يتعلّم SmartMeal من اختياراتك ويعدّل خططك القادمة. غيّر الشريط أعلاه عندما يتغيّر وضعك."),
    "No meal fits in {t} minutes with your other constraints, so these are the quickest available options.":
        ("Aucun repas ne tient en {t} minutes avec vos autres contraintes : voici les options les plus rapides.",
         "لا توجد وجبة تناسب {t} دقيقة مع باقي شروطك، لذلك هذه أسرع الخيارات المتاحة."),
    "Recommended meals": ("Repas recommandés", "الوجبات المقترحة"),
    "No meal matches all your constraints. Try more time, another meal or a different budget.":
        ("Aucun repas ne respecte toutes vos contraintes. Essayez plus de temps, un autre repas ou un autre budget.",
         "لا توجد وجبة تحقق كل شروطك. جرّب وقتاً أطول أو وجبة أخرى أو ميزانية مختلفة."),
    "Pages": ("Pages", "الصفحات"), "Previous": ("Précédent", "السابق"), "Page {p} of {n}": ("Page {p} sur {n}", "صفحة {p} من {n}"),
    "More meals": ("Plus de repas", "وجبات أكثر"),
    # details
    "Back to my plan": ("Retour à mon plan", "العودة إلى خطتي"), "image hidden in low-data mode": ("image masquée en mode économie de données", "الصورة مخفية في وضع توفير البيانات"),
    "per serving": ("par portion", "للحصة"), "Difficulty:": ("Difficulté :", "الصعوبة:"),
    "Score {s}, rank {r} in your current plan": ("Score {s}, rang {r} dans votre plan actuel", "الدرجة {s}، الترتيب {r} في خطتك الحالية"),
    "Rule": ("Règle", "القاعدة"), "Criterion": ("Critère", "المعيار"), "Points": ("Points", "النقاط"),
    "Not in your current plan:": ("Absent de votre plan actuel :", "ليست في خطتك الحالية:"),
    "takes {t} min, more than your {a} min available": ("demande {t} min, plus que vos {a} min disponibles", "تحتاج {t} د، أكثر من الـ {a} د المتاحة لك"),
    "Choose this meal": ("Choisir ce repas", "اختر هذه الوجبة"), "Save for later": ("Enregistrer pour plus tard", "احفظها لوقت لاحق"),
    "Nutrition per serving": ("Valeurs nutritionnelles par portion", "القيم الغذائية للحصة"), "Estimated values": ("Valeurs estimées", "قيم تقديرية"),
    "compared with your estimated target for this meal ({p}% of the day)": ("comparées à votre objectif estimé pour ce repas ({p} % de la journée)", "مقارنة بهدفك التقديري لهذه الوجبة ({p}٪ من اليوم)"),
    "Nutrient": ("Nutriment", "العنصر الغذائي"), "Amount": ("Quantité", "الكمية"), "Your target for this meal": ("Votre objectif pour ce repas", "هدفك لهذه الوجبة"),
    "Allergens:": ("Allergènes :", "مسببات الحساسية:"), "none of the 9 tracked allergens": ("aucun des 9 allergènes suivis", "لا شيء من مسببات الحساسية التسعة المتتبَّعة"),
    "Values are estimates for a typical serving, not medical or dietary advice.": ("Valeurs estimées pour une portion type, sans valeur de conseil médical ou diététique.", "القيم تقديرية لحصة عادية، وليست نصيحة طبية أو غذائية."),
    "Ingredients": ("Ingrédients", "المكونات"),
    "Energy": ("Énergie", "الطاقة"), "Carbohydrates": ("Glucides", "الكربوهيدرات"), "of which sugars": ("dont sucres", "منها سكريات"),
    "of which saturated": ("dont saturés", "منها مشبعة"), "Fibre": ("Fibres", "الألياف"), "Salt": ("Sel", "الملح"),
    "Cholesterol": ("Cholestérol", "الكوليسترول"), "kcal": ("kcal", "سعرة"), "mg": ("mg", "ملغ"),
    # profile
    "Create a profile": ("Créer un profil", "إنشاء ملف شخصي"), "{name}'s profile": ("Profil de {name}", "ملف {name}"),
    "About you": ("À propos de vous", "عنك"),
    "These are the static attributes of your user model. You set them, and the rules use them.":
        ("Ce sont les attributs statiques de votre modèle utilisateur. Vous les définissez et les règles les utilisent.",
         "هذه هي الخصائص الثابتة في نموذجك كمستخدم. أنت تحدّدها، والقواعد تستخدمها."),
    "Name": ("Nom", "الاسم"), "Avatar": ("Avatar", "الصورة الرمزية"), "Initial letter": ("Initiale", "الحرف الأول"),
    "Goal": ("Objectif", "الهدف"), "Usual budget": ("Budget habituel", "الميزانية المعتادة"), "Cooking level": ("Niveau en cuisine", "مستوى الطبخ"),
    "Food you enjoy": ("Ce que vous aimez", "الأطعمة التي تحبها"), "Meals you plan most often": ("Repas que vous planifiez le plus", "الوجبات التي تخطط لها غالباً"),
    "Diet (always respected)": ("Régime (toujours respecté)", "النظام الغذائي (يُحترم دائماً)"), "Health": ("Santé", "الصحة"),
    "Choose as many as apply. Meals that do not respect these settings are never suggested. The limits are general guidelines, not medical advice: follow your doctor's recommendations.":
        ("Choisissez tout ce qui s'applique. Les repas qui ne respectent pas ces réglages ne sont jamais proposés. Les limites sont des repères généraux, pas un avis médical : suivez les recommandations de votre médecin.",
         "اختر كل ما ينطبق عليك. الوجبات التي لا تحترم هذه الإعدادات لا تُقترح أبداً. الحدود إرشادات عامة وليست نصيحة طبية: اتبع توصيات طبيبك."),
    "Health conditions": ("Problèmes de santé", "الحالات الصحية"), "Allergies and foods to avoid": ("Allergies et aliments à éviter", "الحساسية والأطعمة الواجب تجنّبها"),
    "Body data": ("Données corporelles", "بيانات الجسم"), "optional": ("facultatif", "اختياري"),
    "Fill in what you know. With age, height and weight (or weight and body fat), SmartMeal estimates your energy and protein needs and uses them to rank meals.":
        ("Indiquez ce que vous savez. Avec l'âge, la taille et le poids (ou le poids et la masse grasse), SmartMeal estime vos besoins en énergie et en protéines pour classer les repas.",
         "املأ ما تعرفه. بالعمر والطول والوزن (أو الوزن ونسبة الدهون) يقدّر SmartMeal احتياجك من الطاقة والبروتين ويستخدمه لترتيب الوجبات."),
    "Age": ("Âge", "العمر"), "Sex": ("Sexe", "الجنس"), "Prefer not to say": ("Je préfère ne pas répondre", "أفضّل عدم الإجابة"),
    "Activity": ("Activité", "النشاط"), "Height (cm)": ("Taille (cm)", "الطول (سم)"), "Weight (kg)": ("Poids (kg)", "الوزن (كغ)"),
    "Body fat (%)": ("Masse grasse (%)", "نسبة الدهون (٪)"), "Create profile": ("Créer le profil", "أنشئ الملف"),
    "Save profile": ("Enregistrer le profil", "احفظ الملف"), "Your estimated needs": ("Vos besoins estimés", "احتياجاتك التقديرية"),
    "Body mass index": ("Indice de masse corporelle", "مؤشر كتلة الجسم"),
    "Energy per day for your goal": ("Énergie par jour pour votre objectif", "الطاقة اليومية لهدفك"),
    "Protein per day for your goal": ("Protéines par jour pour votre objectif", "البروتين اليومي لهدفك"),
    "Target for:": ("Objectif pour :", "الهدف لـ:"),
    "Calculated with the {method} formula, your activity level and your goal.": ("Calculé avec la formule {method}, votre niveau d'activité et votre objectif.", "محسوبة بمعادلة {method} ومستوى نشاطك وهدفك."),
    "These are rough estimates used to rank meals, not a diet prescription.": ("Ce sont des estimations approximatives pour classer les repas, pas une prescription diététique.", "هذه تقديرات تقريبية لترتيب الوجبات، وليست وصفة غذائية."),
    "Add your age, height and weight to get personal calorie and protein targets.": ("Ajoutez votre âge, votre taille et votre poids pour obtenir des objectifs personnels de calories et de protéines.", "أضف عمرك وطولك ووزنك لتحصل على أهداف شخصية للسعرات والبروتين."),
    "Katch-McArdle (uses body fat)": ("Katch-McArdle (utilise la masse grasse)", "كاتش-ماكاردل (تستخدم نسبة الدهون)"),
    "Mifflin-St Jeor": ("Mifflin-St Jeor", "ميفلين-سانت جيور"),
    "Mifflin-St Jeor (sex not given: average)": ("Mifflin-St Jeor (sexe non indiqué : moyenne)", "ميفلين-سانت جيور (الجنس غير محدد: متوسط)"),
    "What SmartMeal has learned": ("Ce que SmartMeal a appris", "ما تعلّمه SmartMeal"),
    "Dynamic attributes. They are recomputed with SQL after every interaction and every session.":
        ("Attributs dynamiques, recalculés en SQL après chaque interaction et chaque session.", "خصائص ديناميكية، يُعاد حسابها بـ SQL بعد كل تفاعل وكل جلسة."),
    "Meals viewed": ("Repas consultés", "الوجبات المعروضة"), "Meals chosen": ("Repas choisis", "الوجبات المختارة"),
    "Meals saved": ("Repas enregistrés", "الوجبات المحفوظة"), "Opened from recommendations": ("Ouverts depuis les recommandations", "فُتحت من الاقتراحات"),
    "Favourite category": ("Catégorie préférée", "الفئة المفضلة"), "none yet": ("aucune pour l'instant", "لا يوجد بعد"),
    "Vegetarian share of choices": ("Part de choix végétariens", "نسبة الاختيارات النباتية"), "High-protein share": ("Part riche en protéines", "نسبة الغني بالبروتين"),
    "Quick-meal share": ("Part de repas rapides", "نسبة الوجبات السريعة"), "Sessions": ("Sessions", "الجلسات"),
    "Sessions in the last 7 days": ("Sessions des 7 derniers jours", "جلسات آخر 7 أيام"), "Average session": ("Session moyenne", "متوسط الجلسة"),
    "Last active": ("Dernière activité", "آخر نشاط"), "never": ("jamais", "أبداً"),
    # dashboard
    "{name}'s activity": ("Activité de {name}", "نشاط {name}"), "Show": ("Afficher", "اعرض"),
    "Recommendations opened": ("Recommandations ouvertes", "الاقتراحات المفتوحة"), "Activity, last 14 days": ("Activité des 14 derniers jours", "النشاط خلال آخر 14 يوماً"),
    "Daily views, choices and saves over the last 14 days": ("Consultations, choix et enregistrements par jour sur 14 jours", "المشاهدات والاختيارات والحفظ يومياً خلال 14 يوماً"),
    "Most viewed categories": ("Catégories les plus consultées", "الفئات الأكثر مشاهدة"), "No meals viewed yet.": ("Aucun repas consulté pour l'instant.", "لم تُعرض أي وجبة بعد."),
    "Most chosen categories": ("Catégories les plus choisies", "الفئات الأكثر اختياراً"), "No meals chosen yet.": ("Aucun repas choisi pour l'instant.", "لم تُختر أي وجبة بعد."),
    "Most chosen meals": ("Repas les plus choisis", "الوجبات الأكثر اختياراً"),
    "Choose a meal from your plan to see it here.": ("Choisissez un repas dans votre plan pour le voir ici.", "اختر وجبة من خطتك لتظهر هنا."),
    "Most viewed meals": ("Repas les plus consultés", "الوجبات الأكثر مشاهدة"), "Sessions and their context": ("Sessions et leur contexte", "الجلسات وسياقها"),
    "Each row is one record of the Context table. The same person cooks in different situations.":
        ("Chaque ligne est un enregistrement de la table Context. La même personne cuisine dans des situations différentes.",
         "كل سطر هو سجل في جدول Context. الشخص نفسه يطبخ في ظروف مختلفة."),
    "Started": ("Début", "البداية"), "Minutes": ("Minutes", "الدقائق"), "Actions": ("Actions", "الإجراءات"), "live": ("en cours", "جارية"),
    "No sessions yet.": ("Aucune session pour l'instant.", "لا توجد جلسات بعد."), "Recommendation history": ("Historique des recommandations", "سجل الاقتراحات"),
    "When": ("Quand", "متى"), "Rank": ("Rang", "الترتيب"), "Context at that time": ("Contexte à ce moment", "السياق وقتها"),
    "Recommendations are recorded when a plan is displayed.": ("Les recommandations sont enregistrées quand un plan est affiché.", "تُسجَّل الاقتراحات عند عرض الخطة."),
    "Recent interactions": ("Interactions récentes", "التفاعلات الأخيرة"), "Action": ("Action", "الإجراء"), "From": ("Origine", "المصدر"),
    "No interactions yet.": ("Aucune interaction pour l'instant.", "لا توجد تفاعلات بعد."),
    # rules / scenarios
    "Adaptation rules": ("Règles d'adaptation", "قواعد التكيّف"),
    "All {n} rules are read from the rules table of backend/rules.db. Higher-priority rules are evaluated first and win interface conflicts. Boosts and filters from all applicable rules are combined.":
        ("Les {n} règles sont lues dans la table rules de backend/rules.db. Les règles de priorité plus haute sont évaluées d'abord et l'emportent en cas de conflit d'interface. Les bonus et filtres de toutes les règles applicables sont combinés.",
         "تُقرأ القواعد الـ {n} من جدول rules في backend/rules.db. القواعد ذات الأولوية الأعلى تُقيَّم أولاً وتفوز عند تعارض إعدادات الواجهة. وتُجمع النقاط والفلاتر من كل القواعد المنطبقة."),
    "Priority": ("Priorité", "الأولوية"), "Kind": ("Type", "النوع"), "IF (condition)": ("SI (condition)", "إذا (الشرط)"),
    "THEN (adaptation)": ("ALORS (adaptation)", "فإن (التكيّف)"), "Explanation": ("Explication", "الشرح"),
    "Same rules, different people, different contexts": ("Mêmes règles, personnes différentes, contextes différents", "قواعد واحدة، أشخاص مختلفون، سياقات مختلفة"),
    "The engine runs live on the evaluation scenarios using the profiles, context values and rules stored in SQLite. Nothing here is written to the history. Each scenario is shown in the layout its own context produces.":
        ("Le moteur s'exécute en direct sur les scénarios d'évaluation avec les profils, contextes et règles stockés dans SQLite. Rien n'est écrit dans l'historique. Chaque scénario est affiché dans la disposition produite par son propre contexte.",
         "يعمل المحرك مباشرة على سيناريوهات التقييم باستخدام الملفات والسياقات والقواعد المخزنة في SQLite. لا يُكتب شيء في السجل. يظهر كل سيناريو بالتخطيط الذي ينتجه سياقه."),
    "Expected:": ("Attendu :", "المتوقع:"), "{n} rules applied": ("{n} règles appliquées", "{n} قاعدة مطبّقة"),
    "Scenario A: muscle gain at the desk": ("Scénario A : prise de muscle au bureau", "السيناريو أ: زيادة العضل على المكتب"),
    "Scenario B: healthy eating on the go": ("Scénario B : manger sain en déplacement", "السيناريو ب: أكل صحي أثناء التنقل"),
    "Scenario C: same user as A, new context": ("Scénario C : même utilisateur que A, nouveau contexte", "السيناريو ج: نفس مستخدم أ، سياق جديد"),
    "High-protein meals, desktop grid": ("repas riches en protéines, grille ordinateur", "وجبات غنية بالبروتين، شبكة للكمبيوتر"),
    "Quick, affordable meals, mobile layout, reduced media": ("repas rapides et abordables, mise en page mobile, médias réduits", "وجبات سريعة ورخيصة، تخطيط موبايل، وسائط أقل"),
    "Different (quick) meals and a mobile interface": ("des repas différents (rapides) et une interface mobile", "وجبات مختلفة (سريعة) وواجهة موبايل"),
    # flash messages (app.py)
    "Choose a profile and your current context to start.": ("Choisissez un profil et votre contexte actuel pour commencer.", "اختر ملفاً شخصياً وسياقك الحالي للبدء."),
    "Please choose a profile.": ("Veuillez choisir un profil.", "الرجاء اختيار ملف شخصي."),
    "Context updated. Your plan has been re-adapted.": ("Contexte mis à jour. Votre plan a été réadapté.", "تم تحديث السياق. أُعيد تكييف خطتك."),
    "“{meal}” added to your meal plan.": ("« {meal} » ajouté à votre plan de repas.", "أُضيفت «{meal}» إلى خطة وجباتك."),
    "“{meal}” saved.": ("« {meal} » enregistré.", "حُفظت «{meal}»."),
    "“{meal}” removed from saved meals.": ("« {meal} » retiré des repas enregistrés.", "أُزيلت «{meal}» من الوجبات المحفوظة."),
    "Profile updated. Recommendations now use your new profile.": ("Profil mis à jour. Les recommandations utilisent maintenant votre nouveau profil.", "تم تحديث الملف. الاقتراحات تستخدم ملفك الجديد الآن."),
    "Could not save profile: {error}": ("Impossible d'enregistrer le profil : {error}", "تعذّر حفظ الملف: {error}"),
    "Could not create profile: {error}": ("Impossible de créer le profil : {error}", "تعذّر إنشاء الملف: {error}"),
    "Profile created. Now tell us about your current context.": ("Profil créé. Décrivez maintenant votre contexte actuel.", "تم إنشاء الملف. أخبرنا الآن عن سياقك الحالي."),
    "Session ended. Your profile statistics were updated.": ("Session terminée. Les statistiques de votre profil ont été mises à jour.", "انتهت الجلسة. تم تحديث إحصائيات ملفك."),
    # explanation sentences
    "Recommended because {reasons}.": ("Recommandé : {reasons}.", "مقترحة لأنها {reasons}."),
    "Suggested because it fits your {t}-minute window ({p} min).": ("Suggéré car il tient dans vos {t} minutes ({p} min).", "مقترحة لأنها تناسب الـ {t} دقيقة المتاحة لك ({p} د)."),
    "Suggested to complete your plan.": ("Suggéré pour compléter votre plan.", "مقترحة لإكمال خطتك."),
    " and ": (" et ", " و"),
}

# labels: English display -> (French, Arabic)
UI.update({
    "Weight loss": ("Perte de poids", "خسارة الوزن"), "Weight gain": ("Prise de poids", "زيادة الوزن"),
    "Muscle gain": ("Prise de muscle", "زيادة العضل"), "Healthy eating": ("Alimentation saine", "أكل صحي"),
    "Low": ("Bas", "منخفضة"), "Medium": ("Moyen", "متوسطة"), "High": ("Élevé", "مرتفعة"),
    "Beginner": ("Débutant", "مبتدئ"), "Intermediate": ("Intermédiaire", "متوسط"), "Advanced": ("Avancé", "متقدّم"),
    "Desktop": ("Ordinateur", "كمبيوتر"), "Tablet": ("Tablette", "تابلت"), "Mobile": ("Mobile", "موبايل"),
    "Slow": ("Lente", "بطيء"), "Normal": ("Normale", "عادي"), "Fast": ("Rapide", "سريع"),
    "Any time": ("N'importe quand", "أي وقت"), "Breakfast": ("Petit-déjeuner", "فطور"), "Lunch": ("Déjeuner", "غداء"),
    "Dinner": ("Dîner", "عشاء"), "Snack": ("Collation", "وجبة خفيفة"),
    "High protein": ("Riche en protéines", "غني بالبروتين"), "Vegetables": ("Légumes", "خضار"), "Balanced": ("Équilibré", "متوازن"),
    "Fish & seafood": ("Poisson et fruits de mer", "سمك ومأكولات بحرية"), "Spicy": ("Épicé", "حار"), "Light": ("Léger", "خفيف"),
    "High fibre": ("Riche en fibres", "غني بالألياف"), "Vegan": ("Végan", "نباتي صرف"), "Gluten-free": ("Sans gluten", "خالٍ من الغلوتين"),
    "Dairy-free": ("Sans lactose", "خالٍ من الحليب"), "Veggie-rich": ("Riche en légumes", "غني بالخضار"),
    "Diabetes": ("Diabète", "السكري"), "High cholesterol": ("Cholestérol élevé", "الكوليسترول المرتفع"),
    "High blood pressure (salt)": ("Hypertension (sel)", "ارتفاع ضغط الدم (الملح)"), "Coeliac disease": ("Maladie cœliaque", "السيلياك (حساسية الغلوتين)"),
    "Lactose intolerance": ("Intolérance au lactose", "عدم تحمّل اللاكتوز"),
    "Gluten": ("Gluten", "الغلوتين"), "Dairy": ("Produits laitiers", "مشتقات الحليب"), "Eggs": ("Œufs", "البيض"),
    "Tree nuts": ("Fruits à coque", "المكسرات"), "Peanuts": ("Arachides", "الفول السوداني"), "Shellfish": ("Fruits de mer", "القشريات"),
    "Soy": ("Soja", "الصويا"), "Sesame": ("Sésame", "السمسم"), "Female": ("Femme", "أنثى"), "Male": ("Homme", "ذكر"),
    "Low (mostly sitting)": ("Faible (surtout assis)", "منخفض (جلوس معظم الوقت)"), "Moderate": ("Modérée", "متوسط"),
    "High (very active)": ("Élevée (très actif)", "مرتفع (نشيط جداً)"),
    "Grid": ("Grille", "شبكة"), "Two columns": ("Deux colonnes", "عمودان"), "Single column": ("Une colonne", "عمود واحد"),
    "Detailed": ("Détaillées", "مفصّلة"), "Compact": ("Compactes", "مختصرة"), "Easy": ("Facile", "سهلة"), "Hard": ("Difficile", "صعبة"),
    "Recommended": ("Recommandé", "مقترحة"), "Viewed": ("Consulté", "معروضة"), "Chosen": ("Choisi", "مختارة"),
    "Removed": ("Retiré", "أُزيلت"), "Recommendation": ("Recommandation", "اقتراح"), "Direct": ("Direct", "مباشر"),
    "Constraint": ("Contrainte", "قيد"),
})

# avatar descriptions
UI.update({
    "Runner with ponytail": ("Coureuse à queue-de-cheval", "عدّاءة بذيل حصان"), "Athlete with whistle": ("Sportif au sifflet", "رياضي مع صفّارة"),
    "Young man in a hoodie": ("Jeune homme en sweat", "شاب بكنزة بقبعة"), "Young woman with long hair": ("Jeune femme aux cheveux longs", "شابة بشعر طويل"),
    "Boy": ("Garçon", "ولد"), "Girl with pigtails": ("Fille à couettes", "بنت بضفيرتين"), "Grandfather with glasses": ("Grand-père à lunettes", "جدّ بنظارات"),
    "Grandmother with a bun": ("Grand-mère au chignon", "جدّة بكعكة شعر"), "Tech fan with headphones": ("Geek au casque", "محب للتقنية بسماعات"),
    "Developer with a bob": ("Développeuse au carré", "مبرمجة بشعر قصير"), "Woman with hijab": ("Femme voilée", "امرأة محجبة"),
    "Woman with hijab and glasses": ("Femme voilée à lunettes", "امرأة محجبة بنظارات"), "Woman with afro": ("Femme aux cheveux afro", "امرأة بشعر أفرو"),
    "Woman with braids": ("Femme aux tresses", "امرأة بضفائر"), "Man with a beard": ("Homme barbu", "رجل بلحية"),
    "Man in a flannel shirt": ("Homme en chemise à carreaux", "رجل بقميص مربعات"), "Woman with curly hair": ("Femme aux cheveux bouclés", "امرأة بشعر مجعّد"),
    "Chef": ("Chef cuisinier", "طاهٍ"), "Professional in a blazer": ("Professionnelle en blazer", "موظفة ببدلة"), "Teen with a cap": ("Ado à casquette", "مراهق بقبعة"),
})


def gettext(text, lang, **values):
    if lang in _IDX and text in UI:
        text = UI[text][_IDX[lang]]
    return text.format(**values) if values else text


def label(value, lang):
    value = str(value)
    return gettext(LABELS.get(value, value.replace("_", " ").capitalize()), lang)


def meal_name(meal, lang):
    t = MEALS.get(meal["id"])
    return t[_IDX[lang] * 2] if t and lang in _IDX else meal["name"]


def meal_desc(meal, lang):
    t = MEALS.get(meal["id"])
    return t[_IDX[lang] * 2 + 1] if t and lang in _IDX else meal["description"]


def meal_name_by_id(meal_id, english, lang):
    t = MEALS.get(meal_id)
    return t[_IDX[lang] * 2] if t and lang in _IDX else english


def ingredient(name, lang):
    t = INGREDIENTS.get(name)
    return t[_IDX[lang]] if t and lang in _IDX else name


def rule_text(rule_name, english, lang):
    t = RULES.get(rule_name)
    return t[_IDX[lang]] if t and lang in _IDX else english


def criterion(key, english, lang):
    if lang not in _IDX:
        return english
    i = _IDX[lang]
    if key in CRITERIA:
        return CRITERIA[key][i]
    if key.startswith("tag:") and key[4:] in TAGS:
        return TAGS[key[4:]][i]
    if key.startswith("no_allergen:") and key[12:] in ALLERGEN_NAMES:
        return ("sans " if i == 0 else "بدون ") + ALLERGEN_NAMES[key[12:]][i]
    if key.startswith(("max:", "min:")):
        from backend.nutrition import NUTRIENT_LABELS
        bound, field, value = key.split(":")
        name, unit = NUTRIENT_LABELS[field]
        return f"{gettext(name, lang)} {'≤' if bound == 'max' else '≥'} {value} {gettext(unit, lang)}"
    if key.startswith("category:"):
        return label(key[9:], lang)
    return english


def explain(item, context, lang):
    """Translated 'why' sentence (same logic as adapt_meal.explain for English)."""
    if lang not in _IDX:
        return item["explanation"]
    names = item.get("reason_rules", [])[:2]
    if not names:
        m = item["meal"]
        if context:
            return gettext("Suggested because it fits your {t}-minute window ({p} min).", lang,
                           t=context["available_time"], p=m["prep_time"])
        return gettext("Suggested to complete your plan.", lang)
    parts = [rule_text(n, n, lang) for n in names]
    return gettext("Recommended because {reasons}.", lang,
                   reasons=" ; ".join(parts) if lang == "fr" else "؛ و".join(parts))


def money(eur, lang):
    if lang == "fr":
        return f"{eur:.2f} €".replace(".", ",")
    if lang == "ar":
        return f"{eur:.2f} €"
    return f"€{eur:.2f}"
