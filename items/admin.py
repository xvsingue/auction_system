from django.contrib import admin
from .models import ItemCategory, AuctionItem

admin.site.register(ItemCategory)

@admin.register(AuctionItem)
class ItemAdmin(admin.ModelAdmin):  # 修正此处：去掉 .site
    list_display = ('name', 'category', 'seller', 'start_price', 'status', 'create_time')
    list_filter = ('status', 'category')
    search_fields = ('name',)