from django.db import models
from django.contrib.auth.models import User

   

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    country = models.CharField(max_length=100)
    national_team_leader = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

class TeamMember(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    competent_authority = models.CharField(max_length=100)
    contact_email = models.EmailField()

    def __str__(self):
        return self.name

class StrategicPriority(models.Model):
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title

class Objective(models.Model):
    priority = models.ForeignKey(StrategicPriority, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    weight = models.FloatField(default=1.0)
    phase = models.IntegerField(choices=[(1, 'Phase 1'), (2, 'Phase 2'), (3, 'Phase 3'), (4, 'Phase 4'), (5, 'Phase 5')], default=1)    

    def __str__(self):
        return f"{self.priority.title} - {self.title}"

class Question(models.Model):
    objective = models.ForeignKey(Objective, on_delete=models.CASCADE)
    text = models.TextField()
    html_text = models.TextField(blank=True, null=True)
    allow_na = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class QuestionnaireSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_submitted = models.BooleanField(default=False)

class Answer(models.Model):
    submission = models.ForeignKey(QuestionnaireSubmission, on_delete=models.CASCADE, null=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    level = models.CharField(max_length=10, null=True, blank=True)


class Planning(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    objective = models.ForeignKey(Objective, on_delete=models.CASCADE)
    start_quarter = models.CharField(max_length=10)  # e.g. '2026Q1'
    end_quarter = models.CharField(max_length=10)    # e.g. '2027Q4'
