from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_GET
from django.contrib.auth.views import PasswordChangeView
from core.models import *
from core.forms import *
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from core.contextMaker import *
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json, logging, os
from datetime import datetime
import pytz
from django.utils.timezone import localtime
from core.mixins import CustomLoginRequiredMixin, custom_login_required




#講師側ビュー
class TeacherHomeView(CustomLoginRequiredMixin,TemplateView):
    template_name = "teacher_pages/teacher_home.html"

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        school_id = self.request.session.get('school_id')
        user_id = self.request.session.get('user_id')
        account = get_account_info(self.request)
        user_id = account.get('u_id')
        ctxt.update(get_teacher_home_context(school_id, user_id))
        ctxt.update(get_account_info(self.request))
        qr_code_data = generate_qr_code(user_id)
        ctxt['qr_code'] = qr_code_data

        return ctxt


class TaskAddStuListView(CustomLoginRequiredMixin,TemplateView):
    template_name = "teacher_pages/task_add_student_list.html"

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        school_id = self.request.session.get('school_id')
        user_id = self.request.session.get('user_id')
        ctxt.update(get_account_info(self.request))
        ctxt.update(get_teacher_home_context(school_id, user_id))
        return ctxt
    


class TeacherTaskAddView(CustomLoginRequiredMixin, TemplateView):
    template_name = 'teacher_pages/task_add_view.html'

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt.update(get_account_info(self.request))
        


        # URLから渡されたstudent_nameを取得
        student_name = self.kwargs.get('student_u_id')
        if not student_name:
            return ctxt

        # student_nameを使用してTblUserから該当のu_idを取得
        student_user = get_object_or_404(TblUser, u_id=student_name)
        student_id = student_user.u_id

        tasks = TblTask.objects.filter(u=student_user).order_by('sub_id')

        curr_ids = tasks.values_list('curr', flat=True).distinct()
        curriculums = TblCurriculum.objects.filter(id__in=curr_ids)
        curr_details = TblCurrDetail.objects.filter(curr_id__in=curr_ids)

        subjects = TblCurriculum.objects.filter(id__in=curr_ids).values_list('sub_name', flat=True).distinct().order_by('sub_id')
        subject_curriculum_pairs = list(zip(subjects, curriculums))

        selected_curriculum_id = self.request.GET.get('curriculum_id', curriculums.first().id if curriculums.exists() else None)
        if selected_curriculum_id:
            tasks = tasks.filter(curr_id=selected_curriculum_id)

        tasks_by_tag = {}
        for task in tasks:
            tag = task.tag
            if tag not in tasks_by_tag:
                tasks_by_tag[tag] = []
            details = TblCurrDetail.objects.filter(curr=task.curr, sub_id=task.sub_id, task_id=task.task_id)
            for detail in details:
                tasks_by_tag[tag].append({
                    'task_name': detail.task_name,
                    'status': task.get_status_display(),
                    'priority': task.get_priority_display(),
                    'grade': task.get_grade_display(),
                    'id': task.id,
                })

        ctxt['tasks'] = tasks
        ctxt['curriculums'] = curriculums
        ctxt['curr_details'] = curr_details
        ctxt['subjects'] = subjects
        ctxt['subject_curriculum_pairs'] = subject_curriculum_pairs
        ctxt['tasks_by_tag'] = tasks_by_tag
        
        return ctxt




@custom_login_required
def create_curriculum(request):
    if request.method == 'POST':
        form = CurriculumForm(request.POST)
        if form.is_valid():
            curr_name = form.cleaned_data['curr_name']
            subjects = form.cleaned_data['subjects']
            
            # ログインしているユーザーがu_idかs_idかで分岐
            school_id = request.session.get('school_id')
            user_id = request.session.get('user_id')
            
            if school_id:
                school = TblSchoolid.objects.get(id=school_id)
            elif user_id:
                user = TblUser.objects.get(u_id=user_id)
                school = TblSchoolid.objects.get(id=user.s_id)
            else:
                # school_idもuser_idもない場合のエラーハンドリング
                return render(request, 'teacher_pages/teacher_home.html', {'form': form, 'error': 'School ID or User ID not found'})

            # 最初のカリキュラムを作成
            curriculum = TblCurriculum.objects.create(
                s=school,
                curr_name=curr_name,
                sub_id=0,
                sub_name='全体',
                next_num=1,
            )
            
            # 最初のタスクをTblCurrDetailに追加
            TblCurrDetail.objects.create(
                s=school,
                curr=curriculum,
                sub_id=0,
                task_id=1,
                task_name='すべてのタスクを完了させる',
                next_num=2,
            )
            teacher = TblUser.objects.filter(s=school).first()
            TblTask.objects.create(
                u=teacher,
                curr=curriculum,
                sub_id=0,
                task_id=1,
                grade=1,
                priority=1,
                tag='全体',
            )
            
            # 入力された教科名の回数だけデータベースに保存
            next_num = 1
            for subject in subjects:
                TblCurriculum.objects.create(
                    s=school,
                    curr_name=curr_name,
                    sub_id=next_num,
                    sub_name=subject.sub_name,
                    next_num=next_num
                )
                next_num += 1

            return redirect('teacherHome')
    else:
        form = CurriculumForm()

    return render(request, 'teacher_pages/teacher_home.html', {'form': form})

class StudentDetailView(CustomLoginRequiredMixin, TemplateView):
    template_name = "student_pages/student_home.html"

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        student_id = self.kwargs.get('student_id')
        ctxt.update(get_account_info(self.request))
        ctxt.update(get_home_context(student_id))
        

        if student_id:
            try:
                user = TblUser.objects.get(u_id=student_id)
                ctxt['user_name'] = user.u_name
                ctxt['user_auth'] = user.u_auth
                ctxt['test_result_form'] = TestResultForm(user=user)
                ctxt['student_id'] = student_id
            except TblUser.DoesNotExist:
                ctxt['error'] = '指定されたユーザーは存在しません。'

        return ctxt
    
    def post(self, request, *args, **kwargs):
        student_id = self.kwargs.get('student_id')
        
        try:
            user = TblUser.objects.get(u_id=student_id)
        except TblUser.DoesNotExist:
            return redirect('studentHome')  # ユーザーが存在しない場合のリダイレクト先を指定
        
        form = TestResultForm(request.POST, user=user)
        
        if form.is_valid():
            form.save()
            return redirect('student_detail', student_id=student_id)
        
        ctxt = self.get_context_data(**kwargs)
        ctxt['test_result_form'] = form
        return self.render_to_response(ctxt)


class CurriculumDetailView(CustomLoginRequiredMixin, TemplateView):
    template_name = "teacher_pages/curr_detail.html"
    
    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        curriculum_name = self.kwargs.get('curriculum_name')
        ctxt.update(get_account_info(self.request))

        # TblCurriculumからcurriculum_nameに一致するレコードを取得
        curriculums = TblCurriculum.objects.filter(curr_name=curriculum_name).order_by('sub_id')

        
        # subjects辞書を作成
        curr_info = {curriculum_name: [curriculum.sub_name for curriculum in curriculums]}
        subjects = [curriculum.sub_name for curriculum in curriculums]
        
        # tasks辞書を作成
        tasks = {}
        
        for curriculum in curriculums:
            task_details = TblCurrDetail.objects.filter(curr=curriculum).order_by('task_id')
            tasks[curriculum.sub_name] = [
                {
                    'id': task.id,
                    'sub_id': task.sub_id,
                    'task_id': task.task_id,
                    'task_name': task.task_name,
                    'task_enable': 'true' if task.task_enable else 'false',
                    'next_num': task.next_num,
                }
                for task in task_details
            ]

        ctxt['curriculum_name'] = curriculum_name
        ctxt['curr_info'] = curr_info
        ctxt['subjects'] = subjects
        ctxt['tasks'] = tasks
        return ctxt



class TaskEditView(View):
    def post(self, request, *args, **kwargs):
        task_id = kwargs.get('task_id')
        task = TblCurrDetail.objects.get(id=task_id)
        data = json.loads(request.body)
        form = TaskEditForm(data, instance=task)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Task updated successfully.'})
        return JsonResponse({'success': False, 'errors': form.errors})

class NewTaskAddView(View):
    def post(self, request, *args, **kwargs):
        school_id = request.session.get('school_id')
        user_id = request.session.get('user_id')
            
        if school_id:
            school = TblSchoolid.objects.get(id=school_id)
        elif user_id:
            user = TblUser.objects.get(u_id=user_id)
            school = TblSchoolid.objects.get(id=user.s_id)
        else:
            # school_idもuser_idもない場合のエラーハンドリング
            return render(request, 'teacher_pages/teacher_home.html', {'form': form, 'error': 'School ID or User ID not found'})
            
        try:
            data = json.loads(request.body)
            curriculum_name = data.get('curriculum_name')
            subject_name = data.get('subject_name')
            task_name = data.get('task_name')
            task_enable = data.get('task_enable')
            order = data.get('order')

            if subject_name is None:
                return JsonResponse({'success': False, 'error': 'Subject name is required'})

            curriculum = TblCurriculum.objects.filter(curr_name=curriculum_name, s=school,sub_name=subject_name).first() #filterで取得したものはリストで返ってくるので、first()で最初の要素を取得する必要がある
            if not curriculum:
                return JsonResponse({'success': False, 'error': 'Curriculum not found'})
            subject = TblCurriculum.objects.filter(curr_name=curriculum_name,sub_name=subject_name).first()
            if not subject:
                return JsonResponse({'success': False, 'error': 'Subject not found'})

            task_data = {
                's': school,
                'curr': curriculum,
                'sub_id': subject.sub_id,
                'task_id': order,
                'task_name': task_name,
                'next_num': order + 1,
                'task_enable': task_enable
            }

            form = TaskAddForm(task_data)
            if form.is_valid():
                form.save()
                return JsonResponse({'success': True, 'message': 'Task added successfully.'})
            return JsonResponse({'success': False, 'errors': form.errors})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class TaskDeleteView(View):
    def post(self, request, task_id, *args, **kwargs):
        try:
            task = TblCurrDetail.objects.get(id=task_id)
            task.delete()
            return JsonResponse({'success': True, 'message': 'Task deleted successfully.'})
        except TblCurrDetail.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Task not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def qr_result(request):
    if request.method == 'POST':
        try:
            # リクエストボディをJSONとして読み取る
            data = json.loads(request.body)
            qr_data = data.get('qr_data', '')  # 'qr_data' を取得

            # qr_data が文字列の場合、辞書に変換
            if isinstance(qr_data, str):
                qr_data = json.loads(qr_data)

            # qr_data が辞書形式か確認
            if not isinstance(qr_data, dict):
                return JsonResponse({'error': 'qr_dataが辞書形式ではありません'}, status=400)

            # 必要なデータを取得
            u_id = qr_data.get('u_id')
            user = TblUser.objects.get(u_id=u_id)

            # 今日の日付を取得
            today = timezone.now().date()

            # 今日の入室ログを取得
            log = EntryExitLog.objects.filter(user=user, entry_time__date=today).order_by('-entry_time').first()

            if log and log.status == 'entered':
                # 既に入室中の場合、退出処理を行う
                log.exit_time = timezone.now()
                log.status = 'exited'
                log.save()
                return JsonResponse({'message': '退出処理が完了しました', 'log_id': log.id})
            else:
                # 入室処理を行う
                log = EntryExitLog.objects.create(
                    user=user,
                    entry_time=timezone.now(),
                    status='entered'
                )
                return JsonResponse({'message': '入室処理が完了しました', 'log_id': log.id})
        except TblUser.DoesNotExist:
            return JsonResponse({'error': '指定されたユーザーが存在しません'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': '無効なJSONデータ'}, status=400)
    return JsonResponse({'error': '無効なリクエスト'}, status=400)

class QRReaderView(TemplateView):
    template_name = "teacher_pages/qr_reader.html"

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt.update(get_account_info(self.request))
        today = timezone.now().date()
        logs = EntryExitLog.objects.filter(entry_time__date=today)

        # duration を「時間 分」の形式でフォーマット
        for log in logs:
            if log.duration:
                total_seconds = int(log.duration.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                log.formatted_duration = f"{hours}時間 {minutes}分"
            else:
                log.formatted_duration = "未計算"

        ctxt['logs'] = logs
        return ctxt
    
    
def get_latest_logs(request):
    if request.method == 'GET':
        today = timezone.now().date()
        logs = EntryExitLog.objects.filter(entry_time__date=today).select_related('user')

        log_data = []
        for log in logs:
            if log.duration:
                total_seconds = int(log.duration.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                formatted_duration = f"{hours}時間 {minutes}分"
            else:
                formatted_duration = "未計算"

            log_data.append({
                'user_name': log.user.user_simei,
                'entry_time': log.entry_time.strftime('%Y-%m-%d %H:%M:%S'),
                'exit_time': log.exit_time.strftime('%Y-%m-%d %H:%M:%S') if log.exit_time else "未退室",
                'status': log.get_status_display(),
                'duration': formatted_duration,
            })

        return JsonResponse({'logs': log_data})
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def keep_session_alive(request):
    if request.session.session_key:
        # セッションの有効期限を延長
        request.session.modified = True
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=400)

#生徒側ビュー
class StudentHomeView(CustomLoginRequiredMixin, TemplateView):
    template_name = "student_pages/student_home.html"

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt.update(get_account_info(self.request))

        user_id = self.request.session.get('user_id')
        user = TblUser.objects.get(u_id=user_id)

        # QRコードを生成してコンテキストに追加
        qr_code_data = generate_qr_code(user_id)
        ctxt['qr_code'] = qr_code_data

        ctxt.update(get_home_context(user_id))

        if user_id:
            ctxt['test_result_form'] = TestResultForm(user=user)

        return ctxt
    
    def post(self, request, *args, **kwargs):
        user_id = self.request.session.get('user_id')
        user = TblUser.objects.get(u_id=user_id)
        form = TestResultForm(request.POST, user=user)
        
        if form.is_valid():
            form.save()
            return redirect('studentHome')
        
        ctxt = self.get_context_data(**kwargs)
        ctxt['test_result_form'] = form
        
        return self.render_to_response(ctxt)
    
    
@custom_login_required
def get_results(request, test_id,student_id=None):
    grades = TblGrades.objects.filter(id=test_id)
    grades_data = [{'tst': grade.tst.name, 'rank': grade.rank, 'score': grade.score} for grade in grades]
    return JsonResponse({'grades': grades_data})

@custom_login_required
def update_report_data(request, student_id=None):
    days = int(request.GET.get('days', 7))  # デフォルトは7日間
    if student_id:
        u_id = student_id
    else:
        u_id = request.session.get('user_id')
    
    firstCHK_dict = get_complete_task_date(u_id, days)
    return JsonResponse(firstCHK_dict)

@csrf_exempt
def update_status(request, task_id):
    if request.method == 'POST':
        try:
            # print("task_id",task_id)
            task = TblTask.objects.get(id=task_id)
            task.status += 1
            task.save()
            return JsonResponse({'success': True})
        except TblTask.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Task not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def update_task_status(request, task_id, student_id=None):
    task = get_object_or_404(TblTask, pk=task_id)
    print("task id",task_id)
    task.status = 2
    task.number_1stchk = timezone.now()  # 今日の日付を追加
    task.save()
    
    if student_id:
        return redirect('student_detail', student_id=student_id)
    return redirect('studentHome')


class TaskAddView(CustomLoginRequiredMixin, TemplateView):
    template_name = 'student_pages/task_add_view.html'

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt.update(get_account_info(self.request))

        user_id = self.request.session.get('user_id')
        if not user_id:
            ctxt['error'] = 'User ID is not available.'
            return ctxt

        try:
            user = TblUser.objects.get(u_id=user_id)
        except TblUser.DoesNotExist:
            ctxt['error'] = 'User does not exist.'
            return ctxt

        if user.u_auth == 0:
            tasks = TblTask.objects.filter(u=user).order_by('sub_id')
            curr_ids = tasks.values_list('curr', flat=True).distinct()
            curriculums = TblCurriculum.objects.filter(id__in=curr_ids)
            curr_details = TblCurrDetail.objects.filter(curr_id__in=curr_ids)

            subjects = TblCurriculum.objects.filter(id__in=curr_ids).values_list('sub_name', flat=True).distinct().order_by('sub_id')
            subject_curriculum_pairs = list(zip(subjects, curriculums))

            selected_curriculum_id = self.request.GET.get('curriculum_id', curriculums.first().id if curriculums.exists() else None)
            if selected_curriculum_id:
                tasks = tasks.filter(curr_id=selected_curriculum_id)

            tasks_by_tag = {}
            for task in tasks:
                tag = task.tag
                if tag not in tasks_by_tag:
                    tasks_by_tag[tag] = []
                details = TblCurrDetail.objects.filter(curr=task.curr, sub_id=task.sub_id, task_id=task.task_id)
                for detail in details:
                    tasks_by_tag[tag].append({
                        'task_name': detail.task_name,
                        'status': task.get_status_display(),
                        'priority': task.get_priority_display(),
                        'grade': task.get_grade_display(),
                        'id': task.id
                    })

            ctxt['tasks'] = tasks
            ctxt['curriculums'] = curriculums
            ctxt['curr_details'] = curr_details
            ctxt['subjects'] = subjects
            ctxt['subject_curriculum_pairs'] = subject_curriculum_pairs
            ctxt['tasks_by_tag'] = tasks_by_tag
        else:
            ctxt['error'] = 'User is not authorized to view this page.'
        
        print(ctxt)
        return ctxt
    

@method_decorator(csrf_exempt, name='dispatch')
class UpdateTaskStatusView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            deadline = data.get('deadline')
            manage_ids = data.get('manage_id', [])
            print(manage_ids)

            for manage_id in manage_ids:
                try:
                    task = TblTask.objects.get(id=manage_id)
                    task.status = 1  # ステータスを自動で1(実行中)に設定
                    task.deadline = datetime.strptime(deadline, '%Y-%m-%d').date()
                    task.save()
                except TblTask.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': f'Task with id {manage_id} not found'})

            return JsonResponse({'status': 'success', 'message': 'Tasks updated successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
        
@csrf_exempt
def add_task_deadline(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        deadline = data.get('deadline')
        student_id = data.get('student_id')

        if 'tag' in data:
            tag = data.get('tag')
            print(f"一括追加: タグ={tag}, 期限={deadline}, 生徒ID={student_id}")
            # 一括追加の処理
            tasks = TblTask.objects.filter(u_id=student_id, tag=tag)
            for task in tasks:
                task.status = 1  # ステータスを1に変更
                task.deadline = deadline  # 期限を設定
                task.save()
            
        elif 'detail_id' in data:
            detail_id = data.get('detail_id')
            print(f"個別追加: タスクID={detail_id}, 期限={deadline}, 生徒ID={student_id}")
            # 個別追加の処理
            try:
                task = TblTask.objects.get(id=detail_id)
                task.status = 1  # ステータスを1に変更
                task.deadline = deadline  # 期限を設定
                task.save()
            except TblTask.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Task not found'}, status=404)

        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

#保護者側ビュー
class ParentHomeView(CustomLoginRequiredMixin, TemplateView):
    template_name = "parent_pages/parent_home.html"
    
    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        user_id = self.request.session.get('user_id')
        account = get_account_info(self.request)
        ctxt.update(get_account_info(self.request))
        student_name = TblUser.objects.get(u_id=user_id).u_name[1:]
        student = TblUser.objects.get(u_name=student_name)
        ctxt["student_id"] = student.u_id
        ctxt.update(get_home_context(student.u_id))
        print(ctxt)
        return ctxt