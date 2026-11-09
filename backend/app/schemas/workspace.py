"""知识空间契约模型。"""

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from app.config import get_settings
from app.schemas.common import CamelModel

# 空间字段长度等配置，用在 Create/Update 校验边界
_settings = get_settings()


class WorkspaceCreate(CamelModel):
    # 新建空间名称，用在 POST /workspaces 请求体
    name: str = Field(
        min_length=_settings.workspace_name_min_length,
        max_length=_settings.workspace_name_max_length,
        description="知识空间名称",
    )
    # 可选描述，用在 POST /workspaces 请求体
    description: str | None = Field(
        default=None,
        max_length=_settings.workspace_description_max_length,
        description="可选描述",
    )

    @field_validator("name")
    @classmethod
    # 去掉名称首尾空白并拒绝空串，用在创建请求校验
    def strip_name(cls, value: str) -> str:
        # 去空白后的名称，用在非空校验与回写
        stripped = value.strip()
        if not stripped:
            raise ValueError("名称去首尾空白后不能为空")
        return stripped

    @field_validator("description")
    @classmethod
    # 规范化描述空白，用在创建请求校验
    def strip_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        # 去空白后的描述，用在空串转 None
        stripped = value.strip()
        return stripped or None


class WorkspaceUpdate(CamelModel):
    # 可选新名称，用在 PATCH /workspaces/{id} 请求体
    name: str | None = Field(
        default=None,
        min_length=_settings.workspace_name_min_length,
        max_length=_settings.workspace_name_max_length,
        description="知识空间名称",
    )
    # 可选新描述（显式 null 可清空），用在 PATCH 请求体
    description: str | None = Field(
        default=None,
        max_length=_settings.workspace_description_max_length,
        description="可选描述；传 null 可清空",
    )

    @field_validator("name")
    @classmethod
    # 去掉名称首尾空白并拒绝空串，用在更新请求校验
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        # 去空白后的名称，用在非空校验与回写
        stripped = value.strip()
        if not stripped:
            raise ValueError("名称去首尾空白后不能为空")
        return stripped

    @field_validator("description")
    @classmethod
    # 规范化描述空白，用在更新请求校验
    def strip_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        # 去空白后的描述，用在空串转 None
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    # 确保至少更新一项，用在 PATCH 空 body 拒绝
    def at_least_one_field(self) -> "WorkspaceUpdate":
        if self.name is None and "description" not in self.model_fields_set:
            raise ValueError("至少需要更新 name 或 description 中的一项")
        return self


class Workspace(CamelModel):
    # 空间 id，用在列表/详情响应与路径参数
    id: str
    # 所有者用户 id，用在前端归属展示
    owner_id: str
    # 空间名称，用在列表与详情展示
    name: str
    # 空间描述，用在详情展示
    description: str | None
    # 创建时间，用在列表排序与展示
    created_at: datetime
    # 更新时间，用在详情展示
    updated_at: datetime
    # 下来源数量，用在列表卡片与详情头
    source_count: int = Field(description="该空间下来源数量")
