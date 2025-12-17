from pathlib import Path
import os

# 构建项目根目录路径
BASE_DIR = Path(__file__).resolve().parent.parent

# ===================================================
# 核心安全配置
# ===================================================
SECRET_KEY = 'django-insecure-change-me-for-production-!@#$'
DEBUG = True  # 开发阶段开启，生产环境需关闭
ALLOWED_HOSTS = ['*']  # 允许所有主机访问，方便局域网/手机端调试

# ===================================================
# 应用注册 (INSTALLED_APPS)
# ===================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 第三方库
    'rest_framework',  # 构建 Web API
    'corsheaders',  # 处理跨域请求 (前后端分离/混合开发必备)
    'django_celery_results',  # 存储 Celery 任务结果
    'django_celery_beat',  # 处理定时任务 (减价拍卖自动降价)
    'django_filters',  # 筛选功能
    'django_extensions',
    # 自定义业务模块 (按依赖顺序排列)
    'users.apps.UsersConfig',  # 用户模块 (包含自定义用户模型)
    'items.apps.ItemsConfig',  # 拍品模块
    'auctions.apps.AuctionsConfig',  # 拍卖活动模块
    'trades.apps.TradesConfig',  # 竞价交易模块
    'finance.apps.FinanceConfig',  # 资金模块
    'system.apps.SystemConfig',  # 系统管理模块
    'web',
]

# ===================================================
# 中间件配置 (MIDDLEWARE)
# ===================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # 必须放在 CommonMiddleware 之前
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'auction_backend.urls'

# ===================================================
# 模板配置 (TEMPLATES)
# ===================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # 指向根目录下的 templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'auction_backend.wsgi.application'

# ===================================================
# 数据库配置 (DATABASES)
# ===================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'auction_db',  # 数据库名
        'USER': 'root',
        'PASSWORD': '1234',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        }
    }
}

# ===================================================
# 自定义用户模型
# ===================================================
# 这一点至关重要，必须在第一次 migrate 之前配置
AUTH_USER_MODEL = 'users.UserProfile'

# ===================================================
# 密码验证
# ===================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ===================================================
# 国际化配置
# ===================================================
LANGUAGE_CODE = 'zh-hans'  # 使用中文
TIME_ZONE = 'Asia/Shanghai'  # 中国时区
USE_I18N = True
USE_TZ = False

# ===================================================
# 静态文件与媒体文件
# ===================================================
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ===================================================
# Django Rest Framework 配置
# ===================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # 使用我们自定义的免 CSRF 认证类
        'auction_backend.my_auth.CsrfExemptSessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',  # 默认权限
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,  # 默认分页大小
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',  # 统一时间格式
}

# ===================================================
# Redis 缓存配置
# ===================================================
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",  # 使用 1 号库作为缓存
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# ===================================================
# Celery 异步任务配置
# ===================================================
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'  # 使用 0 号库作为消息中间件
CELERY_RESULT_BACKEND = 'django-db'  # 结果存储在数据库中(或者用 redis)
CELERY_TIMEZONE = 'Asia/Shanghai'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
# CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# ===================================================
# 跨域配置 (CORS)
# ===================================================
CORS_ALLOW_ALL_ORIGINS = True  # 开发阶段允许所有跨域

from celery.schedules import crontab

# auction_backend/settings.py

CELERY_BEAT_SCHEDULE = {
    # 1. 原有的减价拍自动降价 (每5秒)
    'decrease-price-every-5-seconds': {
        'task': 'auctions.tasks.decrease_auction_price',
        'schedule': 5.0,
    },

    # 自动结算到期场次 (每 10 秒检查一次，方便演示)
    # 实际生产环境通常设为 1 分钟 (crontab(minute='*'))
    'close-expired-auctions': {
        'task': 'auctions.tasks.check_and_close_auctions',
        'schedule': 10.0,
    },
}
