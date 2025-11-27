from rest_framework import serializers
from .models import AuctionSession
from items.serializers import AuctionItemSerializer


class AuctionSessionSerializer(serializers.ModelSerializer):
    """
    场次通用序列化器 (包含拍品详情，适合列表/详情页)
    """
    item_detail = AuctionItemSerializer(source='item', read_only=True)  # 嵌套拍品信息
    status_text = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = AuctionSession
        fields = [
            'id', 'name', 'item', 'item_detail', 'start_time', 'end_time',
            'auction_type', 'price_step', 'reduce_interval', 'bottom_price',
            'status', 'status_text', 'current_price'
        ]
        read_only_fields = ['status', 'current_price']


class SessionCreateSerializer(serializers.ModelSerializer):
    """
    场次创建序列化器
    """

    class Meta:
        model = AuctionSession
        fields = [
            'name', 'item', 'start_time', 'end_time',
            'auction_type', 'price_step', 'reduce_interval', 'bottom_price'
        ]

    def validate(self, data):
        # 1. 时间校验
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("结束时间必须晚于开始时间")

        # 2. 拍品状态校验
        item = data['item']
        # 只有"待开拍"或"流拍"的商品才能重新创建场次
        # 注意：这里逻辑要灵活，暂定必须是审核通过(status=1)的
        if item.status != 1:
            raise serializers.ValidationError(f"拍品 {item.name} 当前状态不可排期（需为待开拍状态）")

        # 3. 减价拍卖规则校验
        if data['auction_type'] == 'decrease':
            if not data.get('reduce_interval') or data.get('reduce_interval') <= 0:
                raise serializers.ValidationError("减价拍卖必须设置有效的降价间隔")
            if not data.get('bottom_price'):
                raise serializers.ValidationError("减价拍卖必须设置底价")
            if data.get('bottom_price') >= item.start_price:
                raise serializers.ValidationError("底价必须低于起拍价")

        return data

    def create(self, validated_data):
        session = super().create(validated_data)
        # 自动初始化当前价为起拍价
        session.current_price = session.item.start_price
        session.save()
        return session