"""Chroma 向量库读写。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import get_settings

# 向量相关配置，用在集合名与路径
_settings = get_settings()


@lru_cache
# 懒加载 Chroma collection，用在 upsert/query/delete
def _get_collection():  # type: ignore[no-untyped-def]
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    # 持久化目录，用在 Client 初始化
    persist_dir = Path(_settings.vector_persist_directory)
    persist_dir.mkdir(parents=True, exist_ok=True)
    # Chroma 客户端，用在 get_or_create_collection
    client = chromadb.PersistentClient(
        path=str(persist_dir),
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(name=_settings.vector_collection_name)


# 写入或覆盖一批向量，用在入库成功后
def upsert_vectors(
    *,
    ids: list[str],
    embeddings: list[list[float]],
    documents: list[str],
    metadatas: list[dict[str, Any]],
) -> None:
    if not ids:
        return
    # Chroma 集合，用在 upsert
    collection = _get_collection()
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )


# 按 workspace 检索相似片段，用在严格边界问答
def query_vectors(
    *,
    embedding: list[float],
    workspace_id: str,
    top_k: int,
) -> list[dict[str, Any]]:
    # Chroma 集合，用在 query
    collection = _get_collection()
    # 检索原始结果，用在整理 hits
    raw = collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        where={"workspace_id": workspace_id},
        include=["documents", "metadatas", "distances"],
    )
    # 整理后的命中列表，用在检索服务
    hits: list[dict[str, Any]] = []
    # 命中 id 列表，用在与 metadata 对齐
    ids = (raw.get("ids") or [[]])[0]
    # 文档列表，用在回填 content
    documents = (raw.get("documents") or [[]])[0]
    # 元数据列表，用在 chunk/source/owner
    metadatas = (raw.get("metadatas") or [[]])[0]
    # 距离列表，用在换算分数
    distances = (raw.get("distances") or [[]])[0]
    for index, doc_id in enumerate(ids):
        # 单条距离，用在 score=1/(1+d)
        distance = float(distances[index]) if index < len(distances) else 0.0
        # 元数据字典，用在字段提取
        meta = metadatas[index] if index < len(metadatas) else {}
        hits.append(
            {
                "id": doc_id,
                "document": documents[index] if index < len(documents) else "",
                "metadata": meta,
                "score": 1.0 / (1.0 + distance),
            }
        )
    return hits


# 按来源 id 删除向量，用在删 Source
def delete_by_source_id(source_id: str) -> None:
    # Chroma 集合，用在 delete
    collection = _get_collection()
    try:
        collection.delete(where={"source_id": source_id})
    except Exception:
        # 集合为空或不存在 where 匹配时忽略，用在幂等清理
        return


# 按空间 id 删除向量，用在删 Workspace
def delete_by_workspace_id(workspace_id: str) -> None:
    # Chroma 集合，用在 delete
    collection = _get_collection()
    try:
        collection.delete(where={"workspace_id": workspace_id})
    except Exception:
        return
