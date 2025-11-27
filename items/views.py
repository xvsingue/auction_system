from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import AuctionItem, ItemCategory
from .serializers import (
    AuctionItemSerializer, ItemCreateSerializer,
    ItemCategorySerializer, ItemAuditSerializer
)


# items/views.py

class IsSellerOrReadOnly(permissions.BasePermission):
    """自定义权限：仅卖家可创建/修改，其他人只读"""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        # === 调试代码开始 ===
        print(f"--- 权限调试 ---")
        print(f"用户: {request.user}")
        print(f"是否登录: {request.user.is_authenticated}")
        if request.user.is_authenticated:
            print(f"用户角色: {getattr(request.user, 'role', 'No Role Field')}")
        print(f"--- 调试结束 ---")
        # === 调试代码结束 ===

        return request.user.is_authenticated and request.user.role == 'seller'


class IsAdminUser(permissions.BasePermission):
    """自定义权限：仅管理员"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    分类只读接口
    """
    queryset = ItemCategory.objects.all()
    serializer_class = ItemCategorySerializer
    permission_classes = [permissions.AllowAny]


class ItemViewSet(viewsets.ModelViewSet):
    """
    拍品管理接口
    包含：发布、查询、筛选、审核
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status']  # 支持按分类和状态筛选
    search_fields = ['name']  # 支持按名称搜索
    ordering_fields = ['start_price', 'create_time']

    def get_queryset(self):
        user = self.request.user
        # 1. 如果是管理员，看所有
        if user.is_authenticated and user.role == 'admin':
            return AuctionItem.objects.all()

        # 2. 如果是卖家，看自己的 + 其他已上架的
        # 但标准逻辑是列表页一般只展示“可竞拍”的。
        # 为了毕设演示方便：
        # - list: 只返回 status >= 1 (待开拍/竞拍中/已成交)
        # - retrieve: 允许查看详情
        # - 另外提供 action 查看 'my_items'

        if self.action == 'list':
            return AuctionItem.objects.filter(status__gte=1)

        return AuctionItem.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return ItemCreateSerializer
        if self.action == 'audit':
            return ItemAuditSerializer
        return AuctionItemSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsSellerOrReadOnly()]
        if self.action == 'audit':
            return [IsAdminUser()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def perform_create(self, serializer):
        # 已经在 Serializer 中处理了 seller，这里只需占位
        serializer.save()

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_items(self, request):
        """查看我发布的拍品 (卖家专用)"""
        items = AuctionItem.objects.filter(seller=request.user)
        serializer = AuctionItemSerializer(items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def audit(self, request, pk=None):
        """
        管理员审核接口
        POST /api/items/{id}/audit/
        body: { "status": 1 }  (1=通过/待开拍)
        """
        item = self.get_object()
        serializer = ItemAuditSerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "审核完成"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)