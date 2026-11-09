# 知域 KnowledgeScope — MVP 业务说明

> 本文档定义第一期「最小可跑通」范围，承接《项目初步预想》。  
> 契约策略采用 **方案 A：后端 Pydantic 为真相源**，由 FastAPI 产出 OpenAPI，前端据此生成 TypeScript 类型。

---

## 1. 目标与原则

### 1.1 MVP 目标

在本地可跑通一条最短闭环：

```text
创建知识空间 → 向空间投入纯文字来源 → 通过 SSE 维持连接心跳 → 管理空间与来源
```

验证三件事：

1. **知识空间**作为产品中心实体成立（不是以「聊天会话」为中心）。
2. **单一 SourceType** 能走完「创建 → 列表 → 详情 → 删除」链路，为后续多源管道留扩展位。
3. **SSE** 通道可用，后续 Agent 工作流事件可挂在同一机制上。

### 1.2 非目标（本期内明确不做）

| 不做 | 说明 |
|------|------|
| 多 SourceType | 网页、视频、图片、Office、Markdown 等延后 |
| 采集 / 解析 / Embedding / 向量库 | 不做 RAG 入库与问答 |
| 多 Agent 协作 | 不做规划、检索、核验等工作流 |
| 用户体系 / 权限 / 多成员 | 单机单用户即可；可不登录 |
| 站点爬取、ASR、OCR、VLM | 全部延后 |
| WebSocket | MVP 只用 SSE |
| 严格/边界优先/开放研究等回答模式 | 无问答能力时不需要 |

### 1.3 技术边界（与实现约定）

| 目录 | 职责 |
|------|------|
| `front/` | Vue 3 + TypeScript + Element Plus + UnoCSS；消费 OpenAPI 生成类型 |
| `backend/` | FastAPI + Pydantic；**领域模型与 API 契约的唯一真相源** |
| `shared/` | 不手写平行类型；放置生成脚本约定、生成产物路径说明，或前端生成的 TS 类型输出目录 |

**契约流转：**

```text
backend Pydantic 模型
    → FastAPI OpenAPI (/openapi.json)
    → 前端 codegen（如 openapi-typescript）
    → front 使用生成类型，禁止手写一份平行 DTO
```

改字段只改后端模型；前端重新生成类型后再改调用处。

---

## 2. 产品范围

### 2.1 功能清单

| 编号 | 能力 | 优先级 | 验收要点 |
|------|------|--------|----------|
| F1 | 知识空间 CRUD | P0 | 创建、列表、详情、更新、删除 |
| F2 | 纯文字来源 CRUD（挂在空间下） | P0 | 创建、列表、详情、删除；更新可选 |
| F3 | SSE 心跳 | P0 | 客户端可订阅；周期性 `heartbeat` 事件 |
| F4 | 基础前端页面 | P0 | 空间列表/详情；详情内投递与查看纯文字；SSE 连接状态展示 |

### 2.2 用户故事

1. **作为用户**，我可以创建一个知识空间并命名，以便后续把资料归入明确边界。
2. **作为用户**，我可以打开某个空间，粘贴一段纯文字并保存为来源。
3. **作为用户**，我可以查看、删除空间内的纯文字来源。
4. **作为用户**，我可以重命名或删除整个知识空间（删除时其下来源一并删除）。
5. **作为用户**，我能看到与后端的 SSE 连接是否存活（心跳），以便后续扩展实时任务流。

### 2.3 本期唯一 SourceType

```text
plain_text
```

对应预想文档中的「复制过来的纯文字」：保存原文、可选标题，不做摘要、分块、向量化。

---

## 3. 领域模型与数据定义

以下定义为 **业务契约**；实现时落成后端 Pydantic / ORM，字段名保持一致（JSON 使用 camelCase 或 snake_case 需在后端统一配置，**推荐 API JSON 使用 camelCase，Python 内部 snake_case**，由 Pydantic alias 转换）。

下文 JSON 示例统一 **camelCase**。

### 3.1 枚举

#### SourceType（本期仅开放一项）

| 值 | 含义 | MVP |
|----|------|-----|
| `plain_text` | 用户粘贴的纯文字 | ✅ |
| `web_page` | 网站链接 | ❌ |
| `video_url` | 视频链接 | ❌ |
| `image` / `image_url` | 图片 | ❌ |
| `markdown` | Markdown | ❌ |
| `pdf` / `word` / `excel` / `powerpoint` | Office | ❌ |

后端枚举可预先声明全部取值，但 API 校验：**创建来源时只允许** `plain_text`。

#### SourceStatus（为后续管道预留）

| 值 | 含义 | MVP 行为 |
|----|------|----------|
| `ready` | 可被后续检索使用 | 创建纯文字后直接置为 `ready` |
| `pending` | 等待处理 | 不用 |
| `processing` | 处理中 | 不用 |
| `failed` | 处理失败 | 不用 |

### 3.2 Workspace（知识空间）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | 服务端生成，建议 UUID |
| `name` | string | 是 | 1～100 字符，去首尾空白后非空 |
| `description` | string \| null | 否 | 最长 500 字符 |
| `createdAt` | string (ISO 8601) | 是 | 创建时间 |
| `updatedAt` | string (ISO 8601) | 是 | 最后更新时间 |
| `sourceCount` | number | 是 | 该空间下来源数量（列表/详情可带；删除来源后更新） |

**创建请求** `WorkspaceCreate`

| 字段 | 类型 | 必填 |
|------|------|------|
| `name` | string | 是 |
| `description` | string \| null | 否 |

**更新请求** `WorkspaceUpdate`

| 字段 | 类型 | 必填 |
|------|------|------|
| `name` | string | 否（至少改一项） |
| `description` | string \| null | 否 |

### 3.3 Source（来源）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | UUID |
| `workspaceId` | string | 是 | 所属知识空间 |
| `type` | SourceType | 是 | MVP 固定为 `plain_text` |
| `title` | string | 是 | 未传时可由服务端生成，如「未命名文本」或取正文前 30 字 |
| `status` | SourceStatus | 是 | MVP 恒为 `ready` |
| `createdAt` | string | 是 | |
| `updatedAt` | string | 是 | |
| `content` | string | 是 | 纯文字正文；创建时必填，最长建议 100_000 字符 |
| `contentPreview` | string | 是 | 列表用，正文截断（如前 120 字），详情可仍返回全文 |

列表接口可不返回完整 `content`，只返回 `contentPreview`，以控制载荷。

**创建请求** `PlainTextSourceCreate`

| 字段 | 类型 | 必填 |
|------|------|------|
| `title` | string \| null | 否 |
| `content` | string | 是，去首尾后非空 |

**更新请求（可选，P1）**`PlainTextSourceUpdate`

| 字段 | 类型 | 必填 |
|------|------|------|
| `title` | string | 否 |
| `content` | string | 否 |

### 3.4 通用响应包装（可选但建议）

若项目统一包装：

```json
{
  "code": 0,
  "message": "ok",
  "data": { }
}
```

错误时：

```json
{
  "code": 40401,
  "message": "知识空间不存在",
  "data": null
}
```

也可直接使用 FastAPI 默认 HTTP 状态码 + `{ "detail": "..." }`。**选定一种后全项目一致**；本文 API 示例按「HTTP 状态码 + JSON body 为资源本身或列表」描述，实现时可再套包装层。

### 3.5 列表分页（MVP 可简化）

MVP 允许不分页，一次返回全部（假设空间与来源数量很小）。

若预留分页：

| 字段 | 类型 | 说明 |
|------|------|------|
| `items` | T[] | 数据 |
| `total` | number | 总数 |
| `page` | number | 从 1 开始 |
| `pageSize` | number | 默认 20，最大 100 |

---

## 4. API 需求

Base path 建议：`/api/v1`

### 4.1 知识空间

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/workspaces` | 创建 |
| `GET` | `/workspaces` | 列表（含 `sourceCount`） |
| `GET` | `/workspaces/{workspaceId}` | 详情 |
| `PATCH` | `/workspaces/{workspaceId}` | 更新名称/描述 |
| `DELETE` | `/workspaces/{workspaceId}` | 删除空间及其下全部来源 |

**业务规则**

- 删除空间为级联删除来源；MVP 可不做软删除。
- `name` 在同一部署实例内可不强制唯一（允许重名）；若实现简单唯一约束亦可，需在文档与错误信息中写明。
- 不存在的 `workspaceId` → `404`。

### 4.2 来源（纯文字）

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/workspaces/{workspaceId}/sources` | 创建 `plain_text` 来源 |
| `GET` | `/workspaces/{workspaceId}/sources` | 列出该空间来源 |
| `GET` | `/workspaces/{workspaceId}/sources/{sourceId}` | 详情（含全文 `content`） |
| `DELETE` | `/workspaces/{workspaceId}/sources/{sourceId}` | 删除 |
| `PATCH` | `/workspaces/{workspaceId}/sources/{sourceId}` | 可选：改标题/正文 |

**业务规则**

- `type` 由服务端写入为 `plain_text`，客户端无需传；若传了且不为 `plain_text` → `400`。
- `content` 为空 → `400`。
- `sourceId` 不属于该 `workspaceId` → `404`。
- 创建/删除后，对应 Workspace 的 `sourceCount` 与 `updatedAt` 应反映变化。

### 4.3 SSE 心跳

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/events/heartbeat` | SSE 流；持续推送心跳 |

**建议事件**

| event | 周期 | data 示例 |
|-------|------|-----------|
| `heartbeat` | 每 15 秒（可配置） | `{"ts":"2026-11-09T06:00:00.000Z","serverTime":"..."}` |
| `connected` | 连接建立时一次 | `{"message":"connected"}` |

**行为要求**

- `Content-Type: text/event-stream`
- 禁用代理缓冲（如设置 `Cache-Control: no-cache`，必要时 `X-Accel-Buffering: no`）
- 客户端断开后服务端结束生成器，不泄漏任务
- MVP **不**要求鉴权；后续可改为按 `workspaceId` 订阅任务事件

**与后续扩展的关系**

心跳验证通道后，同一 SSE（或按 workspace 的 `/workspaces/{id}/events`）可扩展：

- `task_started` / `agent_started` / `source_found` 等（见预想文档第七章）

本期只保证 `connected` + `heartbeat`。

---

## 5. 前端页面需求（最小）

### 5.1 页面

| 页面 | 内容 |
|------|------|
| 空间列表 | 展示名称、描述摘要、来源数、创建时间；创建入口；删除确认 |
| 空间详情 | 展示基本信息；编辑名称/描述；纯文字投递表单；来源列表；进入来源详情或抽屉 |
| 全局/顶栏 | SSE 连接状态：连接中 / 已连接（显示最近心跳时间） / 断开 |

### 5.2 交互要点

- 删除空间、删除来源使用 Element Plus 确认框。
- 表单校验：空间名、正文非空。
- 列表空态有简短提示（如「暂无知识空间，先创建一个」）。
- 不要求精美动效；布局清晰即可。

### 5.3 类型使用

- 请求/响应类型来自 OpenAPI 生成结果。
- 禁止在 `front` 再维护一份与后端冲突的 Workspace/Source 接口定义（生成文件除外）。

---

## 6. 后端实现约束（业务向）

### 6.1 存储

MVP 可选其一，业务行为一致即可：

| 方案 | 说明 |
|------|------|
| A. SQLite + ORM | 便于后续演进，推荐 |
| B. 进程内内存 / JSON 文件 | 最快跑通，重启可丢数据需在 README 写明 |

无论哪种：Workspace 与 Source 的关联、级联删除语义必须满足第 4 节。

### 6.2 Pydantic 模型清单（真相源）

至少包含：

- `SourceType` / `SourceStatus` 枚举
- `Workspace` / `WorkspaceCreate` / `WorkspaceUpdate`
- `Source` / `PlainTextSourceCreate`（及可选 Update）
- `HeartbeatEvent` / `ConnectedEvent`（若事件 data 也建模）
- 列表包装类型（若使用分页）

这些模型应出现在 OpenAPI schema 中，供前端生成。

### 6.3 配置项（勿散落魔法值）

| 配置项 | 建议默认 | 说明 |
|--------|----------|------|
| SSE 心跳间隔秒数 | 15 | |
| 正文最大长度 | 100000 | |
| 标题最大长度 | 200 | |
| 列表预览长度 | 120 | |
| API 前缀 | `/api/v1` | |

---

## 7. 验收标准

### 7.1 功能验收

1. 可创建至少 2 个知识空间，列表可见且互不干扰。
2. 在空间 A 创建纯文字来源后，仅空间 A 的 `sourceCount` 增加；空间 B 不变。
3. 来源详情可看到完整正文；列表可见标题与预览。
4. 删除来源后计数减少；删除空间后其来源不可再访问。
5. 浏览器或前端页面打开 SSE 后，至少连续收到 2 次 `heartbeat`；断开网络或离开页面后服务端无异常堆积（抽查日志即可）。

### 7.2 契约验收

1. 访问 `/openapi.json`（或文档 UI）可见 Workspace、Source 相关 schema。
2. 前端类型由 OpenAPI 生成，核心字段与本文第 3 节一致。

### 7.3 明确不验收

- 问答准确率、向量检索、多 Agent、多文件格式解析。

---

## 8. 里程碑建议

| 顺序 | 交付 | 完成标志 |
|------|------|----------|
| M1 | backend 骨架 + Workspace CRUD | 用 HTTP 客户端打通 CRUD |
| M2 | Source `plain_text` CRUD | 挂在 workspace 下可读写 |
| M3 | SSE heartbeat | curl/`EventSource` 可见心跳 |
| M4 | front 三块页面 + 对接 API + 订阅 SSE | 浏览器内完成第 7.1 节 |
| M5 | OpenAPI → TS 生成接入 | 去掉前端手写 DTO |

---

## 9. 后续与预想文档的衔接

MVP 完成后，按预想文档优先级建议增量：

1. 增加 `web_page`：采集 → 正文 → 仍先落 Source，再引入分块。
2. 引入 Chunk + Embedding + 空间级检索。
3. 问答 + 引用；再引入回答模式（严格边界等）。
4. SSE 扩展为 Agent 任务事件流。
5. 其余 SourceType 与多 Agent 职责拆分。

每增加一种 SourceType 或一种 SSE event，**先改后端 Pydantic / OpenAPI，再生成前端类型**。

---

## 10. 附录：示例载荷

### 创建空间

```http
POST /api/v1/workspaces
Content-Type: application/json

{
  "name": "新能源汽车行业研究",
  "description": "竞品与政策资料"
}
```

```json
{
  "id": "ws_01",
  "name": "新能源汽车行业研究",
  "description": "竞品与政策资料",
  "createdAt": "2026-11-09T06:00:00.000Z",
  "updatedAt": "2026-11-09T06:00:00.000Z",
  "sourceCount": 0
}
```

### 创建纯文字来源

```http
POST /api/v1/workspaces/ws_01/sources
Content-Type: application/json

{
  "title": "会议临时记录",
  "content": "今天讨论了三家车企的固态电池进度……"
}
```

```json
{
  "id": "src_01",
  "workspaceId": "ws_01",
  "type": "plain_text",
  "title": "会议临时记录",
  "status": "ready",
  "content": "今天讨论了三家车企的固态电池进度……",
  "contentPreview": "今天讨论了三家车企的固态电池进度……",
  "createdAt": "2026-11-09T06:05:00.000Z",
  "updatedAt": "2026-11-09T06:05:00.000Z"
}
```

### SSE

```text
event: connected
data: {"message":"connected"}

event: heartbeat
data: {"ts":"2026-11-09T06:05:15.000Z"}

event: heartbeat
data: {"ts":"2026-11-09T06:05:30.000Z"}
```
