from django import forms
from django.contrib.auth.hashers import make_password
from django.contrib.auth.forms import PasswordChangeForm
from .models import *

class TblUserPasswordChangeForm(forms.ModelForm):
    old_password = forms.CharField(
        label="現在のパスワード",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'currentPassword'})
    )
    new_password1 = forms.CharField(
        label="新しいパスワード",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'newPassword'})
    )
    new_password2 = forms.CharField(
        label="パスワード入力（確認）",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'renewPassword'})
    )

    class Meta:
        model = TblUser
        fields = ['old_password', 'new_password1', 'new_password2']

    def clean(self):
        cleaned_data = super().clean()
        old_password = cleaned_data.get("old_password")
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")

        if not self.instance.check_password(old_password):
            self.add_error('old_password', "現在のパスワードが正しくありません。")

        if new_password1 and new_password2 and new_password1 != new_password2:
            self.add_error('new_password2', "新しいパスワードが一致しません。")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.u_pass = make_password(self.cleaned_data['new_password1'])
        if commit:
            user.save()
        return user
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
        
        