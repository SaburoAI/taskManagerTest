from django.contrib.auth import logout
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone

class AutoLogoutMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_authenticated:
            return

        last_activity = request.session.get('last_activity')
        if last_activity:
            now = timezone.now()
            elapsed_time = (now - last_activity).total_seconds()
            if elapsed_time > 300:  # 5分 (300秒)
                logout(request)
                return

        request.session['last_activity'] = timezone.now()