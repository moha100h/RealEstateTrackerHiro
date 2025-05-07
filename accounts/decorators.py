"""
توابع دکوراتور برای استفاده در views
"""

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

def csrf_exempt_class(view_class):
    """
    دکوراتور برای غیرفعال کردن CSRF در یک CBV (Class-Based View)
    برای محیط توسعه. در محیط تولید استفاده نشود.
    """
    view_class.dispatch = method_decorator(csrf_exempt)(view_class.dispatch)
    return view_class