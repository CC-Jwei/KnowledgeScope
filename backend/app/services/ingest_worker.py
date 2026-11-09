"""入库后台 Worker：pending → processing → ready|failed。"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.models.chunk import ChunkRecord
from app.models.source import SourceRecord
from app.schemas.enums import ModelPurpose, SourceStatus, SourceType
from app.services import chunking, llm_client, model_profile_service, vector_cleanup, vector_store
from app.services.web_fetch import fetch_page_text_sync

# 入库相关配置，用在轮询间隔与重试
_settings = get_settings()
# 模块日志，用在 worker 异常记录（不打印 Key）
_logger = logging.getLogger(__name__)
# 后台任务句柄，用在 lifespan 启停
_worker_task: asyncio.Task | None = None
# 停止标志，用在优雅退出循环
_stop_event: asyncio.Event | None = None


# 返回当前 UTC 时间，用在状态时间戳
def _now() -> datetime:
    return datetime.now(timezone.utc)


# 截断错误信息，用在写入 error_message
def _trim_error(message: str) -> str:
    # 最大长度，用在切片
    max_len = _settings.source_error_message_max_length
    if len(message) <= max_len:
        return message
    return message[:max_len]


# 规范化来源正文（plain/md 原样；web 抓取），用在分块前
def _normalize_content(record: SourceRecord) -> str:
    if record.type == SourceType.WEB_PAGE.value:
        if not record.source_url:
            raise ValueError("web_page 缺少 url")
        return fetch_page_text_sync(record.source_url)
    # 已有正文，用在 plain_text / markdown
    content = (record.content or "").strip()
    if not content:
        raise ValueError("正文为空，无法入库")
    return content


# 处理单条 pending 来源，用在 worker 一轮认领
def _process_one(source_id: str) -> None:
    # 独立会话，用在后台任务与请求会话隔离
    db = SessionLocal()
    try:
        # 待处理来源，用在状态流转
        record = db.get(SourceRecord, source_id)
        if record is None or record.status != SourceStatus.PENDING.value:
            return
        record.status = SourceStatus.PROCESSING.value
        record.ingest_attempt_count += 1
        record.error_message = None
        record.updated_at = _now()
        db.commit()

        try:
            # 解析嵌入模型（系统默认或日后可扩展），用在向量化
            embed_model = model_profile_service.resolve_model(
                db,
                record.owner_id,
                ModelPurpose.EMBEDDING,
                None,
            )
            # 规范化正文，用在写回 content 与分块
            normalized = _normalize_content(record)
            record.content = normalized
            # 先清旧向量与旧块，用在重试场景幂等
            vector_cleanup.delete_vectors_for_source(record.id)
            for old in list(record.chunks):
                db.delete(old)
            db.flush()

            # 切分结果，用在写 Chunk 与嵌入
            pieces = chunking.split_text(normalized)
            if not pieces:
                raise ValueError("分块结果为空")

            # 待写入的 Chunk 列表，用在批量 add
            chunk_records: list[ChunkRecord] = []
            for ordinal, piece in enumerate(pieces):
                # 分块 id，同时作为向量 id
                chunk_id = str(uuid.uuid4())
                # 预览文本，用在 Citation
                preview = piece[: _settings.content_preview_length]
                chunk_records.append(
                    ChunkRecord(
                        id=chunk_id,
                        source_id=record.id,
                        workspace_id=record.workspace_id,
                        owner_id=record.owner_id,
                        ordinal=ordinal,
                        content=piece,
                        content_preview=preview,
                        vector_ref=chunk_id,
                        created_at=_now(),
                    )
                )
            db.add_all(chunk_records)
            db.flush()

            # 嵌入向量，用在 upsert Chroma
            embeddings = llm_client.create_embeddings(
                embed_model,
                [item.content for item in chunk_records],
            )
            if len(embeddings) != len(chunk_records):
                raise ValueError("嵌入结果数量与分块不一致")

            vector_store.upsert_vectors(
                ids=[item.id for item in chunk_records],
                embeddings=embeddings,
                documents=[item.content for item in chunk_records],
                metadatas=[
                    {
                        "chunk_id": item.id,
                        "source_id": record.id,
                        "workspace_id": record.workspace_id,
                        "owner_id": record.owner_id,
                    }
                    for item in chunk_records
                ],
            )

            record.status = SourceStatus.READY.value
            record.error_message = None
            record.updated_at = _now()
            db.commit()
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            # 重新加载后写失败态，用在前端展示原因
            record = db.get(SourceRecord, source_id)
            if record is None:
                return
            # 是否还可重试，用在回到 pending 或 failed
            can_retry = record.ingest_attempt_count < _settings.ingest_max_retry
            record.status = (
                SourceStatus.PENDING.value if can_retry else SourceStatus.FAILED.value
            )
            # 可读错误文案：HTTPException 取 detail，用在 errorMessage
            error_text = (
                str(exc.detail)
                if isinstance(exc, HTTPException)
                else str(exc)
            )
            record.error_message = _trim_error(error_text)
            record.updated_at = _now()
            db.commit()
            _logger.warning("ingest failed source=%s err=%s", source_id, error_text)
    finally:
        db.close()


# 认领一批 pending 并处理，用在 worker 循环每轮
def _claim_and_process_batch() -> int:
    # 独立会话，用在扫描 pending
    db = SessionLocal()
    try:
        # pending 查询，用在认领 id 列表
        stmt = (
            select(SourceRecord.id)
            .where(SourceRecord.status == SourceStatus.PENDING.value)
            .order_by(SourceRecord.created_at.asc())
            .limit(5)
        )
        # 本轮待处理 id，用在循环 process
        ids = list(db.scalars(stmt).all())
    finally:
        db.close()
    for source_id in ids:
        _process_one(source_id)
    return len(ids)


# 异步轮询循环，用在 lifespan 后台任务
async def _worker_loop(stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        try:
            await asyncio.to_thread(_claim_and_process_batch)
        except Exception:  # noqa: BLE001
            _logger.exception("ingest worker loop error")
        try:
            await asyncio.wait_for(
                stop_event.wait(),
                timeout=_settings.ingest_worker_poll_interval_seconds,
            )
        except asyncio.TimeoutError:
            continue


# 启动入库 worker，用在应用 lifespan 启动
def start_ingest_worker() -> None:
    global _worker_task, _stop_event
    if _worker_task is not None and not _worker_task.done():
        return
    _stop_event = asyncio.Event()
    _worker_task = asyncio.create_task(_worker_loop(_stop_event))


# 停止入库 worker，用在应用 lifespan 关闭
async def stop_ingest_worker() -> None:
    global _worker_task, _stop_event
    if _stop_event is not None:
        _stop_event.set()
    if _worker_task is not None:
        try:
            await asyncio.wait_for(_worker_task, timeout=5)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            _worker_task.cancel()
    _worker_task = None
    _stop_event = None
