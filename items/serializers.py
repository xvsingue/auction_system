from rest_framework import serializers
from .models import AuctionItem, ItemCategory
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import uuid


class ItemCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemCategory
        fields = '__all__'


class AuctionItemSerializer(serializers.ModelSerializer):
    """
    拍品通用序列化器 (读取用)
    """
    seller_name = serializers.CharField(source='seller.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    images = serializers.ListField(child=serializers.CharField(), source='get_images', read_only=True)  # 前端拿到的是数组

    class Meta:
        model = AuctionItem
        fields = [
            'id', 'name', 'category', 'category_name', 'seller', 'seller_name',
            'start_price', 'reserve_price', 'deposit_ratio', 'earnest_money_ratio',
            'images', 'description', 'status', 'reject_reason', 'create_time',
            'auction_type', 'price_step', 'reduce_interval', 'bottom_price',
            'expected_start_time', 'expected_end_time'
        ]
        read_only_fields = ['seller', 'status', 'reject_reason', 'create_time']


class ItemCreateSerializer(serializers.ModelSerializer):
    """
    拍品创建序列化器 (写入用)
    处理多图上传逻辑
    """
    # 接收前端上传的文件列表 (key: 'upload_images')
    upload_images = serializers.ListField(
        child=serializers.ImageField(max_length=1000000, allow_empty_file=False, use_url=False),
        write_only=True,
        required=True,
        max_length=5  # 限制最多5张
    )

    class Meta:
        model = AuctionItem
        fields = [
            'name', 'category', 'start_price', 'reserve_price', 'description',
            'deposit_ratio', 'earnest_money_ratio', 'upload_images',
            'auction_type', 'price_step', 'reduce_interval', 'bottom_price',
            'expected_start_time', 'expected_end_time'
        ]

    def validate(self, data):
        # 时间逻辑校验
        st = data.get('expected_start_time')
        et = data.get('expected_end_time')
        if st and et and st >= et:
            raise serializers.ValidationError({"expected_end_time": "结束时间必须晚于开拍时间。"})
        # 减价拍卖规则校验
        if data.get('auction_type') == 'decrease':
            if not data.get('reduce_interval') or data.get('reduce_interval') <= 0:
                raise serializers.ValidationError({"reduce_interval": "减价拍卖必须设置有效的降价间隔(>0)。"})
            if not data.get('bottom_price') and data.get('bottom_price') != 0:
                raise serializers.ValidationError({"bottom_price": "减价拍卖必须设置底价。"})
            if data.get('bottom_price') >= data.get('start_price'):
                raise serializers.ValidationError({"bottom_price": "底价必须低于起拍价。"})
        
        # 必须提供有效的 price_step
        if data.get('price_step') is None or data.get('price_step') <= 0:
            raise serializers.ValidationError({"price_step": "必须设置有效的加/降价幅度(>0)。"})
            
        return data

    def create(self, validated_data):
        images = validated_data.pop('upload_images')
        user = self.context['request'].user

        # 1. 处理图片保存
        path_list = []
        for image in images:
            # 生成随机文件名防止冲突
            ext = os.path.splitext(image.name)[1]
            filename = f"auction_items/{uuid.uuid4().hex}{ext}"
            saved_path = default_storage.save(filename, ContentFile(image.read()))
            path_list.append(saved_path)

        # 2. 拼接路径
        image_paths_str = ','.join(path_list)

        # 3. 创建对象
        item = AuctionItem.objects.create(
            seller=user,
            image_paths=image_paths_str,
            status=0,  # 默认为待审核
            **validated_data
        )
        return item


class ItemAuditSerializer(serializers.ModelSerializer):
    """
    管理员审核用的序列化器
    """

    class Meta:
        model = AuctionItem
        fields = ['status', 'reject_reason']

    def validate(self, data):
        # 如果是驳回(这里假设状态4代表流拍/驳回，或者我们定义特定逻辑，
        # 文档中status=0待审核, 1待开拍。这里我们约定：管理员审核不通过不删除，而是保持0或设为特定状态？
        # 根据文档3.2.1，支持通过/驳回。我们可以约定驳回状态仍为0但有reject_reason，或者新增状态。
        # 为简单起见，这里只更新状态。
        return data