from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from sim import simulate, create_three_body_problem, create_pluto_system


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

app = FastAPI(title="Ethan N-Body Backend", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")


@app.get("/")
def get_index():
    return FileResponse(FRONTEND_DIR / "dashboard.html")


@app.get("/dashboard")
def get_dashboard():
    return FileResponse(FRONTEND_DIR / "dashboard.html")


@app.get("/sim")
def get_sim_viewer():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/simulate/{scenario}")
def get_simulation(
    scenario: str,
    dt: Optional[float] = None,
    steps: Optional[int] = None,
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
            steps = _resolve_steps(steps, default_steps=12000)
            history = simulate(bodies, dt, steps, G=1.0, softening=0.05, record_every=20)
        elif scenario == "pluto_system":
            bodies = create_pluto_system()
            if dt is None:
                dt = 1000
            steps = _resolve_steps(steps, default_steps=4000)
            history = simulate(bodies, dt, steps)
        else:
            return {"error": "Unknown scenario"}

        return {"history": history, "steps": len(history), "scenario": scenario}
    except Exception as e:
        return {"error": str(e), "scenario": scenario}


@app.get("/simulate/{scenario}")
def get_simulation_legacy(
    scenario: str,
    dt: Optional[float] = None,
    steps: Optional[int] = None,
    pos: Optional[str] = None,
    vel: Optional[str] = None,
    mass: Optional[str] = None,
):
    return get_simulation(
        scenario=scenario,
        dt=dt,
        steps=steps,
        pos=pos,
        vel=vel,
        mass=mass,
    )


def _parse_vecs(s: str, n: int):
    vals = [float(x) for x in s.split(",")]
    return [vals[i * 2:(i + 1) * 2] for i in range(n)]


def _parse_floats(s: str, n: int):
    vals = [float(x) for x in s.split(",")]
    return vals[:n]


def _resolve_steps(steps: Optional[int], default_steps: int) -> int:
    if steps is None:
        return default_steps
    if steps < 1:
        raise ValueError("steps must be a positive integer")
    return steps


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)