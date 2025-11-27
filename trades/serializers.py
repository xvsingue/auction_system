from rest_framework import serializers
from .models import BidRecord, AuctionOrder
from auctions.models import AuctionSession
from decimal import Decimal


class BidRecordSerializer(serializers.ModelSerializer):
    """竞价记录展示"""
    username = serializers.CharField(source='buyer.username', read_only=True)

    class Meta:
        model = BidRecord
        fields = ['id', 'session', 'username', 'bid_price', 'bid_time', 'is_leading']


class BidCreateSerializer(serializers.Serializer):
    """
    竞价操作序列化器
    不直接绑定 Model，因为涉及复杂的业务逻辑校验
    """
    session_id = serializers.IntegerField()
    bid_price = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate(self, data):
        session_id = data['session_id']
        bid_price = data['bid_price']

        try:
            session = AuctionSession.objects.get(pk=session_id)
        except AuctionSession.DoesNotExist:
            raise serializers.ValidationError("场次不存在")

        if session.status != 1:  # 1=进行中
            raise serializers.ValidationError("当前场次未开始或已结束")

        # 增价拍卖逻辑校验
        if session.auction_type == 'increase':
            # 必须大于 (当前最高价 + 加价幅度)
            # 优先从 Redis 取，没有则取数据库
            current_price = session.current_price
            min_price = current_price + session.price_step
            if bid_price < min_price:
                raise serializers.ValidationError(f"出价过低，最低需出价: {min_price}")

        # 减价拍卖逻辑校验 (抢拍)
        elif session.auction_type == 'decrease':
            # 减价拍卖通常是点击“抢拍”，价格由系统当前价决定，前端传来的价格用于校验一致性
            current_price = session.current_price
            if abs(bid_price - current_price) > Decimal('0.5'):  # 允许细微误差
                raise serializers.ValidationError("价格已变动，请刷新后重试")

        return data


class OrderSerializer(serializers.ModelSerializer):
    """订单展示"""
    item_name = serializers.CharField(source='session.item.name', read_only=True)

    class Meta:
        model = AuctionOrder
        fields = '__all__'