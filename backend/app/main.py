"""
应用主文件 - 创建 FastAPI 应用实例，注册中间件、路由、启动事件

这个文件是整个后端应用的核心组装工厂，负责：
1. 创建 FastAPI 应用实例
2. 配置 CORS（跨域请求）中间件
3. 注册启动事件（自动建表和导入演示数据）
4. 挂载 API 路由
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # 跨域中间件

from app.api.routes import router
from app.core.config import settings
from app.db.init_db import init_demo_data
from app.db.session import Base, SessionLocal, engine
from app import models  # noqa: F401 - 导入模型确保 SQLAlchemy 能识别所有表结构


def create_app() -> FastAPI:
    """
    创建并配置 FastAPI 应用实例。

    这是典型的"应用工厂"模式——把创建和配置封装在一个函数里，
    方便测试时传入不同配置、或者在其他地方复用。
    """
    # 1. 创建 FastAPI 实例，标题和版本从配置读取
    app = FastAPI(title=settings.app_name, version="1.0.0")

    # 2. 添加 CORS 中间件
    #    作用是允许前端（比如 Vue 开发服务器 localhost:5173）跨域请求后端
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,  # 允许的来源域名列表
        allow_credentials=True,               # 允许携带 Cookie 等凭证
        allow_methods=["*"],                   # 允许所有 HTTP 方法（GET, POST, PUT, DELETE 等）
        allow_headers=["*"],                   # 允许所有请求头
    )

    # 3. 注册"启动时"执行的事件
    #    应用启动时会自动执行这个函数里的操作
    @app.on_event("startup")
    def startup() -> None:
        # 自动创建所有数据库表（如果表不存在的话）
        # 这是根据 models.py 里的模型定义来创建的
        Base.metadata.create_all(bind=engine)

        # 如果开启了"自动播种演示数据"的配置，
        # 就往数据库里插一些示例数据（初始用户、项目、客户等）
        if settings.auto_seed_demo_data:
            db = SessionLocal()
            try:
                init_demo_data(db)
            finally:
                db.close()  # 记得关闭数据库连接

    # 4. 注册路由
    #    所有 API 接口都以 /api 开头
    #    比如 /api/auth/login、/api/leads/evaluate 等
    app.include_router(router, prefix="/api")

    return app


# 实际创建应用实例 —— 模块级别直接执行，导入时自动创建
app = create_app()
