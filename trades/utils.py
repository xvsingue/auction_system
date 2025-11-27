from django_redis import get_redis_connection
from django.core.cache import cache
import time

class RedisAuctionHelper:
    """
    Redis 竞价辅助工具类
    """
    def __init__(self, session_id):
        self.session_id = session_id
        self.price_key = f"auction:session:{session_id}:price"
        self.lock_key = f"auction:session:{session_id}:lock"
        self.conn = get_redis_connection("default")

    def get_current_price(self):
        """获取当前最高价/当前价"""
        price = self.conn.get(self.price_key)
        if price:
            return float(price)
        return None

    def set_current_price(self, price):
        """更新价格"""
        self.conn.set(self.price_key, str(price))

    def acquire_lock(self, timeout=5):
        """获取分布式锁 (简单版)"""
        # 使用 setnx 实现锁，防止减价拍卖多人同时抢到一个商品
        identifier = str(time.time())
        if self.conn.set(self.lock_key, identifier, ex=timeout, nx=True):
            return identifier
        return False

    def release_lock(self, identifier):
        """释放锁"""
        current_id = self.conn.get(self.lock_key)
        if current_id and current_id.decode('utf-8') == identifier:
            self.conn.delete(self.lock_key)