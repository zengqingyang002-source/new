"""
安全认证模块 - 处理密码加密、Token 生成和验证

这个模块负责：
1. 密码的加密存储（不存明文密码）
2. 登录验证（比对密码是否正确）
3. 生成访问令牌（Token，相当于"临时通行证"）
4. 验证 Token 的有效性

注意：当前实现是简化版，Token 保存在内存（字典）中，
生产环境一般会使用 JWT（JSON Web Token）来替代。
"""

import hashlib
import hmac
import secrets
from datetime import datetime

from app.core.config import settings


# 内存中的 Token 存储 —— 格式：{ "token字符串": {"user_id": 1, "username": "admin", ...} }
# 简化实现：服务重启后所有 Token 都会失效
_TOKENS: dict[str, dict] = {}


def hash_password(password: str) -> str:
    """
    对密码进行加密（哈希）处理

    做法是把"应用秘钥 + 密码"拼接后用 SHA256 算法加密。
    加"应用秘钥"是为了防止"彩虹表攻击"——就算黑客拿到了加密后的密码，
    也无法反推出原始密码。
    """
    payload = f"{settings.app_secret}:{password}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """
    验证密码是否正确

    把用户输入的密码用同样的方式加密，然后和数据库中存的加密密码做对比。
    使用 hmac.compare_digest 是为了防止"计时攻击"（通过比较耗时猜测密码）。
    """
    return hmac.compare_digest(hash_password(password), password_hash)


def create_access_token(user_id: int, username: str, role: str) -> str:
    """
    创建访问令牌（Token）

    参数：
      - user_id: 用户 ID
      - username: 用户名
      - role: 角色（ADMIN/EMPLOYEE/STUDENT/CUSTOMER）

    返回一个随机字符串作为 Token，同时把用户信息存到内存字典中。
    后续请求携带这个 Token 就可以识别用户身份，不需要每次输入密码。
    """
    token = secrets.token_urlsafe(32)  # 生成一个安全的随机字符串（32 字节）
    _TOKENS[token] = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "created_at": datetime.utcnow().isoformat(),
    }
    return token


def get_token_payload(token: str) -> dict | None:
    """
    根据 Token 查找用户信息

    如果 Token 有效，返回之前存的用户数据；
    如果 Token 无效或过期（内存中的已清除），返回 None。
    """
    return _TOKENS.get(token)
