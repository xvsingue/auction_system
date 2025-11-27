from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from auctions.models import AuctionSession
from finance.models import Deposit
from decimal import Decimal


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
    拍卖详情页 (逻辑升级)
    pk: 对应 AuctionSession 的 id
    """
    # 1. 获取场次信息
    session = get_object_or_404(AuctionSession, pk=pk)

    # 2. 计算需缴纳的保证金金额 = 起拍价 * (保证金比例 / 100)
    # 注意转为 Decimal 防止精度丢失
    ratio = session.item.deposit_ratio
    deposit_amount = session.item.start_price * (ratio / Decimal('100.0'))

    # 3. 检查当前用户是否已缴纳 (仅针对登录用户)
    has_paid_deposit = False
    if request.user.is_authenticated:
        has_paid_deposit = Deposit.objects.filter(
            user=request.user,
            auction_item=session.item,
            status='paid'
        ).exists()

    # 4. 组装上下文数据传给模板
    context = {
        'session_id': pk,
        'session': session,  # 场次对象
        'item': session.item,  # 关联的拍品对象
        'deposit_amount': round(deposit_amount, 2),  # 保证金金额(保留2位小数)
        'has_paid_deposit': has_paid_deposit  # 核心状态：True/False
    }
    return render(request, 'auction_detail.html', context)


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