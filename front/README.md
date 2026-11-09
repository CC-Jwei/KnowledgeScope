# 知域 KnowledgeScope — 前端（MVP）

Vue 3 + TypeScript + Element Plus + UnoCSS。本目录消费 [`shared/`](../shared/) 导出的类型与路径常量，**不手写**与后端平行的 Workspace / Source DTO。

对应业务范围见 [`docs/MVP业务说明.md`](../docs/MVP业务说明.md)。

## 功能范围（MVP）

| 能力 | 说明 |
|------|------|
| 知识空间列表 | 创建、打开、删除（确认框）；展示名称、描述、来源数、时间 |
| 知识空间详情 | 查看/编辑名称与描述；删除空间 |
| 纯文字来源 | 投递、列表、抽屉详情（含全文）、编辑、删除 |
| SSE 心跳 | 顶栏展示：连接中 / 已连接（最近心跳时间） / 断开（可重连） |

本期不做：多 SourceType、RAG、多 Agent、登录权限、WebSocket。

## 环境准备

需要 Node.js ≥ 20。并先按以下文档准备好后端与契约层：

1. [`backend/README.md`](../backend/README.md) — 创建 `.venv` 并启动 FastAPI（默认 `8000`）
2. [`shared/README.md`](../shared/README.md) — 契约已生成（或执行 `npm run generate`）

在 `front/` 安装依赖（PowerShell）：

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

浏览器打开：`http://127.0.0.1:5173`

开发态默认通过 Vite 代理转发 `/api`、`/health` 到 `http://127.0.0.1:8000`（见 `vite.config.ts` / `.env.development`），因此：

- REST 与 SSE 都走同源相对路径，避免浏览器 CORS / EventSource 跨域问题
- 前端代码使用 `@knowledgescope/shared` 的 `ApiPaths`，路径与 backend 保持一致

## 配置

| 变量 | 默认 | 说明 |
|------|------|------|
| `VITE_API_BASE_URL` | 空 | API 基址；开发留空走代理；直连可写 `http://127.0.0.1:8000` |
| `VITE_PROXY_TARGET` | `http://127.0.0.1:8000` | 仅 Vite dev server 代理目标 |

可复制 `.env.example` 为本地覆盖文件（勿提交密钥类内容）。

## 契约使用约定

```text
backend Pydantic
  → /openapi.json
  → shared npm run generate
  → front 引用 @knowledgescope/shared
```

### 推荐 import

```ts
import type {
  Workspace,
  WorkspaceCreate,
  Source,
  SourceListItem,
  PlainTextSourceCreate,
} from '@knowledgescope/shared'

import { ApiPaths, SseEventName, MVP_SOURCE_TYPE } from '@knowledgescope/shared'
```

Vite / TS 已配置别名：

```ts
'@knowledgescope/shared' → ../shared/src/index.ts
```

**禁止**在 `front/src` 再定义一份与 OpenAPI 冲突的 `interface Workspace` / `interface Source`。

改字段流程：

1. 改 `backend/app/schemas/`
2. 在 `shared/` 执行 `npm.cmd run generate`
3. 改本目录调用处

## 目录结构

```text
front/
  src/
    api/                 # REST 封装（workspaces / sources / http）
    components/          # 表单对话框、来源抽屉、SSE 徽标
    composables/         # useSseHeartbeat
    constants/           # 展示用常量（非 DTO）
    layouts/             # 顶栏布局
    router/              # 空间列表 / 详情路由
    utils/               # 时间与错误文案
    views/               # 页面
  .env.development
  .env.example
  vite.config.ts
  uno.config.ts
  README.md
```

## 页面与路由

| 路由 | 页面 | 说明 |
|------|------|------|
| `/` | 知识空间列表 | F1 + 删除确认 |
| `/workspaces/:workspaceId` | 空间详情 | F2 投递/列表/抽屉；编辑空间 |

顶栏全局展示 SSE 连接状态（F3）。

## 常用命令

```powershell
cd front
npm.cmd run dev        # 开发服务器
npm.cmd run build      # 类型检查 + 生产构建
npm.cmd run typecheck  # 仅 vue-tsc
npm.cmd run preview    # 预览构建产物
```

## 验收对照（前端部分）

对应业务文档里程碑 **M4 / 7.1**：

1. 可创建至少 2 个知识空间，列表可见且互不干扰。
2. 在空间 A 投递纯文字后，仅 A 的来源数增加。
3. 来源抽屉可见全文；列表可见标题与 `contentPreview`。
4. 删除来源后计数减少；删除空间后回到列表且无法再打开其来源。
5. 顶栏 SSE 在连接后变为「已连接」，并能看到最近心跳时间更新（约每 15 秒）。

## 常见问题

**Q: 页面提示请求失败 / SSE 一直断开？**  
A: 先确认 backend 已在 `8000` 端口运行；再确认未把 `VITE_API_BASE_URL` 指到错误地址。

**Q: 类型报错找不到 `@knowledgescope/shared`？**  
A: 确认仓库内存在 `shared/src/index.ts`；本前端通过 Vite/TS 路径别名引用，无需把 shared 发布到 npm。

**Q: 后端改了字段前端没跟上？**  
A: 在 `shared/` 重新 `npm run generate`，再按新类型改 `front` 调用处。
