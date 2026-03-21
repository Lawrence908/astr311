"""
controller.py — Secure WebSocket Controller

Manages authentication, session lifecycle, and simulation process management.
Simulations run as isolated threads; the controller brokers all client communication.

HTML is served statically by nginx from /var/www/gravsim/.
This controller only handles: /auth, /simulations, /health, /ws

Run with:
    uvicorn controller:app --host 10.10.10.2 --port 8000
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import time
import traceback
import threading
import secrets
import importlib
import os
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# ============================================================================
# CONFIGURATION
# ============================================================================

load_dotenv()
SHARED_PASSWORD = os.environ.get("SIMLAB_PASSWORD")
if not SHARED_PASSWORD:
    raise RuntimeError("SIMLAB_PASSWORD environment variable is not set")

ALLOWED_ORIGINS = [
    "https://gravsim.duckdns.org",
    "http://localhost:8000",
    "http://10.10.10.2:8000",
]

# Registry of available simulations.
# To add a new simulation:
#   1. Drop a new file in simulations/ implementing the AsyncSimulator interface
#   2. Add an entry here
#   3. Add the HTML file to /var/www/gravsim/sim/<id>.html on the web server
SIMULATION_REGISTRY: Dict[str, Dict[str, Any]] = {
    "jaspersim": {
        "id": "jaspersim",
        "name": "Real Time Gravitational Curvature Simulator",
        "description": "GPU-accelerated N-body orbital mechanics simulation",
        "module": "simulations.jasper.app",
        "icon": "⚛",
        "tags": ["physics", "GPU", "N-body"],
    },
    "ethansim": {
    "id":          "ethansim",
    "name":        "N-Body Simulator",
    "description": "Chaotic three-body problem and Pluto system",
    "module":      "simulations.ethan.app",
    "html_file":   "ethansim.html",
    "icon":        "🪐",
    "tags":        ["physics", "CPU", "N-body", "3D"],
    },
    "chrissim": {
        "id": "chrissim",
        "name": "Big Bang Gravity Simulator",
        "description": "N-body explosion from a point — particles expand outward while gravity pulls them back",
        "module": "simulations.chris.app",
        "icon": "💥",
        "tags": ["physics", "CPU", "N-body", "explosion"],
    },
}

# ============================================================================
# FASTAPI SETUP
# ============================================================================

app = FastAPI(title="SimController", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

serialization_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="serializer")

# ============================================================================
# SESSION & TOKEN MANAGEMENT
# ============================================================================

ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}
ACTIVE_RUNNERS: Dict[str, Any] = {}
SESSION_LOCK = threading.Lock()


class AuthRequest(BaseModel):
    password: str


@app.post("/auth")
async def authenticate(auth: AuthRequest):
    if auth.password != SHARED_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid password")

    token = secrets.token_urlsafe(32)
    with SESSION_LOCK:
        ACTIVE_SESSIONS[token] = {
            "valid": True,
            "sim_id": None,
            "created_at": time.time(),
        }

    return {
        "token": token,
        "expires_in": 86400,
        "message": "Authentication successful",
        "simulations": list(SIMULATION_REGISTRY.values()),
    }


@app.get("/simulations")
async def list_simulations(token: Optional[str] = None):
    if not token or not _verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"simulations": list(SIMULATION_REGISTRY.values())}


@app.get("/health")
async def health():
    import torch
    return {
        "ok": True,
        "cuda": bool(torch.cuda.is_available()),
        "active_sessions": len(ACTIVE_SESSIONS),
        "active_simulations": len(ACTIVE_RUNNERS),
        "available_simulations": list(SIMULATION_REGISTRY.keys()),
    }


def _verify_token(token: str) -> bool:
    with SESSION_LOCK:
        session = ACTIVE_SESSIONS.get(token)
        return session is not None and session["valid"]


def _stop_runner_for_token(token: str):
    """Stop any running simulation for this token and free GPU resources."""
    with SESSION_LOCK:
        runner = ACTIVE_RUNNERS.pop(token, None)
    if runner is not None:
        try:
            runner.stop()
        except Exception as e:
            print(f"[Controller] Error stopping runner for token ...{token[-6:]}: {e}")
        print(f"[Controller] Simulation stopped for token ...{token[-6:]}")


# ============================================================================
# SIMULATION RUNNER
# ============================================================================

class SimulationRunner:
    """
    Wraps a simulation module, providing a unified start/stop/command interface.
    Each simulation module must expose an AsyncSimulator class.
    """

    def __init__(self, sim_id: str):
        self.sim_id = sim_id
        reg = SIMULATION_REGISTRY[sim_id]
        mod = importlib.import_module(reg["module"])
        self.sim = mod.AsyncSimulator()

    def get_latest_state(self):
        return self.sim.get_latest_state()

    def send_command(self, cmd: dict):
        self.sim.send_command(cmd)

    def calculate_velocity(self, position, mass):
        return self.sim.calculate_velocity(position, mass)

    def stop(self):
        self.sim.stop()


# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = None,
    sim_id: Optional[str] = None,
):
    import msgpack

    if not token or not _verify_token(token):
        await websocket.close(code=1008, reason="Invalid token")
        print("[Controller] Rejected unauthenticated WebSocket")
        return

    if not sim_id or sim_id not in SIMULATION_REGISTRY:
        await websocket.close(code=4004, reason=f"Unknown simulation: {sim_id}")
        print(f"[Controller] Rejected unknown sim_id: {sim_id}")
        return

    _stop_runner_for_token(token)
    await websocket.accept()
    print(f"[Controller] Client connected: sim={sim_id}, token=...{token[-6:]}")

    runner = None
    try:
        runner = SimulationRunner(sim_id)
        with SESSION_LOCK:
            ACTIVE_RUNNERS[token] = runner
            ACTIVE_SESSIONS[token]["sim_id"] = sim_id

        initial_state = runner.sim.sim.get_state()
        initial_packed = await asyncio.get_event_loop().run_in_executor(
            serialization_executor,
            lambda: msgpack.packb(_make_serializable(initial_state), use_bin_type=True),
        )
        if initial_packed:
            await asyncio.wait_for(websocket.send_bytes(initial_packed), timeout=5.0)

        last_ping = time.time()

        while True:
            try:
                state = runner.get_latest_state()
                if state:
                    reset_flag = state.pop("reset_occurred", False)
                    packed = await asyncio.get_event_loop().run_in_executor(
                        serialization_executor,
                        lambda s=state: msgpack.packb(_make_serializable(s), use_bin_type=True),
                    )
                    if packed:
                        try:
                            if reset_flag:
                                init_msg = msgpack.unpackb(packed, raw=False)
                                init_msg["type"] = "init"
                                packed = msgpack.packb(init_msg, use_bin_type=True)
                            await asyncio.wait_for(websocket.send_bytes(packed), timeout=1.0)
                        except asyncio.TimeoutError:
                            pass
                        except Exception as e:
                            if "closed" not in str(e).lower():
                                print(f"[Controller] Send error: {e}")
                            break

                now = time.time()
                if now - last_ping > 30:
                    try:
                        await asyncio.wait_for(
                            websocket.send_bytes(
                                msgpack.packb({"type": "ping"}, use_bin_type=True)
                            ),
                            timeout=1.0,
                        )
                        last_ping = now
                    except Exception:
                        break

                try:
                    raw_data = await asyncio.wait_for(websocket.receive(), timeout=0.001)

                    try:
                        if "text" in raw_data:
                            import json
                            msg = json.loads(raw_data["text"])
                        elif "bytes" in raw_data:
                            msg = msgpack.unpackb(raw_data["bytes"], raw=True, strict_map_key=False)
                        else:
                            continue
                    except Exception as e:
                        print(f"[Controller] Decode error: {e}")
                        continue

                    if not isinstance(msg, dict):
                        continue

                    msg = _decode_msg(msg)
                    mtype = msg.get("type")

                    if mtype == "pong":
                        pass
                    elif mtype == "stop_simulation":
                        print(f"[Controller] Client requested stop: sim={sim_id}")
                        break
                    elif mtype == "compute_velocity":
                        data = msg.get("data", {})
                        position = data.get("position", [0, 0, 0])
                        mass = float(data.get("mass", 1.0))
                        velocity = runner.calculate_velocity(position, mass)
                        response = msgpack.packb(
                            {
                                "type": "velocity_computed",
                                "data": {
                                    "velocity": velocity,
                                    "requestId": data.get("requestId"),
                                },
                            },
                            use_bin_type=True,
                        )
                        await asyncio.wait_for(websocket.send_bytes(response), timeout=1.0)
                    else:
                        runner.send_command(msg)

                except asyncio.TimeoutError:
                    pass
                except asyncio.CancelledError:
                    break
                except WebSocketDisconnect:
                    break
                except RuntimeError as e:
                    if "disconnect" in str(e).lower() or "closed" in str(e).lower():
                        break
                    print(f"[Controller] Runtime error: {e}")
                    break
                except Exception as e:
                    if "disconnect" in str(e).lower() or "closed" in str(e).lower():
                        break

                await asyncio.sleep(0.001)

            except asyncio.CancelledError:
                break

    except asyncio.CancelledError:
        pass
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[Controller] WebSocket error: {e}")
        traceback.print_exc()
    finally:
        _stop_runner_for_token(token)
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
        print(f"[Controller] Connection closed: sim={sim_id}, token=...{token[-6:]}")


# ============================================================================
# HELPERS
# ============================================================================

def _make_serializable(state: dict) -> dict:
    import numpy as np

    def convert(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [convert(i) for i in obj]
        return obj

    return convert(state)


def _decode_msg(msg: dict) -> dict:
    decoded = {}
    for k, v in msg.items():
        key = k.decode("utf-8") if isinstance(k, bytes) else k
        if isinstance(v, dict):
            val = _decode_msg(v)
        elif isinstance(v, bytes):
            try:
                val = v.decode("utf-8")
            except Exception:
                val = v
        else:
            val = v
        decoded[key] = val
    return decoded