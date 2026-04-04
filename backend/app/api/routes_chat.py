from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None
    source: str = "dify"
    top_k: int = 8
    temperature: float = 0.2


class ChatResponse(BaseModel):
    answer: str
    source: str
    session_id: str | None = None


@router.post("/ask", response_model=ChatResponse)
def ask(req: ChatRequest) -> ChatResponse:
    """对话接口占位，后续可接入 Dify 或本地推理服务。"""
    answer = (
        "### TauClear 后端对话占位\n"
        f"收到问题：{req.question}\n\n"
        "- 当前模式：Mock\n"
        "- 下一步：接入 Dify / 本地 LLM API\n"
        "- 建议：把图谱检索结果作为上下文注入 Prompt"
    )
    return ChatResponse(answer=answer, source=req.source, session_id=req.session_id)
