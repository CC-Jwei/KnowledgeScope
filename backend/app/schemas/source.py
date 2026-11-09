"""来源契约模型。"""

from datetime import datetime
from urllib.parse import urlparse

from pydantic import Field, field_validator, model_validator

from app.config import get_settings
from app.schemas.common import CamelModel
from app.schemas.enums import (
    ALLOWED_SOURCE_TYPES_FOR_CREATE,
    SourceStatus,
    SourceType,
)

# 标题/正文/URL 相关配置，用在 Create/Update 校验
_settings = get_settings()


class SourceCreate(CamelModel):
    # 来源类型，用在 POST sources；仅允许初期三种
    type: SourceType = Field(description="plain_text | markdown | web_page")
    # 可选标题，用在创建请求；空则服务端生成
    title: str | None = Field(
        default=None,
        max_length=_settings.title_max_length,
        description="可选标题；未传时由服务端生成",
    )
    # 正文；plain_text/markdown 必填，web_page 可空
    content: str | None = Field(
        default=None,
        max_length=_settings.content_max_length,
        description="纯文字或 Markdown 正文",
    )
    # 网页 URL；web_page 必填
    url: str | None = Field(
        default=None,
        max_length=2000,
        description="web_page 必填的 http(s) URL",
    )

    @field_validator("type")
    @classmethod
    # 限制创建类型为初期落地集，用在创建请求校验
    def allow_initial_types(cls, value: SourceType) -> SourceType:
        if value not in ALLOWED_SOURCE_TYPES_FOR_CREATE:
            raise ValueError("不支持的来源类型")
        return value

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
    # 规范化正文空白，用在创建请求校验
    def strip_content(cls, value: str | None) -> str | None:
        if value is None:
            return None
        # 去空白后的正文，用在后续必填判断
        stripped = value.strip()
        return stripped or None

    @field_validator("url")
    @classmethod
    # 规范化 URL 空白，用在 web_page 校验
    def strip_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        # 去空白后的 URL，用在 scheme 检查
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    # 按类型校验 content/url 必填与 scheme，用在创建请求
    def validate_by_type(self) -> "SourceCreate":
        if self.type in {SourceType.PLAIN_TEXT, SourceType.MARKDOWN}:
            if not self.content:
                raise ValueError("正文去首尾空白后不能为空")
        if self.type == SourceType.WEB_PAGE:
            if not self.url:
                raise ValueError("web_page 必须提供 url")
            # 解析后的 URL，用在 scheme 白名单校验
            parsed = urlparse(self.url)
            if parsed.scheme.lower() not in _settings.web_fetch_allowed_scheme_set:
                raise ValueError("仅支持 http/https URL")
            if not parsed.netloc:
                raise ValueError("URL 无效")
        return self


class SourceUpdate(CamelModel):
    # 可选新标题，用在 PATCH sources（入库后编辑）
    title: str | None = Field(
        default=None,
        max_length=_settings.title_max_length,
        description="标题",
    )
    # 可选新正文，用在 PATCH；改正文需重新入库由实现决定（本期允许改元数据为主）
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
    def at_least_one_field(self) -> "SourceUpdate":
        if self.title is None and self.content is None:
            raise ValueError("至少需要更新 title 或 content 中的一项")
        return self


class Source(CamelModel):
    # 来源 id，用在详情响应与路径参数
    id: str
    # 所属空间 id，用在响应归属展示
    workspace_id: str
    # 所有者 id，用在响应
    owner_id: str
    # 来源类型，用在表单与列表
    type: SourceType
    # 展示标题，用在列表与详情
    title: str
    # 处理状态，用在前端轮询
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
    # 网页 URL，用在 web_page 详情
    source_url: str | None = None
    # 失败原因，用在 status=failed
    error_message: str | None = None


class SourceListItem(CamelModel):
    """列表项：不含全文 content。"""

    # 来源 id，用在列表项点击进入详情
    id: str
    # 所属空间 id，用在列表归属
    workspace_id: str
    # 所有者 id，用在列表归属
    owner_id: str
    # 来源类型，用在列表展示
    type: SourceType
    # 展示标题，用在列表主文案
    title: str
    # 处理状态，用在列表状态徽标
    status: SourceStatus
    # 创建时间，用在列表排序与展示
    created_at: datetime
    # 更新时间，用在列表展示
    updated_at: datetime
    # 预览截断文本，用在列表摘要
    content_preview: str
    # 网页 URL，用在列表辅助信息
    source_url: str | None = None
    # 失败原因摘要，用在 failed 状态提示
    error_message: str | None = None
