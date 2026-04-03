import numpy as np
import math

G_SI = 6.67430e-11  # Gravitational constant in m^3 kg^-1 s^-2

class Body:
    def __init__(self, mass, position, velocity, name=""):
        self.mass = mass
        self.position = np.array(position, dtype=float)
        self.velocity = np.array(velocity, dtype=float)
        self.name = name

def gravitational_acceleration(body, bodies, G, softening=0.0):
    acceleration = np.zeros(2)
    for other in bodies:
        if other is not body:
            r_vector = other.position - body.position
            r2 = np.dot(r_vector, r_vector) + softening * softening
            r = np.sqrt(r2)
            if r > 1e-10:
                acceleration += G * other.mass / (r2 * r) * r_vector
    return acceleration

def simulate(bodies, dt, steps, G=None, softening=0.0, record_every=1):
    """Simulate using Velocity Verlet integrator.
    softening: Plummer softening length to prevent close-encounter blowups.
    record_every: save state every N steps to reduce output size."""
    if G is None:
        G = G_SI
    history = []
    accelerations = [gravitational_acceleration(body, bodies, G, softening) for body in bodies]

    for step in range(steps):
        if step % record_every == 0:
            state = {
                "time": step * dt,
                "bodies": [
                    {
                        "name": body.name,
                        "position": body.position.tolist(),
                        "velocity": body.velocity.tolist(),
                        "mass": body.mass
                    } for body in bodies
                ]
            }
            history.append(state)

        for i, body in enumerate(bodies):
            body.position += body.velocity * dt + 0.5 * accelerations[i] * dt**2

        new_accelerations = [gravitational_acceleration(body, bodies, G, softening) for body in bodies]

        for i, body in enumerate(bodies):
            body.velocity += 0.5 * (accelerations[i] + new_accelerations[i]) * dt

        accelerations = new_accelerations

    return history

def create_three_body_problem(positions=None, velocities=None, masses=None):
    """Create a chaotic three-body problem.
    Default: three bodies at vertices of a triangle, starting near rest.
    User can override positions, velocities, masses."""
    n = 3
    if masses is None:
        masses = [3.0, 4.0, 5.0]
    if positions is None:
        # Pythagorean three-body problem: vertices of a 3-4-5 right triangle
        positions = [[1.0, 3.0], [-2.0, -1.0], [1.0, -1.0]]
    if velocities is None:
        # Start from rest — gravity alone drives the chaos
        velocities = [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]

    # Center on COM and zero COM velocity
    total_mass = sum(masses)
    com_pos = np.zeros(2)
    com_vel = np.zeros(2)
    for i in range(n):
        com_pos += masses[i] * np.array(positions[i])
        com_vel += masses[i] * np.array(velocities[i])
    com_pos /= total_mass
    com_vel /= total_mass
    positions = [list(np.array(positions[i]) - com_pos) for i in range(n)]
    velocities = [list(np.array(velocities[i]) - com_vel) for i in range(n)]

    bodies = [
        Body(masses[i], positions[i], velocities[i], f"Body {i+1}")
        for i in range(n)
    ]
    return bodies

def create_pluto_system():
    """Full Pluto system: Pluto + Charon + Nix + Styx + Kerberos + Hydra.
    All bodies in the barycenter frame with circular orbit velocities."""
    G = G_SI
    M_pluto = 1.303e22
    M_charon = 1.586e21
    M_nix = 4.5e16
    M_styx = 7.5e15
    M_kerberos = 1.65e16
    M_hydra = 4.8e16

    M_total = M_pluto + M_charon

    # Pluto-Charon orbital distance
    d_pc = 1.9571e7  # 19,571 km in meters

    # Barycenter distances
    r_pluto = M_charon * d_pc / M_total
    r_charon = M_pluto * d_pc / M_total

    # Orbital velocity
    v_orbital = math.sqrt(G * M_total / d_pc)
    v_pluto = M_charon / M_total * v_orbital
    v_charon = M_pluto / M_total * v_orbital

    # Small moon semi-major axes (m)
    r_styx = 4.2656e7
    r_nix = 4.8694e7
    r_kerberos = 5.7783e7
    r_hydra = 6.4738e7

    # Circular orbit velocities
    v_styx = math.sqrt(G * M_total / r_styx)
    v_nix = math.sqrt(G * M_total / r_nix)
    v_kerberos = math.sqrt(G * M_total / r_kerberos)
    v_hydra = math.sqrt(G * M_total / r_hydra)

    # Starting angles (spread moons around orbits)
    a_styx = math.radians(45)
    a_nix = math.radians(135)
    a_kerberos = math.radians(225)
    a_hydra = math.radians(315)

    bodies = [
        Body(M_pluto, [-r_pluto, 0], [0, -v_pluto], "Pluto"),
        Body(M_charon, [r_charon, 0], [0, v_charon], "Charon"),
        Body(M_styx,
             [r_styx * math.cos(a_styx), r_styx * math.sin(a_styx)],
             [-v_styx * math.sin(a_styx), v_styx * math.cos(a_styx)],
             "Styx"),
        Body(M_nix,
             [r_nix * math.cos(a_nix), r_nix * math.sin(a_nix)],
             [-v_nix * math.sin(a_nix), v_nix * math.cos(a_nix)],
             "Nix"),
        Body(M_kerberos,
             [r_kerberos * math.cos(a_kerberos), r_kerberos * math.sin(a_kerberos)],
             [-v_kerberos * math.sin(a_kerberos), v_kerberos * math.cos(a_kerberos)],
             "Kerberos"),
        Body(M_hydra,
             [r_hydra * math.cos(a_hydra), r_hydra * math.sin(a_hydra)],
             [-v_hydra * math.sin(a_hydra), v_hydra * math.cos(a_hydra)],
             "Hydra"),
    ]
    return bodies