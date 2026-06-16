"""
依赖注入模块 —— 提供用户认证相关的 FastAPI 依赖

这个模块提供了两个重要的"依赖项"（Depends），
用于在 API 接口中验证用户身份：

1. get_current_user: 验证请求是否携带了有效的 Token
   - 检查 HTTP 头中的 Authorization: Bearer xxx
   - 验证 Token 是否有效
   - 从数据库查找对应用户
   - 返回用户对象

2. require_employee: 在前者的基础上，额外要求用户必须是"员工"类型
   - 用于只允许员工访问的接口（如客户评估、审批请假等）
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import get_token_payload
from app.db.session import get_db
from app.models import SysUser

# HTTPBearer 是一个 FastAPI 工具类，用于从 HTTP 请求头中提取 Bearer Token
# auto_error=False：如果没找到 Token，不自动报错，而是返回 None
# 这样我们可以自己处理错误（返回中文错误信息）
security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> SysUser:
    """
    获取当前登录的用户

    流程：
    1. 检查 HTTP 请求头中是否有 Authorization: Bearer xxx
    2. 如果没有 Token，返回 401 未认证
    3. 验证 Token 是否有效（在内存字典中查找）
    4. 根据 Token 中的 user_id 从数据库查找用户
    5. 如果用户不存在，返回 401
    6. 返回用户对象

    这个函数作为 FastAPI 的"依赖项"使用：
    ```
    def my_api(user: SysUser = Depends(get_current_user)):
        # user 就是当前登录的用户
    ```
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    payload = get_token_payload(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    user = db.get(SysUser, payload["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


def require_employee(user: SysUser = Depends(get_current_user)) -> SysUser:
    """
    要求当前用户必须是"员工"类型

    在 get_current_user 的基础上，额外检查 user_type == "EMPLOYEE"
    如果不是员工，返回 403 禁止访问。

    用在只有员工才能操作的接口上，比如：
    - 评估客户（员工才能评估，客户不能）
    - 审批请假（员工才能审批）
    - 查看心理预警（员工才能查看）
    """
    if user.user_type != "EMPLOYEE":
        raise HTTPException(status_code=403, detail="Employee role required")
    return user
