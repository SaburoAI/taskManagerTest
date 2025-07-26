from core.contextMaker import get_account_info, get_home_context
from django.shortcuts import redirect


#アカウントのテーブルを2つに分けているため既存のLoginRequiredMixinやlogin_requiredが機能しないので、独自のログインチェックを行うユーザーモデルの移植完了とともに削除　
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

#ここから残すクラス
class AccountContextMixin:
    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        ctxt.update(get_account_info(self.request))
        return ctxt
    
    
class HomeContextMixin:
    def get_context_data(self, **kwargs):
        ctxt = super().get_context_data(**kwargs)
        user_id = self.request.session.get('user_id')
        if user_id:
            ctxt.update(get_home_context(user_id))
        return ctxt


