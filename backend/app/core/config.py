"""
应用配置模块 - 集中管理所有配置项

这个文件负责从环境变量（.env 文件或系统环境变量）读取所有配置。
新手理解要点：
- 环境变量：操作系统或 .env 文件里设置的"键值对"
- os.getenv()：从环境变量里读取值，如果没找到就用默认值
- 这样做的好处是：同样的代码，在开发/测试/生产环境可以通过不同的 .env 文件配置不同的行为
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv  # 可以从 .env 文件加载环境变量
except Exception:
    load_dotenv = None


# 项目根目录（edu_dify_platform 文件夹）
# __file__ 是当前文件的路径，通过 parents[3] 往上翻 3 层父目录
# 得到项目根目录 d:\mouth_milion\edu_dify_platform
ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT_DIR / "backend"

# 尝试加载 .env 文件中定义的环境变量
if load_dotenv:
    load_dotenv(BACKEND_DIR / ".env")


def _bool(name: str, default: bool) -> bool:
    """从环境变量读取布尔值，支持 1/true/yes/on 等表示"真"的字符串"""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    """从环境变量读取整数，如果解析失败则返回默认值"""
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


class Settings:
    """
    配置类 —— 所有可配置项集中在这里

    使用类属性（而不是 __init__）的好处是：
    - 简洁，不需要 self.xxx 赋值
    - 类级别的属性可以在类外部直接访问
    Settings 是一个"单例"——整个应用只有一个 settings 实例
    """

    # ---- 应用基础配置 ----
    app_name = os.getenv("APP_NAME", "Edu Dify Platform")      # 应用名称
    app_env = os.getenv("APP_ENV", "development")               # 运行环境：development / production
    app_secret = os.getenv("APP_SECRET", "change-me-in-production")  # 应用秘钥（用于密码加密等）

    # ---- CORS 跨域配置 ----
    # 允许哪些前端域名访问后端接口
    # 默认支持 Vue 开发服务器（5173）和构建版本（4173）
    cors_origins = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173",
        ).split(",")
        if origin.strip()
    ]

    # ---- 数据库配置 ----
    database_url = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:123456@127.0.0.1:3306/edu_dify_platform?charset=utf8mb4",
    )
    mysql_host = os.getenv("MYSQL_HOST", "127.0.0.1")
    mysql_port = _int("MYSQL_PORT", 3306)
    mysql_database = os.getenv("MYSQL_DATABASE", "edu_dify_platform")
    mysql_user = os.getenv("MYSQL_USER", "root")
    mysql_password = os.getenv("MYSQL_PASSWORD", "123456")
    auto_create_database = _bool("AUTO_CREATE_DATABASE", True)     # 是否自动创建数据库
    auto_seed_demo_data = _bool("AUTO_SEED_DEMO_DATA", True)       # 是否自动插入演示数据

    # ---- Dify AI 平台配置 ----
    # Dify 是一个开源的 LLM 应用平台，我们用它来驱动 AI 对话和 AI 评估
    dify_base_url = os.getenv("DIFY_BASE_URL", "http://192.168.110.27").rstrip("/")
    dify_timeout_seconds = _int("DIFY_TIMEOUT_SECONDS", 35)        # 请求 Dify 的超时时间（秒）
    dify_fallback_enabled = _bool("DIFY_FALLBACK_ENABLED", True)   # Dify 失败时是否启用本地兜底方案
    # 以下四个是不同的 API 密钥，对应 Dify 中不同的"应用"（Chatbot 或 Workflow）
    dify_customer_chat_api_key = os.getenv("DIFY_CUSTOMER_CHAT_API_KEY", "")    # 给客户用的聊天机器人
    dify_lead_workflow_api_key = os.getenv("DIFY_LEAD_WORKFLOW_API_KEY", "")    # 客户评估工作流
    dify_employee_chat_api_key = os.getenv("DIFY_EMPLOYEE_CHAT_API_KEY", "")    # 给员工用的聊天机器人
    dify_report_workflow_api_key = os.getenv("DIFY_REPORT_WORKFLOW_API_KEY", "") # 报告生成工作流

    # ---- 其他 AI 服务 ----
    qwen_api_key = os.getenv("QWEN_API_KEY", "")  # 通义千问 API 密钥（备用 AI 服务）

    @property
    def dify_api_base(self) -> str:
        """
        Dify API 的基础地址
        自动处理 URL 末尾是否需要加 /v1
        """
        if self.dify_base_url.endswith("/v1"):
            return self.dify_base_url
        return f"{self.dify_base_url}/v1"


# 创建一个全局可用的配置实例 —— 其他地方通过 from app.core.config import settings 来使用
settings = Settings()
