# Gravitational Systems Simulator: Chris's Sections

**ASTR 311 Group Presentation**
Brad, Chris, Ethan, Jasper

---

## Simulating the Big Bang with N-Body Methods

The three-body problem generalises naturally to the N-body problem: every particle feels the gravitational pull of every other particle. The physics does not change going from 3 bodies to 5,000, but the computational cost scales as N squared, meaning each additional body dramatically increases the number of pairwise interactions (Binney & Tremaine, 2008, Ch. 2).

This scaling is what makes cosmological simulation so demanding. The Millennium Simulation used over 10 billion dark matter particles on supercomputers to reproduce the large-scale structure of the universe: filaments, voids, and galaxy clusters emerging from nearly uniform initial conditions after the Big Bang (Springel et al., 2005).

The goal is always the same: start from nearly uniform matter and watch gravity build structure. Even with months of compute time, the outcome depends critically on two things: the initial conditions and the expansion rate of space (Springel, 2005). Our project applies the same concept at a much smaller scale, thousands of particles on a personal server, to explore how gravitational dynamics and cosmological expansion shape the evolution of matter.


## Attempt 1: Newtonian Gravity Simulation

### The Physical Setup

For my first simulation, I modelled a dense cloud of 5,000 particles expanding outward under mutual Newtonian gravity. Forces are calculated using a softened inverse-square law and time integration is performed using the leapfrog method, a symplectic integrator that conserves energy over long runs unlike simpler methods such as forward Euler (Hairer, Lubich & Wanner, 2003).

Gravitational softening is a standard technique in N-body simulation. By adding a small length scale epsilon to the denominator of the force law, we prevent the unphysical singularity that occurs when two particles pass arbitrarily close. Without softening, close encounters produce numerically infinite accelerations that blow up the simulation. The softened force law is:

**a_i = G * sum_{j != i} m_j * (r_j - r_i) / (|r_j - r_i|^2 + epsilon^2)^(3/2)**

This is the standard Plummer softening formulation used in astrophysical N-body codes (Dehnen & Read, 2011). The softening length epsilon sets the spatial resolution of the simulation; below this scale, gravitational forces are artificially weakened. In our simulation, epsilon = 0.05 in code units.

### Computational Scale

Each timestep requires evaluating the gravitational acceleration on every particle due to every other particle, an O(N^2) calculation. For N = 5,000 particles over 20,000 timesteps:

N^2 x S = 5000^2 x 20,000 = 5 x 10^11 force evaluations

This took approximately 50 hours of wall-clock time on a single GPU. Production cosmological codes like GADGET-2 use tree algorithms to reduce the scaling to O(N log N), which is essential when N exceeds roughly 10^5 (Springel, 2005).

### What Emerged

The simulation produced several physically realistic phenomena:

**Gravitational clumping.** Particles slightly closer together attracted more neighbours, creating a runaway process of gravitational collapse. Dense knots formed and grew over time, the same hierarchical clustering that drives globular cluster and galaxy formation (Binney & Tremaine, 2008, Ch. 4).

**Slingshot ejections.** During close multi-body encounters, energy exchange can accelerate one particle to escape velocity while the others become more tightly bound. This dynamical ejection mechanism is the same process responsible for hypervelocity stars ejected from the Galactic centre (Binney & Tremaine, 2008, Ch. 8).

**A bound rotating core.** After the initial expansion, a subset of particles remained gravitationally bound, settling into a rotating structure. Angular momentum conservation forces infalling material into a disk-like configuration rather than a simple point collapse (Binney & Tremaine, 2008, Ch. 4).

### The Problem

While these dynamics are physically real, the model has a fundamental conceptual flaw as an analogy for the Big Bang: it has a centre and an edge. Particles move through a fixed, pre-existing space, radiating outward from a central point.

The Big Bang is not an explosion of matter into pre-existing space. Space itself expanded, and continues to expand, carrying matter with it. There is no centre, no edge, and no preferred vantage point. Every observer sees every other galaxy receding (Binney & Tremaine, 2008; ASTR 311 course notes). This distinction motivated the second simulation.


## Attempt 1: The Physics Engine

The force law is the same structure as the three-body equations presented by Ethan, generalised to sum over all N particles. Each particle i feels the gravitational acceleration due to every other particle j:

**a_i = G * sum_{j != i} m_j * (r_j - r_i) / (|r_j - r_i|^2 + epsilon^2)^(3/2)**

The key components:

- **G** is the gravitational constant, set to 1 in dimensionless code units for numerical stability
- **epsilon** is the softening length, preventing singularities at close approach and mimicking the finite size of real astrophysical objects (Dehnen & Read, 2011)
- The **denominator** uses the 3/2 power of the softened distance squared, giving the correct inverse-square law at large separations while remaining finite at small separations

The complexity is O(N^2) because every particle interacts with every other, giving N(N-1)/2 unique pairs per step. For 5,000 particles over 20,000 steps this totalled roughly 5 x 10^11 force evaluations, requiring about 50 hours of computation.

Time integration used the leapfrog (kick-drift-kick) method, a symplectic integrator. Symplectic integrators are preferred for gravitational dynamics because they conserve a quantity close to the true Hamiltonian, preventing the artificial energy drift that plagues non-symplectic methods over long integration times (Hairer, Lubich & Wanner, 2003).


## Attempt 2: Spacetime Expansion

### The Conceptual Framework

The second simulation addresses the fundamental flaw of the first: instead of particles flying through fixed space, space itself grows over time. This is described by the scale factor a(t), a dimensionless number that multiplies all distances. When a(t) doubles, every distance between every pair of particles doubles, not because they moved, but because the space between them stretched (Friedmann, 1922).

Particles sit at fixed "comoving coordinates," like dots drawn on a balloon. As the balloon inflates, the dots move apart even though they are not moving on the surface. The physical distance between any two particles is their comoving separation multiplied by a(t).

This framework produces Hubble's Law: the recession velocity of any distant object is proportional to its distance:

**v_recession = H(t) x d**

where H(t) = a'(t)/a(t) is the expansion rate at time t. This is not motion through space but the stretching of space itself. There is no centre and no edge: every observer sees every other galaxy receding, and farther apart means faster recession because there is more expanding space in between (Binney & Tremaine, 2008).

### The Friedmann Equation

The evolution of the scale factor is governed by the Friedmann equation, derived from general relativity applied to a homogeneous, isotropic universe (Friedmann, 1922):

**H^2(a) = H_0^2 [ Omega_r / a^4 + Omega_m / a^3 + Omega_Lambda ]**

H_0 is the present-day Hubble constant, and the three Omega terms represent the fractional energy densities of radiation, matter, and dark energy respectively. Each term dominates at a different epoch:

| Era | Dominant Term | Expansion Behaviour | Physical Reason |
|-----|--------------|-------------------|----------------|
| Inflation | Vacuum energy (Lambda) | Exponential growth | Constant H drives runaway expansion |
| Radiation | Omega_r / a^4 | Decelerating | Photon pressure dilutes as a^-4, H drops quickly |
| Matter | Omega_m / a^3 | Slowing | Gravity wins over expansion; structure forms |
| Dark Energy | Omega_Lambda | Accelerating | Lambda is constant while matter dilutes; gravity loses |

Our simulation implements this equation directly: at each timestep we compute H(t) from the current scale factor and update the expansion rate. The initial Omega parameters determine the entire subsequent evolution, which is why we say the expansion rate is the initial condition that sets everything.


## What The Models Show, and What They Can't

The Newtonian "explosion" model captures real local gravitational dynamics: clumping, ejection, and bound structure formation are all physically accurate. However, it treats expansion as particles moving through fixed space, giving the system a centre, an edge, and a preferred reference frame that do not exist in the real universe.

The spacetime expansion model captures the correct conceptual framework: Hubble flow, no preferred centre, and dependence on Friedmann equation parameters. However, at our scale (~5,000 particles) it cannot reproduce the filamentary "cosmic web" that emerges in production simulations with billions of particles (Springel et al., 2005).

Neither model includes radiation pressure, thermodynamics, or baryonic physics, all of which are essential for reproducing detailed observed structure. Real cosmological simulations require roughly 10^10 particles and months of supercomputer time (Springel, 2005).

What both models demonstrate is that the initial conditions completely determine the outcome. The same physics (gravity) produces radically different structures depending on how the simulation begins. Initial conditions determine everything.

### Live Demonstrations

Both simulations are available as interactive web applications:

- **Newtonian N-body simulation:** gravity.chrislawrence.ca
- **Spacetime expansion simulation:** astr311.chrislawrence.ca


---

## Factual References

Binney, J. & Tremaine, S. (2008). *Galactic Dynamics* (2nd ed.). Princeton University Press.

Dehnen, W. & Read, J.I. (2011). N-body simulations of gravitational dynamics. *European Physical Journal Plus*, 126, 55. DOI: 10.1140/epjp/i2011-11055-3.

Friedmann, A. (1922). Uber die Krummung des Raumes. *Zeitschrift fur Physik*, 10(1), 377-386. DOI: 10.1007/BF01332580.

Hairer, E., Lubich, C. & Wanner, G. (2003). Geometric numerical integration illustrated by the Stormer-Verlet method. *Acta Numerica*, 12, 399-450. DOI: 10.1017/S0962492902000144.

Springel, V. (2005). The cosmological simulation code GADGET-2. *Monthly Notices of the Royal Astronomical Society*, 364, 1105-1134. DOI: 10.1111/j.1365-2966.2005.09655.x.

Springel, V. et al. (2005). Simulations of the formation, evolution and clustering of galaxies and quasars. *Nature*, 435(7042), 629-636. DOI: 10.1038/nature03597.

ASTR 311 Course Notes: Big Bang; Cosmology. Vancouver Island University.


## Image References

Figure 1 (Slide 10): Millennium Simulation visualization showing large-scale structure of the universe. Springel, V. et al. (2005). Retrieved from the Millennium Simulation Project, Max Planck Institute for Astrophysics.

Figure 2 (Slide 13): Screenshot of the Newtonian N-body simulation web viewer showing gravitational clumping and ejection. Original work by Chris Lawrence. Available at gravity.chrislawrence.ca.

Figure 3 (Slide 15): Screenshot of the spacetime expansion simulation showing Friedmann-driven expansion. Original work by Chris Lawrence. Available at astr311.chrislawrence.ca.
