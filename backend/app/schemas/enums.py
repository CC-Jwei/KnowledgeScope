"""领域枚举。"""

from enum import StrEnum


class SourceType(StrEnum):
    """来源类型。创建仅允许初期落地集。"""

    # 纯文字来源，用在创建与入库
    PLAIN_TEXT = "plain_text"
    # Markdown 来源，用在 Phase 2c 创建与入库
    MARKDOWN = "markdown"
    # 单页网页来源，用在 Phase 2c 采集与入库
    WEB_PAGE = "web_page"
    # 以下为后续预留，创建请求若出现 → 400
    VIDEO_URL = "video_url"
    IMAGE = "image"
    IMAGE_URL = "image_url"
    PDF = "pdf"
    WORD = "word"
    EXCEL = "excel"
    POWERPOINT = "powerpoint"


class SourceStatus(StrEnum):
    """来源处理状态。"""

    # 等待入库，用在创建后的初始状态
    PENDING = "pending"
    # 入库处理中，用在 worker 认领任务
    PROCESSING = "processing"
    # 可被检索，用在问答过滤
    READY = "ready"
    # 处理失败，用在展示 errorMessage
    FAILED = "failed"


class MessageRole(StrEnum):
    """会话消息角色。"""

    # 用户提问，用在 Message.role
    USER = "user"
    # 助手回答，用在 Message.role
    ASSISTANT = "assistant"
    # 系统消息（慎用），用在枚举预留
    SYSTEM = "system"


class ModelPurpose(StrEnum):
    """模型配置档用途。"""

    # 聊天生成，用在问答
    CHAT = "chat"
    # 向量嵌入，用在入库与检索
    EMBEDDING = "embedding"


# 初期允许创建的来源类型集合，用在 SourceCreate 校验
ALLOWED_SOURCE_TYPES_FOR_CREATE = frozenset(
    {
        SourceType.PLAIN_TEXT,
        SourceType.MARKDOWN,
        SourceType.WEB_PAGE,
    }
)
