# Generated by Django 5.1.4 on 2024-12-09 06:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TblMaster',
            fields=[
                ('num', models.AutoField(primary_key=True, serialize=False)),
                ('type', models.TextField()),
                ('tdata', models.TextField()),
                ('order_no', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'tbl_master',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='TblSchoolid',
            fields=[
                ('id', models.SmallAutoField(db_comment='管理用の連番', primary_key=True, serialize=False)),
                ('s_id', models.TextField(db_comment='スクールID')),
                ('s_pass', models.TextField(db_comment='パスワード')),
                ('l_login_date', models.DateTimeField(blank=True, db_comment='最終ログイン日', null=True)),
                ('update_date', models.DateTimeField(auto_now=True, null=True)),
                ('reg_date', models.DateTimeField(auto_now_add=True, db_comment='登録日', null=True)),
            ],
            options={
                'db_table': 'tbl_schoolid',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='TblCurriculum',
            fields=[
                ('id', models.SmallAutoField(db_comment='管理用の連番', primary_key=True, serialize=False)),
                ('curr_name', models.TextField(db_comment='カリキュラム名')),
                ('sub_id', models.SmallIntegerField(db_comment='科目ID')),
                ('sub_name', models.TextField(blank=True, db_comment='科目名', null=True)),
                ('next_num', models.SmallIntegerField(blank=True, db_comment='次の番号', default=1)),
                ('sub_enable', models.BooleanField(blank=True, db_comment='有効無効', default=True, null=True)),
                ('update_date', models.DateTimeField(auto_now=True, null=True)),
                ('reg_date', models.DateTimeField(auto_now_add=True, db_comment='登録日', null=True)),
                ('s', models.ForeignKey(db_comment='スクールID', default=1, on_delete=django.db.models.deletion.CASCADE, to='core.tblschoolid')),
            ],
            options={
                'db_table': 'tbl_curriculum',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='TblCurrDetail',
            fields=[
                ('id', models.SmallAutoField(db_comment='管理用の連番', primary_key=True, serialize=False)),
                ('sub_id', models.SmallIntegerField(db_comment='科目ID')),
                ('task_id', models.SmallIntegerField(db_comment='タスクID')),
                ('task_name', models.TextField(db_comment='タスク名')),
                ('next_num', models.SmallIntegerField(db_comment='次の番号')),
                ('task_enable', models.BooleanField(db_comment='有効無効', default=True)),
                ('update_date', models.DateTimeField(auto_now=True, null=True)),
                ('reg_date', models.DateTimeField(auto_now_add=True, db_comment='登録日', null=True)),
                ('curr', models.ForeignKey(db_comment='カリキュラムID', default=10, on_delete=django.db.models.deletion.CASCADE, to='core.tblcurriculum')),
                ('s', models.ForeignKey(db_comment='スクールID', default=1, on_delete=django.db.models.deletion.CASCADE, to='core.tblschoolid')),
            ],
            options={
                'db_table': 'tbl_curr_detail',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='TblSubject',
            fields=[
                ('id', models.SmallAutoField(db_comment='管理用の連番', primary_key=True, serialize=False)),
                ('sub_name', models.TextField(db_comment='科目名')),
                ('update_date', models.DateTimeField(auto_now=True, null=True)),
                ('reg_date', models.DateTimeField(auto_now_add=True, db_comment='登録日', null=True)),
                ('s', models.ForeignKey(db_comment='スクールID', default=1, on_delete=django.db.models.deletion.CASCADE, to='core.tblschoolid')),
            ],
            options={
                'db_table': 'tbl_subject',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='TblTask',
            fields=[
                ('id', models.SmallAutoField(db_comment='管理用の連番', primary_key=True, serialize=False)),
                ('u_id', models.SmallIntegerField(db_comment='ユーザーID', null=True)),
                ('sub_id', models.SmallIntegerField(db_comment='科目ID')),
                ('task_id', models.SmallIntegerField(db_comment='タスクID')),
                ('status', models.SmallIntegerField(choices=[(0, '計画中'), (1, '実行中'), (2, '復習1回目'), (3, '復習2回目'), (4, '復習3回目'), (5, '復習4回目'), (6, '復習5回目'), (7, '復習6回目'), (8, '完全習得')], db_comment='ステータス', default=0)),
                ('grade', models.SmallIntegerField(choices=[(0, '未設定'), (1, 'A'), (2, 'B'), (3, 'C')], db_comment='重要度', default=0)),
                ('priority', models.SmallIntegerField(choices=[(0, '未設定'), (1, 'A'), (2, 'B'), (3, 'C')], db_comment='優先度', default=0)),
                ('tag', models.TextField(db_comment='タグ', default='未設定')),
                ('deadline', models.DateField(blank=True, db_comment='期限', null=True)),
                ('number_1stchk', models.DateField(blank=True, db_column='1stCHK', db_comment='初回チェック日', null=True)),
                ('number_1streview', models.DateField(blank=True, db_column='1stReview', db_comment='初回復習日', null=True)),
                ('number_2ndchk', models.DateField(blank=True, db_column='2ndCHK', db_comment='2回目復習日', null=True)),
                ('number_3rdchk', models.DateField(blank=True, db_column='3rdCHK', db_comment='3回目復習日', null=True)),
                ('number_4thchk', models.DateField(blank=True, db_column='4thCHK', db_comment='4回目復習日', null=True)),
                ('number_5thchk', models.DateField(blank=True, db_column='5thCHK', db_comment='5回目復習日', null=True)),
                ('number_6thchk', models.DateField(blank=True, db_column='6thCHK', db_comment='6回目復習日', null=True)),
                ('update_date', models.DateTimeField(auto_now=True, null=True)),
                ('reg_date', models.DateTimeField(auto_now_add=True, db_comment='登録日', null=True)),
                ('curr', models.ForeignKey(db_comment='カリキュラムID', default=1, on_delete=django.db.models.deletion.CASCADE, to='core.tblcurriculum')),
            ],
            options={
                'db_table': 'tbl_task',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='TblTestname',
            fields=[
                ('id', models.SmallAutoField(db_comment='管理用の連番', primary_key=True, serialize=False)),
                ('name', models.TextField(db_comment='テスト名')),
                ('dsp_order', models.SmallIntegerField(db_comment='表示順')),
                ('update_date', models.DateTimeField(auto_now=True, null=True)),
                ('reg_date', models.DateTimeField(auto_now_add=True, db_comment='登録日', null=True)),
                ('s', models.ForeignKey(db_comment='tbl_SchoolID', on_delete=django.db.models.deletion.CASCADE, to='core.tblschoolid')),
            ],
            options={
                'db_table': 'tbl_testname',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='TblUser',
            fields=[
                ('u_id', models.SmallAutoField(db_comment='no', primary_key=True, serialize=False)),
                ('u_name', models.TextField(db_comment='ユーザー名')),
                ('u_pass', models.TextField(db_comment='パスワード')),
                ('u_auth', models.SmallIntegerField(choices=[(0, '生徒'), (1, '講師'), (2, '管理者')], db_comment='権限', default=0)),
                ('l_login_date', models.DateTimeField(auto_now=True, db_comment='最終ログイン日', null=True)),
                ('update_date', models.DateTimeField(auto_now=True, null=True)),
                ('reg_date', models.DateTimeField(auto_now_add=True, db_comment='登録日', null=True)),
                ('s', models.ForeignKey(db_comment='スクールID', on_delete=django.db.models.deletion.CASCADE, to='core.tblschoolid')),
            ],
            options={
                'db_table': 'tbl_user',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='TblGrades',
            fields=[
                ('id', models.SmallAutoField(db_comment='管理用の連番', primary_key=True, serialize=False)),
                ('rank', models.SmallIntegerField(db_comment='順位')),
                ('score', models.SmallIntegerField(db_comment='点数')),
                ('update_date', models.DateTimeField(auto_now=True, null=True)),
                ('reg_date', models.DateTimeField(auto_now_add=True, db_comment='登録日', null=True)),
                ('tst', models.ForeignKey(db_comment='テスト名ID', on_delete=django.db.models.deletion.CASCADE, to='core.tbltestname')),
                ('user', models.ForeignKey(db_comment='ユーザーID', on_delete=django.db.models.deletion.CASCADE, to='core.tbluser')),
            ],
            options={
                'db_table': 'tbl_grades',
                'managed': True,
            },
        ),
    ]