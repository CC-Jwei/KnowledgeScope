# 知域 KnowledgeScope — 前端（Phase 2）

Vue 3 + TypeScript + Element Plus + UnoCSS。本目录消费 [`shared/`](../shared/) 导出的类型与路径常量，**不手写**与后端平行的 DTO。

范围见 [`docs/初期基本功能开发说明.md`](../docs/初期基本功能开发说明.md) 与 [`docs/配置说明.md`](../docs/配置说明.md)。

## 功能范围

| 能力 | 说明 |
|------|------|
| 登录 / 注册 | 手机号 + 密码；JWT 存 `localStorage`；未登录跳 `/login` |
| 知识空间 | 仅当前用户；列表/创建/编辑/删除（级联提示） |
| 来源投递 | `plain_text` / `markdown` / `web_page`；创建后 `pending` |
| 入库状态 | 列表轮询 `pending` / `processing` / `ready` / `failed`；抽屉含 `errorMessage` / `sourceUrl` |
| 会话问答 | 空间下新建/删除会话；严格边界提问；助手消息展示 Citation |
| 模型设置 | 系统默认标注「默认」；个人档 CRUD；API Key 只写脱敏 |
| SSE 心跳 | 登录后 `ApiPaths.heartbeat(accessToken)`；顶栏连接态 |

本期不做：成员协作、多 Agent、非严格回答模式、短信登录。

## 环境准备

需要 Node.js ≥ 20。

1. 按 [`backend/README.md`](../backend/README.md) 启动 FastAPI（默认 `8000`）。
2. 按 [`shared/README.md`](../shared/README.md) 确认契约已生成。

```powershell
cd front
npm.cmd install
```

## 日常启动

**终端 1 — 后端**

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**终端 2 — 前端**

```powershell
cd front
npm.cmd run dev
```

打开：`http://127.0.0.1:5173`

开发态 `/api`、`/health` 由 Vite 代理到后端（见 `vite.config.ts`）。REST 与 SSE 同源，EventSource 通过 `?access_token=` 鉴权。

## 配置

| 变量 | 默认 | 说明 |
|------|------|------|
| `VITE_API_BASE_URL` | 空 | 开发留空走代理；直连可写 `http://127.0.0.1:8000` |
| `VITE_PROXY_TARGET` | `http://127.0.0.1:8000` | 仅 dev server 代理目标 |

JWT 密钥、默认模型、向量库等**只配在 backend**，不要写进 front/shared。

## 契约使用

```text
backend Pydantic → OpenAPI → shared generate → front @knowledgescope/shared
```

```ts
import type {
  SourceCreateInput,
  AskMessageRequest,
  ModelProfile,
} from '@knowledgescope/shared'
import { ApiPaths, SourceTypeValue, SourceStatusValue } from '@knowledgescope/shared'
```

别名：`'@knowledgescope/shared' → ../shared/src/index.ts`

改字段：改 backend → `shared` 执行 `npm run generate` → 改 front 调用处。

## 页面路由

| 路由 | 页面 |
|------|------|
| `/login` | 登录 / 注册 |
| `/` | 知识空间列表 |
| `/workspaces/:workspaceId` | 空间详情 + 来源投递/轮询 |
| `/workspaces/:workspaceId/chat` | 会话与严格问答 |
| `/model-profiles` | 模型设置 |

## 目录结构

```text
front/src/
  api/           # http + workspaces/sources/conversations/modelProfiles
  stores/        # auth（Token + 当前用户）
  router/        # 路由与登录守卫
  views/         # 登录、列表、详情、会话、模型设置
  components/    # 投递表单、抽屉、对话框、SSE 徽标
  composables/   # useSseHeartbeat（带 Token）
  utils/         # 时间、错误、来源状态展示
```

## 常用命令

```powershell
npm.cmd run dev        # 开发
npm.cmd run typecheck  # vue-tsc
npm.cmd run build      # 类型检查 + 构建
npm.cmd run preview    # 预览构建
```

## 验收对照

1. 注册/登录后获得 Token；未登录访问业务页会跳登录。
2. 用户只能看到自己空间；来源创建后状态经轮询变为 ready/failed。
3. 会话可提问；无证据时展示后端固定文案；有证据时展示引用标题/片段。
4. 模型设置可增删改个人档，系统默认不可改删；Key 不回显明文。
