from django.db import models
from django.conf import settings
from trades.models import AuctionOrder

class TransactionRecord(models.Model):
    """
    资金流水表
    """
    TYPE_CHOICES = (
        ('topup', '充值'),
        ('payment', '支付订单'),
        ('income', '出售收入'),
        ('refund', '退款'),
        ('service_fee', '服务费扣除'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="用户")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="变动金额")
    balance_after = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="变动后余额")
    trans_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="交易类型")
    order = models.ForeignKey(AuctionOrder, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="关联订单")
    remark = models.CharField(max_length=200, blank=True, verbose_name="备注")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="交易时间")

    class Meta:
        verbose_name = "资金流水"
        verbose_name_plural = verbose_name
        ordering = ['-create_time']


