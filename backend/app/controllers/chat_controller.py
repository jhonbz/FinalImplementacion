from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from app.models.database import Conversation, get_db
from app.core.security import get_current_user
from app.agents.graph import run_agent
import json

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    has_context: bool


@router.post("/", response_model=ChatResponse)
async def chat(
    data: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not data.question.strip():
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía.")

    user_id = int(current_user["sub"])

    # Ejecutar el agente LangGraph
    result = await run_agent(question=data.question, user_id=user_id)

    # Guardar en historial (Nodo 6 del grafo)
    conversation = Conversation(
        user_id=user_id,
        question=data.question,
        answer=result["answer"],
        sources=json.dumps(result["sources"]),
    )
    db.add(conversation)
    await db.commit()

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        has_context=result["has_context"],
    )


@router.get("/history")
async def get_history(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
):
    user_id = int(current_user["sub"])
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(desc(Conversation.created_at))
        .limit(limit)
    )
    conversations = result.scalars().all()

    return [
        {
            "id": c.id,
            "question": c.question,
            "answer": c.answer,
            "sources": json.loads(c.sources) if c.sources else [],
            "created_at": c.created_at.isoformat(),
        }
        for c in conversations
    ]
