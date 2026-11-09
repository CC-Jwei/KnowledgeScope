"""SQLAlchemy 自定义列类型。"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, TypeDecorator


class UTCDateTime(TypeDecorator):
    """存取均按 UTC；SQLite 读出无时区时补上 UTC。"""

    # 底层列类型，用在 SQLAlchemy 映射 created_at/updated_at
    impl = DateTime
    # 允许类型缓存，用在 SQLAlchemy 语句编译优化
    cache_ok = True

    # 写入前规范化为 UTC，用在 ORM flush/commit
    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    # 读出后补齐 UTC 时区，用在 ORM 查询结果与 API 序列化
    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
