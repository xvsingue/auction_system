from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import TransactionRecord, Deposit
from .serializers import TransactionSerializer, PaymentSerializer
from trades.models import AuctionOrder
from items.models import AuctionItem
from decimal import Decimal


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

        # 2. 计算需支付金额 = 成交价 - 已付保证金
        pay_amount = order.final_price - order.deposit

        # 防御性检查
        if pay_amount < 0:
            pay_amount = Decimal('0.00')

        if user.balance < pay_amount:
            return Response({"error": f"余额不足，需支付尾款 ¥{pay_amount}"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. 原子交易
        with transaction.atomic():
            # 扣减买家余额 (只扣尾款)
            user.balance -= pay_amount
            user.save()

            # === 计算卖家收入 ===
            # 手续费 (假设按成交全额的 5% 计算)
            fee_rate = Decimal('0.05')
            fee = order.final_price * fee_rate

            # 卖家实际收入 = (尾款 + 保证金) - 手续费
            total_received = pay_amount + order.deposit
            seller_income = total_received - fee

            # 增加卖家余额
            seller = order.seller
            seller.balance += seller_income
            seller.save()

            # 更新订单
            order.status = 1  # 已支付
            order.service_fee = fee
            order.save()

            # 记录流水 (买家)
            TransactionRecord.objects.create(
                user=user, amount=-pay_amount, balance_after=user.balance,
                trans_type='payment', order=order, remark=f"支付订单尾款 {order.order_no}"
            )

            # 记录流水 (卖家)
            TransactionRecord.objects.create(
                user=seller, amount=seller_income, balance_after=seller.balance,
                trans_type='income', order=order, remark=f"订单收入 {order.order_no} (含保证金,扣手续费)"
            )

        return Response({"message": "支付成功"})

    @action(detail=False, methods=['post'])
    def pay_deposit(self, request):
        """
        缴纳保证金接口
        POST /api/finance/pay_deposit/
        body: { "item_id": 1 }
        """
        item_id = request.data.get('item_id')
        if not item_id:
            return Response({"error": "缺少 item_id 参数"}, status=status.HTTP_400_BAD_REQUEST)

        item = get_object_or_404(AuctionItem, id=item_id)
        user = request.user

        # 1. 检查是否已缴纳
        if Deposit.objects.filter(user=user, auction_item=item, status='paid').exists():
            return Response({"message": "您已缴纳过保证金，无需重复缴纳"}, status=status.HTTP_200_OK)

        # 2. 计算保证金金额 = 起拍价 * (保证金比例 / 100)
        ratio = item.deposit_ratio  # 模型里是 20.00
        deposit_amount = item.start_price * (ratio / Decimal('100.0'))

        # 3. 检查余额
        if user.balance < deposit_amount:
            return Response({"error": f"余额不足，需缴纳保证金 ¥{deposit_amount}"},
                            status=status.HTTP_402_PAYMENT_REQUIRED)

        # 4. 原子操作：扣款 + 记录
        try:
            with transaction.atomic():
                # 扣减用户余额
                user.balance -= deposit_amount
                user.save()

                # 创建保证金记录
                Deposit.objects.create(
                    user=user,
                    auction_item=item,
                    amount=deposit_amount,
                    status='paid'
                )

                # 创建资金流水记录
                TransactionRecord.objects.create(
                    user=user,
                    amount=-deposit_amount,
                    balance_after=user.balance,
                    trans_type='payment',
                    remark=f"缴纳拍品[{item.name}]保证金"
                )

            return Response({
                "message": "保证金缴纳成功",
                "amount": deposit_amount,
                "balance": user.balance
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"系统错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
