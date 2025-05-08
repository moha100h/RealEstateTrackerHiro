"""
Views related to security features
"""
import json
import logging
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# Logger for security events
security_logger = logging.getLogger('security')

@csrf_exempt
@require_POST
def csp_report_view(request):
    """
    Endpoint for receiving Content Security Policy violation reports
    """
    try:
        # Parse the CSP report from the request body
        csp_report = json.loads(request.body.decode('utf-8'))
        
        # Extract relevant information
        document_uri = csp_report.get('csp-report', {}).get('document-uri', 'unknown')
        blocked_uri = csp_report.get('csp-report', {}).get('blocked-uri', 'unknown')
        violated_directive = csp_report.get('csp-report', {}).get('violated-directive', 'unknown')
        original_policy = csp_report.get('csp-report', {}).get('original-policy', 'unknown')
        
        # Check if user is authenticated before accessing user.username
        username = 'anonymous'
        if hasattr(request, 'user') and request.user.is_authenticated:
            username = request.user.username
        
        # Log the CSP violation with relevant details
        security_logger.warning(
            f"CSP Violation: {violated_directive} directive violated on {document_uri} by {blocked_uri}",
            extra={
                'ip': request.META.get('REMOTE_ADDR', 'unknown'),
                'user': username,
                'document_uri': document_uri,
                'blocked_uri': blocked_uri,
                'violated_directive': violated_directive,
                'original_policy': original_policy
            }
        )
        
        return HttpResponse(status=204)  # No content response
    
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        security_logger.error(f"Failed to process CSP report: {str(e)}")
        return JsonResponse({'error': 'Invalid CSP report format'}, status=400)

@csrf_exempt
def security_headers_test_view(request):
    """
    View to test security headers
    This is only accessible in DEBUG mode
    """
    from django.conf import settings
    
    if not settings.DEBUG:
        return HttpResponse("Forbidden: This page is only available in DEBUG mode".encode('utf-8'), status=403)
    
    headers = {}
    
    # Content Security Policy
    headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'"
    
    # HTTP Strict Transport Security
    headers['Strict-Transport-Security'] = "max-age=31536000; includeSubDomains"
    
    # X-Content-Type-Options
    headers['X-Content-Type-Options'] = "nosniff"
    
    # X-Frame-Options
    headers['X-Frame-Options'] = "SAMEORIGIN"
    
    # X-XSS-Protection
    headers['X-XSS-Protection'] = "1; mode=block"
    
    # Referrer-Policy
    headers['Referrer-Policy'] = "strict-origin-when-cross-origin"
    
    # Feature-Policy
    headers['Feature-Policy'] = "geolocation 'self'; microphone 'none'; camera 'none'"
    
    # Permissions-Policy (newer version of Feature-Policy)
    headers['Permissions-Policy'] = "geolocation=(self), microphone=(), camera=()"
    
    html_content = """
        <html>
        <head>
            <title>Security Headers Test</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; direction: rtl; }
                h1 { color: #333; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { padding: 10px; text-align: right; border: 1px solid #ddd; }
                th { background-color: #f5f5f5; }
                tr:nth-child(even) { background-color: #f9f9f9; }
                code { font-family: monospace; background-color: #f5f5f5; padding: 2px 4px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h1>تست هدرهای امنیتی</h1>
            <p>این صفحه برای آزمایش هدرهای امنیتی است. هدرهای زیر در پاسخ HTTP این صفحه گنجانده شده‌اند:</p>
            
            <table>
                <tr>
                    <th>هدر</th>
                    <th>مقدار</th>
                    <th>توضیحات</th>
                </tr>
                <tr>
                    <td>Content-Security-Policy</td>
                    <td><code>default-src 'self'; script-src 'self' 'unsafe-inline'</code></td>
                    <td>محدود کردن منابع مجاز برای بارگذاری محتوا</td>
                </tr>
                <tr>
                    <td>Strict-Transport-Security</td>
                    <td><code>max-age=31536000; includeSubDomains</code></td>
                    <td>اجبار استفاده از HTTPS</td>
                </tr>
                <tr>
                    <td>X-Content-Type-Options</td>
                    <td><code>nosniff</code></td>
                    <td>جلوگیری از MIME type sniffing</td>
                </tr>
                <tr>
                    <td>X-Frame-Options</td>
                    <td><code>SAMEORIGIN</code></td>
                    <td>محافظت از Clickjacking</td>
                </tr>
                <tr>
                    <td>X-XSS-Protection</td>
                    <td><code>1; mode=block</code></td>
                    <td>محافظت از حملات XSS</td>
                </tr>
                <tr>
                    <td>Referrer-Policy</td>
                    <td><code>strict-origin-when-cross-origin</code></td>
                    <td>کنترل اطلاعات Referrer</td>
                </tr>
                <tr>
                    <td>Feature-Policy</td>
                    <td><code>geolocation 'self'; microphone 'none'; camera 'none'</code></td>
                    <td>محدود کردن دسترسی به ویژگی‌های حساس</td>
                </tr>
                <tr>
                    <td>Permissions-Policy</td>
                    <td><code>geolocation=(self), microphone=(), camera=()</code></td>
                    <td>نسخه جدیدتر Feature-Policy</td>
                </tr>
            </table>
            
            <h2>تست CSP</h2>
            <p>این اسکریپت اجرا نخواهد شد، چون منبع آن با CSP مطابقت ندارد:</p>
            <pre><code>&lt;script src="https://example.com/malicious.js"&gt;&lt;/script&gt;</code></pre>
            <script src="https://example.com/malicious.js"></script>
            
            <h2>اطلاعات مرورگر</h2>
            <p>User-Agent شما: <code id="user-agent">?</code></p>
            
            <script>
                // این اسکریپت اجرا خواهد شد، چون با CSP مطابقت دارد
                document.getElementById('user-agent').textContent = navigator.userAgent;
            </script>
        </body>
        </html>
        """
    
    response = HttpResponse(html_content.encode('utf-8'))
    
    # Add all headers to the response
    for header, value in headers.items():
        response[header] = value
    
    return response