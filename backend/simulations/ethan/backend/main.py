from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sim import simulate, create_three_body_problem, create_pluto_system, G_SI
from typing import Optional
import json

app = FastAPI()

#allow errbody to access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #allow requests from anyone
    allow_credentials=True, #cookie and auth headers can be sent
    allow_methods=["*"], #allow all http methods
    allow_headers=["*"] #allow all headers in requests
)

app.mount("/frontend", StaticFiles(directory="../frontend/"), name="frontend")

#simple dashboard view
@app.get("/", response_class=HTMLResponse)
def get_dashbaord():
    with open("../frontend/dashboard.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/simulate/{scenario}")
def get_simulation(
    scenario: str,
    dt: Optional[float] = None,
    steps: int = 500,
    pos: Optional[str] = None,
    vel: Optional[str] = None,
    mass: Optional[str] = None,
):
    try:
        if scenario == "three_body":
            positions = _parse_vecs(pos, 3) if pos else None
            velocities = _parse_vecs(vel, 3) if vel else None
            masses = _parse_floats(mass, 3) if mass else None
            bodies = create_three_body_problem(positions, velocities, masses)
            if dt is None:
                dt = 0.0005
            if steps == 500:
                steps = 12000
            history = simulate(bodies, dt, steps, G=1.0, softening=0.05, record_every=20)
        elif scenario == "pluto_system":
            bodies = create_pluto_system()
            if dt is None:
                dt = 1000
            if steps == 500:
                steps = 4000
            history = simulate(bodies, dt, steps)
        else:
            return {"error": "Unknown scenario"}
        
        return {"history": history, "steps": len(history), "scenario": scenario}
    except Exception as e:
        return {"error": str(e), "scenario": scenario}
    
def _parse_vecs(s, n):
    vals = [float(x) for x in s.split(',')]
    return [vals[i*2:(i+1)*2] for i in range(n)]

def _parse_floats(s, n):
    vals = [float(x) for x in s.split(',')]
    return vals[:n]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)