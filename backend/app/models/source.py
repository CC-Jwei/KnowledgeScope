"""来源 ORM。"""

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, String, Text
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
    # 所有者冗余，用在向量 metadata 与级联清理
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    # 来源类型字符串，用在入库规范化分支
    type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=SourceType.PLAIN_TEXT.value,
    )
    # 展示标题，用在列表与详情
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # 处理状态，用在轮询与检索过滤
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=SourceStatus.PENDING.value,
        index=True,
    )
    # 规范化后正文，用在分块；web_page 抓取前可为空串
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # 网页原始 URL，用在 web_page 类型
    source_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    # 失败原因，用在 status=failed 时展示
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 入库已尝试次数，用在 worker 重试上限
    ingest_attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
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
    # 级联分块，用在删除来源时清理业务库 Chunk
    chunks = relationship(
        "ChunkRecord",
        back_populates="source",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
