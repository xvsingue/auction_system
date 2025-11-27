from celery import shared_task
from django_redis import get_redis_connection
from .models import AuctionSession
from django.utils import timezone
from trades.utils import RedisAuctionHelper


@shared_task
def decrease_auction_price():
    """
    周期性任务：处理减价拍卖的降价逻辑
    建议每 1-5 秒运行一次 (通过 Celery Beat 配置)
    """
    # 1. 查找所有正在进行中(status=1) 且 类型为减价(decrease) 的场次
    now = timezone.now()
    active_sessions = AuctionSession.objects.filter(
        status=1,
        auction_type='decrease',
        start_time__lte=now,
        end_time__gte=now
    )

    for session in active_sessions:
        helper = RedisAuctionHelper(session.id)
        current_price = helper.get_current_price()

        # 如果 Redis 没数据，从 DB 初始化
        if current_price is None:
            current_price = float(session.current_price)
            helper.set_current_price(current_price)

        # 2. 计算新价格
        # 实际逻辑应判断 上次降价时间，这里简化为每次执行任务都降价(需配合 beat 频率)
        new_price = current_price - float(session.price_step)
        bottom_price = float(session.bottom_price)

        if new_price <= bottom_price:
            new_price = bottom_price
            # 触底处理：可选择自动结束或维持底价

        # 3. 更新 Redis
        helper.set_current_price(new_price)

        # 4. 异步同步回 DB (避免频繁写库，可降低频率，此处为了演示实时性直接写)
        session.current_price = new_price
        session.save(update_fields=['current_price'])

        print(f"Session {session.id} price decreased to {new_price}")


from trades.models import BidRecord, AuctionOrder
from django.db import transaction
import uuid


@shared_task
def check_and_close_auctions():
    """
    定时任务：检查到期的拍卖场次，进行自动结算
    """
    now = timezone.now()

    # 1. 找出所有【进行中】且【时间已到】的场次
    # 注意：减价拍通常是抢购即结束，这里主要处理增价拍(时间到)，或减价拍流拍
    expired_sessions = AuctionSession.objects.filter(
        status=1,  # 进行中
        end_time__lte=now  # 结束时间 <= 当前时间
    )

    if not expired_sessions.exists():
        return "No expired sessions."

    for session in expired_sessions:
        with transaction.atomic():
            print(f"正在结算场次: {session.name} (ID: {session.id})")

            # 2. 查找该场次的获胜者（当前领先的记录）
            # 增价拍：取最高价；减价拍：通常抢购时已处理，但也可能没人买导致时间到
            winner_bid = BidRecord.objects.filter(session=session, is_leading=True).first()

            if winner_bid:
                # === 情况 A: 有人出价，成交 ===

                # 生成订单
                order_no = f"ORD-{uuid.uuid4().hex[:10].upper()}"
                AuctionOrder.objects.create(
                    order_no=order_no,
                    session=session,
                    buyer=winner_bid.buyer,
                    seller=session.item.seller,
                    final_price=winner_bid.bid_price,
                    status=0  # 未支付
                )

                # 更新场次状态 -> 已结束
                session.status = 2
                session.current_price = winner_bid.bid_price
                session.save()

                # 更新拍品状态 -> 已成交
                session.item.status = 3
                session.item.save()

                print(f"  -> 成交！买家: {winner_bid.buyer.username}, 金额: {winner_bid.bid_price}")

            else:
                # === 情况 B: 无人出价，流拍 ===

                # 更新场次状态 -> 已结束
                session.status = 2
                session.save()

                # 更新拍品状态 -> 流拍
                session.item.status = 4
                session.item.save()

                print(f"  -> 流拍！无人出价。")

    return f"Processed {expired_sessions.count()} expired sessions."
