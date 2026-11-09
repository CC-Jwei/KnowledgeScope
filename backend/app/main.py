"""FastAPI 应用入口。"""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.api.router import api_router
from app.config import get_settings
from app.database import init_db
from app.schemas.events import ConnectedEvent, HeartbeatEvent


@asynccontextmanager
# 应用生命周期钩子：启动建表，用在 FastAPI lifespan
async def lifespan(_app: FastAPI):
    init_db()
    yield


# 把 Pydantic 模型写入 OpenAPI components.schemas，用在暴露 SSE 事件契约
def _merge_model_schema(components_schemas: dict[str, Any], model: type) -> None:
    # 当前模型的 JSON Schema，用在合并进 OpenAPI
    schema = model.model_json_schema(
        by_alias=True,
        ref_template="#/components/schemas/{model}",
    )
    # 嵌套 $defs 定义，用在一并写入 components.schemas
    nested = schema.pop("$defs", {})
    for name, definition in nested.items():
        components_schemas.setdefault(name, definition)
    components_schemas[model.__name__] = schema


# 组装 FastAPI 应用（CORS、路由、OpenAPI），用在模块导出与 uvicorn 启动
def create_app() -> FastAPI:
    # 运行时配置，用在应用标题、前缀与 CORS
    settings = get_settings()
    # FastAPI 实例，用在挂载中间件与路由后返回
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "知域 KnowledgeScope MVP API。"
            "契约以本服务 Pydantic 模型为真相源；"
            "请使用 /docs 或 /openapi.json 供前端生成类型。"
        ),
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router, prefix=settings.api_v1_prefix)

    @application.get("/health", tags=["system"], summary="健康检查")
    # 进程存活探测，用在运维探活与本地自检
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # 自定义 OpenAPI：附带 SSE 事件 schema，用在 /openapi.json 与 /docs
    def custom_openapi() -> dict[str, Any]:
        if application.openapi_schema:
            return application.openapi_schema
        # 基础 OpenAPI 文档，用在继续挂入 Connected/Heartbeat schema
        openapi_schema = get_openapi(
            title=application.title,
            version=application.version,
            description=application.description,
            routes=application.routes,
        )
        # components 节点，用在写入 schemas
        components = openapi_schema.setdefault("components", {})
        # schemas 字典，用在前端 codegen 读取模型
        schemas = components.setdefault("schemas", {})
        # SSE 事件 data 不走 response_model，需显式挂入契约
        _merge_model_schema(schemas, ConnectedEvent)
        _merge_model_schema(schemas, HeartbeatEvent)
        application.openapi_schema = openapi_schema
        return application.openapi_schema

    application.openapi = custom_openapi
    return application


# ASGI 入口应用实例，用在 uvicorn app.main:app
app = create_app()
