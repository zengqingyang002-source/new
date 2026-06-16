# 基于 Dify 的国际教育智能服务平台

本项目是一个毕业设计演示完整版，面向国际教育业务场景，覆盖客户咨询、客户画像研判、客户管理 CRM、企业助手、学生请假/投诉、心理预警和智能报告。

## 技术栈

- 前端：Vue3 + Element Plus + Vite
- 后端：FastAPI + SQLAlchemy
- 数据库：MySQL 8
- AI 平台：Dify Chatflow / Workflow
- 文件解析：Python、pdfplumber、openpyxl、docx XML 解析
- 部署：本地运行或 Docker Compose

## 目录结构

```text
edu_dify_platform/
  backend/          FastAPI 后端
  frontend/         Vue3 前端
  data/             知识库资料和种子数据
  dify/             Dify 提示词与配置说明
  docs/             项目文档
  docker/           预留部署资料
  scripts/          资料抽取脚本
  docker-compose.yml
```

## 本地运行

### 1. 后端

确认 MySQL 可用：

```bash
mysql -uroot -p123456 -e "SELECT VERSION();"
```

安装依赖并启动：

```bash
cd backend
pip install -r requirements.txt
python run.py
```

后端地址：

```text
http://localhost:8000
```

接口文档：

```text
http://localhost:8000/docs
```

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

前端地址：

```text
http://localhost:5173
```

也可以在项目根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_dev.ps1
```

停止本地开发服务：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\stop_dev.ps1
```

## Docker 一键启动

```bash
docker compose up --build
```

说明：

- 前端端口：5173
- 后端端口：8000
- Docker 内 MySQL 端口：3306
- 映射到宿主机端口：3307，避免和本机 MySQL 3306 冲突

如果要让 Docker 后端使用真实 Dify Key，请在运行前设置环境变量，或创建 compose 用 `.env`。

## 测试账号

```text
管理员：admin / 123456
员工：employee / 123456
学生：student / 123456
客户：customer / 123456
```

## 20 分钟演示流程

1. 登录管理员账号。
2. 查看首页仪表盘。
3. 进入客服咨询，询问“新加坡 2+2 国际本科班多少钱？”。
4. 进入客户研判，输入样例客户信息并生成画像。
5. 点击“研判并入库”，进入 CRM 查看新增客户。
6. 更新客户状态为“跟进中”或“已签约”。
7. 进入企业助手，查询投诉、新人指南或生成日报。
8. 进入学生服务，提交请假和投诉，员工端审批或处理。
9. 进入智能报告，生成客户经营分析报告和投诉周报。
10. 说明 Dify 知识库、Workflow 和后端工具调用设计。

## Dify 接入说明

真实 Dify 配置在 `backend/.env` 中：

```text
DIFY_BASE_URL=http://192.168.110.27
DIFY_CUSTOMER_CHAT_API_KEY=...
DIFY_LEAD_WORKFLOW_API_KEY=...
DIFY_EMPLOYEE_CHAT_API_KEY=...
DIFY_REPORT_WORKFLOW_API_KEY=...
```

前端不会直接访问 Dify，也不会暴露 API Key。

如果 Dify 暂时不可用，后端会启用本地 fallback，保证毕业设计演示链路稳定。

## 知识库资料

已经整理到：

```text
data/knowledge/
```

包括：

- company_info.md
- faq_text.md
- germany_program.md
- singapore_program.md
- germany_policy.md
- singapore_policy.md
- lead_profile_rules.md
- new_employee_guide.md

这些文件可以直接上传到 Dify 知识库。
