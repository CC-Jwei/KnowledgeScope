"""用户 ORM。"""

from datetime import datetime, timezone

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import UTCDateTime


# 生成 UTC 当前时间，用在 UserRecord 时间戳默认值
def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserRecord(Base):
    # 表名，用在 SQLite users 表映射
    __tablename__ = "users"

    # 用户主键 UUID，用在 JWT sub 与 owner_id
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # 手机号（唯一），用在注册登录标识
    phone: Mapped[str] = mapped_column(String(11), nullable=False, unique=True, index=True)
    # 密码哈希，用在登录校验（禁止明文）
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # 创建时间，用在 API createdAt
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
    )
    # 更新时间，用在 API updatedAt
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    # 名下知识空间，用在级联关系
    workspaces = relationship("WorkspaceRecord", back_populates="owner")
    # 名下模型配置档，用在级联关系
    model_profiles = relationship("ModelProfileRecord", back_populates="owner")
