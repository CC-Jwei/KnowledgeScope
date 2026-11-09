# 知域 KnowledgeScope — 后端（Phase 2）

FastAPI + Pydantic + SQLite + Chroma。本目录是领域模型与 API 契约的**唯一真相源**；前端通过 `/openapi.json` 生成 TypeScript 类型。

对应文档：

- [`docs/初期基本功能开发说明.md`](../docs/初期基本功能开发说明.md)
- [`docs/配置说明.md`](../docs/配置说明.md)
- [`docs/MVP业务说明.md`](../docs/MVP业务说明.md)（Phase 1 基线）

## 功能范围

| 阶段 | 能力 |
|------|------|
| 2a | 手机号+密码注册/登录（JWT）；Workspace `ownerId` 隔离 |
| 2b | plain_text 异步入库（分块→嵌入→Chroma）；会话与严格边界问答+引用；ModelProfile |
| 2c | `markdown` / `web_page`（单页采集）共用同一入库管道 |
| 保留 | SSE 心跳（需登录；可用 `?access_token=`） |

**推荐数据策略：清空重建。** Phase 2 表结构相对 MVP 有破坏性变更（新增 User、owner_id、Chunk 等）。升级时请删除本地库后重启：

```powershell
Remove-Item -Force .\data\knowledgescope.db -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .\data\chroma -ErrorAction SilentlyContinue
```

## Python 环境（勿用 base 裸奔）

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
```

复制环境变量模板并填写 JWT 与（可选）默认模型：

```powershell
Copy-Item .env.example .env
# 编辑 .env：至少改 JWT_SECRET_KEY；问答/入库需配置 DEFAULT_* 模型或在 UI 建个人档
```

### 启动

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

服务：`http://127.0.0.1:8000`  
文档：`/docs` · `/redoc` · `/openapi.json`  
健康检查：`GET /health`（无需登录）

## API 摘要

Base：`/api/v1`。除 `POST /auth/register`、`POST /auth/login`、`GET /health` 外均需：

```http
Authorization: Bearer <accessToken>
```

| 分组 | 路径 |
|------|------|
| Auth | `POST /auth/register` · `POST /auth/login` · `GET /auth/me` |
| Workspace | `CRUD /workspaces`（仅自己的） |
| Source | `CRUD /workspaces/{id}/sources`（`type`: plain_text / markdown / web_page；创建后 `pending`） |
| Conversation | `POST/GET .../conversations` · `GET/DELETE /conversations/{id}` · `POST .../messages` |
| ModelProfile | `GET/POST/PATCH/DELETE /model-profiles`（系统默认只读标注；Key 脱敏） |
| SSE | `GET /events/heartbeat`（头或 `?access_token=`） |

约定：JSON **camelCase**；越权或不存在统一 **404**；错误为 HTTP 状态码 + `{"detail":"..."}`。

## 入库与问答

```text
创建 Source → pending
  → worker：processing → 规范化 → Chunk → Embedding → Chroma
  → ready | failed（errorMessage）
```

- 前端**轮询** Source `status`（本期不强制 SSE 任务事件）。
- 仅 `ready` 参与检索。
- 问答 AnswerMode 固定 `strict`：无证据返回配置文案「当前知识空间中未找到相关依据。」
- 删除 Source/Workspace：**先删向量，再删业务行**。

后台 worker 在应用启动时自动运行；进程重启后会继续处理仍为 `pending` 的来源。

## 配置

全部键名见 [`docs/配置说明.md`](../docs/配置说明.md) 与 `.env.example`，落在 `app/config.py` / `app/constants.py`。业务代码禁止散落魔法字面量。

系统默认模型（未配置则入库/问答返回明确错误，不静默降级）：

| 变量 | 说明 |
|------|------|
| `DEFAULT_CHAT_BASE_URL` / `DEFAULT_CHAT_API_KEY` / `DEFAULT_CHAT_MODEL` | 聊天 |
| `DEFAULT_EMBEDDING_BASE_URL` / `DEFAULT_EMBEDDING_API_KEY` / `DEFAULT_EMBEDDING_MODEL` | 嵌入 |

亦可在「模型设置」创建个人档并在提问时传入 `chatModelProfileId` / `embeddingModelProfileId`。

## 目录结构

```text
backend/
  app/
    main.py                 # 入口 + OpenAPI Bearer
    config.py / constants.py
    security.py / api/deps.py
    models/                 # User / Workspace / Source / Chunk / Conversation / Message / ModelProfile
    schemas/                # OpenAPI 真相源
    services/               # 业务 + ingest_worker + vector_store + llm_client
    api/routes/
  data/                     # SQLite + Chroma（本地生成，勿提交）
  requirements.txt
  .env.example
```

## 快速自测

```powershell
# 注册
curl -X POST http://127.0.0.1:8000/api/v1/auth/register `
  -H "Content-Type: application/json" `
  -d "{\"phone\":\"13800138000\",\"password\":\"secret12\"}"

# 带 Token 创建空间（替换 TOKEN）
curl -X POST http://127.0.0.1:8000/api/v1/workspaces `
  -H "Authorization: Bearer TOKEN" `
  -H "Content-Type: application/json" `
  -d "{\"name\":\"研究空间\",\"description\":\"demo\"}"

# 投递纯文字（替换 TOKEN / WORKSPACE_ID）
curl -X POST http://127.0.0.1:8000/api/v1/workspaces/WORKSPACE_ID/sources `
  -H "Authorization: Bearer TOKEN" `
  -H "Content-Type: application/json" `
  -d "{\"type\":\"plain_text\",\"title\":\"笔记\",\"content\":\"固态电池进度……\"}"
```

配置好嵌入/聊天模型后，轮询来源至 `ready`，再创建会话并 `POST /conversations/{id}/messages` 验证引用与拒答文案。

## 前端契约流转

```text
backend Pydantic → /openapi.json → shared codegen → front
```
