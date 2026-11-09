"""会话 ORM。"""

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import UTCDateTime


# 生成 UTC 当前时间，用在 ConversationRecord 时间戳
def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ConversationRecord(Base):
    # 表名，用在 SQLite conversations 表映射
    __tablename__ = "conversations"

    # 会话主键 UUID，用在路径参数
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # 所属空间 id，用在列表过滤与归属
    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # 所有者 id，用在越权校验
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    # 会话标题，用在列表展示；可空后由首问生成
    title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 创建时间，用在列表排序
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
    )
    # 更新时间，用在发消息后刷新
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    # 所属空间，用在 ORM 反向导航
    workspace = relationship("WorkspaceRecord", back_populates="conversations")
    # 级联消息，用在删除会话时清理 Message
    messages = relationship(
        "MessageRecord",
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="MessageRecord.created_at",
    )
