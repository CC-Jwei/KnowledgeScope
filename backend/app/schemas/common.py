"""Pydantic 通用配置：API JSON 使用 camelCase。"""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Python 字段 snake_case，序列化/文档使用 camelCase。"""

    # 别名与 ORM 映射配置，用在所有 API 契约模型基类
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
