"""删除时向量侧清理（先于业务行删除）。"""

from app.services import vector_store


# 删除某来源在向量库的全部向量，用在删 Source 前
def delete_vectors_for_source(source_id: str) -> None:
    vector_store.delete_by_source_id(source_id)


# 删除某空间在向量库的全部向量，用在删 Workspace 前
def delete_vectors_for_workspace(workspace_id: str) -> None:
    vector_store.delete_by_workspace_id(workspace_id)
