"""
simulations/chris/app.py — Big Bang N-body explosion simulator for SimLab

Particles explode outward from a central point; mutual gravity pulls them
back.  No central star, no orbits — just expansion vs. gravitational collapse.

Runs batched CPU simulations and sends JSON replay payloads over the WebSocket
(via the controller), with periodic progress updates.
"""

from __future__ import annotations

import re
import threading
import traceback
from queue import Empty, Queue
from typing import Any

import numpy as np

from simulations.chris.core.forces import compute_accelerations_vectorized
from simulations.chris.core.init_conditions import make_explosion_3d
from simulations.chris.core.integrators import leapfrog_step
from simulations.chris.core.replay import build_replay_json
from simulations.chris.core.state import ParticleState

MAX_SNAPSHOTS = 2000
MAX_N = 10000
MAX_STEPS = 1_000_000


def _sanitize_name(name: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_-]", "_", name or "replay").strip("_") or "replay"
    return safe[:200]


def _parse_run_params(body: dict) -> tuple[dict[str, Any] | None, str | None]:
    """Validate and normalize run params. Returns (params_dict, error_message)."""
    try:
        name = _sanitize_name(str(body.get("name", "run")))
        n = max(1, min(MAX_N, int(body.get("n", 500))))
        steps = max(1, min(MAX_STEPS, int(body.get("steps", 1000))))
        dt = float(body.get("dt", 0.01))
        r_max = float(body.get("r_max", 0.5))
        v_radial = float(body.get("v_radial", 1.0))
        replay_every = max(1, min(1000, int(body.get("replay_every", 20))))
        n_snapshots_cap = 1 + (steps // replay_every)
        if n_snapshots_cap > MAX_SNAPSHOTS:
            replay_every = max(replay_every, (steps + MAX_SNAPSHOTS - 2) // (MAX_SNAPSHOTS - 1))
        softening = float(body.get("softening", 0.05))
        seed = int(body.get("seed", 42))
        m_particle = body.get("m_particle")
        if m_particle is not None:
            m_particle = float(m_particle)
        velocity_noise = float(body.get("velocity_noise", 0.05))
    except (TypeError, ValueError) as e:
        return None, f"Invalid parameter: {e}"

    return {
        "name": name,
        "n": n,
        "steps": steps,
        "dt": dt,
        "r_max": r_max,
        "v_radial": v_radial,
        "replay_every": replay_every,
        "softening": softening,
        "seed": seed,
        "m_particle": m_particle,
        "velocity_noise": velocity_noise,
    }, None


def _make_initial_state(params: dict[str, Any]) -> ParticleState:
    return make_explosion_3d(
        params["n"],
        seed=params["seed"],
        m_particle=params["m_particle"],
        r_max=params["r_max"],
        v_radial=params["v_radial"],
        velocity_noise=params["velocity_noise"],
    )


class AsyncSimulator:
    """Worker thread runs disk/cloud N-body sim; outputs progress and replay JSON."""

    def __init__(self) -> None:
        self._out_queue: Queue = Queue(maxsize=32)
        self._cmd_queue: Queue = Queue()
        self._running = True
        self._shutdown = threading.Event()
        self._cancel_run = threading.Event()

        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="chris-sim"
        )
        self._thread.start()
        print("[ChrisSim] Ready")

        self.sim = _ReadyProxy()

    def _loop(self) -> None:
        while self._running and not self._shutdown.is_set():
            try:
                cmd = self._cmd_queue.get(timeout=0.1)
            except Empty:
                continue
            try:
                self._handle_command(cmd)
            except Exception as e:
                print(f"[ChrisSim] Command error: {e}")
                traceback.print_exc()
                self._put({"type": "error", "data": {"message": str(e)}})

    def _handle_command(self, cmd: dict) -> None:
        t = cmd.get("type")
        data = cmd.get("data", {}) or {}

        if t == "run_simulation":
            params, err = _parse_run_params(data if isinstance(data, dict) else {})
            if err or params is None:
                self._put({"type": "error", "data": {"message": err or "Invalid parameters"}})
                return

            self._cancel_run.clear()

            result = _run_simulation_with_progress(
                params, self._cancel_run, self._put
            )

            if not result.get("ok"):
                self._put(
                    {
                        "type": "error",
                        "data": {
                            "message": result.get("error", "Simulation failed"),
                            "name": result.get("name"),
                        },
                    }
                )
                return

            self._put({"type": "replay", "data": result["replay"]})

        elif t == "stop_simulation":
            self._cancel_run.set()

        elif t == "pong":
            pass

        else:
            print(f"[ChrisSim] Unknown command: {t}")

    def _put(self, msg: dict) -> None:
        try:
            if self._out_queue.full():
                try:
                    self._out_queue.get_nowait()
                except Empty:
                    pass
            self._out_queue.put_nowait(msg)
        except Exception:
            pass

    def get_latest_state(self):
        try:
            return self._out_queue.get_nowait()
        except Empty:
            return None

    def send_command(self, cmd: dict) -> None:
        if cmd.get("type") == "stop_simulation":
            self._cancel_run.set()
        self._cmd_queue.put(cmd)

    def calculate_velocity(self, position, mass):
        return [0.0, 0.0, 0.0]

    def stop(self) -> None:
        self._cancel_run.set()
        self._running = False
        self._shutdown.set()
        if self._thread.is_alive():
            self._thread.join(timeout=3.0)
        print("[ChrisSim] Stopped")


def _run_simulation_with_progress(
    params: dict[str, Any],
    cancel_event: threading.Event,
    put_fn,
) -> dict[str, Any]:
    """Run the explosion sim, emitting progress every 5% via put_fn."""
    softening = params["softening"]
    steps = params["steps"]
    dt = params["dt"]
    replay_every = params["replay_every"]
    name = params["name"]

    state = _make_initial_state(params)

    def accel_fn(s: ParticleState) -> np.ndarray:
        return compute_accelerations_vectorized(s, softening=softening, G=1.0)

    replay_positions: list[np.ndarray] = []
    replay_steps_list: list[int] = []

    last_progress_bucket = -1

    def emit_progress(completed: int) -> None:
        nonlocal last_progress_bucket
        if steps <= 0:
            return
        if completed <= 0:
            bucket = 0
        elif completed >= steps:
            bucket = 100
        else:
            bucket = min((int(100 * completed / steps) // 5) * 5, 95)
        if bucket != last_progress_bucket:
            last_progress_bucket = bucket
            put_fn(
                {
                    "type": "progress",
                    "data": {
                        "pct": bucket,
                        "step": min(completed, steps),
                        "total_steps": steps,
                        "name": name,
                    },
                }
            )

    emit_progress(0)

    for step in range(steps):
        if cancel_event.is_set():
            return {"ok": False, "error": "cancelled", "name": name}

        state = leapfrog_step(state, dt=dt, accel_fn=accel_fn)

        completed = step + 1
        if completed >= steps:
            emit_progress(steps)
        else:
            b = min((int(100 * completed / steps) // 5) * 5, 95)
            if b > last_progress_bucket:
                emit_progress(completed)

        if step % replay_every == 0:
            replay_positions.append(state.positions.copy())
            replay_steps_list.append(step)

    if not cancel_event.is_set():
        replay_positions.append(state.positions.copy())
        replay_steps_list.append(steps)

    if cancel_event.is_set():
        return {"ok": False, "error": "cancelled", "name": name}

    replay = build_replay_json(
        replay_positions,
        replay_steps_list,
        state.masses,
        dt,
        variable_n=False,
    )
    replay["name"] = name
    return {"ok": True, "replay": replay, "name": name}


class _ReadyProxy:
    def get_state(self) -> dict:
        return {
            "type": "ready",
            "data": {
                "message": "Connected — send run_simulation to launch a Big Bang explosion",
                "sim": "chrissim",
                "parameters": {
                    "n": f"1..{MAX_N} (particle count)",
                    "steps": f"1..{MAX_STEPS}",
                    "dt": "float (timestep, default 0.01)",
                    "r_max": "float (initial sphere radius, default 0.5)",
                    "v_radial": "float (outward expansion speed, default 1.0)",
                    "velocity_noise": "float (fractional perturbation, default 0.05)",
                    "replay_every": "int (snapshot interval, auto-capped)",
                    "softening": "float (default 0.05)",
                    "seed": "int (default 42)",
                    "m_particle": "float | null (per-particle mass, default 1/n)",
                    "name": "string (run label)",
                },
            },
        }
