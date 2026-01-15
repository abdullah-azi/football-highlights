# Camera Switching Cell — Evaluation & Improvement Plan (No Code)

This document reviews the **Camera Switching Logic** cell (the state machine that emits `SwitchDecision`) for a football match multi‑camera pipeline, and lists concrete improvements **without code**.  
Scope: the cell that decides **HOLD vs SWITCH** based on ball detections (raw or sticky), exit zones, trajectory history, cooldown/hold logic, and routing to a target camera.

---

## What this cell is doing (as implemented)

At a high level, the camera switching cell:

1. Consumes per-frame ball detections from the **active camera**.
2. Classifies the frame into a detection state:
   - **FOUND**: confident, non-sticky detection
   - **HELD**: sticky detection (tracker holding last)
   - **LOST**: no bbox or low-confidence non-sticky detection
3. Maintains short history (ball center positions) to estimate **motion / velocity**.
4. Uses **exit-zone** geometry to detect when the ball approaches the border of the frame.
5. Uses a combination of:
   - cooldown frames
   - minimum hold duration
   - miss counts / disappearance logic
   - (optional) trajectory checks  
   to decide whether a switch is warranted.
6. Chooses a target camera (often via camera “names” or inferred roles) and returns a `SwitchDecision`.

This is the correct general architecture for a switching “brain”.

---

## What’s strong / correct

### 1) A state machine exists (not a one-frame heuristic)
Having FOUND/HELD/LOST and gating decisions via cooldown/hold is essential. This reduces camera ping‑pong and prevents switches from a single noisy detection.

### 2) Exit-zone concept is directionally right for football broadcast
Broadcast camera feeds have consistent framing; when the ball leaves view, it typically exits near an edge. Zone arming and “disappear after zone” is a good heuristic.

### 3) Telemetry and reasons are included
Switch reasons and per-frame debug prints are critical for tuning and for making the system explainable.

---

## High-impact issues (most likely to cause bad switching)

### 1) Exit zones are too generic and too sensitive
If exit zones are large (e.g., full height/width strips), then:
- camera panning can place the ball in the strip even while it’s still central to play
- detection jitter pushes the center over boundaries
- set pieces near the touchline cause repetitive arming

**Symptom:** unnecessary switches and instability.

**Improvement direction:**
- shrink zones (especially top/bottom) for broadcast football
- require **consecutive frames** in zone to arm (time-based, FPS-scaled)
- gate arming by **confidence** and (optionally) **ball speed**

---

### 2) Missing a “switch moment sync invariant” (integration issue)
The camera switching cell can correctly decide “SWITCH”, but if the orchestrator does not **hard-seek** the target camera to the current timeline frame at the moment of switching, the highlight output will show:
- time jumps
- ball not present after switch
- “wrong moment” switches

**This is not a bug inside the switching cell**, but the switching cell should define this requirement explicitly.

**Improvement direction:**
- document the invariant: **on switch, target camera must be synced to reference frame**
- log frame/timestamp used for decision to support debugging

---

### 3) Thresholds are frame-count based, not FPS-scaled
Using constants like “3 frames to switch” behaves very differently at:
- 25 fps vs 60 fps
- varying decode performance

**Symptom:** too aggressive switching on low FPS; too sluggish switching on high FPS.

**Improvement direction:**
- define thresholds in seconds (cooldown, hold, miss tolerance, arming) and convert using FPS.

---

### 4) Miss logic conflates occlusion with true exit
In football, the ball is frequently occluded for short periods (players), especially near the midfield. If miss-based switching is too aggressive:
- you’ll trigger fallback scans too often
- switch on noise when ball is merely hidden

**Improvement direction:**
- split missing logic into:
  - **missing while armed in zone** (fast switch)
  - **missing while not in zone** (slow or no switch; let orchestrator scan)
- make miss tolerances time-based, and depend on last known confidence

---

### 5) Trajectory gating may be disabled or underused
Direction-of-motion validation is critical:
- it prevents edge jitter from triggering a switch
- it disambiguates “ball near edge” vs “ball leaving frame”

**Symptom:** switches triggered even when the ball is not moving toward that edge.

**Improvement direction:**
- enable trajectory gating by default
- require **minimum speed** before trusting direction (avoid jitter)
- compute direction from a short window and smooth the center positions (EMA)

---

### 6) Camera role mapping is fragile (name-based inference)
Inferring role (“LEFT/RIGHT/MIDDLE”) from camera name strings can break easily:
- inconsistent naming
- reordered IDs
- missing keywords
- two cameras both tagged “wide” or “main”

**Symptom:** switches to the wrong camera or always routing to the middle.

**Improvement direction:**
- define explicit camera roles in config: `{cam_id: role}`
- define explicit routing rules per role
- validate mapping at startup (must be unique + complete)

---

## Recommended improvements (ordered by ROI)

### Tier 1 — Must do (highest benefit)
1. **FPS-scaled thresholds** (seconds-based) for cooldown/hold/arming/miss tolerance  
2. **Consecutive-frame zone arming** + confidence gating  
3. **Trajectory gating** with minimum speed + smoothed centers  
4. **Explicit camera roles** (no name guessing) and explicit routing rules  
5. **Document + enforce the switch-time sync invariant** in orchestrator integration

### Tier 2 — Strongly recommended
6. Add “candidate switch confirmation” (2-step): suspect → confirm next frames  
7. Add “switch quality guard”: don’t switch unless target camera is likely to contain the ball (orchestrator scan)  
8. Add “set-piece awareness”: reduce switching aggressiveness near stationary-ball phases

### Tier 3 — Nice to have (polish / robustness)
9. Add adaptive zone sizes depending on zoom level or camera type  
10. Add switch hysteresis based on game context (e.g., ball in attacking third)  
11. Add automatic tuning metrics collection (switches/min, time-to-ball-after-switch)

---

## How to validate improvements (practical checklist)

Run on multiple real match clips (different stadiums/lighting) and measure:

- **Switches per minute** (too high = jittery; too low = sluggish)
- **Ball visible within 0.5s after switch** (key metric)
- **False switch rate**: switches where ball remains in active cam view
- **Zone arming stability**: number of arm/disarm oscillations
- **Occlusion handling**: average hold duration during occlusions; avoid switching in midfield crowd

---

## Operational guidance: tuning workflow

1. Start with **wide camera locked** (no switching) to calibrate ball detector + sticky.  
2. Enable switching only with **trajectory gating + armed zone disappearance**.  
3. Tune:
   - zone sizes
   - arming time
   - min speed threshold
   - miss tolerance (in-zone vs not-in-zone)  
4. Only then add:
   - more aggressive proactive switching
   - multi-camera verification integration

---

## The single most important improvement

**Move from name-inference + frame-count thresholds to:**
- **explicit roles + seconds-based thresholds + trajectory gating**.

This change alone dramatically stabilizes camera switching for football broadcasts.

