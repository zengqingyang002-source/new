"""
数据库会话模块 - 创建数据库连接和管理会话

这个模块负责：
1. 自动创建数据库（如果还不存在的话）
2. 创建 SQLAlchemy 引擎（Engine）—— 数据库连接的核心
3. 创建会话工厂（SessionLocal）—— 用来操作数据库的对象
4. 提供获取数据库会话的依赖函数（用于 FastAPI 依赖注入）
5. 提供数据库健康检查功能

新手需要知道的名词：
- Engine（引擎）：连接数据库的"总入口"，整个应用共享一个
- Session（会话）：实际执行 SQL 查询的"工作台"，每次请求创建新的
- Base（基类）：所有数据模型的父类，SQLAlchemy 用它来注册表结构
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# 声明基类 —— 所有数据模型（Model）都要继承这个 Base
# SQLAlchemy 通过 Base.metadata 知道所有表的结构
Base = declarative_base()


def create_database_if_missing() -> None:
    """
    如果数据库不存在，自动创建它

    具体做法：
    1. 先连接到 MySQL 服务器（不指定具体数据库）
    2. 然后执行 CREATE DATABASE 语句
    3. 这样即使数据库还没创建，应用也能正常运行

    注意：只对 MySQL 有效，且需要 auto_create_database 配置为 True
    """
    if not settings.auto_create_database:
        return
    if not settings.database_url.startswith("mysql"):
        return

    try:
        import pymysql
    except Exception:
        return

    # 先连到 MySQL 服务器（不指定数据库）
    connection = pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        charset="utf8mb4",
        autocommit=True,  # 自动提交 —— 执行 CREATE DATABASE 后不需要再 COMMIT
    )
    try:
        with connection.cursor() as cursor:
            # 执行建库语句，注意 IF NOT EXISTS —— 如果已经存在就不重复创建
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{settings.mysql_database}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
    finally:
        connection.close()


# 在模块导入时就执行 —— 确保先创建数据库，再创建引擎
create_database_if_missing()

# 创建数据库引擎（Engine）
# engine 是整个应用与数据库通信的核心
# pool_pre_ping=True：每次从连接池取出连接前，先检查连接是否有效（防止"连接已断开"错误）
# future=True：使用 SQLAlchemy 2.0 风格（较新的 API）
engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)

# 创建会话工厂（SessionLocal）
# SessionLocal 是一个"可以创建数据库会话的类"
# 调用 SessionLocal() 就会创建一个新的数据库会话
# autocommit=False：不自动提交 —— 需要手动 db.commit() 来保存更改
# autoflush=False：不自动刷新 —— 防止一些意外的数据库操作
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_db():
    """
    FastAPI 依赖项 —— 获取数据库会话

    使用方法：在路由函数参数中写 db: Session = Depends(get_db)

    这个函数是"生成器函数"（用了 yield 而不是 return）：
    - yield 之前：创建数据库会话
    - yield 之后（finally）：关闭会话，释放连接

    这样保证每次请求都使用独立的会话，请求结束后自动关闭连接。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # 关！一定要关闭！否则数据库连接会被耗尽


def ping_database() -> bool:
    """
    数据库健康检查

    执行一个最简单的 SQL 查询（SELECT 1），如果能成功返回 True，否则返回 False。
    这个函数会被 /api/health 接口调用，用来检测数据库是否正常。
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
