# 基于 Django + Vue 的在线拍卖管理系统

## 1. 项目简介
本项目是一个前后端混合开发的在线拍卖平台，支持增价拍卖与减价拍卖两种模式。系统集成了实时竞价、自动结算、资金管理及可视化数据大屏等功能，旨在模拟真实的在线拍卖全流程。

## 2. 技术栈
* **后端框架**: Django 5.2.8, Django REST Framework 3.16
* **前端技术**: Vue.js 2, Bootstrap 5, Axios, ECharts 5
* **数据库**: MySQL 8.0 (驱动: mysqlclient)
* **缓存/消息队列**: Redis 7.1 (驱动: django-redis)
* **异步任务**: Celery 5.3.6 + Django-Celery-Beat + Eventlet

## 3. 核心功能
* **多角色系统**: 管理员、卖家、买家三端分离。
* **双模式竞拍**: 支持传统的增价拍和刺激的减价拍（荷兰式拍卖）。
* **高并发抢拍**: 利用 Redis 原子锁解决减价拍超卖问题。
* **全自动结算**: 基于 Celery 定时任务，拍卖到期自动判断输赢、生成订单。
* **可视化指挥舱**: 管理员独享的数据监控大屏。

## 4. 环境依赖
* Python 3.10+
* MySQL Server (需预先创建数据库 `auction_db`)
* Redis Server (需在本地启动服务)

## 5. 快速启动
1.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **配置数据库**: 
    打开 `auction_backend/settings.py`，找到 `DATABASES` 配置项，修改 `PASSWORD` 为你本地 MySQL 的真实密码。
3.  **迁移数据**:
    ```bash
    python manage.py migrate
    ```
4.  **启动服务 (需开启三个独立的终端窗口)**:
    
    * **窗口 1 (Web 服务 - 前台页面)**:
        ```bash
        python manage.py runserver
        ```
    
    * **窗口 2 (Celery Worker - 异步任务执行者)**:
        *推荐使用 python 模块方式启动，避免环境变量路径问题：*
        ```bash
        python -m celery -A auction_backend worker -l info
        ```
    
    * **窗口 3 (Celery Beat - 定时任务调度者)**:
        *负责触发自动降价和自动结算任务：*
        ```bash
        python -m celery -A auction_backend beat -l info
        ```

## 6. 测试账号
* **管理员 (Admin)**: 
    * 账号: `admin` 
    * 密码: `admin`
* **买家 (Buyer)**: 
    * 账号: `buyer1` / 密码: `123456` (支付密码同登录密码)
    * 账号: `buyer2` / 密码: `buy123456`
* **卖家 (Seller)**: 
    * 账号: `seller1` / 密码: `sell123456`
    * 账号: `seller2` / 密码: `sell123456`