from rest_framework.authentication import SessionAuthentication

class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    自定义的 Session 认证类
    强制关闭 DRF 的 CSRF 检查，彻底解决 403 问题
    """
    def enforce_csrf(self, request):
        return  # 什么都不做，直接通过