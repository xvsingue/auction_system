from django.db.models import Q
from rest_framework import viewsets, permissions, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from .models import BidRecord, AuctionOrder
from .serializers import BidRecordSerializer, BidCreateSerializer, OrderSerializer
from auctions.models import AuctionSession
from finance.models import Deposit
from .utils import RedisAuctionHelper
from decimal import Decimal
import uuid


class BidViewSet(viewsets.GenericViewSet):
    """
    竞价接口
    """
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def place_bid(self, request):
        """
        核心接口：用户出价/抢拍
        POST /api/trades/bids/place_bid/
        body: { "session_id": 1, "bid_price": 100.00 }
        """
        # 必须加上 context={'request': request}，否则序列化器里拿不到 request.user
        serializer = BidCreateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        session = AuctionSession.objects.get(pk=data['session_id'])
        user = request.user
        price = data['bid_price']

        # === 增价拍卖处理 ===
        if session.auction_type == 'increase':
            with transaction.atomic():
                # 1. 悲观锁查询场次，防止并发更新覆盖
                session_locked = AuctionSession.objects.select_for_update().get(pk=session.id)

                # 再次校验价格 (防止查询期间被别人加价)
                if price < (session_locked.current_price + session_locked.price_step):
                    return Response({"error": "手慢了，价格已被更新"}, status=status.HTTP_400_BAD_REQUEST)

                # 2. 更新旧的领先者状态
                BidRecord.objects.filter(session=session, is_leading=True).update(is_leading=False)

                # 3. 插入新记录
                BidRecord.objects.create(
                    session=session, buyer=user, bid_price=price, is_leading=True
                )

                # 4. 更新场次当前价
                session_locked.current_price = price
                session_locked.save()

                # 5. 更新 Redis (供前端实时刷新)
                helper = RedisAuctionHelper(session.id)
                helper.set_current_price(price)

            return Response({"message": "出价成功", "current_price": price})

        # === 减价拍卖处理 (抢拍) ===
        elif session.auction_type == 'decrease':
            helper = RedisAuctionHelper(session.id)
            lock_id = helper.acquire_lock()

            if not lock_id:
                return Response({"error": "正如火如荼，请重试"}, status=status.HTTP_409_CONFLICT)

            try:
                # 检查是否已结束
                session.refresh_from_db()
                if session.status != 1:
                    return Response({"error": "很遗憾，已被抢走"}, status=status.HTTP_400_BAD_REQUEST)

                with transaction.atomic():
                    # 1. 生成成交记录
                    BidRecord.objects.create(session=session, buyer=user, bid_price=price, is_leading=True)

                    # === 处理保证金流转 ===
                    deposit_amount = Decimal('0.00')
                    # 查找并锁定该用户的保证金记录
                    deposit_record = Deposit.objects.filter(
                        user=user,
                        auction_item=session.item,
                        status='paid'
                    ).first()

                    if deposit_record:
                        deposit_record.status = 'transferred'  # 转为货款
                        deposit_record.save()
                        deposit_amount = deposit_record.amount
                    # ===================

                    # 2. 结束场次
                    session.status = 2  # 已结束
                    session.current_price = price
                    session.save()

                    # 3. 更新拍品状态
                    item = session.item
                    item.status = 3  # 已成交
                    item.save()

                    # 4. 生成订单
                    order_no = f"ORD-{uuid.uuid4().hex[:12].upper()}"
                    AuctionOrder.objects.create(
                        order_no=order_no,
                        session=session,
                        buyer=user,
                        seller=session.item.seller,
                        final_price=price,
                        deposit=deposit_amount,  # 记录保证金，以便支付时抵扣
                        status=0  # 未支付
                    )

                return Response({"message": "抢拍成功！订单已生成", "order_no": order_no})

            finally:
                helper.release_lock(lock_id)

    @action(detail=False, methods=['get'])
    def history(self, request):
        """查看某场次的出价历史"""
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response({"error": "缺少 session_id"}, status=status.HTTP_400_BAD_REQUEST)

        bids = BidRecord.objects.filter(session_id=session_id).order_by('-bid_price')
        page = self.paginate_queryset(bids)  # 需要在 ViewSet 中配置分页
        serializer = BidRecordSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    订单查看接口 (仅查看自己的)
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # 买家看自己买的，卖家看自己卖的
        return AuctionOrder.objects.filter(Q(buyer=user) | Q(seller=user))