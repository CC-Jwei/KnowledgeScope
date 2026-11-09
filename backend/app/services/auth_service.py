"""注册与登录业务。"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import UserRecord
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserPublic
from app.security import create_access_token, hash_password, verify_password


# 返回当前 UTC 时间，用在用户时间戳
def _now() -> datetime:
    return datetime.now(timezone.utc)


# 注册新用户并签发 Token，用在 POST /auth/register
def register_user(db: Session, payload: RegisterRequest) -> TokenResponse:
    # 查重语句，用在判断手机号是否已注册
    existing = db.scalar(select(UserRecord).where(UserRecord.phone == payload.phone))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该手机号已注册",
        )
    # 创建时刻，用在 created_at/updated_at
    now = _now()
    # 待写入用户，用在 commit
    user = UserRecord(
        id=str(uuid.uuid4()),
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id))


# 校验手机号密码并签发 Token，用在 POST /auth/login
def login_user(db: Session, payload: LoginRequest) -> TokenResponse:
    # 按手机号查到的用户，用在密码校验
    user = db.scalar(select(UserRecord).where(UserRecord.phone == payload.phone))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误",
        )
    return TokenResponse(access_token=create_access_token(user.id))


# ORM 转公开用户信息，用在 GET /auth/me
def to_user_public(user: UserRecord) -> UserPublic:
    return UserPublic.model_validate(user)
