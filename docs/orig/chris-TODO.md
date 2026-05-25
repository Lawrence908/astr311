# Chris — Presentation TODO
## Section: The Big Bang (N-body cosmology)

---

## 1. Takeaway for the class
N-body simulation is how cosmologists study the Big Bang and large-scale structure. Our toy model captures the *gravity* part of cosmic expansion — inflation, gravitational clumping, the tension between expansion force and gravity. It can't replace a supercomputer, but it shows you the intuition behind the real thing.

---

## 2. Slide storyboard (~5 slides)

**Slide 1 — History: Big Bang simulations in the wild**
- Millennium Simulation (2005, 10 billion particles), Illustris, EAGLE, TNG — what they modeled and what they found
- Goal of these projects: reproduce filamentary large-scale structure (galaxies, voids, walls) from smooth early-universe ICs
- Key point: even with supercomputers, initial conditions + expansion rate are the dial that sets everything

**Slide 2 — Physics: Big Bang stages (gravity-relevant)**
- Inflation: rapid homologous expansion (v ∝ r), space itself expanding — NOT an explosion, no center, no edge
- Quark-gluon plasma / nucleosynthesis (temperature-driven, not our focus)
- Recombination (~380,000 years): universe cools enough for atoms to form, light can finally travel freely (CMB)
- Structure formation: gravity wins against expansion, matter starts clumping → galaxies, filaments, voids
- Our sim lives roughly at the inflation → structure formation boundary

**Slide 3 — Our simulation: what it does and doesn't model**
- What it does: homologous radial expansion + mutual gravity, leapfrog integrator, Plummer softening
- What it doesn't: radiation pressure, dark matter halo, thermodynamics, relativistic effects
- Why that's fine: this is a *gravity visualization*, not a cosmological calculator
- Language: "expansion", not "explosion"

**Slide 4 — Demo**
- Pre-load sim in a tab before presenting
- Show 2 runs if time allows: moderate expansion force (clumping visible) vs. high expansion force (more like real inflation)
- Point out: where gravity is winning (clumps forming), where expansion wins (particles escaping)
- Optional: opacity/fog visual for pre-recombination era

**Slide 5 — Comparison & honest gaps**
- Hubble constant: real expansion rate ~70 km/s/Mpc — our `v_radial` is a tuning knob analogy
- Real universe: particles don't noticeably clump for hundreds of millions of years; ours clumps fast (no pressure, wrong scale)
- That's the point: toy model shows gravitational intuition; production sim needs 10^10 particles and months of compute
- *IC thread:* "The expansion rate we choose completely changes what we see — just like the real universe."

---

## 3. Demo / replay checklist

- [ ] Pre-compute 2–3 good runs before presentation day (one already running as of April 2 — ~48+ hrs)
- [ ] Pick best run: want to see clear clumping without total central collapse
- [ ] Tune `v_radial` (~1.5–2.0) — higher is more physically accurate for inflation phase
- [ ] Add center reference point (sphere or crosshair at origin) so expanding particles have a visual anchor
- [ ] Optional: add opacity/fog layer for pre-recombination phase visual
- [ ] Optional: add color-by-local-density so clumping is visually obvious
- [ ] Pre-load simulation tab before presenting (large JSON files take ~1 min)
- [ ] Have a backup: screen recording of a good run, embeddable as video in slides
- [ ] Run simulation on own frontend (`chrissim`) — don't stress integrating into Jasper's before presentation

---

## 4. Dependencies on others

- **Jasper**: no hard dependencies for presentation; integration into unified app is a post-presentation goal
- **Brad**: no analysis of Big Bang sim required (too hard to define meaningful orbit metrics for N-body gas)
- **Ethan**: narrative handoff — Ethan ends with "3 bodies"; you open with "what if N = 10^89?"
- **Slides**: Jasper's Google Slides template (~20 slides shell); fill in your ~5 slides

---

## 5. Risks / mitigations

| Risk | Mitigation |
|------|-----------|
| Sim takes too long to load live | Pre-record video; have tab pre-loaded |
| Clumping not visible in chosen run | Tune `v_radial` lower; use more particles with smaller dt |
| Physics too complex to explain in 5 min | Lead with visual intuition; save math for "if asked" |
| "Why does it clump in the middle?" question | Prepared answer: softening limits singularity; central clump is a toy-model artifact of starting in a small sphere |
| Running out of time | Slide 4 (demo) is the one to cut short; slides 1 and 5 are most important for rubric |

---

## 6. References

- Meeting transcript lines 289–292 (Big Bang sim history angle), 777–804 (well-mixed / clumping metrics), 1123–1124 (not an "explosion"), 1218–1250 (inflation phases, opacity era), 1303–1315 (goals for weekend improvement)
- Course notes: Big Bang section (Greg's notes on inflation, CMB, structure formation)
- Illustris Project: https://www.illustris-project.org
- Millennium Simulation: Springel et al. 2005
- EAGLE: Schaye et al. 2015
