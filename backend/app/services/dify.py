"""
Dify AI 平台客户端模块 —— 对接 Dify 的聊天 API 和工作流 API

这个模块负责与 Dify AI 平台通信，提供：
1. chat() - 聊天功能（给客户或员工使用的 AI 对话助手）
2. workflow() - 工作流功能（AI 评估客户、生成报告等）

另外还提供了本地"兜底"回复函数（fallback_*），
当 Dify 服务不可用时，用写好的固定答案回复用户。
"""

from typing import Any

import httpx  # 异步 HTTP 请求库，类似 requests 但支持 async/await

from app.core.config import settings


class DifyClient:
    """
    Dify API 客户端

    Dify 是一个开源的 LLM（大语言模型）应用平台。
    简单说就是：我们在 Dify 上配置好了 AI 对话机器人/工作流，
    然后通过这个客户端调用 Dify 提供的 API 接口。
    """

    def __init__(self) -> None:
        self.base_url = settings.dify_api_base  # Dify 服务器地址
        self.timeout = settings.dify_timeout_seconds  # 请求超时时间（秒）

    async def chat(
        self,
        api_key: str,
        message: str,
        user: str,
        conversation_id: str | None = None,
        inputs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        调用 Dify 的聊天 API

        参数：
          api_key: Dify 应用的 API 密钥（不同的聊天机器人用不同的密钥）
          message: 用户发送的消息
          user: 用户标识（用于 Dify 追踪对话来源）
          conversation_id: 对话 ID（续接之前的对话）
          inputs: 额外的输入变量

        返回 Dify 的原始响应，包含 AI 的回答和对话 ID
        """
        if not api_key:
            raise RuntimeError("Dify chat API key is not configured")

        # 构造请求体
        payload: dict[str, Any] = {
            "inputs": inputs or {},
            "query": message,
            "response_mode": "blocking",  # 阻塞模式：等 AI 回复完再返回（非流式）
            "user": user,
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id

        # 发送 HTTP POST 请求到 Dify 的聊天消息接口
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat-messages",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            )
            response.raise_for_status()  # 如果状态码不是 2xx，抛出异常
            return response.json()

    async def workflow(
        self,
        api_key: str,
        inputs: dict[str, Any],
        user: str,
    ) -> dict[str, Any]:
        """
        调用 Dify 的工作流 API

        工作流（Workflow）是 Dify 上的一个功能，可以编排多个 AI 步骤。
        比如：先分析客户文本 -> 提取关键信息 -> 匹配项目 -> 生成评分和建议

        参数：
          api_key: Dify 工作流的 API 密钥
          inputs: 工作流的输入参数（字典格式）
          user: 用户标识
        """
        if not api_key:
            raise RuntimeError("Dify workflow API key is not configured")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/workflows/run",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"inputs": inputs, "response_mode": "blocking", "user": user},
            )
            response.raise_for_status()
            return response.json()


# 创建全局唯一的 Dify 客户端实例
dify_client = DifyClient()


def fallback_customer_answer(message: str) -> str:
    """
    客户聊天的本地兜底回复函数

    当 Dify 服务不可用时，用这个函数生成"固定答案"回复客户。
    根据用户消息中的关键词（如"新加坡"、"德国"、"费用"等），
    返回预先写好的回答。

    这样做的好处是：即使 AI 平台挂了，用户也不会收到空白回复。
    """
    text = message.lower()
    if "新加坡" in message and ("多少钱" in message or "费用" in message or "学费" in message):
        return (
            "新加坡项目费用可按项目区分：2+2 国际本科班四年总费用约 30-31 万人民币；"
            "0.5/1+2 国际本科班总费用约 25-26 万人民币。具体还要结合专业方向，"
            "例如计算机专业第四年约 19500 新币，其他专业约 16500 新币。"
        )
    if "德国" in message or "双元制" in message:
        return (
            "德国双元制项目适合 18-35 岁、高中及以上学历、动手能力和逻辑思维较强、"
            "愿意学习德语并接受 6-12 个月封闭式培训的学生。项目优势包括免学费、培训津贴、"
            "就业机会、可升学和后续永居规划。"
        )
    if "公司" in message or "联系方式" in message:
        return (
            "广东省教育服务有限公司简称"粤教服务"，创办于 1981 年。公司地址为广东省广州市"
            "越秀区东风东路 723 号高教大厦二楼，电话 020-37628058，邮箱 postmaster@ges1981.com。"
        )
    if "报名" in message or "流程" in message:
        return (
            "报名流程通常包括：提交报名材料、材料核查、参加入学笔试及面试、审核通过后缴纳第一年费用、"
            "发放入学通知或 Offer。德国项目还需要完成德语 B1、企业面试和签证办理。"
        )
    if "hello" in text or "你好" in message:
        return "你好，我是粤教服务智能咨询助手。你可以问我新加坡升学、德国双元制、报名流程、费用和留学政策。"
    return (
        "这���问题我可以先按资料为你初步说明：粤教服务主要提供国际教育、智慧教育、素质教育和实体教育。"
        "如果你能补充年龄、学历、预算和意向国家，我可以进一步推荐新加坡或德国方向的项目。"
    )


def fallback_employee_answer(message: str) -> str:
    """
    员工聊天的本地兜底回复函数

    与 fallback_customer_answer 类似，但面向内部员工，
    回答关于日报、投诉处理、请假审批等工作相关的问题。
    """
    if "日报" in message:
        return "已为你整理日报：今日重点是客户跟进、投诉处理和项目咨询。建议补充客户姓名、跟进结果和下一步计划。"
    if "投诉" in message:
        return "当前系统有待处理或处理中投诉，请在"投诉反馈"页面查看详情并更新处理方案。"
    if "请假" in message:
        return "你可以在"学生请假"页面查看待审批申请，也可以输入"同意某���同学请假"进行业务处理。"
    if "打印机" in message or "新人" in message:
        return "公司打印机位于 3 楼行政办公室正门口走廊处，单次打印不超过 50 页，彩色打印需提前报备。"
    return "我可以协助查询客户、更新跟进状态、生成日报、查看投诉与请假，也能回答新人指南相关问题。"
