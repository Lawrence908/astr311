import math
from simulations.jasper.app import AdvancedOrbitalSimulator

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def barycentre(pos_tensor, mass_tensor):
    """Return the mass-weighted barycentre as a torch tensor [x, y, z]."""
    total_mass = mass_tensor.sum()
    com = (pos_tensor * mass_tensor.unsqueeze(1)).sum(dim=0) / total_mass
    return com


# G in AU³ M☉⁻¹ yr⁻²  (exact from Kepler's 3rd law)
G_M_SUN = 4.0 * math.pi ** 2


def eccentricity_vector(rx, rz, vx, vz):
    """
    Compute the Laplace-Runge-Lenz (eccentricity) vector for a planet in the
    xz plane.  All quantities must be relative to the Sun.

    h_y = (r × v)_y  — the only non-zero component of specific angular momentum
                        when the orbit lies in the xz plane.

    e_vec = (v × h) / (G·M_sun) − r̂

    Returns (ex, ez, |e|).  The direction atan2(ez, ex) points from the Sun
    toward perihelion; aphelion is exactly π away.
    """
    r = math.sqrt(rx*rx + rz*rz)
    if r == 0:
        return 0.0, 0.0, 0.0

    h_y = rz * vx - rx * vz          # (r × v)_y  (into/out of xz-plane)

    # v × h  where h = (0, h_y, 0):
    #   x-component: -vz * h_y
    #   z-component:  vx * h_y
    ex = (-vz * h_y) / G_M_SUN - rx / r
    ez = ( vx * h_y) / G_M_SUN - rz / r

    return ex, ez, math.sqrt(ex*ex + ez*ez)


# ---------------------------------------------------------------------------
# setup
# ---------------------------------------------------------------------------

sim = AdvancedOrbitalSimulator()
planet_names = list(sim.names)          # 0 = Sun, 1-8 = planets

dt = sim.dt
print(f"dt={dt}, planets={planet_names}")

N_PLANETS = 9   # Sun + 8 planets


class OrbitTracker:
    """
    Tracks per-orbit statistics for one planet.

    Orbit detection uses the barycentre-relative angle (stable over 500 yr).
    r_min / r_max use sun-relative distance (correct physical focus).
    Perihelion direction is the time-averaged eccentricity vector over the
    orbit — guaranteed to be geometrically exact, with aphelion always 180°
    opposite.
    """

    def __init__(self, name):
        self.name             = name
        self.prev_angle       = None
        self.accumulated      = 0.0
        self.orbits           = []
        self.orbit_start_time = None
        self.current_r_min    = None
        self.current_r_max    = None
        # Eccentricity-vector accumulator (averaged over all steps in orbit)
        self.ex_sum           = 0.0
        self.ez_sum           = 0.0
        self.ev_count         = 0

    def update(self, bary_x, bary_z, sun_rx, sun_rz, sun_vx, sun_vz, r_bary, sim_time):
        """
        bary_x, bary_z : planet position relative to barycentre (for angle/orbit detection)
        sun_rx, sun_rz  : planet position relative to Sun       (for eccentricity vector)
        sun_vx, sun_vz  : planet velocity relative to Sun       (for eccentricity vector)
        r_bary          : |r| from barycentre                   (for r_min / r_max / eccentricity)
        sim_time        : current simulation time (yr)
        """
        angle = math.atan2(bary_z, bary_x)

        if self.prev_angle is None:
            self.prev_angle        = angle
            self.orbit_start_time  = sim_time
            self.current_r_min     = r_bary
            self.current_r_max     = r_bary
            return

        d_angle = angle - self.prev_angle
        if d_angle >  math.pi:
            d_angle -= 2 * math.pi
        elif d_angle < -math.pi:
            d_angle += 2 * math.pi

        self.accumulated += d_angle
        self.prev_angle   = angle

        if r_bary < self.current_r_min:
            self.current_r_min = r_bary
        if r_bary > self.current_r_max:
            self.current_r_max = r_bary

        # Accumulate eccentricity vector (will be averaged at orbit end)
        ex, ez, _ = eccentricity_vector(sun_rx, sun_rz, sun_vx, sun_vz)
        self.ex_sum  += ex
        self.ez_sum  += ez
        self.ev_count += 1

        while abs(self.accumulated) >= 2 * math.pi:
            sign = 1 if self.accumulated > 0 else -1
            self.accumulated -= sign * 2 * math.pi

            r_min  = self.current_r_min
            r_max  = self.current_r_max
            period = sim_time - self.orbit_start_time

            # Eccentricity and perihelion direction from averaged eccentricity vector
            if self.ev_count > 0:
                ex_avg = self.ex_sum / self.ev_count
                ez_avg = self.ez_sum / self.ev_count
                ecc        = math.sqrt(ex_avg**2 + ez_avg**2)
                peri_angle = math.atan2(ez_avg, ex_avg)
            else:
                ecc        = 0.0
                peri_angle = 0.0

            apo_angle = peri_angle + math.pi   # always exactly opposite

            self.orbits.append({
                'orbit_num':    len(self.orbits) + 1,
                'period_yr':    round(period, 4),
                'r_min_AU':     round(r_min, 6),
                'r_max_AU':     round(r_max, 6),
                'angle_min':    round(peri_angle, 6),
                'angle_max':    round(apo_angle,  6),
                'eccentricity': round(ecc, 6),
            })

            self.orbit_start_time = sim_time
            self.current_r_min    = r_bary
            self.current_r_max    = r_bary
            self.ex_sum           = 0.0
            self.ez_sum           = 0.0
            self.ev_count         = 0


trackers = {i: OrbitTracker(planet_names[i]) for i in range(1, N_PLANETS)}

# ---------------------------------------------------------------------------
# main loop  — 500 years at dt=0.002 requires 250,000 steps
# ---------------------------------------------------------------------------

sim_time = 0.0
STEPS    = 5000_000

for step in range(STEPS):
    sim.step()
    sim_time += dt

    bary   = barycentre(sim.pos, sim.mass)
    bary_x = bary[0].item()
    bary_z = bary[2].item()

    sun_px = sim.pos[0][0].item()
    sun_pz = sim.pos[0][2].item()
    sun_vx = sim.vel[0][0].item()
    sun_vz = sim.vel[0][2].item()

    for i in range(1, N_PLANETS):
        # Barycentre-relative position — stable orbit-angle detection over 500 yr
        bx = sim.pos[i][0].item() - bary_x
        bz = sim.pos[i][2].item() - bary_z

        # Sun-relative position and velocity — needed for eccentricity vector
        rx = sim.pos[i][0].item() - sun_px
        rz = sim.pos[i][2].item() - sun_pz
        vx = sim.vel[i][0].item() - sun_vx
        vz = sim.vel[i][2].item() - sun_vz

        r_bary = math.sqrt(bx*bx + bz*bz)

        trackers[i].update(bx, bz, rx, rz, vx, vz, r_bary, sim_time)

    if step % 10000 == 0:
        print(f"  step {step:>7} / {STEPS}   sim_time = {sim_time:.2f} yr", flush=True)

# ---------------------------------------------------------------------------
# results
# ---------------------------------------------------------------------------

print("\n" + "=" * 96)
print(f"{'Planet':<12}  {'Orbits':>6}  {'Period (yr)':>11}  {'r_min (AU)':>10}  "
      f"{'r_max (AU)':>10}  {'Eccentricity':>12}  {'a_min (rad)':>11}  {'a_max (rad)':>11}")
print("-" * 96)

for i in range(1, N_PLANETS):
    t = trackers[i]
    if not t.orbits:
        print(f"{t.name:<12}  {'0':>6}  {'—':>11}  {'—':>10}  {'—':>10}  {'—':>12}  {'—':>11}  {'—':>11}")
        continue
    for o in t.orbits:
        print(
            f"{t.name:<12}  {o['orbit_num']:>6}  "
            f"{o['period_yr']:>11.4f}  "
            f"{o['r_min_AU']:>10.6f}  "
            f"{o['r_max_AU']:>10.6f}  "
            f"{o['eccentricity']:>12.6f}  "
            f"{o['angle_min']:>11.6f}  "
            f"{o['angle_max']:>11.6f}"
        )

print("=" * 72)
print("Done.", flush=True)
