
import pandas as pd
from accounts.models import StrategicPriority, Objective, Question
from django.db import transaction

df = pd.read_excel("questionnaire_backup.xlsx")

with transaction.atomic():
    StrategicPriority.objects.all().delete()
    Objective.objects.all().delete()
    Question.objects.all().delete()

    sp_cache = {}
    obj_cache = {}

    for _, row in df.iterrows():
        sp_title = row['sp_title']
        obj_title = row['objective_title']
        q_text = row['question_text']
        html_text = row['html_text']
        allow_na = bool(row['allow_na'])
        weight = float(row.get("objective_weight", 1.0))
        phase = int(row.get("objective_phase", 1))

        if sp_title not in sp_cache:
            sp = StrategicPriority.objects.create(title=sp_title)
            sp_cache[sp_title] = sp
        else:
            sp = sp_cache[sp_title]

        key = (sp_title, obj_title)
        if key not in obj_cache:
            obj = Objective.objects.create(title=obj_title, priority=sp, weight=weight, phase=phase)
            obj_cache[key] = obj
        else:
            obj = obj_cache[key]

        Question.objects.create(objective=obj, text=q_text, html_text=html_text, allow_na=allow_na)

print("✅ Imported questionnaire from 'questionnaire_backup.xlsx'")
