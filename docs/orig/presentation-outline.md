# Gravitational Systems — The Human Experience
## Rough Draft Presentation Outline

**ASTR 311 Group Presentation | ~20 minutes**
**Order:** Ethan → Chris → Jasper → Brad → Group close

---

### Narrative arc
A chronological ride through humanity's discovery and simulation of gravity:
- Newton's classical mechanics (small-N)
- Cosmic-scale N-body (Big Bang)
- Einstein's post-Newtonian refinements (Solar System / GR)
- What the metrics actually tell us (Validation)

**Unifying thread:** *Initial conditions matter* — surfaces in every segment.
**Tone:** We built cool toy models. Disclaimers are a feature, not a bug. This is how science works.

**Rubric alignment:** Teaching ASTR 311 content not fully covered in lectures; acknowledging gaps demonstrates understanding rather than hiding it.

---

## Section 1 — Hook (~1 min, Ethan leads)

- Gravity: the most universally felt force in human experience
- Everything from standing up to the Big Bang traces back to it
- Transition: "Let's go back to where our understanding started..."

---

## Section 2 — Ethan: The Three Body Problem (~5 min)

**Pattern:** History → Science → Demo → Compare

**History**
- Newton & Kepler (~1600s): inverse-square law, two-body problem solved exactly
- Three bodies: immediately intractable — Euler, Lagrange, Poincaré reveal chaos (~1800s–1890s)
- Problem dates back to ~1500s; still unsolved in general form

**Science**
- Almost all initial conditions → chaotic, unpredictable trajectories
- Rare exceptions: Lagrange points, figure-8 orbit, Pluto system stability
- Our solar system is a *miracle* of stable initial conditions (ties to Brad's findings)

**Demo**
- `ethansim`: three-body chaotic run (Pythagorean configuration)
- Optional: Pluto system (Pluto + 5 moons around shared barycenter)
- Show sensitivity: small IC change → totally different trajectory

**Compare / Limits**
- Our sim: Velocity Verlet integrator, Newtonian only, softened gravity
- Real work: analytical solutions require centuries of effort; most cases just don't have them
- *Initial conditions thread:* "For almost every starting position, chaos. Which makes our solar system's stability remarkable."

**Handoff to Chris:** "Ethan showed us 3 bodies. What if N is 10^89?"

---

## Section 3 — Chris: The Big Bang (~5 min)

**Pattern:** History → Science → Demo → Compare

**History**
- N-body cosmological simulations: Millennium Simulation, Illustris, EAGLE — huge computational infrastructure
- Goal: understand large-scale structure (galaxies, filaments, voids) emerging from early-universe initial conditions
- These use billions of particles on supercomputers; ours uses hundreds on a laptop

**Science**
- Big Bang stages (gravity-relevant): inflation (rapid homologous expansion), quark-gluon era, nucleosynthesis, recombination (CMB — universe becomes transparent), structure formation (gravity wins, clumping begins)
- Language note: *not an explosion* — space itself expanded; no center, no edge
- Hubble-like expansion: v ∝ r (every point moving away from every other)

**Demo**
- `chrissim`: particles expanding radially outward, gravitational clumping visible over time
- Higher radial velocity → more physically accurate inflation (things don't clump immediately)
- Visual cues: opacity/fog for pre-recombination era, clumping as gravity eventually wins

**Compare / Limits**
- No dark matter, no thermodynamics, no radiation pressure — pure gravity toy
- Can't run long enough at scale to see realistic filamentary structure
- *Initial conditions thread:* "The expansion rate we choose completely changes what we see — just like in the real universe, initial conditions set everything."

**Handoff to Jasper:** "Chris showed N-body at cosmic scale. Now let's zoom in to our own solar system and add Einstein."

---

## Section 4 — Jasper: The Solar System & Spacetime (~5 min)

**Pattern:** History → Science → Demo → Compare

**History**
- Einstein & General Relativity (~1915): gravity is geometry, not force
- Mercury's perihelion precession: 43"/century unexplained by Newton, explained exactly by GR
- Gravitational waves: predicted 1916, detected by LIGO 2015 — ripples in spacetime from massive accelerating bodies

**Science**
- Post-Newtonian (1PN) corrections: small relativistic terms added to Newtonian gravity
- Spacetime curvature visualization: Flamm paraboloid — embedding diagram of the Schwarzschild metric
- Schwarzschild radius (r_s = 2GM/c²) sets the depth of the well

**Demo**
- `jaspersim`: full solar system, GPU-accelerated Yoshida 4th-order integrator
- Spacetime grid (Flamm paraboloid) deforming around massive bodies in real time
- Mercury perihelion precession: 43"/century reproduced
- Note: planets start colinear (artificial IC) — sets up Brad's analysis

**Compare / Limits**
- Our sim: 1PN correction, not full GR tensor field equations
- Starting conditions: all planets in a line on day 0 (not where they actually are)
- *Initial conditions thread:* "We had to start somewhere. Brad is going to show exactly what that choice cost us."

**Handoff to Brad:** "So those are our three simulations. Now let's talk about how they actually performed."

---

## Section 5 — Brad: Metric Analysis (~5 min)

**Pattern:** Hypothesis → Methodology → Findings → Explanation → Implications

**Hypothesis**
- Expected: near-circular orbits, fairly stable eccentricities, roughly matching real solar system
- Starting condition caveat: planets aligned → artificial periodicity expected

**Methodology**
- Read Jasper's simulation position outputs
- Track eccentricity of each planet *from the barycenter* (not the Sun) per complete orbit
- Record min/max eccentricity per orbit; plot over time

**Findings**
- Eccentricities vary significantly, correlating with barycenter shifts
- When Jupiter + Saturn align on same side: inner planets' orbits more elliptical (peaks)
- ~180-year repeating cycle — artifact of planets starting colinear
- Compare: real solar system eccentricities stable to 6 decimal places (Milankovitch cycles are much subtler)
- Perihelion analysis: sporadic results (near-circular orbits make perihelion ill-defined at this timescale)

**Explanation**
- Artificial starting condition → exaggerated alignment effects → amplified eccentricity swings
- Real solar system built up over billions of years of orbital settling, impacts, interactions
- Our model can't just "place planets" in real positions and get real behavior

**Implications / Limits**
- *Initial conditions thread:* "Everything Ethan said about sensitivity? We see it here. Different starting point → different results."
- Not a failure — it's the expected behavior of a simplified model
- Shows our understanding of what the sim is and isn't doing

---

## Section 6 — Group Close (~30-60s)

- Shared lesson: initial conditions matter at every scale (3 bodies, cosmic, solar)
- Toy models are how you build intuition before you get supercomputer time
- "The Human Experience" of gravity: from Newton scratching his head to LIGO detecting a black hole merger
- Optional: if time, open Jasper's sim for class interaction (add a body, black hole)

---

## Logistics

| Item | Deadline |
|------|----------|
| Individual slides uploaded to Google Drive | Sunday ~4–7 PM |
| Group run-through / rehearsal | Monday (time TBD) |
| Final quick run-through | Tuesday morning before class |

- Format: Google Slides (Jasper's space-themed template) + live sim tabs / pre-recorded video
- Laptop to projector: test connection before presenting
- Pre-load all simulation tabs before presenting (Chris's sim: ~1 min load for large JSON files)
- ~5 min per person; better over than under — can cut, can't add on the fly
