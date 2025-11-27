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


from django.db import models
from django.conf import settings
from trades.models import AuctionOrder


# === 保证金 ===
class Deposit(models.Model):
    """
    保证金记录表
    """
    STATUS_CHOICES = (
        ('paid', '已缴纳'),
        ('refunded', '已退回'),
        ('deducted', '已扣除(违约)'),
        ('transferred', '已转货款'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="缴纳用户")
    # 指向 items 应用下的 AuctionItem
    auction_item = models.ForeignKey('items.AuctionItem', on_delete=models.CASCADE, verbose_name="关联拍品")

    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="保证金金额")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='paid', verbose_name="状态")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="缴纳时间")

    class Meta:
        verbose_name = "拍卖保证金"
        verbose_name_plural = verbose_name
        # 联合唯一索引：防止同一个用户对同一个拍品重复交保证金
        unique_together = ('user', 'auction_item')

    def __str__(self):
        return f"{self.user.username} - {self.auction_item.name}"
