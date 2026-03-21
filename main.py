import uvicorn
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from simulation_engine import SimulationEngine
from fastapi.responses import FileResponse
import os
import io
import PyPDF2

app = FastAPI(title="Generative Parallel World Simulator")
engine = SimulationEngine()

# Ensure static folder exists
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

class SeedRequest(BaseModel):
    seed_text: str

class EpochRequest(BaseModel):
    world_id: str
    steps: int = 1

@app.get("/")
def read_index():
    return FileResponse("static/index.html")

@app.post("/api/world/parse_file")
async def parse_file(file: UploadFile = File(...)):
    text = ""
    try:
        content = await file.read()
        if file.filename.lower().endswith(".pdf"):
            reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        else:
            # Assumes txt or md
            text = content.decode("utf-8")
        return {"parsed_text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse file: {str(e)}")

@app.post("/api/world/spawn")
def spawn_world(req: SeedRequest):
    try:
        world = engine.generate_world_from_seed(req.seed_text)
        return engine.get_world_status(world.world_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/world/advance")
def advance_world(req: EpochRequest):
    try:
        for _ in range(req.steps):
            engine.advance_epoch(req.world_id)
        return engine.get_world_status(req.world_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/world/{world_id}")
def get_world(world_id: str):
    try:
        return engine.get_world_status(world_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail="World not found")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
