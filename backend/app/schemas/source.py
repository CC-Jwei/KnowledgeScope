"""来源契约模型。"""

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from app.config import get_settings
from app.schemas.common import CamelModel
from app.schemas.enums import SourceStatus, SourceType

# 标题/正文长度配置，用在 Create/Update 校验边界
_settings = get_settings()


class PlainTextSourceCreate(CamelModel):
    # 可选标题，用在 POST sources 请求体；空则服务端生成
    title: str | None = Field(
        default=None,
        max_length=_settings.title_max_length,
        description="可选标题；未传时由服务端生成",
    )
    # 纯文字正文，用在 POST sources 请求体
    content: str = Field(
        min_length=1,
        max_length=_settings.content_max_length,
        description="纯文字正文",
    )
    # 可选类型声明，用在校验仅允许 plain_text
    type: SourceType | None = Field(
        default=None,
        description="可选；若传入必须为 plain_text",
    )

    @field_validator("title")
    @classmethod
    # 规范化标题空白，用在创建请求校验
    def strip_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        # 去空白后的标题，用在空串转 None
        stripped = value.strip()
        return stripped or None

    @field_validator("content")
    @classmethod
    # 去掉正文首尾空白并拒绝空串，用在创建请求校验
    def strip_content(cls, value: str) -> str:
        # 去空白后的正文，用在非空校验与回写
        stripped = value.strip()
        if not stripped:
            raise ValueError("正文去首尾空白后不能为空")
        return stripped

    @field_validator("type")
    @classmethod
    # 限制创建类型仅为 plain_text，用在 MVP 契约校验
    def only_plain_text(cls, value: SourceType | None) -> SourceType | None:
        if value is not None and value != SourceType.PLAIN_TEXT:
            raise ValueError("MVP 仅支持 plain_text")
        return value


class PlainTextSourceUpdate(CamelModel):
    # 可选新标题，用在 PATCH sources 请求体
    title: str | None = Field(
        default=None,
        max_length=_settings.title_max_length,
        description="标题",
    )
    # 可选新正文，用在 PATCH sources 请求体
    content: str | None = Field(
        default=None,
        min_length=1,
        max_length=_settings.content_max_length,
        description="纯文字正文",
    )

    @field_validator("title")
    @classmethod
    # 去掉标题首尾空白并拒绝空串，用在更新请求校验
    def strip_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        # 去空白后的标题，用在非空校验与回写
        stripped = value.strip()
        if not stripped:
            raise ValueError("标题去首尾空白后不能为空")
        return stripped

    @field_validator("content")
    @classmethod
    # 去掉正文首尾空白并拒绝空串，用在更新请求校验
    def strip_content(cls, value: str | None) -> str | None:
        if value is None:
            return None
        # 去空白后的正文，用在非空校验与回写
        stripped = value.strip()
        if not stripped:
            raise ValueError("正文去首尾空白后不能为空")
        return stripped

    @model_validator(mode="after")
    # 确保至少更新一项，用在 PATCH 空 body 拒绝
    def at_least_one_field(self) -> "PlainTextSourceUpdate":
        if self.title is None and self.content is None:
            raise ValueError("至少需要更新 title 或 content 中的一项")
        return self


class Source(CamelModel):
    # 来源 id，用在详情响应与路径参数
    id: str
    # 所属空间 id，用在响应归属展示
    workspace_id: str
    # 来源类型，用在响应与后续多源扩展
    type: SourceType
    # 展示标题，用在列表与详情
    title: str
    # 处理状态，用在响应展示
    status: SourceStatus
    # 创建时间，用在列表排序与展示
    created_at: datetime
    # 更新时间，用在详情展示
    updated_at: datetime
    # 全文正文，用在详情接口；列表通常省略
    content: str | None = Field(
        default=None,
        description="全文；列表接口通常省略",
    )
    # 预览截断文本，用在列表与详情预览
    content_preview: str = Field(description="列表预览截断文本")


class SourceListItem(CamelModel):
    """列表项：不含全文 content。"""

    # 来源 id，用在列表项点击进入详情
    id: str
    # 所属空间 id，用在列表归属
    workspace_id: str
    # 来源类型，用在列表展示
    type: SourceType
    # 展示标题，用在列表主文案
    title: str
    # 处理状态，用在列表展示
    status: SourceStatus
    # 创建时间，用在列表排序与展示
    created_at: datetime
    # 更新时间，用在列表展示
    updated_at: datetime
    # 预览截断文本，用在列表摘要
    content_preview: str
