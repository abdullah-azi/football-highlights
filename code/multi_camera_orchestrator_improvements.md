# Multi‑Camera Orchestrator Cell — Evaluation & Improvement Plan (No Code)

This document reviews the **Multi‑Camera Orchestrator** cell — the component that coordinates *all camera streams on a shared timeline*, applies fallback scanning, and applies camera switch decisions produced by the switching logic.

Scope:
- synchronizing multiple camera videos
- selecting which camera’s frame is processed at each moment
- performing fallback scans on non‑active cameras
- enforcing timeline alignment during switches
- feeding the final camera choice to the highlight writer

This document contains **no code** — only architectural and algorithmic guidance.

---

## What the orchestrator cell is doing (as designed)

The orchestrator acts as the **control plane** of the system:

1. Opens all camera streams.
2. Establishes a **reference timeline** (usually frame index or time).
3. Maintains an **active camera**.
4. For each step on the timeline:
   - reads a frame from the active camera
   - sends the frame to ball tracking → sticky → switching logic
   - receives a `SwitchDecision` (HOLD or SWITCH)
5. If HOLD:
   - continue reading from the active camera.
6. If SWITCH:
   - select a new camera
   - (optionally) scan other cameras to validate availability
7. Passes frames (or camera ID decisions) downstream to the highlight writer.

This separation of concerns is conceptually correct.

---

## What’s strong / correct

### 1) Centralized timeline ownership
The orchestrator being the **only component that advances time** is the correct design.  
Ball tracking and switching logic should never advance or rewind time themselves.

### 2) Separation of decision vs execution
- Camera switching logic decides *what should happen*.
- Orchestrator decides *how and when to apply it*.

This allows you to evolve switching logic independently.

### 3) Fallback scanning exists (important)
Scanning other cameras when the ball is lost is essential in football, where:
- occlusion is frequent
- detectors miss small fast objects
- the ball may already be visible in another view

---

## High‑impact risks / issues

### 1) Missing a **hard synchronization invariant**
The single most critical rule:

> **When a switch occurs, the target camera MUST be aligned to the current reference frame.**

If this is not enforced every time:
- the new camera may be ahead or behind in time
- highlight output shows jumps or wrong moments
- ball “disappears” after a switch even if logic was correct

**Improvement direction:**
- Treat timeline sync as a non‑negotiable invariant.
- Always log the reference frame index used during a switch.
- Never assume cameras are “already aligned”.

---

### 2) Reference timeline ambiguity
If the orchestrator mixes:
- loop iteration count
- wall‑clock time
- `CAP_PROP_POS_FRAMES` inconsistently

then drift will accumulate.

**Symptoms:**
- fallback scans don’t match the active camera moment
- switching decisions appear late or early
- statistics become unreliable

**Improvement direction:**
- choose ONE reference:
  - preferably `CAP_PROP_POS_FRAMES` of a reference camera
- treat all other time notions as derived, not authoritative

---

### 3) Fallback scanning can be CPU‑heavy and destabilizing
Scanning *all* other cameras frequently:
- increases latency
- creates uneven processing cadence
- may cause frame drops or delayed switching

**Improvement direction:**
- rate‑limit fallback scans
- use round‑robin scanning (one camera per tick)
- trigger fallback only after meaningful loss duration (time‑based)

---

### 4) Switching without verifying candidate camera readiness
If the orchestrator switches immediately on a decision without checking:
- whether the target camera can read a frame
- whether the frame contains a plausible ball

then switching can degrade user experience.

**Improvement direction:**
- add a lightweight “pre‑switch verification”:
  - one frame read
  - optional quick ball check
- allow switching logic to be advisory, not absolute

---

### 5) Active camera state leaks across responsibilities
If the orchestrator updates:
- sticky tracker
- camera switcher
- highlight writer  
without clearly resetting or isolating state, cross‑contamination occurs.

**Symptom:**
- sticky logic rejects valid detections after a switch
- jump rejections caused by previous camera state

**Improvement direction:**
- orchestrator should explicitly signal:
  - camera change events
  - reset / re‑initialization boundaries

---

## Recommended improvements (ordered by ROI)

### Tier 1 — Must do (highest impact)
1. **Enforce hard timeline sync on every switch**  
2. **Define a single authoritative reference timeline**  
3. **Explicitly signal camera‑change events to downstream logic**  
4. **Rate‑limit fallback scanning (time‑based, not frame‑based)**  

### Tier 2 — Strongly recommended
5. Add pre‑switch camera readiness checks  
6. Track per‑camera read failures and deprioritize unstable feeds  
7. Store switch metadata (from_cam, to_cam, ref_frame, reason)

### Tier 3 — Nice to have (robustness & polish)
8. Add switch hysteresis at orchestrator level (secondary guard)  
9. Support multi‑candidate switching (pick best among several cameras)  
10. Add watchdog metrics (time drift, lag, dropped reads)

---

## How orchestrator quality affects the whole system

The orchestrator is the **highest‑leverage component**:

- A perfect switching algorithm fails if orchestrator sync is wrong.
- Sticky and ball tracking quality is irrelevant if frames are misaligned.
- Highlight output quality directly reflects orchestrator correctness.

In practice:
> Most “bad switching” bugs originate in the orchestrator, not the switch logic.

---

## Practical validation checklist

When testing on real match footage:

- Are **reference frame indices monotonically increasing**?
- After a switch, is the ball visible within **0.5 seconds**?
- Do fallback scans respect timing limits?
- Does switching remain stable during long occlusions?
- Are read failures handled gracefully?

---

## Tuning & debugging workflow

1. Lock orchestrator to **single camera only** → verify timeline integrity.
2. Enable fallback scanning → verify alignment across cameras.
3. Enable switching logic → observe switch timing and continuity.
4. Only then enable highlight writing.

---

## The single most important improvement

**Treat timeline synchronization as a strict invariant, not a best‑effort behavior.**  

If this rule is enforced, most visual artifacts and switching complaints disappear.

