"""模型配置档业务（系统默认 + 用户档）。"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.constants import API_KEY_MASK_PREFIX
from app.models.model_profile import ModelProfileRecord
from app.schemas.enums import ModelPurpose
from app.schemas.model_profile import ModelProfile, ModelProfileCreate, ModelProfileUpdate

# 模型相关配置，用在系统默认档与脱敏
_settings = get_settings()


@dataclass
# 可调用的模型连接信息，用在嵌入/聊天 HTTP
class ResolvedModel:
    # 展示用 id，用在日志与错误信息
    profile_id: str
    # Base URL，用在请求前缀
    base_url: str
    # 模型名，用在请求 body
    model_name: str
    # 完整 API Key，用在 Authorization（禁止回读给前端）
    api_key: str
    # 用途，用在校验
    purpose: ModelPurpose


# 返回当前 UTC 时间，用在创建/更新档时间戳
def _now() -> datetime:
    return datetime.now(timezone.utc)


# 对 API Key 脱敏，用在列表/详情回读
def mask_api_key(api_key: str) -> str:
    if not api_key:
        return API_KEY_MASK_PREFIX
    # 末尾可见长度，用在切片
    suffix_len = _settings.model_api_key_mask_visible_suffix
    if len(api_key) <= suffix_len:
        return API_KEY_MASK_PREFIX
    return f"{API_KEY_MASK_PREFIX}{api_key[-suffix_len:]}"


# 判断系统默认聊天是否已配置，用在列表与解析
def is_system_chat_configured() -> bool:
    return bool(
        _settings.default_chat_base_url
        and _settings.default_chat_api_key
        and _settings.default_chat_model
    )


# 判断系统默认嵌入是否已配置，用在列表与解析
def is_system_embedding_configured() -> bool:
    return bool(
        _settings.default_embedding_base_url
        and _settings.default_embedding_api_key
        and _settings.default_embedding_model
    )


# 组装系统默认聊天档（只读），用在 GET /model-profiles
def build_system_chat_profile() -> ModelProfile | None:
    if not is_system_chat_configured():
        return None
    return ModelProfile(
        id=_settings.system_default_chat_profile_id,
        owner_id=None,
        name=_settings.system_default_chat_profile_name,
        purpose=ModelPurpose.CHAT,
        base_url=_settings.default_chat_base_url,
        model_name=_settings.default_chat_model,
        api_key_masked=mask_api_key(_settings.default_chat_api_key),
        is_system_default=True,
        created_at=None,
        updated_at=None,
    )


# 组装系统默认嵌入档（只读），用在 GET /model-profiles
def build_system_embedding_profile() -> ModelProfile | None:
    if not is_system_embedding_configured():
        return None
    return ModelProfile(
        id=_settings.system_default_embedding_profile_id,
        owner_id=None,
        name=_settings.system_default_embedding_profile_name,
        purpose=ModelPurpose.EMBEDDING,
        base_url=_settings.default_embedding_base_url,
        model_name=_settings.default_embedding_model,
        api_key_masked=mask_api_key(_settings.default_embedding_api_key),
        is_system_default=True,
        created_at=None,
        updated_at=None,
    )


# ORM 转脱敏响应，用在用户档列表
def to_public(record: ModelProfileRecord) -> ModelProfile:
    return ModelProfile(
        id=record.id,
        owner_id=record.owner_id,
        name=record.name,
        purpose=ModelPurpose(record.purpose),
        base_url=record.base_url,
        model_name=record.model_name,
        api_key_masked=mask_api_key(record.api_key),
        is_system_default=False,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


# 列出系统默认 + 当前用户档，用在 GET /model-profiles
def list_profiles(db: Session, owner_id: str) -> list[ModelProfile]:
    # 结果列表，用在返回
    items: list[ModelProfile] = []
    # 系统聊天默认，用在列表头部标注默认
    chat_default = build_system_chat_profile()
    if chat_default is not None:
        items.append(chat_default)
    # 系统嵌入默认，用在列表头部标注默认
    embed_default = build_system_embedding_profile()
    if embed_default is not None:
        items.append(embed_default)
    # 用户档查询，用在追加个人配置
    stmt = (
        select(ModelProfileRecord)
        .where(ModelProfileRecord.owner_id == owner_id)
        .order_by(ModelProfileRecord.created_at.desc())
    )
    for record in db.scalars(stmt).all():
        items.append(to_public(record))
    return items


# 创建用户模型档，用在 POST /model-profiles
def create_profile(
    db: Session,
    owner_id: str,
    payload: ModelProfileCreate,
) -> ModelProfile:
    # 创建时刻，用在时间戳
    now = _now()
    # 待写入记录，用在 commit
    record = ModelProfileRecord(
        id=str(uuid.uuid4()),
        owner_id=owner_id,
        name=payload.name,
        purpose=payload.purpose.value,
        base_url=payload.base_url.rstrip("/"),
        model_name=payload.model_name,
        api_key=payload.api_key,
        is_system_default=False,
        created_at=now,
        updated_at=now,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return to_public(record)


# 按所有者取用户档，用在 PATCH/DELETE/解析
def get_owned_profile_or_404(
    db: Session,
    profile_id: str,
    owner_id: str,
) -> ModelProfileRecord:
    # 按主键查到的档，用在归属校验
    record = db.get(ModelProfileRecord, profile_id)
    if record is None or record.owner_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型配置档不存在",
        )
    return record


# 更新用户档（Key 不传则保留），用在 PATCH
def update_profile(
    db: Session,
    profile_id: str,
    owner_id: str,
    payload: ModelProfileUpdate,
) -> ModelProfile:
    # 待更新记录，用在写回字段
    record = get_owned_profile_or_404(db, profile_id, owner_id)
    if payload.name is not None:
        record.name = payload.name
    if payload.base_url is not None:
        record.base_url = payload.base_url.rstrip("/")
    if payload.model_name is not None:
        record.model_name = payload.model_name
    if payload.api_key is not None:
        record.api_key = payload.api_key
    record.updated_at = _now()
    db.commit()
    db.refresh(record)
    return to_public(record)


# 删除用户档（禁止删系统默认），用在 DELETE
def delete_profile(db: Session, profile_id: str, owner_id: str) -> None:
    if profile_id in {
        _settings.system_default_chat_profile_id,
        _settings.system_default_embedding_profile_id,
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不可删除系统默认配置档",
        )
    # 待删除记录，用在 db.delete
    record = get_owned_profile_or_404(db, profile_id, owner_id)
    db.delete(record)
    db.commit()


# 解析聊天或嵌入连接；缺省用系统默认，用在入库与问答
def resolve_model(
    db: Session,
    owner_id: str,
    purpose: ModelPurpose,
    profile_id: str | None,
) -> ResolvedModel:
    if profile_id is None:
        if purpose == ModelPurpose.CHAT:
            if not is_system_chat_configured():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="未配置系统默认聊天模型，请在设置中创建个人档或配置环境变量",
                )
            return ResolvedModel(
                profile_id=_settings.system_default_chat_profile_id,
                base_url=_settings.default_chat_base_url.rstrip("/"),
                model_name=_settings.default_chat_model,
                api_key=_settings.default_chat_api_key,
                purpose=ModelPurpose.CHAT,
            )
        if not is_system_embedding_configured():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未配置系统默认嵌入模型，请在设置中创建个人档或配置环境变量",
            )
        return ResolvedModel(
            profile_id=_settings.system_default_embedding_profile_id,
            base_url=_settings.default_embedding_base_url.rstrip("/"),
            model_name=_settings.default_embedding_model,
            api_key=_settings.default_embedding_api_key,
            purpose=ModelPurpose.EMBEDDING,
        )

    if profile_id == _settings.system_default_chat_profile_id:
        return resolve_model(db, owner_id, ModelPurpose.CHAT, None)
    if profile_id == _settings.system_default_embedding_profile_id:
        return resolve_model(db, owner_id, ModelPurpose.EMBEDDING, None)

    # 用户自建档，用在覆盖系统默认
    record = get_owned_profile_or_404(db, profile_id, owner_id)
    if record.purpose != purpose.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="模型配置档用途与请求不匹配",
        )
    return ResolvedModel(
        profile_id=record.id,
        base_url=record.base_url.rstrip("/"),
        model_name=record.model_name,
        api_key=record.api_key,
        purpose=purpose,
    )
