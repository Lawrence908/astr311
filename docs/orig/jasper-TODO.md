# Jasper — Presentation TODO
## Section: The Solar System, Spacetime & Gravitational Waves

---

## 1. Takeaway for the class
Einstein didn't just refine Newton — he changed what gravity *is*. Post-Newtonian corrections explain Mercury's orbit, predict gravitational waves, and reshape how we simulate planetary systems. Our solar system sim is the most physically advanced of the three, and the spacetime visualization makes the abstract concept of curved space tangible.

**Note on GW/Brad overlap:** The meeting transcript (~lines 271–284) has Brad describing gravitational waves as his topic. Per the presentation assignment, GR/gravitational waves belong here under Jasper. If Brad drafted any GW content, merge it into your section and keep Brad focused on orbital metrics.

---

## 2. Slide storyboard (~5 slides)

**Slide 1 — History: Einstein and post-Newtonian gravity**
- Newton's gravity: instantaneous action at a distance, no speed limit
- Einstein (~1915): gravity is the curvature of spacetime; massive objects warp the fabric
- Mercury's perihelion: moves 43"/century beyond Newton's prediction — explained exactly by GR
- Key shift: from "force" to "geometry"

**Slide 2 — Gravitational waves**
- GR predicts: accelerating massive objects create ripples in spacetime (gravitational waves)
- Predicted 1916; took 100 years to detect
- LIGO (2015): first direct detection — two black holes merging, 1.3 billion light-years away
- Strain: 10^-21 — a change in length smaller than a proton across 4 km
- Why it matters: new way to "see" the universe; confirms spacetime is real and dynamic

**Slide 3 — Spacetime curvature: what our visualization shows**
- Flamm paraboloid: embedding diagram of the Schwarzschild metric (1916)
- z-displacement ∝ -2√(r_s · r) where r_s = 2GM/c² (Schwarzschild radius)
- Shows how space is "dented" around a massive body — particles follow curved paths through this geometry
- Our sim computes this on a 64×64 GPU grid in real time

**Slide 4 — Demo**
- `jaspersim`: full solar system, real AU/M☉/yr units
- Show: orbit trails, spacetime grid deforming, Mercury's precession over time
- Point out: GPU-accelerated Yoshida 4th-order integrator (better energy conservation than leapfrog)
- 1PN correction: small relativistic term added to force law — reproduces Mercury 43"/century
- Note artificial starting condition (planets colinear) — sets up Brad's analysis

**Slide 5 — Limitations & bridge to Brad**
- Starting conditions: all planets at t=0 in a line — not where they actually are
- 1PN, not full GR — good enough for planetary-scale, not for neutron stars/black holes
- No thermodynamics, no radiation pressure
- *IC thread:* "We had to start somewhere. Brad is going to show you exactly what that choice did to our orbital data."

---

## 3. Demo / replay checklist

- [ ] Confirm `jaspersim` running cleanly, GPU available on presentation machine
- [ ] Enable spacetime grid visualization (Flamm paraboloid)
- [ ] Enable orbit trails
- [ ] Let simulation run long enough to show Mercury precession accumulating
- [ ] Keep simulation at default solar system (don't add extra bodies for presentation — time is tight)
- [ ] Optional: after Brad's section, invite class to add a body / black hole if time allows

---

## 4. Dependencies on others

- **Brad**: keep planets starting colinear (don't adjust ICs before presentation); this is deliberate — Brad's analysis uses it as a talking point
- **Chris**: clean handoff from Big Bang ("from cosmic scale back to our own backyard")
- **Slides**: already created Google Slides template (~20 slides shell); fill in your ~5 slides and share for others to add theirs

---

## 5. Risks / mitigations

| Risk | Mitigation |
|------|-----------|
| GPU not available on presentation laptop | Yoshida integrator falls back to CPU — slower but functional |
| Spacetime grid compute stalls physics | Grid runs on dedicated daemon thread; physics won't stall |
| LIGO/GW content overlaps with Brad's prior work | Merge Brad's GW content here; redirect Brad to metrics only |
| 5 min feels short for GR + GW + demo | History (slides 1-2) can be combined; demo is the centerpiece |

---

## 6. References

- Meeting transcript lines 310–311 (post-Newtonian / GR angle), 265–274 (history → sim pattern), 672–740 (IC discussion, planets in line)
- Einstein, A. (1915). General Theory of Relativity
- LIGO Scientific Collaboration (2016). *Observation of Gravitational Waves from a Binary Black Hole Merger*. PRL 116, 061102
- Schwarzschild, K. (1916). Flamm paraboloid / Schwarzschild metric
- ASTR 311 course notes: relativity section
