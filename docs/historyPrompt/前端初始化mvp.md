# Frontend development with documentation
_Exported on 11/9/2026 at 15:41:01 GMT+8 from Cursor (3.27.14)_

---

**Cursor**

先摸清文档、后端和 `shared` 契约，再按现有结构把 `front` 基础开发补齐并写好 README。

前端目录还是空的。接下来对照仓库里现有 Vue 项目和后端 API，按同一套栈把基础脚手架搭起来。

按 MVP 文档搭 Vue3 前端：对接 shared 契约，覆盖空间/来源 CRUD 和 SSE 状态。

开始创建前端脚手架与核心文件。

修正表单绑定，并继续补齐页面组件。

---

**User**

之前的任务异常中断，请继续执行

---

**Cursor**

接着把中断的前端安装和类型检查做完，先看当前目录状态。

依赖基本在，先跑类型检查，再补齐 `package-lock`。

前端 MVP 已续完：依赖装好，`typecheck` 与 `build` 均通过。

### 已交付（`front/`）
- **技术栈**：Vue 3 + TS + Element Plus + UnoCSS + Vue Router  
- **契约**：通过别名引用 `@knowledgescope/shared`（类型 + `ApiPaths` + SSE 常量），不手写平行 DTO  
- **页面**：空间列表 `/`、空间详情 `/workspaces/:id`（投递/列表/抽屉详情与编辑）  
- **SSE**：顶栏连接状态（连接中 / 已连接+最近心跳 / 断开可重连）  
- **文档**：[`front/README.md`](front/README.md)（启动、代理、契约约定、验收）

### 本地启动
```powershell
# 终端 1
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 终端 2
cd front
npm.cmd run dev
```
打开 `http://127.0.0.1:5173`（开发态 `/api` 代理到 `8000`）。

```text
feat(front): 完成 KnowledgeScope MVP 前端基础页与 shared 契约对接

接入空间/来源 CRUD、SSE 顶栏状态与 Vite 代理，并补充 front README。
```

