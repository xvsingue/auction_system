import os
from celery import Celery

# 设置 Django 的 settings 模块环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auction_backend.settings')

# 创建 Celery 应用实例
app = Celery('auction_backend')

# 从 Django settings 中加载配置，所有 CELERY_ 开头的配置项都会被读取
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现各个 App 中的 tasks.py 文件
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')