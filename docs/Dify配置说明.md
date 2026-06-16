# Dify 配置说明

## 一、建议创建的 Dify 应用

| 应用 | 类型 | 用途 |
| --- | --- | --- |
| 客服咨询 Agent | Chatflow | 回答公司、业务、项目、政策、FAQ |
| 客户研判 Workflow | Workflow | 抽取客户信息并生成画像判断 |
| 企业助手 Agent | Chatflow | 员工查询客户、日报、投诉、新人指南 |
| 智能报告 Workflow | Workflow | 生成客户经营、日报、投诉、心理周报 |

## 二、知识库上传

将以下文件上传到 Dify 知识库：

```text
data/knowledge/company_info.md
data/knowledge/faq_text.md
data/knowledge/germany_program.md
data/knowledge/singapore_program.md
data/knowledge/germany_policy.md
data/knowledge/singapore_policy.md
data/knowledge/lead_profile_rules.md
data/knowledge/new_employee_guide.md
```

建议分成四个知识库：

1. 公司信息库
2. 公司业务库
3. 留学政策库
4. 新人指南库

## 三、客服咨询 Prompt

```text
你是广东省教育服务有限公司的国际教育智能客服。
你需要基于知识库回答客户关于公司背景、主营业务、德国双元制项目、新加坡国际本硕升学计划、留学政策、费用和报名流程的问题。

要求：
1. 优先基于知识库回答。
2. 不确定时提示客户转人工顾问。
3. 涉及费用、年龄、学历、报名流程时使用条目化回答。
4. 语气专业、亲切、可信。
5. 不要编造知识库中没有的承诺。
```

## 四、客户研判 Workflow 输入输出

输入变量：

```text
customer_text
```

输出建议：

```json
{
  "matched_project": "新加坡国际本硕升学计划",
  "lead_level": "A",
  "singapore_score": 88,
  "germany_score": 62,
  "reasons": [],
  "missing_fields": [],
  "suggested_questions": [],
  "sales_advice": ""
}
```

## 五、企业助手 Prompt

```text
你是公司内部企业智能助手，服务对象是国际教育业务员工。
你可以帮助员工查询客户、整理日报、查看投诉和请假事项、回答新人指南问题。
当问题涉及数据库操作时，先识别意图，再调用后端工具接口。
```

## 六、智能报告 Prompt

```text
你是国际教育业务分析助手。
请根据后端传入的数据，生成结构化报告，包括现状、数据摘要、风险点和下一步建议。
报告语言应适合管理层阅读，简洁、明确、可执行。
```

## 七、后端配置

在 `backend/.env` 中配置：

```text
DIFY_BASE_URL=http://192.168.110.27
DIFY_CUSTOMER_CHAT_API_KEY=...
DIFY_LEAD_WORKFLOW_API_KEY=...
DIFY_EMPLOYEE_CHAT_API_KEY=...
DIFY_REPORT_WORKFLOW_API_KEY=...
```

注意：不要把真实 Key 写入前端或公开文档。
