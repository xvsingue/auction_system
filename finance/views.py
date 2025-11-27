from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import TransactionRecord
from .serializers import TransactionSerializer, PaymentSerializer
from trades.models import AuctionOrder
from decimal import Decimal  # <--- 核心修改1：引入 Decimal


class FinanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    资金流水查询 & 支付操作
    """
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TransactionRecord.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def pay_order(self, request):
        """
        模拟支付接口
        POST /api/finance/pay_order/
        """
        serializer = PaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order_no = serializer.validated_data['order_no']
        password = serializer.validated_data['pay_password']
        user = request.user

        # 1. 验证密码
        if not user.check_password(password):
            return Response({"error": "支付密码错误"}, status=status.HTTP_403_FORBIDDEN)

        try:
            order = AuctionOrder.objects.get(order_no=order_no, buyer=user)
        except AuctionOrder.DoesNotExist:
            return Response({"error": "订单不存在"}, status=status.HTTP_404_NOT_FOUND)

        if order.status != 0:  # 0=未支付
            return Response({"error": "订单状态不正确"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. 计算金额
        pay_amount = order.final_price

        if user.balance < pay_amount:
            return Response({"error": "余额不足，请充值"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. 原子交易
        with transaction.atomic():
            # 扣减买家
            user.balance -= pay_amount
            user.save()

            # === 核心修改开始 ===
            # 计算手续费 (全部使用 Decimal 防止报错)
            fee_rate = Decimal('0.05')  # 5% 手续费
            fee = pay_amount * fee_rate

            # 计算卖家实际收入
            seller_income = pay_amount - fee

            # 增加卖家余额
            seller = order.seller
            seller.balance += seller_income
            seller.save()
            # === 核心修改结束 ===

            # 更新订单
            order.status = 1  # 已支付
            order.service_fee = fee
            order.save()

            # 记录流水 (买家)
            TransactionRecord.objects.create(
                user=user, amount=-pay_amount, balance_after=user.balance,
                trans_type='payment', order=order, remark=f"支付订单 {order.order_no}"
            )

            # 记录流水 (卖家)
            TransactionRecord.objects.create(
                user=seller, amount=seller_income, balance_after=seller.balance,
                trans_type='income', order=order, remark=f"订单收入 {order.order_no} (已扣手续费)"
            )

        return Response({"message": "支付成功"})

    @action(detail=False, methods=['post'])
    def top_up(self, request):
        """测试用充值接口"""
        amount = Decimal(request.data.get('amount', 10000))  # 确保转为 Decimal
        request.user.balance += amount
        request.user.save()
        TransactionRecord.objects.create(
            user=request.user, amount=amount, balance_after=request.user.balance,
            trans_type='topup', remark="系统测试充值"
        )
        return Response({"message": f"充值成功，当前余额: {request.user.balance}"})


