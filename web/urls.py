from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_page, name='login_page'),
    path('register/', views.register_page, name='register_page'),

    # 新增路由
    path('create-item/', views.create_item_page, name='create_item'),
    path('my-items/', views.my_items_page, name='my_items'),
    path('auctions/', views.auction_list_page, name='auction_list'),

    # === 新增：详情页路由 ===
    # <int:pk> 会捕获 URL 中的数字ID，并传给 views.auction_detail_page
    path('auction/<int:pk>/', views.auction_detail_page, name='auction_detail'),
    path('dashboard/', views.dashboard_page, name='dashboard'),  # 管理员页面
    path('my-orders/', views.my_orders_page, name='my_orders'),
    path('pay-order/<str:order_no>/', views.pay_order_page, name='pay_order'),
    path('profile/', views.profile_page, name='profile'),

]
