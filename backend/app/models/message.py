"""会话消息 ORM。"""

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import UTCDateTime
from app.schemas.enums import MessageRole


# 生成 UTC 当前时间，用在 MessageRecord.created_at
def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MessageRecord(Base):
    # 表名，用在 SQLite messages 表映射
    __tablename__ = "messages"

    # 消息主键 UUID，用在详情列表
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # 所属会话 id，用在外键与查询
    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # 角色 user/assistant/system，用在历史拼装
    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=MessageRole.USER.value,
    )
    # 消息正文，用在展示与模型上下文
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # 助手引用 JSON 字符串，用在 Citation 回读
    citations_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 创建时间，用在会话内排序
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
    )

    # 所属会话，用在 ORM 反向导航
    conversation = relationship("ConversationRecord", back_populates="messages")
