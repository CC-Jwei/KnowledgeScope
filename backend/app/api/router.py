"""聚合 API v1 路由。"""

from fastapi import APIRouter

from app.api.routes import events, sources, workspaces

# v1 总路由，用在 main 以 api_v1_prefix 挂载
api_router = APIRouter()
api_router.include_router(workspaces.router, tags=["workspaces"])
api_router.include_router(sources.router, tags=["sources"])
api_router.include_router(events.router, tags=["events"])
