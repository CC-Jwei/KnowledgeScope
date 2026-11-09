"""用户模型配置档 ORM。"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import UTCDateTime
from app.schemas.enums import ModelPurpose


# 生成 UTC 当前时间，用在 ModelProfileRecord 时间戳
def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ModelProfileRecord(Base):
    # 表名，用在 SQLite model_profiles 表映射
    __tablename__ = "model_profiles"

    # 配置档主键 UUID，用在问答可选 profileId
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # 所有者用户 id，用在列表隔离
    owner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # 展示名称，用在模型设置页
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # 用途 chat/embedding，用在解析默认档
    purpose: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ModelPurpose.CHAT.value,
    )
    # OpenAI 兼容 Base URL，用在 HTTP 调用
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    # 模型名，用在 API 请求 body
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    # API Key（服务端保管，回读脱敏），用在调用鉴权
    api_key: Mapped[str] = mapped_column(Text, nullable=False)
    # 是否系统默认（用户档恒 false），用在前端标注
    is_system_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # 创建时间，用在列表排序
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
    )
    # 更新时间，用在 PATCH 后刷新
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    # 所有者，用在 ORM 反向导航
    owner = relationship("UserRecord", back_populates="model_profiles")
