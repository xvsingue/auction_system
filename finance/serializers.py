from rest_framework import serializers
from .models import TransactionRecord

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionRecord
        fields = '__all__'

class PaymentSerializer(serializers.Serializer):
    """模拟支付请求参数"""
    order_no = serializers.CharField()
    pay_password = serializers.CharField(write_only=True) # 模拟支付密码（毕设中通常复用登录密码或独立字段）