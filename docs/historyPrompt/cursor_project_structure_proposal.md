# Project structure proposal
_Exported on 11/9/2026 at 14:38:59 GMT+8 from Cursor (3.27.14)_

---

**User**

根据@docs/项目初步预想.md 文档，我想在项目中初始化一个项目，用于做一个，包含两个文件夹front、backend，分别对应前端、中间层类型定义、后端。前端使用vue3+ts，组件库使用element plus，样式使用UnoCSS；后端使用fastApi。考虑是否可行，并且再考虑是否可以加个中间层文件夹shared，用于存储数据类型，分别统一前后端的数据类型，这样前后端无需重复定义，但是前台是ts，后端是python。

---

**Cursor**

先读项目预想文档，再结合前后端技术栈评估可行性与 `shared` 类型层方案。

结论：**`front` + `backend` 完全可行**，也和文档里的 Vue 3 / FastAPI / SSE 路线一致；**加 `shared` 存「统一类型」可行，但不能指望同一份文件被 TS 和 Python 直接共用**，需要选定一份真相源，再生成另一端。

## 1. 目录方案是否可行

文档定位是：

```text
多源采集 → 解析 → RAG → 边界检索 → 多 Agent → 引用溯源
```

技术栈建议也是 Vue 3 + TypeScript + FastAPI + SSE/WebSocket。因此初始化成：

```text
knowledge-scope/          # 或你定的项目名
├── front/                # Vue3 + TS + Element Plus + UnoCSS
├── backend/              # FastAPI + Pydantic
└── shared/               # 契约层（推荐有，但角色要定清楚）
```

是合理且常见的 monorepo 拆法。

| 层 | 职责 | 和文档的对应 |
|---|---|---|
| `front` | 知识空间 UI、来源投递、Agent 任务链可视化、SSE 消费 | 产品交互面 |
| `backend` | 采集/解析、向量库、Agent 编排、SSE 事件流 | 文档第四～七章 |
| `shared` | API / 领域模型契约，而不是业务实现 | `SourceType`、`KnowledgeScope`、SSE event 等 |

你写的「两个文件夹分别对应前端、中间层类型、后端」里，**中间层类型更适合单独成 `shared`**，不要塞进 `front` 或 `backend` 之一，否则另一端仍会重复或漂移。

## 2. `shared` 统一类型：可行，但有语言墙

前端是 TS，后端是 Python，**不能**像同语言 monorepo 那样：

```ts
// front 直接 import shared 的 .ts —— 可以
import type { KnowledgeScope } from '@shared/types'
```

```python
# backend 直接 import 同一个 .ts —— 不行
from shared.types import KnowledgeScope  # 不存在这种用法
```

所以「一份定义、两端直接引用」在 TS↔Python 之间不成立；能成立的是：

**一份真相源（source of truth）→ 生成另一端类型**

文档里已经有典型契约，例如：

```137:149:docs/项目初步预想.md
type SourceType =
  | 'plain_text'
  | 'web_page'
  | 'video_url'
  // ...
```

```361:373:docs/项目初步预想.md
interface KnowledgeScope {
  workspaceId: string
  sourceIds?: string[]
  // ...
}
```

这些正适合放进契约层，而不是在前后端各抄一份。

## 3. 三种常见做法（按推荐顺序）

### 方案 A：后端 Pydantic 为真相源（最贴合 FastAPI）

1. 在 `backend` 用 Pydantic 定义模型（或从 `shared/openapi.yaml` 生成）
2. FastAPI 自动产出 OpenAPI
3. 前端用 `openapi-typescript` / `hey-api` 等生成 TS 类型与可选 client

优点：和 FastAPI 原生契合，接口一改前端类型跟着变。  
缺点：领域枚举若只写在 Python 里，前端开发早期要等后端先出模型，或先手写 stub。

适合本项目：API 多、SSE/WebSocket 事件多、领域模型以后端为准。

### 方案 B：`shared` 放 JSON Schema / OpenAPI，两端都生成

```text
shared/
  schemas/
    source-type.schema.json
    knowledge-scope.schema.json
    sse-events.schema.json
  openapi/          # 或最终合并成一份 openapi.yaml
```

- Python：`datamodel-code-generator` → Pydantic
- TS：`json-schema-to-typescript` / `openapi-typescript` → `.d.ts`

优点：真正「语言无关」的中间层；前后端可并行。  
缺点：要维护生成流水线（脚本 / CI），改 schema 后要记得 regenerate。

适合本项目：你明确想要一个独立的 `shared` 文件夹，且希望「契约先于实现」。

### 方案 C：`shared` 只放 TS，再 codegen 到 Python（不推荐作主路径）

可以，但生态弱于「OpenAPI → TS」。FastAPI 生态更顺的是 Python/OpenAPI 往外推，而不是 TS 往 Python 推。

## 4. 建议你怎么落

结合文档体量，推荐：

```text
project/
├── front/                 # Vue3 + TS + Element Plus + UnoCSS
├── backend/               # FastAPI
├── shared/
│   ├── openapi.yaml       # 或 schemas/*.json —— 契约真相源
│   ├── generated/         # 可选：提交生成物，或 CI 生成
│   │   ├── ts/
│   │   └── python/
│   └── README.md          # 约定：改契约后如何生成
├── package.json           # 可选：pnpm workspace 管 front + 生成脚本
└── README.md
```

实践建议：

1. **MVP 可先不做完整 codegen**：`shared` 先放 OpenAPI/JSON Schema 手写契约 + 两端手工对齐；核心模型稳定后再上生成。
2. **优先统一这些类型**（文档已点名）：`SourceType`、`KnowledgeScope`、Source/Chunk 元数据、SSE event 名与 payload、Agent step 状态。
3. **不要把运行时逻辑放进 `shared`**：爬虫、Embedding、Agent prompt 都留在 `backend`；UI 组件留在 `front`。
4. **枚举与常量用字符串字面量对齐**（如 `'plain_text'`），避免前后端各写一套魔法值。
5. **校验以服务端为准**：前端类型只保证开发期；边界、权限、workspaceId 过滤必须在 FastAPI/检索层强制（文档第五章也强调了这一点）。

## 5. 技术栈本身的可行性

| 选择 | 判断 |
|---|---|
| Vue3 + TS + Element Plus + UnoCSS | 可行；和本仓库其它前端习惯也一致 |
| FastAPI | 可行；异步任务、SSE、Pydantic、OpenAPI 都对口 |
| SSE 推 Agent 工作流 | 文档第七章设计合理，FastAPI `StreamingResponse` / sse-starlette 可做 |
| `shared` 统一类型 | 可行，但是「契约 + 生成」，不是「一份 TS 被 Python import」 |

需要注意的不是目录，而是业务复杂度：网页采集、视频 ASR、Office 分块、本地 RAG、多 Agent——**目录初始化简单，MVP 范围要收**（文档对视频站点也已建议先收窄）。

---

**一句话**：`front` / `backend` 可以开；`shared` 也建议加，但把它定位成 **OpenAPI/JSON Schema 契约层**，用生成打通 TS 与 Python，而不是共享同一份语言源码。

若你之后切到 Agent 模式，我可以按「最小可跑通：知识空间 CRUD + 一种 SourceType + SSE 心跳」帮你起目录骨架和契约约定。

---

**User**

根据刚刚的讨论结果，我选择方案A：后端 Pydantic 为真相源（最贴合 FastAPI）作为shared层的定义。请在@docs 写一份本项目MVP「最小可跑通：知识空间 CRUD + 一种 SourceType + SSE 心跳」的业务文档（包含需求、数据定义等）。

---

**Cursor**

先看 `docs` 现有文档风格与结构，再按方案 A 写 MVP 业务文档。

按方案 A 与 MVP 范围撰写业务文档，写入 `docs`。

已写入 [`docs/MVP业务说明.md`](docs/MVP业务说明.md)。

文档按方案 A 约定：**Pydantic → OpenAPI → 前端生成类型**；MVP 范围收成三条线——知识空间 CRUD、唯一 `plain_text` 来源、SSE `connected` + `heartbeat`。

主要内容包括：目标/非目标、领域字段与枚举、API 与业务规则、前端最小页面、后端存储与配置约束、验收标准、里程碑，以及示例载荷。后续 RAG / 多 SourceType / 多 Agent 明确列为衔接项，不进本期验收。

```text
docs(mvp): 补充知识空间 CRUD、plain_text 与 SSE 心跳的业务说明

约定后端 Pydantic 为契约真相源，明确 MVP 范围、数据模型、API 与验收标准。
```

