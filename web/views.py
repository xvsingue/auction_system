from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


def index(request):
    """
    首页视图逻辑升级：
    1. 如果是【管理员】：直接跳转到数据看板（管理控制台），不让他看首页。
    2. 如果是【普通用户/游客】：正常展示拍卖首页。
    """
    if request.user.is_authenticated and request.user.role == 'admin':
        return redirect('dashboard')  # 这里的 'dashboard' 对应 urls.py 里的 name='dashboard'

    return render(request, 'index.html')


def login_page(request):
    return render(request, 'login.html')


def register_page(request):
    return render(request, 'register.html')


@login_required(login_url='/login/')
def create_item_page(request):
    """发布拍品页 (需要登录)"""
    return render(request, 'create_item.html')


@login_required(login_url='/login/')
def my_items_page(request):
    """我的拍品页 (需要登录)"""
    return render(request, 'my_items.html')


def auction_list_page(request):
    """拍卖大厅 (公开)"""
    return render(request, 'auction_list.html')


def auction_detail_page(request, pk):
    """
    拍卖详情页
    接收 URL 中的 pk 参数，并将其传给模板中的 session_id 变量
    """
    return render(request, 'auction_detail.html', {'session_id': pk})


@login_required(login_url='/login/')
def dashboard_page(request):
    """数据可视化看板 (仅管理员)"""
    if request.user.role != 'admin':
        # 如果不是管理员，踢回首页
        return redirect('/')
    return render(request, 'dashboard.html')

@login_required(login_url='/login/')
def my_orders_page(request):
    """我的订单页"""
    return render(request, 'my_orders.html')

@login_required(login_url='/login/')
def pay_order_page(request, order_no):
    """支付页"""
    return render(request, 'pay_order.html', {'order_no': order_no})

@login_required(login_url='/login/')
def profile_page(request):
    """个人中心页"""
    return render(request, 'profile.html')