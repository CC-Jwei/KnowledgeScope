"""会话与问答契约模型。"""

from datetime import datetime

from pydantic import Field, field_validator

from app.config import get_settings
from app.schemas.common import CamelModel
from app.schemas.enums import MessageRole

# 会话标题相关配置，用在 Create 校验
_settings = get_settings()


class Citation(CamelModel):
    # 引用来源 id，用在助手消息与前端跳转
    source_id: str
    # 引用分块 id，用在精确定位
    chunk_id: str
    # 来源标题，用在引用展示
    title: str
    # 可选片段预览，用在引用卡片
    snippet: str | None = None


class Message(CamelModel):
    # 消息 id，用在会话详情列表
    id: str
    # 所属会话 id，用在归属
    conversation_id: str
    # 角色，用在气泡左右区分
    role: MessageRole
    # 正文，用在展示
    content: str
    # 引用列表，用在助手消息
    citations: list[Citation] = Field(default_factory=list)
    # 创建时间，用在排序
    created_at: datetime


class ConversationCreate(CamelModel):
    # 可选初始标题，用在 POST conversations
    title: str | None = Field(
        default=None,
        max_length=_settings.conversation_title_max_length,
        description="可选标题；空则首问后自动生成",
    )

    @field_validator("title")
    @classmethod
    # 规范化标题空白，用在创建会话
    def strip_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        # 去空白后的标题，用在空串转 None
        stripped = value.strip()
        return stripped or None


class Conversation(CamelModel):
    # 会话 id，用在列表与路径
    id: str
    # 所属空间 id，用在归属
    workspace_id: str
    # 所有者 id，用在归属
    owner_id: str
    # 标题，用在会话列表
    title: str | None
    # 创建时间，用在列表排序
    created_at: datetime
    # 更新时间，用在列表排序
    updated_at: datetime


class ConversationDetail(Conversation):
    # 消息列表，用在会话详情
    messages: list[Message] = Field(default_factory=list)


class AskMessageRequest(CamelModel):
    # 用户提问正文，用在 POST .../messages
    content: str = Field(min_length=1, max_length=_settings.content_max_length)
    # 可选聊天模型档 id，用在覆盖系统默认
    chat_model_profile_id: str | None = None
    # 可选嵌入模型档 id，用在检索覆盖默认
    embedding_model_profile_id: str | None = None

    @field_validator("content")
    @classmethod
    # 去掉提问首尾空白并拒绝空串，用在提问校验
    def strip_content(cls, value: str) -> str:
        # 去空白后的提问，用在非空校验
        stripped = value.strip()
        if not stripped:
            raise ValueError("提问内容不能为空")
        return stripped


class AskMessageResponse(CamelModel):
    # 写入的用户消息，用在前端追加气泡
    user_message: Message
    # 写入的助手消息（含引用），用在前端追加气泡
    assistant_message: Message
