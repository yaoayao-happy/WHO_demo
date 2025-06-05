
import pandas as pd
from accounts.models import StrategicPriority, Objective, Question

data = []

for sp in StrategicPriority.objects.all():
    for obj in sp.objective_set.all():
        for q in obj.question_set.all():
            data.append({
                "sp_title": sp.title,
                "objective_title": obj.title,
                "objective_weight": obj.weight,
                "question_text": q.text,
                "html_text": q.html_text or "",
                "allow_na": q.allow_na,
                "phase": obj.phase,
            })

df = pd.DataFrame(data)
df.to_excel("questionnaire_backup.xlsx", index=False)
print("✅ Exported questionnaire to 'questionnaire_backup.xlsx'")
