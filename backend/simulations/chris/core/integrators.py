"""Time integration methods for the gravity simulation."""

from __future__ import annotations

from .state import AccelerationFn, ParticleState


def leapfrog_step(
    state: ParticleState,
    dt: float,
    accel_fn: AccelerationFn,
) -> ParticleState:
    """Leapfrog (kick-drift-kick) integrator."""
    a0 = accel_fn(state)
    v_half = state.velocities + 0.5 * dt * a0

    pos_new = state.positions + dt * v_half
    mid_state = ParticleState(positions=pos_new, velocities=v_half, masses=state.masses)

    a1 = accel_fn(mid_state)
    v_new = v_half + 0.5 * dt * a1

    return ParticleState(positions=pos_new, velocities=v_new, masses=state.masses)
