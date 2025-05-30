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
from .models import *
from .forms import *
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .contextMaker import *
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json, logging, os
from datetime import datetime
import pytz
from django.utils.timezone import localtime


#アカウントのテーブルを2つに分けているため既存のLoginRequiredMixinやlogin_requiredが機能しないので、独自のログインチェックを行う　
class CustomLoginRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('user_id') and not request.session.get('school_id'):
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

def custom_login_required(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        if not request.session.get('user_id') and not request.session.get('school_id'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view_func

#共通ビュー
class MypageView(CustomLoginRequiredMixin, TemplateView):
    template_name = "mypage.html"
    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt.update(get_account_info(self.request))
        
        return ctxt
    
    
class TblUserPasswordChangeView(LoginRequiredMixin, FormView):
    form_class = TblUserPasswordChangeForm
    template_name = 'mypage.html'
    success_url = reverse_lazy('mypage')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.request.user
        return kwargs

    def form_invalid(self, form):
        messages.error(self.request, "パスワードが一致しません。もう一度お試しください。")
        return self.render_to_response(self.get_context_data(form=form))

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "パスワードが変更されました。")
        return super().form_valid(form)
    
    
@custom_login_required
def create_user(request):
    school_id = request.session.get('school_id')
    if not school_id:
        return redirect('login')  # ログインしていない場合はログインページにリダイレクト

    try:
        school = TblSchoolid.objects.get(id=school_id)
    except TblSchoolid.DoesNotExist:
        return redirect('login')  # 無効なschool_idの場合はログインページにリダイレクト

    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.s = school  # 現在ログインしているスクールIDを設定
            user.save()
            return redirect('teacherHome')  # 適切なリダイレクト先に変更
    else:
        form = UserForm()
    
    ctxt = {'form': form}
    ctxt.update(get_account_info(request))
    return render(request, 'registration/create_account.html', ctxt)

def root_view(request):
    
    user_id = request.session.get('user_id')
    school_id = request.session.get('school_id')
    
    if not user_id and not school_id:
        return redirect('login')
    
    if user_id:
        user = TblUser.objects.get(u_id=user_id)
        if user.u_auth == 0:
            return redirect('studentHome')
        elif user.u_auth == -1:
            print("parentHome")
            return redirect('parentHome')
        else:
            return redirect('teacherHome')
    
    if school_id:
        return redirect('teacherHome')
    
    return redirect('login')

class LoginView(FormView):
    template_name = 'registration/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('studentHome')

    def form_valid(self, form):
        u_name = form.cleaned_data['u_name']
        u_pass = form.cleaned_data['u_pass']
        # TblSchoolidテーブルをチェック
        try:
            school = TblSchoolid.objects.get(s_id=u_name)
            if check_password(u_pass, school.s_pass):
                self.request.session['school_id'] = school.id
                return redirect('teacherHome')
        except TblSchoolid.DoesNotExist:
            pass

        # TblUserテーブルをチェック
        try:
            user = TblUser.objects.get(u_name=u_name)
            if check_password(u_pass, user.u_pass):
                self.request.session['user_id'] = user.u_id
                if user.u_auth == 0:
                    return redirect('studentHome')
                elif user.u_auth == -1:
                    return redirect('parentHome')
                else:
                    return redirect('teacherHome')
        except TblUser.DoesNotExist:
            pass

        messages.error(self.request, 'ユーザー名またはパスワードが正しくありません')
        return self.form_invalid(form)

def user_logout(request):
    logout(request)
    return redirect('login')

def page_not_found(request, exception):
    return render(request, 'pages-error-404.html', status=404)

class LibraryView(CustomLoginRequiredMixin, TemplateView):
    template_name = "library.html"
    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        if 'school_id' in self.request.session:
            school_id = self.request.session.get('school_id')
            user_neme = TblUser.objects.filter(s_id=school_id, u_auth=2).first()
            user_id = user_neme.u_id
            ctxt['user_id'] = user_id
            ctxt['user'] = user_neme

        elif 'user_id' in self.request.session:
            user_id = self.request.session.get('user_id')
            ctxt['user'] = user_id
            
            try:
                user = TblUser.objects.get(u_id=user_id)
                school_id = user.s_id
                
            except TblUser.DoesNotExist:
                ctxt['error'] = 'User ID does not exist.'
                return ctxt
            
        else:
            ctxt['error'] = 'No valid session data.'
            return ctxt
        ctxt.update(get_account_info(self.request))
        ctxt.update(get_curr_info(user_id))
        ctxt.update(get_teacher_home_context(school_id, user_id))
        ctxt.update(get_account_info(self.request))
        


        return ctxt


class CurrHomeView(CustomLoginRequiredMixin, TemplateView):
    template_name = "curr_home.html"

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt.update(get_account_info(self.request))

        
        # ログインしているユーザーがs_idかu_idかで分岐
        if 'school_id' in self.request.session:
            school_id = self.request.session.get('school_id')
            user_name = TblUser.objects.filter(s_id=school_id, u_auth=2).first()
            user_id = user_name.u_id
            
            ctxt['user'] = user_name
            ctxt['user_id'] = user_id
            ctxt['school_id'] = school_id

        elif 'user_id' in self.request.session:
            user_id = self.request.session.get('user_id')
            user = TblUser.objects.get(u_id=user_id)
            user_name = user.u_name
            school = TblSchoolid.objects.get(id=user.s_id)
            school_id = school.id
            
            ctxt['user'] = user.u_name
            ctxt['user_id'] = user_id
            ctxt['school_id'] = school_id
            
            try:
                user = TblUser.objects.get(u_id=user_id)
                school_id = user.s_id
                
            except TblUser.DoesNotExist:
                ctxt['error'] = 'User ID does not exist.'
                return ctxt
            
        else:
            ctxt['error'] = 'No valid session data.'
            return ctxt
        
        
        users = TblUser.objects.filter(s_id=school_id, u_auth__in=[0, 1])
        ctxt.update(get_account_info(self.request))
        ctxt.update(get_teacher_home_context(school_id, user_id))
        # print(get_account_info(self.request))
  

        # curriculum_nameとsが一致するuを取得
        curriculum_name = kwargs.get('curriculum_name')
        
        try:
            school = TblSchoolid.objects.get(id=school_id)
            
        except TblSchoolid.DoesNotExist:
            ctxt['error'] = 'School ID does not exist.'
            return ctxt

        all_task = TblTask.objects.filter(curr__curr_name=curriculum_name,)
        
        
        students = TblUser.objects.filter(u_id__in=all_task.values_list('u', flat=True), u_auth=0)
        teachers = TblUser.objects.filter(u_id__in=all_task.values_list('u', flat=True), u_auth__in=[1,2])
        

        # u_authのラベルを追加
        for user in students:
            user.u_auth_label = dict(TblUser.AUTH_TYPE).get(user.u_auth, "Unknown")
        for user in teachers:
            user.u_auth_label = dict(TblUser.AUTH_TYPE).get(user.u_auth, "Unknown")
        
        # 最初の教師IDを取得
        first_teacher_id = None
        if teachers.exists():
            first_teacher_id = teachers.first().u_id
            ctxt['model_user'] = first_teacher_id
        
        
        curriculums = TblCurriculum.objects.filter(curr_name=curriculum_name).order_by('sub_id')

        
        # subjects辞書を作成
        subjects = [curriculum.sub_name for curriculum in curriculums]
        
        # tasks辞書を作成
        tasks = {}
        
        for curriculum in curriculums:
            task_details = TblCurrDetail.objects.filter(curr=curriculum).order_by('task_id')
            tasks[curriculum.sub_name] = []
            for task in task_details:
                try:
                    tbl_task = TblTask.objects.get(u_id =user_id,curr__curr_name=curriculum_name,sub_id=task.sub_id, task_id=task.task_id)
                    tasks[curriculum.sub_name].append({
                        'id': task.id,#TblCurrDetailのIDであることに注意
                        'sub_id': task.sub_id,
                        'task_id': task.task_id,
                        'task_name': task.task_name,
                        'grade': tbl_task.grade,
                        'priority': tbl_task.priority,
                        # 'grade': dict(TblTask.GRADE_CHOICES).get(tbl_task.grade, "未設定"),
                        # 'priority': dict(TblTask.PRIORITY_CHOICES).get(tbl_task.priority, "未設定"),
                        'tag': tbl_task.tag,
                        'Tbltask_id': tbl_task.id,
                        'grade_choices': TblTask.GRADE_CHOICES,
                        'priority_choices': TblTask.PRIORITY_CHOICES,
                    })
                except TblTask.DoesNotExist:
                    tasks[curriculum.sub_name].append({
                        'id': task.id,
                        'sub_id': task.sub_id,
                        'task_id': task.task_id,
                        'task_name': task.task_name,
                        'grade': "未設定",
                        'priority': "未設定",
                        'tag': None,
                        'grade_choices': TblTask.GRADE_CHOICES,
                        'priority_choices': TblTask.PRIORITY_CHOICES,
                    })
        ctxt['students'] = students
        ctxt['teachers'] = teachers
        ctxt['curriculum_name'] = curriculum_name
        
        ctxt['users'] = users
        ctxt['subjects'] = subjects
        ctxt['tasks'] = tasks
        #print(ctxt)
        return ctxt


class TestMenuView(CustomLoginRequiredMixin, TemplateView):
    template_name = "test_home.html"

    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt.update(get_account_info(self.request))

        # ログインしているユーザーがs_idかu_idかで分岐
        if 'school_id' in self.request.session:
            school_id = self.request.session.get('school_id')
            user_name = TblUser.objects.filter(s_id=school_id, u_auth=2).first()
            user_id = user_name.u_id
            
            ctxt['user'] = user_name
            ctxt['user_id'] = user_id
            ctxt['school_id'] = school_id

        elif 'user_id' in self.request.session:
            user_id = self.request.session.get('user_id')
            user = TblUser.objects.get(u_id=user_id)
            user_name = user.u_name
            school = TblSchoolid.objects.get(id=user.s_id)
            school_id = school.id
            
            ctxt['user'] = user.u_name
            ctxt['user_id'] = user_id
            ctxt['school_id'] = school_id
            
            try:
                user = TblUser.objects.get(u_id=user_id)
                school_id = user.s_id
                
            except TblUser.DoesNotExist:
                ctxt['error'] = 'User ID does not exist.'
                return ctxt
            
        else:
            ctxt['error'] = 'No valid session data.'
            return ctxt
        
        users = TblUser.objects.filter(s_id=school_id, u_auth__in=[0, 1])
        ctxt.update(get_account_info(self.request))
        ctxt.update(get_teacher_home_context(school_id, user_id))

        # curriculum_nameとsが一致するuを取得
        curriculum_name = kwargs.get('curriculum_name')
        
        try:
            school = TblSchoolid.objects.get(id=school_id)
            
        except TblSchoolid.DoesNotExist:
            ctxt['error'] = 'School ID does not exist.'
            return ctxt

        all_task = TblTask.objects.filter(curr__curr_name=curriculum_name)
        
        students = TblUser.objects.filter(u_id__in=all_task.values_list('u', flat=True), u_auth=0)
        teachers = TblUser.objects.filter(u_id__in=all_task.values_list('u', flat=True), u_auth__in=[1, 2])

        # u_authのラベルを追加
        for user in students:
            user.u_auth_label = dict(TblUser.AUTH_TYPE).get(user.u_auth, "Unknown")
        for user in teachers:
            user.u_auth_label = dict(TblUser.AUTH_TYPE).get(user.u_auth, "Unknown")
        
        # 最初の教師IDを取得
        first_teacher_id = None
        if teachers.exists():
            first_teacher_id = teachers.first().u_id
            ctxt['model_user'] = first_teacher_id
        
        curriculums = TblCurriculum.objects.filter(curr_name=curriculum_name).order_by('sub_id')

        # subjects辞書を作成
        subjects = [curriculum.sub_name for curriculum in curriculums]
        
        # tasks辞書を作成
        tasks = {}
        
        for curriculum in curriculums:
            task_details = TblCurrDetail.objects.filter(curr=curriculum).order_by('task_id')
            tasks[curriculum.sub_name] = []
            for task in task_details:
                try:
                    tbl_task = TblTask.objects.get(u_id=user_id, curr__curr_name=curriculum_name, sub_id=task.sub_id, task_id=task.task_id)
                    tasks[curriculum.sub_name].append({
                        'id': task.id,  # TblCurrDetailのIDであることに注意
                        'sub_id': task.sub_id,
                        'Tbltask_id': tbl_task.id,
                        'task_id': task.task_id,
                        'task_name': task.task_name,
                        'grade': tbl_task.grade,
                        'priority': tbl_task.priority,
                        'tag': tbl_task.tag,
                        'grade_choices': TblTask.GRADE_CHOICES,
                        'priority_choices': TblTask.PRIORITY_CHOICES,
                    })
                except TblTask.DoesNotExist:
                    tasks[curriculum.sub_name].append({
                        'id': task.id,
                        'sub_id': task.sub_id,
                        'task_id': task.task_id,
                        'task_name': task.task_name,
                        'grade': "未設定",
                        'priority': "未設定",
                        'tag': None,
                        'grade_choices': TblTask.GRADE_CHOICES,
                        'priority_choices': TblTask.PRIORITY_CHOICES,
                    })
        ctxt['students'] = students
        ctxt['teachers'] = teachers
        ctxt['curriculum_name'] = curriculum_name
        
        ctxt['users'] = users
        ctxt['subjects'] = subjects
        ctxt['tasks'] = tasks
        return ctxt
    
    
@csrf_exempt
def submit_answers(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        print(data)
        answers = data.get('answers', [])
        test_id = int(data.get('test_id'))
        task_id = int(data.get('task_id'))
        print(type(task_id))
        task = TblTask.objects.get(id=task_id)
        print(task.tag)
        
        # 正解の辞書を作成
        correct_answers = {
            1: [1, 2, 1],
            2: [3, 4, 1, 2],
            3: [4,2,3,2,2,4,3],
            4: [2, 4, 5],
            5: [1,2,3,3,1,2,1],
            6: [2,4,5],
            7: [2,1,2,5,5],
            8: [1,2,3,3,2]
        }
        
        # 答えをint型に変換
        answers = [int(answer) for answer in answers]
        
        # 採点ロジック
        correct = correct_answers.get(test_id, [])
        score = sum(1 for a, b in zip(answers, correct) if a == b)
        total_questions = len(correct)
        score_percentage = (score / total_questions) * 100 if total_questions > 0 else 0
        score_view = f'{score}/{total_questions}'
        
        # スコアが100%の場合、タスクのステータスを8に変更
        if score_percentage == 100:
            try:
                task = TblTask.objects.get(id=task_id)
                task.status = 8
                task.save()
            except TblTask.DoesNotExist:
                return JsonResponse({'error': 'Task not found'}, status=404)
        
        return JsonResponse({'result': score_view})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class AddMemberToTaskView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            curriculum_name = data.get('curriculum_name')
            school_id = data.get('school_id')
            deadline = data.get('deadline')

            user = TblUser.objects.get(u_id=user_id)
            school = TblSchoolid.objects.get(s_id=school_id)
            if 'school_id' in self.request.session:
                school_user = "t" + str(school)


            elif 'user_id' in self.request.session:
                user_id= self.request.session.get('user_id')
                school_user = TblUser.objects.get(u_id=user_id)
                
            

            copy_from_user = TblUser.objects.get(u_name=school_user)
            curriculums = TblCurriculum.objects.filter(curr_name=curriculum_name, s=school)

            for curriculum in curriculums:
                # uとcurrがJSONと一致するタスクをフィルタリング
                copy_from_tasks = TblTask.objects.filter(u=copy_from_user, curr=curriculum)
                for task in copy_from_tasks:
                    task_data = {
                        'u': user,
                        'curr': task.curr,
                        'sub_id': task.sub_id,
                        'task_id': task.task_id,
                        'status': task.status,
                        'grade': task.grade,
                        'priority': task.priority,
                        'tag': task.tag,
                        'deadline': deadline  # JSONから取得した期限を設定
                    }
                    # print(task_data)

                    # 既存のタスクを更新するか、新しいタスクを作成する
                    TblTask.objects.update_or_create(
                        u=user,
                        curr=task.curr,
                        sub_id=task.sub_id,
                        task_id=task.task_id,
                        defaults=task_data
                    )

            return JsonResponse({'status': 'success'})
        except TblUser.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User does not exist'})
        except TblSchoolid.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'School does not exist'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

@csrf_exempt
def get_task_attributes(request):
    try:
        data = json.loads(request.body)
        teacher_id = data.get('teacherId')
        curr = data.get('curr')
        sub_id = data.get('subid')
        task_id = data.get('task_id')

        print(f"Received data: teacher_id={teacher_id}, curr={curr}, sub_id={sub_id}, task_id={task_id}")

        tasks = TblTask.objects.filter(u_id=teacher_id, curr=curr, sub_id=sub_id, task_id=task_id)
        if not tasks.exists():
            return JsonResponse({'error': 'No tasks found for the specified criteria'}, status=404)

        # すべてのタスクの属性をリストに変換
        task_data = []
        for task in tasks:
            task_info = {
                'tag': task.tag,
                'priority': task.priority,
                'grade': task.grade,
            }
            task_data.append(task_info)

        return JsonResponse({'tasks': task_data})
    except TblTask.DoesNotExist:
        return JsonResponse({'error': 'Task not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    
@csrf_exempt
def delete_task(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        print(data)
        task_id = int(data.get('task_id'))
        tblTask_id = int(data.get('tbl_task_id'))
        print(task_id, tblTask_id)
        
        try:
            task = TblCurrDetail.objects.get(id=task_id).delete()
            tblTask= TblTask.objects.get(id=tblTask_id).delete()
            return JsonResponse({'success': True})
        except TblTask.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

#タスク総合編集　講師側のタスク編集はいずれ廃止予定
@method_decorator(csrf_exempt, name='dispatch')
class SaveTasksView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            tasks = data.get('tasks', [])
            # print(tasks)

            # tasksにsub_idを追加して保存
            for task in tasks:
                # 入力データをTblCurriculumから検索してsub_idを取得してcurr_nameを更新
                s_id = task.get('s_id')
                school = TblSchoolid.objects.get(id=s_id)
                user = TblUser.objects.get(u_id=task.get('user_id'))
                curr_name = task.get('curr_name')
                subject = task.get('subject')
                curriculum = TblCurriculum.objects.get(curr_name=curr_name, s=s_id, sub_name=subject)
                sub_id = curriculum.sub_id
                curr_name = curriculum.curr_name
                task_id = int(task.get('task_id'))
                management_id = int(task.get('management_id'))
                tag = task.get('tag')
                grade = int(task.get('grade'))
                priority = int(task.get('priority'))

                if management_id == -1:
                    next_num = task_id + 1
                else:
                    next_num = curriculum.next_num

                task['sub_id'] = sub_id
                task['curr_name'] = curr_name
                task['next_num'] = next_num

                # TblCurrDetailから該当タスクを更新、もしくは新規作成
                if management_id == -1:
                    TblCurrDetail.objects.create(
                        s=school,
                        curr=curriculum,
                        sub_id=sub_id,
                        task_id=task_id,
                        task_name=task.get('task_name'),
                        next_num=next_num,
                        task_enable=True
                    )
                else:
                    TblCurrDetail.objects.filter(id=management_id).update(
                        task_name=task.get('task_name'),
                        # task_enable=task.get('task_enable')
                    )

                # TblTaskから該当タスクを更新、もしくは新規作成
                TblTask.objects.update_or_create(
                    u=user,
                    curr=curriculum,
                    sub_id=sub_id,
                    task_id=task_id,
                    defaults={
                        'tag': tag,
                        'grade': grade,
                        'priority': priority
                    }
                )
            saved_tasks = tasks
            return JsonResponse({'status': 'success', 'tasks': saved_tasks})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

@require_GET
def search_members(request):
    query = request.GET.get('q', '')
    school_id = request.GET.get('school_id', '')
    if query and school_id:
        results = TblUser.objects.filter(
            Q(u_id__icontains=query) & Q(s_id=school_id)
        ).values('u_id', 'u_name')
    else:
        results = []
    return JsonResponse(list(results), safe=False)

class SubjectHomeView(CustomLoginRequiredMixin, TemplateView):
    template_name = "teacher_pages/subject_add_view.html"
    
    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt.update(get_account_info(self.request))
        
        if 'school_id' in self.request.session:
            school_id = self.request.session.get('school_id')
            ctxt['school_id'] = school_id
            user_id = TblUser.objects.filter(s_id=school_id, u_auth=2).first()
            ctxt['user'] = user_id
            subjects = TblSubject.objects.filter(s=school_id).values('id', 'sub_name')
            ctxt['subjects'] = subjects
        else:
            user_id = self.request.session.get('user_id')
            user = TblUser.objects.get(u_id=user_id)
            ctxt['user'] = user
            school_id = user.s_id
            ctxt['school_id'] = school_id
            subjects = TblSubject.objects.filter(s=school_id).values('id', 'sub_name')
            ctxt['subjects'] = subjects
        
        # print(ctxt)
        return ctxt

@method_decorator(csrf_exempt, name='dispatch')
class SaveSubjectsView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        subjects = data.get('subjects', [])
        subject_ids = [subject['id'] for subject in subjects if subject['id'] != '-1']

        # 送られてきていない教科を削除
        TblSubject.objects.exclude(id__in=subject_ids).delete()

        for subject in subjects:
            school = TblSchoolid.objects.get(id=subject['s_id'])
            if subject['id'] == '-1':
                TblSubject.objects.create(
                    s=school,
                    sub_name=subject['sub_name']
                )
            else:
                TblSubject.objects.filter(id=subject['id']).update(
                    s=school,
                    sub_name=subject['sub_name']
                )

        return JsonResponse({'status': 'success'})


class TestHomeView(CustomLoginRequiredMixin, TemplateView):
    template_name = "teacher_pages/test_add_view.html"
    
    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt.update(get_account_info(self.request))
        
        
        school_id = None  # school_idを初期化
        
        if 'school_id' in self.request.session:
            school_id = self.request.session.get('school_id')
            ctxt['school_id'] = school_id
            user_id = TblUser.objects.filter(s_id=school_id, u_auth=2).first()
            ctxt['user'] = user_id
            tests = TblTestname.objects.filter(s=school_id).values('id', 'name')
            ctxt['tests'] = tests
            return ctxt
        elif 'user_id' in self.request.session:
            u_auth = TblUser.objects.get(u_id=self.request.session.get('user_id')).u_auth
            if u_auth == 2:
                if school_id is None:
                    school_id = TblUser.objects.get(u_id=self.request.session.get('user_id')).s_id
                user_id = TblUser.objects.filter(s_id=school_id, u_auth=2).first()
                ctxt['user'] = user_id
                tests = TblTestname.objects.filter(s=school_id).values('id', 'name')
                ctxt['tests'] = tests
            else:
                return redirect('root')  # ルートにリダイレクト
        else:
            ctxt['error'] = 'No valid session data.'
        
        return ctxt

@method_decorator(csrf_exempt, name='dispatch')
class SaveTestsView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        tests = data.get('tests', [])
        test_ids = [test['id'] for test in tests if test['id'] != '-1']
        # print("test_ids", test_ids)

        # 送られてきていない教科を削除
        TblTestname.objects.exclude(id__in=test_ids).delete()

        for test in tests:
            school = TblSchoolid.objects.get(id=test['s_id'])
            if test['id'] == '-1':
                TblTestname.objects.create(
                    s=school,
                    name=test['name']
                )
                
            else:
                TblTestname.objects.filter(id=test['id']).update(
                    s=school,
                    name=test['name']
                )
                

        return JsonResponse({'status': 'success'})

class StudentStatusView(CustomLoginRequiredMixin, TemplateView):
    template_name = "teacher_pages/student_status.html"
    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt.update(get_account_info(self.request))
        student_id = self.kwargs.get('student_id')
        curr_info = get_curr_info(student_id)
        curr_name = curr_info.get('curr_name')
        task_info = get_task_info(student_id,curr_name)
        recent_task = task_info.get('recent_task')
        ctxt['recent_task'] = recent_task
        doing_task = task_info.get('doing_task')
        ctxt['doing_task']=doing_task
        review_dict = get_review_list(student_id)
        ctxt['reviews'] = review_dict
        message = get_message_list(student_id)
        ctxt['message'] = message
        recommended_task= get_recommended_task(student_id)
        ctxt['recommended_task'] = recommended_task
        all_task=get_all_tasks(student_id)
        ctxt['all_task'] = all_task  
        ctxt['task_info'] = task_info


        if student_id:
            try:
                user = TblUser.objects.get(u_id=student_id)
                ctxt['user_name'] = user.user_simei
                ctxt['user_auth'] = user.u_auth
                ctxt['test_result_form'] = TestResultForm(user=user)
                ctxt['student_id'] = student_id
            except TblUser.DoesNotExist:
                ctxt['error'] = '指定されたユーザーは存在しません。'

        #print(ctxt)
        
        return ctxt

@csrf_exempt
def add_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        message_content = data.get('message')
        receiver_id = data.get('receiver_id')  
        sender_id = data.get('sender_id')  
        open_or_not = data.get('open_or_not')
        receiver = TblUser.objects.get(u_id=receiver_id)
        sender = TblUser.objects.get(u_id=sender_id)
        # print(sender, receiver, message_content, open_or_not)

        new_message = TblMessage(
            sender=sender,
            receiver=receiver,
            message=message_content,
            open_or_not=open_or_not,
            reg_date=timezone.now()
        )
        new_message.save()

        return JsonResponse({'status': 'success', 'message': 'メッセージが追加されました。'})

    return JsonResponse({'status': 'error', 'message': '無効なリクエストです。'})

@csrf_exempt
def update_tasks(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        date = data.get('date')
        tag = data.get('tag')
        tasks = data.get('tasks')
        
        try:
            # tasksからidを取得
            task_ids = [task['id'] for task in tasks]
            # TblTaskから該当するタスクを取得
            tasks_to_update = TblTask.objects.filter(id__in=task_ids)
            for task in tasks_to_update:
                task.status = 1
                task.deadline = date
                task.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
def save_oral_check(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        task_id = data.get('task_id')
        result = data.get('result')
        # print(task_id)

        try:
            task = TblTask.objects.get(id=task_id)
            if result == "合格":
                task.status += 1
                task.number_1stchk = date.today()
            elif result == "不合格":
                task.status = 1
            task.save()
            return JsonResponse({'success': True})
        except TblTask.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Task not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

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