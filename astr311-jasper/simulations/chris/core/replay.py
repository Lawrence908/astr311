"""Build web-viewer JSON replay dicts from in-memory snapshot lists."""

from __future__ import annotations

from typing import Any

import numpy as np


def build_replay_json(
    positions_list: list[np.ndarray],
    step_indices: list[int],
    masses_final: np.ndarray,
    dt: float,
    *,
    variable_n: bool,
    masses_per_snapshot: list[np.ndarray] | None = None,
    thin_every: int | None = None,
) -> dict[str, Any]:
    """Build a JSON-serializable replay dict matching astr311-chris export format.

    Parameters
    ----------
    positions_list, step_indices
        Parallel lists of snapshot positions and step numbers.
    masses_final
        Masses after the last step (used for constant-N ``masses`` field).
    dt
        Timestep.
    variable_n
        True if particle count changes per snapshot (collisions).
    masses_per_snapshot
        Required when variable_n is True; one mass array per snapshot.
    thin_every
        If set, keep every Nth snapshot plus the last (same as export --every).
    """
    n_snap = len(positions_list)
    if n_snap == 0:
        return {
            "positions": [],
            "steps": [],
            "masses": [],
            "dt": dt,
            "n_snapshots": 0,
            "variable_n": variable_n,
        }

    if thin_every is not None and thin_every > 1:
        indices = list(range(0, n_snap, thin_every))
        if indices[-1] != n_snap - 1:
            indices.append(n_snap - 1)
        positions_list = [positions_list[i] for i in indices]
        step_indices = [step_indices[i] for i in indices]
        if variable_n and masses_per_snapshot is not None:
            masses_per_snapshot = [masses_per_snapshot[i] for i in indices]
        n_snap = len(positions_list)

    steps_arr = np.array(step_indices, dtype=np.int64)

    if variable_n and masses_per_snapshot is not None:
        return {
            "positions": [p.tolist() for p in positions_list],
            "masses": [m.tolist() for m in masses_per_snapshot],
            "steps": steps_arr.tolist(),
            "dt": dt,
            "n_snapshots": n_snap,
            "variable_n": True,
        }

    stacked = np.stack(positions_list, axis=0)
    return {
        "positions": stacked.tolist(),
        "steps": steps_arr.tolist(),
        "masses": masses_final.tolist(),
        "dt": dt,
        "n_particles": int(masses_final.shape[0]),
        "n_snapshots": n_snap,
        "variable_n": False,
    }
