from rest_framework import views, permissions
from rest_framework.response import Response
from users.models import UserProfile
from items.models import AuctionItem
from trades.models import AuctionOrder
from finance.models import Deposit
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth


class DashboardView(views.APIView):
    """
    数据可视化接口
    GET /api/system/dashboard/
    """
    permission_classes = [permissions.IsAuthenticated]  # 建议仅管理员可见

    def get(self, request):
        # 1. 基础统计
        total_users = UserProfile.objects.count()
        total_items = AuctionItem.objects.count()

        # 总成交额 (已支付的订单)
        total_volume = AuctionOrder.objects.filter(status=1).aggregate(sum=Sum('final_price'))['sum'] or 0

        # === 2. 新增：保证金资金池统计 ===
        # 统计当前还在冻结中(status='paid')的保证金总额，展示平台沉淀资金
        active_deposits = Deposit.objects.filter(status='paid').aggregate(sum=Sum('amount'))['sum'] or 0

        # 3. 拍品分类占比 (饼图)
        # 需在 AuctionItem 中关联 Category
        category_data = AuctionItem.objects.values('category__name').annotate(count=Count('id'))

        # 4. 近期成交趋势 (折线图)

        return Response({
            "stats": {
                "users": total_users,
                "items": total_items,
                "volume": total_volume,
                "active_deposits": active_deposits,  # <--- 3. 将保证金数据返回给前端
            },
            "charts": {
                "categories": category_data
            }
        })