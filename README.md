# 基于 Django + Vue 的在线拍卖管理系统

<img width="2416" height="1777" alt="QQ_1774117260472" src="https://github.com/user-attachments/assets/314cc6a0-7be8-48f7-b764-8f51e7181bdd" />


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
* **双模式自由定制**: 卖家发品时可自主选定增价或减价模式，并灵活配比成交流程（起拍价、加降幅度、保留价/保底价）。
* **全自动排期与上架**: 摆脱繁琐的人工建场操作。卖家预设起止时间，管理员一键审核后，系统依赖 Celery 定时时钟实现无感知的“到点自动开拍”。
* **极致的数据同步体系**: 状态机严丝合缝，管理员对拍品库存的后续修改（如延期、改价）可以毫秒级无感热更新到前台正在运行的拍卖场次中，告别数据孤岛。
* **高并发抢拍**: 利用 Redis 原子锁解决减价拍超卖问题。
* **全自动结算**: 基于 Celery 定时任务，拍卖到期自动判断输赢交割、流拍重置以及生成订单。
* **可视化指挥舱**: 管理员独享的 ECharts 数据监控大屏。

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

## 6. 测试账号(这里需自行注册账号测试)
* **管理员 (Admin)**: 
    * 账号: `admin` 
    * 密码: `admin`
* **买家 (Buyer)**: 
    * 账号: `buyer1` / 密码: `123456` (支付密码同登录密码)
    * 账号: `buyer2` / 密码: `buy123456`
* **卖家 (Seller)**: 
    * 账号: `seller1` / 密码: `sell123456`
    * 账号: `seller2` / 密码: `sell123456`
