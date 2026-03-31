import os
import io
import json
import asyncio
from dotenv import load_dotenv
load_dotenv()

import uvicorn
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import pypdf

import research_agent as agent

app = FastAPI(title="Autonomous Research Agent")

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ─── Request Models ──────────────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    topic: str


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/")
def read_index():
    return FileResponse("static/index.html")


@app.post("/api/research/parse_file")
async def parse_file(file: UploadFile = File(...)):
    """Extract text from PDF, TXT, or MD upload."""
    text = ""
    try:
        content = await file.read()
        if file.filename.lower().endswith(".pdf"):
            reader = pypdf.PdfReader(io.BytesIO(content))
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        else:
            text = content.decode("utf-8")
        return {"parsed_text": text.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse file: {str(e)}")


@app.post("/api/research/start")
def start_research(req: ResearchRequest):
    """Create a new research session and start the agent in the background."""
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    research_id = agent.create_session(req.topic.strip())
    agent.start_research_thread(research_id)
    return {"research_id": research_id, "topic": req.topic.strip()}


@app.get("/api/research/{research_id}/stream")
async def stream_research(research_id: str):
    """SSE endpoint — streams agent step events as they are produced."""
    session = agent.get_session(research_id)
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found.")

    q = session["queue"]

    async def event_generator():
        loop = asyncio.get_event_loop()
        while True:
            # Poll the thread-safe queue without blocking the event loop
            try:
                item = await loop.run_in_executor(None, lambda: q.get(timeout=60))
            except Exception:
                break

            if item is None:
                # Sentinel — agent finished
                yield {"event": "close", "data": json.dumps({"message": "stream closed"})}
                break

            yield {
                "event": item["type"],
                "data": json.dumps(item),
            }

    return EventSourceResponse(event_generator())


@app.get("/api/research/{research_id}/report")
def get_report(research_id: str):
    """Return the completed report and source list."""
    session = agent.get_session(research_id)
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found.")
    if session["status"] == "running":
        raise HTTPException(status_code=202, detail="Research still in progress.")
    return {
        "status": session["status"],
        "topic": session["topic"],
        "report": session.get("report", ""),
        "sources": session.get("sources", []),
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
