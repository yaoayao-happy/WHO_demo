from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.forms import Form, ChoiceField, RadioSelect

from .models import (
    Question,
    UserProfile,
    TeamMember,
    StrategicPriority,
    Answer,
    QuestionnaireSubmission,
    Objective
)

def get_color(score):
    if score >= 80:
        return "#009966"  # Green
    elif score >= 60:
        return "#99cc00"
    elif score >= 40:
        return "#ffcc00"
    elif score >= 20:
        return "#ff9900"
    else:
        return "#ff3333"



def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.is_staff:
                return redirect('admin_home')
            else:
                return redirect('user_home')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email    = request.POST['email']
        pwd1     = request.POST['password1']
        pwd2     = request.POST['password2']
        country = request.POST['country']
        leader = request.POST['leader']

        if pwd1 != pwd2:
            return render(request, 'register.html', {'error': 'Passwords do not match'})
        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'Username already exists'})
        user = User.objects.create_user(username=username, email=email, password=pwd1)
        UserProfile.objects.create(user=user, country=country, national_team_leader=leader)
        return redirect('login')
    return render(request, 'register.html')

def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def user_profile_view(request):
    profile = UserProfile.objects.get(user=request.user)
    return render(request, 'user_profile.html', {'profile': profile})

@login_required
def admin_home(request):
    return render(request, 'admin_home.html')

@login_required
def user_home(request):
    profile = UserProfile.objects.get(user=request.user)
    return render(request, 'user_home.html', {'profile': profile})

@login_required
def team_member_list_view(request):
    members = TeamMember.objects.filter(user=request.user)
    return render(request, 'team_member_list.html', {'members': members})

@login_required
def add_team_member_view(request):
    if request.method == 'POST':
        name = request.POST['name']
        position = request.POST['position']
        authority = request.POST['authority']
        email = request.POST['email']
        TeamMember.objects.create(
            user=request.user,
            name=name,
            position=position,
            competent_authority=authority,
            contact_email=email
        )
        return redirect('team_member_list')
    return render(request, 'add_team_member.html')

LEVEL_CHOICES = [(str(i), f'Level {i}') for i in range(1, 6)]
@login_required
def questionnaire_view(request):
    priorities = StrategicPriority.objects.prefetch_related('objective_set__question_set')
    
    if request.method == 'POST':
        action = request.POST.get('action')  # 'save' or 'submit'
        is_submit = (action == 'submit')

        draft_id = request.POST.get('draft_id')
        if draft_id:
            submission = QuestionnaireSubmission.objects.get(id=draft_id, user=request.user)
            submission.answer_set.all().delete()
        else:
            submission = QuestionnaireSubmission.objects.create(user=request.user)

        submission.is_submitted = is_submit
        submission.save()

        for q in Question.objects.all():
            value = request.POST.get(f'question_{q.id}')
            if value:
                Answer.objects.create(
                    submission=submission,
                    question=q,
                    level=value
                )

        all_questions = Question.objects.all()
        answered_qids = [int(k.split('_')[1]) for k in request.POST if k.startswith('question_')]
        
        if is_submit and len(answered_qids) < all_questions.count():
            messages.error(request, "Please answer all questions before submitting.")
            return redirect('questionnaire')

        if is_submit:
            messages.success(request, "Your questionnaire was submitted.")
            QuestionnaireSubmission.objects.filter(user=request.user, is_submitted=False).exclude(id=submission.id).delete()
        else:
            messages.success(request, "Your progress was saved. You can continue later.")
        
        return redirect('questionnaire')

    try:
        draft = QuestionnaireSubmission.objects.filter(
            user=request.user,
            is_submitted=False
        ).latest('submitted_at')  # 取最近草稿

        answers = {a.question_id: a.level for a in draft.answer_set.all()}
        draft_id = draft.id
        messages.info(request, "You are continuing your saved draft.")
    except QuestionnaireSubmission.DoesNotExist:
        draft_id = None
        answers = {}

    return render(request, 'questionnaire.html', {
        'priorities': priorities,
        'level_choices': LEVEL_CHOICES,
        'answers': answers,
        'draft_id': draft_id,
    })


@login_required
def questionnaire_history(request):
    submissions = QuestionnaireSubmission.objects.filter(user=request.user).order_by('-submitted_at')
    return render(request, 'questionnaire_history.html', {'submissions': submissions})

@login_required
def questionnaire_detail(request, submission_id):
    submission = get_object_or_404(QuestionnaireSubmission, pk=submission_id, user=request.user)
    answers = {a.question_id: a.level for a in submission.answer_set.all()}
    priorities = StrategicPriority.objects.prefetch_related('objective_set__question_set')

    return render(request, 'questionnaire_readonly.html', {
        'priorities': priorities,
        'answers': answers,
        'submitted': True,
        'submitted_at': submission.submitted_at,
        'level_choices': [(str(i), f'Level {i}') for i in range(1, 6)],
    })

from collections import defaultdict

@login_required
def analysis_view(request):
    submission = QuestionnaireSubmission.objects.filter(user=request.user, is_submitted=True).order_by('-submitted_at').first()
    if not submission:
        return render(request, 'analysis.html', {'message': "No submissions yet."})

    # Prepare: priority -> list of (objective, average_score, weight)
    priority_barcharts = []
    report = []
    total_weight = 0
    weighted_score_sum = 0

    for priority in StrategicPriority.objects.all():
        priority_objectives = []
        priority_weight = 0
        priority_weighted_score = 0
        bars = []

        for obj in priority.objective_set.all():
            answers = Answer.objects.filter(
                submission=submission,
                question__objective=obj
            )

            scores = []
            for ans in answers:
                if ans.level == "NA":
                    scores.append(1)  # Not Applicable 记作1分
                elif ans.level:
                    scores.append(int(ans.level))
            if scores:
                avg_score = sum(scores) / len(scores)
            else:
                avg_score = 0

            weight = obj.weight or 1
            priority_objectives.append((obj.title, avg_score, weight))

            priority_weight += weight
            priority_weighted_score += avg_score * weight
            
            bars.append({
                'label': obj.title.split()[0],  # e.g. SO 1.1
                'value': round(priority_weighted_score*100, 2),
            })

        if priority_weight > 0:
            priority_score = priority_weighted_score / priority_weight
        else:
            priority_score = 0

        total_weight += priority_weight
        weighted_score_sum += priority_weighted_score

        priority_barcharts.append({
            'title': priority.title,
            'data': bars,
        })

        report.append({
            'priority': priority.title,
            'objectives': priority_objectives,
            'priority_score': round(priority_score, 2)
        })

    overall_score = round(weighted_score_sum / total_weight, 2) if total_weight > 0 else 0

    return render(request, 'analysis.html', {
        "priority_barcharts": priority_barcharts,
        'submission': submission,
        'report': report,
        'overall_score': overall_score,
    })


@staff_member_required
def admin_analysis_view(request, submission_id):
    submission = get_object_or_404(QuestionnaireSubmission, id=submission_id)
    # submission = get_object_or_404(QuestionnaireSubmission.objects.select_related('user'), id=submission_id)

    priority_barcharts = []
    report = []
    total_weight = 0
    weighted_score_sum = 0

    for priority in StrategicPriority.objects.all():
        priority_objectives = []
        priority_weight = 0
        priority_weighted_score = 0
        bars = []

        for obj in priority.objective_set.all():
            answers = Answer.objects.filter(
                submission=submission,
                question__objective=obj
            )

            scores = []
            for ans in answers:
                if ans.level == "NA":
                    scores.append(1)  # Not Applicable 记作1分
                elif ans.level:
                    scores.append(int(ans.level))
            if scores:
                avg_score = sum(scores) / len(scores)
            else:
                avg_score = 0

            weight = obj.weight or 1
            priority_objectives.append((obj.title, avg_score, weight))

            priority_weight += weight
            priority_weighted_score += avg_score * weight
            
            bars.append({
                'label': obj.title.split()[0],  # e.g. SO 1.1
                'value': round(priority_weighted_score*100, 2),
            })

        if priority_weight > 0:
            priority_score = priority_weighted_score / priority_weight
        else:
            priority_score = 0

        total_weight += priority_weight
        weighted_score_sum += priority_weighted_score

        priority_barcharts.append({
            'title': priority.title,
            'data': bars,
        })

        report.append({
            'priority': priority.title,
            'objectives': priority_objectives,
            'priority_score': round(priority_score, 2)
        })

    overall_score = round(weighted_score_sum / total_weight, 2) if total_weight > 0 else 0

    return render(request, 'analysis.html', {       
        "priority_barcharts": priority_barcharts, 
        'submission': submission,
        'report': report,
        'overall_score': overall_score,
    })



@login_required
def dashboard_view(request):
    submission = QuestionnaireSubmission.objects.filter(user=request.user, is_submitted=True).order_by('-submitted_at').first()
    if not submission:
        return render(request, 'dashboard.html', {'phases': []})

    # 筛出每个 objective 的分数
    phase_data = {i: [] for i in range(1, 6)}

    all_objectives = Objective.objects.select_related('priority').all()
    phase_scores = defaultdict(lambda: {"weighted_sum": 0, "total_weight": 0})
    for obj in all_objectives:
        answers = Answer.objects.filter(submission=submission, question__objective=obj)
        scores = []
        for ans in answers:
            if ans.level == "NA":
                scores.append(100)
            elif ans.level:
                scores.append(int(ans.level) * 20)  # 转换为百分比
        avg = sum(scores) / len(scores) if scores else 0
        weight = obj.weight or 1
        phase_scores[obj.phase]["weighted_sum"] += avg * weight
        phase_scores[obj.phase]["total_weight"] += weight
        phase_data[obj.phase].append({
            'code': obj.title.split()[0],  # 如 “SO 1.1”
            'title': obj.title,
            'color': get_color(avg),
        })

    phase_bars = []
    for phase in range(1, 6):
        ps = phase_scores[phase]
        avg = ps["weighted_sum"] / ps["total_weight"] if ps["total_weight"] > 0 else 0
        phase_bars.append({"label": f"Phase {phase}", "value": round(avg, 1)})

    context = {
        'submission': submission,
        "phase_chart": phase_bars,
        'phases': [phase_data[i] for i in range(1, 6)]
    }
    return render(request, 'dashboard.html', context)


@staff_member_required
def admin_dashboard_view(request, submission_id):
    submission = get_object_or_404(QuestionnaireSubmission, id=submission_id)

    # 筛出每个 objective 的分数
    phase_data = {i: [] for i in range(1, 6)}

    all_objectives = Objective.objects.select_related('priority').all()
    phase_scores = defaultdict(lambda: {"weighted_sum": 0, "total_weight": 0})
    for obj in all_objectives:
        answers = Answer.objects.filter(submission=submission, question__objective=obj)
        scores = []
        for ans in answers:
            if ans.level == "NA":
                scores.append(100)
            elif ans.level:
                scores.append(int(ans.level) * 20)  # 转换为百分比
        avg = sum(scores) / len(scores) if scores else 0
        weight = obj.weight or 1
        phase_scores[obj.phase]["weighted_sum"] += avg * weight
        phase_scores[obj.phase]["total_weight"] += weight
        phase_data[obj.phase].append({
            'code': obj.title.split()[0],  # 如 “SO 1.1”
            'title': obj.title,
            'color': get_color(avg),
        })

    phase_bars = []
    for phase in range(1, 6):
        ps = phase_scores[phase]
        avg = ps["weighted_sum"] / ps["total_weight"] if ps["total_weight"] > 0 else 0
        phase_bars.append({"label": f"Phase {phase}", "value": round(avg, 1)})

    context = {
        'submission': submission,
        "phase_chart": phase_bars,
        'phases': [phase_data[i] for i in range(1, 6)]
    }
    return render(request, 'dashboard.html', context)


@login_required
def planning_view(request):
    user = request.user
    submission = QuestionnaireSubmission.objects.filter(user=user, is_submitted=True).order_by('-submitted_at').first()

    # 构造时间区间 2025Q3 到 2030Q4
    years = range(2025, 2031)
    quarters = [f"{y}Q{q}" for y in years for q in range(1, 5)]

    planning_data = []
    for obj in Objective.objects.select_related('priority').all():
        answers = Answer.objects.filter(submission=submission, question__objective=obj)
        scores = [100 if a.level == "NA" else int(a.level) * 20 for a in answers if a.level]
        avg = sum(scores) / len(scores) if scores else 0

        planning_data.append({
            "id": obj.id,
            "priority": obj.priority.title,
            "objective": obj.title,
            "phase": obj.phase,
            "score": round(avg, 1),
            "start": "2026Q1",  # 默认值（你也可以根据 phase 决定）
            "end": "2027Q4",
        })

    return render(request, "planning.html", {
        "planning_data": planning_data,
        "quarters": quarters
    })
