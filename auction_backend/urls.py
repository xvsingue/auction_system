from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),  # 注册用户模块 API
    path('api/items/', include('items.urls')),  # 拍品
    path('api/auctions/', include('auctions.urls')),  # 拍卖
    path('api/trades/', include('trades.urls')),  # 竞价交易
    path('api/system/', include('system.urls')),
    path('api/finance/', include('finance.urls')),

    # 前端页面路由
    path('', include('web.urls')),

]

# 开发环境挂载媒体文件路由，否则无法访问上传的图片
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
