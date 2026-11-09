# 知域 KnowledgeScope

基于本地 RAG 的多源知识归并与多智能体协作平台（MVP 阶段）。

用户将文字、文件、网页、图片与视频链接投入**知识空间**，系统在明确知识边界内完成采集、解析、归并与检索；后续可由多个 Agent 基于证据协作分析，并追溯原始出处。

> 当前仓库已跑通 MVP 最短闭环：**知识空间 CRUD → 纯文字来源 CRUD → SSE 心跳**。多源解析、RAG、多 Agent 等能力按路线图迭代。

## 功能概览（MVP）

| 能力 | 说明 |
|------|------|
| 知识空间 | 创建 / 列表 / 详情 / 更新 / 删除 |
| 纯文字来源 | 在空间内投递、查看、编辑、删除 |
| SSE 心跳 | 前后端长连接状态展示，为后续任务流预留通道 |

本期明确不做：多 SourceType、Embedding / 向量库、多 Agent、登录权限、WebSocket。详见 [`docs/MVP业务说明.md`](docs/MVP业务说明.md)。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 `front/` | Vue 3 · TypeScript · Element Plus · UnoCSS · Vite |
| 后端 `backend/` | FastAPI · Pydantic · SQLAlchemy · SQLite · SSE |
| 契约 `shared/` | 由后端 OpenAPI 生成 TypeScript 类型（openapi-typescript） |

**契约约定：** 领域模型与 API 的唯一真相源在 `backend/`。改字段只改后端 Pydantic，再在 `shared/` 执行 `npm run generate`，前端禁止手写平行 DTO。

## 仓库结构

```text
.
├── front/          # Vue 3 前端
├── backend/        # FastAPI 后端
├── shared/         # OpenAPI → TypeScript 契约层
├── docs/           # 产品预想与 MVP 业务说明
├── LICENSE         # MIT
└── README.md
```

## 快速开始

### 环境要求

- Python ≥ 3.11（建议使用 `backend/.venv`，勿用全局 base）
- Node.js ≥ 20
- Windows PowerShell / macOS / Linux 均可

### 1. 后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # macOS/Linux: source .venv/bin/activate
python -m pip install -U pip
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API：`http://127.0.0.1:8000`
- Swagger：`http://127.0.0.1:8000/docs`
- OpenAPI：`http://127.0.0.1:8000/openapi.json`

可选：复制 `backend/.env.example` 为 `backend/.env` 覆盖配置。

### 2. 契约层（首次或改过后端模型时）

```powershell
cd shared
npm.cmd install
npm.cmd run generate
```

生成脚本默认从 `backend/.venv` 导入应用导出 OpenAPI，**不必先启动 uvicorn**。

### 3. 前端

```powershell
cd front
npm.cmd install
npm.cmd run dev
```

浏览器打开：`http://127.0.0.1:5173`  
开发态通过 Vite 代理转发 `/api`、`/health` 到后端 `8000`，避免 CORS / EventSource 跨域。

更细的说明见：

- [`backend/README.md`](backend/README.md)
- [`shared/README.md`](shared/README.md)
- [`front/README.md`](front/README.md)

## 文档

| 文档 | 内容 |
|------|------|
| [`CONTEXT.md`](CONTEXT.md) | 领域术语（知识空间、来源、严格边界等） |
| [`docs/项目初步预想.md`](docs/项目初步预想.md) | 产品定位、知识空间模型、多源与 Agent 路线 |
| [`docs/MVP业务说明.md`](docs/MVP业务说明.md) | Phase 1 基线：空间 / plain_text / SSE |
| [`docs/初期基本功能开发说明.md`](docs/初期基本功能开发说明.md) | Phase 2：多用户、RAG、多 SourceType、数据模型 |
| [`docs/配置说明.md`](docs/配置说明.md) | 配置键与默认值（禁止业务魔法字面量） |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | 本地开发与贡献约定 |

## 路线图（摘录）

1. **MVP（当前）**：知识空间 + 纯文字来源 + SSE
2. **Phase 2a–2c**：用户隔离 → plain_text RAG → markdown / web_page（见初期开发说明）
3. **后续**：更多 SourceType、Redis/Go 演进、多 Agent 协作工作流

## 开源许可

本项目采用 [MIT License](LICENSE)。
