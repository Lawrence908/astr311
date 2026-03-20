"""CPU implementations of gravitational forces (2D and 3D)."""

from __future__ import annotations

import numpy as np

from .state import ParticleState


def compute_accelerations_vectorized(
    state: ParticleState,
    softening: float = 0.05,
    G: float = 1.0,
) -> np.ndarray:
    """Compute accelerations using vectorized NumPy (broadcasting)."""
    pos = state.positions
    masses = state.masses

    dx = pos[None, :, :] - pos[:, None, :]
    r2 = np.sum(dx * dx, axis=-1) + softening * softening
    np.fill_diagonal(r2, 1.0)
    inv_r3 = 1.0 / (r2 * np.sqrt(r2))
    np.fill_diagonal(inv_r3, 0.0)

    acc = G * (masses[None, :, None] * dx * inv_r3[:, :, None]).sum(axis=1)
    return acc.astype(pos.dtype)


def compute_halo_acceleration(
    positions: np.ndarray,
    M_halo: float,
    a_halo: float,
    G: float = 1.0,
) -> np.ndarray:
    """Acceleration from a static Hernquist dark-matter halo centred at the origin."""
    r = np.sqrt(np.sum(positions * positions, axis=-1, keepdims=True))
    r_safe = np.maximum(r, 1e-12)
    acc = -G * M_halo / (r_safe + a_halo) ** 2 * (positions / r_safe)
    return acc.astype(positions.dtype)
