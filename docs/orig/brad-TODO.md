# Brad — Presentation TODO
## Section: Metric Analysis & Validation

---

## 1. Takeaway for the class
A simulation is only as good as its ability to produce verifiable results. By applying rigorous orbital metrics to Jasper's solar system sim, we can see exactly where our toy model succeeds, where it diverges from reality, and *why* — all tracing back to the choice of initial conditions.

---

## 2. Slide storyboard (~5 slides)

**Slide 1 — Background: orbital metrics**
- What is eccentricity? (0 = circle, 1 = parabola; most planets < 0.1)
- What is the barycenter? (system center of mass, not the Sun — relevant when Jupiter moves it significantly)
- What is perihelion? (closest approach point in orbit — moves slightly over time due to GR and perturbations)
- Why measure from the barycenter, not the Sun? (Sun is not at rest; barycenter is the inertial reference)

**Slide 2 — Hypothesis & methodology**
- Hypothesis: orbits should be near-circular, stable eccentricities, roughly matching real solar system values
- Method: read Jasper's sim position outputs → track each planet's orbit completion → compute per-orbit eccentricity from barycenter → log metadata → plot over time
- Setup: Brad's analysis pipeline reads simulation output files (positions), does not require Jasper to change anything

**Slide 3 — Findings: eccentricity results**
- Eccentricities vary significantly over time (more than expected from real solar system)
- Variation correlates with barycenter shift: when barycenter moves far from Sun's center, inner planets' orbits become more elliptical
- Jupiter + Saturn aligned on same side → peaks in eccentricity; opposite side → dips
- ~180-year repeating cycle — matches the period for planets to return to their starting (colinear) configuration
- Contrast with real solar system: eccentricities stable to 6 decimal places; Milankovitch cycles (~100k years) are extremely subtle

**Slide 4 — The perihelion puzzle**
- Attempted to track perihelion precession (especially Mercury: 43"/century from GR)
- Results: sporadic, inconsistent direction — not cleanly tracking
- Why: orbits are so nearly circular that "closest approach" can skip a timestep or be dominated by barycenter motion
- What this tells us: our sim *does* implement 1PN GR (Jasper verified Mercury precession), but at this level of analysis, near-circular orbits make perihelion a poor diagnostic
- Honest assessment: this part needs more work; what we have is suggestive but not conclusive

**Slide 5 — What this all means**
- The 180-year eccentricity cycle is directly traceable to artificial starting conditions (planets colinear at t=0)
- Real solar system orbits emerged from billions of years of gravitational settling, impacts, orbital resonances — you can't just place planets in a line
- *IC thread:* "Everything Ethan said about three-body sensitivity? We see it here at solar-system scale. Different starting point → measurably different orbital behavior."
- Conclusion: toy model works well enough to reveal interesting dynamics, but initial conditions limit how close we get to reality — and that's the point of the exercise

---

## 3. Demo / replay checklist

- [ ] Verify eccentricity math is correct before presenting (validate against known Mercury/Earth values for a short run)
- [ ] Finalize eccentricity vs. time plot (all 8 planets, clearly labeled)
- [ ] Add annotation showing ~180-year cycle and Jupiter+Saturn alignment moments
- [ ] Prepare comparison table: our eccentricities vs. real solar system values (NASA/JPL)
- [ ] Document perihelion findings honestly — show what you got and why it's inconclusive
- [ ] Optional: show "before vs. after" eccentricity if ICs are adjusted to realistic starting positions (nice-to-have, not required)
- [ ] Slides can include static plots (no live computation needed during presentation)

---

## 4. Dependencies on others

- **Jasper**: simulation output files (position data) — already accessible; no changes to Jasper's sim needed
- **Ethan**: IC sensitivity framing sets up your findings — coordinate on the callback ("Brad is going to quantify this")
- **Chris**: no direct dependency; Big Bang N-body metrics would require different analysis entirely (density, clumping) — out of scope for your section
- **Slides**: add your ~5 slides to Jasper's Google Slides template

---

## 5. Risks / mitigations

| Risk | Mitigation |
|------|-----------|
| Eccentricity math is wrong | Double-check: compute eccentricity from semi-major/minor axes AND from vis-viva; they should match |
| Perihelion results look bad | Present honestly as "inconclusive for near-circular orbits" — that's a valid scientific finding |
| Audience confused by barycenter vs Sun | Slide 1 defines this clearly; include a visual diagram |
| Not enough material for 5 min | The 180-year cycle + Jupiter/Saturn explanation is already rich; add Milankovitch comparison if time allows |
| Three-body analysis asked for | Explicitly scope it out: "For chaos regimes (Ethan's sim), there's nothing stable to compare against — metrics need something to latch on to" |

---

## 6. References

- Meeting transcript lines 535–598 (eccentricity findings, barycenter, 180-yr cycle), 610–646 (perihelion issues), 686–696 (why planets can't just be placed), 1350–1375 (scope: solar system, not three-body), 745–757 (scientific method framing)
- NASA/JPL planetary fact sheets: eccentricity values for comparison
- Milankovitch, M. (1941). Orbital forcing and ice ages
- ASTR 311 course notes: orbital mechanics, eccentricity
