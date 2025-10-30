import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the chat router from the file we just fixed
from .chat.chat_api import router as chat_router

# --- SETUP ---
app = FastAPI(title="Kanbanotion AI Assistant Backend")

# Configure CORS to allow your frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "null"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTERS ---
# Include your chat router with the /api prefix
app.include_router(chat_router, prefix="/api", tags=["chat"])

# --- HEALTH CHECK ---
@app.get("/health")
def health_check():
    """A simple endpoint to check if the server is running."""
    return {"status": "ok"}


# This part allows the server to be run directly
if __name__ == "__main__":
    print("🚀 Starting Kanbanotion AI Assistant server at http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
