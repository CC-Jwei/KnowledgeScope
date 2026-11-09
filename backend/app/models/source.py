"""来源 ORM。"""

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import UTCDateTime
from app.schemas.enums import SourceStatus, SourceType


# 生成 UTC 当前时间，用在 SourceRecord 默认/更新时间戳
def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SourceRecord(Base):
    # 表名，用在 SQLite sources 表映射
    __tablename__ = "sources"

    # 来源主键 UUID，用在路径参数与详情查询
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # 所属空间 id，用在外键关联与按空间过滤
    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # 来源类型字符串，用在 MVP 固定 plain_text
    type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=SourceType.PLAIN_TEXT.value,
    )
    # 展示标题，用在列表与详情
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # 处理状态，用在 MVP 恒为 ready
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=SourceStatus.READY.value,
    )
    # 纯文字全文，用在详情接口与预览截断
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # 创建时间，用在列表排序与 API createdAt
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
    )
    # 最后更新时间，用在 API updatedAt
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    # 所属空间关系，用在 ORM 反向导航
    workspace = relationship("WorkspaceRecord", back_populates="sources")
