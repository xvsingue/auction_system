from django.contrib import admin
from django.utils import timezone
from datetime import timedelta
from .models import ItemCategory, AuctionItem

admin.site.register(ItemCategory)

@admin.register(AuctionItem)
class ItemAdmin(admin.ModelAdmin):  # 修正此处：去掉 .site
    list_display = ('name', 'category', 'seller', 'start_price', 'status', 'create_time')
    list_filter = ('status', 'category')
    search_fields = ('name',)

    def save_model(self, request, obj, form, change):
        original_status = None
        if change:
            old_obj = self.model.objects.get(pk=obj.pk)
            original_status = old_obj.status
            
        super().save_model(request, obj, form, change)
        
        # 自动化黑科技：如果拍品状态变为 1（审核通过），全自动创建拍卖场次
        if obj.status == 1 and original_status != 1:
            from auctions.models import AuctionSession
            # 防止重复创建
            if not obj.sessions.exists():
                now = timezone.now()
                # 兼容旧数据，如果没有填写排期，默认为现在到3天后
                st = obj.expected_start_time or now
                et = obj.expected_end_time or (now + timedelta(days=3))
                
                is_active = (st <= now)
                
                AuctionSession.objects.create(
                    name=f"{obj.name} 专拍场",
                    item=obj,
                    start_time=st,
                    end_time=et,
                    auction_type=obj.auction_type,
                    price_step=obj.price_step,
                    reduce_interval=obj.reduce_interval,
                    bottom_price=obj.bottom_price if obj.auction_type == 'decrease' else obj.reserve_price,
                    status=1 if is_active else 0,
                    current_price=obj.start_price
                )
                
                # 同步更新拍品状态为“竞拍中”
                if is_active:
                    obj.status = 2
                    # 避免再次触发 save() 引起死循环，只更新状态字段
                    self.model.objects.filter(pk=obj.pk).update(status=2)
                    
        elif change:
            # 如果不是首次过审，而是修改旧数据，盲同步卖家改动到未结束的场次
            active_sessions = obj.sessions.exclude(status=2)
            for session in active_sessions:
                if obj.expected_start_time: session.start_time = obj.expected_start_time
                if obj.expected_end_time: session.end_time = obj.expected_end_time
                session.auction_type = obj.auction_type
                session.price_step = obj.price_step
                session.reduce_interval = obj.reduce_interval
                session.bottom_price = obj.bottom_price if obj.auction_type == 'decrease' else obj.reserve_price
                session.save()