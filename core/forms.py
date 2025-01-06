from django import forms
from django.contrib.auth.hashers import make_password
from .models import *

class UserForm(forms.ModelForm):
    class Meta:
        model = TblUser
        fields = ['u_name', 'u_pass', 'u_auth']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.u_pass = make_password(self.cleaned_data['u_pass'])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    u_name = forms.CharField(label='ユーザー名', max_length=100)
    u_pass = forms.CharField(label='パスワード', widget=forms.PasswordInput)

class TblTaskForm(forms.ModelForm):
    class Meta:
        model = TblTask
        fields = '__all__'  # すべてのフィールドを含める

class TestResultForm(forms.ModelForm):
    class Meta:
        model = TblGrades
        fields = ['tst', 'score', 'rank']
        widgets = {
            'tst': forms.Select(attrs={'class': 'form-control'}),
            'score': forms.NumberInput(attrs={'class': 'form-control'}),
            'rank': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(TestResultForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(TestResultForm, self).save(commit=False)
        if self.user:
            instance.user = self.user
        if commit:
            instance.save()
        return instance
    


class CurriculumForm(forms.ModelForm):
    subjects = forms.ModelMultipleChoiceField(
        queryset=TblSubject.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta:
        model = TblCurriculum
        fields = ['curr_name', 'subjects']
        

class TaskEditForm(forms.ModelForm):
    class Meta:
        model = TblCurrDetail
        fields = ['task_name', 'task_enable']


class TaskAddForm(forms.ModelForm):
    class Meta:
        model = TblCurrDetail
        fields = ['s','curr','sub_id','task_id','task_name', 'next_num','task_enable' ]


class UpdateTaskForm(forms.ModelForm):
    deadline = forms.DateField(widget=forms.SelectDateWidget)

    class Meta:
        model = TblTask
        fields = ['status', 'deadline']