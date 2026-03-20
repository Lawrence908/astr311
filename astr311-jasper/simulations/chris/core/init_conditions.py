"""Initial condition generators for the gravity simulation."""

from __future__ import annotations

import numpy as np

from .state import ParticleState

G_DEFAULT = 1.0


def _hernquist_enclosed(r: np.ndarray, M_halo: float, a_halo: float) -> np.ndarray:
    """Hernquist enclosed mass: M(<r) = M_halo * r^2 / (r + a)^2."""
    return M_halo * r**2 / (r + a_halo) ** 2


def make_explosion_3d(
    n_particles: int,
    seed: int | None = None,
    m_particle: float | None = None,
    r_max: float = 0.5,
    v_radial: float = 1.0,
    velocity_noise: float = 0.05,
    position_noise: float = 0.0,
) -> ParticleState:
    """Particles uniformly distributed in a small sphere, all moving radially outward.

    Mimics a Big Bang-like explosion: no central object, no orbits -- just
    mutual gravity acting on an expanding cloud.

    Parameters
    ----------
    n_particles : int
        Total number of particles (no special star particle).
    r_max : float
        Initial radius of the sphere containing all particles.
    v_radial : float
        Hubble-like expansion speed: each particle's radial velocity is
        ``v_radial * (r / r_max)`` so outer shells move faster (homologous
        expansion).  Increase for a faster bang; decrease to let gravity
        recollapse sooner.
    velocity_noise : float
        Fractional random perturbation added to each velocity component.
    position_noise : float
        Absolute Gaussian noise added to positions (in same units as r_max).
    """
    rng = np.random.default_rng(seed)

    u = rng.random(n_particles, dtype=float)
    r = (u ** (1.0 / 3.0)) * r_max
    phi = np.arccos(2.0 * rng.random(n_particles, dtype=float) - 1.0)
    theta = 2.0 * np.pi * rng.random(n_particles, dtype=float)

    x = r * np.sin(phi) * np.cos(theta)
    y = r * np.sin(phi) * np.sin(theta)
    z = r * np.cos(phi)
    positions = np.column_stack([x, y, z]).astype(float)
    if position_noise > 0:
        positions += position_noise * rng.normal(size=(n_particles, 3))

    r_safe = np.maximum(r, 1e-12)
    speed = v_radial * (r / r_max)

    r_hat_x = x / r_safe
    r_hat_y = y / r_safe
    r_hat_z = z / r_safe
    vx = speed * r_hat_x
    vy = speed * r_hat_y
    vz = speed * r_hat_z
    velocities = np.column_stack([vx, vy, vz]).astype(float)
    if velocity_noise > 0:
        velocities += velocity_noise * speed[:, None] * rng.normal(size=(n_particles, 3))

    if m_particle is None:
        m_particle = 1.0 / n_particles
    masses = np.full(n_particles, m_particle, dtype=float)

    return ParticleState(positions=positions, velocities=velocities, masses=masses)


def make_disk_2d(
    n_particles: int,
    seed: int | None = None,
    M_star: float = 1.0,
    m_particle: float | None = None,
    r_min: float = 0.5,
    r_max: float = 2.0,
    G: float = G_DEFAULT,
    velocity_noise: float = 0.02,
    position_noise: float = 0.01,
    M_halo: float = 0.0,
    a_halo: float = 5.0,
) -> ParticleState:
    rng = np.random.default_rng(seed)
    n_total = n_particles + 1

    star_pos = np.zeros((1, 2), dtype=float)
    star_vel = np.zeros((1, 2), dtype=float)
    star_mass = np.array([M_star], dtype=float)

    r2_min, r2_max = r_min * r_min, r_max * r_max
    r2 = r2_min + (r2_max - r2_min) * rng.random(n_particles, dtype=float)
    r = np.sqrt(r2)
    theta = 2.0 * np.pi * rng.random(n_particles, dtype=float)

    x = r * np.cos(theta)
    y = r * np.sin(theta)
    positions = np.column_stack([x, y]).astype(float)
    positions += position_noise * rng.normal(size=(n_particles, 2))

    M_enc = M_star + _hernquist_enclosed(r, M_halo, a_halo)
    v_circ = np.sqrt(G * M_enc / r)
    vx = -v_circ * np.sin(theta)
    vy = v_circ * np.cos(theta)
    velocities = np.column_stack([vx, vy]).astype(float)
    velocities += velocity_noise * v_circ[:, None] * rng.normal(size=(n_particles, 2))

    if m_particle is None:
        m_particle = 1.0 / n_total
    masses_disk = np.full(n_particles, m_particle, dtype=float)

    positions = np.vstack([star_pos, positions])
    velocities = np.vstack([star_vel, velocities])
    masses = np.concatenate([star_mass, masses_disk])

    return ParticleState(positions=positions, velocities=velocities, masses=masses)


def make_cloud_2d(
    n_particles: int,
    seed: int | None = None,
    M_star: float = 1.0,
    m_particle: float | None = None,
    r_max: float = 2.0,
    angular_fraction: float = 0.5,
    G: float = G_DEFAULT,
    M_halo: float = 0.0,
    a_halo: float = 5.0,
) -> ParticleState:
    rng = np.random.default_rng(seed)
    n_total = n_particles + 1

    star_pos = np.zeros((1, 2), dtype=float)
    star_vel = np.zeros((1, 2), dtype=float)
    star_mass = np.array([M_star], dtype=float)

    r = np.sqrt(rng.random(n_particles, dtype=float)) * r_max
    theta = 2.0 * np.pi * rng.random(n_particles, dtype=float)
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    positions = np.column_stack([x, y]).astype(float)

    r_safe = np.maximum(r, 1e-8)
    M_enc = M_star + _hernquist_enclosed(r_safe, M_halo, a_halo)
    v_circ = np.sqrt(G * M_enc / r_safe)
    v_tangent = angular_fraction * v_circ
    vx = -v_tangent * np.sin(theta)
    vy = v_tangent * np.cos(theta)
    velocities = np.column_stack([vx, vy]).astype(float)

    if m_particle is None:
        m_particle = 1.0 / n_total
    masses_disk = np.full(n_particles, m_particle, dtype=float)

    positions = np.vstack([star_pos, positions])
    velocities = np.vstack([star_vel, velocities])
    masses = np.concatenate([star_mass, masses_disk])

    return ParticleState(positions=positions, velocities=velocities, masses=masses)


def make_disk_3d(
    n_particles: int,
    seed: int | None = None,
    M_star: float = 1.0,
    m_particle: float | None = None,
    r_min: float = 0.5,
    r_max: float = 2.0,
    thickness: float = 0.05,
    G: float = G_DEFAULT,
    velocity_noise: float = 0.02,
    position_noise: float = 0.01,
    M_halo: float = 0.0,
    a_halo: float = 5.0,
) -> ParticleState:
    rng = np.random.default_rng(seed)
    n_total = n_particles + 1

    star_pos = np.zeros((1, 3), dtype=float)
    star_vel = np.zeros((1, 3), dtype=float)
    star_mass = np.array([M_star], dtype=float)

    r2_min, r2_max = r_min * r_min, r_max * r_max
    r2 = r2_min + (r2_max - r2_min) * rng.random(n_particles, dtype=float)
    r = np.sqrt(r2)
    theta = 2.0 * np.pi * rng.random(n_particles, dtype=float)

    x = r * np.cos(theta)
    y = r * np.sin(theta)
    z = thickness * (rng.random(n_particles, dtype=float) - 0.5)
    positions = np.column_stack([x, y, z]).astype(float)
    positions += position_noise * rng.normal(size=(n_particles, 3))

    r_safe = np.maximum(r, 1e-8)
    M_enc = M_star + _hernquist_enclosed(r_safe, M_halo, a_halo)
    v_circ = np.sqrt(G * M_enc / r_safe)
    vx = -v_circ * np.sin(theta)
    vy = v_circ * np.cos(theta)
    vz = velocity_noise * v_circ * rng.normal(size=n_particles)
    velocities = np.column_stack([vx, vy, vz]).astype(float)
    velocities += velocity_noise * v_circ[:, None] * rng.normal(size=(n_particles, 3))

    if m_particle is None:
        m_particle = 1.0 / n_total
    masses_disk = np.full(n_particles, m_particle, dtype=float)

    positions = np.vstack([star_pos, positions])
    velocities = np.vstack([star_vel, velocities])
    masses = np.concatenate([star_mass, masses_disk])

    return ParticleState(positions=positions, velocities=velocities, masses=masses)


def make_cloud_3d(
    n_particles: int,
    seed: int | None = None,
    M_star: float = 1.0,
    m_particle: float | None = None,
    r_max: float = 2.0,
    angular_fraction: float = 0.5,
    G: float = G_DEFAULT,
    M_halo: float = 0.0,
    a_halo: float = 5.0,
) -> ParticleState:
    rng = np.random.default_rng(seed)
    n_total = n_particles + 1

    star_pos = np.zeros((1, 3), dtype=float)
    star_vel = np.zeros((1, 3), dtype=float)
    star_mass = np.array([M_star], dtype=float)

    u = rng.random(n_particles, dtype=float)
    r = (u ** (1.0 / 3.0)) * r_max
    phi = np.arccos(2.0 * rng.random(n_particles, dtype=float) - 1.0)
    theta = 2.0 * np.pi * rng.random(n_particles, dtype=float)
    x = r * np.sin(phi) * np.cos(theta)
    y = r * np.sin(phi) * np.sin(theta)
    z = r * np.cos(phi)
    positions = np.column_stack([x, y, z]).astype(float)

    r_safe = np.maximum(r, 1e-8)
    M_enc = M_star + _hernquist_enclosed(r_safe, M_halo, a_halo)
    v_circ = np.sqrt(G * M_enc / r_safe)
    v_tangent = angular_fraction * v_circ
    vx = -v_tangent * np.sin(theta)
    vy = v_tangent * np.cos(theta)
    vz = np.zeros(n_particles, dtype=float)
    velocities = np.column_stack([vx, vy, vz]).astype(float)

    if m_particle is None:
        m_particle = 1.0 / n_total
    masses_disk = np.full(n_particles, m_particle, dtype=float)

    positions = np.vstack([star_pos, positions])
    velocities = np.vstack([star_vel, velocities])
    masses = np.concatenate([star_mass, masses_disk])

    return ParticleState(positions=positions, velocities=velocities, masses=masses)
