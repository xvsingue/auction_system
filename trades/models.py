from django.db import models
from django.conf import settings
from auctions.models import AuctionSession


class BidRecord(models.Model):
    """
    竞拍记录表 (bid_record)
    对应毕设文档 4.1.4
    """
    session = models.ForeignKey(AuctionSession, on_delete=models.CASCADE, related_name='bids', verbose_name="所属场次")
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="竞买人")
    bid_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="出价金额")
    bid_time = models.DateTimeField(auto_now_add=True, verbose_name="出价时间")
    # 冗余字段，方便查询当前最高
    is_leading = models.BooleanField(default=False, verbose_name="是否领先")

    class Meta:
        verbose_name = "竞价记录"
        verbose_name_plural = verbose_name
        ordering = ['-bid_price']  # 默认按价格倒序

    def __str__(self):
        return f"{self.session.name} - {self.bid_price}"


class AuctionOrder(models.Model):
    """
    订单表 (auction_order)
    对应毕设文档 4.1.5
    """
    STATUS_CHOICES = (
        (0, '未支付'),
        (1, '已支付'),
        (2, '已取消'),
        (3, '已完成'),
    )

    order_no = models.CharField(max_length=32, unique=True, verbose_name="订单号")
    session = models.ForeignKey(AuctionSession, on_delete=models.CASCADE, verbose_name="竞拍场次")
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='buy_orders',
                              verbose_name="买家")
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sell_orders',
                               verbose_name="卖家")

    final_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="成交价")
    deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="已付保证金")
    earnest_money = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="定金")
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="手续费")

    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=0, verbose_name="状态")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    pay_time = models.DateTimeField(null=True, blank=True, verbose_name="支付时间")

    class Meta:
        verbose_name = "拍卖订单"
        verbose_name_plural = verbose_name
        ordering = ['-create_time']

    def __str__(self):
        return self.order_no