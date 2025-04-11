import base64
from django import template

register = template.Library()

@register.filter
def b64encode(value):
    """
    バイナリデータをBase64エンコードするテンプレートフィルター
    """
    return base64.b64encode(value).decode('utf-8')