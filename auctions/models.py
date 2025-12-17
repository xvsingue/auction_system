from django.db import models
from items.models import AuctionItem


class AuctionSession(models.Model):
    """
    拍卖场次表 (auction_session)
    """
    TYPE_CHOICES = (
        ('increase', '增价拍卖'),
        ('decrease', '减价拍卖'),
    )

    STATUS_CHOICES = (
        (0, '未开始'),
        (1, '进行中'),
        (2, '已结束'),
    )

    name = models.CharField(max_length=200, verbose_name="场次名称")
    item = models.ForeignKey(AuctionItem, on_delete=models.CASCADE, related_name='sessions', verbose_name="关联拍品")

    start_time = models.DateTimeField(verbose_name="开始时间")
    end_time = models.DateTimeField(verbose_name="结束时间")

    auction_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='increase', verbose_name="拍卖类型")

    # 规则配置
    price_step = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="加/降价幅度",
                                     help_text="增价为最小加价，减价为每次降价")
    reduce_interval = models.IntegerField(default=0, blank=True, null=True, verbose_name="降价间隔(秒)",
                                          help_text="仅减价拍卖有效")
    bottom_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="底价",
                                       help_text="仅减价拍卖有效")

    # 状态与当前价（重要扩展）
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=0, verbose_name="状态")
    current_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="当前价格", blank=True, null=True)

    class Meta:
        verbose_name = "拍卖场次"
        verbose_name_plural = verbose_name
        db_table = 'auction_session'
        ordering = ['start_time']

    def __str__(self):
        return f"[{self.get_auction_type_display()}] {self.name}"

    def save(self, *args, **kwargs):
        # 创建时如果当前价为空，初始化为拍品的起拍价
        if not self.current_price and self.item:
            self.current_price = self.item.start_price
        super().save(*args, **kwargs)