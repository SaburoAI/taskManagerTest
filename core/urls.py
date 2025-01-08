from django.urls import path
from.views import *
from.import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.root_view, name='root'),
    path('create_user/', create_user, name='create_user'),
    path('ログアウト/', views.user_logout, name='logout'),
    path('ログイン/', LoginView.as_view(), name='login'),
    path('生徒ホーム/', StudentHomeView.as_view(), name="studentHome"),
    path('テスト結果/<int:test_id>/', views.get_results, name='get_results'),
    path('テスト結果/<int:test_id>/<int:student_id>/', get_results, name='get_results_with_student'),
    path('講師ホーム/', TeacherHomeView.as_view(), name="teacherHome"),
    path('生徒一覧/', TaskAddStuListView.as_view(), name="task_add_student_list"),
    path('タスクの期限追加/<str:student_name>/', TeacherTaskAddView.as_view(), name="teacher_task_add"),
    path('ライブラリ/', LibraryView.as_view(), name='library'),
    path('カリキュラム/<str:curriculum_name>/', CurrHomeView.as_view(), name='curriculum_home'),
    path('get-task-attributes/', get_task_attributes, name='get_task_attributes'),
    path('マイページ/', MypageView.as_view(), name='my_page'),
    path("教科一覧", SubjectHomeView.as_view(), name="subject_list"),
    path('save_subjects/', SaveSubjectsView.as_view(), name='save_subjects'),


    path('add-member-to-task/', AddMemberToTaskView.as_view(), name='add_member_to_task'),
    path('save-tasks/', SaveTasksView.as_view(), name='save-tasks'),
    path('生徒画面/<str:student_id>/', StudentDetailView.as_view(), name='student_detail'),
    path('カリキュラム編集/<str:curriculum_name>/', CurriculumDetailView.as_view(), name='curriculum_detail'),
    path('new_task_add/', NewTaskAddView.as_view(), name='new_task_add'),
    path('タスク予定作成/', TaskAddView.as_view(), name='task_add'),
    path('update-task-status/', UpdateTaskStatusView.as_view(), name='update_task_status'),
    path('task_edit/<int:task_id>/', TaskEditView.as_view(), name='task_edit'),
    path('task_delete/<int:task_id>/', TaskDeleteView.as_view(), name='task_delete'),
    path('カリキュラム作成/', views.create_curriculum, name='create_curriculum'),
    path('update_report_data/', views.update_report_data, name='update_report_data'),
    path('生徒画面/<int:student_id>/update_report_data/', update_report_data, name='update_report_data_with_student'),
    path('update_task_status/<int:task_id>/', views.update_task_status, name='update_task_status'),
    path('update_task_status/<int:task_id>/<int:student_id>/', update_task_status, name='update_task_status_with_student'),
    path('update_status/<int:task_id>/', views.update_status, name='update_status'),
]
