from rest_framework import views, permissions
from rest_framework.response import Response
from users.models import UserProfile
from items.models import AuctionItem
from trades.models import AuctionOrder
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
        total_volume = AuctionOrder.objects.filter(status=1).aggregate(sum=Sum('final_price'))['sum'] or 0

        # 2. 拍品分类占比 (饼图)
        # 需在 AuctionItem 中关联 Category，这里演示聚合逻辑
        category_data = AuctionItem.objects.values('category__name').annotate(count=Count('id'))

        # 3. 近期成交趋势 (折线图 - 简单版)
        # 实际开发需按月份/日期 group by

        return Response({
            "stats": {
                "users": total_users,
                "items": total_items,
                "volume": total_volume
            },
            "charts": {
                "categories": category_data
            }
        })