from fastapi import FastAPI
from pydantic import BaseModel
from sim_entry_points.TraverseAPIInput import traverse_api_input

app = FastAPI()

class SimRequest(BaseModel):
    Team: list
    Mystic_Code_ID: int
    Quest_ID: int
    Commands: list

@app.post("/simulate")
async def simulate(req: SimRequest):
    result = traverse_api_input(
        req.Team,
        req.Mystic_Code_ID,
        req.Quest_ID,
        req.Commands
    )
    return {"result": result}