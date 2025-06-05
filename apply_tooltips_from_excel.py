import pandas as pd
from accounts.models import Question
from django.db import transaction
import re

# 加载 Excel 的关键词和提示内容
df = pd.read_excel("keyword_tooltips.xlsx")

tooltip_dict = {}
for _, row in df.iterrows():
    keyword = str(row['keyword']).strip()
    title = str(row['title']).strip()
    content = str(row['content']).strip()
    tooltip_dict[keyword] = (title, content)

# HTML 模板
def make_tooltip(keyword, title, content):
    return (
        f'<a href="javascript:void(0)" tabindex="0" role="button" '
        f'data-bs-toggle="popover" title="{title}" data-bs-content="{content}">{keyword}</a>'
    )

updated = 0

with transaction.atomic():
    for q in Question.objects.all():
        original = q.text
        modified = original

        for kw, (title, content) in tooltip_dict.items():
            # 使用正则匹配整个词，忽略大小写（避免在 html 中重复替换）
            pattern = re.compile(rf'\b({re.escape(kw)})\b', re.IGNORECASE)
            modified = pattern.sub(lambda m: make_tooltip(m.group(1), title, content), modified)

        q.html_text = modified
        q.save()
        updated += 1

print(f"✅ Processed and updated {updated} questions with tooltip replacements.")
