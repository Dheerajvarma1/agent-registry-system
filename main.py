from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Set, Dict

app = FastAPI(title="Agent Discovery + Usage Platform")

# Models
class Agent(BaseModel):
    name: str = Field(..., example="DocParser")
    description: str = Field(..., example="Extracts structured data from PDFs")
    endpoint: str = Field(..., example="https://api.example.com/parse")
    tags: List[str] = []

class UsageRequest(BaseModel):
    caller: str = Field(..., example="AgentA")
    target: str = Field(..., example="DocParser")
    units: int = Field(..., example=10)
    request_id: str = Field(..., example="abc123")

# Storage (In-memory)
agents: List[Agent] = []
usage_logs: List[UsageRequest] = []
processed_request_ids: Set[str] = set()
usage_aggregation: Dict[str, int] = {}

# Helper functions
def extract_keywords(text: str) -> List[str]:
    # Simple keyword extraction: lower case, split, filter out short words
    # Option B: implement simple keyword extraction logic
    words = text.lower().replace(".", " ").replace(",", " ").split()
    # Filter out common stopwords (minimal set)
    stopwords = {"and", "the", "for", "from", "with", "extracts", "structured", "data"}
    keywords = [w for w in words if len(w) > 2 and w not in stopwords]
    return list(set(keywords))

# --- Part 1: Agent Registry ---

@app.post("/agents", status_code=201)
async def add_agent(agent: Agent):
    # Check if agent with same name already exists (optional but good practice)
    for existing in agents:
        if existing.name.lower() == agent.name.lower():
            # If exists, maybe we update or return error. 
            # Re-registration should be handled. Let's make it idempotent as well.
            return existing
    
    # Generate tags if missing (Bonus logic)
    if not agent.tags:
        agent.tags = extract_keywords(agent.description)
    
    agents.append(agent)
    return agent

@app.get("/agents", response_model=List[Agent])
async def list_agents():
    return agents

@app.get("/search", response_model=List[Agent])
async def search_agents(q: str = Query(..., description="Query string to search in name or description")):
    query = q.lower()
    results = [
        agent for agent in agents
        if query in agent.name.lower() or query in agent.description.lower()
    ]
    return results

# --- Part 2 & 3: Usage Logging & Data Thinking ---

@app.post("/usage")
async def log_usage(usage: UsageRequest):
    # 1. Validation: Unknown agent
    target_exists = any(a.name.lower() == usage.target.lower() for a in agents)
    if not target_exists:
        raise HTTPException(status_code=404, detail=f"Target agent '{usage.target}' not found")

    # 2. Idempotency: Duplicate request_id
    if usage.request_id in processed_request_ids:
        # Ignore second request (return current state or just success)
        return {"status": "ignored", "message": "Duplicate request_id", "request_id": usage.request_id}

    # 3. Log usage
    usage_logs.append(usage)
    processed_request_ids.add(usage.request_id)
    
    # 4. Aggregate usage
    target_name = next(a.name for a in agents if a.name.lower() == usage.target.lower())
    usage_aggregation[target_name] = usage_aggregation.get(target_name, 0) + usage.units
    
    return {"status": "recorded", "request_id": usage.request_id}

@app.get("/usage-summary")
async def get_usage_summary():
    return usage_aggregation

@app.get("/")
async def root():
    return {"message": "Welcome to Agent Discovery + Usage Platform API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
