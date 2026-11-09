# 知域 KnowledgeScope — shared（契约层）

本目录是前后端之间的 **TypeScript 契约消费层**，不是第二份手写 DTO。

对应业务范围见 [`docs/MVP业务说明.md`](../docs/MVP业务说明.md)。  
领域模型与 API 的**唯一真相源**在 [`backend/`](../backend/)（Pydantic → FastAPI OpenAPI）。

## 定位（方案 A）

```text
backend Pydantic 模型
    → FastAPI /openapi.json
    → shared 生成脚本（openapi-typescript）
    → shared/generated + src 类型别名
    → front 只引用 shared，禁止再手写平行 Workspace/Source 接口
```

| 可以放这里 | 不要放这里 |
|------------|------------|
| OpenAPI 快照与生成脚本 | 手写与后端字段平行的 DTO |
| 生成的 TS 类型 / 友好别名 | 爬虫、RAG、Agent 等业务逻辑 |
| API 路径、SSE 事件名等客户端常量 | Vue 组件、页面、样式 |
| 给 front 用的路径拼装工具 | 第二套「真相源」枚举/模型 |

改字段：**只改 backend 模型 → 在本目录重新 `npm run generate` → 再改 front 调用处。**

## 目录结构

```text
shared/
  openapi/
    openapi.json       # 从 backend 导出的 OpenAPI 快照（可提交）
  generated/
    openapi.ts         # openapi-typescript 产物（可提交，勿手改）
    README.md
  src/
    index.ts           # 对外入口
    schema.ts          # 从 generated 抽出的类型别名
    constants.ts       # API 前缀、SSE 事件名等
    paths.ts           # REST/SSE 路径拼装
  scripts/
    dump-openapi.mjs   # 导出 OpenAPI JSON
    generate.mjs       # dump + 生成 TS
  package.json
  tsconfig.json
  README.md
```

## 环境准备

需要 Node.js ≥ 20。在 `shared/` 安装依赖：

```powershell
cd shared
npm.cmd install
```

生成脚本默认通过 **`backend/.venv`** 直接 `import app` 导出 OpenAPI，**不必先启动 uvicorn**。  
请确保已按 [`backend/README.md`](../backend/README.md) 创建虚拟环境并安装依赖。

## 生成类型

在 `shared/` 执行：

```powershell
cd shared
npm.cmd run generate
```

等价于：

1. `dump:openapi` — 写出 `openapi/openapi.json`
2. `openapi-typescript` — 写出 `generated/openapi.ts`

### 可选：从已启动的后端拉取

```powershell
# 默认 http://127.0.0.1:8000/openapi.json
npm.cmd run generate:from-url

# 或自定义地址
$env:OPENAPI_URL = "http://127.0.0.1:8000/openapi.json"
node .\scripts\generate.mjs --from-url --url http://127.0.0.1:8000/openapi.json
```

### 仅导出 OpenAPI 快照

```powershell
npm.cmd run dump:openapi
```

## 前端如何使用

`front` 尚未接入时，可先按下列方式准备（任选其一）。

### 方式 1：Vite / TS 路径别名

```ts
// vite.config 示例
resolve: {
  alias: {
    '@knowledgescope/shared': path.resolve(__dirname, '../shared/src/index.ts'),
  },
}
```

### 方式 2：workspace 依赖

```json
{
  "dependencies": {
    "@knowledgescope/shared": "workspace:*"
  }
}
```

### 推荐 import

```ts
import type {
  Workspace,
  WorkspaceCreate,
  Source,
  SourceListItem,
  PlainTextSourceCreate,
  HeartbeatEvent,
  ConnectedEvent,
} from '@knowledgescope/shared'

import {
  ApiPaths,
  SseEventName,
  API_V1_PREFIX,
  MVP_SOURCE_TYPE,
} from '@knowledgescope/shared'

const url = ApiPaths.workspaces()
const sseUrl = ApiPaths.heartbeat()

if (eventName === SseEventName.Heartbeat) {
  // data 类型为 HeartbeatEvent
}
```

需要完整 OpenAPI `paths` / `operations`（例如配合 openapi-fetch）时：

```ts
import type { paths, operations } from '@knowledgescope/shared'
// 或
import type { paths } from '@knowledgescope/shared/generated/openapi'
```

## 当前契约覆盖（MVP）

与 backend OpenAPI 对齐，生成结果中应包含：

| Schema | 用途 |
|--------|------|
| `Workspace` / `WorkspaceCreate` / `WorkspaceUpdate` | 知识空间 |
| `Source` / `SourceListItem` | 来源详情 / 列表 |
| `PlainTextSourceCreate` / `PlainTextSourceUpdate` | 纯文字写入 |
| `SourceType` / `SourceStatus` | 枚举 |
| `ConnectedEvent` / `HeartbeatEvent` | SSE data |

| 路径（`ApiPaths`） | 方法 | 说明 |
|--------------------|------|------|
| `/api/v1/workspaces` | CRUD | 知识空间 |
| `/api/v1/workspaces/{id}/sources` | CRUD | 纯文字来源 |
| `/api/v1/events/heartbeat` | GET (SSE) | `connected` + 周期 `heartbeat` |

JSON 字段为 **camelCase**（与 backend alias 一致）。

## 工作流约定

1. 在 `backend/app/schemas/` 修改或新增 Pydantic 模型。
2. （可选）本地启动 backend，打开 `/docs` 确认 schema。
3. 在 `shared/` 执行 `npm run generate`。
4. 查看 `generated/openapi.ts`；若有新 schema，在 `src/schema.ts` / `src/index.ts` 补别名导出。
5. 更新 `front` 调用处；**不要**在 front 再定义一份同名 interface。

新增 SSE 事件或 SourceType 时：同样先改 backend，再 regenerate；若有新的事件名常量，同步补 `src/constants.ts`。

## 验收对照（shared 部分）

对应业务文档里程碑 **M5**：

1. `openapi/openapi.json` 含 Workspace、Source、SSE 相关 schema。
2. `generated/openapi.ts` 可由脚本稳定再生。
3. `src/index.ts` 能导出 MVP 所需类型别名与 `ApiPaths` / `SseEventName`。
4. README 写清生成命令与「禁止手写平行 DTO」约定。

## 常见问题

**Q: 为什么不直接在 shared 手写 TypeScript interface？**  
A: 会与 Pydantic 漂移。方案 A 要求后端为真相源，shared 只消费生成结果。

**Q: `src/schema.ts` 里的 `export type Workspace = ...` 算不算手写 DTO？**  
A: 不算。那是对生成 schema 的别名投影，字段定义仍来自 OpenAPI。

**Q: generate 报错找不到 python？**  
A: 先完成 `backend/.venv` 安装；或改用 `npm run generate:from-url`（需 backend 已在 8000 端口运行）。

**Q: 要不要把 `generated/` 提交进 git？**  
A: MVP 建议提交，方便 front 在未跑生成脚本时也能拿到类型；后端契约变更后务必重新 generate 并一并提交。
