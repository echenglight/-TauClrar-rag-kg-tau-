from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_analysis import router as analysis_router
from app.api.routes_chat import router as chat_router
from app.api.routes_graph import router as graph_router
from app.api.routes_template import router as template_router
from app.core.config import settings

app = FastAPI(title=settings.app_name)

# 前后端分离开发阶段允许跨域，生产环境应限制来源。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "env": settings.app_env}


app.include_router(graph_router)
app.include_router(chat_router)
app.include_router(analysis_router)
app.include_router(template_router)
