# Improvements Not Applied - Evaluation Report

This document evaluates which improvements from the improvement plan files have **NOT** been applied to the codebase, and assesses whether each improvement is needed.

**Generated:** 2026-01-10  
**Codebase:** `football_camera_switching.ipynb`

---

## Summary

### ✅ Improvements That HAVE Been Applied

1. **Hard timeline synchronization on switch** - ✅ Applied
   - Location: `_hard_sync_cap()` function, called before fallback and normal switches
   - Status: Fully implemented

2. **Center smoothing (EMA)** - ✅ Applied
   - Location: `StickyBallTracker._apply_center_smoothing()`
   - Status: Fully implemented with EMA alpha configuration

3. **Candidate confirmation (2-frame)** - ✅ Applied
   - Location: `STICKY_SUSPECT_CONFIRM_FRAMES = 2` in sticky tracker
   - Status: Fully implemented

4. **Sticky reset on camera switch** - ✅ Applied
   - Location: `STICKY_RESET_ON_CAM_SWITCH = True` with reset logic
   - Status: Fully implemented

5. **FPS-scaled thresholds (sticky)** - ✅ Applied
   - Location: `STICKY_USE_SECONDS = True` with `STICKY_FPS = 30`
   - Status: Fully implemented for sticky tracker

6. **Trajectory gating with minimum speed** - ✅ Applied
   - Location: `MIN_SPEED_FOR_EXIT = 0.002` with trajectory checks
   - Status: Fully implemented

7. **Consecutive frame zone arming** - ✅ Applied
   - Location: `ZONE_ARM_FRAMES = 3` with `_update_zone_arming()`
   - Status: Fully implemented

8. **Camera usage statistics** - ✅ Applied
   - Location: `_orch_stats["phase1"]["camera_usage"]` and highlight stats
   - Status: Fully implemented

9. **Round-robin fallback scanning** - ✅ Applied
   - Location: `FALLBACK_SCAN_ONE_CAM_PER_TICK` option
   - Status: Implemented as optional feature

10. **Reference timeline tracking** - ✅ Applied
    - Location: `REF_CAM_ID` and `ref_frame_pos` tracking
    - Status: Fully implemented

11. **Frame-accurate skip logic** - ✅ Applied
    - Location: Reference frame-based skipping in highlight output
    - Status: Fully implemented

---

## ❌ Improvements NOT Applied (Detailed Analysis)

### 1. Ball Tracking Improvements

#### 1.1 Motion-Consistency Selection
**Status:** ❌ NOT APPLIED  
**Priority:** HIGH  
**Needed:** YES - Critical for reducing false positives

**Description:**
- Current implementation selects highest confidence candidate without considering proximity to last known position
- Should prefer candidates near predicted location, penalizing large jumps unless confidence is extremely high

**Current Code:**
```python
# In detect_ball() - line ~4970
b = max(boxes, key=lambda x: float(x.conf.item()))  # Simple max confidence
```

**Impact:**
- Ball "teleports" between unrelated points
- Identity switches to false positives
- Unstable trajectory signals for switching

**Recommendation:** Implement motion-consistency gate that combines confidence with proximity to last known center or predicted location.

---

#### 1.2 Pitch-Aware Filtering
**Status:** ❌ NOT APPLIED  
**Priority:** HIGH  
**Needed:** YES - Major false positive reduction opportunity

**Description:**
- No filtering based on whether detection is on the pitch area
- Should reject detections outside green field region (crowd, scoreboard, ads)

**Current Code:**
- No pitch mask or field region detection implemented

**Impact:**
- False positives in crowd/scoreboard areas
- Wasted processing on off-field detections
- Unnecessary switching triggered by false positives

**Recommendation:** Add simple HSV-based pitch segmentation to create pitch mask, then reject or downweight detections outside pitch region.

---

#### 1.3 Soft Bbox-Size Prior (Adaptive)
**Status:** ⚠️ PARTIALLY APPLIED  
**Priority:** MEDIUM  
**Needed:** YES - But current implementation may be sufficient

**Description:**
- Should maintain adaptive expected size (EMA of bbox area) and reject boxes too large/small relative to frame
- Current code has static size constraints in fallback scan (`FALLBACK_MIN_BBOX_SIZE`, `FALLBACK_MAX_BBOX_SIZE`) but not in main detection

**Current Code:**
- Fallback scan has size constraints (lines ~8747-8748, ~9085-9086)
- Main `detect_ball()` has no adaptive size filtering

**Impact:**
- Detector may return big white blobs (ads/lines) as ball
- No adaptive size tracking based on zoom level

**Recommendation:** Add adaptive bbox area tracking (EMA) in main detection path, not just fallback scan.

---

#### 1.4 Standardized Detector Output Format
**Status:** ✅ MOSTLY APPLIED  
**Priority:** LOW  
**Needed:** PARTIALLY - Current format is adequate

**Description:**
- Should return explicit `found=False`, `conf=0`, `bbox=None` for "no detection" frames
- Current code returns `BallDet` with `bbox=None` which is functionally equivalent

**Current Code:**
- Returns `BallDet(bbox=None, center=None, conf=0.0, ...)` for no detections
- This is effectively the same as explicit `found=False`

**Impact:** Minimal - current implementation is functionally correct

**Recommendation:** Consider adding explicit `found` boolean field for clarity, but not critical.

---

### 2. Camera Switching Improvements

#### 2.1 FPS-Scaled Thresholds (Switching Logic)
**Status:** ⚠️ PARTIALLY APPLIED  
**Priority:** HIGH  
**Needed:** YES - Some thresholds are still frame-based

**Description:**
- Sticky tracker uses seconds-based thresholds, but camera switching logic still uses frame counts
- Should convert `SWITCH_COOLDOWN_FRAMES`, `MIN_HOLD_FRAMES`, `BALL_MISS_FRAMES_TO_SWITCH`, `ZONE_ARM_FRAMES` to seconds-based

**Current Code:**
```python
SWITCH_COOLDOWN_FRAMES = 15  # Still frame-based
ZONE_ARM_FRAMES = 3          # Still frame-based
BALL_MISS_FRAMES_TO_SWITCH = 10  # Still frame-based
```

**Impact:**
- Switching behavior varies with FPS (too aggressive at low FPS, sluggish at high FPS)
- Inconsistent behavior across different video sources

**Recommendation:** Convert all switching thresholds to seconds-based, similar to sticky tracker implementation.

---

#### 2.2 Explicit Camera Roles (No Name Inference)
**Status:** ❌ NOT APPLIED  
**Priority:** MEDIUM  
**Needed:** YES - Current name-based inference is fragile

**Description:**
- Currently infers camera roles from `CAMERA_NAMES` dictionary by string matching ("LEFT", "RIGHT", "MIDDLE")
- Should use explicit role mapping: `{cam_id: role}` with validation

**Current Code:**
```python
# Lines ~8300-8320: Name-based inference
if 'RIGHT' in name_upper:
    right_cam_id = cam_id
elif 'LEFT' in name_upper:
    left_cam_id = cam_id
# etc.
```

**Impact:**
- Breaks with inconsistent naming
- Fails if camera IDs are reordered
- Missing keywords cause routing failures

**Recommendation:** Add explicit `CAMERA_ROLES = {0: "RIGHT", 1: "LEFT", 2: "MIDDLE"}` configuration with startup validation.

---

#### 2.3 Pre-Switch Camera Readiness Checks
**Status:** ❌ NOT APPLIED  
**Priority:** MEDIUM  
**Needed:** YES - Would improve switch quality

**Description:**
- Should verify target camera can read a frame and optionally check for plausible ball before switching
- Currently switches immediately on decision without verification

**Current Code:**
- No pre-switch verification implemented
- Switches directly based on decision

**Impact:**
- May switch to camera that can't read frames
- May switch to camera without ball visible
- Degraded user experience

**Recommendation:** Add lightweight pre-switch check: read one frame from target camera, optionally run quick ball detection.

---

#### 2.4 Switch Moment Sync Invariant Documentation
**Status:** ⚠️ IMPLEMENTED BUT NOT DOCUMENTED  
**Priority:** LOW  
**Needed:** YES - Should be explicitly documented

**Description:**
- Hard-sync is implemented but not documented as a strict invariant
- Should document requirement that target camera must be synced to reference frame at switch moment

**Current Code:**
- `_hard_sync_cap()` is called before switches (lines ~9181, ~9332)
- No explicit documentation of this as an invariant

**Impact:** Low - functionality works, but lack of documentation makes maintenance harder

**Recommendation:** Add clear documentation comment explaining the sync invariant requirement.

---

### 3. Sticky Ball Logic Improvements

#### 3.1 Stationary Filter Context-Awareness
**Status:** ❌ NOT APPLIED  
**Priority:** MEDIUM  
**Needed:** YES - Current filter may suppress legitimate stationary ball

**Description:**
- Stationary filter marks detections as false if center stays within threshold for required frames
- Should only apply when stationary point is in known false-positive regions OR require size/shape mismatch OR only apply when confidence is low

**Current Code:**
- Stationary filter exists but doesn't check for set-piece context
- May reject legitimate stationary ball during corners, free kicks, penalties

**Impact:**
- Legitimate stationary ball moments (set pieces) may be rejected
- False negatives during important game moments

**Recommendation:** Make stationary filter context-aware: only apply in known false-positive regions (exclusion zones) or when confidence is consistently low.

---

#### 3.2 Per-Camera Sticky State (Alternative to Reset)
**Status:** ✅ APPLIED (Reset on Switch)  
**Priority:** N/A  
**Needed:** NO - Reset approach is sufficient

**Description:**
- Improvement suggests per-camera state OR reset on switch
- Current code uses reset on switch (`STICKY_RESET_ON_CAM_SWITCH = True`)

**Current Code:**
```python
if STICKY_RESET_ON_CAM_SWITCH:
    self.reset()
```

**Impact:** N/A - Reset approach works correctly

**Recommendation:** Current implementation is sufficient. Per-camera state would add complexity without clear benefit.

---

### 4. Multi-Camera Orchestrator Improvements

#### 4.1 Rate-Limited Fallback Scanning (Time-Based)
**Status:** ⚠️ PARTIALLY APPLIED  
**Priority:** MEDIUM  
**Needed:** YES - Current implementation is frame-based

**Description:**
- Round-robin option exists but fallback trigger is still frame-based
- Should use time-based limits for fallback scanning frequency

**Current Code:**
```python
FALLBACK_SCAN_ONE_CAM_PER_TICK = False  # Round-robin option exists
# But fallback trigger uses: frames_since_ball_found
```

**Impact:**
- Fallback scanning frequency varies with FPS
- May be too aggressive on high FPS, too slow on low FPS

**Recommendation:** Convert fallback trigger thresholds to time-based (seconds) instead of frame-based.

---

#### 4.2 Switch Metadata Storage
**Status:** ⚠️ PARTIALLY APPLIED  
**Priority:** LOW  
**Needed:** PARTIALLY - Some metadata exists but not comprehensive

**Description:**
- Should store comprehensive switch metadata: `from_cam`, `to_cam`, `ref_frame`, `reason`, `timestamp`
- Current code logs switches but doesn't store structured metadata

**Current Code:**
- Switch events are logged but not stored in structured format
- Some stats exist but not comprehensive metadata

**Impact:** Low - logging exists, but structured metadata would help analytics

**Recommendation:** Add structured switch metadata storage for post-processing analytics.

---

### 5. Highlight Output Improvements

#### 5.1 Camera Dominance Warnings
**Status:** ❌ NOT APPLIED  
**Priority:** LOW  
**Needed:** YES - Would help detect upstream issues

**Description:**
- Should compute per-camera usage ratios and emit warnings when dominance exceeds threshold (e.g., 90-100%)
- Current code tracks usage but doesn't warn on dominance

**Current Code:**
- Usage statistics are computed and printed
- No warnings for excessive dominance

**Impact:**
- May not detect when one camera dominates (indicating switching issues)
- Silent failures in switching logic

**Recommendation:** Add dominance check: if any camera > 90% usage, emit warning about potential switching issues.

---

#### 5.2 Audio Handling
**Status:** ❌ NOT APPLIED  
**Priority:** LOW  
**Needed:** OPTIONAL - Depends on requirements

**Description:**
- OpenCV video writing drops audio completely
- Should document audio loss or plan post-process audio mux step (FFmpeg)

**Current Code:**
- No audio handling
- Silent highlights

**Impact:**
- Silent highlights (may or may not be acceptable)
- Mismatch with broadcast expectations if audio is needed

**Recommendation:** Document audio loss clearly, optionally add post-process FFmpeg step to mux audio from source videos.

---

#### 5.3 Frame Read Failure Handling
**Status:** ⚠️ BASIC HANDLING EXISTS  
**Priority:** LOW  
**Needed:** PARTIALLY - Current handling may be sufficient

**Description:**
- Should explicitly track read failures and decide whether to retry, skip, or terminate
- Current code has basic error handling but may not be comprehensive

**Current Code:**
- Basic error handling exists with `errors_per_camera` tracking
- May need more explicit retry/skip logic

**Impact:** Low - basic handling exists, but could be more robust

**Recommendation:** Review and enhance frame read failure handling if issues are observed.

---

## Priority Ranking of Not-Applied Improvements

### 🔴 HIGH PRIORITY (Should Implement Soon)

1. **Motion-Consistency Selection** (Ball Tracking)
   - Critical for reducing false positives and teleportation
   - Directly impacts switching quality

2. **Pitch-Aware Filtering** (Ball Tracking)
   - Major false positive reduction opportunity
   - Relatively simple to implement (HSV segmentation)

3. **FPS-Scaled Thresholds** (Camera Switching)
   - Ensures consistent behavior across different FPS
   - Already implemented for sticky, should extend to switching

### 🟡 MEDIUM PRIORITY (Should Implement When Possible)

4. **Explicit Camera Roles** (Camera Switching)
   - Improves robustness and maintainability
   - Prevents failures from naming inconsistencies

5. **Stationary Filter Context-Awareness** (Sticky Logic)
   - Prevents false negatives during set pieces
   - Important for game coverage quality

6. **Pre-Switch Camera Readiness Checks** (Orchestrator)
   - Improves switch quality and user experience
   - Prevents switching to unavailable cameras

7. **Rate-Limited Fallback Scanning** (Orchestrator)
   - Ensures consistent fallback behavior across FPS
   - Prevents CPU overload

### 🟢 LOW PRIORITY (Nice to Have)

8. **Soft Bbox-Size Prior** (Ball Tracking)
   - Current static constraints may be sufficient
   - Adaptive version would be polish

9. **Camera Dominance Warnings** (Highlight Output)
   - Helps detect issues but doesn't fix them
   - Useful for debugging

10. **Switch Metadata Storage** (Orchestrator)
    - Useful for analytics but not critical for functionality
    - Can be added later if analytics are needed

11. **Audio Handling** (Highlight Output)
    - Depends on requirements
    - Can be handled post-process if needed

---

## Implementation Recommendations

### Quick Wins (Easy to Implement, High Impact)

1. **Pitch-Aware Filtering**: Simple HSV-based green field detection
2. **Camera Dominance Warnings**: Add check after usage statistics computation
3. **FPS-Scaled Thresholds**: Convert frame-based constants to seconds-based (similar to sticky)

### Medium Effort (Moderate Complexity, High Impact)

1. **Motion-Consistency Selection**: Add proximity check to candidate selection
2. **Explicit Camera Roles**: Refactor name inference to explicit configuration
3. **Pre-Switch Readiness Checks**: Add frame read + optional ball check before switch

### Longer Term (More Complex, Medium Impact)

1. **Stationary Filter Context-Awareness**: Integrate with exclusion zones or confidence history
2. **Rate-Limited Fallback Scanning**: Convert to time-based with proper timing logic

---

## Notes

- Many improvements have been successfully applied, showing good progress
- The highest-impact remaining improvements are in ball tracking (motion-consistency, pitch-aware)
- FPS-scaling should be extended from sticky tracker to switching logic for consistency
- Most improvements are incremental enhancements rather than critical fixes

---

**End of Report**
