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
    # 列表预览截断长度，用在 source_service 生成 contentPreview
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

    @property
    # 把 CORS 字符串拆成列表，用在 main 注册 CORSMiddleware
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
# 缓存并返回全局 Settings 单例，用在各模块读取配置
def get_settings() -> Settings:
    return Settings()
