# Ethan — Presentation TODO
## Section: The Three Body Problem + Intro Hook

---

## 1. Takeaway for the class
The three-body problem is the original demonstration that Newtonian gravity, despite being "solved," produces complexity we still can't fully tame. Sensitivity to initial conditions is the core lesson — and it echoes through everything that follows in the presentation.

---

## 2. Slide storyboard (~5 slides)

**Slide 1 — Intro hook (shared with group opening, ~1 min)**
- Gravity: the most universally *felt* force
- Sets up theme: "The Human Experience" — every discovery here was made by people trying to understand something they could feel but not explain
- Transition to three-body history

**Slide 2 — History: Newton to chaos**
- Kepler (~1609): planets move in ellipses, two-body problem has an exact solution
- Newton (~1687): inverse-square law, *Principia* — two-body fully solved
- Three bodies: immediately intractable; even Newton noted it
- Euler, Lagrange (~1750s–1770s): special cases (Lagrange points L1–L5)
- Poincaré (~1890): proves the general three-body problem has no closed-form solution — *this is the birth of chaos theory*
- Problem dates back to ~1500s attempts; still unsolved in general form today

**Slide 3 — Science: chaos, stability, and special solutions**
- Sensitivity to initial conditions: tiny IC change → completely different trajectory
- Known stable configurations: figure-8 orbit (Chenciner & Montgomery 2000), Lagrange-point solutions, Pluto system (resonance locks)
- Our solar system: a gravitational *miracle* — near-circular orbits, stable for billions of years
- Most random starting conditions → bodies are eventually ejected or collide

**Slide 4 — Demo**
- `ethansim`: three-body chaotic run (Pythagorean 3-4-5 configuration as default)
- Show: trajectories diverge chaotically, bodies sling around each other
- Optional: Pluto + 5 moons (stable resonant system — contrast with chaos)
- Optional: show two runs with slightly different ICs → totally different outcomes (if time)
- Note: precomputed JSON approach limits demo length (~30–40 sec of full-res sim) — keep it punchy

**Slide 5 — Bridge to Chris**
- The three-body problem generalized: what if N isn't 3 but 10^89?
- That's the Big Bang — every particle in the observable universe
- "Ethan showed us 3 bodies. Chris is going to show us what happens at the other extreme."
- *IC thread:* "For almost every starting position, chaos. Which makes our solar system's stability remarkable — and Brad is going to quantify just how stable it actually is."

---

## 3. Demo / replay checklist

- [ ] Confirm `ethansim` running cleanly on presentation machine
- [ ] Load `three_body` scenario (Pythagorean default) — already working
- [ ] Load `pluto_system` scenario — already working
- [ ] Optional: prepare a second three-body run with slightly perturbed IC to show sensitivity
- [ ] Keep each demo segment under 2 min — you have 5 min total including talking
- [ ] Precomputed JSON: verify file sizes won't hit transport limits (keep to ~30–40 sec of recorded sim)

---

## 4. Dependencies on others

- **Opening hook**: coordinate with group on 30-60s intro — or own it yourself since you're first
- **Chris**: clean narrative handoff ("N=3 → N=cosmic")
- **Jasper/Brad**: your IC sensitivity point sets up both their discussions; no direct dependency
- **Slides**: Jasper's Google Slides template; add your ~5 slides

---

## 5. Risks / mitigations

| Risk | Mitigation |
|------|-----------|
| "Descent into madness" integrator tangent runs long | Explicitly cut it; mention it's in the appendix / "ask me after" |
| Three-body demo looks like random noise to audience | Narrate what they're seeing in real time; point to bodies by name |
| Pluto system too subtle for audience | Skip it if time is tight; three-body chaos is the headline |
| Running out of slide time | Slide 5 (bridge) can be verbal; slides 2-3 are most important for content |

---

## 6. References

- Meeting transcript lines 298–301 (history angle), 334–343 (OG gravity / n-body chain), 706–728 (IC sensitivity, solar system stability), 793–797 (stable vs chaotic configurations)
- Poincaré, H. (1892). *Les Méthodes Nouvelles de la Mécanique Céleste*
- Chenciner & Montgomery (2000). Figure-8 orbit discovery
- ASTR 311 course notes: Newtonian gravity, orbital mechanics
