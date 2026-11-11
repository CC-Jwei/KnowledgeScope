# 知域 KnowledgeScope — shared（契约层）

本目录是前后端之间的 **TypeScript 契约消费层**，不是第二份手写 DTO，也不是另一个独立后端。

领域模型与 API 的**唯一真相源**在 [`backend/`](../backend/)：`Pydantic → FastAPI OpenAPI → shared TypeScript → front`。

## 文档与范围

| 文档 | 与本目录的关系 |
|------|----------------|
| [`docs/初期基本功能开发说明.md`](../docs/初期基本功能开发说明.md) | 当前 Phase 2a / 2b / 2c 的 API、数据模型与验收范围 |
| [`docs/配置说明.md`](../docs/配置说明.md) | 后端阈值、模型、向量库等配置；**不在 shared 复制这些环境变量** |
| [`docs/MVP业务说明.md`](../docs/MVP业务说明.md) | Phase 1 基线；已被 Phase 2 契约替换的部分以最新 OpenAPI 为准 |
| [`backend/README.md`](../backend/README.md) | 后端启动、鉴权、入库与问答实现说明 |

当前生成契约覆盖：

- **2a**：手机号注册/登录、JWT、当前用户、Workspace `ownerId` 隔离
- **2b**：异步入库状态、Conversation / Message / Citation、严格边界问答、ModelProfile
- **2c**：`plain_text` / `markdown` / `web_page` 三种来源创建
- **SSE**：登录后的 `connected` + `heartbeat`；EventSource 可通过 `?access_token=` 传令牌

## 定位（方案 A）

```text
backend/app/schemas/（Pydantic）
    → backend app.openapi()
    → shared/openapi/openapi.json
    → openapi-typescript
    → shared/generated/openapi.ts
    → shared/src/schema.ts 类型别名 + src/index.ts 导出
    → front 引用 @knowledgescope/shared
```

| 可以放这里 | 不要放这里 |
|------------|------------|
| OpenAPI 快照与生成脚本 | 手写与后端字段平行的 DTO |
| 生成类型的友好别名 | 爬虫、分块、向量库、问答编排等业务逻辑 |
| API 路径、SSE 事件名等客户端常量 | Vue 组件、页面、样式 |
| 为前端收窄的条件必填输入类型 | JWT 密钥、模型 Key、Chroma 路径等后端配置 |
| 固定的严格模式文案等协议约定 | 另一套可独立修改的领域模型 |

**改字段流程：只改 backend Pydantic → 在本目录 `npm run generate` → 再改 front 调用处。**

## 目录结构

```text
shared/
  openapi/
    openapi.json       # 从 backend 导出的 OpenAPI 快照
  generated/
    openapi.ts         # openapi-typescript 产物，勿手改
    README.md
  src/
    index.ts           # 对外入口：类型、常量、ApiPaths
    schema.ts          # 从 generated 投影的类型别名与表单输入收窄
    constants.ts       # 枚举字面量、SSE 名称、严格模式约定
    paths.ts           # REST / SSE 路径拼装
  scripts/
    dump-openapi.mjs   # 导出 OpenAPI JSON
    generate.mjs       # dump + 生成 TS
  package.json
  tsconfig.json
  README.md
```

## 环境与生成

需要 Node.js ≥ 20。先安装依赖：

```powershell
cd shared
npm.cmd install
```

再生成契约：

```powershell
npm.cmd run generate
npm.cmd run typecheck
```

`generate` 默认调用 `backend/.venv` 中的 Python，直接执行 `app.openapi()` 导出契约，**无需先启动 uvicorn**。因此先生成类型、再启动后端也可以。

前提是已按 [`backend/README.md`](../backend/README.md) 创建 `backend/.venv` 并安装依赖。导出契约不会替后端设置生产配置，也不会启动入库 worker。

### 从运行中的服务拉取

```powershell
# 默认 http://127.0.0.1:8000/openapi.json
npm.cmd run generate:from-url

# 或指定其他地址
$env:OPENAPI_URL = "http://127.0.0.1:8000/openapi.json"
node .\scripts\generate.mjs --from-url --url http://127.0.0.1:8000/openapi.json
```

仅更新 JSON 快照、不生成 TS 时：

```powershell
npm.cmd run dump:openapi
```

## 前端引用

当前 `front` 可通过 Vite / TS 路径别名使用：

```ts
'@knowledgescope/shared' → ../shared/src/index.ts
```

若改用 workspace 依赖，包名为 `@knowledgescope/shared`，入口是 `src/index.ts`。

### 1. 认证与请求头

```ts
import type {
  LoginRequest,
  TokenResponse,
  UserPublic,
  Workspace,
} from '@knowledgescope/shared'
import { ApiPaths } from '@knowledgescope/shared'

const loginBody: LoginRequest = {
  phone: '13800138000',
  password: 'secret12',
}

// POST ApiPaths.authLogin()，成功响应为 TokenResponse。
// 后续 REST 请求带 Authorization: Bearer <accessToken>。
// GET ApiPaths.authMe() 返回 UserPublic；Workspace 含 ownerId。
```

除 `POST /auth/register`、`POST /auth/login`、`GET /health` 外，当前业务接口均需 Bearer Token。越权或资源不存在统一返回 `404`。

### 2. 三种来源投递

OpenAPI 的 `SourceCreate` 对 `content` / `url` 使用可选字段，因为 Pydantic 在模型校验器中按 `type` 判断条件必填。shared 额外提供**不改动运行时**的类型收窄，帮助表单在编译期传对字段：

```ts
import type {
  PlainTextSourceCreate,
  MarkdownSourceCreate,
  WebPageSourceCreate,
  SourceCreateInput,
} from '@knowledgescope/shared'
import { SourceTypeValue } from '@knowledgescope/shared'

const text: PlainTextSourceCreate = {
  type: SourceTypeValue.PlainText,
  title: '会议记录',
  content: '正文……',
}

const markdown: MarkdownSourceCreate = {
  type: SourceTypeValue.Markdown,
  content: '# 标题\n\n正文……',
}

const webPage: WebPageSourceCreate = {
  type: SourceTypeValue.WebPage,
  url: 'https://example.com/article',
}

const payload: SourceCreateInput = text
// POST ApiPaths.sources(workspaceId)
```

`SourceType` 仍完整保留后端预留枚举；投递表单只使用 `CREATABLE_SOURCE_TYPES` 中的三种。

创建后来源进入 `pending`，随后可能为 `processing` / `ready` / `failed`。前端轮询 `Source.status`，失败原因读 `errorMessage`，网页地址读 `sourceUrl`。

```ts
import {
  ApiPaths,
  CREATABLE_SOURCE_TYPES,
  INITIAL_SOURCE_STATUS,
  SourceStatusValue,
} from '@knowledgescope/shared'

// INITIAL_SOURCE_STATUS === 'pending'
// SourceStatusValue.Ready === 'ready'
```

### 3. 会话、严格问答与引用

```ts
import type {
  Conversation,
  ConversationCreate,
  ConversationDetail,
  AskMessageRequest,
  AskMessageResponse,
  Citation,
} from '@knowledgescope/shared'
import {
  ANSWER_MODE_STRICT,
  ApiPaths,
  STRICT_NO_EVIDENCE_REPLY,
} from '@knowledgescope/shared'

const createBody: ConversationCreate = { title: '研究讨论' }
// POST ApiPaths.conversations(workspaceId)

const askBody: AskMessageRequest = {
  content: '这篇资料的主要结论是什么？',
  // 可选：chatModelProfileId / embeddingModelProfileId
}
// POST ApiPaths.conversationMessages(conversationId)
// 响应 AskMessageResponse：userMessage + assistantMessage
```

`assistantMessage.citations` 为 `Citation[]`，包含 `sourceId`、`chunkId`、`title` 与可选 `snippet`。

`ANSWER_MODE_STRICT` 和 `STRICT_NO_EVIDENCE_REPLY` 是与后端对齐的协议常量，不是前端自行决定回答内容的逻辑。检索、拒答和生成仍全部由 backend 完成。

### 4. 模型配置

```ts
import type {
  ModelProfile,
  ModelProfileCreate,
  ModelProfileUpdate,
} from '@knowledgescope/shared'
import { ApiPaths, ModelPurposeValue } from '@knowledgescope/shared'

const createBody: ModelProfileCreate = {
  name: '我的聊天模型',
  purpose: ModelPurposeValue.Chat,
  baseUrl: 'https://example.com/v1',
  modelName: 'my-chat-model',
  apiKey: '<write-only-key>',
}

// GET/POST ApiPaths.modelProfiles()
// PATCH/DELETE ApiPaths.modelProfile(profileId)
```

列表中的 `isSystemDefault` 用于标注「默认」。响应只含 `apiKeyMasked`；个人档更新不传 `apiKey` 时保留原 Key。

**不要把默认模型名、完整 API Key、JWT 密钥或 Chroma 配置写进 shared/front。** 这些属于 [`docs/配置说明.md`](../docs/配置说明.md) 与 backend。

### 5. 带 Token 的 SSE 心跳

浏览器原生 `EventSource` 不能自定义 `Authorization` 头，可把 accessToken 交给路径工厂：

```ts
import type { ConnectedEvent, HeartbeatEvent } from '@knowledgescope/shared'
import { ApiPaths, SseEventName } from '@knowledgescope/shared'

const source = new EventSource(ApiPaths.heartbeat(accessToken))

source.addEventListener(SseEventName.Connected, (event) => {
  const data = JSON.parse(event.data) as ConnectedEvent
})

source.addEventListener(SseEventName.Heartbeat, (event) => {
  const data = JSON.parse(event.data) as HeartbeatEvent
})
```

若使用支持自定义请求头的 SSE 客户端，也可调用无参数 `ApiPaths.heartbeat()`，自行添加 Bearer 头。

## 当前契约索引

本次从 backend 生成 **14 条路径、29 个 schema**。字段以 `generated/openapi.ts` 和 `openapi/openapi.json` 为准。

### Schema

| 分组 | 导出 |
|------|------|
| Auth | `RegisterRequest`、`LoginRequest`、`TokenResponse`、`UserPublic` |
| Workspace | `Workspace`、`WorkspaceCreate`、`WorkspaceUpdate` |
| Source | `Source`、`SourceListItem`、`SourceCreate`、`SourceUpdate` |
| 来源输入收窄 | `PlainTextSourceCreate`、`MarkdownSourceCreate`、`WebPageSourceCreate`、`SourceCreateInput` |
| 枚举 | `SourceType`、`SourceStatus`、`MessageRole`、`ModelPurpose` |
| 会话问答 | `Conversation`、`ConversationCreate`、`ConversationDetail`、`Message`、`Citation`、`AskMessageRequest`、`AskMessageResponse` |
| 模型档 | `ModelProfile`、`ModelProfileCreate`、`ModelProfileUpdate` |
| SSE | `ConnectedEvent`、`HeartbeatEvent` |
| FastAPI 错误 | `HTTPValidationError`、`ValidationError` |

Chunk、向量库记录、密码哈希、加密 API Key 不是前端 API 契约，不应在这里另造 DTO。

### ApiPaths

| 方法 | 地址 |
|------|------|
| `authRegister()` | `POST /api/v1/auth/register` |
| `authLogin()` | `POST /api/v1/auth/login` |
| `authMe()` | `GET /api/v1/auth/me` |
| `workspaces()` / `workspace(id)` | 空间 CRUD |
| `sources(id)` / `source(id, sourceId)` | 来源 CRUD 与状态轮询 |
| `conversations(id)` / `conversation(id)` | 会话创建、列表、详情、删除 |
| `conversationMessages(id)` | 严格边界提问 |
| `modelProfiles()` / `modelProfile(id)` | 模型档列表、创建、更新、删除 |
| `heartbeat(token?)` | `GET /api/v1/events/heartbeat` |

需要完整 OpenAPI `paths` / `operations` 时：

```ts
import type { paths, operations, components } from '@knowledgescope/shared'
```

JSON 字段统一为 **camelCase**；Python 内部为 snake_case。

## 与配置说明的边界

`配置说明.md` 中的配置分两类：

1. **后端运行配置**：JWT、密码哈希、分块、网页采集、向量库、默认模型等。只放 backend `.env` / `Settings` / 常量类，不生成到 TS。
2. **前端需要理解的协议约定**：例如来源类型、处理状态、模型用途、SSE 事件名。枚举以生成的 OpenAPI 类型为准；常用字面量由 `src/constants.ts` 的 `satisfies` 约束，后端删掉或改值时会在 `typecheck` 暴露不一致。

`STRICT_NO_EVIDENCE_REPLY` 是后端未进入 OpenAPI schema 的固定协议文案，因此集中在 shared 常量中供前端核对展示；修改时应同步 backend `app/constants.py`。

## 工作流与验收

1. 修改 `backend/app/schemas/` 或路由。
2. 在 `shared/` 执行 `npm run generate`。
3. 若新增 schema，在 `src/schema.ts` 补别名，并确认 `src/index.ts` 导出。
4. 执行 `npm run typecheck`。
5. 再修改 front 的 API 封装和页面；不在 front 定义平行 DTO。
6. 将 `openapi/openapi.json`、`generated/openapi.ts` 与源码一起提交。

shared 侧验收：

- Auth / Workspace / Source / Conversation / ModelProfile / SSE schema 均已生成。
- 三种来源输入与条件必填收窄类型可直接 import。
- 所有 Phase 2 路径可由 `ApiPaths` 构造，SSE 支持 accessToken 查询参数。
- `npm run generate` 可重复执行，`npm run typecheck` 通过。

## 常见问题

**Q: `PlainTextSourceCreate` 还在，是否代表仍是 MVP 契约？**  
A: 不是。它现在是 `SourceCreate` 的 `type: 'plain_text' + content: string` 收窄别名，用于表单；另有 `MarkdownSourceCreate`、`WebPageSourceCreate`。旧的 `PlainTextSourceUpdate` 仅作为迁移别名保留。

**Q: 为什么 OpenAPI 中 `SourceCreate.content` 和 `url` 是可选？**  
A: 后端用模型校验器按 `type` 判断条件必填。shared 的 `SourceCreateInput` 联合类型把这条规则反映到 TS，不替代服务端校验。

**Q: 为什么生成结果里没有 Chunk？**  
A: Chunk 和向量是入库内部模型，当前路由没有暴露对应 API。前端问答引用使用公开的 `Citation`。

**Q: generate 找不到 Python 或依赖报错？**  
A: 先准备 `backend/.venv`；或启动 backend 后执行 `npm run generate:from-url`。

**Q: generated/ 要不要提交？**  
A: 建议提交，便于 front 不执行脚本也能使用类型。后端契约变化后必须重新生成并一起提交。
