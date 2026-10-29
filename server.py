import os
import subprocess
import datetime
from pathlib import Path
from contextlib import asynccontextmanager
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from src.graph.workflow import create_sdlc_graph

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

state_store = {
    "graph": None,
    "activities": []
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing HabitatAI LangGraph agents...")
    state_store["graph"] = await create_sdlc_graph(model_name="gemini-3.1-flash-lite")
    print("HabitatAI agents ready.")
    yield
    print("Shutting down HabitatAI backend.")

app = FastAPI(title="HabitatAI API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_git_info() -> Dict[str, Any]:
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], 
            stderr=subprocess.DEVNULL,
            cwd=str(BASE_DIR)
        ).decode().strip()
    except Exception:
        branch = "main"

    try:
        status_line = subprocess.check_output(
            ["git", "status", "-sb"], 
            stderr=subprocess.DEVNULL,
            cwd=str(BASE_DIR)
        ).decode().splitlines()[0]
        tracking = status_line.replace(f"## {branch}", "").strip()
        if not tracking:
            tracking = "up to date with main"
        elif tracking.startswith("..."):
            tracking = tracking.replace("...", " &bull; ")
    except Exception:
        tracking = "clean tree"

    try:
        latest_commit = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%s"], 
            stderr=subprocess.DEVNULL,
            cwd=str(BASE_DIR)
        ).decode().strip()
    except Exception:
        latest_commit = "No recent commits"

    chroma_dir = BASE_DIR / "chroma_db"
    if chroma_dir.exists():
        mtime = datetime.datetime.fromtimestamp(chroma_dir.stat().st_mtime)
        delta_min = int((datetime.datetime.now() - mtime).total_seconds() / 60)
        chroma_status = f"ChromaDB refreshed {delta_min}m ago" if delta_min > 0 else "ChromaDB refreshed just now"
        index_state = "up to date"
    else:
        chroma_status = "ChromaDB local store active"
        index_state = "ready"

    return {
        "repo_name": os.path.basename(BASE_DIR),
        "branch": branch,
        "tracking": tracking,
        "latest_commit": latest_commit,
        "chroma_status": chroma_status,
        "index_state": index_state,
        "sandbox_path": str(BASE_DIR).replace("\\", "/")
    }

class QueryRequest(BaseModel):
    query: str

@app.get("/api/status")
async def get_status():
    git_data = get_git_info()
    return {
        "git": git_data,
        "activities": state_store["activities"]
    }

@app.post("/api/chat")
async def chat_with_agents(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Empty query")

    graph = state_store.get("graph")
    if not graph:
        raise HTTPException(status_code=503, detail="Graph not initialized")

    try:
        result = await graph.ainvoke({
            "messages": [("user", req.query)]
        })

        last_message = result["messages"][-1]
        raw_content = getattr(last_message, "content", last_message)

        if isinstance(raw_content, str):
            text_content = raw_content
        elif isinstance(raw_content, list):
            parts = []
            for item in raw_content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and "text" in item:
                    parts.append(item["text"])
                else:
                    parts.append(str(item))
            text_content = "\n".join(parts)
        elif isinstance(raw_content, dict):
            text_content = raw_content.get("text", str(raw_content))
        else:
            text_content = str(raw_content)

        agent_type = "Developer"
        color = "emerald"
        q_lower = req.query.lower()
        if any(w in q_lower for w in ["health", "check", "diagnos", "status"]):
            agent_type = "Support"
            color = "blue"
        elif any(w in q_lower for w in ["refactor", "docstring", "type", "clean"]):
            agent_type = "Refactor"
            color = "amber"

        new_activity = {
            "agent": agent_type,
            "color": color,
            "text": req.query,
            "time": datetime.datetime.now().strftime("%H:%M")
        }
        state_store["activities"].insert(0, new_activity)
        if len(state_store["activities"]) > 10:
            state_store["activities"].pop()

        return {
            "agent": agent_type,
            "response": text_content,
            "activity": new_activity
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")