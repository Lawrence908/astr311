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

RENDER_CONFIG = {
    "body_colors": ["#4dabf7", "#ff6b6b", "#51cf66"],
    "com_color": "#ffd43b",
    "sun": {
        "enabled_by_default": True,
        "direction": [320, 130, 230],
        "color": "#ffd27a",
    },
    "run_config": {
        "three_body": {
            "dt": 0.0005,
            "defaultDurationSec": 6.0,
            "minDurationSec": 0.001,
            "maxDurationSec": 60.0,
            "durationStep": 0.1,
            "durationDecimals": 3,
            "presets": [
                {"label": "3 s", "seconds": 3},
                {"label": "6 s", "seconds": 6},
                {"label": "12 s", "seconds": 12},
                {"label": "30 s", "seconds": 30},
            ],
        },
        "pluto_system": {
            "dt": 1000,
            "defaultDurationSec": 4_000_000,
            "minDurationSec": 1000,
            "maxDurationSec": 4_000_000,
            "durationStep": 1000,
            "durationDecimals": 0,
            "presets": [
                {"label": "1 day", "seconds": 86_400},
                {"label": "7 days", "seconds": 604_800},
                {"label": "30 days", "seconds": 2_592_000},
                {"label": "46 days", "seconds": 4_000_000},
            ],
        },
    },
    "pluto_visuals": {
        "Pluto":   {"color": "#b89a82", "emissive": "#5f4738", "trail": "#d3b59a", "radius": 0.46, "accent": "#ded1c4", "crater": "#8b7663"},
        "Charon":  {"color": "#bfc6cc", "emissive": "#606970", "trail": "#d6dde3", "radius": 0.34, "accent": "#e0e4e8", "crater": "#8d949b"},
        "Styx":    {"color": "#8aa4c8", "emissive": "#334a66", "trail": "#a5bddd", "radius": 0.16, "accent": "#b8c8de", "crater": "#566b85"},
        "Nix":     {"color": "#8f9daf", "emissive": "#3a4a5e", "trail": "#afbdd1", "radius": 0.18, "accent": "#c2ccd9", "crater": "#5d6d82"},
        "Kerberos": {"color": "#b08d7a", "emissive": "#5a4135", "trail": "#caa894", "radius": 0.17, "accent": "#cdb29f", "crater": "#7c5f50"},
        "Hydra":   {"color": "#9ba7b8", "emissive": "#434f60", "trail": "#b8c4d6", "radius": 0.20, "accent": "#c7d0dc", "crater": "#667588"},
    },
    "pluto_visual_fallback": {
        "color": "#d0d6de",
        "emissive": "#5b6673",
        "trail": "#c4cfdb",
        "radius": 0.16,
        "accent": "#e5e9ef",
        "crater": "#909aa8",
    },
    "visual_config": {
        "renderer": {
            "toneMappingExposure": 1.05,
            "shadowsEnabled": True,
        },
        "ui_defaults": {
            "showLabels": True,
            "showTrails": True,
            "showCOM": True,
        },
        "camera": {
            "fov": 60,
            "minDistance": 0.2,
            "maxDistance": 300,
            "resetZ": {
                "three_body": 20,
                "pluto_system": 24,
            },
        },
        "starfield": {
            "count": 2000,
            "minRadius": 300,
            "maxRadius": 450,
            "pointSize": 0.8,
            "opacity": 0.6,
        },
        "lighting": {
            "ambient": {"color": 0x404860, "intensity": 0.22},
            "hemisphere": {"skyColor": 0x8DA4FF, "groundColor": 0x111115, "intensity": 0.22},
            "sun": {
                "color": 0xFFF1D8,
                "intensity": 1.35,
                "shadowMapSize": 2048,
                "shadowBias": -0.00025,
                "shadowNormalBias": 0.025,
                "shadowNear": 1,
                "shadowFar": 1000,
            },
            "rim": {"color": 0x7AA4FF, "intensity": 0.34, "oppositeScale": -0.48},
            "modes": {
                "pluto_on": {"ambient": 0.14, "hemisphere": 0.20, "sun": 1.35, "rim": 0.34},
                "pluto_off": {"ambient": 0.30, "hemisphere": 0.30, "sun": 0.0, "rim": 0.0},
                "other": {"ambient": 0.24, "hemisphere": 0.22, "sun": 1.15, "rim": 0.30},
            },
        },
        "sun_visual": {
            "radius": 4.8,
            "haloScale": 1.9,
            "haloOpacity": 0.18,
            "haloColor": 0xFFE4A8,
        },
        "pluto_rendering": {
            "sphereSegments": 42,
            "fallbackSegments": 20,
            "plutoBumpScale": 0.048,
            "moonBumpScale": 0.034,
            "plutoRoughness": 0.84,
            "moonRoughness": 0.9,
            "metalness": 0.02,
            "emissiveIntensity": 0.045,
            "glowScale": 1.1,
            "glowOpacityPluto": 0.13,
            "glowOpacityMoon": 0.08,
        },
        "shadow": {
            "orbitRadius": 13,
            "sizeFactor": 1.45,
            "minSize": 12,
        },
    },
}

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


@app.get("/api/render-config")
def get_render_config():
    return RENDER_CONFIG


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