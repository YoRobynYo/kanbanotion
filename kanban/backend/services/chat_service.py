from typing import Dict, Set
from fastapi import WebSocket

class ChatManager:
    def __init__(self):
        self.active: Dict[int, Set[WebSocket]] = {}

    async def connect(self, thread_id: int, ws: WebSocket):
        await ws.accept()
        self.active.setdefault(thread_id, set()).add(ws)

    def disconnect(self, thread_id: int, ws: WebSocket):
        if thread_id in self.active and ws in self.active[thread_id]:
            self.active[thread_id].remove(ws)
            if not self.active[thread_id]:
                self.active.pop(thread_id, None)

    async def broadcast(self, thread_id: int, message: dict):
        for ws in list(self.active.get(thread_id, [])):
            await ws.send_json(message)

manager = ChatManager()
