from django.db.models import Count, F, Case, When, IntegerField, Q, Func, Value, CharField, Min, Max
from .models import *
from django.utils import timezone
from django.utils.dateformat import DateFormat
from datetime import timedelta, date, datetime
import json,qrcode
from io import BytesIO
from django.http import HttpResponse






SAMPLE_SCHOOL = "ベイスクール"
TopSchool = {
    "国語": 85,
    "数学": 80,
    "理科": 85,
    "社会": 85,
    "英語": 80,
    "学校タイプ": "トップ校"
}

MiddleSchool = {
    "国語": 66,
    "数学": 64,
    "理科": 70,
    "社会": 70,
    "英語": 70,
    "学校タイプ": "中堅校"
}

BusinessSchool = {
    "国語": 55,
    "数学": 45,
    "理科": 55,
    "社会": 55,
    "英語": 53,
    "学校タイプ": "実業系高校"
}

class Replace(Func):
    function = 'REPLACE'
    template = "%(function)s(%(expressions)s)"
    output_field = CharField()  # output_fieldを追加

def get_account_info(request):
    user_id = request.session.get('user_id')
    school_id = request.session.get('school_id')
    
    if not user_id and not school_id:
        return {"error": "you are not logged in"}
    
    account_info = {}
    
    if user_id is not None:
        user = TblUser.objects.get(u_id=user_id)
        s_id = user.s_id
        school = TblSchoolid.objects.get(id=s_id)
        account_info = {
            "u_id": user.u_id,
            "u_name": user.u_name,
            "u_simei": user.user_simei,
            "u_auth": user.u_auth,
            "auth_type": user.get_u_auth_display(),
            "s_id": user.s_id,
            "school_account": user.s.s_id,
            "school_id": school.id,
            "s_name": school.s_name,
        }
    
    if school_id is not None:
        school = TblSchoolid.objects.get(id=school_id)
        user_neme = TblUser.objects.filter(s_id=school_id, u_auth=2).first()
        account_info = {
            "school_id": school.id,
            "s_id": school.s_id,
            "s_name": school.s_name,
            "u_id": user_neme.u_id,
            "u_name": user_neme.u_name,
            "u_simei": user_neme.user_simei,
            "u_auth": user_neme.u_auth,
            "auth_type": user_neme.get_u_auth_display(),
        }

    # 新しい変数を追加
    account_info["in"] = "some_value"
    
    
    return account_info

def get_library_context():
    ctxt = {}
    ctxt["school"] = SAMPLE_SCHOOL
    ctxt["subjects"] = TblSubject.objects.all()
    ctxt["curriculums"] = TblCurriculum.objects.filter(sub_id=0)
    ctxt["tasks"] = TblCurrDetail.objects.all()
    return ctxt

def get_subject_info(u_id):
    subject_info = TblTask.objects.filter(u_id=u_id).exclude(sub_id=0).values('sub_id').annotate(
        task_count=Count('task_id'),
        sub_name=F('curr__sub_name'),
        undone_task_count=Count(Case(When(Q(status=0) | Q(status=1), then=1), output_field=IntegerField())),
        complete_task_count=Count(Case(When(~Q(status__in=[0, 1]), then=1), output_field=IntegerField())),
        achievement_rate=Case(
            When(task_count=0, then=0),  # タスクがない場合は達成率を0に設定
            default=(Count(Case(When(~Q(status__in=[0, 1]), then=1), output_field=IntegerField())) * 100.0 / Count('task_id')),
            output_field=IntegerField()
        )
    ).order_by('sub_id') 
    return subject_info

def get_curr_info(u_id):
    curr_name = TblTask.objects.filter(u_id=u_id).values_list('curr__curr_name', flat=True).first()
    tasks = TblTask.objects.filter(u_id=u_id)
    
    total_tasks = tasks.count()
    completed_tasks = tasks.exclude(status__in=[0, 1]).count()
    achievement_rate = (completed_tasks * 100 // total_tasks) if total_tasks > 0 else 0

    # reg_dateの一番古い日付とdeadlineの一番新しい日付を取得
    oldest_reg_date = tasks.aggregate(Min('reg_date'))['reg_date__min']
    latest_deadline = tasks.aggregate(Max('deadline'))['deadline__max']

    # 本日の日付を取得
    today = date.today()

    # 期間に対する本日の割合を計算
    if oldest_reg_date and latest_deadline:
        # datetime.date 型に変換
        oldest_reg_date = oldest_reg_date.date() if isinstance(oldest_reg_date, datetime) else oldest_reg_date
        latest_deadline = latest_deadline.date() if isinstance(latest_deadline, datetime) else latest_deadline

        total_days = (latest_deadline - oldest_reg_date).days
        days_passed = (today - oldest_reg_date).days
        period_percentage = (days_passed * 100 // total_days) if total_days > 0 else 0
    else:
        period_percentage = 0
    
    

    return {
        'curr_name': curr_name,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'achievement_rate': achievement_rate,
        'period_percentage': period_percentage  # 期間に対する本日の割合を追加
    }
    
def get_school_type(u_id):
    # ユーザーIDと同じカリキュラムネームを取得
    curr_name = TblTask.objects.filter(u_id=u_id).values_list('curr__curr_name', flat=True).first()
    school_type = '未設定'
    # 辞書の定義
    school_type_dict = {
        'トップ校': 'トップ校',
        '中堅校': '中堅校',
        '実業系高校': '実業系高校'
    }
    # curr_nameがNoneでないか確認
    if curr_name:
        # curr_nameに辞書のキーが含まれているかを確認
        for key, value in school_type_dict.items():
            if key in curr_name:
                school_type = school_type_dict[key]
    return school_type

def get_task_list(u_id):
    # TblTaskからu_idが一致し、statusが0か1のものを取得
    tasks = TblTask.objects.filter(u_id=u_id).filter(Q(status=1))
    task_details = []
    for task in tasks:
        
        # TblCurriculumからsub_nameを取得
        curriculum = TblCurriculum.objects.filter(sub_id=task.sub_id).first()
        sub_name = curriculum.sub_name if curriculum else '不明'
        
        # TblCurrDetailからsub_idとtask_idが一致するtasknameを取得
        task_detail = TblCurrDetail.objects.filter(sub_id=task.sub_id, task_id=task.task_id).first()
        task_name = task_detail.task_name if task_detail else '不明'

        # deadlineを日付形式にフォーマット
        deadline_date = DateFormat(task.deadline).format('Y/m/d') if task.deadline else '不明'
        
        # number_1stchkを日付形式にフォーマット
        number_1stchk_date = DateFormat(task.number_1stchk).format('Y/m/d') if task.number_1stchk else '不明'
        
        # タスクのIDを追加
        task_details.append({
            'id': task.id,
            'task_name': task_name,
            'sub_name': sub_name,
            'status': task.status,
            'deadline': deadline_date,
            'number_1stchk': number_1stchk_date
        })

    return task_details

def get_review_list(u_id):
    review_details = []
    tasks = TblTask.objects.filter(u_id=u_id).filter(status__in=[2, 3, 4, 5, 6, 7])
    for task in tasks:
        id = task.id
        curriculum = TblCurriculum.objects.filter(sub_id=task.sub_id).first()
        sub_name = curriculum.sub_name if curriculum else '不明'
        
        task_detail = TblCurrDetail.objects.filter(sub_id=task.sub_id, task_id=task.task_id).first()
        task_name = task_detail.task_name if task_detail else '不明'

        if task.status == 2:
            review_date = task.number_1streview
        elif task.status == 3:
            review_date = task.number_2ndchk
        elif task.status == 4:
            review_date = task.number_3rdchk
        elif task.status == 5:
            review_date = task.number_4thchk
        elif task.status == 6:
            review_date = task.number_5thchk
        elif task.status == 7:
            review_date = task.number_6thchk
        else:
            review_date = None

        review_date_formatted  = DateFormat(review_date).format('Y/m/d') if review_date else '不明'
        
        review_details.append({
            'id': id,
            'task_name': task_name,
            'sub_name': sub_name,
            'status': task.status,
            'status_name': task.get_status_display(),
            'review_date': review_date_formatted,
            'review_date_raw': review_date  # ソート用の生の日付を保持
        })

    # review_date_rawをキーにしてreview_detailsをソート
    review_details_sorted = sorted(review_details, key=lambda x: x['review_date_raw'] or datetime.date.max)

    return review_details_sorted

def get_recommended_task(u_id):
    # ステータスが `0` で、`sub_id` が `0` 以外のタスクをフィルタリング
    tasks = TblTask.objects.filter(u_id=u_id, status=0, grade=1, priority=1).exclude(sub_id=0)
    
    # 各教科でIDが一番若いもののタスクを取得
    sub_ids = tasks.values('sub_id').distinct()
    min_id_tasks = []
    for sub_id in sub_ids:
        min_id_task = tasks.filter(sub_id=sub_id['sub_id']).order_by('id').first()
        if min_id_task:
            min_id_tasks.append(min_id_task)
    
    # タグに含まれた `grade=1` と `priority=1` のタスク数とタスクを取得
    tag_task_counts = []
    for task in min_id_tasks:
        tag_tasks = TblTask.objects.filter(u_id=u_id, tag=task.tag, grade=1, priority=1)
        task_count = tag_tasks.count()
        curriculum = TblCurriculum.objects.filter(sub_id=task.sub_id).first()
        sub_name = curriculum.sub_name if curriculum else '不明'
        task_details = []
        for tag_task in tag_tasks:
            curr_detail = TblCurrDetail.objects.filter(curr=tag_task.curr, task_id=tag_task.task_id).first()
            task_details.append({
                'id': tag_task.id,
                'task_name': curr_detail.task_name if curr_detail else '不明',
                'status': tag_task.status,
                'deadline': tag_task.deadline.isoformat() if tag_task.deadline else None  # 日付を文字列に変換
            })
        tag_task_counts.append({
            'sub_name': sub_name,
            'tag': task.tag,
            'task_count': task_count,
            'tasks': json.dumps(task_details)  # JSONにシリアライズ
        })
    
    return tag_task_counts

def get_test_list(u_id):
    # TblGradesからu_idが一致するものを取得
    grades = TblGrades.objects.filter(user_id=u_id).select_related('tst')
    score_list = []
    for grade in grades:
        score_list.append({
            'id': grade.id,
            'test_name': grade.tst.name,
            'rank': grade.rank,
            'score': grade.score,
        })
    
    # テスト名のリストを取得
    testnames = TblTestname.objects.all().values('id', 'name')
    
    return score_list, testnames

def get_all_tasks(u_id):
    tasks = TblTask.objects.filter(u_id=u_id)
    task_list = []

    for task in tasks:
        curriculum = TblCurriculum.objects.filter(sub_id=task.sub_id).first()
        sub_name = curriculum.sub_name if curriculum else '不明'

        task_detail = TblCurrDetail.objects.filter(sub_id=task.sub_id, task_id=task.task_id).first()
        task_name = task_detail.task_name if task_detail else '不明'

        task_info = {
            'id': task.id,
            'sub_id': task.sub_id,
            'sub_name': sub_name,
            'task_id': task.task_id,
            'task_name': task_name,
            'status': task.status,
            'grade': task.grade,
            'priority': task.priority,
            'tag': task.tag,
            'deadline': task.deadline,
            'number_1stchk': task.number_1stchk,
            'number_1streview': task.number_1streview,
            'number_2ndchk': task.number_2ndchk,
            'number_3rdchk': task.number_3rdchk,
            'number_4thchk': task.number_4thchk,
            'number_5thchk': task.number_5thchk,
            'number_6thchk': task.number_6thchk,
            'get_grade_display': task.get_grade_display(),
            'get_priority_display': task.get_priority_display(),
            'get_status_display': task.get_status_display(),
        }
        task_list.append(task_info)

    return task_list

def get_complete_task_date(u_id, days=30):
    # TblTaskからu_idが一致するものを取得
    tasks = TblTask.objects.filter(u_id=u_id).exclude(number_1stchk__isnull=True)
    complete_task_dates = {}
    
    # 今日の日付を取得
    today = date.today()
    
    # 指定された日数分の日付を生成
    for i in range(days):
        current_date = today - timedelta(days=i)
        complete_task_dates[current_date.isoformat()] = 0  # 初期値として0を設定
    
    # タスクの完了日をカウント
    for task in tasks:
        complete_date = task.number_1stchk.isoformat()
        if complete_date in complete_task_dates:
            complete_task_dates[complete_date] += 1
        else:
            complete_task_dates[complete_date] = 1
    
    return complete_task_dates

def get_home_context(u_id):
    ctxt = {}
    # サンプルデータを設定
    ctxt["school"] = SAMPLE_SCHOOL

    subjectInfo = get_subject_info(u_id)
    currInfo = get_curr_info(u_id)
    school_type = get_school_type(u_id)
    task_dict = get_task_list(u_id)
    review_dict = get_review_list(u_id)
    firstCHK_dict = get_complete_task_date(u_id)
    test_dict, test_names = get_test_list(u_id)
    total_undone_tasks = sum(item['undone_task_count'] for item in subjectInfo)
    
    # school_typeに基づいて使用する辞書を選択
    school_dict = {
        'トップ校': TopSchool,
        '中堅校': MiddleSchool,
        '実業系高校': BusinessSchool
    }.get(school_type, {})
    
    goal_scores = {key: value for key, value in school_dict.items() if key != "学校タイプ"}

    # 選択した辞書の各バリューにachievement_rateの値を乗じてuser_predScoreに代入
    user_predScore = {}
    for subject in subjectInfo:
        sub_name = subject['sub_name']
        achievement_rate = subject['achievement_rate'] / 100.0  # パーセンテージを小数に変換
        if sub_name in school_dict:
            # 初期値をgoal_scoresの半分に設定し、achievement_rateが100%に近づくにつれてgoal_scoresと一致するようにする
            initial_value = school_dict[sub_name] / 2
            user_predScore[sub_name] = initial_value + (school_dict[sub_name] - initial_value) * achievement_rate
    
    ctxt["subjectInfo"] = subjectInfo
    ctxt["currInfo"] = currInfo
    ctxt["school_types"] = school_type
    ctxt["task_list"] = task_dict
    ctxt["review_list"] = review_dict
    ctxt["firstCHK_list"] = firstCHK_dict
    ctxt["tests"] = test_dict
    ctxt["testnames"] = test_names
    ctxt["now"] = timezone.now()
    ctxt["curr_name"] = TblTask.objects.filter(u_id=u_id).values_list('curr__curr_name', flat=True).first()
    ctxt["total_undone_tasks"] = total_undone_tasks
    ctxt["goal_scores"] = goal_scores
    ctxt["user_predScore"] = user_predScore
    

    return ctxt

#教師機能のコンテキスト

def get_teacher_home_context(school_id, user_id):
    context = {}
    school = None
    # school_idがある場合はTblSchoolidから取得、ない場合はTblUserから取得
    if school_id:
        user = TblSchoolid.objects.get(id=school_id)
        school = TblSchoolid.objects.get(id=school_id)
        context['user_name'] = user.s_name

    elif user_id:
        user = TblUser.objects.get(u_id=user_id)
        school = TblSchoolid.objects.get(id=user.s_id)
        context['user_name'] = user.user_simei
    
    if not school:
        return context

    context['school_id'] = school.s_id
    context['curriculums'] = TblCurriculum.objects.filter(s_id=school.id, sub_id=0)
    context['subjects'] = TblSubject.objects.filter(s_id=school.id).values('id', 'sub_name')
    
    students = TblUser.objects.filter(s_id=school.id, u_auth=0)
    student_data = []
    for student in students:
        student_info = {
            'u_id': student.u_id,
            'u_name': student.u_name,
            'user_simei': student.user_simei,
            'school_type': get_school_type(student.u_id),
            'curr_info': get_curr_info(student.u_id),
            # 'task_info': get_task_info(student.u_id),
        }
        student_data.append(student_info)
    context['student_data'] = student_data

    return context

def get_task_info(user_id, curriculum_name):
    curriculums = TblCurriculum.objects.filter(curr_name=curriculum_name).order_by('sub_id')
    subjects = [curriculum.sub_name for curriculum in curriculums]
    tasks = {}
    recent_task = []
    doing_task = []  # statusが1のタスクを格納するリスト
    one_week_ago = date.today() - timedelta(days=7)

    for curriculum in curriculums:
        task_details = TblCurrDetail.objects.filter(curr=curriculum).order_by('task_id')
        tasks[curriculum.sub_name] = []
        for task in task_details:
            try:
                tbl_task = TblTask.objects.get(u_id=user_id, curr__curr_name=curriculum_name, sub_id=task.sub_id, task_id=task.task_id)
                task_detail = {
                    'id': task.id,  # TblCurrDetailのIDであることに注意
                    'tbl_task_id': tbl_task.id,
                    'sub_id': task.sub_id,
                    'sub_name': curriculum.sub_name,
                    'task_id': task.task_id,
                    'task_name': task.task_name,
                    'grade': tbl_task.grade,
                    'priority': tbl_task.priority,
                    'tag': tbl_task.tag,
                    'grade_choices': TblTask.GRADE_CHOICES,
                    'priority_choices': TblTask.PRIORITY_CHOICES,
                    'status': tbl_task.status,
                    'deadline': tbl_task.deadline,
                    'number_1stchk': tbl_task.number_1stchk,
                    'get_grade_display': tbl_task.get_grade_display(),
                    'get_priority_display': tbl_task.get_priority_display(),
                }
                tasks[curriculum.sub_name].append(task_detail)
                
                if tbl_task.number_1stchk and tbl_task.number_1stchk >= one_week_ago and tbl_task.status == 2:
                    recent_task.append(task_detail)
                
                if tbl_task.status == 1:
                    doing_task.append(task_detail)
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
                    'status': None,
                    'deadline': None,
                    'number_1stchk': None,
                    'get_grade_display': "未設定",
                    'get_priority_display': "未設定",
                })
    return {'subjects': subjects, 'tasks': tasks, 'recent_task': recent_task, 'doing_task': doing_task}

def get_message_list(student_id):
    
    try:
        user = TblUser.objects.get(u_id=student_id)
        
    except TblUser.DoesNotExist:
        print("User does not exist")
        return []

    messages = TblMessage.objects.filter(receiver=user).order_by('-reg_date')
    
    message_list = []
    for message in messages:
        message_list.append({
            'id': message.id,
            'sender': message.sender.user_simei,  # ここを変更
            'message': message.message,
            'reg_date': message.reg_date,
            'get_reg_date': DateFormat(message.reg_date).format('Y/m/d H:i'),
        })
        
    return message_list

def generate_qr_code(u_id):
    """
    u_id を含む高解像度のQRコードを生成し、バイナリデータを返す関数
    """
    # QRコードに埋め込むデータ
    data = {
        "u_id": int(u_id),
        "u_simei": TblUser.objects.get(u_id=u_id).user_simei,
        "s_id": TblUser.objects.get(u_id=u_id).s_id,
        "s_name": TblSchoolid.objects.get(id=TblUser.objects.get(u_id=u_id).s_id).s_name,
        "u_auth": TblUser.objects.get(u_id=u_id).u_auth,
    }

    # QRコードを生成
    qr = qrcode.QRCode(
        version=1,  # サイズ（1が最小）
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # エラー訂正レベル
        box_size=40,  # 高解像度のためにボックスサイズを大きく設定
        border=4,  # ボーダーのサイズ
    )
    qr.add_data(json.dumps(data))  # 辞書データをJSON文字列に変換して埋め込む
    qr.make(fit=True)

    # QRコードを画像としてメモリ上に保存
    buffer = BytesIO()
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # バイナリデータを返す
    return buffer.getvalue()