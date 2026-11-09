"""知识空间 ORM。"""

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import UTCDateTime


# 生成 UTC 当前时间，用在 WorkspaceRecord 默认/更新时间戳
def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WorkspaceRecord(Base):
    # 表名，用在 SQLite workspaces 表映射
    __tablename__ = "workspaces"

    # 空间主键 UUID，用在路径参数与外键关联
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # 所有者用户 id，用在 Owner 隔离校验
    owner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # 空间显示名称，用在列表与详情展示
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # 可选描述，用在详情展示与编辑
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 创建时间，用在列表排序与 API createdAt
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
    )
    # 最后更新时间，用在 API updatedAt 与来源变更同步
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    # 下来源数量缓存，用在列表/详情 sourceCount
    source_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # 所有者用户，用在 ORM 反向导航
    owner = relationship("UserRecord", back_populates="workspaces")
    # 级联来源集合，用在删除空间时一并删除来源
    sources = relationship(
        "SourceRecord",
        back_populates="workspace",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    # 级联会话集合，用在删除空间时一并删除会话
    conversations = relationship(
        "ConversationRecord",
        back_populates="workspace",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
