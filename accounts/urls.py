from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),  # ✅ 添加注册路由
    path('admin_home/', views.admin_home, name='admin_home'),
    path('user_home/', views.user_home, name='user_home'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.user_profile_view, name='user_profile'),
    path('team/', views.team_member_list_view, name='team_member_list'),
    path('team/add/', views.add_team_member_view, name='add_team_member'),
    path('questionnaire/', views.questionnaire_view, name='questionnaire'),
    path('questionnaire/history/', views.questionnaire_history, name='questionnaire_history'),
    path('questionnaire/view/<int:submission_id>/', views.questionnaire_detail, name='questionnaire_detail'),
    path('analysis/', views.analysis_view, name='analysis'),
    # path('admin/analysis/<int:submission_id>/', views.admin_analysis_view, name='admin_analysis'),
    path('submission_analysis/<int:submission_id>/', views.admin_analysis_view, name='admin_analysis'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('submission_dashboard/<int:submission_id>/', views.admin_dashboard_view, name='admin_dashboard'),
    path('planning/', views.planning_view, name='planning'),
]
