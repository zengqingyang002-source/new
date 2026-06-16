"""
请求/响应数据模式模块 —— 定义 API 的输入和输出格式

这个文件使用 Pydantic（一个数据验证库）来定义：
1. 请求体（Request）：前端发给后端的数据长什么样、有哪些必填字段
2. 响应体（Response）：后端返回给前端的数据结构

这样做的好处：
- 自动验证数据格式（比如字段类型对不对、字段有没有缺失）
- 生成 API 文档（FastAPI 会自动把这里的定义显示在 Swagger 文档中）
- 提供代码提示（写代码时 IDE 知道字段名和类型）

新手只需要知道：这里的每个类都是在定义"数据长什么样"
"""

from typing import Any

from pydantic import BaseModel, Field


# ========== 认证相关 ==========

class LoginRequest(BaseModel):
    """登录请求体 —— 用户登录时需要提供的用户名和密码"""
    username: str
    password: str


class UserOut(BaseModel):
    """用户信息输出 —— 返回给前端的用户信息（不包含密码）"""
    id: int
    username: str
    real_name: str
    user_type: str
    employee_role: str | None = None
    department: str | None = None
    contact_info: str | None = None

    model_config = {"from_attributes": True}  # 允许从 SQLAlchemy 模型对象直接转换


class LoginResponse(BaseModel):
    """登录成功后的返回结果 —— 包含访问令牌和用户信息"""
    access_token: str     # 后续请求需要用这个 token 来验证身份
    token_type: str = "bearer"  # Token 类型（固定值）
    user: UserOut         # 用户基本信息


# ========== 聊天相关 ==========

class ChatRequest(BaseModel):
    """聊天请求体 —— 用户发送给 AI 的消息"""
    message: str                    # 用户消息内容
    conversation_id: str | None = None  # 对话 ID（用于多轮对话，第一次可以为空）


class ChatResponse(BaseModel):
    """聊天响应 —— AI 返回的回复消息"""
    answer: str                         # AI 的回答内容
    conversation_id: str | None = None  # 对话 ID（用于继续对话）
    source: str = "local"               # 回答来源：dify（AI平台）/ local-fallback（本地兜底）
    raw: Any | None = None              # 原始响应数据（调试用）


# ========== 客户评估相关 ==========

class LeadEvaluationRequest(BaseModel):
    """客户评估请求体 —— 要评估的客户文本信息"""
    text: str                     # 客户原始文本（比如对话记录、填写的表单等）
    source_type: str = "text"     # 信息来源：text / docx / xlsx / pdf 等
    save_to_crm: bool = False     # 是否同时保存到 CRM（创建客户记录）


class LeadCreate(BaseModel):
    """创建客户（Lead）请求体"""
    customer_name: str
    contact_info: str | None = None
    age: int | None = None
    gender: str | None = None
    education: str | None = None
    background_info: str | None = None
    intended_project: str | None = None
    follow_up_history: str | None = None
    status: str = "新增意向"


class LeadStatusUpdate(BaseModel):
    """更新客户状态请求体"""
    status: str                    # 新状态：跟进中/已签约/已流失等
    follow_up_note: str | None = None  # 跟进备注


# ========== 日报相关 ==========

class DailyReportCreate(BaseModel):
    """创建日报请求体"""
    employee_id: int | None = None  # 员工 ID（不传则用当前登录用户）
    report_date: str | None = None  # 汇报日期（不传则用今天）
    content: str                    # 日报正文


# ========== 请假相关 ==========

class LeaveCreate(BaseModel):
    """创建请假申请请求体"""
    reason: str
    start_time: str | None = None
    end_time: str | None = None


class LeaveApprove(BaseModel):
    """审批请假请求体 —— 注意使用正则限制了只能填这三个值"""
    status: str = Field(pattern="^(已通过|已驳回|待审批)$")


# ========== 投诉反馈相关 ==========

class FeedbackCreate(BaseModel):
    """创建投诉/反馈请求体"""
    content: str
    detail: str | None = None


class FeedbackUpdate(BaseModel):
    """更新投诉处理结果请求体"""
    status: str                    # 新状态
    solution: str | None = None    # 解决方案


# ========== 报告相关 ==========

class ReportCreate(BaseModel):
    """创建报告请求体"""
    report_type: str              # 报告类型：customer-analysis / daily-summary / complaint-weekly / psych-weekly
    title: str | None = None      # 报告标题
    payload: dict[str, Any] | None = None  # 报告的附加参数
