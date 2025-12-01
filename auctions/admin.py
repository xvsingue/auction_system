from django.contrib import admin
from .models import AuctionSession
from .forms import AuctionSessionForm


@admin.register(AuctionSession)
class AuctionSessionAdmin(admin.ModelAdmin):
    form = AuctionSessionForm  # 指定使用自定义 Form (支持多选拍品)
    list_display = ('name', 'item', 'auction_type', 'status', 'start_time', 'current_price')
    list_filter = ('status', 'auction_type')
    search_fields = ('name', 'item__name')

    def save_model(self, request, obj, form, change):
        """
        重写保存逻辑：
        1. 支持批量创建场次。
        2. 智能填充底价：如果管理员没填底价，自动使用拍品的保留价。
        """
        # 获取表单中选中的所有拍品
        selected_items = form.cleaned_data.get('items')

        if not selected_items:
            return

        # 关键点：先记录下管理员在表单里到底填没填底价
        # 如果没填(为None)，后续所有批量场次都去取各自拍品的保留价。
        manual_bottom_price = obj.bottom_price

        # === 1. 处理主要对象 (obj) - 即列表中的第一个拍品 ===
        first_item = selected_items[0]
        obj.item = first_item

        # 逻辑A：自动初始化当前价 = 拍品起拍价 (如果管理员未填)
        if obj.current_price is None:
            obj.current_price = first_item.start_price

        # 逻辑B (本次优化)：自动初始化底价
        # 如果管理员留白，则自动填入该拍品的保留价
        if obj.bottom_price is None:
            obj.bottom_price = first_item.reserve_price

        # 保存这第一条记录
        super().save_model(request, obj, form, change)

        # === 2. 批量创建剩余的 (如果是新增模式) ===
        if not change and len(selected_items) > 1:
            rest_items = selected_items[1:]  # 剩下的拍品
            for item in rest_items:

                # 智能判定该场次的底价
                if manual_bottom_price is not None:
                    # 管理员手动统一指定了底价
                    this_bottom_price = manual_bottom_price
                else:
                    # 管理员留白，自动使用当前这个拍品的保留价
                    this_bottom_price = item.reserve_price

                # 创建关联场次
                AuctionSession.objects.create(
                    name=f"{obj.name} ({item.name})",  # 场次名自动加后缀区分
                    item=item,
                    start_time=obj.start_time,
                    end_time=obj.end_time,
                    auction_type=obj.auction_type,
                    price_step=obj.price_step,
                    reduce_interval=obj.reduce_interval,

                    bottom_price=this_bottom_price,  # <--- 使用智能判定的底价

                    status=obj.status,
                    current_price=item.start_price  # 使用拍品各自的起拍价
                )
