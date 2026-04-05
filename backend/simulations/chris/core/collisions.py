"""Collision detection and inelastic merging for the gravity simulation."""

from __future__ import annotations

import numpy as np

from .state import ParticleState


def resolve_collisions(
    state: ParticleState,
    r_collide: float,
    star_index: int = 0,
) -> ParticleState:
    """Resolve collisions by inelastic merge; return state with possibly smaller N."""
    pos = state.positions
    vel = state.velocities
    masses = state.masses
    n = pos.shape[0]
    r2_collide = r_collide * r_collide

    if n <= 1:
        return state

    p = np.array(pos, dtype=float, copy=True)
    v = np.array(vel, dtype=float, copy=True)
    m = np.array(masses, dtype=float, copy=True)

    keep = np.ones(n, dtype=bool)

    star_pos = p[star_index]
    star_vel = v[star_index]
    star_mass = m[star_index]

    for i in range(n):
        if i == star_index or not keep[i]:
            continue
        dr = p[i] - star_pos
        r2 = float(np.sum(dr * dr))
        if r2 < r2_collide:
            star_mass += m[i]
            keep[i] = False

    p[star_index] = star_pos
    v[star_index] = star_vel
    m[star_index] = star_mass

    indices = np.where(keep)[0]
    others = [i for i in indices if i != star_index]
    order = np.array([star_index] + sorted(others), dtype=np.intp)
    p = p[order]
    v = v[order]
    m = m[order]
    n_curr = len(order)

    if n_curr <= 1:
        return ParticleState(positions=p, velocities=v, masses=m)

    while True:
        non_star = p[1:]
        n_ns = non_star.shape[0]
        if n_ns <= 1:
            break
        dx = non_star[:, None, :] - non_star[None, :, :]
        r2 = np.sum(dx * dx, axis=2)
        np.fill_diagonal(r2, np.inf)
        i_min, j_min = np.unravel_index(np.argmin(r2), r2.shape)
        r2_min = r2[i_min, j_min]
        if r2_min >= r2_collide:
            break
        ii = i_min + 1
        jj = j_min + 1
        mi = m[ii]
        mj = m[jj]
        mtot = mi + mj
        com = (mi * p[ii] + mj * p[jj]) / mtot
        v_com = (mi * v[ii] + mj * v[jj]) / mtot
        p[ii] = com
        v[ii] = v_com
        m[ii] = mtot
        mask = np.ones(n_curr, dtype=bool)
        mask[jj] = False
        p = p[mask]
        v = v[mask]
        m = m[mask]
        n_curr = p.shape[0]

    return ParticleState(positions=p, velocities=v, masses=m)
