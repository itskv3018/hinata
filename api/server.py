# api/server.py
# FastAPI server with WebSocket support — connects mobile app to Hinata.

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import Config
from core.agent import HinataAgent
from utils.logger import get_logger

log = get_logger("api")

# Global agent instance
agent: HinataAgent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the agent on startup."""
    global agent
    log.info("🌸 Starting Hinata API server...")
    agent = HinataAgent()
    yield
    log.info("🌸 Hinata API server stopped")


app = FastAPI(
    title="Hinata AI Agent",
    description="Your personal AI assistant that controls your devices",
    version=Config.AGENT_VERSION,
    lifespan=lifespan,
)

# CORS — allow mobile app connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Request/Response Models ----------

class ChatRequest(BaseModel):
    message: str
    user_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    user_id: str


class PluginRequest(BaseModel):
    plugin: str
    action: str
    params: dict = {}


# ---------- REST Endpoints ----------

@app.get("/")
async def root():
    return {
        "name": Config.AGENT_NAME,
        "version": Config.AGENT_VERSION,
        "status": "running",
        "message": f"🌸 {Config.AGENT_NAME} is ready!",
    }


@app.get("/health")
async def health():
    return agent.get_status() if agent else {"status": "initializing"}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Send a message to Hinata and get a response."""
    if not agent:
        raise HTTPException(503, "Agent not ready")

    response = await agent.process(req.message, req.user_id)
    return ChatResponse(response=response, user_id=req.user_id)


@app.post("/plugin")
async def execute_plugin(req: PluginRequest):
    """Directly execute a plugin action (bypasses LLM)."""
    if not agent:
        raise HTTPException(503, "Agent not ready")

    result = await agent.quick_action(req.plugin, req.action, req.params)
    return {"plugin": req.plugin, "action": req.action, "result": result}


@app.get("/plugins")
async def list_plugins():
    """List all available plugins and their actions."""
    if not agent:
        raise HTTPException(503, "Agent not ready")
    return {"plugins": agent.plugins.list_plugins()}


# ---------- WebSocket (Real-time mobile app connection) ----------

class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        log.info(f"WebSocket connected ({len(self.active_connections)} active)")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        log.info(f"WebSocket disconnected ({len(self.active_connections)} active)")

    async def send(self, websocket: WebSocket, data: dict):
        await websocket.send_json(data)

    async def broadcast(self, data: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                pass


ws_manager = ConnectionManager()


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    Real-time WebSocket connection for the mobile app.
    Send JSON: {"message": "your text here"}
    Receive JSON: {"response": "Hinata's reply", "type": "chat"}
    """
    await ws_manager.connect(websocket)

    # Send welcome message
    await ws_manager.send(websocket, {
        "type": "system",
        "response": f"🌸 Connected to {Config.AGENT_NAME}! How can I help?",
    })

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "").strip()

            if not message:
                continue

            # Send "thinking" indicator
            await ws_manager.send(websocket, {
                "type": "thinking",
                "response": "🤔 Thinking...",
            })

            # Process the message
            response = await agent.process(message, user_id)

            # Send the response
            await ws_manager.send(websocket, {
                "type": "chat",
                "response": response,
                "user_id": user_id,
            })

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        log.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


# ---------- Server entry point ----------

def start_server():
    """Start the FastAPI server."""
    import uvicorn
    log.info(f"🌸 Starting {Config.AGENT_NAME} server on {Config.API_HOST}:{Config.API_PORT}")
    uvicorn.run(
        "api.server:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=Config.DEBUG,
        log_level="info",
    )
