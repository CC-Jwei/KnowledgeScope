# 知域 KnowledgeScope — 后端（MVP）

FastAPI + Pydantic + SQLite。本目录是领域模型与 API 契约的**唯一真相源**；前端应通过 `/openapi.json` 生成 TypeScript 类型，不要手写平行 DTO。

对应业务范围见仓库根目录 [`docs/MVP业务说明.md`](../docs/MVP业务说明.md)。

## 功能范围（MVP）

| 能力 | 说明 |
|------|------|
| 知识空间 CRUD | `POST/GET/PATCH/DELETE /api/v1/workspaces` |
| 纯文字来源 CRUD | 挂在空间下的 `plain_text` 来源 |
| SSE 心跳 | `GET /api/v1/events/heartbeat`，`connected` + 周期 `heartbeat` |

本期不做：多 SourceType、RAG、多 Agent、用户权限、WebSocket。

## Python 环境（请勿使用 base 裸奔）

项目已约定使用 **backend 目录下的独立虚拟环境** `.venv`，不要直接用 conda `base` 或系统全局 Python 安装依赖。

### 首次创建 / 重建

在 `backend/` 目录执行（PowerShell）：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
```

若执行策略拦截激活脚本：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 日常启动

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

不激活也可直接：

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

服务默认：`http://127.0.0.1:8000`

## OpenAPI 文档

FastAPI 自带交互文档与机器可读契约：

| 地址 | 说明 |
|------|------|
| [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Swagger UI |
| [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) | ReDoc |
| [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json) | OpenAPI 3 JSON（前端 codegen 输入） |

健康检查：`GET /health`

## 配置

通过环境变量或 `backend/.env` 覆盖（见 `app/config.py`）：

| 变量 | 默认 | 说明 |
|------|------|------|
| `API_V1_PREFIX` | `/api/v1` | API 前缀 |
| `DATABASE_URL` | `sqlite:///./data/knowledgescope.db` | SQLite 路径 |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | 逗号分隔 |
| `SSE_HEARTBEAT_INTERVAL_SECONDS` | `15` | 心跳间隔（秒） |
| `CONTENT_MAX_LENGTH` | `100000` | 正文最大长度 |
| `TITLE_MAX_LENGTH` | `200` | 标题最大长度 |
| `CONTENT_PREVIEW_LENGTH` | `120` | 列表预览截断长度 |

业务常量（名称长度、默认标题文案等）集中在 `app/config.py`，业务代码不散落魔法字面量。

## 数据存储

- 方案：**SQLite + SQLAlchemy ORM**
- 库文件默认：`backend/data/knowledgescope.db`（首次启动自动建目录与表）
- 删除知识空间会**级联删除**其下全部来源（硬删除）
- 数据持久化在本地文件；删库或换路径即清空

## API 约定

- Base path：`/api/v1`
- JSON 字段：**camelCase**（Python 内部 snake_case，Pydantic alias 转换）
- 错误：HTTP 状态码 + `{"detail": "..."}`（FastAPI 默认）
- MVP 不分页，列表一次返回全部
- 创建来源时 `type` 由服务端写为 `plain_text`；若客户端传入其它类型 → `422`
- 未传标题时：取正文前 30 字，否则「未命名文本」；状态恒为 `ready`

### 快速自测（示例）

```powershell
# 创建空间
curl -X POST http://127.0.0.1:8000/api/v1/workspaces `
  -H "Content-Type: application/json" `
  -d "{\"name\":\"新能源汽车行业研究\",\"description\":\"竞品与政策资料\"}"

# 创建纯文字来源（替换 WORKSPACE_ID）
curl -X POST http://127.0.0.1:8000/api/v1/workspaces/WORKSPACE_ID/sources `
  -H "Content-Type: application/json" `
  -d "{\"title\":\"会议临时记录\",\"content\":\"今天讨论了三家车企的固态电池进度……\"}"

# SSE 心跳（需支持流式的客户端；Ctrl+C 断开）
curl -N http://127.0.0.1:8000/api/v1/events/heartbeat
```

## 目录结构

```text
backend/
  .venv/                 # 本项目独立 Python 环境（勿提交）
  app/
    main.py              # 应用入口
    config.py            # 配置与业务常量
    database.py          # SQLite / Session
    models/              # SQLAlchemy ORM
    schemas/             # Pydantic 契约（OpenAPI 真相源）
    api/routes/          # HTTP / SSE 路由
    services/            # 业务逻辑
  data/                  # SQLite 数据（本地生成，勿提交）
  requirements.txt
  README.md
```

## 前端契约流转

```text
backend Pydantic
  → FastAPI /openapi.json
  → shared/ 生成脚本（openapi-typescript）
  → front 引用 @knowledgescope/shared
```

改字段只改本后端模型，然后在 [`shared/`](../shared/) 执行 `npm run generate`，再改 front 调用处。详见 [`shared/README.md`](../shared/README.md)。

## 验收对照（后端部分）

1. 可创建多个知识空间，互不干扰。
2. 在空间 A 创建来源后仅 A 的 `sourceCount` 增加。
3. 来源详情含全文；列表含 `contentPreview`、不含完整 `content`。
4. 删除来源后计数减少；删除空间后其来源不可再访问。
5. SSE 可连续收到 `connected` 与多次 `heartbeat`。
6. `/docs` 与 `/openapi.json` 可见 Workspace / Source 相关 schema。
