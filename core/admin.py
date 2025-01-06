from django.contrib import admin
from .models import *
from django import forms
from django.contrib.auth.hashers import make_password

# Register your models here.

class TblCurriculumAdmin(admin.ModelAdmin):
    list_display = ('id', 's', 'curr_name', 'sub_id', 'sub_name', 'next_num', 'sub_enable', 'update_date', 'reg_date')

class TblSubjectAdmin(admin.ModelAdmin):
    list_display = ('id','sub_name')

class TblGradesAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'tst','rank', 'score', 'update_date','reg_date')
    
class TblCurrDetailAdmin(admin.ModelAdmin):
    list_display = ('id', 's', 'curr','sub_id', 'task_id', 'task_name', 'next_num', 'task_enable', 'update_date', 'reg_date')

    # def get_sub_name(self, obj):
    #     return obj.sub_id.sub_name
    # get_sub_name.short_description = '科目名'

class TblSchoolidAdminForm(forms.ModelForm):
    class Meta:
        model = TblSchoolid
        fields = '__all__'

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.s_pass:
            instance.s_pass = make_password(instance.s_pass)
        if commit:
            instance.save()
        return instance

class TblSchoolidAdmin(admin.ModelAdmin):
    form = TblSchoolidAdminForm

admin.site.register(TblSchoolid, TblSchoolidAdmin)
admin.site.register(TblUser)
admin.site.register(TblTask)
admin.site.register(TblCurrDetail, TblCurrDetailAdmin)
admin.site.register(TblCurriculum, TblCurriculumAdmin)
admin.site.register(TblSubject, TblSubjectAdmin)
admin.site.register(TblTestname)
admin.site.register(TblGrades, TblGradesAdmin)
