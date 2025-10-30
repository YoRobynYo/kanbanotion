from fastapi import APIRouter
from ..schemas import AIMessage
from ..services.ai_svc import assistant_reply

router = APIRouter()

@router.post("/ai/assist")
async def ai_assist(msg: AIMessage):
    reply = await assistant_reply(msg.message, user_email=msg.user_email)
    return {"reply": reply}
