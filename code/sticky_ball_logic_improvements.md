# Sticky Ball Logic Cell — Evaluation & Improvement Plan (No Code)

This document reviews the **Sticky Ball Tracker** cell (the “sticky ball logic” / stabilization layer that wraps `detect_ball`) and lists concrete improvements to make it more reliable for football broadcast footage and multi‑camera switching.

---

## What the sticky layer is doing (as implemented)

The sticky tracker acts as a **temporal stabilizer** on top of raw detections:

- **Accept** detections when confidence passes a gate (`STICKY_CONF_GATE`) and they are plausible relative to the last accepted ball.
- **Hold last** ball for up to `STICKY_MAX_HOLD_FRAMES` when the detector misses or returns low‑confidence output.
- **Reject** likely false positives using:
  - **Big jump + low IoU gate** (`STICKY_MAX_JUMP_PX` + `STICKY_IOU_GATE`)
  - **Exclusion zones** per camera (normalized rectangles)
  - **Stationary object filter** (detections that stay nearly fixed for many frames)
- Emits a `meta` field with flags like **`sticky`** and **`reason`** (accepted / hold_last / jump_rejected / low_conf_hold_last / exclusion_zone / stationary, etc.) plus counters.

This is a good foundation: it’s already structured as a “filter + memory + telemetry” module.

---

## What’s strong / correct

### 1) Multi-layer rejection is the right strategy
Football footage produces frequent false positives (field lines, ads, crowd highlights, goal net, corner flags). Combining **jump+IoU**, **exclusion zones**, and a **stationary filter** is exactly how you reduce those.

### 2) Holding last detection is essential for occlusion
Short occlusions from players are constant. A small “hold last” window prevents your pipeline from switching cameras or triggering fallback scans too early.

### 3) You are recording reasons and counters
The `meta.reason` plus counters (hold_count / total_miss_count / jump_px / iou_with_last) is extremely useful for debugging and for building later analytics (“why did we lose the ball here?”).

---

## High-impact risks / issues (needs attention)

### 1) **State is not camera-isolated**
The tracker keeps a single `last_det`, `hold_count`, and stationary history.

**Why this is risky:**  
When the orchestrator switches cameras, the new camera’s first valid ball position can be far from the last camera’s ball center. That can cause:
- **false “jump_rejected”** (because last_det belongs to a different camera view)
- unnecessary “hold_last” on the wrong location
- longer “lost” periods and worse switching decisions

**Fix direction (conceptual):**  
Maintain **per-camera sticky state** (last_det, hold_count, stationary history) *or* reset sticky state whenever the camera changes.

---

### 2) Stationary filter can suppress real “ball stopped” moments
The stationary object filter marks detections as false if the center stays within `STATIONARY_THRESHOLD_PX` for `STATIONARY_FRAMES_REQUIRED`.

**Why this can be wrong in football:**  
- Set pieces: corners, free kicks, throw-ins, penalties  
- Ball can be stationary on the pitch for seconds

**Fix direction (conceptual):**
- Only apply stationary filter when the stationary point is in **known false-positive regions** (e.g., a fixed ad board) or
- Require stationary *and* “ball-like size/shape mismatch” or
- Apply stationary filter only if confidence is low/unstable (not when confidence is consistently high)

---

### 3) Jump+IoU gate is good, but needs a “motion-aware” threshold
The condition “big jump and low IoU” rejects wrong objects, but:
- Broadcast cameras can pan/zoom suddenly
- Ball can move quickly across frames (especially at 25–30 fps + motion blur)

**Fix direction (conceptual):**
- Make the jump threshold **adaptive** based on:
  - estimated ball speed
  - recent camera motion (if you have it)
  - frame resolution
- Or introduce a “two-step confirmation”: treat one suspicious detection as **candidate**, accept only if it persists in the next frame.

---

### 4) Hold window may be too short for real occlusions
`STICKY_MAX_HOLD_FRAMES = 8` might be too small depending on FPS:
- At 30 fps: ~0.27 s
- At 25 fps: ~0.32 s
Some occlusions last longer.

**Fix direction (conceptual):**
- Scale hold frames by FPS, or tune by match footage:
  - Typical: 0.4–0.8 seconds of hold for football
- Additionally, allow **longer hold if the last detection confidence was high**, shorter hold if last confidence was low.

---

### 5) Exclusion zones are powerful but need a maintenance workflow
You already support per-camera exclusion rectangles, which is great.

**Failure mode:**  
If the camera framing changes slightly (different match, different stadium, different crop), hardcoded zones become stale.

**Fix direction (conceptual):**
- Create a simple calibration workflow:
  - Collect “false positive centers” automatically into a CSV/JSON
  - Cluster them per camera
  - Suggest zones from clusters (then you manually approve)
- Keep zones versioned per camera profile (“Stadium A”, “Stadium B”, etc.)

---

## Recommended improvements (ordered by ROI)

### Tier 1 — Must do (biggest benefit)
1. **Per-camera sticky state** or **reset on camera switch**  
2. Convert all frame-count thresholds to **FPS-scaled seconds** (hold, stationary required frames, etc.)  
3. Add an explicit **“camera cut / zoom” tolerance mode** (temporarily relax jump checks)

### Tier 2 — Strongly recommended
4. Make stationary filter context-aware (don’t punish legitimate stationary ball)  
5. Add “candidate accept” logic (require 2 consecutive frames before accepting a suspicious new location)  
6. Improve exclusion-zone workflow (auto collect false-positive points; cluster & propose zones)

### Tier 3 — Nice to have (polish / robustness)
7. Track and log **false-rejection rate** and **hold utilization**  
8. Provide a “confidence smoothing” score (EMA of confidence) for better downstream decisions  
9. Add a lightweight “ball size sanity check” (bbox area range as a soft feature, not a hard gate)

---

## How this impacts camera switching quality

A sticky layer directly affects switching in two ways:

- **Prevents spurious switches**: false positives near edges shouldn’t arm exit zones or trigger switch logic.
- **Improves continuity**: holding last known ball avoids “ball lost” events that cause fallback scanning and unstable camera changes.

The single most important integration guarantee:  
**Sticky state must be compatible with multi-camera switching** (per-camera memory or reset on switch), otherwise it can create time-jumps and “ball disappears after switch” artifacts even if the orchestrator is correct.

---

## Suggested validation checklist (practical)

When you run on a representative match clip, measure:

- % frames with **valid ball** (after sticky)  
- # of **jump_rejected** events (should drop after per-camera state)  
- # of **stationary** rejections (should not spike during set pieces)  
- average **hold length** during occlusions  
- camera switching stability: # switches/minute and % switches where ball is visible within 0.5s after switching

---

## Next step you should implement first

**Implement per-camera sticky state OR reset sticky state on camera change.**  
This is the highest-impact fix for a multi-camera pipeline and will immediately reduce incorrect rejections and “sticky holds” after a switch.

