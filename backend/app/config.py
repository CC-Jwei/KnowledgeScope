"""应用配置与业务常量。"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """可随运行环境变化的配置，支持环境变量与 .env。"""

    # pydantic-settings 读取方式，用在从 .env / 环境变量加载配置
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # OpenAPI 与应用标题，用在 FastAPI 应用元信息
    app_name: str = "KnowledgeScope"
    # 应用语义版本，用在 OpenAPI 文档 version 字段
    app_version: str = "0.1.0"
    # API 路由前缀，用在 main 挂载 api_router
    api_v1_prefix: str = "/api/v1"
    # SQLite 连接串，用在 database 创建引擎
    database_url: str = "sqlite:///./data/knowledgescope.db"
    # CORS 允许源（逗号分隔），用在 cors_origin_list 解析
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # SSE 心跳间隔秒数，用在 events 路由推送周期
    sse_heartbeat_interval_seconds: int = 15
    # 正文最大字符数，用在来源创建/更新校验
    content_max_length: int = 100_000
    # 标题最大字符数，用在来源创建/更新校验与截断
    title_max_length: int = 200
    # 列表预览截断长度，用在 source_service / chunk 预览
    content_preview_length: int = 120
    # 默认标题取正文前缀长度，用在未传标题时生成 title
    default_source_title_prefix_length: int = 30
    # 正文过短时的默认标题，用在未传标题且前缀为空的场景
    default_untitled_source_title: str = "未命名文本"

    # 空间名称最短长度，用在 WorkspaceCreate/Update 校验
    workspace_name_min_length: int = 1
    # 空间名称最长长度，用在 WorkspaceCreate/Update 校验
    workspace_name_max_length: int = 100
    # 空间描述最长长度，用在 WorkspaceCreate/Update 校验
    workspace_description_max_length: int = 500

    # JWT 签名密钥，用在签发与校验 Access Token（开发放 .env）
    jwt_secret_key: str = "dev-only-change-me-knowledgescope"
    # JWT 算法，用在 encode/decode
    jwt_algorithm: str = "HS256"
    # Access Token 有效期（分钟），用在登录签发
    jwt_access_token_expire_minutes: int = 1440
    # 密码哈希方案标识，用在 security 模块选型说明
    password_hash_scheme: str = "bcrypt"
    # 中国大陆手机号正则，用在注册/登录校验
    phone_regex: str = r"^1\d{10}$"
    # 手机号存储长度上限，用在 User 表与 schema
    phone_max_length: int = 11

    # 入库 worker 轮询间隔秒，用在后台任务 sleep
    ingest_worker_poll_interval_seconds: int = 2
    # 入库失败最大重试次数，用在 ingest worker
    ingest_max_retry: int = 3
    # 分块滑动窗口大小（字符），用在 chunking
    chunk_size_chars: int = 500
    # 分块窗口重叠（字符），用在 chunking
    chunk_overlap_chars: int = 80
    # 过短块丢弃阈值，用在 chunking
    chunk_min_chars: int = 20
    # failed 错误信息最长，用在写入 Source.error_message
    source_error_message_max_length: int = 2000

    # 网页抓取超时秒，用在 web_page 采集
    web_fetch_timeout_seconds: int = 15
    # 网页最大下载字节，用在 web_page 采集
    web_fetch_max_bytes: int = 2_097_152
    # 网页请求 UA，用在 web_page 采集
    web_fetch_user_agent: str = "KnowledgeScopeBot/0.1"
    # 允许的 URL scheme（逗号分隔），用在 web_page 校验
    web_fetch_allowed_schemes: str = "http,https"

    # 向量后端标识，用在 vector_store 选型
    vector_backend: str = "chroma"
    # Chroma 持久化目录，用在 vector_store 初始化
    vector_persist_directory: str = "./data/chroma"
    # Chroma 集合名，用在向量读写
    vector_collection_name: str = "knowledgescope_chunks"
    # 问答检索返回片段数，用在 retrieve
    retrieval_top_k: int = 8
    # 最低检索分数门槛，用在 retrieve 过滤（0 表示不过滤）
    retrieval_min_score: float = 0.0

    # 默认回答模式，用在问答编排
    answer_mode_default: str = "strict"
    # 交给聊天模型的最近消息条数，用在 ask
    chat_history_message_limit: int = 10
    # 生成上限 token，用在聊天 API 调用
    chat_max_output_tokens: int = 2048
    # 嵌入请求超时秒，用在 create_embeddings
    embedding_request_timeout_seconds: float = 60.0
    # 聊天请求超时秒，用在 create_chat_completion
    chat_request_timeout_seconds: float = 120.0
    # 上游模型调用最多尝试次数（含首次），用在 llm_client 重试
    llm_max_attempts: int = 3
    # 重试退避基数秒，用在两次尝试之间的等待
    llm_retry_backoff_seconds: float = 1.0
    # 单条助手消息最多引用数，用在 ask 截断 Citation
    citation_max_count: int = 8
    # 会话标题最长，用在 Conversation 校验
    conversation_title_max_length: int = 100
    # 未命名会话取首问前缀长度，用在自动标题
    conversation_title_from_question_prefix: int = 30

    # 系统默认聊天 Base URL，用在系统默认 ModelProfile
    default_chat_base_url: str = ""
    # 系统默认聊天 API Key，用在系统默认档调用
    default_chat_api_key: str = ""
    # 系统默认聊天模型名，用在系统默认档
    default_chat_model: str = ""
    # 系统默认嵌入 Base URL，用在系统默认 ModelProfile
    default_embedding_base_url: str = ""
    # 系统默认嵌入 API Key，用在嵌入调用
    default_embedding_api_key: str = ""
    # 系统默认嵌入模型名，用在嵌入调用
    default_embedding_model: str = ""
    # API Key 脱敏末尾可见位数，用在 model-profiles 列表
    model_api_key_mask_visible_suffix: int = 4
    # 用户模型档名称最长，用在 ModelProfile schema
    model_profile_name_max_length: int = 100
    # Base URL 最长，用在 ModelProfile schema
    model_base_url_max_length: int = 500

    # SSE Token 查询参数名，用在 EventSource 鉴权
    sse_access_token_query_param: str = "access_token"
    # 系统默认聊天档展示名，用在 model-profiles 列表
    system_default_chat_profile_name: str = "系统默认（聊天）"
    # 系统默认嵌入档展示名，用在 model-profiles 列表
    system_default_embedding_profile_name: str = "系统默认（嵌入）"
    # 系统默认聊天档虚拟 id，用在前端选择与解析
    system_default_chat_profile_id: str = "system-default-chat"
    # 系统默认嵌入档虚拟 id，用在前端选择与解析
    system_default_embedding_profile_id: str = "system-default-embedding"

    @property
    # 把 CORS 字符串拆成列表，用在 main 注册 CORSMiddleware
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    # 把允许的 URL scheme 拆成集合，用在 web_page 校验
    def web_fetch_allowed_scheme_set(self) -> set[str]:
        return {
            item.strip().lower()
            for item in self.web_fetch_allowed_schemes.split(",")
            if item.strip()
        }


@lru_cache
# 缓存并返回全局 Settings 单例，用在各模块读取配置
def get_settings() -> Settings:
    return Settings()
