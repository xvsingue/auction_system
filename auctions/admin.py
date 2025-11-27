from django.contrib import admin
from .models import AuctionSession
from .forms import AuctionSessionForm  # 导入刚才创建的 Form


@admin.register(AuctionSession)
class AuctionSessionAdmin(admin.ModelAdmin):
    form = AuctionSessionForm  # 指定使用自定义 Form
    list_display = ('name', 'item', 'auction_type', 'status', 'start_time', 'current_price')
    list_filter = ('status', 'auction_type')
    search_fields = ('name', 'item__name')

    def save_model(self, request, obj, form, change):
        """
        重写保存逻辑：支持批量创建
        """
        # 获取表单中选中的所有拍品
        selected_items = form.cleaned_data.get('items')

        if not selected_items:
            return

        # === 1. 处理主要对象 (obj) ===
        # 将表单选中的第一个拍品赋给当前对象，作为主记录
        first_item = selected_items[0]
        obj.item = first_item

        # 自动初始化当前价 = 拍品起拍价 (如果未填)
        if obj.current_price is None:
            obj.current_price = first_item.start_price

        # 保存这第一条记录
        super().save_model(request, obj, form, change)

        # === 2. 批量创建剩余的 (如果是新增模式) ===
        if not change and len(selected_items) > 1:
            rest_items = selected_items[1:]  # 剩下的拍品
            for item in rest_items:
                # 复制一份配置，但关联不同的拍品
                AuctionSession.objects.create(
                    name=f"{obj.name} ({item.name})",  # 场次名自动加上拍品名，区分一下
                    item=item,
                    start_time=obj.start_time,
                    end_time=obj.end_time,
                    auction_type=obj.auction_type,
                    price_step=obj.price_step,
                    reduce_interval=obj.reduce_interval,
                    bottom_price=obj.bottom_price,
                    status=obj.status,
                    current_price=item.start_price  # 重要：用拍品自己的起拍价
                )