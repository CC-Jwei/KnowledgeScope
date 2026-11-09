"""SQLAlchemy ORM 模型。"""

from app.models.chunk import ChunkRecord
from app.models.conversation import ConversationRecord
from app.models.message import MessageRecord
from app.models.model_profile import ModelProfileRecord
from app.models.source import SourceRecord
from app.models.user import UserRecord
from app.models.workspace import WorkspaceRecord

# 对外导出的 ORM 符号，用在 database.init_db 导入注册表
__all__ = [
    "ChunkRecord",
    "ConversationRecord",
    "MessageRecord",
    "ModelProfileRecord",
    "SourceRecord",
    "UserRecord",
    "WorkspaceRecord",
]
