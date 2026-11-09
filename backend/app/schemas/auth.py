"""认证相关契约模型。"""

import re
from datetime import datetime

from pydantic import Field, field_validator

from app.config import get_settings
from app.schemas.common import CamelModel

# 认证校验配置，用在手机号/密码字段边界
_settings = get_settings()


class RegisterRequest(CamelModel):
    # 注册手机号，用在 POST /auth/register
    phone: str = Field(max_length=_settings.phone_max_length, description="中国大陆手机号")
    # 注册密码，用在哈希后入库
    password: str = Field(min_length=6, max_length=128, description="登录密码")

    @field_validator("phone")
    @classmethod
    # 按 PHONE_REGEX 校验手机号，用在注册请求
    def validate_phone(cls, value: str) -> str:
        # 去空白后的手机号，用在正则匹配
        stripped = value.strip()
        if not re.fullmatch(_settings.phone_regex, stripped):
            raise ValueError("手机号格式不正确")
        return stripped


class LoginRequest(CamelModel):
    # 登录手机号，用在 POST /auth/login
    phone: str = Field(max_length=_settings.phone_max_length, description="中国大陆手机号")
    # 登录密码，用在校验哈希
    password: str = Field(min_length=1, max_length=128, description="登录密码")

    @field_validator("phone")
    @classmethod
    # 按 PHONE_REGEX 校验手机号，用在登录请求
    def validate_phone(cls, value: str) -> str:
        # 去空白后的手机号，用在正则匹配
        stripped = value.strip()
        if not re.fullmatch(_settings.phone_regex, stripped):
            raise ValueError("手机号格式不正确")
        return stripped


class TokenResponse(CamelModel):
    # JWT Access Token，用在前端 Authorization 头
    access_token: str
    # Token 类型，固定 bearer，用在 OpenAPI/客户端约定
    token_type: str = "bearer"


class UserPublic(CamelModel):
    # 用户 id，用在 /auth/me 与 ownerId 对照
    id: str
    # 手机号，用在个人资料展示
    phone: str
    # 注册时间，用在 /auth/me
    created_at: datetime
    # 更新时间，用在 /auth/me
    updated_at: datetime
