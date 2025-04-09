from django.db import models
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now


class TblSchoolid(models.Model):
    id = models.SmallAutoField(primary_key=True)
    s_id = models.TextField()
    s_name = models.CharField(max_length=100, default='未設定')
    s_pass = models.TextField()
    l_login_date = models.DateTimeField(blank=True, null=True)
    update_date = models.DateTimeField(auto_now=True,blank=True, null=True)
    reg_date = models.DateTimeField(auto_now_add=True,blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'tbl_schoolid'
    def __str__(self):
        return self.s_id

@receiver(post_save, sender=TblSchoolid)
def create_user_for_school(sender, instance, created, **kwargs):
    if created:
        TblUser.objects.create(
            u_name=f't{instance.s_id}',
            u_pass=instance.s_pass,
            s=instance,
            u_auth=2
        )

class TblUser(models.Model):
    AUTH_TYPE = [
        (-1, '保護者'),
        (0, '生徒'),
        (1, '講師'),
        (2, '教室'),
    ]
    u_id = models.SmallAutoField(primary_key=True)
    u_name = models.TextField()
    user_simei = models.CharField(max_length=100,default='未設定')
    u_pass = models.TextField()
    s = models.ForeignKey(TblSchoolid, on_delete=models.CASCADE)
    u_auth = models.SmallIntegerField(choices=AUTH_TYPE,default=0)
    l_login_date = models.DateTimeField(auto_now=True, blank=True, null=True)
    update_date = models.DateTimeField(auto_now=True,blank=True, null=True)
    reg_date = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    
    

    class Meta:
        managed = True
        db_table = 'tbl_user'

    def __str__(self):
        return self.u_name
    
    
@receiver(post_save, sender=TblUser)
def create_parent_account(sender, instance, created, **kwargs):
    if created and instance.u_auth == 0:
        parent_u_name = f'p{instance.u_name}'
        TblUser.objects.create(
            u_name=parent_u_name,
            u_pass=instance.u_pass,
            user_simei = f'{instance.user_simei} 保護者',
            s=instance.s,
            u_auth=-1
        )


class TblSubject(models.Model):
    id = models.SmallAutoField(primary_key=True)
    s = models.ForeignKey(TblSchoolid, on_delete=models.CASCADE)
    sub_name = models.TextField()
    update_date = models.DateTimeField(auto_now=True,blank=True, null=True)
    reg_date = models.DateTimeField(auto_now_add=True,blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_subject'
    def __int__(self):
        return self.sub_name

class TblCurriculum(models.Model):
    id = models.SmallAutoField(primary_key=True)
    s = models.ForeignKey(TblSchoolid, on_delete=models.CASCADE, default=1)
    curr_name = models.TextField()
    sub_id = models.SmallIntegerField()
    sub_name = models.TextField(blank=True, null=True)
    next_num = models.SmallIntegerField(blank=True, default=1)
    sub_enable = models.BooleanField(blank=True, null=True,default=True)
    update_date = models.DateTimeField(auto_now=True,blank=True, null=True)
    reg_date = models.DateTimeField(auto_now_add=True,blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_curriculum'

    def save(self, *args, **kwargs):
        if self.sub_id == 0:
            self.sub_name = '全体'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.curr_name

class TblCurrDetail(models.Model):
    id = models.SmallAutoField(primary_key=True)
    s = models.ForeignKey(TblSchoolid, on_delete=models.CASCADE, default=1)
    curr = models.ForeignKey(TblCurriculum, default=10, on_delete=models.CASCADE)
    sub_id = models.SmallIntegerField()
    task_id = models.SmallIntegerField()
    task_name = models.TextField()
    next_num = models.SmallIntegerField()
    task_enable = models.BooleanField(default=False)
    update_date = models.DateTimeField(auto_now=True,blank=True, null=True)
    reg_date = models.DateTimeField(auto_now_add=True,blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_curr_detail'
    def __str__(self):
        return self.task_name




class TblTask(models.Model):
    STATUS_CHOICES = [
        (0, '計画中'),
        (1, '実行中'),
        (2, '復習1回目'),
        (3, '復習2回目'),
        (4, '復習3回目'),
        (5, '復習4回目'),
        (6, '復習5回目'),
        (7, '復習6回目'),
        (8, '完全習得'),
    ]
    GRADE_CHOICES = [
        (0, '未設定'),
        (1, 'A'),
        (2, 'B'),
        (3, 'C'),
    ]
    PRIORITY_CHOICES = [
        (0, '未設定'),
        (1, 'A'),
        (2, 'B'),
        (3, 'C'),
    ]

    id = models.SmallAutoField(primary_key=True)
    # u_id = models.SmallIntegerField(null=True)
    u = models.ForeignKey(TblUser, on_delete=models.CASCADE, default=1)
    # s = models.ForeignKey(TblUser, on_delete=models.CASCADE, default=10)
    curr = models.ForeignKey(TblCurriculum, default=1, on_delete=models.CASCADE)
    # curr_id = models.SmallIntegerField(default=1)
    sub_id = models.SmallIntegerField()
    task_id = models.SmallIntegerField()
    status = models.SmallIntegerField(choices=STATUS_CHOICES,default=0)
    grade = models.SmallIntegerField(choices=GRADE_CHOICES, default=0)
    priority = models.SmallIntegerField(choices=PRIORITY_CHOICES, default=0)
    tag = models.TextField(default='未設定')
    deadline = models.DateField(blank=True, null=True)
    number_1stchk = models.DateField(db_column='1stCHK', blank=True, null=True)  # Field name made lowercase. Field renamed because it wasn't a valid Python identifier.
    number_1streview = models.DateField(db_column='1stReview', blank=True, null=True)  # Field name made lowercase. Field renamed because it wasn't a valid Python identifier.
    number_2ndchk = models.DateField(db_column='2ndCHK', blank=True, null=True)  # Field name made lowercase. Field renamed because it wasn't a valid Python identifier.
    number_3rdchk = models.DateField(db_column='3rdCHK', blank=True, null=True)  # Field name made lowercase. Field renamed because it wasn't a valid Python identifier.
    number_4thchk = models.DateField(db_column='4thCHK', blank=True, null=True)  # Field name made lowercase. Field renamed because it wasn't a valid Python identifier.
    number_5thchk = models.DateField(db_column='5thCHK', blank=True, null=True)  # Field name made lowercase. Field renamed because it wasn't a valid Python identifier.
    number_6thchk = models.DateField(db_column='6thCHK', blank=True, null=True)  # Field name made lowercase. Field renamed because it wasn't a valid Python identifier.
    update_date = models.DateTimeField(auto_now=True,blank=True, null=True)
    reg_date = models.DateTimeField(auto_now_add=True,blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_task'

    def save(self, *args, **kwargs):
        if self.number_1stchk:
            self.number_1streview = self.number_1stchk + timedelta(days=2)
            self.number_2ndchk = self.number_1stchk + timedelta(days=4)
            self.number_3rdchk = self.number_2ndchk + timedelta(days=7)
            self.number_4thchk = self.number_3rdchk + timedelta(days=14)
            self.number_5thchk = self.number_4thchk + timedelta(days=14)
            self.number_6thchk = self.number_5thchk + timedelta(days=14)
        super(TblTask, self).save(*args, **kwargs)

    def __str__(self):
        return f'Task {self.task_id} - Status: {self.get_status_display()}'



class TblTestname(models.Model):
    id = models.SmallAutoField(primary_key=True)
    s = models.ForeignKey(TblSchoolid, on_delete=models.CASCADE)
    name = models.TextField()
    dsp_order = models.SmallIntegerField(default=0)
    update_date = models.DateTimeField(auto_now=True,blank=True, null=True)
    reg_date = models.DateTimeField(auto_now_add=True,blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_testname'

    def __str__(self):
        return self.name
class TblGrades(models.Model):
    id = models.SmallAutoField(primary_key=True)
    user = models.ForeignKey(TblUser, on_delete=models.CASCADE)
    tst = models.ForeignKey(TblTestname, on_delete=models.CASCADE)
    rank = models.SmallIntegerField()
    score = models.SmallIntegerField()
    update_date = models.DateTimeField(auto_now=True,blank=True, null=True)
    reg_date = models.DateTimeField(auto_now_add=True,blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_grades'

    def __str__(self):
        return self.tst.name
class TblMaster(models.Model):
    num = models.AutoField(primary_key=True)
    type = models.TextField()
    tdata = models.TextField()
    order_no = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'tbl_master'
        


class TblMessage(models.Model):
    id = models.SmallAutoField(primary_key=True)
    sender = models.ForeignKey(TblUser, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(TblUser, related_name='received_messages', on_delete=models.CASCADE)
    message = models.TextField()
    read = models.BooleanField(default=False)
    open_or_not = models.BooleanField(default=False)
    update_date = models.DateTimeField(auto_now=True, blank=True, null=True)
    reg_date = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'tbl_message'

    def __str__(self):
        return f'Message from {self.sender} to {self.receiver}'
    


class EntryExitLog(models.Model):
    STATUS_CHOICES = [
        ('entered', '入室中'),
        ('exited', '退室済み'),
    ]

    user = models.ForeignKey(TblUser, on_delete=models.CASCADE, related_name='entry_exit_logs')
    entry_time = models.DateTimeField(default=now, verbose_name="入室時間")
    exit_time = models.DateTimeField(blank=True, null=True, verbose_name="退室時間")
    duration = models.DurationField(blank=True, null=True, verbose_name="滞在時間")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='entered', verbose_name="状態")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    def save(self, *args, **kwargs):
        # 滞在時間を計算
        if self.entry_time and self.exit_time:
            self.duration = self.exit_time - self.entry_time
            self
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.u_name} - {self.status}"