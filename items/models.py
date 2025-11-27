from django.db import models
from django.conf import settings


class ItemCategory(models.Model):
    """
    拍品分类表
    """
    name = models.CharField(max_length=50, verbose_name="分类名称")

    class Meta:
        verbose_name = "拍品分类"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class AuctionItem(models.Model):
    """
    拍品表 (auction_item)
    """
    STATUS_CHOICES = (
        (0, '待审核'),
        (1, '待开拍'),  # 审核通过后，关联场次前或关联后未开始
        (2, '竞拍中'),
        (3, '已成交'),
        (4, '流拍'),
    )

    name = models.CharField(max_length=200, verbose_name="拍品名称")
    category = models.ForeignKey(ItemCategory, on_delete=models.CASCADE, verbose_name="所属分类")
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='items',
                               verbose_name="卖家")

    start_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="起拍价")
    reserve_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="保留价",
                                        help_text="低于此价格不成交")

    # 保证金与定金比例
    deposit_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=20.00, verbose_name="保证金比例(%)")
    earnest_money_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=10.00, verbose_name="定金比例(%)")

    # 图片路径存储 (逗号分隔的字符串)
    image_paths = models.TextField(verbose_name="图片路径", help_text="存储多张图片路径，用逗号分隔")

    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=0, verbose_name="状态")

    # 审核相关
    reject_reason = models.CharField(max_length=255, blank=True, null=True, verbose_name="驳回原因")

    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "拍品"
        verbose_name_plural = verbose_name
        db_table = 'auction_item'
        ordering = ['-create_time']

    def __str__(self):
        return self.name

    def get_images(self):
        """辅助方法：返回图片列表"""
        if self.image_paths:
            return self.image_paths.split(',')
        return []