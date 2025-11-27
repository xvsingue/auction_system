from django.shortcuts import redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from rest_framework import views, generics, status, permissions, authentication
from rest_framework.response import Response
from .serializers import UserRegistrationSerializer, UserProfileSerializer


class RegisterView(views.APIView):
    """
    API: 用户注册
    POST /api/users/register/
    """
    permission_classes = [permissions.AllowAny]  # 允许未登录用户访问

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # 注册后是否自动登录视业务而定，此处选择注册成功后让用户去登录
            return Response({"message": "注册成功", "user_id": user.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(views.APIView):
    """
    API: 用户登录 (Session模式)
    POST /api/users/login/
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        # Django auth 验证
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)  # 写入 Session
                return Response({
                    "message": "登录成功",
                    "role": user.role,
                    "username": user.username
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "账号已被禁用"}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({"error": "用户名或密码错误"}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(views.APIView):
    """
    API: 用户登出
    POST /api/users/logout/
    """

    def post(self, request):
        logout(request)
        return Response({"message": "已登出"}, status=status.HTTP_200_OK)


class UserInfoView(generics.RetrieveUpdateAPIView):
    """
    API: 获取/修改当前用户信息
    GET/PATCH /api/users/me/
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]  # 必须登录

    def get_object(self):
        # 直接返回当前登录用户，不依赖 URL 中的 ID，更加安全
        return self.request.user


class LogoutView(views.APIView):
    """
    API: 用户登出
    POST /api/users/logout/
    """

    def post(self, request):
        logout(request)

        # 判断请求来源：如果是 AJAX/API 请求，返回 JSON
        # 如果是浏览器表单提交 (HTML form)，执行跳转
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return Response({"message": "已登出"}, status=status.HTTP_200_OK)

        # 核心修改：直接重定向到登录页
        return redirect('/login/')


class ChangePasswordView(views.APIView):
    """
    API: 修改密码
    POST /api/users/change_password/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        old_pwd = request.data.get('old_password')
        new_pwd = request.data.get('new_password')

        if not user.check_password(old_pwd):
            return Response({"error": "旧密码不正确"}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_pwd) < 6:
            return Response({"error": "新密码长度至少6位"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_pwd)
        user.save()

        # 关键：更新 Session，否则改密码后会被踢下线
        update_session_auth_hash(request, user)

        return Response({"message": "密码修改成功"}, status=status.HTTP_200_OK)
