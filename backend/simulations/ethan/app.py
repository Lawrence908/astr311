"""
simulations/ethan/app.py — N-Body 2D Simulator controller adapter

Wraps Ethan's pre-computed N-body simulator (three_body + pluto_system scenarios)
for integration with the SimLab WebSocket controller.

Key difference from GravSim: this sim is NOT continuously streamed. Instead:
  1. Client sends   { type: 'run_simulation', data: { scenario, ...params } }
  2. Server computes full history (fast, pure CPU)
  3. Server sends   { type: 'history', data: { history, steps, scenario } }
  4. Client scrubs the history locally via playback controls

Controller interface required:
  AsyncSimulator.get_latest_state() -> dict | None
  AsyncSimulator.send_command(cmd: dict)
  AsyncSimulator.calculate_velocity(position, mass) -> list
  AsyncSimulator.stop()
  AsyncSimulator.sim.get_state() -> dict   (for initial connect message)
"""

from __future__ import annotations

import threading
import traceback
from queue import Queue, Empty

# sim.py lives at simulations/ethan/backend/sim.py
from simulations.ethan.backend.sim import (
    simulate,
    create_bodies_from_ic,
    create_binary_with_trojan,
    create_figure_eight,
    create_lagrange_equilateral,
    create_pluto_system,
    create_three_body_problem,
)


# ============================================================================
# ASYNC SIMULATOR — Controller Interface
# ============================================================================

class AsyncSimulator:
    """
    Thin adapter that makes Ethan's request/response sim work with the
    SimLab WebSocket controller's streaming interface.

    The controller calls get_latest_state() in a tight loop. Normally this
    returns None (nothing to stream). When a run_simulation command is
    processed, it puts the full history dict into the output queue once.
    """

    def __init__(self):
        self._out_queue: Queue = Queue(maxsize=4)
        self._cmd_queue: Queue = Queue()
        self._running = True
        self._shutdown = threading.Event()

        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="ethan-sim"
        )
        self._thread.start()
        print("[EthanSim] Ready")

        # Expose inner sim object for controller's initial-state read on connect
        self.sim = _ReadyProxy()

    # ------------------------------------------------------------------
    # WORKER THREAD
    # ------------------------------------------------------------------

    def _loop(self):
        while self._running and not self._shutdown.is_set():
            try:
                cmd = self._cmd_queue.get(timeout=0.1)
            except Empty:
                continue
            try:
                self._handle_command(cmd)
            except Exception as e:
                print(f"[EthanSim] Command error: {e}")
                traceback.print_exc()
                self._put({"type": "error", "data": {"message": str(e)}})

    def _handle_command(self, cmd: dict):
        t    = cmd.get("type")
        data = cmd.get("data", {}) or {}

        if t == "run_simulation":
            scenario = data.get("scenario", "pluto_system")

            if scenario == "three_body":
                pos = data.get("pos")
                vel = data.get("vel")
                mass = data.get("mass")
                steps = int(data.get("steps", 12000))
                dt = float(data.get("dt", 0.0005))

                parsed = _parse_ic_triples(pos, vel, mass)
                if parsed is None:
                    bodies = create_three_body_problem()
                else:
                    positions, velocities, masses = parsed
                    bodies = create_bodies_from_ic(positions, velocities, masses)
                history = simulate(
                    bodies, dt, steps, G=1.0, softening=0.05, record_every=20
                )

            elif scenario == "three_body_figure8":
                steps = int(data.get("steps", 20000))
                dt = float(data.get("dt", 0.002))
                bodies = create_figure_eight()
                history = simulate(
                    bodies, dt, steps, G=1.0, softening=0.001, record_every=40
                )

            elif scenario == "three_body_lagrange":
                steps = int(data.get("steps", 12000))
                dt = float(data.get("dt", 0.01))
                bodies = create_lagrange_equilateral()
                history = simulate(
                    bodies, dt, steps, G=1.0, softening=0.001, record_every=30
                )

            elif scenario == "three_body_trojan":
                steps = int(data.get("steps", 32000))
                dt = float(data.get("dt", 0.0002))
                bodies = create_binary_with_trojan()
                history = simulate(
                    bodies, dt, steps, G=1.0, softening=0.001, record_every=40
                )

            elif scenario == "pluto_system":
                steps = int(data.get("steps", 4000))
                dt    = float(data.get("dt", 1000))
                bodies  = create_pluto_system()
                history = simulate(bodies, dt, steps)

            else:
                self._put({"type": "error",
                           "data": {"message": f"Unknown scenario: {scenario}"}})
                return

            print(f"[EthanSim] Computed {len(history)} frames for '{scenario}'")
            self._put({
                "type": "history",
                "data": {
                    "history":  history,
                    "steps":    len(history),
                    "scenario": scenario,
                },
            })

        elif t in ("stop_simulation", "pong"):
            pass  # lifecycle handled by controller

        else:
            print(f"[EthanSim] Unknown command: {t}")

    def _put(self, msg: dict):
        try:
            # Drop if queue full (stale result) — client will request again
            if self._out_queue.full():
                try:
                    self._out_queue.get_nowait()
                except Empty:
                    pass
            self._out_queue.put_nowait(msg)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # CONTROLLER INTERFACE
    # ------------------------------------------------------------------

    def get_latest_state(self):
        """Called by controller in a tight loop. Returns next message or None."""
        try:
            return self._out_queue.get_nowait()
        except Empty:
            return None

    def send_command(self, cmd: dict):
        """Route incoming WebSocket commands from the client."""
        self._cmd_queue.put(cmd)

    def calculate_velocity(self, position, mass):
        """Not applicable for this sim. Controller calls this for compute_velocity requests."""
        return [0.0, 0.0, 0.0]

    def stop(self):
        """Clean shutdown called by controller on disconnect / navigation home."""
        self._running = False
        self._shutdown.set()
        if self._thread.is_alive():
            self._thread.join(timeout=3.0)
        print("[EthanSim] Stopped")


class _ReadyProxy:
    """
    Stub inner sim so the controller can call runner.sim.sim.get_state()
    on WebSocket connect and get a sensible initial message.
    The frontend uses this to know the server is ready.
    """
    def get_state(self):
        return {
            "type": "ready",
            "data": {
                "message": "Connected — send run_simulation to begin",
                "scenarios": [
                    "pluto_system",
                    "three_body",
                    "three_body_figure8",
                    "three_body_lagrange",
                    "three_body_trojan",
                ],
            },
        }


# ============================================================================
# HELPERS — comma-separated vector parsing for WebSocket run params
# ============================================================================

def _parse_ic_triples(
    pos: str | None, vel: str | None, mass: str | None
) -> tuple[list, list, list] | None:
    """Parse comma-separated pos (x,y pairs), vel, mass for N bodies; N >= 1."""
    if not pos or not vel or not mass:
        return None
    pv = [float(x) for x in pos.split(",")]
    vv = [float(x) for x in vel.split(",")]
    mv = [float(x) for x in mass.split(",")]
    n = len(mv)
    if n < 1 or len(pv) != 2 * n or len(vv) != 2 * n:
        return None
    positions = [[pv[2 * i], pv[2 * i + 1]] for i in range(n)]
    velocities = [[vv[2 * i], vv[2 * i + 1]] for i in range(n)]
    return positions, velocities, mv