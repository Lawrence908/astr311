# ASTR311 Gravity Simulator

A multi-scenario gravitational physics simulator built for the ASTR311 course. Three independent simulation backends are served over a real-time WebSocket API and rendered in the browser using Canvas and Three.js.

---

## Simulations

### ChrisSim — N-Body Explosion
A CPU-based N-body simulator modelling a particle cloud expanding against self-gravity, representing a simplified Big Bang scenario.

**Physics:**
- Leapfrog (kick-drift-kick) time integration — 2nd-order accurate, symplectic
- Plummer-softened Newtonian gravity to avoid force singularities at close range
- Hernquist dark matter halo potential for background gravitational field
- Inelastic collision merging: particles within a threshold radius merge with momentum conservation, positions updated to center of mass
- Initial conditions: uniform random sphere with homologous radial expansion (v ∝ r), configurable velocity noise
- Alternative ICs: disk (central star + circular orbit particles) and non-rotating cloud

**Mode:** Batch — computes the full trajectory, then streams the complete replay to the client. Progress updates are emitted every 5%.

**Parameters:** Up to 10,000 particles, 1,000,000 steps, 2,000 replay snapshots, configurable softening, timestep, initial radius, expansion velocity, and particle mass.

---

### EthanSim — Pluto System & Three-Body Problem
A CPU-based integrator for small N-body systems with physically realistic initial conditions.

**Scenarios:**
- **Three-Body Problem:** Pythagorean initial conditions (3-4-5 triangle) producing chaotic, non-repeating orbits. Fully customizable positions, velocities, and masses.
- **Pluto System:** Six-body simulation of Pluto, Charon, Nix, Styx, Kerberos, and Hydra using JPL masses in SI units and real orbital distances.

**Physics:**
- Velocity Verlet (Störmer-Verlet) integration — 2nd-order, time-reversible
- O(N²) pairwise gravitational force summation
- Plummer softening

**Mode:** Batch — full position/velocity history is computed on the server and sent to the client in one message. The client scrubs through frames locally with a playback slider and speed control.

---

### JasperSim — GPU Solar System with Spacetime Visualization
A high-fidelity real-time solar system simulator running on the GPU with general relativistic corrections and a spacetime curvature visualization.

**Physics:**
- **Yoshida 4th-order symplectic integrator** — significantly more accurate than Leapfrog for long integrations; energy error scales as O(dt⁴) vs O(dt²)
- **Units:** AU / M☉ / yr, with G = 4π² (exact from Kepler's third law)
- **Plummer-softened gravity:** F = G·m₁·m₂ / (r² + ε²)^(3/2), ε = 0.001 AU
- **1st Post-Newtonian (1PN) GR correction** using the Einstein-Infeld-Hoffmann (EIH) equations (Will 1993, eq. 10.28) — accounts for spacetime curvature effects on orbital motion
- Mercury perihelion precession verified at 43.00″/century, matching the GR prediction
- Inelastic collision merging with radius-based detection

**Initial Conditions:** Sun + 8 planets (Mercury through Neptune) with JPL DE430 mass ratios. Circular orbit velocities calculated as v = √(G·M☉/a). Visual radii are exaggerated for clarity.

**Spacetime Grid:** A dedicated daemon thread computes a 64×64 Flamm paraboloid (the standard embedding diagram of the Schwarzschild exterior metric) at ~30 Hz:

```
z(r) = -2√(r_s · r)     where r_s = 2GM/c²
```

The grid is exported as raw float32 bytes and rendered as a warped mesh in Three.js.

**Mode:** Real-time streaming at ~50 Hz. Physics and grid computation run on independent threads so grid rendering never blocks the physics loop.

**Hardware:** Requires PyTorch. Uses CUDA GPU tensors when available; falls back to CPU.

---

## System Architecture

### Network Topology

```
                          Internet (Public IP, TCP 80)
                                      │
                         ┌────────────▼────────────┐
                         │   AWS EC2 (astr311-web-app)  │
                         │   Ubuntu LTS 24.2            │
                         │   Nginx — serves index.html  │
                         │   WireGuard: 10.10.10.1      │
                         └────────────┬────────────┘
                                      │ TCP 8000 over WireGuard VPN
                         ┌────────────▼────────────┐
                         │  Local Server (astr311-vm)   │
                         │  Alma Linux 10               │
                         │  Intel Xeon E5-2643 12-Core  │
                         │  36 GB RAM / 32 GB Disk      │
                         │  GPU: NVIDIA A2000            │
                         │  Uvicorn + FastAPI (app.py)  │
                         │  WireGuard: 10.10.10.2       │
                         └─────────────────────────┘

Remote workstations connect via WireGuard:
  10.10.10.3 / 10.10.10.4 / 10.10.10.5 (UDP 51820)
```

The static frontend is served by Nginx on the AWS EC2 instance. All simulation computation runs on the local server (which has the GPU). Communication between the web server and simulation server is tunnelled over a WireGuard VPN on port TCP 8000.

---

### Backend

**`backend/controller.py`** — FastAPI application and WebSocket broker.

- `POST /auth` — Validates password against `SIMLAB_PASSWORD` environment variable, returns a JWT token.
- `GET /simulations` — Lists available simulation modules.
- `GET /health` — Reports CUDA availability and active session count.
- `WebSocket /ws?token=T&sim_id=X` — Bi-directional simulation stream. The controller authenticates the token, instantiates the requested `AsyncSimulator`, and proxies commands and state messages between the client and the simulation worker thread. State is serialized with msgpack for efficient binary transport. GPU memory is cleaned up on disconnect.

Each simulation module implements the same `AsyncSimulator` interface:
- A worker thread runs the physics loop
- An input command queue receives `run_simulation` / `stop_simulation` / `update_params` commands
- An output message queue holds state updates for the controller to forward

```
Browser ──WebSocket──▶ controller.py ──command queue──▶ AsyncSimulator (worker thread)
        ◀─────────────               ◀──output queue──
```

**Simulation modules:**

| ID | Module | Integrator | Compute |
|---|---|---|---|
| `chrissim` | `simulations.chris.app` | Leapfrog | CPU / NumPy |
| `ethansim` | `simulations.ethan.app` | Velocity Verlet | CPU / NumPy |
| `jaspersim` | `simulations.jasper.app` | Yoshida 4th-order | GPU / PyTorch |

---

### Frontend

The frontend is plain HTML/CSS/JavaScript with no build step.

| File | Purpose |
|---|---|
| `frontend/index.html` | Authentication portal and simulation selector |
| `frontend/sim/chrissim.html` | 2D/3D Canvas particle renderer with parameter panel |
| `frontend/sim/ethansim.html` | Canvas renderer with playback scrubber and scenario selector |
| `frontend/sim/jaspersim.html` | Three.js 3D solar system with spacetime mesh and sidebar controls |

**Auth flow:** The user submits a password to `POST /auth`, receives a JWT token stored in `localStorage`, then navigates to a simulation page which appends the token to the WebSocket URL.

---

### Message Protocol

**Batch simulations (ChrisSim, EthanSim):**
```
Client → {type: "run_simulation", data: {...params}}
Server → {type: "progress",  data: {pct, step, total_steps}}  (repeated)
Server → {type: "replay",    data: {positions, masses, steps, dt, ...}}
```

**Real-time simulation (JasperSim):**
```
Client → {type: "update_params", data: {dt, substeps}}
Server → {type: "state", data: {pos, vel, bodies, energy}}  (~50 Hz)
Server → {type: "grid",  data: <raw float32 bytes>}          (~30 Hz)
```

All messages are binary msgpack encoded over the WebSocket connection.

---

## Running the Server

### Requirements

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
numpy==2.0.2
torch          # GPU support requires CUDA toolkit
msgpack
python-jose    # JWT auth
```

### Start

```bash
export SIMLAB_PASSWORD=your_password_here
cd backend
uvicorn controller:app --host 10.10.10.2 --port 8000
```

Or use the provided script:

```bash
bash backend/start_uvicorn.sh
```

### Static Files

Deploy the `frontend/` directory to the Nginx document root (default `/var/www/gravsim/`). Nginx proxies the WebSocket connection through the WireGuard tunnel to the simulation server at `10.10.10.2:8000`.

---

## Repository Structure

```
astr311-gravity/
├── backend/
│   ├── controller.py
│   ├── start_uvicorn.sh
│   └── simulations/
│       ├── chris/
│       │   ├── app.py
│       │   └── core/
│       │       ├── state.py
│       │       ├── forces.py
│       │       ├── integrators.py
│       │       ├── init_conditions.py
│       │       ├── collisions.py
│       │       └── replay.py
│       ├── ethan/
│       │   ├── app.py
│       │   └── backend/
│       │       └── sim.py
│       └── jasper/
│           └── app.py
└── frontend/
    ├── index.html
    └── sim/
        ├── chrissim.html
        ├── ethansim.html
        └── jaspersim.html
```
