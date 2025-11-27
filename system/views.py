from rest_framework import views, permissions
from rest_framework.response import Response
from users.models import UserProfile
from items.models import AuctionItem
from trades.models import AuctionOrder
from finance.models import Deposit
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta


class DashboardView(views.APIView):
    """
    数据可视化接口
    GET /api/system/dashboard/
    """
    # 建议仅管理员可见，如果要做权限控制可以加上 IsAdminUser
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # === 1. 基础统计 ===
        total_users = UserProfile.objects.count()
        total_items = AuctionItem.objects.count()

        # 总成交额 (统计状态为1-已支付的订单)
        total_volume = AuctionOrder.objects.filter(status=1).aggregate(sum=Sum('final_price'))['sum'] or 0

        # 保证金资金池 (统计当前还在冻结中 status='paid' 的保证金总额)
        active_deposits = Deposit.objects.filter(status='paid').aggregate(sum=Sum('amount'))['sum'] or 0

        # === 2. 拍品分类占比 (饼图数据) ===
        # 按分类名称分组统计数量
        category_data = AuctionItem.objects.values('category__name').annotate(count=Count('id'))

        # === 3. 近期成交趋势 (折线/柱状图数据) ===
        # 计算最近 7 天每一天的成交额
        trend_dates = []
        trend_values = []

        today = timezone.now().date()

        # 循环生成过去7天的日期（从6天前到今天）
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            date_str = date.strftime('%m-%d')  # 格式化为 "11-27"

            # 查询当天的成交总额
            # 注意：这里使用 create_time__date 进行日期匹配
            day_volume = AuctionOrder.objects.filter(
                status=1,  # 仅统计已支付/已完成的订单
                create_time__date=date
            ).aggregate(sum=Sum('final_price'))['sum'] or 0

            trend_dates.append(date_str)
            trend_values.append(day_volume)

        # === 4. 组装返回数据 ===
        return Response({
            "stats": {
                "users": total_users,
                "items": total_items,
                "volume": total_volume,
                "active_deposits": active_deposits,  # 保证金池
            },
            "charts": {
                "categories": category_data,
                "trend": {
                    "dates": trend_dates,  # X轴日期
                    "values": trend_values  # Y轴金额
                }
            }
        })