"""模型配置档契约模型。"""

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from app.config import get_settings
from app.schemas.common import CamelModel
from app.schemas.enums import ModelPurpose

# 模型档字段长度配置，用在 Create/Update 校验
_settings = get_settings()


class ModelProfileCreate(CamelModel):
    # 配置档名称，用在 POST /model-profiles
    name: str = Field(
        min_length=1,
        max_length=_settings.model_profile_name_max_length,
    )
    # 用途，用在区分聊天/嵌入
    purpose: ModelPurpose
    # OpenAI 兼容 Base URL，用在 HTTP 调用
    base_url: str = Field(min_length=1, max_length=_settings.model_base_url_max_length)
    # 模型名，用在请求 body
    model_name: str = Field(min_length=1, max_length=200)
    # API Key（只写），用在服务端保管
    api_key: str = Field(min_length=1, max_length=2000)

    @field_validator("name", "base_url", "model_name", "api_key")
    @classmethod
    # 去掉首尾空白并拒绝空串，用在创建校验
    def strip_required(cls, value: str) -> str:
        # 去空白后的字段值，用在非空校验
        stripped = value.strip()
        if not stripped:
            raise ValueError("字段不能为空")
        return stripped


class ModelProfileUpdate(CamelModel):
    # 可选新名称，用在 PATCH
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=_settings.model_profile_name_max_length,
    )
    # 可选新 Base URL，用在 PATCH
    base_url: str | None = Field(
        default=None,
        min_length=1,
        max_length=_settings.model_base_url_max_length,
    )
    # 可选新模型名，用在 PATCH
    model_name: str | None = Field(default=None, min_length=1, max_length=200)
    # 可选新 Key；不传则保留，用在 PATCH
    api_key: str | None = Field(default=None, min_length=1, max_length=2000)

    @field_validator("name", "base_url", "model_name", "api_key")
    @classmethod
    # 规范化可选字段空白，用在更新校验
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        # 去空白后的字段值，用在非空校验
        stripped = value.strip()
        if not stripped:
            raise ValueError("字段不能为空")
        return stripped

    @model_validator(mode="after")
    # 确保至少更新一项，用在 PATCH 空 body 拒绝
    def at_least_one_field(self) -> "ModelProfileUpdate":
        if not self.model_fields_set:
            raise ValueError("至少需要更新一项")
        return self


class ModelProfile(CamelModel):
    # 配置档 id（系统默认为虚拟 id），用在选择器
    id: str
    # 所有者；系统默认可为 null，用在展示
    owner_id: str | None = None
    # 展示名称，用在模型设置列表
    name: str
    # 用途，用在分组
    purpose: ModelPurpose
    # Base URL，用在展示与编辑回填
    base_url: str
    # 模型名，用在展示与编辑回填
    model_name: str
    # 脱敏后的 Key，用在列表展示（不可还原）
    api_key_masked: str
    # 是否系统默认，用在前端标注「默认」
    is_system_default: bool
    # 创建时间；系统默认可为 null
    created_at: datetime | None = None
    # 更新时间；系统默认可为 null
    updated_at: datetime | None = None
