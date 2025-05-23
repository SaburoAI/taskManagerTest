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
    path("保護者ホーム/", ParentHomeView.as_view(), name="parentHome"),
    path('テスト結果/<int:test_id>/', views.get_results, name='get_results'),
    path('テスト結果/<int:test_id>/<int:student_id>/', get_results, name='get_results_with_student'),
    path('講師ホーム/', TeacherHomeView.as_view(), name="teacherHome"),
    path('生徒一覧/', TaskAddStuListView.as_view(), name="task_add_student_list"),
    
    path('タスクの期限追加/<int:student_u_id>/', TeacherTaskAddView.as_view(), name="teacher_task_add"),
    path('add_task_deadline/', views.add_task_deadline, name='add_task_deadline'),
    
    path('ライブラリ/', LibraryView.as_view(), name='library'),
    path('カリキュラム/<str:curriculum_name>/', CurrHomeView.as_view(), name='curriculum_home'),
    path('get_task_attributes/', get_task_attributes, name='get_task_attributes'),
    path('テスト/<str:curriculum_name>/', TestMenuView.as_view(), name='test_menu'),
    path('delete_task/', delete_task, name='delete_task'),

    
    path('マイページ/', MypageView.as_view(), name='my_page'),
    

    path('生徒カルテ/<str:student_id>/',StudentStatusView.as_view(), name='student_status'),
    path('add_message/', views.add_message, name='add_message'),
    path('update_tasks/', update_tasks, name='update_tasks'),
    path('save_oral_check/', save_oral_check, name='save_oral_check'),


    path("教科一覧/", SubjectHomeView.as_view(), name="subject_list"),
    path("テスト一覧/", TestHomeView.as_view(), name="test_list"),
    path('submit_answers/', submit_answers, name='submit_answers'),


    path('save_subjects/', SaveSubjectsView.as_view(), name='save_subjects'),
    path('save_tests/', SaveTestsView.as_view(), name='save_tests'),

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
    
    path('qr-reader/', QRReaderView.as_view(), name='qr_reader'),
    path('qr-result/', views.qr_result, name='qr_result'),
    path('keep-session-alive/', keep_session_alive, name='keep_session_alive'),
    path('get-latest-logs/', get_latest_logs, name='get_latest_logs'),

    
    
    
]
