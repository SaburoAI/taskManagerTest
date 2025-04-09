from django import template
register = template.Library()

@register.filter
def format_duration(value):
    if value is None:
        return "未計算"
    total_seconds = int(value.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}時間 {minutes}分 {seconds}秒"