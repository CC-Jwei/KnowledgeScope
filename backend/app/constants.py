"""集中业务文案与固定标识（非环境变量亦可配置处）。"""

# 严格边界无检索证据时的固定回复，用在问答编排空检索短答
STRICT_NO_EVIDENCE_REPLY = "当前知识空间中未找到相关依据。"

# 严格模式系统提示，用在聊天模型仅依据片段作答
STRICT_SYSTEM_PROMPT = (
    "你是知域 KnowledgeScope 的助手。"
    "只能依据用户提供的「知识片段」回答问题；"
    "不得编造片段中不存在的事实。"
    "若片段不足以回答，请明确说明依据不足。"
)

# 脱敏占位前缀，用在 API Key 回读掩码
API_KEY_MASK_PREFIX = "****"

# Bearer 方案名，用在 OpenAPI security scheme
HTTP_BEARER_SCHEME_NAME = "bearerAuth"
