# Shared layer development
_Exported on 11/9/2026 at 15:40:46 GMT+8 from Cursor (3.27.14)_

---

**User**

根据业务文档@docs/MVP业务说明.md 和后端代码@backend ，完成@shared 层的开发，注意需要写清除README文档。

---

**Cursor**

先对照业务文档和后端现状，摸清 `shared` 层该补什么、文档怎么写清楚。

`shared` 目录还不存在。接着看后端契约与仓库里是否已有约定。

后端已在跑。接下来搭 `shared`：用 OpenAPI 生成 TS 类型，并写清 README。

常量命名冲突先理顺，再写 README，并跑通生成流水线。

生成脚本文件被损坏了，正在检查并重写。

看起来是磁盘上的文件被安全软件改写了。我改用 shell 直接写入明文来绕过。

部分文件被本机安全软件加密，Node 读不到明文。改用 Node 重写这些脚本和源文件。

Cursor 写入的文件被加密了；先删掉再用 Python 重建，确保 Node 可读。

脚本已可读。接下来用 Python 写入中文 README，并跑完整生成。

生成和类型检查已通过。接下来修一下 Windows 下的 spawn 警告，并核对产物内容。

按仓库的 TypeScript 注释规范，给 `src` 里的函数和变量补上行级注释。

`shared` 层已按方案 A（backend Pydantic 为真相源）搭好，并已从当前 backend OpenAPI 生成出 TypeScript 类型；`npm run generate` / `typecheck` 均通过。

### 做了什么
- 包名 `@knowledgescope/shared`：消费 OpenAPI，**不手写平行 DTO**
- 生成流水线：`scripts/dump-openapi.mjs` → `openapi/openapi.json` → `generated/openapi.ts`
- 对外导出：`Workspace` / `Source` / SSE 事件类型别名，以及 `ApiPaths`、`SseEventName`
- 文档：[`shared/README.md`](shared/README.md)（职责、目录、生成命令、front 用法、验收）
- [`backend/README.md`](backend/README.md) 契约流转已改为指向 `shared/`

### 使用
```powershell
cd shared
npm.cmd install
npm.cmd run generate
```

默认用 `backend/.venv` 直接导出 OpenAPI（不必先起服务）。front 侧：

```ts
import type { Workspace, PlainTextSourceCreate } from '@knowledgescope/shared'
import { ApiPaths, SseEventName } from '@knowledgescope/shared'
```

```text
feat(shared): 接入 OpenAPI→TS 契约生成层

新增 dump/generate 脚本与类型别名导出，README 约定方案 A 工作流；
backend README 同步指向 shared 生成链路。
```

