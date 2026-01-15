# Highlight Output Cell — Evaluation & Improvement Plan (No Code)

This document reviews the **Highlight Output** cell — the final stage that writes the stitched highlight video from the active camera timeline — and proposes improvements **without code**.

Scope:
- consuming the active camera decision over time
- reading frames from synchronized camera streams
- trimming / skipping / duration control
- video writer configuration
- producing the final highlight MP4

This document focuses on **correctness, continuity, and broadcast quality**, not switching logic.

---

## What the highlight cell is doing (as designed)

The highlight cell acts as the **final recorder**:

1. Opens all camera video streams for output.
2. Seeks all cameras to a common **skip offset** (e.g., skip first N seconds).
3. Assumes camera switching decisions are already finalized upstream.
4. In a loop:
   - reads frames only from the **current active camera**
   - writes frames sequentially to a single `VideoWriter`
5. Stops after a fixed output duration.
6. Releases resources and saves the final highlight file.

This division of responsibility is architecturally correct.

---

## What’s strong / correct

### 1) Clear separation from decision logic
The highlight cell does **not** decide which camera is active.  
It simply records what the orchestrator decided.

This makes the pipeline debuggable and modular.

---

### 2) Explicit skip + max duration control
Supporting:
- `SKIP_SECONDS`
- `MAX_DUR`

is essential for highlight generation and replay trimming.

---

### 3) Lazy VideoWriter initialization
Initializing the writer only after receiving the first valid frame:
- avoids size mismatches
- avoids corrupted output files
- handles unknown resolution safely

---

### 4) FPS fallback protection
Using a fallback FPS avoids OpenCV edge cases where:
- input FPS is reported as 0
- writer silently fails

---

### 5) Logging and stats are present
Printing:
- output path
- frames written
- processing time
helps diagnose incomplete or corrupted outputs.

---

## High-impact risks / issues

### 1) Highlight cell reveals orchestrator bugs (but does not fix them)
If the orchestrator:
- switches cameras without hard-sync
- misaligns timelines
- advances time inconsistently

the highlight cell will faithfully record those mistakes.

**Key insight:**  
Highlight artifacts usually indicate **orchestrator errors**, not highlight logic bugs.

---

### 2) Skip logic must be frame-accurate
Seeking by time alone can be imprecise due to codec behavior.

**Symptoms:**
- skip starts a few frames early or late
- slight temporal mismatch across cameras

**Improvement direction:**
- prefer frame-based skipping using a reference camera
- hard-align all cameras to the same frame index after skip

---

### 3) Output FPS is decoupled from input FPS
Writing output at a fixed FPS:
- simplifies output
- but may introduce slight speed differences if input FPS differs

**Improvement direction:**
- either normalize deliberately (document it)
- or compute output FPS from the active camera or reference camera

---

### 4) No audio handling
OpenCV video writing drops audio completely.

**Symptoms:**
- silent highlights
- mismatch with broadcast expectations

**Improvement direction:**
- document audio loss clearly
- optionally plan a post-process audio mux step (FFmpeg)

---

### 5) Camera dominance is not validated
If one camera dominates 90–100% of frames:
- highlight may look static
- indicates upstream switching issues

**Improvement direction:**
- compute per-camera usage ratios
- emit warnings when dominance exceeds a threshold

---

### 6) Frame read failures are minimally handled
If `cap.read()` fails:
- behavior depends on fallback logic
- output duration may silently shorten

**Improvement direction:**
- track read failures explicitly
- decide whether to retry, skip, or terminate output

---

## Recommended improvements (ordered by ROI)

### Tier 1 — Must do (highest impact)
1. **Hard-align cameras after skip using a reference frame**  
2. **Treat orchestrator as the single source of truth** (do not add decision logic here)  
3. **Log frame indices and camera IDs during writing**  

### Tier 2 — Strongly recommended
4. Add **camera usage statistics** and dominance warnings  
5. Add explicit handling for frame read failures  
6. Clarify and document output FPS policy  

### Tier 3 — Nice to have (broadcast polish)
7. Add optional **audio reattachment** workflow (post-process)  
8. Add optional **burn-in overlays** (camera ID, timecode) for debug builds  
9. Support multiple output profiles (short highlight, extended cut, replay)

---

## How highlight quality depends on upstream components

The highlight cell is a **truth mirror** of upstream behavior:

- Bad ball tracking → missed moments
- Bad sticky logic → unnecessary fallback scanning
- Bad switching → wrong camera recorded
- Bad orchestrator sync → temporal jumps

The highlight cell itself should remain simple and deterministic.

---

## Validation checklist (practical)

When validating a highlight output:

- Does the video start exactly after the skip duration?
- Are camera switches visually continuous (no time jump)?
- Is the ball visible shortly after each switch?
- Is the output duration correct?
- Is file size and codec playable on common players?

---

## Operational workflow recommendation

1. Validate highlight cell with **single-camera input** first.
2. Enable orchestrator without switching → validate sync.
3. Enable switching → inspect continuity.
4. Only then enable trimming, logging, and stats.

---

## The single most important improvement

**Ensure that all cameras are perfectly aligned to the same frame index before writing begins, and rely entirely on the orchestrator for camera choice.**

If this invariant holds, highlight output quality becomes predictable and stable.

