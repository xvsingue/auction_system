from django.contrib import admin
from .models import BidRecord, AuctionOrder

@admin.register(BidRecord)
class BidRecordAdmin(admin.ModelAdmin):
    list_display = ('session', 'buyer', 'bid_price', 'bid_time', 'is_leading')
    list_filter = ('session',)

@admin.register(AuctionOrder)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_no', 'session', 'buyer', 'final_price', 'status', 'create_time')
    list_filter = ('status',)