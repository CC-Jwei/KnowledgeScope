# 贡献指南

感谢关注 **知域 KnowledgeScope**。当前仓库处于 MVP 阶段，欢迎提 Issue 与 PR。

## 开发约定

1. **契约真相源在后端**  
   改 API / 领域字段时，只改 `backend/app/schemas/`（及对应 ORM）。然后在 `shared/` 执行：

   ```powershell
   npm.cmd run generate
   ```

   再改 `front/` 调用处。禁止在前端手写与 OpenAPI 冲突的平行 DTO。

2. **提交信息**  
   使用 [Conventional Commits](https://www.conventionalcommits.org/)：`feat`、`fix`、`chore`、`docs`、`refactor`、`test`。

3. **后端常量**  
   Redis TTL、超时、分页默认值、固定业务标识等不要散落魔法字面量，集中到配置类或配置文件（见项目 Cursor 规则）。

4. **前端样式**  
   优先 Element Plus；布局与定制用 UnoCSS 原子类写在模板 `class` 上。可点击元素需有 hover 反馈。

## 本地跑通

按根目录 [`README.md`](README.md) 的「快速开始」分别启动 backend、生成 shared、启动 front。

子目录说明：

- [`backend/README.md`](backend/README.md)
- [`shared/README.md`](shared/README.md)
- [`front/README.md`](front/README.md)

## Pull Request

1. 从最新 `main` 拉分支，保持改动聚焦。
2. 说明动机与验证方式（可对照 [`docs/MVP业务说明.md`](docs/MVP业务说明.md) 验收要点）。
3. 若改动了 API 契约，确认已重新生成并提交 `shared/openapi/` 与 `shared/generated/`（如适用）。

## 行为准则

请保持友善、就事论事。恶意破坏、骚扰或不相关广告的 Issue / PR 将被关闭。
