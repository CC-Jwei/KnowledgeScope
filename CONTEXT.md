# 知域 KnowledgeScope

面向多源异构内容的边界知识研究与协作平台：用户在明确知识边界内投递来源、归并知识，并基于证据问答。

## Language

### 身份与归属

**User（用户）**：
可登录系统的主体；拥有自己的知识空间与来源，彼此数据隔离。初期以**手机号 + 密码**标识与认证；手机号验证码登录为后续能力，不在初期验收。
_Avoid_: Account, 数据空间主人, Client；初期不要把「邮箱」当成唯一登录标识

**Owner（所有者）**：
对某个知识空间拥有完整控制权的用户。初期每个 Workspace 有且仅有一个 Owner；无成员协作。
_Avoid_: Admin（除非日后指平台管理员）, Member

### 知识边界

**Workspace（知识空间）**：
用户人为划定的一块知识边界，内含来源、索引与问答范围。问答必须选定一个 Workspace。
_Avoid_: 数据空间, Project, Folder, 知识库（口语可说，正式文档用 Workspace）

**KnowledgeScope（检索边界）**：
在一次问答中，对 Workspace 内可检索范围的进一步约束。初期仅强制 `workspaceId`（整空间）；来源级过滤后续再加。
_Avoid_: Filter 单独当产品名

### 内容

**Source（来源）**：
投入某 Workspace 的一条原始内容单元（纯文字、Markdown、网页等），经处理后可被检索。
_Avoid_: Document（易与文件混淆）, File（仅文件型来源的子集）

**SourceType**：
来源的种类。初期落地：`plain_text`、`markdown`、`web_page`（仅单页）。
_Avoid_: 把「站点整站爬取」叫成 web_page

**Chunk（分块）**：
将来源正文切成的、可嵌入与检索的文本片段，带上来源与位置等引用信息。
_Avoid_: Passage 与 Chunk 混用而不定义

### 问答

**AnswerMode（回答模式）**：
如何使用知识边界外的信息。初期仅 **严格边界（strict）**：无证据则明确说明找不到。
_Avoid_: 把「开放研究」当成初期默认

**Citation（引用）**：
回答中指向具体 Source / Chunk（及可选位置）的证据标记。
_Avoid_: Reference 与 Citation 不加区分地混用

**Conversation（会话）**：
某个 Workspace 下的一轮或多轮问答容器，归属该空间的 Owner。
_Avoid_: Chat（口语可说，模型与表名用 Conversation）, Thread 不加定义地混用

**Message（消息）**：
会话中的一条用户提问或助手回答；助手消息可携带 Citation 列表。
_Avoid_: Turn（除非明确等于一对问答）

### 模型配置

**ModelProfile（模型配置档）**：
一套可用于嵌入或聊天的模型连接信息（端点、模型名、用途等）。初期由服务端持久化；用户可在前端选择/管理自己的配置档。API Key 只写不完整回读（脱敏展示）。系统可提供**默认配置档**，前端须明确标注「默认」。
_Avoid_: 把「环境变量里的默认 Key」和「用户可切换的配置档」当成同一个概念不区分；禁止把完整 Key 存进浏览器作为正式方案

**IngestPipeline（入库管道）**：
Source 创建后的异步处理链：规范化正文 → 分块 → 嵌入 → 写入向量库 → 置为 ready/failed。
_Avoid_: 用「上传完成」表示已可检索

### 处理状态

**SourceStatus**：
来源在处理管道中的状态：`pending` → `processing` → `ready` | `failed`。仅 `ready` 进入检索。
_Avoid_: 用「已上传」代替 ready
