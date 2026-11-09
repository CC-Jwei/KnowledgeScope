"""分块 ORM（业务元数据；向量在 Chroma）。"""

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import UTCDateTime


# 生成 UTC 当前时间，用在 ChunkRecord.created_at
def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ChunkRecord(Base):
    # 表名，用在 SQLite chunks 表映射
    __tablename__ = "chunks"

    # 分块主键 UUID，用在 Citation.chunkId 与向量 metadata
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # 所属来源 id，用在级联删除与引用
    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # 所属空间 id（冗余），用在检索过滤
    workspace_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    # 所有者 id（冗余），用在向量 metadata
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    # 来源内序号，用在展示顺序
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    # 块全文，用在嵌入与引用预览源
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # 短预览，用在 Citation 可选片段
    content_preview: Mapped[str] = mapped_column(String(500), nullable=False)
    # 向量侧 id，用在 Chroma 文档 id 对齐
    vector_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # 创建时间，用在审计
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
    )

    # 所属来源，用在 ORM 反向导航
    source = relationship("SourceRecord", back_populates="chunks")
