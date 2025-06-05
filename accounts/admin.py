from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    StrategicPriority,
    Objective,
    Question,
    Answer,
    UserProfile,
    TeamMember,
    QuestionnaireSubmission,
)

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ('question', 'level', 'get_user')

    def get_user(self, obj):
        return obj.submission.user if obj.submission else '—'
    get_user.short_description = 'User'

@admin.register(QuestionnaireSubmission)
class QuestionnaireSubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'submitted_at', 'is_submitted', 'view_analysis_link', 'view_dashboard_link')
    list_filter = ('is_submitted',)
    search_fields = ('user__username',)
    inlines = [AnswerInline]

    def view_analysis_link(self, obj):
        if obj.is_submitted:
            url = reverse('admin_analysis', args=[obj.id])
            return format_html('<a href="{}">📊 View Analysis</a>', url)
        return '-'

    def view_dashboard_link(self, obj):
        if obj.is_submitted:
            url = reverse('admin_dashboard', args=[obj.id])
            return format_html('<a href="{}">📊 Dashboard</a>', url)
        return '-'
    view_dashboard_link.short_description = "Dashboard"

admin.site.register(StrategicPriority)
admin.site.register(Objective)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(UserProfile)
admin.site.register(TeamMember)

