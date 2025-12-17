from django.db import models
from django.contrib.auth.models import AbstractUser


class UserProfile(AbstractUser):
    """
    用户表 (user_profile)
    继承 Django 原生 AbstractUser，扩展角色、信用分、余额等字段
    """
    # 角色枚举
    ROLE_CHOICES = (
        ('admin', '管理员'),
        ('seller', '卖家'),
        ('buyer', '买家'),
    )

    # 基础字段扩展
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='buyer', verbose_name='角色')

    # 信用与认证
    credit_rating = models.DecimalField(max_digits=3, decimal_places=1, default=5.0, verbose_name='信用分')
    id_card = models.CharField(max_length=18, blank=True, null=True, verbose_name='身份证号')
    business_license = models.ImageField(upload_to='licenses/%Y%m/', blank=True, null=True, verbose_name='营业执照')

    # 资金字段
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='账户余额')

    # 冗余字段（显式定义 create_time）
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = verbose_name
        db_table = 'user_profile'  # 强制指定表名，符合文档要求

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"