# TypeScript and Python rule
_Exported on 11/9/2026 at 14:56:10 GMT+8 from Cursor (3.27.14)_

---

**User**

@.cursor/rules/ts-line-comments.mdc 重写该rule，现在要求ts、python都需要起作用。

---

**Cursor**

先读现有 rule 和写 rule 的技能说明，再按 TypeScript + Python 一起改写。

会把规则改成同时覆盖 TypeScript 与 Python，并改成更贴切的文件名。

已重写并更名为 `.cursor/rules/line-comments.mdc`（原 `ts-line-comments.mdc` 已删）。

主要变化：
- **作用范围**：`ts` / `tsx` / `vue` / `py`
- **注释符号**：TS/Vue 用 `//`，Python 用 `#`
- **格式不变**：用途 + 使用位置；`import` 与纯类型声明仍不用写

```text
docs(rules): 行级注释规则覆盖 TypeScript 与 Python

将 ts-line-comments 重写为 line-comments，globs 增加 .py，并补充 Python 示例。
```

