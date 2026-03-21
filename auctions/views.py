from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import AuctionSession
from .serializers import AuctionSessionSerializer, SessionCreateSerializer


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == 'admin'


class AuctionSessionViewSet(viewsets.ModelViewSet):
    """
    拍卖场次接口
    """
    queryset = AuctionSession.objects.all().order_by('-start_time')
    pagination_class = None  # 取消分页，让前端本地过滤可以囊括所有数据
    permission_classes = [IsAdminOrReadOnly]

    # 筛选与搜索
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'auction_type']
    search_fields = ['name', 'item__name']
    ordering_fields = ['start_time', 'current_price']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SessionCreateSerializer
        return AuctionSessionSerializer

    def perform_destroy(self, instance):
        # 仅未开始的场次允许删除
        if instance.status != 0:
            raise permissions.exceptions.PermissionDenied("只能删除未开始的场次")
        instance.delete()